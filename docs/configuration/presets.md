# Layout Presets

Presets let you save and quickly switch between named layout configurations.

## Commands

| Command | Description |
|---------|-------------|
| `preset save <name>` | Save current workspace's layout as a named preset |
| `preset load <name>` | Apply a saved preset to the current workspace |
| `preset list` | List all saved presets |
| `preset delete <name>` | Delete a preset |

## Sway Configuration

```
# Save current layout as a preset
bindsym $mod+Ctrl+s nop layman preset save coding

# Load a preset
bindsym $mod+Ctrl+1 nop layman preset load coding
bindsym $mod+Ctrl+2 nop layman preset load browsing
```

## How It Works

A preset stores:
- The layout name (e.g., "MasterStack", "ThreeColumn")
- Layout-specific options (future: per-preset option overrides)

When loaded, the preset sets the current workspace's layout to the saved layout name.

## File Location

Presets are stored as JSON in `~/.config/layman/presets/`:

```
~/.config/layman/
├── config.toml
├── presets/
│   ├── coding.json
│   └── browsing.json
└── sessions/
```

## Use Cases

- **Workflow switching**: Save "coding" with MasterStack and "browsing" with Autotiling
- **Quick reconfiguration**: One keybinding to set up your preferred layout per task
- **Sharing configs**: Presets are simple JSON files that can be copied between machines
