# Command Naming Convention Design

This document proposes a standardized naming convention for layman commands.

## Current State

Current commands have inconsistent naming patterns:

| Command | Style | Notes |
|---------|-------|-------|
| `window move up` | verb + direction | |
| `window move down` | verb + direction | |
| `window move left` | verb + direction | |
| `window move right` | verb + direction | |
| `window move to master` | verb + preposition + noun | |
| `window move to index <n>` | verb + preposition + noun + arg | |
| `window focus up` | verb + direction | |
| `window focus down` | verb + direction | |
| `window focus master` | verb + noun | |
| `stack toggle` | noun + verb | **Inconsistent** |
| `stack side toggle` | noun + verb | **Inconsistent** |
| `window swap master` | verb + noun | |
| `window rotate cw` | verb + abbreviation | |
| `window rotate ccw` | verb + abbreviation | |
| `layout maximize` | verb only | |
| `reload` | verb only | |
| `layout set <name>` | noun + arg | **Inconsistent** |
| `help` | noun only | |
| `status` | noun only | |

## Problems

1. **Verb position inconsistent**: Most commands are verb-first, but `stack toggle` and `stack side toggle` are noun-first
2. **layout command** is noun-first unlike movement commands
3. **No clear hierarchy**: Commands don't group logically

## Proposal A: Verb-First Everywhere

Change all commands to verb-first:

```
# Movement (unchanged)
move up|down|left|right
move to master
move to index <n>

# Focus (unchanged)
focus up|down
focus master

# Layout changes
set layout <name>         # was: layout <name>
toggle stack              # was: stack toggle
toggle stackside          # was: stackside toggle
toggle maximize           # was: maximize

# Rotation (unchanged)
rotate cw|ccw

# Swap (unchanged)
swap master

# Meta commands (unchanged)
reload
help
status
```

**Pros:**
- Consistent verb-first pattern
- `toggle` groups related commands
- `set` makes layout change explicit

**Cons:**
- Breaking change for existing configs
- `toggle maximize` is more awkward than `maximize`

## Proposal B: Subcommand Groups

Use subcommand hierarchy for related actions:

```
# Window commands
window move up|down|left|right
window move to master
window move to index <n>
window focus up|down|master
window swap master
window rotate cw|ccw

# Stack commands
stack toggle              # Toggle stack layout
stack side toggle         # Toggle stack side

# Layout commands
layout set <name>
layout maximize           # Toggle maximize mode

# Meta commands
reload
help
status
```

**Pros:**
- Clear grouping
- Extensible
- Tab-completion friendly

**Cons:**
- More verbose
- Major breaking change
- More typing for common operations

## Proposal C: Minimal Breaking Changes

Keep backward compatibility, add new preferred forms:

```
# Keep existing (mark as deprecated in docs)
stack toggle
stackside toggle
layout <name>
maximize

# Add new preferred forms (aliases)
toggle stack              # Same as: stack toggle
toggle stackside          # Same as: stackside toggle
set layout <name>         # Same as: layout <name>
toggle maximize           # Same as: maximize
```

**Pros:**
- No breaking changes
- Gradual migration path
- Users can choose style

**Cons:**
- Multiple ways to do the same thing
- More code to maintain
- Docs need to explain both

## Recommendation

**Proposal C** for the short term:
- Add the new verb-first aliases
- Document new forms as preferred
- Keep old forms working

**Future consideration:**
- In a major version (2.0), deprecate old forms
- Eventually remove old forms in 3.0

## Implementation Notes

For aliases in `onCommand()`:

```python
# Normalize command aliases
command_aliases = {
    "toggle stack": "stack toggle",
    "toggle stackside": "stackside toggle",
    "toggle maximize": "maximize",
}
if command in command_aliases:
    command = command_aliases[command]
```

For `set layout`:
```python
if command.startswith("set layout "):
    command = command.replace("set layout ", "layout ", 1)
```

## Decision Needed

Which proposal to implement?

- [ ] Proposal A: Full verb-first (breaking)
- [ ] Proposal B: Subcommand groups (breaking)
- [ ] Proposal C: Aliases with backward compat (recommended)
- [ ] None: Keep current naming

---

*Created: 2026-02-04*
*Status: Pending decision*
