# TUI Improvements Implementation

Implement the TUI improvement plan from docs/TUI-improvement-plan.md.

## Goals
- Make the TUI keyboard-first with contextual bindings
- Add status bar, footer, and responsive layout
- Implement task actions (complete, add, delete, edit)
- Add search, filter, and sort
- Add polish (help overlay, NO_COLOR, vim nav)

## Checklist

### Phase 1: Foundation
- [x] 1.1 Add Status Bar widget — `src/mtd/tui/widgets/status_bar.py`
- [x] 1.2 Context-sensitive footer — bindings added to MtdApp
- [x] 1.3 Responsive panel layout — CSS updated, detail toggle with `i`

### Phase 2: Task Actions
- [x] 2.1 Toggle task completion (c) — `action_toggle_complete()`
- [x] 2.2 Add new task (a) — `AddTaskScreen` modal
- [x] 2.3 Delete task (d) — `action_delete_task()`
- [x] 2.4 Edit task (e) — `EditTaskScreen` modal

### Phase 3: Search & Filter
- [x] 3.1 Task search (/) — cycles queries, filters live
- [x] 3.2 Filter controls (1/2/3) — all/active/completed
- [x] 3.3 Sort options (s) — due/importance/title cycling

### Phase 4: Polish
- [x] 4.1 Loading spinners — status bar sync indicator
- [x] 4.2 NO_COLOR support — checks env var
- [x] 4.3 Vim navigation (j/k/g/G) — sidebar and table
- [x] 4.4 Help overlay (?) — `HelpScreen` modal

### Phase 5: Error Handling
- [x] 5.1 Better error display — status bar shows errors
- [x] 5.2 Empty state handling — helpful messages
- [x] 5.3 Network error recovery — cached data + stale indicator

## Verification
- [x] StatusBar widget renders sync time and counts
- [x] AddTaskScreen modal creates tasks with title/due/importance
- [x] EditTaskScreen modal updates task fields
- [x] HelpScreen shows all keyboard shortcuts
- [x] Search (/) filters tasks by title
- [x] Filter (1/2/3) shows all/active/completed
- [x] Sort (s) cycles due/importance/title
- [x] Vim nav (j/k/g/G) works in sidebar and table
- [x] NO_COLOR disables colors
- [x] Empty states show actionable messages
- [x] Detail pane toggles with `i`
- [x] All tests pass (18 passed)

## Notes
- Implementation complete across all 5 phases
- Committed and pushed to main
- Remaining enhancements: interactive search input, delete confirmation, auto-breakpoints
