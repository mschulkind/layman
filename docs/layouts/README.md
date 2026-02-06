# Layout Managers

This section documents each layout manager included with layman.

## Contents

| File | Description |
|------|-------------|
| [autotiling.md](autotiling.md) | Autotiling (spiral) layout |
| [master-stack.md](master-stack.md) | Master + Stack layout |
| [grid.md](grid.md) | Grid layout |
| [three-column.md](three-column.md) | Three-column layout with center master |
| [tabbed-pairs.md](tabbed-pairs.md) | Tabbed window pairs layout |
| [custom-layouts.md](custom-layouts.md) | Creating custom layouts |

## Layout Comparison

| Layout | Description | Use Case |
|--------|-------------|----------|
| `none` | No management | Manual control |
| `Autotiling` | Spiral tiling | General purpose |
| `MasterStack` | Master + stack | Focus on one main window |
| `Grid` | Grid pattern | Equal window importance |
| `ThreeColumn` | Center master + two side stacks | Multi-monitor feel on ultrawide |
| `TabbedPairs` | Windows grouped in tabbed pairs | Code + preview workflows |

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

### ThreeColumn

```
┌──────────┬──────────┬──────────┐
│  Stack 1 │          │  Stack 3 │
├──────────┤  Master  ├──────────┤
│  Stack 2 │          │  Stack 4 │
└──────────┴──────────┴──────────┘
```

### TabbedPairs

```
┌──────────────┬──────────────┬──────────┐
│ [Ed] [Term]  │ [Br] [Docs]  │ Unpaired │
│   content    │   content    │          │
└──────────────┴──────────────┴──────────┘
```

## Switching Layouts

```
# Via keybinding
bindsym $mod+a nop layman layout set Autotiling
bindsym $mod+m nop layman layout set MasterStack
bindsym $mod+g nop layman layout set Grid
bindsym $mod+t nop layman layout set ThreeColumn
bindsym $mod+p nop layman layout set TabbedPairs

# Via CLI
layman layout set MasterStack
```

## Common Configuration

All layouts support:

- `debug`: Enable debug logging for this workspace

Layout-specific options documented in each layout's page.
