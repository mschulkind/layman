# Session Management

Session management lets you save and restore workspace layouts, including which applications were open and their positions.

## Commands

All session commands use the `nop layman session <action>` format:

| Command | Description |
|---------|-------------|
| `session save [name]` | Save current session (default name: "default") |
| `session restore [name]` | Restore a saved session |
| `session list` | List all saved sessions |
| `session delete [name]` | Delete a saved session |

## Sway Configuration

```
bindsym $mod+Shift+s nop layman session save default
bindsym $mod+Shift+r nop layman session restore default
```

## How It Works

### Saving

When you save a session, layman captures:
- All workspace names and their active layout
- For each workspace: window `app_id`, `window_class`, position, and launch command
- A timestamp for when the session was saved

Sessions are stored as JSON files in `~/.config/layman/sessions/`.

### Restoring

When you restore a session, layman:
1. Reads the saved session data
2. For each workspace in the session:
   - Matches existing windows to saved slots by `app_id`/`window_class`
   - Optionally launches missing applications
   - Applies the saved layout

### Window Matching

Windows are matched to saved slots using:
1. Exact `app_id` match (case-insensitive)
2. Fallback to `window_class` match (case-insensitive)

## File Location

Sessions are stored in `~/.config/layman/sessions/`:

```
~/.config/layman/
├── config.toml
└── sessions/
    ├── default.json
    ├── coding.json
    └── gaming.json
```
