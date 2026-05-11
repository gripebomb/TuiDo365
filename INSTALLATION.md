# Installation Guide

This guide covers everything needed to install, configure, and run `TuiDo365` on Linux.

## Prerequisites

- **Python 3.12 or newer**
- **A Microsoft account** (personal, work, or school)
- **A registered application in Microsoft Entra** (see below)

Verify your Python version:

```bash
python3 --version
```

## Register an application in Microsoft Entra

`TuiDo365` uses delegated permissions and device-code flow. You must register your own application to obtain a `client_id`.

1. Go to [Microsoft Entra admin center](https://entra.microsoft.com/) → **Identity** → **Applications** → **App registrations** → **New registration**.
2. Enter a name (e.g., `TuiDo365-cli`).
3. Under **Supported account types**, select **Accounts in any organizational directory (multitenant) and personal Microsoft accounts**.
4. Click **Register**.
5. On the overview page, copy the **Application (client) ID** — this is your `client_id`.
6. Go to **Authentication** → **Add a platform** → **Mobile and desktop applications**.
7. Check the redirect URI `https://login.microsoftonline.com/common/oauth2/nativeclient` and click **Configure**.
8. Go to **API permissions** → **Add a permission** → **Microsoft Graph** → **Delegated permissions**.
9. Search for and add `Tasks.ReadWrite`.
   The `offline_access` scope is always requested automatically by the MSAL library and does not need to be added manually.
10. Click **Grant admin consent** if you are an admin, or the user will consent on first login.

## Install from source

### 1. Clone the repository

```bash
git clone https://github.com/gripebomb/TuiDo365.git
cd TuiDo365
```

### 2. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install in editable mode

```bash
pip install -e ".[dev]"
```

This installs the `mtd` console script and all runtime and development dependencies.

### 4. Verify the installation

```bash
tuido --help
```

You should see the full command list including `login`, `logout`, `lists`, `tasks`, `add`, `tui`, etc.

## Configure the application

Create the configuration directory and file:

```bash
mkdir -p ~/.config/tuido
cat > ~/.config/mtd/config.toml << 'EOF'
client_id = "YOUR_APP_ID"
EOF
```

Replace `YOUR_APP_ID` with the value copied from Microsoft Entra.

### Alternative: environment variable

If you prefer not to use a config file, set the environment variable:

```bash
export MTD_CLIENT_ID="YOUR_APP_ID"
```

Add this line to your shell profile (`~/.bashrc`, `~/.zshrc`, etc.) to make it persistent.

### Optional configuration

```toml
client_id = "YOUR_APP_ID"
tenant = "common"                    # or your specific tenant ID
scopes = ["Tasks.ReadWrite"]

[ui]
date_format = "%Y-%m-%d"
default_list = "Tasks"
theme = "dark"

[cache]
enabled = true
ttl_seconds = 300
```

All top-level keys can be overridden via environment variables prefixed with `MTD_`:

| Config key | Environment variable |
|-----------|----------------------|
| `client_id` | `MTD_CLIENT_ID` |
| `tenant` | `MTD_TENANT` |
| `ui.date_format` | `MTD_UI__DATE_FORMAT` |
| `cache.enabled` | `MTD_CACHE__ENABLED` |

## Authenticate

Run the login command and follow the instructions:

```bash
tuido login
```

1. A URL and user code are printed to the terminal.
2. Open the URL in a browser (on any device).
3. Enter the user code.
4. Sign in with your Microsoft account and consent to the permissions.
5. Return to the terminal — you should see a success message.

Your access token is cached in `~/.local/share/mtd/token_cache.bin`. You only need to log in again when the token expires and cannot be refreshed silently.

## Verify everything works

```bash
# List your task lists
tuido lists

# List tasks in the default "Tasks" list
tuido tasks --list "Tasks"

# Add a test task
tuido add --list "Tasks" --title "Hello from TuiDo365" --due $(date -d '+1 day' +%Y-%m-%d)
```

## Launch the TUI

```bash
tuido tui
```

Keybindings:

| Key | Action |
|-----|--------|
| `r` | Refresh data from Microsoft Graph |
| `Tab` | Cycle focus between panels |
| `q` | Quit |

## Upgrade

Pull the latest code and reinstall:

```bash
git pull origin main
source .venv/bin/activate
pip install -e ".[dev]"
```

## Uninstall

```bash
source .venv/bin/activate
pip uninstall tuido365
```

Remove local data if desired:

```bash
rm -rf ~/.config/tuido
rm -rf ~/.local/share/tuido
rm -rf ~/.local/state/tuido
```

## Troubleshooting

### `client_id is not configured`

The `client_id` is missing. Create `~/.config/mtd/config.toml` with your Application ID, or set `MTD_CLIENT_ID`.

### `Not authenticated. Run tuido login first.`

Your token cache is empty or expired. Run `tuido login` again.

### `Permission denied by Microsoft Graph.`

The application registration is missing the `Tasks.ReadWrite` delegated permission, or admin consent has not been granted. Check step 9 of the app registration instructions above.

### `Network error contacting Graph`

Check your internet connection. If the cache is populated, `TuiDo365` automatically falls back to cached data and shows the cache age. You can also use `--offline` to read from cache intentionally:

```bash
tuido lists --offline
tuido tasks --list "Tasks" --offline
```

### TUI shows `client_id not configured`

The TUI reads the same configuration as the CLI. Ensure `~/.config/mtd/config.toml` exists or `MTD_CLIENT_ID` is exported in the shell where you launch `tuido tui`.

### Data paths

| Purpose | Path |
|---------|------|
| Config | `~/.config/mtd/config.toml` |
| Token cache | `~/.local/share/mtd/token_cache.bin` |
| SQLite cache | `~/.local/share/mtd/cache.db` |
| Logs | `~/.local/state/mtd/app.log` |
