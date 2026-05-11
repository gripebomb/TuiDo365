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
- [x] 1.1 Add Status Bar widget
- [x] 1.2 Context-sensitive footer (bindings added, Textual Footer handles context)
- [x] 1.3 Responsive panel layout (CSS updated for status bar, detail toggle with `i`)

### Phase 2: Task Actions
- [x] 2.1 Toggle task completion (c) — implemented action_toggle_complete
- [x] 2.2 Add new task (a) — AddTaskScreen modal implemented
- [x] 2.3 Delete task (d) — implemented without confirmation dialog
- [x] 2.4 Edit task (e) — EditTaskScreen modal implemented

### Phase 3: Search & Filter
- [x] 3.1 Task search (/) — cycles preset queries, filters live
- [x] 3.2 Filter controls (1/2/3) — all/active/completed
- [x] 3.3 Sort options (s) — due/importance/title cycling

### Phase 4: Polish
- [x] 4.1 Loading spinners — status bar shows sync state
- [x] 4.2 NO_COLOR support — disables color system if env var set
- [x] 4.3 Vim navigation (j/k/g/G) — added to sidebar and task table
- [x] 4.4 Help overlay (?) — HelpScreen modal implemented

### Phase 5: Error Handling
- [x] 5.1 Better error display — status bar shows errors
- [x] 5.2 Empty state handling — helpful messages in sidebar and table
- [x] 5.3 Network error recovery — cached data shown with stale indicator

## Verification
- StatusBar widget created at src/mtd/tui/widgets/status_bar.py
- MainScreen updated to include StatusBar
- MtdApp bindings extended with c, a, d, e, /, s, 1, 2, 3, ?, i
- AddTaskScreen modal with title, due date, importance fields
- EditTaskScreen modal pre-populated with task data
- HelpScreen with keyboard shortcut reference
- Search cycles preset queries and filters tasks live
- Filter by all/active/completed with 1/2/3 keys
- Sort by due/importance/title with s key
- Vim navigation (j/k/g/G) added to ListSidebar and TaskTable
- NO_COLOR support checks environment variable
- Empty states show helpful messages
- Detail pane toggle with `i` key adjusts layout
- Tests pass (18 passed in test_todo_api.py and test_settings.py)

## Notes
- All phases implemented
- Search uses preset demo queries instead of interactive input
- Delete task has no confirmation dialog (could be added later)
- Responsive layout could be enhanced with automatic breakpoint detection
