# Sway/i3 Integration

## Starting Layman

Add to your sway/i3 config:

```
exec layman
```

For debugging, log output:

```
exec layman 2>&1 | tee /tmp/layman.log
```

## Key Bindings

### Layout Selection

```
# Toggle layout managers
bindsym $mod+a nop layman layout set Autotiling
bindsym $mod+m nop layman layout set MasterStack
bindsym $mod+g nop layman layout set Grid
bindsym $mod+n nop layman layout set none
```

### Movement Overrides

For layouts that handle movement differently:

```
# Override move binds
bindsym $mod+Shift+Left nop layman window move left
bindsym $mod+Shift+Down nop layman window move down
bindsym $mod+Shift+Up nop layman window move up
bindsym $mod+Shift+Right nop layman window move right

# Vim-style (optional)
bindsym $mod+Shift+h nop layman window move left
bindsym $mod+Shift+j nop layman window move down
bindsym $mod+Shift+k nop layman window move up
bindsym $mod+Shift+l nop layman window move right
```

### MasterStack / ThreeColumn Commands

```
# Swap focused with master
bindsym $mod+Return nop layman window swap master

# Focus master
bindsym $mod+space nop layman window focus master

# Toggle stack layout (splitv → splith → stacking → tabbed)
bindsym $mod+t nop layman stack toggle

# Toggle stack side (left ↔ right)
bindsym $mod+y nop layman stack side toggle

# Multi-master: add/remove master windows
bindsym $mod+equal nop layman master add
bindsym $mod+minus nop layman master remove

# Rotate windows
bindsym $mod+r nop layman window rotate cw
bindsym $mod+Shift+r nop layman window rotate ccw

# Fake fullscreen
bindsym $mod+f nop layman layout maximize

# Focus previous window (per-workspace history)
bindsym $mod+Tab nop layman window focus previous
```

### Configuration Reload

```
# Reload layman config
bindsym $mod+Shift+c nop layman reload
```

## Using `nop` vs `exec`

### `nop` Method (Recommended)

```
bindsym $mod+m nop layman layout set MasterStack
```

**Pros:**

- No process spawn overhead
- Instant response
- Uses existing i3ipc connection

**How it works:** Sway emits a `BindingEvent` containing the full command string. Layman parses the command after "nop layman".

### `exec` Method

```
bindsym $mod+m exec layman layout set MasterStack
```

**Pros:**

- Works if layman daemon isn't running
- Clear process isolation

**Cons:**

- Spawns new process each time
- Slight latency
- Uses named pipe

## Complete Example

```
# Start layman
exec layman

# Layout switching
bindsym $mod+a nop layman layout set Autotiling
bindsym $mod+m nop layman layout set MasterStack
bindsym $mod+g nop layman layout set Grid
bindsym $mod+t nop layman layout set ThreeColumn
bindsym $mod+p nop layman layout set TabbedPairs

# Window movement
bindsym $mod+Shift+Left nop layman window move left
bindsym $mod+Shift+Down nop layman window move down
bindsym $mod+Shift+Up nop layman window move up
bindsym $mod+Shift+Right nop layman window move right

# Window focus
bindsym $mod+Left nop layman window focus left
bindsym $mod+Down nop layman window focus down
bindsym $mod+Up nop layman window focus up
bindsym $mod+Right nop layman window focus right

# MasterStack / ThreeColumn controls
bindsym $mod+Return nop layman window swap master
bindsym $mod+space nop layman window focus master
bindsym $mod+equal nop layman master add
bindsym $mod+minus nop layman master remove

# Stack controls
bindsym $mod+s nop layman stack toggle
bindsym $mod+y nop layman stack side toggle

# Fake fullscreen
bindsym $mod+f nop layman layout maximize

# Focus history
bindsym $mod+Tab nop layman window focus previous

# Session management
bindsym $mod+Shift+s nop layman session save default
bindsym $mod+Shift+r nop layman session restore default

# Reload config
bindsym $mod+Shift+c nop layman reload
```

## Troubleshooting

### Layman not receiving events

1. Check if layman is running: `pgrep -a layman`
2. Check logs if debug enabled
3. Verify sway is sending events: `swaymsg -t subscribe '["binding"]'`

### Commands not working

1. Test pipe directly: `echo "layout set MasterStack" > /tmp/layman.pipe`
2. Check pipe exists: `ls -la /tmp/layman.pipe`
3. Verify config path is correct
