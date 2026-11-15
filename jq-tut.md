# jq tutorial: munging `tuios ls --json` from Nushell

jq is a small functional language for JSON: a program is a *filter* that takes
one JSON document and emits zero, one, or many values. Learning it is mostly
learning the handful of shapes below, then composing them.

The first half of this tutorial is generic jq. The second half is a running
example in Nushell: a question about a running TUIOS daemon is answered by
reshaping `tuios ls --json`, and a question about its git worktrees by
reshaping `tuios worktree ls --json`.

Tested with jq 1.8.2, Nushell 0.117.0, and a dev build of `tuios`. The
sample output is a snapshot; counts and names differ on your machine.

---

## Part 1: jq basics

### 1. The filter model

A jq program runs once per input document. `.` is the identity filter: it
emits its input unchanged.

```jq
.
```

Consecutive filters are separated by `|`, and each stage feeds the next. A
filter may emit several values; the next stage runs once per value.

```jq
.panes[] | .cmd
```

If the input is a stream of documents rather than one document, jq runs the
program once per document. `-s` (slurp) turns the whole stream into one array
first.

For the basics, use this document:

```json
{
  "name": "api",
  "created": 1794165576,
  "attached": false,
  "panes": [
    {"cmd": "go", "cpu": 12, "workspace": 1},
    {"cmd": "node", "cpu": 3, "workspace": 2}
  ]
}
```

### 2. Fields, indexes, slices

```jq
.name,                   # "api"
.["name"],               # same; needed when the key is not an identifier
.panes[0].cmd,           # "go"
.panes[-1].cmd,          # "node"
.panes[0:1]              # first pane, as an array
```

Missing keys yield `null`:

```jq
.worktree.branch         # null, no error
```

`.foo?` suppresses the error when `.` is not an object, or when the key is
missing in a chain:

```jq
.worktree?.branch        # null, never an error
```

The `?` operator works on any filter, not just field access:

```jq
.panes[]?                # emits nothing if .panes is not iterable
```

### 3. Iteration

`.[]` iterates an array or object's values:

```jq
.panes[],                # two pane objects
.[]                      # the values of the document
```

A comma emits several outputs from one input:

```jq
.name, .attached         # "api", then false
```

Pipe has lower precedence than comma, so `a, b | f` applies `f` to both
outputs. That is what lets a header row and the data rows share one encoder.

Combined with array construction, that is how you collect:

```jq
[.panes[].cmd],                        # ["go","node"]
[.panes[] | select(.cpu > 5) | .cmd]   # ["go"]
```

### 4. Constructing values

Objects and arrays are built by placing filters inside them:

```jq
{name, attached},                              # shorthand for {name: .name, ...}
{name: .name, panes: (.panes | length)},
{(.name): .attached},                          # computed key
[.panes[].cmd],
[{cmd: .panes[].cmd}]
```

Inside `{}`, the shorthand `{name}` means `{name: .name}`. Inside `[]`, each
output of the inner filter becomes an element.

`tojson` and `fromjson` go between JSON text and values:

```jq
.panes | tojson | fromjson | length
```

### 5. `map`, `select`, `map_values`

`select` keeps the input when its condition is true, and emits nothing when it
is false:

```jq
.panes[] | select(.cpu > 5)
```

`map(f)` applies `f` to every element and collects the results:

```jq
(.panes | map(.cmd)),                # ["go","node"]
(.panes | map(select(.cpu > 5)))     # [ {"cmd":"go", ...} ]
```

`map_values` does the same for an object's values:

```jq
{go: 12, node: 3} | map_values(. * 2)   # {"go":24,"node":6}
```

### 6. Sorting, grouping, aggregates

```jq
(.panes | sort),                       # array sorted by value
(.panes | sort_by(.cpu)),              # ascending
(.panes | sort_by(-.cpu)),             # descending
(.panes | group_by(.cmd)),             # array of arrays
(.panes | unique_by(.cmd)),            # first of each key
(.panes | min_by(.cpu)), (.panes | max_by(.cpu))
```

`group_by` sorts its input by the key and returns groups. Each group is an
array, so read a group's representative with `.[0]`:

```jq
.panes | group_by(.workspace) | map({workspace: .[0].workspace, count: length})
```

`add` folds with `+`, which sums numbers and concatenates arrays or strings:

```jq
([.panes[].cpu] | add),                  # 15
(.panes | map(.cmd) | join(","))         # "go,node"
```

Length and keys:

```jq
(.panes | length),
(.panes[0] | keys),
(.panes[0] | has("cpu"))                # true
```

`length` on a string counts code points; on an object, keys.

### 7. Strings, numbers, booleans

Interpolation uses `\(...)` inside a string:

```jq
"\(.name): \(.panes | length) panes"
```

String functions include `ascii_downcase`, `ascii_upcase`, `startswith`,
`endswith`, `contains`, `split`, `join`, `test` (regex), `match`, `capture`,
`sub`, `gsub`, `ltrimstr`, `rtrimstr`, `tostring`.

```jq
(.name | startswith("a")),
(.name | test("^[a-z]+$"; "i"))
```

Arithmetic is the usual `+ - * / %`; `floor`, `ceil`, `round`, and `fabs` are
available. `tonumber` and `tostring` convert.

Booleans combine with `and`, `or`, `not`. Comparisons are `< <= > >= == !=`.

### 8. Conditionals and alternatives

```jq
if .attached then "attached" else "detached" end,
if .panes | length > 5 then "busy"
elif .panes | length > 0 then "idle"
else "empty"
end
```

`//` is the alternative operator: it emits the left side unless it is `null`
or `false`, otherwise the right side. It is the idiom for defaults:

```jq
(.worktree.branch // "-"),
(.worktree.branch? // "-")
```

Beware: `//` also treats `false` as absent. Use `has("key")` when `false` is a
real value.

`try f catch g` handles errors. `f?` is shorthand for ignoring them:

```jq
try (.worktree.branch | ascii_upcase) catch "none"
```

### 9. Variables, `reduce`, `def`

`as $x` binds a value for the rest of the filter:

```jq
.panes[] as $p | {cmd: $p.cmd, room: $p.workspace}
```

`reduce` folds a stream into an accumulator:

```jq
reduce .panes[] as $p (0; . + $p.cpu)
```

`foreach` is the streaming version, emitting the accumulator at each step.
`def` names a filter:

```jq
def total_cpu: [.panes[].cpu] | add;
{name, total: total_cpu}
```

`INDEX(stream; key)` builds an object keyed by an expression:

```jq
INDEX(.panes[]; .cmd)           # {"go": {...}, "node": {...}}
```

### 10. Paths and editing

`paths` lists paths to every value; `paths(scalars)` only leaves:

```jq
.panes[0] | paths(scalars) | join(".")
# "cmd", "cpu", "workspace"
```

`join` puts its separator only **between** elements, never before the first
or after the last. Each path from `.panes[0]` here is one element long
(`["cmd"]`, `["cpu"]`, `["workspace"]`), so no `.` is emitted at all. The
separator shows up only on a path with two or more segments, which `paths`
produces when it runs on the whole document:

```jq
paths(scalars) | join(".")
# "name", "created", "panes.0.cmd", ..., "panes.1.workspace"
```

That is also why `.panes[0] |` matters: prefixing it strips the leading
`panes` and index segments, leaving nothing for `join` to separate. To get a
trailing separator, append it yourself:

```jq
.panes[0] | paths(scalars) | join(".") + "."
# "cmd.", "cpu.", "workspace."
```

To render a path as the jq expression that rebuilds it, map array indexes to
`[n]`, object keys to `.key`, and join with the empty string:

```jq
paths(scalars) | map(if type == "number" then "[\(.)]" else ".\(.)" end) | join("")
# ".name", ".created", ".panes[0].cmd", ..., ".panes[1].workspace"
```

`getpath` and `setpath` use arrays as paths:

```jq
getpath(["panes", 0, "cmd"]),
setpath(["panes", 0, "cpu"]; 99)
```

`del` removes keys or elements:

```jq
del(.panes),
del(.panes[0])
```

`with_entries` rewrites an object as key/value pairs:

```jq
.panes[0] | with_entries(select(.key != "cpu"))
```

`walk` applies a filter bottom-up to every value:

```jq
walk(if type == "object" then del(.cpu) else . end)
```

### 11. Dates

Timestamps in JSON are usually Unix seconds. jq has:

```jq
now,                                   # seconds since the epoch
(.created | todate),                   # "2026-11-08T19:19:36Z"
("2026-11-08T19:19:36Z" | fromdate),   # Unix seconds
(.created | gmtime | strftime("%Y-%m-%d %H:%M"))
```

`now` is evaluated when the filter runs, so `now - .last_active` is an age in
seconds.

### 12. Command line

| Flag | Effect |
|---|---|
| `-r` | Raw output: strings printed without JSON quotes |
| `-c` | Compact output: one line per value |
| `-s` | Slurp: read all input documents into one array |
| `-n` | Null input: run the program once with `null` |
| `-e` | Exit status reflects the output (see below) |
| `--arg name value` | Bind a string as `$name` |
| `--argjson name json` | Bind parsed JSON as `$name` |
| `--slurpfile name file` | Bind an array of the file's documents as `$name` |
| `-f file` | Read the program from a file |
| `--indent n` | Pretty-print with `n` spaces |
| `--tab` | Pretty-print with tabs |
| `-j` | Do not print a trailing newline |
| `-S` | Sort object keys |

`-r` matters when the output is consumed by a person or another program:

```bash
jq '.[].name' input.json      # "api"  (JSON string, with quotes)
jq -r '.[].name' input.json   # api    (raw text, no quotes)
```

`-n` builds a document from arguments instead of input:

```bash
jq -n --arg name api '{name: $name, panes: 0}'
```

`--argjson` is for numbers, arrays, objects, and booleans:

```bash
jq --argjson limit 3 'select(.cpu > $limit)'
```

Never splice a shell or Nushell value into the program text. Pass it with
`--arg` or `--argjson`; then the value cannot change the program's meaning.

### 13. Encoders

An encoder turns a value into text with the right escaping:

```jq
([.name, .attached] | @tsv),            # "api\tfalse"
([.name, .attached] | @csv),            # "\"api\",false"
(["tuios", "attach", .name] | @sh),     # "'tuios' 'attach' 'api'"
(.name | @json),                        # "\"api\""
(.name | @base64),                      # "YXBp"
(.name | @uri)                          # "api"
```

Each comment is the JSON value jq prints for that line. `-r` drops the outer
quotes and their escapes, so the first line writes `api`, a tab, then
`false`. With `"name": "api"`:

- `@tsv` stringifies each element and escapes `\t`, `\n`, `\r` and `\\`
  inside a field; `null` becomes an empty field, and `false` prints as
  `false`.
- `@csv` quotes every string and doubles an embedded `"`; numbers, `null`
  and booleans are written bare.
- `@sh` single-quotes every string, so a name with spaces stays one
  argument (`'a b'`); an embedded `'` becomes `'\''`.
- `@json` is the JSON text for the value, quotes included.
- `@base64` encodes the UTF-8 bytes: `api` → `YXBp`.
- `@uri` percent-encodes everything outside `A-Za-z0-9-._~`:
  `pi > dim as help` → `pi%20%3E%20dim%20as%20help`; `api` needs no
  encoding.

Because `@tsv` output is plain text, `-r` plus `@tsv` is the usual
tab-separated recipe:

```bash
jq -r '["name","panes"], (.[] | [.name, .panes]) | @tsv'
```

### 14. Errors and exit status

An error aborts the program unless caught. `try`, `catch`, and `?` are the
three tools.

With `-e`, jq sets its exit status from the last output:

| Situation | Status |
|---|---|
| Last output is neither `false` nor `null` | 0 |
| Last output is `false` or `null` | 1 |
| No output at all | 4 |
| Error | 5 |

That makes `-e` usable as an assertion:

```bash
jq -e 'any(.[]; .attached)' sessions.json
```

---

## Part 2: the running example, in Nushell

Everything below runs in Nushell. `^tuios` and `^jq` force the external
binaries, so a Nushell alias or custom command of the same name cannot
intercept them.

### What `tuios ls --json` emits

For a local listing, the root is always an array, one object per session. A
live session looks like this (trimmed):

```json
[
  {
    "name": "Gaurav-Gosain-tuios-help-mode",
    "id": "4e6df5c1-58f2-44d9-a162-f798877f5bd2",
    "created": 1794165576,
    "last_active": 1794575464,
    "window_count": 11,
    "attached": true,
    "width": 140,
    "height": 42,
    "windows": [
      {
        "id": "559be146-a0f5-4476-83c3-ce3b4243dca2",
        "title": "π > dim as help",
        "agent_state": "done",
        "agent_state_at": 1794402178747488300,
        "agent_harness": "omp",
        "completion_seq": 111,
        "foreground_cmd": "omp",
        "workspace": 1
      }
    ],
    "current_workspace": 8,
    "dir": "~",
    "worktree": {
      "repo": "Gaurav-Gosain---tuios",
      "repo_root": "/home/cog/git/Gaurav-Gosain---tuios",
      "branch": "help-mode",
      "path": "/home/cog/.local/share/tuios/worktrees/Gaurav-Gosain---tuios/help-mode",
      "managed": true
    }
  }
]
```

Session fields:

| Field | Meaning |
|---|---|
| `name` | The session name, which is what commands address |
| `id` | The session UUID |
| `created`, `last_active` | Unix seconds |
| `window_count` | Number of panes |
| `attached` | A client is attached |
| `width`, `height` | Session size in cells |
| `windows` | Per-pane summaries, omitted by an older daemon |
| `current_workspace` | Workspace being shown; omitted when zero |
| `dir` | Base name of the focused pane's directory |
| `branch` | Git branch in that directory |
| `display_name` | A label set with `set-session-name`, when different |
| `accent`, `note`, `space`, `rank` | Optional metadata; omitted when unset |
| `restored` | True for a session rebuilt from saved state |
| `worktree` | Repository, branch, path, and `managed` for a git worktree |
| `server` | Set when a named server answered |
| `saved` | True for an on-disk session when no daemon runs |
| `agent_title` | Label taken from the session's first agent pane |

Pane fields:

| Field | Meaning |
|---|---|
| `id`, `title` | Pane identity and title |
| `workspace` | Workspace number |
| `foreground_cmd` | Program in the foreground; omitted for a plain shell and for a pane the user named |
| `agent_state` | Agent state, when an agent runs there |
| `agent_harness` | Which agent, for example `omp` or `claude-code` |
| `agent_state_at` | When the state began, in Unix **nanoseconds** |
| `agent_message`, `agent_kind`, `agent_queued` | What the agent is asking or doing |
| `completion_seq` | Finished turns the pane has counted |
| `program_status` | OSC 7501 records, when the program sends them |
| `scratch` | The session's scratch terminal |
| `note` | The pane's return note |

Optional fields are omitted rather than sent as `null`, so use `?` or `//`
instead of assuming a key exists.

Two other shapes matter:

- With no daemon, `tuios ls --json` prints the saved sessions (only `name`,
  `window_count`, `last_active`, `space`, `saved`, and `server` are meaningful)
  and exits 3.
- `tuios ls --all-hosts --json` prints an object, not an array:

```json
{
  "success": true,
  "message": "command executed",
  "hosts": [
    {
      "host": "laptop",
      "status": "up",
      "stale": false,
      "fetched_at": 1794575464,
      "sessions": [ ... ]
    }
  ]
}
```

A host that did not answer carries `error`; rows it gave earlier carry
`stale` and `fetched_at`. `status` is one of `up`, `connecting`,
`reconnecting`, `unreachable`, `no_daemon`, `no_tuios`, `incompatible`, or
`tailscale_check`.
A verb failure prints `{"success": false, "error": "..."}` and exits non-zero.

### Capture once, then query

Calling the daemon for every question is fine for interactive use. For a
batch, save one snapshot and query the file:

```nu
^tuios ls --json | save -f /tmp/tuios-ls.json
```

Nushell's `open` recognizes `.json`, so the native path is:

```nu
open /tmp/tuios-ls.json | length  # 7
```

The jq path is:

```nu
^jq 'length' /tmp/tuios-ls.json  # 7
```

For live output, pipe directly. Nushell passes the external command's stdout
to jq's stdin:

```nu
^tuios ls --json | jq -r '.[].name'
```

prints:

```text
Gaurav-Gosain-tuios-help-mode
lzv-book
rak
session-0
tuios
session-1
jq
```

`jq -r` prints one name per line. In Nushell that becomes a list of strings
after `lines`:

```nu
^tuios ls --json | jq -r '.[].name' | lines
```

### Discovery: what fields does this build emit?

Never guess the schema; ask the JSON. This is the first thing to run on a new
`tuios` version:

```nu
# Session keys, from the first row
^jq '.[0] | keys' /tmp/tuios-ls.json

# Every distinct set of pane keys, including optional fields
^jq -c '[.[].windows[] | keys] | unique' /tmp/tuios-ls.json

# Every path to a scalar in the first session
^jq -r '.[0] | paths(scalars) | join(".")' /tmp/tuios-ls.json

# One whole session, compacted to one line
^jq -c '.[0]' /tmp/tuios-ls.json | lines | first
```

The pane-key query is the useful one: a build with agent reporting adds
`agent_state`, `agent_harness`, and friends, and the `unique` shows you
exactly which combinations occur.

### Session-level munging

Count sessions:

```nu
^tuios ls --json | jq 'length'  # 7
```

Names, one per line:

```nu
^tuios ls --json | jq -r '.[].name'
```

prints:

```text
Gaurav-Gosain-tuios-help-mode
lzv-book
rak
session-0
tuios
session-1
jq
```

Names of attached sessions only:

```nu
^tuios ls --json | jq -r '.[] | select(.attached) | .name'
```

prints:

```text
Gaurav-Gosain-tuios-help-mode
lzv-book
jq
```

A table for a human, with a header row:

```nu
^tuios ls --json | jq -r '
  ["name", "windows", "attached"],
  (.[] | [.name, .window_count, .attached])
  | @tsv
'
```

prints:

```text
name	windows	attached
Gaurav-Gosain-tuios-help-mode	7	true
lzv-book	4	true
rak	2	false
session-0	1	false
tuios	7	false
session-1	2	false
jq	4	true
```

The same lines as a Nushell list, one string per row:

```nu
^tuios ls --json | jq -r '
  ["name", "windows"],
  (.[] | [.name, .window_count])
  | @tsv
' | lines
```

`sort_by` must happen before the `@tsv` conversion:

```nu
^tuios ls --json | jq -r '
  ["name", "windows"],
  (sort_by(-.window_count)[] | [.name, .window_count])
  | @tsv
'
```

prints:

```text
name	windows
Gaurav-Gosain-tuios-help-mode	7
tuios	7
lzv-book	4
jq	4
rak	2
session-1	2
session-0	1
```

Total panes across all sessions:

```nu
^tuios ls --json | jq '[.[].window_count] | add'  # 27
```

Busiest session:

```nu
^tuios ls --json | jq -r 'max_by(.window_count) | "\(.name) (\(.window_count))"'  # tuios (7)
```

Sessions with more than three panes, using a JSON parameter rather than
splicing the number into the program:

```nu
let n = 3
^tuios ls --json | jq --argjson n $n -c '[.[] | select(.window_count >= $n) | .name]'  # ["Gaurav-Gosain-tuios-help-mode","lzv-book","tuios","jq"]
```

Recently active sessions (last 24 hours):

```nu
^tuios ls --json | jq -c '[.[] | select((now - .last_active) < 86400) | .name]'  # ["Gaurav-Gosain-tuios-help-mode","lzv-book","rak","session-1","jq"]
```

Ages in minutes, as a table:

```nu
^tuios ls --json | jq -r '
  .[] | [.name, ((now - .last_active) / 60 | floor | tostring) + "m"]
  | @tsv
'
```

prints:

```text
Gaurav-Gosain-tuios-help-mode	853m
lzv-book	1058m
rak	1053m
session-0	8396m
tuios	8396m
session-1	952m
jq	25m
```

Creation and last-activity times as ISO 8601:

```nu
^tuios ls --json | jq -r '
  .[] | [.name, (.created | todate), (.last_active | todate)] | @tsv
'
```

prints:

```text
Gaurav-Gosain-tuios-help-mode	2026-11-08T19:19:36Z	2026-11-14T01:03:12Z
lzv-book	2026-11-08T19:19:36Z	2026-11-13T21:38:21Z
rak	2026-11-08T19:19:36Z	2026-11-13T21:42:41Z
session-0	2026-11-08T19:19:36Z	2026-11-08T19:19:36Z
tuios	2026-11-08T19:19:36Z	2026-11-08T19:19:36Z
session-1	2026-11-13T23:15:07Z	2026-11-13T23:23:35Z
jq	2026-11-13T23:23:35Z	2026-11-14T14:50:44Z
```

Sessions whose pane directory is a given name:

```nu
^tuios ls --json | jq -c --arg d mermaid '[.[] | select(.dir == $d) | .name]'  # []
```

Restored sessions, which nobody has attached to since the daemon rebuilt them:

```nu
^tuios ls --json | jq -r '[.[] | select(.restored) | .name] | join(", ")'  # session-0, tuios
```

Sessions that span several workspaces:

```nu
^tuios ls --json | jq -c '
  .[] | .name as $s
  | ([.windows[].workspace] | unique | length) as $w
  | select($w > 1)
  | {session: $s, workspaces: $w}
'
```

prints:

```text
{"session":"Gaurav-Gosain-tuios-help-mode","workspaces":6}
{"session":"lzv-book","workspaces":3}
{"session":"rak","workspaces":2}
{"session":"tuios","workspaces":7}
{"session":"jq","workspaces":2}
```

### Pane-level munging

The session array nests panes. Flatten it once, carrying the session name
down, and every later query becomes a filter over pane records:

```nu
^tuios ls --json | jq -c '
  [.[] as $s | $s.windows[] | {session: $s.name, title, workspace}]
'
```

For a read-only survey, a table is better than JSON:

```nu
^tuios ls --json | jq -r '
  .[] as $s
  | $s.windows[]
  | [$s.name, .workspace, (.foreground_cmd // "-"), .title]
  | @tsv
'
```

prints:

```text
Gaurav-Gosain-tuios-help-mode	1	omp	π > dim as help
Gaurav-Gosain-tuios-help-mode	2	lazygit	Terminal d961eced
Gaurav-Gosain-tuios-help-mode	3	nvim	Terminal 782a6244
Gaurav-Gosain-tuios-help-mode	4	nvim	Terminal 542898f3
Gaurav-Gosain-tuios-help-mode	5	omp	π > 󰋊 QUOTA: Explain go build disk quota failure
Gaurav-Gosain-tuios-help-mode	6	omp	π >  TUIOS: Implement keep-both behavior for alt+tab
Gaurav-Gosain-tuios-help-mode	6	man	Terminal ef5456ca
lzv-book	1	-	π >  SLVT: Build SvelteKit LazyVim course site with index
lzv-book	2	-	Terminal d36b19f9
lzv-book	3	omp	π > 󰙅 TREE: Add status icons to Neo-tree
lzv-book	3	-	Terminal 778cbd0d
rak	1	-	cog@om:~
rak	2	-	cog@om:~/.local/share/tuios/worktrees/cognominal---rakudo/rak
session-0	1	-	cog@om:~/.config/omarchy/plugins/felixzsh.key-visualizer
tuios	1	-	nvvim tuios
tuios	2	-	cog@om:~/git/Gaurav-Gosain---tuios-docs
tuios	3	-	cog@om:~/git/Gaurav-Gosain---tuios
tuios	4	-	π > 󰌐 HYPR: Disable Left-Alt Space hotkey
tuios	5	-	Terminal e106d2a2
tuios	6	-	Terminal 26030ec3
tuios	7	-	π > 󰙅 WTREE: Prune stale git worktree help-mode
session-1	1	-	Terminal e12a56a3
session-1	1	omp	π >  PUBL: Publish site repo publicly
jq	1	nvim	Terminal 236a587e
jq	1	-	~
jq	2	omp	π >  YANK: Yank text range in LazyVim
jq	2	omp	π >  JQTYPE: Print jq entity type
```

Panes per workspace, per session:

```nu
^tuios ls --json | jq -c '
  .[] | .name as $s
  | [.windows | group_by(.workspace)[]
     | {workspace: .[0].workspace, panes: length}]
  | {session: $s, workspaces: .}
'
```

prints:

```text
{"session":"Gaurav-Gosain-tuios-help-mode","workspaces":[{"workspace":1,"panes":1},{"workspace":2,"panes":1},{"workspace":3,"panes":1},{"workspace":4,"panes":1},{"workspace":5,"panes":1},{"workspace":6,"panes":2}]}
{"session":"lzv-book","workspaces":[{"workspace":1,"panes":1},{"workspace":2,"panes":1},{"workspace":3,"panes":2}]}
{"session":"rak","workspaces":[{"workspace":1,"panes":1},{"workspace":2,"panes":1}]}
{"session":"session-0","workspaces":[{"workspace":1,"panes":1}]}
{"session":"tuios","workspaces":[{"workspace":1,"panes":1},{"workspace":2,"panes":1},{"workspace":3,"panes":1},{"workspace":4,"panes":1},{"workspace":5,"panes":1},{"workspace":6,"panes":1},{"workspace":7,"panes":1}]}
{"session":"session-1","workspaces":[{"workspace":1,"panes":2}]}
{"session":"jq","workspaces":[{"workspace":1,"panes":2},{"workspace":2,"panes":2}]}
```

Which programs occupy panes:

```nu
^tuios ls --json | jq -c '
  [.[] | .windows[] | .foreground_cmd // empty]
  | group_by(.)
  | map({cmd: .[0], panes: length})
  | sort_by(-.panes)
'
```

`// empty` drops panes with no foreground command (a plain shell, or a pane
the user named), so the histogram is about programs, not shells.

Placeholder shells, whose titles are still `Terminal <id>`:

```nu
^tuios ls --json | jq -r '
  .[] as $s
  | $s.windows[]
  | select(.title | startswith("Terminal "))
  | [$s.name, .workspace, .title] | @tsv
'
```

prints:

```text
Gaurav-Gosain-tuios-help-mode	2	Terminal d961eced
Gaurav-Gosain-tuios-help-mode	3	Terminal 782a6244
Gaurav-Gosain-tuios-help-mode	4	Terminal 542898f3
Gaurav-Gosain-tuios-help-mode	6	Terminal ef5456ca
lzv-book	2	Terminal d36b19f9
lzv-book	3	Terminal 778cbd0d
tuios	5	Terminal e106d2a2
tuios	6	Terminal 26030ec3
session-1	1	Terminal e12a56a3
jq	1	Terminal 236a587e
```

Agent panes, with session, harness, and state:

```nu
^tuios ls --json | jq -c '
  [.[] as $s
   | $s.windows[]
   | select(.agent_state)
   | {session: $s.name, harness: .agent_harness, state: .agent_state,
      seq: .completion_seq}]
'
```

Which agent runs where, as a histogram:

```nu
^tuios ls --json | jq -c '
  [.[] | .windows[] | select(.agent_harness) | .agent_harness]
  | group_by(.)
  | map({harness: .[0], panes: length})
  | sort_by(-.panes)
'  # [{"harness":"omp","panes":7}]
```

`agent_state_at` is in nanoseconds, unlike the session timestamps:

```nu
^tuios ls --json | jq -r '
  .[0].windows[]
  | select(.agent_state_at)
  | [.title, (.agent_state_at / 1000000000 | floor | todate)] | @tsv
'
```

prints:

```text
π > dim as help	2026-11-11T13:02:58Z
π > 󰋊 QUOTA: Explain go build disk quota failure	2026-11-11T01:07:54Z
π >  TUIOS: Implement keep-both behavior for alt+tab	2026-11-11T01:52:04Z
```

Panes a given agent is waiting on:

```nu
^tuios ls --json | jq -r '
  .[] as $s
  | $s.windows[]
  | select(.agent_state == "needs_input")
  | [$s.name, .workspace, .title, (.agent_kind // "-"), (.agent_message // "-")]
  | @tsv
'  # (no rows)
```

The session's scratch terminal is marked `scratch`; a rail hides it. Drop it
when the listing should match what the attached client draws:

```nu
^tuios ls --json | jq -c '[.[] as $s | $s.windows[] | select(.scratch | not) | {session: $s.name, title}]'
```

### Cross-session aggregation

Worktree sessions, grouped by repository:

```nu
^tuios ls --json | jq -c '
  [.[] | select(.worktree) | .worktree.repo]
  | group_by(.)
  | map({repo: .[0], sessions: length})
  | sort_by(-.sessions)
'
```

A full worktree view, including whether TUIOS created it:

```nu
^tuios ls --json | jq -c '
  [.[] | select(.worktree)
   | {name, repo: .worktree.repo, branch: .worktree.branch,
      path: .worktree.path, managed: (.worktree.managed // false)}]
'
```

Session name to ID, as one object:

```nu
^tuios ls --json | jq -c 'reduce .[] as $s ({}; .[$s.name] = $s.id)'
```

The same with the builtin:

```nu
^tuios ls --json | jq -c 'INDEX(.[]; .name) | map_values(.id)'
```

Counts by attachment and restore state in one pass:

```nu
^tuios ls --json | jq -c '
  {
    total: length,
    attached: ([.[] | select(.attached)] | length),
    restored: ([.[] | select(.restored)] | length),
    worktrees: ([.[] | select(.worktree)] | length)
  }
'  # {"total":7,"attached":3,"restored":2,"worktrees":4}
```

### A second document: `tuios worktree ls --json`

`ls --json` nests a reduced `worktree` object in each session. The `worktree`
command asks a narrower question with more git in the answer: one row per
session whose directory is inside a git repository. `--json` prints those rows
as a flat array, one object per session, with no wrapper:

```json
[
  {
    "session": "Gaurav-Gosain-tuios-help-mode",
    "repo": "Gaurav-Gosain---tuios",
    "repo_root": "/home/cog/git/Gaurav-Gosain---tuios",
    "branch": "help-mode",
    "path": "/home/cog/.local/share/tuios/worktrees/Gaurav-Gosain---tuios/help-mode",
    "base": "",
    "group": "",
    "fan_id": "",
    "main": false,
    "managed": true,
    "gone": false,
    "state": "done",
    "harness": "omp",
    "windows": 11,
    "attached": true,
    "prompt_status": "",
    "prompt_note": "",
    "prompt_ready_by": "",
    "agent": "",
    "changes": 0,
    "ahead": null,
    "merged": false
  },
  {
    "session": "matt ai attention",
    "repo": "teachme",
    "repo_root": "/home/cog/teachme",
    "branch": "main",
    "path": "/home/cog/teachme",
    "base": "",
    "group": "",
    "fan_id": "",
    "main": true,
    "managed": false,
    "gone": false,
    "state": "none",
    "harness": "",
    "windows": 2,
    "attached": false,
    "prompt_status": "",
    "prompt_note": "",
    "prompt_ready_by": "",
    "agent": "",
    "changes": 0,
    "ahead": null,
    "merged": true,
    "merged_into": "main"
  }
]
```

The second row is there on purpose: the daemon records a worktree for every
session inside a repository, the main checkout included, and `main: true`
marks those. No worktree verb acts on a main checkout, so a listing of actual
worktrees filters them out:

```nu
^tuios worktree ls --json | jq -c '[.[] | select(.main | not) | .session]'  # ["Gaurav-Gosain-tuios-help-mode","session-0","tuios","session-1"]
```

Row fields:

| Field | Meaning |
|---|---|
| `session` | The session name, the one `tuios attach` takes |
| `repo` | The repository's name, the base name of `repo_root` |
| `repo_root` | The repository's main checkout on this machine |
| `branch` | The branch checked out in the worktree |
| `path` | The directory the session's panes start in |
| `base` | The ref the branch was created from, when tuios created it; empty on a detected worktree and on a main checkout |
| `group` | The branch stem of the fan-out this session belongs to; empty for a worktree made on its own |
| `fan_id` | Which fan-out, so two of the same name stay apart; empty outside one |
| `main` | True when the row is the repository's main checkout |
| `managed` | True when tuios created the worktree under its own directory |
| `gone` | True when the managed worktree's directory was removed and the session was kept; a detected worktree whose directory vanished drops out of the listing instead |
| `state` | The most urgent agent state across the panes: `none`, `working`, `needs_input`, `idle`, `done`, `errored`, `unknown`, `limit_reached` |
| `harness` | The harness id of the first pane running an agent; empty when none |
| `windows` | Pane count |
| `attached` | A client is attached |
| `prompt_status` | What became of a fan prompt: `""`, `pending`, `held`, `sent`, `not_sent`, `stalled` |
| `prompt_note` | One sentence on a `not_sent` or `stalled` prompt |
| `prompt_ready_by` | The evidence the agent was ready when the prompt was typed (`idle`, `done`, `quiet`); empty until then |
| `agent` | The agent a fan-out started here, as the caller named it (`claude`, `codex --model o5`) |
| `changes` | Paths that differ from HEAD, untracked files included; `-1` when git failed; `null` under `--fast` |
| `ahead` | Commits on HEAD that `base` does not have; `null` when there is no base or git failed |
| `merged` | True when the branch has commits of its own and its base, or that base's upstream, already holds them |
| `merged_into` | The ref that holds them; omitted when `merged` is false |
| `pr` | The branch's pull request, once tuios knows of one |
| `setup` | The worktree's setup record, when it ran one |

A fan session's row carries the fan fields on top, and `pr` and `setup` appear
only when there is one to report:

```json
{
  "group": "fan/retry", "fan_id": "9d1c...", "prompt_status": "sent",
  "prompt_ready_by": "idle", "agent": "claude",
  "pr": {"number": 42, "url": "https://github.com/o/r/pull/42",
         "state": "open", "checks": "fail", "passed": 3, "failed": 2,
         "pending": 1, "branch": "fan/retry-2",
         "checked_at": 1794233298104521300},
  "setup": {"command": "pnpm i", "state": "passed", "agent": "started",
            "started_at": 1794233280747488300,
            "finished_at": 1794233298104521300, "tail": ["Done in 17s"]}
}
```

`pr` carries `number`, `url`, `state` (`open`, `merged` or `closed`),
`checks` (`pass`, `fail` or `pending`, omitted when the pull request has
none), the `passed`, `failed` and `pending` counts, `branch`, `title`, and
`checked_at` in Unix nanoseconds. `setup` carries `command`, `async`, `state`
(`pending`, `running`, `passed` or `failed`), `exit`, `started_at` and
`finished_at` in Unix nanoseconds, `tail` (at most four lines of the setup's
screen), `agent` (`waiting`, `started` or `not_started`), `shell`, `window`,
and, after a failed setup undid the worktree, `removed`, `branch_removed` and
`note`.

A few things the shape does not say:

- Three fields the `list-worktrees` verb computes do not reach this output:
  `launched_from`, `ignored` and `own_commits`. The CLI decodes each row into
  its own struct before printing, and those three are not in it; the close
  dialog asks the daemon for them directly.
- `changes` counts, it does not diff. `-1` means the git read failed, which is
  not the same as a clean worktree. `ahead` is `null`, not `0`, when there is
  no base to count from or the read failed.
- `--fast` skips the git walk behind those columns: `changes` and `ahead` are
  `null` and `merged` is `false` on every row. A `false` there means "not
  asked", not "not merged":

  ```nu
  ^tuios worktree ls --json --fast | jq -c '[.[] | select(.merged)]'   # []
  ```

- The merged check runs no fetch, and with no reflog a branch reads as not
  merged: it can miss a merged branch, never claim one that is not. A `main`
  row has no base, so the check compares that checkout's branch with itself; a
  `true` there repeats `branch` in `merged_into`, and the field is worth
  reading only on worktree rows.
- With no daemon, a refused verb or a broken link, `--json` prints
  `{"error": "...", "success": false}` and exits 1. That is 1, not the 3
  `ls --json` exits when it falls back to sessions on disk: `worktree ls`
  asks the daemon and has no saved form. A failure that came through `--host`
  adds `host` and `untrusted: true`.
- `--repo` and `--group` filter on the daemon, and `--host` sends the same
  verb over the link. The shape does not change: an array, `[]` when nothing
  matches.

### Querying worktree rows

The table the command draws without `--json` has SESSION, REPO, BRANCH, AGENT,
CHANGES, MERGED, PROMPT, SETUP, PR and STATUS. To draw your own:

```nu
^tuios worktree ls --json | jq -r '
  ["session", "repo", "branch", "state", "changes", "merged"],
  (.[] | [.session, .repo, .branch, .state,
          (.changes // "-" | tostring),
          (if .merged then (.merged_into // "yes") else "-" end)])
  | @tsv
'
```

prints:

```text
session	repo	branch	state	changes	merged
Gaurav-Gosain-tuios-help-mode	Gaurav-Gosain---tuios	help-mode	done	0	-
session-0	felixzsh.key-visualizer	consecutive-chars	none	3	consecutive-chars
tuios	Gaurav-Gosain---tuios	main	none	0	-
session-1	cognominal.github.io	master	done	0	-
```

Where the uncommitted work is:

```nu
^tuios worktree ls --json | jq -c '
  [.[] | select((.changes // 0) > 0) | {session, changes}]
  | sort_by(-.changes)
'  # [{"session":"session-0","changes":3}]
```

Branches that have landed:

```nu
^tuios worktree ls --json | jq -r '
  .[] | select(.merged) | "\(.branch) -> \(.merged_into)"
'  # consecutive-chars -> consecutive-chars
```

Commits the base does not have, longest first:

```nu
^tuios worktree ls --json | jq -c '
  [.[] | select((.ahead // 0) > 0) | {session, ahead}]
  | sort_by(-.ahead)
'  # []
```

Fan prompts still waiting on something:

```nu
^tuios worktree ls --json | jq -c '
  [.[] | select(.prompt_status | IN("pending", "held", "stalled", "not_sent"))
   | {session, prompt_status, prompt_note}]
'  # []
```

`IN` is jq 1.6 and later. An empty `prompt_status` is not in the list, so rows
with no prompt are dropped.

Setups that failed, with the last line they printed:

```nu
^tuios worktree ls --json | jq -c '
  [.[] | select(.setup.state == "failed")
   | {session, exit: .setup.exit, tail: (.setup.tail[-1] // "-")}]
'  # []
```

Pull requests whose checks fail:

```nu
^tuios worktree ls --json | jq -c '
  [.[] | select(.pr.checks == "fail") | {session, pr: .pr.number, url: .pr.url}]
'  # []
```

Per repository, with the uncommitted work in each:

```nu
^tuios worktree ls --json | jq -c '
  group_by(.repo)
  | map({repo: .[0].repo, sessions: length,
         changes: ([.[] | .changes // 0] | add)})
  | sort_by(-.sessions)
'
```

`group_by` sorts by `repo` first, so the groups come out in repository order.

The two documents share `session` and each carries what the other lacks:
worktree rows have the git facts, `ls --json` has `dir`, `agent_title` and the
pane titles. Join them with `INDEX`:

```nu
^tuios ls --json | save -f /tmp/tuios-ls.json
^tuios worktree ls --json | save -f /tmp/tuios-wt.json
^jq -n --slurpfile ls /tmp/tuios-ls.json --slurpfile wt /tmp/tuios-wt.json '
  INDEX($ls[0][]; .name) as $by_name
  | [$wt[0][]
     | {session, branch,
        dir: $by_name[.session].dir,
        panes: ($by_name[.session].windows | length)}]
'
```

prints:

```text
[
  {
    "session": "Gaurav-Gosain-tuios-help-mode",
    "branch": "help-mode",
    "dir": "help-mode",
    "panes": 7
  },
  {
    "session": "session-0",
    "branch": "consecutive-chars",
    "dir": "felixzsh.key-visualizer",
    "panes": 1
  },
  {
    "session": "tuios",
    "branch": "main",
    "dir": "Gaurav-Gosain---tuios",
    "panes": 7
  },
  {
    "session": "session-1",
    "branch": "master",
    "dir": "~",
    "panes": 2
  }
]
```

A session the worktree listing knows and `ls` does not reads as `null` and 0
panes instead of failing the program: indexing `null` gives `null`, and
`length` on it gives 0.

### Turning names into commands

Quote each session name for the shell with `@sh`, so a name with spaces stays
one argument:

```nu
^tuios ls --json | jq -r '.[] | "tuios attach \(.name | @sh)"'
```

prints:

```text
tuios attach 'Gaurav-Gosain-tuios-help-mode'
tuios attach 'lzv-book'
tuios attach 'rak'
tuios attach 'session-0'
tuios attach 'tuios'
tuios attach 'session-1'
tuios attach 'jq'
```

Or produce argv arrays, one JSON array per line:

```nu
^tuios ls --json | jq -c '.[] | ["tuios", "attach", .name]'
```

prints:

```text
["tuios","attach","Gaurav-Gosain-tuios-help-mode"]
["tuios","attach","lzv-book"]
["tuios","attach","rak"]
["tuios","attach","session-0"]
["tuios","attach","tuios"]
["tuios","attach","session-1"]
["tuios","attach","jq"]
```

Then feed a picker. `fzf` receives the raw list:

```nu
^tuios ls --json
| jq -r '.[] | [.name, .window_count, (.worktree.branch // "-")] | @tsv'
| fzf --with-nth=1,2,3
```

Do not `eval` a generated command line unless you trust every source of the
name. `@sh` quotes correctly, but a session name is still data, not code.

### Searching with `--arg`

A literal query is fine, but user input belongs in `--arg`:

```nu
let q = "tuios"
^tuios ls --json
| jq --arg q $q -c '
    [.[] | select(.name | test($q; "i"))
     | {name, window_count, dir}]
  '
```

`test` treats the argument as a regular expression. For a plain substring,
escape it or use `contains`:

```nu
let q = "ai"
^tuios ls --json | jq --arg q $q -c '[.[] | select(.name | contains($q)) | .name]'  # ["Gaurav-Gosain-tuios-help-mode"]
```

### Feeding jq's output back into Nushell

jq prints a stream of JSON values, while Nushell's `from json` expects one
document. Two clean ways to bridge that:

1. Make jq emit a single array:

```nu
^tuios ls --json | jq -c '[.[] | select(.attached) | .name]' | from json
```

2. Emit one compact object per line and parse each line:

```nu
^tuios ls --json
| jq -c '.[] | {name, window_count}'
| lines
| each { from json }
| where window_count > 5
```

prints:

![Nushell table: row 0, Gaurav-Gosain-tuios-help-mode, window_count 7; row 1, tuios, window_count 7](https://gist.githubusercontent.com/cognominal/6cb78ab9c9d54ac552dbcaf93436100c/raw/377957e1edebf60550df05d3e2170148f4c5afa9/nu-where-window-count.png)

The second form fails if you pipe `jq -c '.[] | ...'` straight into
`from json`, because that output is several documents, not one:

```nu
# Error: trailing characters after the first JSON value
^tuios ls --json | jq -c '.[] | {name}' | from json
```

Native Nushell (`from json`) is often shorter for simple filters:

```nu
^tuios ls --json | from json | where attached | get name
^tuios ls --json | from json | get window_count | math sum
^tuios ls --json | from json | select name window_count | to tsv
```

prints:

```text
name	window_count
Gaurav-Gosain-tuios-help-mode	7
lzv-book	4
rak	2
session-0	1
tuios	7
session-1	2
jq	4
```

Use jq when the transformation is deep, when you want `@sh`/`@csv`, or when
the program must be portable across shells. Use Nushell when the result is
going straight into another Nushell command.

### Exit status in Nushell

`jq -e` is the assertion form, but Nushell does not throw on a non-zero
external status. Inspect it with `complete`:

```nu
^tuios ls --json | jq -e 'any(.[]; .attached)' | complete | get exit_code  # 0
```

The same for the daemon itself, which exits 3 when it is not running and the
rows came from disk:

```nu
^tuios ls --json | complete | select exit_code
```

`$env.LAST_EXIT_CODE` holds the status of the most recent external command:

```nu
^tuios ls --json | ignore
$env.LAST_EXIT_CODE  # 0
```

### Nushell quoting rules that matter for jq

Use a raw string for a jq program that contains `$`, `"`, or `\`. A Nushell
raw string is `r#'...'#`; its contents are literal:

```nu
let q = "tuios"
^tuios ls --json
| jq --arg q $q r#'[.[] | select(.name | test($q; "i"))] | length'#  # 2
```

Inside `r#'...'#`:

- `$q` is jq's variable, not Nushell's; Nushell does not interpolate it.
- The double quotes around `"i"` need no escaping.
- Backslashes are literal, so a regex like `\d+` survives.

A double-quoted Nushell string is the wrong tool here: it interpolates
`$q` before jq starts, and its own quotes must be escaped. A single-quoted
Nushell string also works for programs without single quotes, but it still
needs escaping for embedded quotes.

Pass values, never program text:

```nu
let q = "tuios"
# good: the value is an argument, so jq never parses it as code
^tuios ls --json | jq --arg q $q -c '[.[] | select(.name | contains($q)) | .name]'  # ["Gaurav-Gosain-tuios-help-mode","tuios"]
```

Splicing the value into the program text is the thing to avoid: a value that
contains `"` or `)` can change the filter, and a value that contains `$` can
change what jq thinks is a variable.

### jq and Nushell compared

| Task | jq | Nushell |
|---|---|---|
| Filter rows | `select(.attached)` | `where attached` |
| Pick fields | `{name, w: .window_count}` | `select name w` |
| Transform rows | `map(f)` | `each { f }` |
| Sort | `sort_by(.last_active)` | `sort-by last_active` |
| Group | `group_by(.dir)` | `group-by dir` |
| Count | `length` | `length` |
| Sum | `[.[].window_count] \| add` | `get window_count \| math sum` |
| Default | `.branch // "-"` | `default "-"` on the value |
| Join | `join(", ")` | `str join ", "` |
| TSV | `@tsv` | `to tsv` |
| JSON | `tojson` | `to json` |
| Raw text | `-r` | `to text` |

The `select` name is the trap: in jq it filters values; in Nushell it chooses
columns. Nushell's filter is `where`.

### A complete session report

Putting the pieces together, a compact report of what the daemon holds:

```nu
^tuios ls --json | jq -r '
  "sessions: \(length)",
  "attached: \([.[] | select(.attached)] | length)",
  "panes:    \([.[].window_count] | add)",
  "",
  (["name", "panes", "workspace", "branch", "restored"] | @tsv),
  (sort_by(-.window_count)[]
   | [.name, .window_count,
      (.current_workspace // 0 | tostring),
      (.worktree.branch // .branch // "-"),
      (.restored // false | tostring)]
   | @tsv)
'
```

prints:

```text
sessions: 7
attached: 3
panes:    27

name	panes	workspace	branch	restored
Gaurav-Gosain-tuios-help-mode	7	3	help-mode	false
tuios	7	7	main	true
lzv-book	4	3	-	false
jq	4	2	-	false
rak	2	1	-	false
session-1	2	1	master	false
session-0	1	1	consecutive-chars	true
```

The header array and each data row go through `@tsv` separately. The plain
strings above them are emitted as they are. In jq 1.8, `@tsv` accepts only an
array, so wrapping each array also keeps the formatting local to the rows.

---

## Cheat sheet

| Goal | jq |
|---|---|
| Identity | `.` |
| Field | `.name`, `.["name"]` |
| Optional field | `.worktree?.branch` |
| Element | `.[0]`, `.[-1]`, `.[1:3]` |
| Iterate | `.[]`, `.[]?` |
| One output per item | `.panes[] \| .cmd` |
| Collect | `[.panes[].cmd]` |
| Object | `{name, n: (.panes \| length)}` |
| Computed key | `{(.name): .window_count}` |
| Filter | `select(.attached)` |
| Map | `map(.cmd)` |
| Sort | `sort_by(.cpu)`, `sort_by(-.cpu)` |
| Group | `group_by(.workspace)` |
| Unique | `unique_by(.cmd)` |
| Min/max | `min_by(.cpu)`, `max_by(.cpu)` |
| Sum | `[.[].window_count] \| add` |
| Length | `length` |
| Keys | `keys` |
| Has key | `has("windows")` |
| Default | `.branch // "-"` |
| Conditional | `if .x then a else b end` |
| Try | `try f catch g`, `f?` |
| Bind | `. as $x \| ...` |
| Fold | `reduce .[] as $x (0; . + $x)` |
| Index by key | `INDEX(.[]; .name)` |
| Delete | `del(.windows)` |
| Paths | `paths(scalars)` |
| Get/set path | `getpath(p)`, `setpath(p; v)` |
| Entries | `to_entries`, `with_entries(f)` |
| Recurse | `walk(f)` |
| Timestamp | `now`, `todate`, `fromdate`, `strftime` |
| TSV/CSV | `@tsv`, `@csv` |
| Shell quoting | `@sh` |
| Regex | `test(re; flags)`, `match`, `capture` |
| Raw output | `jq -r` |
| Compact output | `jq -c` |
| Assertion | `jq -e 'any(.[]; .attached)'` |

---

## Appendix: a field-by-field map of `ls --json`

Root for a local `ls --json`: an array of sessions. Per session:

```
name id created last_active window_count attached width height
windows[] current_workspace dir branch display_name accent note
space rank restored worktree{repo repo_root branch path managed ...}
server saved agent_title
```

Per window:

```
id title workspace foreground_cmd
agent_state agent_harness agent_state_at agent_reason agent_message
agent_kind agent_meta agent_queued agent_draft_held agent_settled
agent_quiet agent_subagents agent_subagent_list agent_parent
completion_seq program_status scratch note
```

Notes:

- `agent_state_at` is Unix nanoseconds; session times are Unix seconds.
- `windows` is a summary. A pane's full state is not in the listing.
- `windows` is absent on a row from an older daemon; guard with
  `.windows[]?` or `select(.windows)`.
- `saved` rows carry zero values for `id`, `created`, `attached`, `width`,
  and `height`, and no `windows`; only `name`, `window_count`, `last_active`,
  `space`, `saved`, and `server` are meaningful. The command exits 3.
- `--all-hosts --json` nests reduced session rows under `hosts[].sessions`.
  Those rows carry `name`, `display_name`, `window_count`, `attached`,
  `restored`, `space`, `last_active`, and `created`; they are not the full
  session objects `ls --json` prints locally. The host entry carries `host`,
  `status`, `reason`, `error`, `stale`, `fetched_at`, and possibly
  `untrusted`.
- A failed verb with `--json` prints `{"success": false, "error": ...}` and
  exits non-zero.

`tuios worktree ls --json` prints a different document: a flat array with one
row per worktree session. Its fields are in "A second document: `tuios
worktree ls --json`" in Part 2.
