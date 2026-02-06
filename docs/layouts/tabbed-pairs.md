# TabbedPairs Layout

TabbedPairs groups windows into tabbed pairs, useful for side-by-side code/preview workflows.

## How It Works

- Windows are arranged in horizontal pairs
- Each pair is displayed as a tabbed container
- Unpaired windows are shown individually alongside pairs
- Auto-pairing matches windows by `app_id` using configurable rules
- Manual pairing lets you pair any two windows on demand

## Visual Example

```
┌──────────────┬──────────────┬──────────┐
│ ┌────┬─────┐ │ ┌────┬─────┐ │          │
│ │ Ed │ Term│ │ │ Br │ Docs│ │ Unpaired │
│ └────┴─────┘ │ └────┴─────┘ │          │
└──────────────┴──────────────┴──────────┘
  Pair 1           Pair 2        Solo
```

## Configuration

```toml
[layman]
defaultLayout = "TabbedPairs"

# Auto-pairing rules: key = app_id to match, value = list of partner app_ids
[layman.pairRules]
nvim = ["code", "terminal", "alacritty"]
firefox = ["slack", "discord"]
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `pairRules` | table | `{}` | Auto-pairing rules: `{app_id = [partner_ids...]}` |

## Commands

| Command | Description |
|---------|-------------|
| `window focus left` | Focus previous pair |
| `window focus right` | Focus next pair |
| `window focus up` | Focus primary window within pair |
| `window focus down` | Focus secondary window within pair |
| `window move left` | Swap pair ordering left |
| `window move right` | Swap pair ordering right |
| `pair` | Start manual pairing (next window opened pairs with this one) |
| `unpair` | Break the pair containing the focused window |
| `layout maximize` | Toggle tabbed maximize across all windows |

## Auto-Pairing

When a new window opens, layman checks if its `app_id` matches any rule key. If so, it searches unpaired windows for one whose `app_id` matches any of the partner values, and automatically creates a pair.

**Example**: With the rule `nvim = ["terminal"]`:
1. Open a terminal → it becomes unpaired
2. Open nvim → layman sees nvim matches the rule key, finds the unpaired terminal, creates a pair

## Manual Pairing

1. Focus the first window
2. Run `nop layman pair`
3. Open or focus the second window → they are automatically paired
4. To cancel, run `nop layman pair` again on the same window

## Sway Configuration Example

```
bindsym $mod+h nop layman window focus left
bindsym $mod+l nop layman window focus right
bindsym $mod+k nop layman window focus up
bindsym $mod+j nop layman window focus down

bindsym $mod+Shift+h nop layman window move left
bindsym $mod+Shift+l nop layman window move right

bindsym $mod+p nop layman pair
bindsym $mod+Shift+p nop layman unpair
```
