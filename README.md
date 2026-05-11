# TuiDo365

A Linux-first terminal application for Microsoft To Do built on Microsoft Graph.

`TuiDo365` provides two user surfaces from one shared core:

- a **scriptable CLI** for shell workflows
- an **interactive TUI** for day-to-day task management

## Features

- Authenticate with Microsoft Entra using device-code flow
- List, create, rename, and delete task lists
- List, add, update, complete, and delete tasks
- Offline read access from a local SQLite cache
- Sync freshness indicators
- Built-in list guardrails (protects default lists from accidental deletion)
- JSON output mode for scripting

## Quick start

### 1. Configure

Create `~/.config/mtd/config.toml`:

```toml
client_id = "YOUR_APP_ID"
```

Or set the environment variable:

```bash
export MTD_CLIENT_ID="YOUR_APP_ID"
```

To obtain a `client_id`, register an application in [Microsoft Entra](https://portal.azure.com/#blade/Microsoft_AAD_IAM/ActiveDirectoryMenuBlade/RegisteredApps) with the ** delegated permission** `Tasks.ReadWrite` and add a mobile/desktop platform.

### 2. Authenticate

```bash
tuido login
```

Follow the device-code flow instructions printed to your terminal.

### 3. Use

```bash
tuido lists
tuido tasks --list "Tasks"
tuido add --list "Tasks" --title "Buy milk" --due 2026-04-25
tuido done --list "Tasks" --task-id <id>
```

Launch the TUI:

```bash
tuido tui
```

## CLI reference

### Authentication

| Command | Description |
|---------|-------------|
| `tuido login` | Authenticate with device-code flow |
| `tuido logout` | Remove saved credentials |

### Task lists

| Command | Description |
|---------|-------------|
| `tuido lists [--json] [--offline]` | List all task lists |
| `tuido list-create --name <name>` | Create a new list |
| `tuido list-rename --name <name> --new-name <name>` | Rename a list |
| `tuido list-delete --name <name>` | Delete a list |

### Tasks

| Command | Description |
|---------|-------------|
| `tuido tasks --list <name> [--json] [--offline]` | List tasks in a list |
| `tuido add --list <name> --title <title> [--due YYYY-MM-DD] [--importance low\|normal\|high]` | Add a task |
| `tuido done --list <name> --task-id <id>` | Mark a task completed |
| `tuido update --list <name> --task-id <id> [--title ...] [--due ...] [--importance ...]` | Update a task |
| `tuido delete --list <name> --task-id <id>` | Delete a task |

### TUI

| Command | Description |
|---------|-------------|
| `tuido tui` | Launch the interactive terminal UI |

Keybindings in the TUI:
- `r` — refresh data
- `Tab` — cycle focus between panels
- `q` — quit

## Offline mode

`TuiDo365` caches task lists and tasks in a local SQLite database at `~/.local/share/mtd/cache.db`. After any successful Graph fetch, the cache is updated automatically.

To read from cache without contacting Graph:

```bash
tuido lists --offline
tuido tasks --list "Tasks" --offline
```

If Graph is unreachable during a normal (online) request, the CLI automatically falls back to cached data and shows the cache age in the output.

## Configuration

Linux paths:

| Purpose | Path |
|---------|------|
| Config | `~/.config/mtd/config.toml` |
| Token cache | `~/.local/share/mtd/token_cache.bin` |
| Local cache | `~/.local/share/mtd/cache.db` |
| Logs | `~/.local/state/mtd/app.log` |

Example `config.toml`:

```toml
tenant = "common"
client_id = "YOUR_APP_ID"
scopes = ["Tasks.ReadWrite", "offline_access"]

[ui]
date_format = "%Y-%m-%d"
default_list = "Tasks"
theme = "dark"

[cache]
enabled = true
ttl_seconds = 300
```

All top-level keys can also be set via environment variables prefixed with `MTD_` (e.g., `MTD_CLIENT_ID`, `MTD_UI__DEFAULT_LIST`).

## Local development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

Quality gates:

```bash
ruff check .
ruff format .
mypy src
pytest
```

## Architecture

See [`docs/architecture.md`](docs/architecture.md) for the layered architecture overview and module boundaries.

## License

MIT
