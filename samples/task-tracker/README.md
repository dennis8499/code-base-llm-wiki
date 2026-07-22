# Task Tracker Sample

這是一個專為 Codebase LLM Wiki E2E 驗證設計的小型 Python codebase，只使用標準函式庫。

## Domain

- `TaskItem` 表示待辦事項，狀態只能是 `open` 或 `completed`。
- `TaskRepository` 隔離儲存介面；`InMemoryTaskRepository` 提供可執行實作。
- `TaskTrackerSettings` 從 JSON 讀取 open-task 上限與預設期限。
- `TaskTrackerService` 建立、完成、查詢和判斷逾期任務，並注入 clock 與 UUID factory 以保持可測試性。

## 重要規則

- 標題去除前後空白後不得為空。
- 未指定期限時使用 `default_due_days`。
- 未完成任務數量不得超過 `max_open_tasks`。
- 不存在的任務不能完成；已完成任務不能再次完成。
- `due_at` 早於目前時間且狀態仍為 open 才算逾期。

## 執行快速檢查

從本目錄執行：

```powershell
python -m unittest discover -s tests -v
```

完整 Wiki workflow 請從上一層 [samples/README.md](../README.md) 開始。

