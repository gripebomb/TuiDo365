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
- [x] 1.3 Responsive panel layout (CSS updated for status bar)

### Phase 2: Task Actions
- [x] 2.1 Toggle task completion (c) — implemented action_toggle_complete
- [ ] 2.2 Add new task (a) — stub, needs modal screen
- [x] 2.3 Delete task (d) — implemented without confirmation dialog
- [ ] 2.4 Edit task (e) — stub, needs modal screen

### Phase 3: Search & Filter
- [ ] 3.1 Task search (/)
- [ ] 3.2 Filter controls (1/2/3)
- [ ] 3.3 Sort options (s)

### Phase 4: Polish
- [ ] 4.1 Loading spinners
- [ ] 4.2 NO_COLOR support
- [x] 4.3 Vim navigation (j/k/g/G) — added to sidebar and task table
- [ ] 4.4 Help overlay (?)

### Phase 5: Error Handling
- [ ] 5.1 Better error display (status bar shows errors now)
- [ ] 5.2 Empty state handling
- [ ] 5.3 Network error recovery

## Verification
- StatusBar widget created at src/mtd/tui/widgets/status_bar.py
- MainScreen updated to include StatusBar
- MtdApp bindings extended with c, a, d, e, /, s, 1, 2, 3, ?, i
- action_toggle_complete implemented
- action_delete_task implemented (no confirmation yet)
- Vim navigation (j/k/g/G) added to ListSidebar and TaskTable
- Tests pass (18 passed in test_todo_api.py and test_settings.py)

## Notes
- Phase 1 mostly complete
- Next: implement Add Task and Edit Task modal screens
- Then: search, filter, sort
- Help overlay can use simple Textual Screen with Static content
