# Configuration Options

## Global Options (`[layman]`)

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `defaultLayout` | string | `"none"` | Default layout for new workspaces |
| `excludeWorkspaces` | array | `[]` | Workspace names to exclude from management |
| `excludeOutputs` | array | `[]` | Output names to exclude |
| `debug` | bool | `false` | Enable debug logging |

## Autotiling Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `depthLimit` | int | `0` | Max nesting depth (0 = unlimited) |

## MasterStack Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `masterWidth` | int | `50` | Master window width (1-99 percent) |
| `stackLayout` | string | `"splitv"` | Stack layout: `splitv`, `splith`, `tabbed`, `stacking` |
| `stackSide` | string | `"right"` | Stack position: `left` or `right` |
| `depthLimit` | int | `0` | Max visible stack windows before substack (0 = unlimited) |

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

## Output Configuration (`[output.<name>]`)

**Note:** Output configuration is currently disabled in the code.

```toml
# Not currently used
[output.HDMI-A-1]
defaultLayout = "Grid"
```

## Built-in Layouts

| Short Name | Class | Description |
|------------|-------|-------------|
| `none` | WorkspaceLayoutManager | No management |
| `Autotiling` | AutotilingLayoutManager | Spiral tiling |
| `MasterStack` | MasterStackLayoutManager | Master + stack |
| `Grid` | GridLayoutManager | Grid tiling |
| `splitv` | (native) | Vertical split |
| `splith` | (native) | Horizontal split |
| `tabbed` | (native) | Tabbed layout |
| `stacking` | (native) | Stacking layout |

## Validation

Invalid values are logged and defaults are used:

```python
# masterWidth validation
if isinstance(masterWidth, int) and masterWidth > 0 and masterWidth < 100:
    self.masterWidth = masterWidth
else:
    self.logError("Invalid masterWidth...")
```

## Debug Mode

When `debug = true`:

- All event handlers log their actions
- Command execution is logged with results
- Window ID tracking is displayed

Debug can be enabled globally or per-workspace.
