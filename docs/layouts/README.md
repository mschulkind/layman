# Layout Managers

This section documents each layout manager included with layman.

## Contents

| File | Description |
|------|-------------|
| [autotiling.md](autotiling.md) | Autotiling (spiral) layout |
| [master-stack.md](master-stack.md) | Master + Stack layout |
| [grid.md](grid.md) | Grid layout |
| [custom-layouts.md](custom-layouts.md) | Creating custom layouts |

## Layout Comparison

| Layout | Description | Use Case |
|--------|-------------|----------|
| `none` | No management | Manual control |
| `Autotiling` | Spiral tiling | General purpose |
| `MasterStack` | Master + stack | Focus on one main window |
| `Grid` | Grid pattern | Equal window importance |

## Visual Comparison

### Autotiling

```
┌─────────────┬─────────────┐
│             │      2      │
│      1      ├──────┬──────┤
│             │  3   │  4   │
└─────────────┴──────┴──────┘
```

### MasterStack

```
┌─────────────┬─────────────┐
│             │      2      │
│      1      ├─────────────┤
│  (master)   │      3      │
│             ├─────────────┤
│             │      4      │
└─────────────┴─────────────┘
```

### Grid

```
┌──────┬──────┬──────┐
│  1   │  2   │  3   │
├──────┼──────┼──────┤
│  4   │  5   │  6   │
└──────┴──────┴──────┘
```

## Switching Layouts

```
# Via keybinding
bindsym $mod+a nop layman layout Autotiling
bindsym $mod+m nop layman layout MasterStack
bindsym $mod+g nop layman layout Grid

# Via CLI
layman layout MasterStack
```

## Common Configuration

All layouts support:

- `debug`: Enable debug logging for this workspace

Layout-specific options documented in each layout's page.
