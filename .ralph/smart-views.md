# Smart Views: Important and Planned

## Goals
- Add "Important" and "Planned" virtual lists to the sidebar
- Important: shows high-importance tasks across all lists
- Planned: shows tasks with due dates across all lists
- Skip My Day (not available in Graph API)

## Checklist
- [ ] Add `get_all_tasks`, `get_important_tasks`, `get_planned_tasks` to TaskService
- [ ] Add virtual TaskList objects for Important and Planned
- [ ] Update sidebar to show virtual lists at top
- [ ] Handle virtual list selection in app (fetch from all lists)
- [ ] Update task table title to show current view
- [ ] Update help screen
- [ ] Tests pass

## Verification
- (to be filled)

## Notes
- Virtual lists use special IDs: `__important__` and `__planned__`
- Task completion/editing still works (uses task.list_id)
