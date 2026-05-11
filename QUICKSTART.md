# Quick Start Guide

Get `TuiDo365` installed and running in under 10 minutes.

---

## Step 1: Check Python

```bash
python3 --version
```

You need **Python 3.12 or newer**. If it's older, install a newer version first.

---

## Step 2: Download the code

```bash
git clone https://github.com/gripebomb/TuiDo365.git
cd TuiDo365
```

---

## Step 3: Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Your prompt should now show `(.venv)` at the beginning.

---

## Step 4: Install TuiDo365

```bash
pip install -e ".[dev]"
```

Wait for the install to finish. Verify it worked:

```bash
tuido --help
```

You should see a list of commands. If you get `command not found`, the virtual environment might not be active — run `source .venv/bin/activate` again.

---

## Step 5: Register your app in Microsoft Entra

`TuiDo365` needs a `client_id` from Microsoft to talk to your To Do data.

1. Go to [Microsoft Entra admin center](https://entra.microsoft.com/)
2. Click **Identity** → **Applications** → **App registrations** → **New registration**
3. Name it `TuiDo365`
4. Choose **Accounts in any organizational directory and personal Microsoft accounts**
5. Click **Register**
6. Copy the **Application (client) ID** — you'll need it in Step 6
7. Click **Authentication** → **Add a platform** → **Mobile and desktop applications**
8. Check `https://login.microsoftonline.com/common/oauth2/nativeclient` and click **Configure**
9. Click **API permissions** → **Add a permission** → **Microsoft Graph** → **Delegated permissions**
10. Add these two permissions:
    - `Tasks.ReadWrite`
    - `offline_access`
11. Click **Grant admin consent** (if you are an admin; otherwise you'll consent on first login)

---

## Step 6: Configure TuiDo365

Create the config file with your `client_id`:

```bash
mkdir -p ~/.config/mtd
cat > ~/.config/mtd/config.toml << EOF
client_id = "PASTE_YOUR_CLIENT_ID_HERE"
EOF
```

Replace `PASTE_YOUR_CLIENT_ID_HERE` with the ID you copied in Step 5.

---

## Step 7: Log in

```bash
tuido login
```

You'll see something like:

```
To sign in, use a web browser to open the page https://microsoft.com/devicelogin
and enter the code ABCDE1234 to authenticate.
```

1. Open that URL in any browser
2. Enter the code shown
3. Sign in with your Microsoft account
4. Accept the permissions
5. Return to your terminal — you should see `Login successful`

Your token is now saved at `~/.local/share/mtd/token_cache.bin`.

---

## Step 8: Try it out

```bash
# See your task lists
tuido lists

# See tasks in your default list
tuido tasks --list "Tasks"

# Add a task
tuido add --list "Tasks" --title "Buy groceries" --due $(date -d '+2 days' +%Y-%m-%d)
```

---

## Step 9: Launch the TUI (optional)

```bash
tuido tui
```

Use these keys inside the TUI:

| Key | Action |
|-----|--------|
| `r` | Refresh data |
| `Tab` | Move focus between panels |
| `q` | Quit |

---

## Common first-run issues

### `client_id is not configured`

You skipped Step 6 or pasted the wrong value. Double-check `~/.config/mtd/config.toml`.

### `Not authenticated. Run tuido login first.`

Run `tuido login` again. Your token may have expired.

### `Permission denied by Microsoft Graph.`

Go back to Step 5 and make sure you added `Tasks.ReadWrite` under **Delegated permissions**.

---

## Next steps

- Read the full [CLI reference](README.md#cli-reference)
- Read the [installation guide](INSTALLATION.md) for advanced config options
- Read the [architecture docs](docs/architecture.md) to understand the codebase
