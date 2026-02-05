# Example Configurations

## Minimal Configuration

```toml
[layman]
defaultLayout = "Autotiling"
```

## Full Configuration

```toml
[layman]
defaultLayout = "none"
excludedWorkspaces = ["9", "10"]
debug = false
pipePath = "/tmp/layman.pipe"

# Autotiling
depthLimit = 0

# MasterStack
stackLayout = "splitv"
stackSide = "right"
masterWidth = 50
visibleStackLimit = 3

# Workspace 1: MasterStack with tabbed stack
[workspace.1]
defaultLayout = "MasterStack"
masterWidth = 55
stackLayout = "tabbed"
stackSide = "right"

# Workspace 2: Autotiling with depth limit
[workspace.2]
defaultLayout = "Autotiling"
depthLimit = 3

# Workspace 3: Grid layout
[workspace.3]
defaultLayout = "Grid"

# Workspace 4: MasterStack with left stack
[workspace.4]
defaultLayout = "MasterStack"
stackSide = "left"
masterWidth = 65
visibleStackLimit = 5

# Coding workspace: Debug enabled
[workspace.coding]
defaultLayout = "MasterStack"
debug = true
masterWidth = 60
stackLayout = "splitv"
```

## Development Workflow

```toml
[layman]
debug = false
defaultLayout = "Autotiling"
excludedWorkspaces = ["9"]

# Main coding workspace
[workspace.1]
defaultLayout = "MasterStack"
masterWidth = 65
stackLayout = "splitv"
visibleStackLimit = 4

# Browser/docs workspace
[workspace.2]
defaultLayout = "Autotiling"
depthLimit = 2

# Terminal workspace
[workspace.3]
defaultLayout = "Grid"
```

## Ultrawide Monitor

```toml
[layman]
defaultLayout = "MasterStack"
masterWidth = 40  # Larger master for ultrawide
stackLayout = "splitv"
visibleStackLimit = 5  # More visible stack windows on a wide screen

[workspace.1]
masterWidth = 35  # Even wider stack for coding
```

## Multi-Monitor

```toml
[layman]
defaultLayout = "Autotiling"

[workspace.1]
defaultLayout = "MasterStack"
masterWidth = 50

# Workspaces 5-8 typically on second monitor
[workspace.5]
defaultLayout = "Grid"
```

## Debugging Issues

```toml
[layman]
debug = true  # Enable globally for troubleshooting
defaultLayout = "none"

[workspace.1]
defaultLayout = "MasterStack"
# debug inherits from [layman]
```
