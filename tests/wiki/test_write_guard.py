from __future__ import annotations

from contextlib import redirect_stdout
import io
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


REPO_ROOT = Path(__file__).parents[2]
HOOKS = REPO_ROOT / ".agents" / "skills" / "codebase-wiki" / "scripts" / "hooks"
CANONICAL_GUARD = HOOKS / "wiki-write-guard.py"
SESSION_HOOK = HOOKS / "wiki-session-init.py"
sys.path.insert(0, str(HOOKS))


def load_guard():
    spec = importlib.util.spec_from_file_location("wiki_write_guard_under_test", CANONICAL_GUARD)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def create_hook_fixture(root: Path) -> None:
    scripts = root / ".agents" / "skills" / "codebase-wiki" / "scripts"
    scripts.mkdir(parents=True)
    shutil.copy2(HOOKS.parent / "frontmatter.py", scripts / "frontmatter.py")
    shutil.copytree(HOOKS, scripts / "hooks")
    (root / "AGENTS.md").write_text("# Fixture\n", encoding="utf-8")
    (root / "wiki").mkdir()
    (root / "wiki" / "index.md").write_text(
        "---\ntitle: Index\ntype: index\nsources: []\n"
        "last_updated: 2026-09-03\ntags: [index]\nstatus: active\n---\n",
        encoding="utf-8",
    )
    (root / "wiki" / "log.md").write_text(
        "---\ntitle: Log\ntype: log\nsources: []\n"
        "last_updated: 2026-09-03\ntags: [log]\nstatus: active\n---\n",
        encoding="utf-8",
    )


def run_configured_command(command: str, cwd: Path, payload: dict[str, object]) -> subprocess.CompletedProcess[str]:
    if os.name == "nt":
        prefix = 'powershell.exe -NoProfile -NonInteractive -Command "'
        if not command.startswith(prefix) or not command.endswith('"'):
            raise AssertionError(f"unexpected Windows hook command: {command}")
        args: str | list[str] = [
            "powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            command[len(prefix) : -1],
        ]
        shell = False
    else:
        args = command
        shell = True
    return subprocess.run(
        args,
        cwd=cwd,
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        shell=shell,
    )


class WriteGuardTests(unittest.TestCase):
    def run_guard(self, guard, payload: object, platform: str = "codex") -> dict[str, object]:
        raw = payload if isinstance(payload, str) else json.dumps(payload)
        output = io.StringIO()
        with (
            mock.patch.object(sys, "argv", [str(CANONICAL_GUARD), "--platform", platform]),
            mock.patch.object(sys, "stdin", io.StringIO(raw)),
            redirect_stdout(output),
        ):
            guard.main()
        return json.loads(output.getvalue())

    def test_common_hook_payload_shapes_and_path_keys_are_normalized(self) -> None:
        import common

        self.assertEqual(
            common.parse_tool_input({"tool_input": {"path": "wiki/a.md"}}),
            {"path": "wiki/a.md"},
        )
        self.assertEqual(
            common.parse_tool_input({"toolInput": {"path": "wiki/b.md"}}),
            {"path": "wiki/b.md"},
        )
        self.assertEqual(
            common.parse_tool_input({"toolArgs": '{"path":"wiki/c.md"}'}),
            {"path": "wiki/c.md"},
        )
        self.assertEqual(common.parse_tool_input({"toolArgs": "not-json"}), "not-json")
        self.assertEqual(common.extract_patch_text("*** Update File: wiki/a.md"), "*** Update File: wiki/a.md")
        self.assertEqual(common.extract_patch_text(42), "")

        paths = common.extract_paths(
            "Write",
            {
                "filePath": "wiki/a.md",
                "file_path": "wiki/b.md",
                "path": "wiki/c.md",
                "targetPath": "wiki/d.md",
                "target_path": "wiki/e.md",
                "files": [
                    "wiki/f.md",
                    {"filePath": "wiki/g.md", "file_path": "wiki/h.md", "path": "wiki/i.md"},
                    42,
                ],
                "patch": "*** Update File: wiki/j.md\n*** Delete File: src/raw.py\n",
            },
        )
        self.assertEqual(
            paths,
            [
                "wiki/a.md",
                "wiki/b.md",
                "wiki/c.md",
                "wiki/d.md",
                "wiki/e.md",
                "wiki/f.md",
                "wiki/g.md",
                "wiki/h.md",
                "wiki/i.md",
                "wiki/j.md",
                "src/raw.py",
            ],
        )

    def test_guard_main_fail_closed_and_supports_platform_payloads(self) -> None:
        guard = load_guard()

        malformed = self.run_guard(guard, "{")
        self.assertEqual(malformed["permissionDecision"], "deny")
        self.assertIn("failed closed", malformed["permissionDecisionReason"])

        non_object = self.run_guard(guard, [])
        self.assertEqual(non_object["permissionDecision"], "deny")

        unknown_tool = self.run_guard(
            guard, {"tool_name": "Read", "tool_input": {"file_path": "src/raw.py"}}
        )
        self.assertEqual(unknown_tool, {})

        missing_path = self.run_guard(guard, {"tool_name": "Write", "tool_input": {}})
        self.assertEqual(missing_path["permissionDecision"], "deny")

        blocked = self.run_guard(
            guard, {"tool_name": "Write", "tool_input": {"file_path": "../outside.py"}}
        )
        self.assertEqual(blocked["permissionDecision"], "deny")

        copilot_shape = self.run_guard(
            guard,
            {"toolName": "Write", "toolInput": {"filePath": "wiki/overview.md"}},
            platform="copilot",
        )
        self.assertEqual(copilot_shape, {})

    def test_guard_coexist_allow_includes_audit_context(self) -> None:
        guard = load_guard()
        with mock.patch.object(guard, "read_guard_mode", return_value="coexist"):
            payload = self.run_guard(
                guard, {"tool_name": "Write", "tool_input": {"file_path": "src/raw.py"}}
            )
        self.assertEqual(payload["permissionDecision"], "allow")
        self.assertIn("raw sources remain read-only", payload["hookSpecificOutput"]["additionalContext"])

    def test_guard_mode_config_maps_legacy_and_invalid_values_fail_closed(self) -> None:
        guard = load_guard()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = root / ".codex/config.toml"
            config.parent.mkdir()
            for value, expected in (
                ("target", "wiki-only"),
                ("wiki-only", "wiki-only"),
                ("coexist", "coexist"),
                ("framework", "framework"),
                ("invalid", "wiki-only"),
            ):
                config.write_text(f"[wiki_guard]\nmode = \"{value}\"\n", encoding="utf-8")
                with self.subTest(value=value), mock.patch.object(guard, "repo_root", return_value=root):
                    self.assertEqual(guard.read_guard_mode("codex"), expected)
            config.unlink()
            with mock.patch.object(guard, "repo_root", return_value=root):
                self.assertEqual(guard.read_guard_mode("codex"), "wiki-only")

    def test_platform_configs_use_canonical_hooks(self) -> None:
        codex_path = REPO_ROOT / ".codex/hooks.json"
        codex = codex_path.read_text(encoding="utf-8")
        self.assertIn(".agents/skills/codebase-wiki/scripts/hooks/", codex.replace("\\", "/"))
        self.assertIn("--platform codex", codex)
        hooks = json.loads(codex)
        for handlers in hooks["hooks"].values():
            for handler_group in handlers:
                for handler in handler_group["hooks"]:
                    command = handler["commandWindows"]
                    self.assertLess(
                        command.index("[Console]::OutputEncoding"),
                        command.index("git rev-parse"),
                    )
                    self.assertIn("$OutputEncoding = [Console]::OutputEncoding", command)
        for path in (REPO_ROOT / ".github/hooks").glob("*.json"):
            text = path.read_text(encoding="utf-8")
            self.assertIn(".agents/skills/codebase-wiki/scripts/hooks/", text)
            self.assertIn("--platform copilot", text)

    def test_session_context_stays_within_budget(self) -> None:
        spec = importlib.util.spec_from_file_location("wiki_session_under_test", SESSION_HOOK)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        message = module.build_message(REPO_ROOT)
        self.assertLessEqual(len(message.encode("utf-8")), 4 * 1024)
        self.assertLessEqual(len(message.splitlines()), 30)
        oversized = module.bounded_message(["中" * 5_000])
        self.assertLessEqual(len(oversized.encode("utf-8")), 4 * 1024)

    def test_session_skips_unsafe_or_unreadable_wiki_files(self) -> None:
        spec = importlib.util.spec_from_file_location(
            "wiki_session_safety_under_test", SESSION_HOOK
        )
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            wiki = root / "wiki"
            wiki.mkdir()
            (wiki / "valid.md").write_text(
                "---\ntype: guide\nstatus: active\n---\n", encoding="utf-8"
            )
            (wiki / "binary.md").write_bytes(bytes((0xFF, 0xFE)))
            outside = root / "outside.md"
            outside.write_text(
                "---\ntype: secret\nstatus: active\n---\nSECRET\n", encoding="utf-8"
            )
            (wiki / "linked.md").write_text(outside.read_text(encoding="utf-8"), encoding="utf-8")

            with mock.patch.object(
                module,
                "audit_path_is_safe",
                side_effect=lambda path: path.name != "linked.md",
            ):
                message = module.build_message(root)

            self.assertIn("Pages: 1", message)
            self.assertIn("Skipped unsafe/unreadable pages: 2", message)
            self.assertNotIn("SECRET", message)

    def test_session_handles_unreadable_log_without_traceback(self) -> None:
        spec = importlib.util.spec_from_file_location(
            "wiki_session_log_safety_under_test", SESSION_HOOK
        )
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / "log.md"
            log.write_bytes(bytes((0xFF, 0xFE)))
            with mock.patch.object(module, "audit_path_is_safe", return_value=True):
                self.assertEqual(module.recent_log_headings(log), [])

    def test_codex_session_matcher_covers_compaction_sources(self) -> None:
        hooks = json.loads((REPO_ROOT / ".codex/hooks.json").read_text(encoding="utf-8"))
        matcher = hooks["hooks"]["SessionStart"][0]["matcher"]
        self.assertEqual(matcher, "startup|resume|clear|compact")

    def test_codex_hooks_run_from_repo_root_git_subdirectory_and_non_git_root(self) -> None:
        hooks = json.loads((REPO_ROOT / ".codex/hooks.json").read_text(encoding="utf-8"))
        cases = {
            "SessionStart": {"hook_event_name": "SessionStart", "source": "startup"},
            "PreToolUse": {
                "tool_name": "apply_patch",
                "tool_input": {"command": "*** Update File: wiki/index.md\n"},
            },
            "PostToolUse": {
                "tool_name": "apply_patch",
                "tool_input": {"command": "*** Update File: wiki/index.md\n"},
            },
        }
        with tempfile.TemporaryDirectory() as directory:
            temporary = (Path(directory) / "使用者 暫存").resolve()
            temporary.mkdir()
            git_root = temporary / "git fixture"
            non_git_root = temporary / "non git fixture"
            for root in (git_root, non_git_root):
                create_hook_fixture(root)
            subprocess.run(["git", "init", "-q"], cwd=git_root, check=True)
            nested = git_root / "nested" / "module"
            nested.mkdir(parents=True)

            for location_name, cwd in (
                ("repo-root", git_root),
                ("git-subdirectory", nested),
                ("non-git-root", non_git_root),
            ):
                for event_name, payload in cases.items():
                    handler = hooks["hooks"][event_name][0]["hooks"][0]
                    command_key = "commandWindows" if os.name == "nt" else "command"
                    result = run_configured_command(handler[command_key], cwd, payload)
                    with self.subTest(location=location_name, event=event_name):
                        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                        self.assertIsInstance(json.loads(result.stdout), dict)

    def test_apply_patch_extraction_catches_mixed_targets(self) -> None:
        guard = load_guard()
        paths = guard.extract_paths(
            "apply_patch",
            {
                "command": (
                    "*** Update File: wiki/overview.md\n"
                    "*** Update File: src/raw.py\n"
                )
            },
        )
        self.assertEqual(paths, ["wiki/overview.md", "src/raw.py"])
        self.assertTrue(guard.is_allowed_path(paths[0], "wiki-only"))
        self.assertFalse(guard.is_allowed_path(paths[1], "wiki-only"))

    def test_codex_deny_output_uses_nested_hook_contract(self) -> None:
        guard = load_guard()
        output = io.StringIO()
        with redirect_stdout(output):
            guard.respond_deny("blocked for test")
        payload = json.loads(output.getvalue())
        self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "PreToolUse")
        self.assertEqual(payload["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertEqual(payload["permissionDecision"], "deny")

    def test_hooks_handle_non_object_json_without_traceback(self) -> None:
        guard = subprocess.run(
            [sys.executable, str(CANONICAL_GUARD), "--platform", "codex"],
            cwd=REPO_ROOT,
            input="[]",
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        self.assertEqual(guard.returncode, 0, guard.stdout + guard.stderr)
        guard_payload = json.loads(guard.stdout)
        self.assertEqual(guard_payload["permissionDecision"], "deny")

        reminder = subprocess.run(
            [
                sys.executable,
                str(CANONICAL_GUARD.with_name("wiki-log-reminder.py")),
                "--platform",
                "codex",
            ],
            cwd=REPO_ROOT,
            input="[]",
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        self.assertEqual(reminder.returncode, 0, reminder.stdout + reminder.stderr)
        self.assertEqual(json.loads(reminder.stdout), {})

    def test_session_and_log_hooks_emit_nested_context(self) -> None:
        session = subprocess.run(
            [sys.executable, str(SESSION_HOOK), "--platform", "codex"],
            cwd=REPO_ROOT,
            input=json.dumps({"hook_event_name": "SessionStart", "source": "compact"}),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        self.assertEqual(session.returncode, 0, session.stdout + session.stderr)
        session_payload = json.loads(session.stdout)
        self.assertEqual(
            session_payload["hookSpecificOutput"]["hookEventName"], "SessionStart"
        )
        self.assertIn("Wiki state", session_payload["hookSpecificOutput"]["additionalContext"])

        reminder = subprocess.run(
            [
                sys.executable,
                str(SESSION_HOOK.with_name("wiki-log-reminder.py")),
                "--platform",
                "codex",
            ],
            cwd=REPO_ROOT,
            input=json.dumps(
                {
                    "tool_name": "apply_patch",
                    "tool_input": {"command": "*** Update File: wiki/overview.md\n"},
                }
            ),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        self.assertEqual(reminder.returncode, 0, reminder.stdout + reminder.stderr)
        reminder_payload = json.loads(reminder.stdout)
        self.assertEqual(
            reminder_payload["hookSpecificOutput"]["hookEventName"], "PostToolUse"
        )

    def test_framework_mode_allows_product_and_schema_paths(self) -> None:
        guard = load_guard()
        allowed = (
            "README.md",
            "docs/operations/setup/README.md",
            "samples/task-tracker/README.md",
            "tests/wiki/test_write_guard.py",
            "tools/release.py",
            "VERSION",
            "LICENSE.txt",
            "wiki/index.md",
            ".agents/skills/codebase-wiki/SKILL.md",
            ".codex/config.toml",
            ".github/copilot-instructions.md",
        )
        for path in allowed:
            with self.subTest(path=path):
                self.assertTrue(guard.is_allowed_path(path, "framework"))

    def test_target_mode_only_allows_wiki(self) -> None:
        guard = load_guard()
        self.assertTrue(guard.is_allowed_path("wiki/modules/orders.md", "target"))
        for path in (
            "README.md",
            "docs/operations/setup/README.md",
            "samples/task-tracker/README.md",
            "tests/wiki/test_write_guard.py",
            ".github/copilot-instructions.md",
            "src/orders/service.py",
        ):
            with self.subTest(path=path):
                self.assertFalse(guard.is_allowed_path(path, "target"))

    def test_wiki_only_alias_and_coexist_mode(self) -> None:
        guard = load_guard()
        self.assertTrue(guard.is_allowed_path("wiki/modules/orders.md", "wiki-only"))
        self.assertFalse(guard.is_allowed_path("src/orders/service.py", "wiki-only"))
        self.assertTrue(guard.is_allowed_path("src/orders/service.py", "coexist"))
        self.assertFalse(guard.is_allowed_path("../outside.py", "coexist"))

    def test_paths_outside_repository_are_denied(self) -> None:
        guard = load_guard()
        for path in ("../outside.md", "C:/outside.md", r"C:\outside.md"):
            with self.subTest(path=path):
                self.assertFalse(guard.is_allowed_path(path, "framework"))

    def test_audit_path_rejects_external_and_reparse_boundaries(self) -> None:
        import common

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            logs = root / "logs"
            logs.mkdir()
            candidate = logs / "audit.jsonl"
            with mock.patch.object(common, "repo_root", return_value=root):
                self.assertFalse(common.audit_path_is_safe(root.parent / "outside.jsonl"))
                with mock.patch.object(
                    common,
                    "_is_reparse_point",
                    side_effect=lambda path: path == logs,
                ):
                    self.assertFalse(common.audit_path_is_safe(candidate))


if __name__ == "__main__":
    unittest.main()
