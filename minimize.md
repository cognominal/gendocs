# Minimizing windows in Omarchy 4.5

Verified against the installed Omarchy build (`omarchy version` → `4.0.0.r7840.gac6cb9c-1`, the 4.5 line) on Hyprland with the Lua config. Source references are to `/usr/share/omarchy/` as shipped.

## Summary

Hyprland has no minimize state. Omarchy emulates it: a "minimized" window is a normal client parked on the hidden special workspace `special:minimized`, and the dock is the stock way to bring it back. There is no stock key for restoring.

| Action | Binding | Where |
|---|---|---|
| Minimize active window to the dock | `SUPER + M` | `default/hypr/bindings/tiling.lua:34` |
| Unminimize (added locally) | `SUPER + ALT + M` | `~/.config/hypr/bindings.lua` |
| Restore by pointer | click the app's dock icon | shell dock plugin |
| Toggle workspace layout (floating/tiling) | `SUPER + L` | `default/hypr/bindings/tiling.lua` |

## How minimizing works

`SUPER + M` runs `omarchy-hyprland-window-minimize [window-address]` (source: `bin/omarchy-hyprland-window-minimize`). With no address it acts on the active window; the titlebar `−` button passes `%WINDOW%`.

1. Resolve the window address and its workspace id (`hyprctl clients -j` / `hyprctl activewindow -j`).
2. **Gate on layout**: return immediately unless the window's workspace layout is `floating` (`omarchy-hyprland-workspace-layout-current`). Tiling workspaces have no dock, so minimize is a silent no-op there.
3. Tag the window `omarchy-minimized-from-<workspace>` so the origin is recorded.
4. Move it: `hl.dsp.window.move({ workspace = "special:minimized", follow = false })`.
5. Refocus the origin workspace, otherwise the next window you open lands on the hidden special workspace.

The minimized client keeps running, keeps its app id, class, title and pid; its `workspace.name` becomes `special:minimized` and `workspace.id` is `null` in `hyprctl clients -j`. It is not mapped, so compositor-side it is invisible.

Nothing else consumes the `omarchy-minimized-from-N` tag: A grep of the whole shipped tree finds only the writer in the minimize script. In particular, restore does **not** return a window to the workspace it was minimized from.

## How restoring works (dock)

The dock is a Quickshell plugin (`shell/plugins/dock/`) rendered only on floating-layout workspaces. `DockWindow.qml` hides it with opacity when the active workspace is not floating, so switching to a tiling workspace removes the only pointer path back.

A minimized window always belongs in the dock, even without a matching desktop entry (`DockModel.isDockWindow` returns true for `window.minimized`), since the dock is the only way back to it. Clicks on an app that owns several windows follow `DockModel.pickWindow`'s ranking: a window already on the focused workspace first, then a minimized one, then one on another workspace. Clicking again while that window is focused advances to the next window in that order.

Clicking runs `Dock.bringForward` (`Dock.qml`), which reproduces what a restore should do:

```js
if (window.minimized) {
  steps.push(set_prop no_anim 1)
  steps.push(move to the focused monitor's active workspace)
  after.push(set_prop no_anim unset)   // 0.4 s later
}
steps.push(focus); steps.push(alter_zorder top)
```

- The target is the **currently focused workspace**, requiring a real id (`>= 1`); a visible special workspace cannot receive the window.
- `no_anim` suppresses the "window animates in from nowhere" artifact of a special-workspace move; it is unset 0.4 s later.
- The window is focused and raised to the top of the stack, matching how a dock click on a normal window behaves.

## Restoring from the keyboard

No stock binding exists. `~/.config/hypr/bindings.lua` adds one, mirroring the dock's semantics without a dependency on the dock being visible:

```lua
function o.unminimize_window()
  local minimized = hl.get_windows({ workspace = "special:minimized" })
  if #minimized == 0 then return end

  -- focus_history_id counts up from 0 (most recent), so the smallest id is the
  -- window minimized last.
  table.sort(minimized, function(a, b)
    return (a.focus_history_id or math.huge) < (b.focus_history_id or math.huge)
  end)

  local workspace = hl.get_active_workspace()
  if not workspace or not workspace.id or workspace.id < 1 then return end

  local target = "address:" .. minimized[1].address
  hl.dispatch(hl.dsp.window.move({ workspace = tostring(workspace.id), window = target }))
  hl.dispatch(hl.dsp.focus({ window = target }))
  hl.dispatch(hl.dsp.window.alter_zorder({ mode = "top", window = target }))
end

o.bind_expressions[o.unminimize_window] = "function() o.unminimize_window() end"
o.bind("SUPER + ALT + M", "Unminimize window", o.unminimize_window)
```

Notes on the choices:

- `SUPER + SHIFT + M` would be the obvious symmetry with `SUPER + M`, but it is already bound to the Spotify "Music" launcher (`default/hypr/bindings/applications.lua:16`), and `SUPER SHIFT ALT + M` is "Music TUI". `SUPER + ALT + M` is free.
- Ordering picks the most recently focused window among the minimized ones. My minimizing a window moves focus away, which lowers its `focus_history_id` relative to windows minimized earlier, so the smallest id is the last one minimized. Pressing the key repeatedly drains the stack newest-first.
- Restore lands on the **focused** workspace, like a dock click. Restoring while on a tiling workspace is allowed and the window simply joins the tiles.
- `o.bind_expressions` is what lets the keybindings menu (`SUPER + K`, or `omarchy menu keybindings`) replay a Lua-function bind: the menu dispatches `hyprctl dispatch 'function() o.unminimize_window() end'`.

Reload and validate after editing:

```bash
hyprctl reload && hyprctl configerrors    # must print nothing
omarchy menu keybindings --print | grep -i unminimize
```

## Manual / scripted access

List every minimized window:

```bash
hyprctl clients -j | jq -r '.[] | select(.workspace.name == "special:minimized") | .address + "  " + .class + "  " + .title'
```

Restore a specific one by address (no `o.` config needed, pure IPC):

```bash
addr=0x556d7a99a1e0
ws=$(hyprctl activeworkspace -j | jq -r '.id')
hyprctl dispatch "hl.dsp.window.move({ workspace = \"$ws\", window = \"address:$addr\" })"
hyprctl dispatch "hl.dsp.focus({ window = \"address:$addr\" })"
hyprctl dispatch "hl.dsp.window.alter_zorder({ mode = \"top\", window = \"address:$addr\" })"
```

Minimize from the command line, either the active window or a named one:

```bash
omarchy hyprland window minimize
omarchy hyprland window minimize 0x556d7a99a1e0
```

Restore using the keybinding's own action, without pressing the key:

```bash
hyprctl dispatch 'function() o.unminimize_window() end'
```

## Caveats

- **Silent no-op on tiling workspaces.** `SUPER + M` exits 0 without moving anything unless the window's workspace layout is `floating`. There is no feedback. Use `SUPER + L` to check/change the layout, or float the single window (`SUPER + T`) — a floating window on a tiling workspace still fails the workspace-layout gate.
- **The dock is the only stock UI, and it is layout-scoped.** With the dock auto-hidden (`omarchy dock autohide on`) a restore also requires reaching the screen edge; `omarchy dock autohide off` keeps it visible. `omarchy dock position top|bottom|left|right` moves it.
- **Restore target is the focused workspace, not the origin.** The origin tag written at minimize time is currently dead data, so a restored window stays on the workspace it was restored to, even if that differs from the one it was minimized from. Clearing the stale tag by hand is unnecessary: `omarchy-hyprland-window-minimize` drops an earlier `omarchy-minimized-from-*` tag when it minimizes that window again.
- **Special workspaces are per monitor internals.** `special:minimized` is not a user workspace: `SUPER + number` cannot focus it, it never appears in the workspaces bar, and `hl.get_active_workspace()` reports the visible workspace while a minimized window is hidden.
- **Minimize vs. scratchpad vs. quake console.** `SUPER + S` (scratchpad, `special:scratchpad`) and `SUPER + grave` (quake console, `special:qconsole`) are toggled special workspaces, not minimize slots; their windows stay visible on demand and never enter the dock.

## Verification performed

On workspace 1 (layout `floating`), with a throwaway `foot` window:

1. `omarchy hyprland window minimize <addr>` → `hyprctl clients -j` showed `ws=special:minimized`.
2. `hyprctl dispatch 'function() o.unminimize_window() end'` → printed `ok`; the window returned to `ws=1` with `focusHistoryID=0` (focused).
3. Invoking it with nothing minimized → `ok`, no-op.
4. `hyprctl reload; hyprctl configerrors` → clean; `omarchy menu keybindings --print` lists `SUPER ALT + M → Unminimize window` and still lists both Music bindings.
