# Configuration Options

This is a summary of all available options. For a comprehensive reference with examples and visual diagrams, see the **[Configuration Reference](config-reference.md)**.

## Global Options (`[layman]`)

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `defaultLayout` | string | `"none"` | Default layout for new workspaces |
| `excludedWorkspaces` | array | `[]` | Workspace names to exclude from management |
| `debug` | bool | `false` | Enable debug logging |
| `pipePath` | string | `"/tmp/layman.pipe"` | Path to the named pipe for IPC commands |

## Autotiling Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `depthLimit` | int | `0` | Max nesting depth (0 = unlimited) |

## MasterStack Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `masterWidth` | int or float | `50` | Master window width as percentage (0–100 exclusive) |
| `stackLayout` | string | `"splitv"` | Stack layout: `splitv`, `splith`, `tabbed`, `stacking` |
| `stackSide` | string | `"right"` | Stack position: `left` or `right` |
| `visibleStackLimit` | int | `3` | Max visible stack windows before substack (0 = disabled) |

## Workspace Overrides (`[workspace.<name>]`)

All options from `[layman]` can be overridden per workspace:

```toml
[workspace.1]
defaultLayout = "MasterStack"
masterWidth = 60
stackLayout = "tabbed"
debug = true

[workspace.music]
defaultLayout = "none"
```

## Built-in Layouts

| Short Name | Description |
|------------|-------------|
| `none` | No management |
| `Autotiling` | Spiral tiling based on window dimensions |
| `MasterStack` | Master window + configurable stack |
| `Grid` | Grid tiling by splitting the largest window |

Sway/i3 native layouts (`splitv`, `splith`, `tabbed`, `stacking`) can also be set directly.

## Validation

Invalid configuration values cause layman to exit with a clear error message showing the valid options. For example:

```
Invalid masterWidth '150'. Must be a number between 0 and 100 exclusive.
Invalid stackLayout 'diagonal'. Valid options: splitv, splith, stacking, tabbed
```

## Debug Mode

When `debug = true`:

- All event handlers log their actions
- Command execution is logged with results
- Window ID tracking is displayed

Debug can be enabled globally or per-workspace.
