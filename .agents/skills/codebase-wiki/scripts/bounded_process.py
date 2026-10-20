"""Shell-free subprocesses with a deadline and a combined output budget."""
from __future__ import annotations

import os
import signal
import subprocess
import threading
import time
from typing import Mapping, Sequence


class ProcessLimitError(subprocess.SubprocessError):
    """The command was stopped; its partial output is not a complete result."""


class _WindowsJob:
    """Kill descendants even when their original parent has already exited."""
    def __init__(self, process):
        import ctypes
        from ctypes import wintypes as w
        class Basic(ctypes.Structure):
            _fields_ = [("process_time", ctypes.c_int64), ("job_time", ctypes.c_int64),
                        ("flags", w.DWORD), ("min_ws", ctypes.c_size_t), ("max_ws", ctypes.c_size_t),
                        ("active", w.DWORD), ("affinity", ctypes.c_size_t), ("priority", w.DWORD), ("scheduling", w.DWORD)]
        class IO(ctypes.Structure):
            _fields_ = [(name, ctypes.c_uint64) for name in ("read_ops", "write_ops", "other_ops", "read_bytes", "write_bytes", "other_bytes")]
        class Extended(ctypes.Structure):
            _fields_ = [("basic", Basic), ("io", IO), ("process_memory", ctypes.c_size_t),
                        ("job_memory", ctypes.c_size_t), ("peak_process", ctypes.c_size_t), ("peak_job", ctypes.c_size_t)]
        self.api = ctypes.WinDLL("kernel32", use_last_error=True)
        self.api.CreateJobObjectW.argtypes = [ctypes.c_void_p, w.LPCWSTR]
        self.api.CreateJobObjectW.restype = w.HANDLE
        self.api.SetInformationJobObject.argtypes = [w.HANDLE, ctypes.c_int, ctypes.c_void_p, w.DWORD]
        self.api.AssignProcessToJobObject.argtypes = [w.HANDLE, w.HANDLE]
        self.api.TerminateJobObject.argtypes = [w.HANDLE, w.UINT]
        self.api.CloseHandle.argtypes = [w.HANDLE]
        self.handle = self.api.CreateJobObjectW(None, None)
        info = Extended(); info.basic.flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if (not self.handle or not self.api.SetInformationJobObject(self.handle, 9, ctypes.byref(info), ctypes.sizeof(info))
            or not self.api.AssignProcessToJobObject(self.handle, int(process._handle))):
            if self.handle:
                self.api.CloseHandle(self.handle)
            raise OSError(ctypes.get_last_error(), "unable to bound the subprocess tree")

    def stop(self):
        self.api.TerminateJobObject(self.handle, 1)

    def close(self):
        self.api.CloseHandle(self.handle)


def _stop(process: subprocess.Popen, job=None) -> None:
    if os.name == "nt":
        # /T includes descendants; no shell or user-controlled command text.
        if job is not None:
            job.stop()
        else:
            try:
                subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                               timeout=5, check=False, creationflags=subprocess.CREATE_NO_WINDOW)
            except (OSError, subprocess.SubprocessError):
                pass
    else:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    if process.poll() is None:
        process.kill()


def run_bounded(command: Sequence[str], *, cwd=None, env: Mapping[str, str] | None = None,
                timeout: float = 30, max_output_bytes: int = 8 * 1024 * 1024,
                check: bool = False, text: bool = False, encoding: str = "utf-8") -> subprocess.CompletedProcess:
    if timeout <= 0 or max_output_bytes <= 0:
        raise ValueError("timeout and output budget must be positive")
    options = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {"start_new_session": True}
    process = subprocess.Popen(list(command), cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False, **options)
    try:
        job = _WindowsJob(process) if os.name == "nt" else None
    except OSError:
        _stop(process)
        process.wait()
        process.stdout.close(); process.stderr.close()
        raise
    output = [bytearray(), bytearray()]
    mutex = threading.Lock()
    exceeded = threading.Event()
    used = 0

    def drain(stream, index):
        nonlocal used
        try:
            while chunk := stream.read(64 * 1024):
                with mutex:
                    remaining = max_output_bytes - used
                    output[index].extend(chunk[:remaining])
                    used += min(remaining, len(chunk))
                    if len(chunk) > remaining:
                        exceeded.set()
        finally:
            stream.close()

    threads = [threading.Thread(target=drain, args=(stream, i), daemon=True)
               for i, stream in enumerate((process.stdout, process.stderr))]
    for thread in threads:
        thread.start()
    deadline = time.monotonic() + timeout
    failure = None
    try:
        while process.poll() is None or any(thread.is_alive() for thread in threads):
            if exceeded.is_set():
                failure = f"command output exceeded {max_output_bytes} bytes; narrow the scope"
                break
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                failure = f"command exceeded {timeout:g} seconds; narrow the scope"
                break
            exceeded.wait(min(remaining, 0.02))
    finally:
        if failure:
            _stop(process, job)
        process.wait()
        for thread in threads:
            thread.join(timeout=5)
        if job is not None:
            job.close()
    if exceeded.is_set() and failure is None:
        failure = f"command output exceeded {max_output_bytes} bytes; narrow the scope"
    if failure:
        raise ProcessLimitError(failure)
    stdout, stderr = (bytes(value) for value in output)
    if text:
        stdout, stderr = (value.decode(encoding, errors="replace") for value in (stdout, stderr))
    result = subprocess.CompletedProcess(list(command), process.returncode, stdout, stderr)
    if check:
        result.check_returncode()
    return result
