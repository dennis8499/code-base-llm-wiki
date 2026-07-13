---
name: update-index
description: >
  重新掃描 wiki/ 目錄，重建 index.md 索引頁——確保索引
  與實際 wiki 頁面完全同步。
agent: "wiki-keeper"
argument-hint: "可選：補充這次重建索引的原因或範圍"
---

## 任務

重新掃描 `wiki/` 目錄，重建 `wiki/index.md`。

## 流程

1. 列出 `wiki/` 下所有 `.md` 檔案（遞迴掃描子目錄）
2. 逐頁讀取 frontmatter（title, type, status）
3. 擷取每頁的第一句摘要
4. 按 type 分類，重建 index.md 的各 section
5. 追加 `wiki/log.md` 條目：`## [YYYY-MM-DD] update | 重建索引`

## 替代方式

也可以直接執行腳本：

```
python .agents/skills/codebase-wiki/scripts/rebuild-index.py wiki/
```

腳本會自動掃描並重建 index.md。
