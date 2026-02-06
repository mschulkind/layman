# Window Rules

Window rules let you automatically apply actions to windows based on their `app_id` or `window_class`. Rules are evaluated when a window is created.

## Configuration

Rules are defined as a top-level `[[rules]]` array in `config.toml`:

```toml
[[rules]]
match_app_id = "pavucontrol"
floating = true

[[rules]]
match_app_id = "Zoom"
exclude = true

[[rules]]
match_window_class = "Steam"
workspace = "gaming"

[[rules]]
match_title = "Picture-in-Picture"
floating = true
```

## Rule Options

| Field | Type | Description |
|-------|------|-------------|
| `match_app_id` | string | Match window's `app_id` (Wayland). Case-insensitive substring. |
| `match_window_class` | string | Match window's `window_class` (X11). Case-insensitive substring. |
| `match_title` | string | Match window's title. Case-insensitive substring. |
| `floating` | bool | If true, enable floating for matched windows |
| `exclude` | bool | If true, exclude window from layout management |
| `workspace` | string | Move matched window to specified workspace |

## Evaluation Order

1. Rules are evaluated in order from top to bottom
2. The **first matching rule** with an action wins
3. Actions are mutually exclusive: only one of `floating`, `exclude`, or `workspace` is applied
4. If no rules match, the window is handled normally by the layout manager

## Reloading Rules

Rules are reloaded when you run the `reload` command:

```
bindsym $mod+Shift+c nop layman reload
```
