# Known Bugs

## Critical

### Window Width Not Preserved on Leave

**Status:** 📋 Planned

**Problem:**
When a window leaves a workspace (closed or moved), it's too late to read the master window's width. The replacement window can't fill the exact spot.

**Current Behavior:**
```
1. Master window has 60% width
2. Master window closes
3. Stack window becomes master
4. New master gets default 50% width (wrong!)
```

**Root Cause:**
In `windowRemoved`, we try to read `window.rect.width`, but by the time the event arrives:
- The window may already be destroyed
- The rect may be stale or zeroed

**Relevant Code:**
```python
# master_stack.py, popWindow method
if window.rect.width == 0:
    self.log("window with width 0 popped. likely a bug.")
```

**Proposed Solutions:**

1. **Track width proactively**
   - Store master width whenever it changes
   - Use stored value on window removal

2. **Use container width**
   - Instead of window rect, use parent container width
   - Container may still exist after window removed

3. **Calculate from workspace**
   - Use workspace width and master percentage
   - More reliable than pixel values

**Implementation Plan:**
```python
class MasterStackLayoutManager:
    lastKnownMasterWidth: Optional[int] = None

    def windowFocused(self, event, workspace, window):
        if window.id == self.windowIds[0]:  # Master focused
            self.lastKnownMasterWidth = window.rect.width

    def popWindow(self, window):
        # Use lastKnownMasterWidth instead of window.rect.width
```

---

## Major

### Existing Windows Sometimes Missed

**Status:** 📋 Planned

**Problem:**
When activating MasterStack on a workspace with existing windows, sometimes windows are missed.

**Note from README:**
> Known bugs: Sometimes existing windows get missed when arranging an existing layout

**Possible Causes:**
- Race condition during initialization
- Floating windows not properly filtered
- Container structure confusing leaf detection

---

## Minor

### Focus Event Race Condition

**Status:** 📋 Planned

**Problem:**
Rapid focus changes can cause stale focus events to be processed.

**Current Mitigation:**
```python
if event.container.id != focused_workspace_window.id:
    # Ignore stale event
    return
```

**Improvement:**
Could add event timestamp comparison or sequence numbering.

---

### Debug Logging Inconsistent

**Status:** 📋 Planned

**Problem:**
Some log messages use different formats or don't respect debug flag.

**Fix:**
Standardize on `self.log()` and `self.logCaller()` methods.
