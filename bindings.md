# Window and workspace bindings: Omarchy 4.5, LazyVim, tuios

Three layers with the same verbs at different scopes: a Wayland compositor, a
Neovim distribution, and a terminal window manager. The table uses each tool's
own vocabulary. Some notes are about my personal/local configuration.

| Notation | Meaning |
|---|---|
| `SUPER` | Windows/Command key in Omarchy/Hyprland. |
| `<leader>` | Space in LazyVim (`vim.g.mapleader = " "`). |
| `alt+space` | The tuios leader on this machine (`leader_key` in `~/.config/tuios/config.toml`; stock default is `ctrl+b`). |
| window mode | tuios's management mode. In terminal mode the keys go to the pane instead. |
| tab | A Vim tabpage (`:tabnew`), not a bufferline buffer. See the buffer rows at the end. |

| Area | Action | Omarchy 4.5 (Hyprland) | LazyVim (Neovim) | tuios |
|---|---|---|---|---|
| **Windows** | Create a window / split | `SUPER+RETURN` opens a terminal; any launched app tiles automatically. `SUPER+J` changes the next split direction. | `<leader>-` split below; `<leader>\|` split right (`<C-w>s`, `<C-w>v`). | `alt+space c` or window mode `n` opens a window; `alt+space -` splits top/bottom, `alt+space \|` splits left/right (`alt+space \` too). |
| | Close focused window | `SUPER+W` or `SUPER+Q`; `CTRL+ALT+DELETE` closes all. | `<leader>wd` (`<C-w>c`); `<leader>bD` closes buffer and window. | `alt+space x`; window mode `x` or `w`; GUI `ctrl+shift+w`. |
| | Focus by direction | `SUPER+←/→/↑/↓`. | `<C-h>`, `<C-j>`, `<C-k>`, `<C-l>`. | Window mode `h/j/k/l` (`h`/`l` snap or focus; `j`/`k` focus). |
| | Cycle windows | `ALT+TAB` / `ALT+SHIFT+TAB` (stock). | `<C-w>w` (Vim built-in); buffers use `<S-h>` / `<S-l>`. | Window mode `Tab` / `Shift+Tab`; prefix `alt+space n` / `alt+space p`; terminal mode `alt+n` / `alt+p`. |
| | Move / swap window | `SUPER+SHIFT+←/→/↑/↓`. | `<leader>w` then `H/J/K/L` (which-key proxy to `<C-w>H/J/K/L`). | Window mode `H/J/K/L` or `Ctrl+←/→/↑/↓`. |
| | Resize | `SUPER+MINUS` / `SUPER+EQUAL` horizontally; add `SHIFT` for vertical. | `<C-←/→/↑/↓>` adjusts by two rows/columns. | Window mode `[` / `]` / `{` / `}`, and `<` / `>` for master width; `alt+space =` equalizes. |
| | Fullscreen / zoom | `SUPER+F` true fullscreen; `SUPER+ALT+F` maximized. | `<leader>wm` zoom; `<leader>uz` zen mode. | Window mode `z` or `alt+space z`; `f` snaps fullscreen. |
| **Workspaces / tabs** | Switch to N | `SUPER+1…9`, `SUPER+0` for workspace 10. Ten slots per monitor. | `gt` / `gT` (Vim built-in), or `Ngt` for tab N. LazyVim adds no number map. | `Alt+1…9`; prefix `alt+space w 1…9`. Nine workspaces per session. |
| | Next / previous | `SUPER+TAB` / `SUPER+SHIFT+TAB`; `SUPER+CTRL+TAB` returns to the former workspace. | `<leader><tab>]` / `<leader><tab>[`. | `alt+tab` / `alt+shift+tab` (next/previous workspace that has panes). |
| | First / last | `SUPER+1` / `SUPER+0`. | `<leader><tab>f` / `<leader><tab>l`. | `Alt+1` / `Alt+9`; no separate first/last binding. |
| | New workspace / tab | No create binding: workspaces are slots created on demand by focusing them. | `<leader><tab><tab>` (`:tabnew`). | Unbound `new_workspace` (jumps to the first empty workspace); open a pane there with `new-window --workspace N`. |
| | Close / delete | No close binding: close or move the windows out; the numbered slot remains. | `<leader><tab>d` (`:tabclose`); `<leader><tab>o` closes other tabs. | Unbound; `tuios close-workspace N` or `run-command close_workspace` (asks for confirmation). `alt+space X` closes the whole session. |
| | Move window to workspace N | `SUPER+SHIFT+N` moves and follows; `SUPER+SHIFT+ALT+N` moves silently. | `<C-w>T` moves the split to a new tab. No default for moving into an existing tab; `:tabmove N` reorders tabs. | `Ctrl+Alt+N` sends without following; `Alt+Shift+N` moves and follows. Prefix form: `alt+space w !` … `alt+space w (` for 1…9. |
| | Reorder workspace / tab | No reorder binding. `SUPER+SHIFT+ALT+←/→/↑/↓` moves a whole workspace to another monitor. | `:tabmove N`; no default key. | Unbound `move_workspace_left` / `move_workspace_right`; drag the workspace pill in the dock. |
| | Rename | No keybinding; workspace names come from Hyprland rules/config. | No tab rename. Buffer names are file names. | `alt+space w r`; CLI `tuios set-workspace-name N name`. |
| | Close others | No equivalent. | `<leader><tab>o` (`:tabonly`); buffers: `<leader>bo`. | Close the workspace: `tuios close-workspace N`. |
| **LazyVim buffers** (the visible file tabs) | Previous / next | — | `<S-h>` / `<S-l>`, `[b` / `]b`, or `<leader>bb` for the other buffer. | — |
| | Close | — | `<leader>bd`; `<leader>bo` closes other buffers; `<leader>br` / `<leader>bl` close right/left. | — |
| | Reorder in bufferline | — | `[B` / `]B` move the buffer left/right. | — |

## Notes that change what you actually press

- **Omarchy's `ALT+TAB` is locally overridden.** `~/.config/hypr/bindings.lua` rebinds `ALT+TAB` and `ALT+SHIFT+TAB` to forward the chord to tuios when the focused window is a tuios terminal, and otherwise run Omarchy's stock cycle. `ALT+SPACE` is unbound there so tuios can use it as its leader. Stock Omarchy the table describes is in `/usr/share/omarchy/default/hypr/bindings/`.
- **Omarchy has ten slots per monitor.** `SUPER+3` means the third slot of the focused monitor's block; the next monitor owns 11–20. There is no create/close step, unlike tabs.
- **tuios has exactly nine workspaces.** `new_workspace` means "go to the first empty one", and `close_workspace` closes every pane on one, after renumbering the rest. This is the closest thing to closing a tab.
- **LazyVim's tab strip is usually bufferline, not tabpages.** `<S-h>` / `<S-l>` and `[B` / `]B` move between and reorder open files. The `<leader><tab>` group is the real tabpage layer that maps to workspaces.

## Russian dolls: Omarchy → Ghostty → tuios → LazyVim

The four systems nest like matryoshka dolls, and each one is a complete window
manager with its own objects:

```
Hyprland/Omarchy   windows, workspaces 1-10 per monitor
  └─ Ghostty        tabs, splits, windows
      └─ tuios      sessions, workspaces 1-9, panes
          └─ shell
              └─ Neovim/LazyVim   buffers, splits, tabpages
```

Hyprland does not know that tuios or LazyVim exist. To Hyprland, the whole
stack is one Ghostty surface. Ghostty does not know about tuios panes; to
Ghostty they are just bytes in a PTY. tuios does not know about LazyVim splits;
to tuios, Neovim is one program in one pane. That ignorance is what lets them
cooperate: every layer handles the keys it recognizes and passes the rest down.

### Who sees the key first

1. **Hyprland/Omarchy.** It sees the hardware key first. A `SUPER+…` binding
   runs and consumes the key. With no match, the key goes to the focused
   Wayland surface.
2. **Ghostty.** It handles its own chords (`CTRL+SHIFT+…`, `CTRL+ALT+…`,
   `ALT+1…9`, and the rest of the table below). Everything else is written to
   the PTY as terminal input.
3. **tuios.** It reads that input. In window mode the keys are commands; in
   terminal mode they are forwarded to the focused pane. Its prefix is
   `ALT+SPACE`.
4. **The pane's program.** A shell passes them to the foreground job; Neovim
   interprets them according to its current mode.

The modifier split is deliberate: **Omarchy owns `SUPER`; tuios owns `ALT` and
deliberately does not use `SUPER`.** Hyprland grabs most `SUPER` chords before
any client sees them, so a tuios binding like `SUPER+1` would never reach
tuios. `ALT+1` is not an Omarchy binding and falls through. That is why tuios's
leader is `ALT+SPACE` here (stock `CTRL+B`), not `SUPER+SPACE`. LazyVim then
lives one layer deeper and uses `SPACE` for its leader and `CTRL` for editing
and window commands.

The layers also use disjoint modifier families: Ghostty sits in the middle with
`CTRL+SHIFT` and `CTRL+ALT`, tuios avoids those, and LazyVim uses `SPACE` and
plain `CTRL`. The design is not formally negotiated; it works because each
layer ignores chords it does not claim.

Some concrete traces:

- `SUPER+W` → Hyprland closes the Omarchy window. Ghostty, tuios, and LazyVim
  never see the key.
- `ALT+SPACE`, `w`, `2` → no Omarchy binding, no Ghostty binding, then tuios's
  prefix switches to workspace 2.
- `ALT+2` → no Omarchy binding, but **Ghostty binds `alt+2` to `goto_tab:2`**.
  Ghostty consumes it; tuios never sees it. This is the broken link in the
  chain.
- `ALT+TAB` → outside tuios, Omarchy cycles windows. The local
  `~/.config/hypr/bindings.lua` detects a focused tuios terminal and injects
  the chord so tuios switches workspaces instead.
- `CTRL+W`, `H` → if Neovim is focused and in normal mode, LazyVim moves the
  split. If Neovim is in terminal mode, `CTRL+W` goes to the terminal job.
- `ESC` in a LazyVim terminal buffer → Snacks sends the first `ESC` to the job
  and the second within 200 ms leaves terminal mode. A built-in `:terminal`
  uses `CTRL-\`, `CTRL+N` instead.

### tuios modes

- **Window mode** — tuios consumes management keys (`h/j/k/l`, `H/J/K/L`, `n`,
  `x`, `z`, `Tab`, …). `i` or `Enter` enters terminal mode.
- **Terminal mode** — keys go to the pane's program. `ALT+ESC` returns to
  window mode. This is the mode Neovim must be in for LazyVim to receive
  anything.
- **Prefix** — `ALT+SPACE` starts a chord (`c`, `x`, `-`, `|`, `w`, …); `ESC`
  cancels it. A prefix chord is consumed by tuios even when terminal mode is
  active.

### LazyVim modes

- **Normal/visual** — `SPACE` is the leader; `<C-w>` commands address Neovim
  windows; `<leader><tab>` addresses tabpages.
- **Insert** — text goes into the buffer. `SUPER`/`ALT` chords still belong to
  the outer layers.
- **Terminal** — Neovim forwards keys to the terminal job. `CTRL-\`, `CTRL+N`
  leaves terminal mode. Snacks terminals (LazyVim's `<leader>ft`) add
  double-`ESC`, plus `CTRL+h/j/k/l` to leave the terminal and move windows, and
  `CTRL+/` to hide it.

Only the innermost active mode interprets a key: if tuios is in window mode,
Neovim gets nothing; if tuios is in terminal mode but Neovim is in normal mode,
Neovim interprets; if both are in terminal mode, the shell gets it.

### Ghostty's bindings

These are the effective bindings on this machine from
`ghostty +list-keybinds` (Ghostty 1.4.0+omarchy.1). Omarchy's base file is
`/usr/share/omarchy/config/ghostty/config`; the user file adds only the font and
the four `super+control+shift+alt` resize chords.

| Scope | Keys | Action |
|---|---|---|
| Config | `CTRL+SHIFT+,` / `CTRL+,` | Reload config / open config |
| Clipboard | `CTRL+SHIFT+C`, `CTRL+INSERT` / `CTRL+SHIFT+V`, `SHIFT+INSERT` | Copy / paste (also bare `copy`/`paste` keys) |
| Font | `CTRL+=`, `CTRL++` / `CTRL+-` / `CTRL+0` | Increase / decrease / reset size |
| Tabs | `CTRL+SHIFT+T` / `CTRL+SHIFT+W` / `CTRL+SHIFT+N` | New tab / close this tab / new window |
| Tabs | `CTRL+TAB`, `CTRL+SHIFT+TAB`; `CTRL+SHIFT+←/→`; `CTRL+PAGE_UP/PAGE_DOWN` | Next / previous tab |
| Tabs | `ALT+1…8` / `ALT+9` | Go to tab 1–8 / go to last tab — **shadows tuios workspace switching when tuios runs inside Ghostty** |
| Tabs | `CTRL+SHIFT+PAGE_UP/PAGE_DOWN` | Move tab left / right |
| Splits | `CTRL+SHIFT+O` / `CTRL+SHIFT+E` | New split right / down |
| Splits | `CTRL+ALT+←/→/↑/↓`; `SUPER+CTRL+[` / `]` | Go to split by direction / previous / next |
| Splits | `SUPER+CTRL+SHIFT+←/→/↑/↓` / `SUPER+CTRL+ALT+SHIFT+←/→/↑/↓` | Resize split by 10 / by 100 — the first is **shadowed by Omarchy's move-window-to-monitor chord** |
| Splits | `CTRL+SHIFT+ENTER` | Toggle split zoom |
| Window | `ALT+F4` / `CTRL+SHIFT+Q` | Close window / quit Ghostty |
| Fullscreen | `CTRL+ENTER` | Toggle fullscreen |
| Screen | `SUPER+CTRL+SHIFT+J` / `CTRL+SHIFT+J` / `CTRL+ALT+SHIFT+J` | Write screen to clipboard / paste / open |
| Selection / scroll | `SHIFT+←/→/↑/↓`; `SHIFT+PAGE_UP/PAGE_DOWN`; `SHIFT+HOME/END` | Adjust selection; scroll a page; scroll to top/bottom |
| Prompt | `CTRL+SHIFT+↑/↓` | Jump to previous / next prompt |
| Search | `CTRL+SHIFT+F` / `ESC` | Start search / end search |
| Misc | `CTRL+SHIFT+A` / `CTRL+SHIFT+I` / `CTRL+SHIFT+P` | Select all / inspector / command palette |
| Input | `SHIFT+ENTER` / `ALT+SHIFT+ENTER` | Send CSI-u encodings so TUIs can distinguish them from `ENTER` |

### The two real collisions

1. **Ghostty's `ALT+1…9` vs tuios's workspace keys.** Ghostty matches the chord
   before the PTY, so tuios cannot see it. Two fixes:

   ```
   # ~/.config/ghostty/config — give the digits back to tuios
   keybind = alt+1=unbind
   keybind = alt+2=unbind
   keybind = alt+3=unbind
   keybind = alt+4=unbind
   keybind = alt+5=unbind
   keybind = alt+6=unbind
   keybind = alt+7=unbind
   keybind = alt+8=unbind
   keybind = alt+9=unbind
   ```

   Or leave Ghostty alone and use tuios's prefix: `ALT+SPACE`, `w`, `2`. The
   prefix is not claimed by Ghostty and always reaches tuios.

2. **Ghostty's `SUPER+CTRL+SHIFT+arrows` vs Omarchy's
   `SUPER+SHIFT+CTRL+arrows`.** The chords are identical, and Hyprland wins:
   Ghostty's default resize does not get the chord while Omarchy holds it.
   The user config's extra `ALT` (`SUPER+CTRL+ALT+SHIFT+arrows`) is the variant
   that escapes Omarchy and reaches Ghostty. This is a good illustration of the
   rule: the outer doll
   consumes first; an inner binding works only if the outer one does not claim
   the chord.

## Sources

- Omarchy: `/usr/share/omarchy/default/hypr/bindings/tiling.lua`, `.../utilities.lua`, `.../monitor-workspaces.lua`, plus `~/.config/hypr/bindings.lua` overrides.
- Ghostty 1.4.0+omarchy.1: `/usr/share/omarchy/config/ghostty/config`, `~/.config/ghostty/config`, and `ghostty +list-keybinds`.
- LazyVim v16.0.1: `lua/lazyvim/config/keymaps.lua`, `lua/lazyvim/plugins/ui.lua`, `lua/lazyvim/plugins/editor.lua`, `lua/lazyvim/plugins/util.lua`; Snacks `lua/snacks/terminal.lua`.
- tuios: `tuios keybinds list`, `tuios keybinds explain`, `tuios --skill panes`, and `~/.config/tuios/config.toml`.
