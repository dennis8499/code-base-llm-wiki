from __future__ import annotations

from contextlib import contextmanager
import os
import shutil
import stat
import subprocess
import sys
import unittest
import uuid
from pathlib import Path


REPO_ROOT = Path(__file__).parents[2]
SKILL_ROOT = REPO_ROOT / ".agents" / "skills" / "codebase-wiki"
VALIDATOR = SKILL_ROOT / "scripts" / "validate-code-audit.py"
HISTORY_FIXTURE = REPO_ROOT / "tests" / "fixtures" / "code-audit" / "history"


def run_git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return result.stdout.strip()


def run_validator(report: Path, root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(VALIDATOR), str(report), "--repo-root", str(root), "--format", "json"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


@contextmanager
def workspace_temp() -> Path:
    """Use inherited workspace ACLs; Python 3.14 temp ACLs can be owner-only on Windows."""

    root = REPO_ROOT / f".code-audit-test-{uuid.uuid4().hex}"
    root.mkdir()
    try:
        yield root
    finally:
        def remove_readonly(function, path, _exc_info) -> None:
            try:
                os.chmod(path, stat.S_IWRITE)
                function(path)
            except OSError:
                pass

        shutil.rmtree(root, onerror=remove_readonly)


def valid_report(head: str) -> str:
    lines = [
        "---",
        'title: "Codebase 健檢：all"',
        "type: synthesis",
        'summary: "目前 source 與定向 Git history 的靜態檢查"',
        "sources:",
        "  - src/service.py",
        "derived_from: []",
        'source_digest: "sha256:' + "a" * 64 + '"',
        "last_updated: 2026-09-17",
        "tags: [synthesis, code-audit]",
        "status: active",
        "notebooklm_group: local-governance",
        "notebooklm_role: exclude",
        "---",
        "# Codebase 健檢：all",
        "<!-- codebase-wiki:managed:start -->",
        "## 結果摘要",
        "- 入口覆蓋：checked 1、partial 0、not checked 0",
        "- 確定缺陷：1；技術風險：0；待確認業務疑點：0",
        "## 檢查範圍與排除",
        "目前 source、設定與定向 history。",
        "## 入口覆蓋",
        "| 入口 | 類型 | 狀態 | 交易／一致性 | 設定／引用 | 邏輯／狀態 | 歷史交叉核對 |",
        "| --- | --- | --- | --- | --- | --- | --- |",
        "| `GET /service` | API | checked | checked | not applicable | checked | evidence-gap | `entry → service` | `none` |",
        "## 靜態交叉檢查",
        "| 類別 | 檢查內容 | 結果 | 證據／限制 |",
        "| --- | --- | --- | --- |",
        "| Transactions and side effects | transaction boundary | checked | source reviewed |",
        "| Configuration references | keys and fallback | checked | source reviewed |",
        "| Logic and state contracts | caller assumptions | checked | source reviewed |",
        "| Change completeness | current callers | evidence-gap | targeted history |",
        "## Git 歷史與變更線索",
        f"- HEAD：`{head}`",
        "- 工作樹：`clean`",
        "- 歷史可用性：`available`",
        "- 歷史查詢範圍：`current-first-targeted`",
        "- 使用的唯讀命令：`git rev-parse`、`git log`、`git show`、`git blame`",
        "- 深入閱讀的 commits：initial fixture 的完整內文與 diff",
        "- 歷史索引限制：候選索引不代表逐筆閱讀全部歷史",
        "| Commit（完整 40 字元 SHA） | 路徑／diff 位置 | Commit 意圖 | Diff 可證實的修改 | 目前 source 核對結果 |",
        "| --- | --- | --- | --- | --- |",
        f"| `{head}` | `src/service.py:1` | initial commit | service exists | current behavior |",
        "## 確定缺陷",
        "### BUG-001 — service result is wrong",
        "- 狀態：`open`",
        "- 證據確定度：`confirmed`",
        "- 影響程度：`low`",
        "- 受影響入口：`GET /service`",
        "- 可達觸發條件：呼叫入口。",
        "- 呼叫路徑：入口 → service。",
        "- 證據：`src/service.py:1` 顯示錯誤結果。",
        "- 已核對防護／反證：沒有防護可阻止錯誤結果。",
        f"- 歷史證據（若有）：`{head}`、`src/service.py:1` 的 diff hunk。",
        "- 預期行為／明確規則：回傳正確結果。",
        "- 實際行為與影響：回傳錯誤結果。",
        "- 修正方向（不執行修正）：修正 service。",
        "- 建議驗證案例：驗證入口回傳值。",
        "## 技術風險",
        "未發現需要技術風險確認的事項。",
        "## 待確認業務疑點",
        "未發現需要業務確認的事項。",
        "## 未完成工作與驗證建議",
        "無。",
        "## 相關頁面",
        "無。",
        "<!-- codebase-wiki:managed:end -->",
        "<!-- codebase-wiki:user-notes:start -->",
        "## 使用者筆記",
        "<!-- codebase-wiki:user-notes:end -->",
    ]
    return "\n".join(lines) + "\n"


def valid_v2_report(head: str) -> str:
    """A minimal functional-review report used to exercise the v2 contract."""

    report = valid_report(head)
    report = report.replace(
        'summary: "目前 source 與定向 Git history 的靜態檢查"\n',
        'summary: "目前 source 與定向 Git history 的靜態檢查"\n'
        "audit_report_version: 2\n",
    )
    report = report.replace(
        "- 入口覆蓋：checked 1、partial 0、not checked 0\n",
        "- 功能覆蓋：checked 1、partial 0、not checked 0\n"
        "- 入口覆蓋：checked 1、partial 0、not checked 0\n"
        "- finding 重跑狀態：new 1；still-present 0；rechecked-no-longer-observed 0；not-rechecked 0\n",
    )
    report = report.replace(
        "## 入口覆蓋\n",
        "## 功能 Review\n\n"
        "| 功能 ID | 功能／使用情境 | 相關入口 | 狀態 | 已檢查情境 | Findings | 未完成原因／限制 |\n"
        "| --- | --- | --- | --- | --- | --- | --- |\n"
        "| `FUNC-orders` | 查詢服務 | `GET /service` | checked | 正常、邊界、錯誤 | `BUG-001` | none |\n\n"
        "## 入口覆蓋\n",
    )
    report = report.replace(
        "| 入口 | 類型 | 狀態 | 交易／一致性 | 設定／引用 | 邏輯／狀態 | 歷史交叉核對 |\n"
        "| --- | --- | --- | --- | --- | --- | --- |\n"
        "| `GET /service` | API | checked | checked | not applicable | checked | evidence-gap | `entry → service` | `none` |",
        "| 功能 ID | 入口 | 類型 | 狀態 | 交易／一致性 | 設定／引用 | 邏輯／狀態 | 歷史交叉核對 | 追查路徑 | 未完成原因 |\n"
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n"
        "| `FUNC-orders` | `GET /service` | API | checked | checked | not applicable | checked | evidence-gap | `entry → service` | `none` |",
    )
    report = report.replace(
        "- 狀態：`open`\n",
        "- 狀態：`open`\n"
        "- 重跑狀態：`new`\n",
    )
    report = report.replace(
        "- 影響程度：`low`\n- 受影響入口：",
        "- 影響程度：`low`\n- 受影響功能：`FUNC-orders`\n- 受影響入口：",
    )
    return report


def shared_entry_v2_report(head: str) -> str:
    """A valid v2 report where two functions share one entrypoint."""

    report = valid_v2_report(head)
    report = report.replace(
        "- 功能覆蓋：checked 1、partial 0、not checked 0",
        "- 功能覆蓋：checked 2、partial 0、not checked 0",
    ).replace(
        "- 入口覆蓋：checked 1、partial 0、not checked 0",
        "- 入口覆蓋：checked 2、partial 0、not checked 0",
    )
    report = report.replace(
        "| `FUNC-orders` | 查詢服務 | `GET /service` | checked | 正常、邊界、錯誤 | `BUG-001` | none |\n\n## 入口覆蓋\n",
        "| `FUNC-orders` | 查詢服務 | `GET /service` | checked | 正常、邊界、錯誤 | `BUG-001` | none |\n"
        "| `FUNC-other` | 其他服務 | `GET /service` | checked | 正常 | none | none |\n\n## 入口覆蓋\n",
    )
    report = report.replace(
        "| `FUNC-orders` | `GET /service` | API | checked | checked | not applicable | checked | evidence-gap | `entry → service` | `none` |",
        "| `FUNC-orders` | `GET /service` | API | checked | checked | not applicable | checked | evidence-gap | `entry → service` | `none` |\n"
        "| `FUNC-other` | `GET /service` | API | checked | checked | not applicable | checked | evidence-gap | `entry → service` | `none` |",
    )
    return report


def mismatched_function_entry_v2_report(head: str) -> str:
    """A v2 report whose function row points to an entry owned by another function."""

    report = valid_v2_report(head)
    report = report.replace(
        "- 功能覆蓋：checked 1、partial 0、not checked 0",
        "- 功能覆蓋：checked 2、partial 0、not checked 0",
    ).replace(
        "- 入口覆蓋：checked 1、partial 0、not checked 0",
        "- 入口覆蓋：checked 2、partial 0、not checked 0",
    )
    report = report.replace(
        "| `FUNC-orders` | 查詢服務 | `GET /service` | checked | 正常、邊界、錯誤 | `BUG-001` | none |\n\n## 入口覆蓋\n",
        "| `FUNC-orders` | 查詢服務 | `GET /service` | checked | 正常、邊界、錯誤 | none | none |\n"
        "| `FUNC-other` | 其他服務 | `GET /other` | checked | 正常 | `BUG-001` | none |\n\n## 入口覆蓋\n",
    )
    report = report.replace(
        "| `FUNC-orders` | `GET /service` | API | checked | checked | not applicable | checked | evidence-gap | `entry → service` | `none` |",
        "| `FUNC-other` | `GET /service` | API | checked | checked | not applicable | checked | evidence-gap | `entry → service` | `none` |\n"
        "| `FUNC-other` | `GET /other` | API | checked | checked | not applicable | checked | evidence-gap | `entry → other` | `none` |",
    )
    return report.replace(
        "- 影響程度：`low`\n- 受影響功能：`FUNC-orders`",
        "- 影響程度：`low`\n- 受影響功能：`FUNC-other`",
    )


class CodeAuditValidatorTests(unittest.TestCase):
    def _init_git(self, root: Path) -> str:
        run_git(root, "init", "-q")
        run_git(root, "config", "user.name", "Code Audit Test")
        run_git(root, "config", "user.email", "audit@example.invalid")
        run_git(root, "add", ".")
        run_git(
            root,
            "-c", "user.name=Code Audit Test",
            "-c", "user.email=audit@example.invalid",
            "commit", "-qm", "initial fixture",
        )
        return run_git(root, "rev-parse", "HEAD")

    def test_validator_accepts_history_aware_report_and_current_sources(self) -> None:
        with workspace_temp() as root:
            (root / "src").mkdir()
            (root / "src/service.py").write_text("def service():\n    return 1\n", encoding="utf-8")
            (root / "wiki/synthesis").mkdir(parents=True)
            head = self._init_git(root)
            report = root / "wiki/synthesis/code-audit-all.md"
            report.write_text(valid_report(head), encoding="utf-8")
            result = run_validator(report, root)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_validator_accepts_functional_review_v2_report(self) -> None:
        with workspace_temp() as root:
            (root / "src").mkdir()
            (root / "src/service.py").write_text("def service():\n    return 1\n", encoding="utf-8")
            (root / "wiki/synthesis").mkdir(parents=True)
            head = self._init_git(root)
            report = root / "wiki/synthesis/code-audit-all.md"
            report.write_text(valid_v2_report(head), encoding="utf-8")
            result = run_validator(report, root)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_validator_accepts_functional_review_v2_multi_function_entrypoint(self) -> None:
        with workspace_temp() as root:
            (root / "src").mkdir()
            (root / "src/service.py").write_text("def service():\n    return 1\n", encoding="utf-8")
            (root / "wiki/synthesis").mkdir(parents=True)
            head = self._init_git(root)
            report = root / "wiki/synthesis/code-audit-all.md"
            report.write_text(shared_entry_v2_report(head), encoding="utf-8")
            result = run_validator(report, root)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_validator_rejects_functional_review_v2_mismatched_function_entrypoint(self) -> None:
        with workspace_temp() as root:
            (root / "src").mkdir()
            (root / "src/service.py").write_text("def service():\n    return 1\n", encoding="utf-8")
            (root / "wiki/synthesis").mkdir(parents=True)
            head = self._init_git(root)
            report = root / "wiki/synthesis/code-audit-all.md"
            report.write_text(mismatched_function_entry_v2_report(head), encoding="utf-8")
            result = run_validator(report, root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("function/entrypoint association is missing", result.stdout)
            self.assertIn("FUNC-orders", result.stdout)
            self.assertIn("GET /service", result.stdout)

    def test_validator_rejects_functional_review_v2_orphan_references_and_counts(self) -> None:
        with workspace_temp() as root:
            (root / "src").mkdir()
            (root / "src/service.py").write_text("def service():\n    return 1\n", encoding="utf-8")
            (root / "wiki/synthesis").mkdir(parents=True)
            head = self._init_git(root)
            report = root / "wiki/synthesis/code-audit-all.md"
            report.write_text(
                valid_v2_report(head)
                .replace("`FUNC-orders` | `GET /service`", "`FUNC-missing` | `GET /service`")
                .replace("- finding 重跑狀態：new 1；still-present 0；rechecked-no-longer-observed 0；not-rechecked 0", "- finding 重跑狀態：new 2；still-present 0；rechecked-no-longer-observed 0；not-rechecked 0"),
                encoding="utf-8",
            )
            result = run_validator(report, root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("unknown function ID", result.stdout)
            self.assertIn("rerun-state counts do not match", result.stdout)

    def test_validator_accepts_source_report_when_git_is_unavailable(self) -> None:
        with workspace_temp() as root:
            (root / "src").mkdir()
            (root / "src/service.py").write_text("def service():\n    return 1\n", encoding="utf-8")
            (root / "wiki/synthesis").mkdir(parents=True)
            report = root / "wiki/synthesis/code-audit-all.md"
            report_text = valid_report("unavailable")
            report_text = "\n".join(
                "- 歷史證據（若有）：無。" if "diff hunk" in line else line
                for line in report_text.splitlines()
            ) + "\n"
            report.write_text(
                report_text
                .replace("- 歷史可用性：`available`", "- 歷史可用性：`not-a-repository`")
                .replace("- 使用的唯讀命令：`git rev-parse`、`git log`、`git show`、`git blame`", "- 使用的唯讀命令：無（Git 不可用）")
                .replace("- 深入閱讀的 commits：initial fixture 的完整內文與 diff", "- 深入閱讀的 commits：無")
                .replace(
                    "| `unavailable` | `src/service.py:1` | initial commit | service exists | current behavior |\n",
                    "",
                ),
                encoding="utf-8",
            )
            result = run_validator(report, root)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_validator_requires_an_explicit_shallow_history_limitation(self) -> None:
        with workspace_temp() as root:
            (root / "src").mkdir()
            (root / "src/service.py").write_text("def service():\n    return 1\n", encoding="utf-8")
            (root / "wiki/synthesis").mkdir(parents=True)
            head = self._init_git(root)
            report = root / "wiki/synthesis/code-audit-all.md"
            report.write_text(
                valid_report(head).replace(
                    "- 歷史可用性：`available`",
                    "- 歷史可用性：`shallow`",
                ),
                encoding="utf-8",
            )
            result = run_validator(report, root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("shallow Git history must state", result.stdout)
            report.write_text(
                report.read_text(encoding="utf-8").replace(
                    "## 確定缺陷",
                    "歷史不完整：僅保留 shallow clone 的目前 HEAD。\n\n## 確定缺陷",
                ),
                encoding="utf-8",
            )
            result = run_validator(report, root)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_validator_rejects_missing_current_source(self) -> None:
        with workspace_temp() as root:
            (root / "wiki/synthesis").mkdir(parents=True)
            report = root / "wiki/synthesis/code-audit-all.md"
            report.write_text(valid_report("unavailable"), encoding="utf-8")
            result = run_validator(report, root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("source does not exist", result.stdout)

    def test_validator_rejects_wiki_sources_and_invalid_frontmatter_values(self) -> None:
        with workspace_temp() as root:
            (root / "wiki/synthesis").mkdir(parents=True)
            (root / "wiki/overview.md").write_text("# Wiki evidence\n", encoding="utf-8")
            report = root / "wiki/synthesis/code-audit-all.md"
            report.write_text(
                valid_report("unavailable")
                .replace("  - src/service.py", "  - wiki/overview.md")
                .replace("last_updated: 2026-09-17", "last_updated: 17-09-2026")
                .replace("status: active", "status: unknown"),
                encoding="utf-8",
            )
            result = run_validator(report, root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("raw repository evidence", result.stdout)
            self.assertIn("last_updated must be a YYYY-MM-DD date", result.stdout)
            self.assertIn("status must be active, stale, or placeholder", result.stdout)

    def test_validator_rejects_duplicate_finding_ids(self) -> None:
        with workspace_temp() as root:
            (root / "src").mkdir()
            (root / "src/service.py").write_text("def service():\n    return 1\n", encoding="utf-8")
            (root / "wiki/synthesis").mkdir(parents=True)
            head = self._init_git(root)
            report = root / "wiki/synthesis/code-audit-all.md"
            report.write_text(
                valid_report(head).replace(
                    "## 技術風險\n",
                    "### BUG-001 — duplicate\n## 技術風險\n",
                ),
                encoding="utf-8",
            )
            result = run_validator(report, root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("duplicate finding ID", result.stdout)

    def test_validator_keeps_user_notes_out_of_managed_finding_counts(self) -> None:
        with workspace_temp() as root:
            (root / "src").mkdir()
            (root / "src/service.py").write_text("def service():\n    return 1\n", encoding="utf-8")
            (root / "wiki/synthesis").mkdir(parents=True)
            head = self._init_git(root)
            report = root / "wiki/synthesis/code-audit-all.md"
            report.write_text(
                valid_report(head).replace(
                    "<!-- codebase-wiki:user-notes:end -->",
                    "### BUG-001 — user note retained on rerun\n- 原始筆記不可覆寫\n<!-- codebase-wiki:user-notes:end -->",
                ),
                encoding="utf-8",
            )
            result = run_validator(report, root)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_validator_accepts_risk_and_business_finding_contracts(self) -> None:
        with workspace_temp() as root:
            (root / "src").mkdir()
            (root / "src/service.py").write_text("def service():\n    return 1\n", encoding="utf-8")
            (root / "wiki/synthesis").mkdir(parents=True)
            head = self._init_git(root)
            report = root / "wiki/synthesis/code-audit-all.md"
            report_text = valid_report(head).replace(
                "確定缺陷：1；技術風險：0；待確認業務疑點：0",
                "確定缺陷：1；技術風險：1；待確認業務疑點：1",
            )
            report_text = report_text.replace(
                "## 技術風險\n未發現需要技術風險確認的事項。",
                """## 技術風險
### RISK-001 — framework boundary needs confirmation
- 狀態：`needs-technical-confirmation`
- 證據確定度：`unresolved`
- 影響程度：`low`
- 受影響入口：`GET /service`
- 成立條件：框架未替 caller 管理交易時。
- 可疑呼叫路徑：入口 → service。
- 目前觀察：`src/service.py:1` 有跨邊界操作。
- 已核對防護／反證：尚未找到 framework boundary。
- 缺少的證據：框架交易文件。
- 確認方式：閱讀框架文件。
- 修正方向（不執行修正）：確認 boundary。
- 建議驗證案例：核對失敗回復。
""",
            )
            report_text = report_text.replace(
                "## 待確認業務疑點\n未發現需要業務確認的事項。",
                """## 待確認業務疑點
### BIZ-001 — service result policy
- 狀態：`needs-business-confirmation`
- 證據確定度：`unresolved`
- 可能影響程度：`low`
- 受影響入口：`GET /service`
- 呼叫路徑：入口 → service。
- 目前行為：回傳 1。
- 已核對防護／反證：沒有政策 guard。
- 推論依據：`src/service.py:1`；這是推論。
- 尚未明確的預期政策：回傳值的業務意義。
- 需確認的業務問題：1 是否為正確結果？
- 確認不同答案可能造成的差異：caller 可能需要不同處理。
- 建議驗證案例：確認 caller 對結果的預期。
""",
            )
            report.write_text(report_text, encoding="utf-8")
            result = run_validator(report, root)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_validator_rejects_unlinked_entrypoint_and_history_location(self) -> None:
        with workspace_temp() as root:
            (root / "src").mkdir()
            (root / "src/service.py").write_text("def service():\n    return 1\n", encoding="utf-8")
            (root / "wiki/synthesis").mkdir(parents=True)
            head = self._init_git(root)
            report = root / "wiki/synthesis/code-audit-all.md"
            report.write_text(
                valid_report(head)
                .replace("- 受影響入口：`GET /service`", "- 受影響入口：`GET /missing`")
                .replace("src/service.py:1", "src/service.py")
                .replace("diff hunk", "history note"),
                encoding="utf-8",
            )
            result = run_validator(report, root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("affected entrypoint is missing", result.stdout)
            self.assertIn("historical evidence must name a diff/blame location", result.stdout)

    def test_history_fixture_records_deletion_and_contract_change_without_running_code(self) -> None:
        with workspace_temp() as directory:
            root = directory / "fixture"
            shutil.copytree(HISTORY_FIXTURE, root)
            legacy = root / "src/legacy_settlement.py"
            legacy.write_text(
                legacy.read_text(encoding="utf-8").replace(
                    "    with db.transaction():\n        db.write(\"settled\")\n    notifier.send(\"settled\")",
                    "    with db.transaction():\n        db.write(\"settled\")\n        notifier.send(\"settled\")",
                ),
                encoding="utf-8",
            )
            initial = self._init_git(root)
            rules = root / "docs/payment-rules.md"
            policy = root / "docs/payment-policy.md"
            rules.rename(policy)
            run_git(root, "add", "-A")
            run_git(
                root,
                "-c", "user.name=Code Audit Test",
                "-c", "user.email=audit@example.invalid",
                "commit", "-qm", "Rename payment rules\n\nKeep the rule body while changing its path.",
            )
            rename_commit = run_git(root, "rev-parse", "HEAD")
            (root / "config/payment.yml").unlink()
            run_git(root, "add", "-u")
            run_git(
                root,
                "-c", "user.name=Code Audit Test",
                "-c", "user.email=audit@example.invalid",
                "commit", "-qm", "Move payment settings to environment injection\n\nThe old file is removed after migration.",
            )
            deletion = run_git(root, "rev-parse", "HEAD")
            payments = root / "src/payments.py"
            payments.write_text(payments.read_text(encoding="utf-8") + "\n# reviewed diff\n", encoding="utf-8")
            run_git(root, "add", "src/payments.py")
            run_git(
                root,
                "-c", "user.name=Code Audit Test",
                "-c", "user.email=audit@example.invalid",
                "commit", "-qm", "Make payment notifications transactional\n\nKeep the payment operation atomic.",
            )
            transaction_commit = run_git(root, "rev-parse", "HEAD")
            legacy.write_text(
                legacy.read_text(encoding="utf-8").replace(
                    "    with db.transaction():\n        db.write(\"settled\")\n        notifier.send(\"settled\")",
                    "    with db.transaction():\n        db.write(\"settled\")\n    notifier.send(\"settled\")",
                ),
                encoding="utf-8",
            )
            run_git(root, "add", "src/legacy_settlement.py")
            run_git(
                root,
                "-c", "user.name=Code Audit Test",
                "-c", "user.email=audit@example.invalid",
                "commit", "-qm", "Fix settlement notification ordering\n\nKeep external effects after the database commit.",
            )
            fixed = run_git(root, "rev-parse", "HEAD")
            refunds = root / "src/refunds.py"
            refunds.write_text(
                refunds.read_text(encoding="utf-8")
                .replace(
                    "def refund_payment(payment_id: str, *, reason: str) -> None:",
                    "def refund_payment(payment_id: str, *, reason: str, actor: str) -> None:",
                ),
                encoding="utf-8",
            )
            run_git(root, "add", "src/refunds.py")
            run_git(
                root,
                "-c", "user.name=Code Audit Test",
                "-c", "user.email=audit@example.invalid",
                "commit", "-qm", "Require refund actor at the service boundary\n\nThe CLI caller must be updated with the new interface.",
            )
            interface_commit = run_git(root, "rev-parse", "HEAD")
            (root / "src/refund_cli.py").write_text(
                (root / "src/refund_cli.py").read_text(encoding="utf-8") + "\n# uncommitted audit fixture edit\n",
                encoding="utf-8",
            )
            log = run_git(root, "log", "--follow", "--format=%H%n%B", "--", "src/payments.py")
            renamed_log = run_git(root, "log", "--follow", "--name-status", "--format=%H%n%B", "--", "docs/payment-policy.md")
            deleted_diff = run_git(root, "show", "--format=fuller", deletion, "--", "config/payment.yml")
            transaction_diff = run_git(root, "show", "--format=fuller", "--patch", transaction_commit)
            transaction_parent = run_git(root, "show", f"{transaction_commit}^:src/payments.py")
            fixed_diff = run_git(root, "show", "--format=fuller", "--patch", fixed)
            interface_diff = run_git(root, "show", "--format=fuller", "--patch", interface_commit)
            blame = run_git(root, "blame", "src/payments.py")
            self.assertIn(initial, log)
            self.assertIn(transaction_commit, log)
            self.assertNotIn(rename_commit, log)
            self.assertIn(deletion, deleted_diff)
            self.assertIn(rename_commit, renamed_log)
            self.assertIn("R", renamed_log)
            self.assertIn("Move payment settings", run_git(root, "show", "-s", "--format=%B", deletion))
            self.assertIn("old file is removed", run_git(root, "show", "-s", "--format=%B", deletion))
            self.assertIn("Fix settlement notification ordering", run_git(root, "show", "-s", "--format=%B", fixed))
            self.assertIn("after the database commit", run_git(root, "show", "-s", "--format=%B", fixed))
            self.assertIn("Make payment notifications", run_git(root, "show", "-s", "--format=%B", transaction_commit))
            self.assertIn("Keep the payment operation atomic", run_git(root, "show", "-s", "--format=%B", transaction_commit))
            self.assertIn("Require refund actor", run_git(root, "show", "-s", "--format=%B", interface_commit))
            self.assertIn("CLI caller must be updated", run_git(root, "show", "-s", "--format=%B", interface_commit))
            self.assertIn("notifier.send_receipt", transaction_diff)
            self.assertIn("notifier.send_receipt", transaction_parent)
            self.assertIn("notifier.send(\"settled\")", fixed_diff)
            self.assertIn("actor: str", interface_diff)
            self.assertIn(transaction_commit[:8], blame)
            self.assertIn("M src/refund_cli.py", run_git(root, "status", "--short"))
            self.assertIn("docs/payment-rules.md", renamed_log)
            self.assertIn("docs/payment-policy.md", renamed_log)
            self.assertFalse((root / "config/payment.yml").exists())


if __name__ == "__main__":
    unittest.main()
