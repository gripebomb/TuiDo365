# TUI Improvement Implementation Plan

## Overview

This document outlines a phased plan to improve the TuiDo365 terminal user interface based on design best practices and user feedback. The changes progress from foundational improvements (layout, status, keyboard) to advanced features (task actions, search, filtering).

---

## Phase 1: Foundation (Status Bar, Footer, Responsive Layout)

### 1.1 Add Status Bar Widget
**File:** `src/mtd/tui/widgets/status_bar.py`

Create a dedicated status bar widget that displays:
- Last sync timestamp (e.g., "Synced 2 min ago")
- Current list/task counts (e.g., "3 lists | 12 tasks")
- Online/offline indicator
- Error state when applicable

**Benefits:** Users know if data is fresh and whether operations succeed.

**Acceptance Criteria:**
- [ ] Status bar updates when lists/tasks refresh
- [ ] Shows "Offline" when network errors occur
- [ ] Shows relative time ("2 min ago", "just now")
- [ ] Doesn't break existing layout

### 1.2 Context-Sensitive Footer
**File:** `src/mtd/tui/widgets/context_footer.py` or modify `MainScreen`

Replace generic Footer with a context-aware footer that shows different bindings based on:
- Which panel has focus (sidebar, task table, detail pane)
- Whether a task is selected
- Whether an error is displayed

**Example footer states:**
```
Default:          [q]uit [r]efresh [Tab]focus [?]help
Task selected:    [q]uit [c]omplete [a]dd [d]elete [Tab]focus
Sidebar focused:  [q]uit [r]efresh [Enter]select [Tab]focus
Error state:      [q]uit [r]etry [Tab]focus
```

**Acceptance Criteria:**
- [ ] Footer updates when focus changes between panels
- [ ] Footer updates when task selection changes
- [ ] Footer updates when error state changes
- [ ] All existing bindings still work

### 1.3 Responsive Panel Layout
**File:** `src/mtd/tui/app.py` (CSS), `src/mtd/tui/screens/main_screen.py`

Make the three-panel layout responsive:
- Minimum terminal size: 80×24
- Below 100 columns: collapse detail pane to overlay (triggered by `i` key)
- Below 80 columns: show "Terminal too small" message
- Sidebar minimum width: 20 columns
- Task table minimum width: 30 columns

**Acceptance Criteria:**
- [ ] Layout adjusts at 100-column breakpoint
- [ ] Detail pane can be toggled with `i` key
- [ ] "Terminal too small" shown below 80 columns
- [ ] No crashes on resize

---

## Phase 2: Task Actions (Create, Complete, Edit, Delete)

### 2.1 Toggle Task Completion
**File:** `src/mtd/tui/app.py`, `src/mtd/tui/widgets/task_table.py`

Add `c` keybinding to toggle task completion status.

**Implementation:**
1. Add `action_toggle_complete()` to `MtdApp`
2. Call `task_service.update_task()` to set status to `completed` or `notStarted`
3. Refresh task list after update
4. Provide visual feedback (brief flash in status bar)

**Acceptance Criteria:**
- [ ] `c` key toggles completion on selected task
- [ ] Visual feedback shown (status bar message)
- [ ] Task table updates to show ✓ or blank
- [ ] Error handled gracefully (show message, don't crash)

### 2.2 Add New Task
**File:** `src/mtd/tui/screens/`, `src/mtd/tui/app.py`

Add `a` keybinding to open a task creation dialog.

**Implementation:**
1. Create `AddTaskScreen` modal dialog
2. Form fields: Title (required), Due date (optional), Importance (optional)
3. Submit creates task via `task_service.create_task()`
4. Close and refresh task list

**Modal layout:**
```
┌─ Add Task ─────────────┐
│ Title: [______________]│
│ Due:   [______________]│
│ Importance: [normal ▼] │
│                        │
│ [Save]  [Cancel]       │
└────────────────────────┘
```

**Acceptance Criteria:**
- [ ] `a` key opens modal from any panel
- [ ] Title field is required
- [ ] Due date accepts YYYY-MM-DD format
- [ ] Importance defaults to "normal"
- [ ] ESC or Cancel closes without saving
- [ ] Save adds task and refreshes list

### 2.3 Delete Task with Confirmation
**File:** `src/mtd/tui/app.py`

Add `d` keybinding to delete selected task.

**Implementation:**
1. Show inline confirmation: "Delete 'Task Title'? [y]es [n]o"
2. On `y`, call `task_service.delete_task()`
3. On `n` or ESC, cancel
4. Refresh task list

**Acceptance Criteria:**
- [ ] `d` key shows confirmation prompt
- [ ] `y` confirms deletion
- [ ] `n` or ESC cancels
- [ ] Task list refreshes after deletion
- [ ] Status bar shows "Task deleted" confirmation

### 2.4 Edit Task
**File:** `src/mtd/tui/screens/`, `src/mtd/tui/app.py`

Add `e` keybinding to edit selected task.

**Implementation:**
1. Create `EditTaskScreen` modal (similar to AddTaskScreen)
2. Pre-populate fields with current task values
3. PATCH only changed fields
4. Refresh task list and detail pane

**Acceptance Criteria:**
- [ ] `e` key opens edit modal for selected task
- [ ] Fields pre-populated with current values
- [ ] Only changed fields sent to API
- [ ] Cancel discards changes
- [ ] Save updates task and refreshes display

---

## Phase 3: Search, Filter, and Sort

### 3.1 Task Search
**File:** `src/mtd/tui/widgets/task_table.py`, `src/mtd/tui/app.py`

Add `/` keybinding to search tasks by title.

**Implementation:**
1. Show search input bar above task table
2. Filter tasks live as user types (fuzzy match)
3. `n` / `N` to cycle through matches
4. `Esc` to clear search

**Acceptance Criteria:**
- [ ] `/` key shows search bar
- [ ] Typing filters tasks live
- [ ] `n` jumps to next match
- [ ] `Esc` clears filter and shows all tasks
- [ ] Search works across all tasks in current list

### 3.2 Filter Controls
**File:** `src/mtd/tui/widgets/task_table.py`

Add filter toggle buttons above the task table:
- `[All]` `[Active]` `[Completed]` — filter by status
- Visual indicator shows active filter

**Keyboard shortcuts:**
- `1` — All tasks
- `2` — Active (not completed)
- `3` — Completed

**Acceptance Criteria:**
- [ ] Filter buttons render above table
- [ ] Click or key switches filter
- [ ] Active filter highlighted
- [ ] Table updates immediately

### 3.3 Sort Options
**File:** `src/mtd/tui/widgets/task_table.py`

Allow sorting tasks by different columns:
- Due date (ascending) — default
- Importance (high → low)
- Title (A → Z)
- Created date (newest first)

**Keyboard shortcuts:**
- `s` — cycle sort mode
- Status bar shows current sort: "Sort: due date ↑"

**Acceptance Criteria:**
- [ ] `s` cycles through sort modes
- [ ] Sort indicator shown in status bar
- [ ] Table re-sorts immediately
- [ ] Sort preference persists during session

---

## Phase 4: Polish and Accessibility

### 4.1 Loading Spinners
**File:** `src/mtd/tui/app.py`

Add loading indicators for async operations:
- Show spinner in status bar after 200ms delay
- Operations: refresh lists, refresh tasks, create task, update task, delete task
- Spinner disappears when operation completes

**Acceptance Criteria:**
- [ ] Spinner appears after 200ms delay
- [ ] Spinner disappears on completion or error
- [ ] Doesn't flicker on fast operations
- [ ] Doesn't block keyboard input

### 4.2 NO_COLOR Support
**File:** `src/mtd/tui/app.py`

Check `NO_COLOR` environment variable and disable colors if set.

**Implementation:**
1. In `MtdApp.__init__`, check `os.environ.get("NO_COLOR")`
2. If set, use monochrome CSS or override theme

**Acceptance Criteria:**
- [ ] Setting `NO_COLOR=1` disables all colors
- [ ] Interface remains usable in monochrome
- [ ] Semantic meaning preserved via symbols/bold/italic

### 4.3 Keyboard Navigation Improvements
**File:** `src/mtd/tui/widgets/*.py`

Add vim-style navigation within panels:
- `j` / `k` — move down/up in task table and sidebar
- `g` / `G` — jump to top/bottom
- `Enter` — select item (same as current behavior)

**Acceptance Criteria:**
- [ ] `j`/`k` work in sidebar and task table
- [ ] `g`/`G` jump to first/last item
- [ ] Doesn't conflict with existing bindings

### 4.4 Help Overlay
**File:** `src/mtd/tui/screens/help_screen.py`

Add `?` keybinding to show full keyboard shortcut reference.

**Layout:** Modal overlay showing all available shortcuts organized by context:
```
┌─ Keyboard Shortcuts ─────────────────┐
│ Navigation                            │
│   j/k or ↑/↓    Move up/down          │
│   g/G           Jump to top/bottom    │
│   Tab           Cycle focus           │
│                                       │
│ Actions                               │
│   r             Refresh data          │
│   a             Add new task          │
│   c             Toggle complete       │
│   e             Edit task             │
│   d             Delete task           │
│                                       │
│ Search & Filter                       │
│   /             Search tasks          │
│   1/2/3         Filter all/active/done│
│   s             Change sort           │
│                                       │
│ [Press any key to close]              │
└───────────────────────────────────────┘
```

**Acceptance Criteria:**
- [ ] `?` key opens help overlay
- [ ] Any key closes overlay
- [ ] Help content is accurate and complete
- [ ] Overlay doesn't interfere with background state

---

## Phase 5: Error Handling and Edge Cases

### 5.1 Better Error Display
**File:** `src/mtd/tui/widgets/status_bar.py`

Replace the current error_message reactive with proper error toasts:
- Brief error message in status bar (3-5 seconds)
- Persistent error indicator for unresolvable errors
- Clear error with `r` (refresh) or any action

**Acceptance Criteria:**
- [ ] Errors show in status bar briefly
- [ ] Critical errors persist until resolved
- [ ] Error doesn't block the UI
- [ ] Refresh clears non-critical errors

### 5.2 Empty State Handling
**File:** `src/mtd/tui/widgets/task_table.py`, `src/mtd/tui/widgets/list_sidebar.py`

Show helpful messages when no data exists:
- No lists: "No task lists found. Create one with `tuido lists --add 'My List'`"
- No tasks in list: "No tasks in this list. Press `a` to add one."
- Empty search results: "No tasks match 'query'. Press `Esc` to clear."

**Acceptance Criteria:**
- [ ] Empty states show helpful text
- [ ] Text includes actionable hints
- [ ] Empty state clears when data appears

### 5.3 Network Error Recovery
**File:** `src/mtd/tui/app.py`

Improve handling of network errors:
- Show cached data with stale indicator
- Auto-retry on transient errors (exponential backoff)
- Manual retry with `r` key

**Acceptance Criteria:**
- [ ] Cached data shown when network fails
- [ ] Stale indicator visible
- [ ] `r` retries the failed operation
- [ ] No crash on network timeout

---

## Implementation Order

Recommended sequence to minimize merge conflicts and provide incremental value:

| Week | Phase | Tasks |
|------|-------|-------|
| 1 | 1.1, 1.2 | Status bar, context footer |
| 2 | 1.3, 2.1 | Responsive layout, toggle complete |
| 3 | 2.2, 2.3 | Add task, delete task |
| 4 | 2.4, 3.1 | Edit task, search |
| 5 | 3.2, 3.3 | Filter, sort |
| 6 | 4.1, 4.2, 4.3 | Loading spinners, NO_COLOR, vim nav |
| 7 | 4.4, 5.x | Help overlay, error handling |

---

## Testing Strategy

Each phase should include:

1. **Unit tests** for new widgets and actions
2. **Integration tests** for screen flows (add → verify → delete)
3. **Manual testing** at 80×24, 120×40, and 200×60 terminal sizes
4. **Accessibility check** with `NO_COLOR=1`

---

## Files to Create/Modify

### New Files
```
src/mtd/tui/widgets/status_bar.py
src/mtd/tui/widgets/context_footer.py
src/mtd/tui/screens/add_task_screen.py
src/mtd/tui/screens/edit_task_screen.py
src/mtd/tui/screens/help_screen.py
```

### Modified Files
```
src/mtd/tui/app.py              — Add actions, bindings, responsive CSS
src/mtd/tui/screens/main_screen.py — Add status bar, filter controls
src/mtd/tui/widgets/task_table.py  — Add search, filter, sort
src/mtd/tui/widgets/list_sidebar.py — Add vim navigation
src/mtd/tui/widgets/task_detail.py  — Minor polish
```

---

## Success Metrics

- [ ] All actions accessible via keyboard (no mouse required)
- [ ] Context-sensitive footer shows relevant bindings
- [ ] Status bar communicates sync state and errors
- [ ] Help overlay documents all shortcuts
- [ ] Works at 80×24 with `NO_COLOR=1`
- [ ] No crashes on network errors or empty data
