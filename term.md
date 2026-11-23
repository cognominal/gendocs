# Terminals, PTYs and Pipes in Unix

A long tutorial in C, Raku, Rust and Go (with the Charm libraries).

This document explains how Unix moves bytes between programs and people. It
covers three mechanisms that every shell user relies on, usually without
noticing them:

- **pipes**, the one-way byte channels behind `ls | grep foo`;
- **terminals** (TTYs), the kernel devices that turn keystrokes into lines,
  signals and job control;
- **pseudo-terminals** (PTYs), the software-only terminals that power
  terminal emulators, `ssh`, `tmux`, `script`, `expect` and every IDE
  console.

The first part is about concepts and works in any language. The second part
goes through four languages. Each one starts with an introduction to its
ecosystem: how to install it, compile and run code, manage packages and find
documentation. Then comes a series of programs that do the same jobs in that
language. The third part builds larger projects and compares the languages.
The appendices hold reference tables, a glossary, exercises and a
troubleshooting guide.

## Versions this was written against

The examples were written and checked on a Linux machine (Arch-based,
kernel 7.2) with these toolchains:

- GCC and Clang, glibc;
- Rakudo Star 2026.08 (Raku 6.d), with the modules it bundles;
- Rust 1.99 with Cargo;
- Go 1.27, with `charm.land/bubbletea/v2`, `charm.land/lipgloss/v2` and
  `charm.land/bubbles/v2`.

Most of the material applies to any modern Linux, and most of the C code
also builds on the BSDs and macOS. Platform differences are marked in the
text when they matter. Where a claim comes from reading a man page or the
source rather than from running code, the text says so.

## How to read this document

You can read it straight through, but it is also built to be skimmed:

- If you only want to know *why* `less` behaves differently when piped,
  read chapters 3 and 4.
- If you are about to write a TUI, read chapters 4, 7 and 8, then the
  chapter for your language.
- If you need to drive an interactive program from code (testing a REPL,
  automating `ssh`, recording a session), read chapter 6 and then the PTY
  chapter of your language.
- If you are writing a shell, read everything, then read it again.

Each code listing starts with a comment naming its file, for example
`// file: c/pipe_basic.c`. If you put the listings into those paths, the
build instructions in each language chapter work as written.
Appendix H has a short script that does it for you.

A note on the prompts used in the shell transcripts:

```text
$ command typed by you, as a normal user
# command typed as root (rare in this document)
> continuation line, or a prompt from the program being run
```

## Table of contents

[Part I: Concepts](#part-i-concepts)

1. [A short history of terminals](#1-a-short-history-of-terminals)
2. [File descriptors: the common currency](#2-file-descriptors-the-common-currency)
3. [Pipes](#3-pipes)
4. [The TTY layer: line discipline and termios](#4-the-tty-layer-line-discipline-and-termios)
5. [Sessions, process groups and job control](#5-sessions-process-groups-and-job-control)
6. [Pseudo-terminals](#6-pseudo-terminals)
7. [Talking to the screen: escape sequences](#7-talking-to-the-screen-escape-sequences)
8. [Window size, terminfo and terminal capabilities](#8-window-size-terminfo-and-terminal-capabilities)

[Part II: Languages](#part-ii-languages)

9. [C: the ecosystem](#9-c-the-ecosystem)
10. [C: pipes, fork and exec](#10-c-pipes-fork-and-exec)
11. [C: termios and raw mode](#11-c-termios-and-raw-mode)
12. [C: pseudo-terminals](#12-c-pseudo-terminals)
13. [C: a tiny job-control shell](#13-c-a-tiny-job-control-shell)
14. [Raku: the ecosystem](#14-raku-the-ecosystem)
15. [Raku: pipes and processes](#15-raku-pipes-and-processes)
16. [Raku: terminals and termios](#16-raku-terminals-and-termios)
17. [Raku: pseudo-terminals through NativeCall](#17-raku-pseudo-terminals-through-nativecall)
18. [Raku: TUIs with the Terminal modules](#18-raku-tuis-with-the-terminal-modules)
19. [Rust: the ecosystem](#19-rust-the-ecosystem)
20. [Rust: pipes and processes](#20-rust-pipes-and-processes)
21. [Rust: termios and raw mode](#21-rust-termios-and-raw-mode)
22. [Rust: pseudo-terminals](#22-rust-pseudo-terminals)
23. [Rust: TUIs with crossterm and ratatui](#23-rust-tuis-with-crossterm-and-ratatui)
24. [Go: the ecosystem](#24-go-the-ecosystem)
25. [Go: pipes and processes](#25-go-pipes-and-processes)
26. [Go: terminals with x/term](#26-go-terminals-with-xterm)
27. [Go: pseudo-terminals with creack/pty](#27-go-pseudo-terminals-with-creackpty)
28. [Go: the Charm stack (Bubble Tea, Lip Gloss, Bubbles, Wish)](#28-go-the-charm-stack)

[Part III: Projects and comparisons](#part-iii--projects)

29. [Project: `script` in four languages](#29-project-script-in-four-languages)
30. [Project: an `expect`-like driver](#30-project-an-expect-like-driver)
31. [Project: a terminal multiplexer in miniature](#31-project-a-terminal-multiplexer-in-miniature)
32. [Debugging terminals and pipes](#32-debugging-terminals-and-pipes)
33. [Comparing the four languages](#33-comparing-the-four-languages)

[Appendices](#appendices)

- [A. termios reference](#appendix-a-termios-reference)
- [B. Escape sequence reference](#appendix-b-escape-sequence-reference)
- [C. Signals reference](#appendix-c-signals-reference)
- [D. Glossary](#appendix-d-glossary)
- [E. Exercises](#appendix-e-exercises)
- [F. Troubleshooting](#appendix-f-troubleshooting)
- [G. Further reading](#appendix-g-further-reading)
- [H. Extracting the listings](#appendix-h-extracting-the-listings)

---

# Part I: Concepts

---

## 1. A short history of terminals

You cannot understand Unix terminal handling without knowing what it was
built for. Many design choices that look strange today made sense for a
machine that clattered, printed on paper and ran at 110 baud.

### 1.1 Teletypes

A *teletypewriter* (teletype, TTY) was an electromechanical typewriter
connected to a communication line. Pressing a key sent a character code down
the wire; characters arriving on the wire were printed on paper. Telegraph
companies used them long before computers, and so they were the natural
first way for a person to talk to a time-sharing computer.

The Teletype Model 33 ASR was the classic one. It was cheap, which made it
the default console of the minicomputers on which Unix was born (the PDP-7
and the PDP-11). Several of its properties live on in today's terminal
layer:

- It printed at 10 characters per second. So the computer had to deal with
  output faster than the device could take it. That is the origin of
  output buffering and of flow control (`^S`/`^Q`, XON/XOFF).
- It had separate *carriage return* (move the print head to column 0) and
  *line feed* (advance the paper one line) operations. Unix decided that
  lines in files end with a single LF (`\n`). The terminal driver therefore
  translates `\n` into `\r\n` on output: the `ONLCR` flag that you will meet
  in chapter 4.
- It had no screen and no cursor addressing. Editing a line meant sending
  special characters that the *computer* interpreted: erase the previous
  character (`#` in early Unix, later Backspace or DEL), kill the whole line
  (`@`, later `^U`). That interpretation lives in the kernel's *line
  discipline* to this day.
- It was half-duplex in spirit: the computer echoed what you typed so that
  it appeared on the paper. Echo is still done by the kernel, not by the
  keyboard (`ECHO` flag).

The abbreviation stuck. Device names on Linux are still `/dev/tty*`, and the
`tty` command prints the name of "the teletype" connected to your shell.

### 1.2 Glass teletypes and video terminals

In the 1970s, CRT terminals replaced paper. The first ones were "glass
TTYs": they behaved like a teletype that printed on a screen and scrolled
when the bottom was reached. Soon terminals gained *cursor addressing*: a
control sequence could move the cursor to any row and column, clear the
screen, insert lines, and so on. Full-screen programs like `vi` became
possible.

Every manufacturer invented its own control sequences. The ADM-3A used
`ESC = row col`. The Hazeltine 1500 used `~` as its escape character. The
VT52 used `ESC Y row col`. To cope with this, Bill Joy wrote the *termcap*
database for `vi` at Berkeley: a text file describing, for each terminal
type, which bytes perform which function. Programs looked up the terminal
type in the `TERM` environment variable and read the right entry. AT&T later
replaced termcap with the compiled *terminfo* database, which is what
`ncurses` uses today. Chapter 8 covers both.

### 1.3 The VT100 and ANSI X3.64

In 1978 DEC shipped the VT100. It implemented (an early version of) the
ANSI X3.64 standard, later ECMA-48 and ISO 6429. These standards define
*control sequences* that start with ESC `[` (the *Control Sequence
Introducer*, CSI), followed by numeric parameters and a final letter. For
example `ESC [ 2 J` clears the screen and `ESC [ 10 ; 20 H` moves the cursor
to row 10, column 20.

The VT100 sold well enough that its control sequences became the de facto
standard. Its successors (VT220, VT320, VT420, VT510, VT520) added features.
Almost every terminal emulator in use today, from xterm to Ghostty, claims
to be "VT100-compatible", with large extensions. When you print
`"\e[31m"` to get red text, you are speaking VT100/ECMA-48.

### 1.4 Serial lines and the kernel

Physical terminals were connected through RS-232 serial lines. The kernel
had to configure the line (baud rate, parity, number of data bits, stop
bits), detect when a modem hung up (carrier loss), and handle flow control.
All this configuration landed in the same structure as the line-editing
settings. That is why `struct termios` mixes things like `CS8` (8 data bits)
and `B9600` (baud rate) with `ICANON` (line editing) and `ISIG` (generate
signals from `^C`). On a pseudo-terminal, the baud rate and parity flags are
stored and reported but mean nothing.

### 1.5 Consoles and virtual consoles

The *system console* was the terminal attached directly to the machine; the
kernel printed its messages there. Linux implements *virtual consoles*
(`/dev/tty1` to `/dev/tty63`) on the PC's video hardware: you switch between
them with Ctrl+Alt+F1..F6. Each virtual console is a real kernel TTY device,
with a terminal emulator built into the kernel (`drivers/tty/vt/`). It
interprets a subset of VT102/ECMA-48 plus Linux-specific sequences, which is
why `TERM=linux` exists.

### 1.6 Terminal emulators and pseudo-terminals

When graphical workstations arrived, people wanted terminals in windows.
A program like `xterm` draws characters in a window, but the shell running
inside it still expects to talk to a TTY device: it wants line editing, `^C`
to send `SIGINT`, job control, window size. The solution is the
*pseudo-terminal*: a pair of devices where one end (the *slave*, or in
newer documentation the *subsidiary* or *replica*) behaves exactly like a
terminal to the program using it, while the other end (the *master*, or
*controller*/*manager*) is held by the terminal emulator. Whatever the
emulator writes into the master shows up as keyboard input on the slave,
and whatever the program writes into the slave can be read from the
master and drawn on screen.

PTYs were introduced in 4.2BSD (1983) for `rlogin` and `telnet`, then
standardized by POSIX in the late 1990s (`posix_openpt`, `grantpt`,
`unlockpt`, `ptsname`). Linux implements them with the `/dev/ptmx`
multiplexer and the `devpts` filesystem mounted on `/dev/pts`. Chapter 6
goes through this in detail.

A note on vocabulary: POSIX and most man pages still say *master* and
*slave*. Some newer documentation (including recent versions of the Linux
man-pages project and several libraries) uses other names. This tutorial
uses *master* and *slave* because that is what the system calls, constants
and man pages you will read use, and it gives the newer terms where they
help.

### 1.7 Where we are today

On a modern Linux desktop, when you open a terminal window and type `ls`,
the following happens:

1. Your terminal emulator (Ghostty, Alacritty, kitty, foot, GNOME Terminal,
   WezTerm, ...) opened `/dev/ptmx` and got a master file descriptor. The
   kernel created a matching slave, say `/dev/pts/3`.
2. It forked a child, which started a new session, opened `/dev/pts/3`
   (which became its controlling terminal), put it on file descriptors 0,
   1 and 2, and exec'ed your shell.
3. You press `l`. The emulator receives a key event from the window system,
   encodes it as the byte `0x6c`, and writes it to the master.
4. The kernel's line discipline on the slave side sees `l`. Because the
   shell's line editor (readline, zle, ...) has put the terminal in raw-ish
   mode, the byte goes straight to the shell's `read()`. The shell itself
   echoes it by writing `l` to the slave.
5. The emulator reads `l` from the master and draws it in the window.
6. You press Enter. The emulator writes `\r`. The shell sees it, restores
   the terminal to "cooked" mode, forks, and the child execs `ls`.
7. `ls` notices that its standard output is a terminal (`isatty(1)` is
   true), so it formats its output in columns, with colors, and writes it
   to the slave.
8. The line discipline translates `\n` to `\r\n` (`ONLCR`). The emulator
   reads from the master, parses the bytes (text, color escapes, CR, LF)
   and updates its screen grid.

If you run `ls | cat` instead, `ls` sees that its output is a *pipe*, not a
terminal, and prints one name per line without colors. That one decision,
"am I talking to a terminal?", explains a lot of the behavior we are about
to study.

### 1.8 Timeline

| Year | Event |
|------|-------|
| 1963 | Teletype Model 33 |
| 1969 | Unix on the PDP-7 |
| 1973 | Pipes added to Unix (V3) |
| 1975 | VT52 |
| 1978 | VT100; termcap |
| 1979 | V7 Unix, Bourne shell |
| 1980 | Job control in 4.1BSD |
| 1983 | 4.2BSD pseudo-terminals |
| 1984 | X Window System, xterm |
| 1988 | POSIX.1: termios |
| 1993 | ncurses |
| 1998 | Unix98 PTYs (posix_openpt) |
| 2000s | UTF-8 becomes the norm |
| 2010s | GPU terminals, truecolor |
| 2020s | kitty keyboard and graphics |

Some dates are approximate to the year; the order is what matters.

### 1.9 Doug McIlroy and pipes

Pipes have their own history. Doug McIlroy had argued since the mid-1960s
for "coupling programs like garden hose": connecting the output of one
program to the input of another. Ken Thompson implemented `pipe()` in
Unix in 1973, and rewrote much of the system's utilities to read standard
input and write standard output in a single night, according to the
well-known account. The `|` notation came shortly after. The *Unix
philosophy* that McIlroy later summarized ("write programs that do one
thing and do it well; write programs to work together; write programs to
handle text streams, because that is a universal interface") grew out of
this.

The rest of Part I explains each mechanism, starting from the thing they all
share: the file descriptor.

---

## 2. File descriptors: the common currency

### 2.1 What a file descriptor is

A *file descriptor* (fd) is a small non-negative integer that a process
uses to refer to an open I/O channel. The kernel keeps, for each process, a
*file descriptor table*: an array mapping integers to pointers to *open file
descriptions* (also called open file table entries, or `struct file` in the
Linux source).

```text
 process A fd table          open file descriptions       inodes / devices
 +----+------------+        +----------------------+
 | 0  | ---------------->   | /dev/pts/3, O_RDWR   | ---> pts device 136:3
 | 1  | ---------------->   |   offset: n/a        |
 | 2  | ---------------->   +----------------------+
 | 3  | ---------------->   +----------------------+
 +----+                     | notes.txt, O_RDONLY  | ---> inode 1234567
                            |   offset: 4096       |
                            +----------------------+
```

Three levels, and the distinction matters:

- The **fd** is per-process. Fd 3 in one process has nothing to do with fd
  3 in another.
- The **open file description** holds the file offset, the status flags
  (`O_APPEND`, `O_NONBLOCK`, ...) and the access mode. It is created by
  `open()`, `pipe()`, `socket()`, `posix_openpt()` and so on. Several fds,
  even in different processes, can point to the same description: after
  `dup()`, or in a child after `fork()`.
- The **inode or device** is the thing itself.

The *close-on-exec* flag (`FD_CLOEXEC`) is the one flag that belongs to the
fd, not to the description. That is why it is set with `F_SETFD` and not
`F_SETFL`.

Why this matters for us:

- After `fork()`, parent and child share the same open file descriptions.
  If the child reads from fd 0, it advances the same offset the parent sees.
  For a terminal or a pipe there is no offset, but they share the
  `O_NONBLOCK` flag. If a program sets its stdin to non-blocking and
  crashes, the *shell* that shares the description may find its own stdin
  non-blocking. This is a classic source of "my shell exits when I press a
  key" bugs.
- A pipe's read end reaches end-of-file only when *every* fd pointing to
  the write end's description, in every process, has been closed. Forgetting
  to close one copy is the number-one pipe bug (section 3.6).
- A terminal's master side sees hangup only when every fd on the slave has
  been closed.

### 2.2 The standard three

By convention, every process starts with three open fds:

| fd | name | C macro | stdio |
|----|------|---------|-------|
| 0 | stdin | `STDIN_FILENO` | `stdin` |
| 1 | stdout | `STDOUT_FILENO` | `stdout` |
| 2 | stderr | `STDERR_FILENO` | `stderr` |

The kernel knows nothing of this convention. A process inherits whatever
fds its parent had (minus those marked close-on-exec), and the shell sets
up 0, 1 and 2 before running a command. In an interactive shell, all three
point to the same open file description of the terminal slave device. You
can check this:

```text
$ ls -l /proc/$$/fd
lrwx------ 1 cog cog 64 Nov 22 10:00 0 -> /dev/pts/3
lrwx------ 1 cog cog 64 Nov 22 10:00 1 -> /dev/pts/3
lrwx------ 1 cog cog 64 Nov 22 10:00 2 -> /dev/pts/3
lrwx------ 1 cog cog 64 Nov 22 10:00 255 -> /dev/pts/3
```

(Bash keeps a private copy of the terminal on fd 255. Zsh uses a different
high number.)

In a pipeline, they differ:

```text
$ ls -l /proc/self/fd | cat
lr-x------ 1 cog cog 64 Nov 22 10:00 0 -> /dev/pts/3
l-wx------ 1 cog cog 64 Nov 22 10:00 1 -> pipe:[812345]
lrwx------ 1 cog cog 64 Nov 22 10:00 2 -> /dev/pts/3
lr-x------ 1 cog cog 64 Nov 22 10:00 3 -> /proc/1234/fd
```

Here `ls` sees fd 1 as a pipe, identified by an inode number in the
`pipefs` pseudo-filesystem.

### 2.3 Everything is a file (descriptor)

The same `read()` and `write()` system calls work on regular files,
directories (for `getdents`), pipes, FIFOs, sockets, terminals, PTY masters,
character devices, `eventfd`, `signalfd`, `timerfd`, `inotify`, `pidfd`,
`epoll` instances and more. They differ in their semantics:

| Kind | Seekable | Short reads | EOF |
|------|----------|-------------|-----|
| Regular file | yes | at end | offset at size |
| Pipe/FIFO | no | common | writers gone |
| Socket | no | common | peer shut down |
| Terminal | no | per line | `^D` or hangup |
| PTY master | no | common | `EIO` on Linux |

The "Short reads" column is the important one. On a regular file, `read(fd,
buf, 4096)` returns 4096 bytes unless you hit the end of the file. On a
pipe, socket or terminal, it returns *whatever is available*, at least one
byte, and blocks only when nothing is available. Code that assumes `read`
fills the buffer works on files and breaks on pipes. Every language's
standard library has a "read exactly n bytes" helper for this reason
(`read_exact` in Rust, `io.ReadFull` in Go, a loop in C).

The "EOF" column hides another trap: on Linux, reading from a PTY master
after the slave side has been closed returns `-1` with `errno == EIO`, not
`0`. Every PTY program has to treat `EIO` from the master as end-of-file.
Chapter 6 explains why.

### 2.4 Inspecting fds

Useful tools, all used throughout this document:

- `ls -l /proc/PID/fd` lists a process's fds and what they point to.
- `cat /proc/PID/fdinfo/N` shows the offset, flags (in octal) and more for
  one fd.
- `lsof -p PID` does the same, portably, with more decoding.
- `ss -xp` shows Unix sockets; `lsof -U` too.
- `strace -f -e trace=desc,process cmd` traces fd-related system calls of a
  command and its children.
- `stat -L /dev/stdin` tells you what kind of file your stdin is.

A quick experiment you should try now:

```text
$ stat -L -c '%F' /dev/stdin
character special file
$ echo | stat -L -c '%F' /dev/stdin
fifo
$ stat -L -c '%F' /dev/stdin < /etc/passwd
regular file
```

`/dev/stdin` is a symlink to `/proc/self/fd/0`, so `stat -L` reports on
whatever fd 0 points to. A terminal is a *character special file*; an
anonymous pipe reports as a *fifo*.

### 2.5 dup, dup2 and redirection

Redirection in the shell is built from two calls:

- `dup(oldfd)` returns the lowest-numbered free fd, pointing to the same
  open file description as `oldfd`.
- `dup2(oldfd, newfd)` makes `newfd` point to the same description as
  `oldfd`, closing `newfd` first if it was open. If `oldfd == newfd`, it
  does nothing.
- `dup3(oldfd, newfd, O_CLOEXEC)` (Linux) is `dup2` with a flag.

So `cmd > out.txt` in the shell is, in the child just before `exec`:

```c
int fd = open("out.txt", O_WRONLY | O_CREAT | O_TRUNC, 0666);
dup2(fd, 1);
close(fd);
execvp("cmd", argv);
```

And `cmd 2>&1` is `dup2(1, 2)`. The order of redirections matters because
each one is a `dup2` applied in sequence:

- `cmd > f 2>&1`: fd 1 becomes `f`, then fd 2 becomes a copy of fd 1,
  i.e. `f`. Both go to the file.
- `cmd 2>&1 > f`: fd 2 becomes a copy of fd 1 (the terminal), then fd 1
  becomes `f`. Errors still go to the terminal.

### 2.6 The lowest-free-fd rule

POSIX guarantees that `open()`, `pipe()`, `dup()` and friends return the
lowest-numbered free descriptor. Old code relies on this:

```c
close(0);
open("/dev/null", O_RDONLY);   /* guaranteed to be fd 0 */
```

Modern code should use `dup2` instead, which is explicit. But you need to
know the rule, because it has a consequence: if a process starts with fd
0, 1 or 2 *closed* (it can happen with daemons or careless parents), the
next file it opens will take that number, and a later `printf` may write
into that file. Robust programs that may be started oddly open `/dev/null`
on any closed standard fd at startup.

### 2.7 Close-on-exec and leaked fds

When a process calls `exec`, every fd without `FD_CLOEXEC` survives into
the new program. This is how stdin/stdout/stderr get passed on, and it is
also how fds *leak*. If your terminal emulator forgets to mark the PTY
master close-on-exec, every program started in the shell inherits a copy
of the master. Consequence: when the shell exits, the master is still open
in some background process, and things like hangup detection break.

Modern APIs take a flag to set close-on-exec atomically at creation:
`open(..., O_CLOEXEC)`, `pipe2(fds, O_CLOEXEC)`, `socket(..., SOCK_CLOEXEC)`,
`posix_openpt(O_RDWR | O_NOCTTY | O_CLOEXEC)` on recent glibc (check your
man page), `dup3(..., O_CLOEXEC)`, `fcntl(fd, F_DUPFD_CLOEXEC, n)`. Doing it
in two steps (`pipe()` then `fcntl(F_SETFD)`) leaves a window during which
another thread may `fork` and `exec` and leak the fd.

Rust and Go set close-on-exec on every fd they create, by default. Raku
(MoarVM, through libuv) does as well for the handles it opens. In C you
must do it yourself.

### 2.8 Blocking and non-blocking I/O

By default, `read()` on an empty pipe or terminal blocks until data
arrives, and `write()` to a full pipe blocks until there is room. Setting
`O_NONBLOCK` on the open file description changes that: the calls return
`-1` with `errno == EAGAIN` (equal to `EWOULDBLOCK` on Linux) instead of
blocking.

```c
int flags = fcntl(fd, F_GETFL);
fcntl(fd, F_SETFL, flags | O_NONBLOCK);
```

Remember that `O_NONBLOCK` is on the *description*, so it is shared with
every process holding a copy. Setting it on fd 0 inherited from your shell
affects the shell. Programs that need non-blocking stdin should either
restore the flag on exit (including on crash, which is hard), or avoid the
problem with `poll()` (wait until readable, then do a blocking read that
will not block), or open `/dev/tty` again to get a *new* description.

### 2.9 Waiting on many fds: select, poll, epoll

A terminal emulator, `ssh`, `script` and `tmux` all need to move data in
two directions at once: from the user to the child and from the child to
the user. A single thread doing blocking reads cannot do that, since it would
block on one side while data waits on the other. The options:

- **Two threads** (or two processes), one per direction. Simple, used by
  early `script` implementations (which forked) and by many Go programs
  (goroutines).
- **I/O multiplexing**: `select()`, `poll()` or Linux `epoll`. You ask the
  kernel "tell me when any of these fds is readable or writable", then do
  non-blocking or known-safe I/O. Used by C programs, `tmux`, and under the
  hood by every async runtime (libuv for Raku's MoarVM, mio for tokio, the
  Go runtime's netpoller).

`poll` is the portable choice for a handful of fds:

```c
struct pollfd pfd[2] = {
    { .fd = STDIN_FILENO, .events = POLLIN },
    { .fd = master_fd,    .events = POLLIN },
};
int n = poll(pfd, 2, -1);            /* -1: wait forever */
if (pfd[0].revents & POLLIN) { /* user typed something */ }
if (pfd[1].revents & (POLLIN | POLLHUP)) { /* child wrote or hung up */ }
```

Two details matter for terminals and pipes:

- `POLLHUP` is reported when the other side of a pipe or PTY is closed. On
  a pipe, you may still read remaining data; read until you get 0.
- On Linux, when the PTY slave is closed, the master reports `POLLHUP`
  (and often `POLLIN`); `read` then fails with `EIO`.

### 2.10 Signals, briefly

Signals are asynchronous notifications sent to a process. They matter here
because the terminal and pipe layers send them:

| Signal | Sent when | Default |
|--------|-----------|---------|
| `SIGINT` | `^C` typed | terminate |
| `SIGQUIT` | `^\` typed | core dump |
| `SIGTSTP` | `^Z` typed | stop |
| `SIGCONT` | `fg`/`bg` | continue |
| `SIGTTIN` | bg reads tty | stop |
| `SIGTTOU` | bg writes tty | stop |
| `SIGHUP` | terminal hung up | terminate |
| `SIGWINCH` | window resized | ignore |
| `SIGPIPE` | write to dead pipe | terminate |
| `SIGCHLD` | child changed state | ignore |

`SIGTTOU` on writes is only sent if the `TOSTOP` flag is set; by default
background jobs can write to the terminal freely. Appendix C has the full
table. Chapter 5 explains the job-control signals, chapter 3 explains
`SIGPIPE`, and chapter 8 explains `SIGWINCH`.

One concept that every language chapter will revisit: a system call
blocked in `read()` can be interrupted by a signal. It then fails with
`EINTR`, unless the signal handler was installed with `SA_RESTART`, in
which case the kernel restarts the call. C code must handle `EINTR`. Rust's
standard library retries on `EINTR` in its `read_exact`/`write_all`
helpers. Go's runtime retries internally. Raku's I/O goes through libuv,
which handles it.

### 2.11 A first program: what is on my fds?

Here is a small C program that reports what each of the standard fds is.
It uses `isatty()` and `fstat()`, the two calls that every program uses to
decide "am I talking to a terminal?".

```c
// file: c/fdinfo.c
#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <sys/stat.h>
#include <unistd.h>

static const char *kind(mode_t m)
{
    if (S_ISREG(m))  return "regular file";
    if (S_ISDIR(m))  return "directory";
    if (S_ISCHR(m))  return "character device";
    if (S_ISBLK(m))  return "block device";
    if (S_ISFIFO(m)) return "fifo/pipe";
    if (S_ISSOCK(m)) return "socket";
    if (S_ISLNK(m))  return "symlink";
    return "unknown";
}

int main(void)
{
    for (int fd = 0; fd <= 2; fd++) {
        struct stat st;
        if (fstat(fd, &st) == -1) {
            fprintf(stderr, "fd %d: closed\n", fd);
            continue;
        }
        const char *name = isatty(fd) ? ttyname(fd) : NULL;
        fprintf(stderr, "fd %d: %-16s tty=%s%s%s\n",
                fd, kind(st.st_mode),
                isatty(fd) ? "yes" : "no",
                name ? " " : "", name ? name : "");
    }
    return 0;
}
```

It writes to stderr so that its own output is visible even when stdout is
redirected. Try it in several situations:

```text
$ cc -Wall -o fdinfo c/fdinfo.c
$ ./fdinfo
fd 0: character device tty=yes /dev/pts/3
fd 1: character device tty=yes /dev/pts/3
fd 2: character device tty=yes /dev/pts/3
$ echo hi | ./fdinfo > /tmp/out
fd 0: fifo/pipe        tty=no
fd 1: regular file     tty=no
fd 2: character device tty=yes /dev/pts/3
$ ./fdinfo <&-
fd 0: closed
fd 1: character device tty=yes /dev/pts/3
fd 2: character device tty=yes /dev/pts/3
```

`<&-` closes stdin for the command. You will write the same program in each
language later; it is a good "hello world" for systems programming.

### 2.12 How isatty works

`isatty(fd)` is not magic. On Linux, glibc implements it by calling the
`TCGETS` ioctl (the one behind `tcgetattr`) on the fd. If the call
succeeds, the fd is a terminal; if it fails with `ENOTTY`, it is not. That
is the whole test. Other systems do the same thing with their own ioctl.

Consequences:

- A PTY slave and a PTY master both answer `TCGETS` on Linux, so
  `isatty(master_fd)` returns true. Do not rely on `isatty` to tell them
  apart.
- A program cannot "fake" being a terminal on a pipe. If you want a child
  to believe it is on a terminal (so that it colors its output, or flushes
  line by line), you must give it a PTY. This is the main reason PTYs are
  used outside terminal emulators, and the reason tools like `unbuffer`
  (from expect) and `script -q -c` exist.

### 2.13 stdio buffering: why output appears late

The C standard library buffers output in `FILE` objects, and the buffering
mode depends on what the fd is:

- `stderr` is unbuffered.
- `stdout` is **line buffered** if it is a terminal: flushed at each `\n`.
- `stdout` is **fully buffered** otherwise (pipe, file): flushed when the
  buffer (typically 4096 bytes or `BUFSIZ`, often 8192) is full, or at
  exit.

This explains a very common surprise:

```text
$ (while true; do date; sleep 1; done) | grep 2026        # works
$ python3 -c 'import time
while True:
    print(time.time()); time.sleep(1)' | grep .         # nothing appears
```

The second command prints nothing for a long time: Python sees a pipe on
stdout and buffers fully. Fixes: make the producer flush (`fflush`,
`print(..., flush=True)`, `python3 -u`), change its buffering from outside
(`stdbuf -oL cmd` works for programs using glibc stdio dynamically), or run
it under a PTY (`unbuffer cmd`, `script -q -c cmd /dev/null`), which makes
it think it is talking to a terminal.

Every language has its own version of this:

- **C**: `setvbuf(stdout, NULL, _IOLBF, 0)` or `fflush(stdout)`.
- **Raku**: `$*OUT.out-buffer` controls buffering. Rakudo enables output
  buffering when stdout is not a TTY, and you can set
  `$*OUT.out-buffer = False` to disable it, or call `$*OUT.flush`.
- **Rust**: `std::io::Stdout` is line buffered *always*, even on a pipe
  (as of current Rust; this has been discussed for years). Wrap it in a
  `BufWriter` for speed and call `flush()` when needed.
- **Go**: `os.Stdout` is unbuffered; every `fmt.Println` is a `write`
  system call. Use `bufio.NewWriter(os.Stdout)` and `Flush()` for speed.

Each language chapter comes back to this with a measured example.

---

## 3. Pipes

### 3.1 The pipe system call

A pipe is a unidirectional byte channel inside the kernel, with a read end
and a write end. You create one with:

```c
int fds[2];
if (pipe(fds) == -1) { perror("pipe"); exit(1); }
/* fds[0] is the read end, fds[1] is the write end */
```

Mnemonic: 0 is stdin (read), 1 is stdout (write), and the array is in the
same order. On Linux, `pipe2(fds, O_CLOEXEC | O_NONBLOCK)` lets you set
flags atomically. `O_DIRECT` asks for "packet mode" (each write is a
separate message; rarely used).

What you get:

- A kernel buffer. On Linux, 16 pages (65536 bytes with 4 KiB pages) by
  default. You can read and change it with `fcntl(fd, F_GETPIPE_SZ)` and
  `fcntl(fd, F_SETPIPE_SZ, n)`, up to `/proc/sys/fs/pipe-max-size` (1 MiB
  by default) for unprivileged users.
- Two open file descriptions, one read-only and one write-only.
- Bytes come out in the order they went in. There are no message
  boundaries (except in `O_DIRECT` mode): two writes of 10 bytes may come
  out as one read of 20, or reads of 3 and 17.

A pipe inside a single process is useless except as a trick (the
"self-pipe trick", section 3.12). Pipes become useful with `fork()`: the
child inherits both ends, each side closes the end it does not use, and you
have a channel between parent and child.

```text
            before fork                     after fork + close
        +---------------+          +---------+          +---------+
        |    parent     |          | parent  |  pipe    |  child  |
        | fds[0] fds[1] |          | fds[1] ---------->  fds[0]  |
        +---------------+          | (write) |          | (read)  |
                                   +---------+          +---------+
```

### 3.2 Blocking rules

The rules come from POSIX and are worth memorizing:

**Reading** from a pipe:

1. If the pipe holds data, `read` returns up to the requested number of
   bytes immediately.
2. If the pipe is empty and at least one write end is open somewhere,
   `read` blocks (or fails with `EAGAIN` if `O_NONBLOCK`).
3. If the pipe is empty and *no* write end is open anywhere, `read`
   returns 0: end of file.

**Writing** to a pipe:

1. If no read end is open anywhere, the writer gets `SIGPIPE`. If it
   ignores or catches the signal, `write` fails with `EPIPE`.
2. If there is room, the data is copied in and `write` returns.
3. If there is not enough room, `write` blocks until all the data has been
   written (blocking mode), possibly in several chunks interleaved with
   other writers if the size is above `PIPE_BUF`.
4. In non-blocking mode, a write of up to `PIPE_BUF` bytes either writes
   everything or fails with `EAGAIN`; a larger write may write partially
   and return the number of bytes written.

### 3.3 PIPE_BUF and atomicity

POSIX guarantees that writes of at most `PIPE_BUF` bytes are *atomic*: they
are not interleaved with writes from other processes. `PIPE_BUF` is at
least 512 bytes by POSIX; on Linux it is 4096. Writes larger than that may
be split, and pieces from different writers may interleave.

This is why many processes can safely write log lines into the same pipe
(for example, all children of `make -j` writing to one terminal through
a pipe, or many workers appending to a FIFO), *as long as each line is
written in one `write` call of at most 4096 bytes*. Note that stdio can
break a line into several writes if the buffer fills in the middle, so for
this guarantee you want to format the line yourself and call `write` once.

### 3.4 SIGPIPE: the quiet killer

Consider:

```text
$ yes | head -n 3
y
y
y
```

`yes` writes `y\n` forever. `head` reads three lines, prints them and
exits, closing the read end. The next `write` by `yes` finds no reader, so
the kernel sends `SIGPIPE`, whose default action terminates `yes`. That is
exactly what you want: the pipeline ends cleanly and quietly.

Now some consequences that bite:

- In bash with `set -o pipefail`, the pipeline's status is 141 (128 + 13,
  SIGPIPE is signal 13), so a script that does `cmd | head` may
  "fail" randomly, depending on whether `cmd` finished before `head`
  closed.
- If a program *ignores* `SIGPIPE` (Python does at startup, turning it into
  a `BrokenPipeError` exception; Go and Rust have their own rules, see
  below), then `write` returns `EPIPE` and the program must handle it. If
  it prints an error message for it, you get noise like
  `BrokenPipeError: [Errno 32] Broken pipe`.
- If a process ignores `SIGPIPE`, that disposition is inherited across
  `exec`. A parent that ignores `SIGPIPE` and spawns `yes` will create a
  `yes` that does not die, and instead loops on `EPIPE` errors (GNU `yes`
  handles this, but not every program does). Always reset `SIGPIPE` to
  `SIG_DFL` in the child before `exec` if you ignored it in the parent.

What each language does by default:

- **C**: default disposition: the process dies.
- **Rust**: the runtime sets `SIGPIPE` to *ignored* before `main`, so
  writes fail with `ErrorKind::BrokenPipe`, and `println!` panics with
  "failed printing to stdout: Broken pipe". The standard `Command` resets
  it to default in children. There is a nightly-only attribute to change
  this (`-Zon-broken-pipe`); in stable you can reset it yourself with
  `libc::signal(SIGPIPE, SIG_DFL)` at the start of `main`.
- **Go**: if a write to fd 1 or 2 fails with `EPIPE`, the runtime makes the
  program die of `SIGPIPE` (matching C behavior for pipelines). For other
  fds, the write returns an `EPIPE` error. Children are spawned with
  default dispositions.
- **Raku**: MoarVM ignores `SIGPIPE` (it relies on libuv); a write to a
  closed pipe raises an exception such as "Failed to write bytes to
  filehandle: Broken pipe". Chapter 15 shows how to deal with it.

### 3.5 What a shell does for `a | b`

Here is the skeleton of what a shell does to run `ls -l | wc -l`. You will
implement it in C in chapter 10, and in every language after.

```text
pipe(p)                         -> p[0] read end, p[1] write end
pid1 = fork()
  child 1:
    dup2(p[1], 1)               stdout -> pipe write end
    close(p[0]); close(p[1])
    execvp("ls", ["ls","-l"])
pid2 = fork()
  child 2:
    dup2(p[0], 0)               stdin <- pipe read end
    close(p[0]); close(p[1])
    execvp("wc", ["wc","-l"])
parent:
    close(p[0]); close(p[1])    !!! essential
    waitpid(pid1); waitpid(pid2)
```

Notes:

- Every process closes the pipe ends it does not use. After `dup2`, the
  original `p[0]`/`p[1]` fds are redundant copies and must be closed too.
- The parent must close *both* ends. If it keeps `p[1]` open, `wc` will
  never see end-of-file and will hang forever, because a writer still
  exists (the parent itself).
- All the processes in the pipeline run concurrently. `ls` does not finish
  before `wc` starts. If the pipe buffer fills, `ls` blocks until `wc`
  catches up. This back-pressure is free flow control.
- In an interactive shell with job control, both children are put into
  the same *process group*, which becomes the foreground process group of
  the terminal (chapter 5). That is how `^C` kills the whole pipeline.

For a pipeline of n commands, you need n-1 pipes. Each middle process
reads from pipe i-1 and writes to pipe i.

### 3.6 The classic deadlocks

**Deadlock 1: the forgotten write end.** A process waits for EOF on a pipe
while it, or one of its children, still holds the write end open. Typical
case: you create a pipe, fork a child that writes to it, and in the parent
you read until EOF without closing `p[1]` first. Your own copy keeps the
pipe alive. Or: you spawn *two* children, and the second one inherits the
write end of the first child's pipe because it was not marked
close-on-exec. The reader then waits for the second child to exit.

**Deadlock 2: both pipes full.** A parent starts a child with *both* stdin
and stdout connected to pipes (bidirectional communication, like
`popen` in both directions). The parent writes a large input, and the child
writes output as it reads. Once the child's output pipe is full (64 KiB),
the child blocks on `write`. It stops reading its stdin, so the parent's
pipe fills up, and the parent blocks on `write`. Both wait for each other
forever.

```text
   parent --- write (blocked: pipe A full) ---> child
   parent <--- nobody reading pipe B (full) --- child (blocked on write)
```

Fixes: write and read concurrently (two threads, or `poll`), or write the
input to a temporary file first. Every high-level API that offers "run a
command with input and capture its output" handles this internally:
Python's `communicate()`, Rust's `Command::output()` with
`Stdio::piped()` stdin written from another thread, Go's
`cmd.CombinedOutput` with `cmd.Stdin` set (it uses goroutines), Raku's
`Proc::Async`.

**Deadlock 3: stderr filling up.** You capture a child's stdout and stderr
through two pipes, but read only stdout until EOF, then stderr. If the
child writes more than 64 KiB to stderr, it blocks, never closes stdout,
and you wait forever. Same fix: read both concurrently.

**Deadlock 4: buffering.** Not a real deadlock but it looks like one: you
write a request to a child's stdin and wait for its reply, but the child
uses stdio, sees a pipe on stdout, and buffers the reply. Or you buffered
your own request and never flushed. For interactive back-and-forth with
an existing program you cannot modify, a PTY often works better than pipes
(chapter 6 and the `expect` project in chapter 30).

### 3.7 Pipe capacity in practice

You can measure the pipe capacity yourself: create a pipe, make the write
end non-blocking, and write one byte at a time until `EAGAIN`.

```c
// file: c/pipe_capacity.c
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <unistd.h>

int main(void)
{
    int p[2];
    if (pipe2(p, O_NONBLOCK) == -1) { perror("pipe2"); return 1; }

    long n = 0;
    char c = 'x';
    for (;;) {
        ssize_t w = write(p[1], &c, 1);
        if (w == 1) { n++; continue; }
        if (w == -1 && errno == EAGAIN) break;
        perror("write");
        return 1;
    }
    printf("default capacity: %ld bytes\n", n);
    printf("F_GETPIPE_SZ:     %d bytes\n", fcntl(p[1], F_GETPIPE_SZ));

    int got = fcntl(p[1], F_SETPIPE_SZ, 1 << 20);
    printf("after F_SETPIPE_SZ(1 MiB): %d\n", got);
    return 0;
}
```

On a typical x86-64 Linux:

```text
$ cc -Wall -o pipe_capacity c/pipe_capacity.c && ./pipe_capacity
default capacity: 65536 bytes
F_GETPIPE_SZ:     65536 bytes
after F_SETPIPE_SZ(1 MiB): 1048576
```

One subtlety: Linux accounts pipe capacity in pages (slots), not in bytes.
Each `write` of 1 byte may use a whole page slot if it cannot be merged
into the previous one. In practice small writes are merged, which is why
you see exactly 65536 here, but if you mix very different write sizes you
may see less.

There is also a per-user limit on the total memory used by pipe buffers
(`/proc/sys/fs/pipe-user-pages-soft` and `-hard`). If a user has too many
pipes, new pipes get a reduced capacity of one or two pages. Programs that
create thousands of pipes can hit this.

### 3.8 Named pipes (FIFOs)

A FIFO is a pipe with a name in the filesystem. You create it with
`mkfifo path` (or `mkfifo(3)`/`mknod(2)`), and processes open it with
ordinary `open()`.

```text
$ mkfifo /tmp/fifo
$ ls -l /tmp/fifo
prw-r--r-- 1 cog cog 0 Nov 22 10:00 /tmp/fifo
$ cat /tmp/fifo &          # blocks in open() until a writer appears
$ echo hello > /tmp/fifo   # opens, writes, closes
hello
```

Key rules:

- Opening a FIFO for reading blocks until someone opens it for writing, and
  vice versa. This rendezvous is often surprising: a program that opens a
  FIFO "to check it" hangs.
- `open(path, O_RDONLY | O_NONBLOCK)` succeeds immediately even without a
  writer. `open(path, O_WRONLY | O_NONBLOCK)` fails with `ENXIO` if there
  is no reader.
- On Linux, opening a FIFO with `O_RDWR` succeeds immediately and gives
  you both ends (POSIX leaves this undefined). It is a common trick for
  a server that wants its FIFO to never reach EOF when the last client
  disconnects: it keeps a write end open itself.
- The data never touches the disk. The inode is only a meeting point.
- When the last writer closes, readers get EOF. A server that wants to
  serve several clients one after the other must reopen the FIFO, or use
  the `O_RDWR` trick.

Uses: simple IPC between unrelated processes, feeding commands into a
long-running program, process substitution in shells that do not have
`/dev/fd` (bash's `<(cmd)` uses `/dev/fd/N` on Linux, and a FIFO
elsewhere).

### 3.9 Process substitution and /dev/fd

Bash, zsh and ksh support `<(cmd)` and `>(cmd)`. The shell creates a
pipe, starts `cmd` with one end, and replaces the `<(cmd)` text with a path
to the other end, like `/dev/fd/63`. The program receives a *file name*
that it can open:

```text
$ diff <(sort a.txt) <(sort b.txt)
$ echo <(true)
/dev/fd/63
```

On Linux, `/dev/fd` is a symlink to `/proc/self/fd`, and opening
`/proc/self/fd/63` gives you a *new* open file description of the same
pipe. (For a regular file, it would reopen the file with a fresh offset; this
is different from `dup`.)

Programs that need to *seek* in their input break with process
substitution, since you cannot seek a pipe. Those that `stat` their input to
learn its size get 0.

### 3.10 Pipes versus other channels

When should you use a pipe, and when something else?

| Channel | Direction | Unrelated procs | Boundaries |
|---------|-----------|-----------------|------------|
| pipe | one way | no (inherit) | no |
| FIFO | one way | yes (by path) | no |
| socketpair | two way | no (inherit) | optional |
| Unix socket | two way | yes (by path) | optional |
| PTY | two way | no (usually) | no, plus tty |
| shared memory | both | yes | none |

`socketpair(AF_UNIX, SOCK_STREAM, 0, sv)` gives you a bidirectional pipe.
Some programs (OpenSSH for its subprocesses, some language runtimes) use
it instead of two pipes. A child process cannot easily tell the
difference, except that `fstat` says "socket", and that `shutdown(fd,
SHUT_WR)` can signal EOF in one direction while leaving the other open.
With `SOCK_SEQPACKET` you also get message boundaries. And Unix sockets
can pass file descriptors between processes (`SCM_RIGHTS`), which pipes
cannot.

### 3.11 splice, tee and vmsplice

Linux has zero-copy calls specific to pipes:

- `splice(fd_in, off_in, fd_out, off_out, len, flags)` moves data between
  a pipe and another fd without copying it to user space. One of the two
  fds must be a pipe.
- `tee(fd_in, fd_out, len, flags)` duplicates data from one pipe into
  another pipe, without consuming it from the first.
- `vmsplice` maps user memory into a pipe.

`cat` from GNU coreutils uses `copy_file_range` or `splice` in some cases.
For our purposes, know that they exist and that they explain why
`strace cat` sometimes shows no `read`/`write` calls at all.

### 3.12 The self-pipe trick

A classic problem: you are blocked in `poll()` waiting on a set of fds, and
a signal arrives (`SIGCHLD` because a child exited, or `SIGWINCH`). You
want the event loop to notice. Doing real work in a signal handler is
dangerous (only async-signal-safe functions are allowed), and if the
signal arrives just *before* you call `poll`, it may be missed.

The self-pipe trick: create a non-blocking pipe, add its read end to the
poll set, and in the signal handler, `write()` one byte to it. `write` is
async-signal-safe. The main loop wakes up because the pipe became readable,
drains it, and handles the event in normal context.

```c
static int sigpipe_w;               /* write end, non-blocking */

static void on_signal(int sig)
{
    int saved = errno;
    unsigned char b = (unsigned char)sig;
    (void)write(sigpipe_w, &b, 1);  /* ignore EAGAIN: already pending */
    errno = saved;
}
```

Linux offers `signalfd()` as a cleaner alternative, and `ppoll`/`pselect`
let you atomically unblock signals while waiting. Async runtimes (libuv,
tokio, Go) all use one of these techniques internally. You will see the
self-pipe trick in the C chapters, because it is portable and it shows
what the runtimes hide from you.

### 3.13 Pipes and the shell: a few experiments

Before writing code, it is worth seeing the kernel's behavior with nothing
but a shell. Each of these is worth five minutes:

**Back-pressure.** The writer is slowed down by the reader:

```text
$ yes | pv -L 1k > /dev/null
```

`pv` reads at 1 KiB/s, so `yes`, which could write gigabytes per second,
spends almost all its time blocked in `write`. Check with
`strace -p $(pgrep -n yes)`: you see one `write` returning every few
seconds.

**EOF requires every writer to close.**

```text
$ { sleep 5 & echo done; } | cat
done
```

`cat` prints `done` immediately but exits only after 5 seconds, because the
background `sleep` inherited the pipe's write end as its stdout and keeps
it open even though it never writes to it. This is deadlock 1 in miniature;
in a daemon or a CI script it can hang forever. The fix is to redirect the
background job's output: `sleep 5 > /dev/null &`.

**SIGPIPE status.**

```text
$ yes | head -1; echo "${PIPESTATUS[@]}"
y
141 0
```

(Bash-specific `PIPESTATUS`; zsh uses `$pipestatus`.) 141 = 128 + 13.

**Pipe capacity from the shell.**

```text
$ ( dd if=/dev/zero bs=1 count=100000 2>/dev/null; echo wrote all >&2 ) | sleep 10
```

Nothing is printed for 10 seconds: `dd` blocks once 65536 bytes are in the
pipe. When `sleep` exits, `dd` gets `SIGPIPE` and dies, so `wrote all`
never appears.

**Which processes share a pipe.** In one terminal run `sleep 100 | sleep
100`, and in another:

```text
$ for p in $(pgrep -x sleep); do ls -l /proc/$p/fd | grep pipe; done
l-wx------ 1 cog cog 64 ... 1 -> pipe:[901234]
lr-x------ 1 cog cog 64 ... 0 -> pipe:[901234]
```

Same inode number on both sides: same pipe.

### 3.14 Pipes and terminals together

A pipeline usually has a terminal at both ends: the first command's stdin
and the last command's stdout are the terminal. Inside the pipeline, the
data is not processed by the terminal layer at all. Only the ends are.
Some consequences:

- `^C` typed at the terminal is turned into `SIGINT` by the terminal's line
  discipline, and delivered to the foreground *process group*. Every process
  in the pipeline gets it, not just the one reading the terminal.
- Programs in the middle of a pipeline that want to talk to the user (a
  password prompt in `ssh`, `sudo`, `gpg`, the pager in `git log | less`)
  open `/dev/tty` directly. `/dev/tty` always means "the controlling
  terminal of this process", whatever fds 0 to 2 are. `less` reads its
  *data* from stdin (the pipe) and its *keyboard commands* from `/dev/tty`.
- Terminal processing such as `\n` to `\r\n` translation is applied only by
  the final write to the terminal, not by the pipes.

You can see the `/dev/tty` trick from the shell:

```text
$ echo data | { read -r line; read -r answer < /dev/tty; echo "$line/$answer"; }
yes                                     <- typed at the keyboard
data/yes
```

### 3.15 Summary of pipe rules

- A pipe has a kernel buffer (64 KiB on Linux by default) and no message
  boundaries.
- Read returns available data, blocks on empty, and returns 0 when every
  write end is closed.
- Write blocks on full and raises `SIGPIPE`/`EPIPE` when every read end is
  closed.
- Writes of up to `PIPE_BUF` (4096 on Linux) bytes are atomic.
- Close every end you do not use, in every process, or EOF never comes.
- Never write a large input and read a large output sequentially to the
  same child: do both at once.
- stdio buffers fully when stdout is a pipe; flush, or use a PTY.

---

## 4. The TTY layer: line discipline and termios

### 4.1 The pieces

A terminal device, whether it is a serial port, a virtual console or a PTY
slave, is made of layers in the kernel:

```text
          user space:      shell, vim, cat, ...
                              |  read() / write() / ioctl()
   ------------------------------------------------------------
          tty core          (drivers/tty/tty_io.c)
                              |
          line discipline   (N_TTY: drivers/tty/n_tty.c)
                              |   editing, echo, signals, CR/NL
          tty driver        (serial 8250, vt console, pty)
   ------------------------------------------------------------
          hardware / other end: UART, keyboard+screen, PTY master
```

- The **tty core** implements the file operations and ioctls common to all
  terminals.
- The **line discipline** sits between the driver and the process. The
  default one, `N_TTY`, implements everything we think of as "terminal
  behavior": the line editing buffer (canonical mode), echo, translation
  of CR and NL, generation of signals from special characters, and flow
  control. Other line disciplines exist for serial protocols (PPP, SLIP,
  Bluetooth HCI, GSM multiplexing) and turn the tty into something
  else entirely; they are irrelevant for interactive use.
- The **driver** moves bytes to and from the "outside world". For a PTY,
  the outside world is the master side.

Input flows *up* from the driver through the line discipline to the reading
process. Output flows *down* from the writing process through the line
discipline (output processing: `OPOST`, `ONLCR`) to the driver.

Echo is the interesting cross-link: when the line discipline receives an
input character with `ECHO` enabled, it writes it back *down* to the
driver's output side, so it appears on the screen. That is why, when your
program is busy, characters you type still appear immediately: the kernel
echoes them, not your program.

### 4.2 Canonical mode ("cooked")

In canonical mode (`ICANON` set), the line discipline collects input into a
line buffer and makes it available to `read()` only when a line is
complete. A line ends with:

- NL (`\n`, which is what Enter produces after the `ICRNL` translation),
- EOL (an optional extra end-of-line character, unset by default),
- EOL2 (Linux extension, also unset),
- EOF (`^D` by default): the line is made available *without* the EOF
  character itself.

While the line is being built, the special characters edit it:

| Name | Default | Effect |
|------|---------|--------|
| ERASE | `^?` (DEL) | delete previous char |
| WERASE | `^W` | delete previous word |
| KILL | `^U` | delete whole line |
| REPRINT | `^R` | redraw the line |
| LNEXT | `^V` | take next char literally |
| EOF | `^D` | send line / EOF |

`WERASE`, `REPRINT` and `LNEXT` are only active if `IEXTEN` is set
(it is by default).

The EOF character deserves a careful explanation because it confuses
everyone. `^D` does not "send an end-of-file character". It means "make
the current line available to `read()` *now*, without adding anything". If
the line is non-empty, `read()` returns the characters typed so far, with
no newline. If the line is empty, `read()` returns 0, which the program
interprets as end-of-file. That is why you sometimes need to press `^D`
twice: the first one flushes the partial line `abc` to the program, and
the second one, on an empty line, produces the 0-byte read.

Try it with `cat`:

```text
$ cat
abc^D            <- cat receives "abc", prints it: line shows abcabc
^D               <- cat receives 0 bytes, exits
```

Another consequence of canonical mode: `read(fd, buf, 1)` returns *one*
byte, but only after the user has pressed Enter. The rest of the line stays
in the kernel's buffer for the next `read`. And a single `read` never
returns more than one line, even if more lines are available.

The line buffer has a maximum size: 4096 bytes on Linux (`N_TTY_BUF_SIZE`).
If you paste a line longer than that into a program reading in canonical
mode, the extra characters are dropped (the terminal may beep). That is a
real limitation when pasting long lines into `cat > file` or into a
`read` in a shell script; in practice a shell with its own line editor
uses raw mode and does not have this limit.

### 4.3 Non-canonical mode ("raw" and "cbreak")

With `ICANON` cleared, there is no line buffer. Bytes are available to
`read()` as they arrive, according to two parameters in the `c_cc` array:

- `VMIN`: minimum number of bytes for `read()` to return.
- `VTIME`: timeout in tenths of a second.

Their combination defines four behaviors:

| VMIN | VTIME | `read()` returns |
|------|-------|------------------|
| 0 | 0 | at once, maybe 0 bytes |
| >0 | 0 | after VMIN bytes |
| 0 | >0 | 1+ bytes, or 0 on timeout |
| >0 | >0 | inter-byte timer |

In the last case, the timer starts after the *first* byte arrives and is
reset by each byte; `read` returns when VMIN bytes have arrived or the
timer expires between two bytes. That was designed for reading bursts from
serial devices, and was used to tell a lone ESC key press apart from the
start of an escape sequence (the first byte arrives, and if no further
bytes come within VTIME tenths of a second, it was a lone ESC).

The usual TUI setting is `VMIN=1, VTIME=0` (block until at least one
byte), combined with `poll()` for timeouts. Some programs use `VMIN=0,
VTIME=1` to poll the keyboard every 100 ms.

Note that `VMIN` and `VTIME` share array slots with `VEOF` and `VEOL` on
some systems (historically, and on Linux for some architectures). Always
set them explicitly when you switch to non-canonical mode, never assume
the values left over from canonical mode.

Historically there were two non-canonical flavors:

- **cbreak** mode: `ICANON` and `ECHO` off, but signals (`ISIG`) and output
  processing kept. `^C` still kills the program. Good for "press any
  key" prompts and simple games.
- **raw** mode: everything off. `^C` arrives as byte `0x03`, `\n` is not
  translated on output, no flow control, 8-bit clean. Good for editors,
  terminal multiplexers, `ssh` client side, and binary protocols.

`cfmakeraw()` (BSD and glibc, not POSIX) sets raw mode as defined by
the old V7 `stty raw`.

### 4.4 struct termios

All of this is configured through one structure:

```c
struct termios {
    tcflag_t c_iflag;   /* input modes */
    tcflag_t c_oflag;   /* output modes */
    tcflag_t c_cflag;   /* control modes */
    tcflag_t c_lflag;   /* local modes */
    cc_t     c_cc[NCCS];/* special characters */
    /* plus implementation-specific fields, e.g. speeds on Linux */
};
```

You read it with `tcgetattr(fd, &t)` and write it with `tcsetattr(fd,
when, &t)`, where `when` is:

- `TCSANOW`: apply immediately.
- `TCSADRAIN`: wait until all queued output has been transmitted, then
  apply. Use this when changing output settings.
- `TCSAFLUSH`: like `TCSADRAIN`, and also discard any input not yet read.
  Commonly used when entering raw mode, so that keys typed before the
  switch are not misinterpreted.

`tcsetattr` returns success if *any* of the requested changes was applied,
so a careful program reads the settings back to check. In practice, on a
PTY, everything is applied.

The most important flags (Appendix A has all of them):

**c_lflag** (local modes, the line discipline proper):

- `ICANON`: canonical mode (line editing).
- `ECHO`: echo input characters.
- `ECHOE`: ERASE visually erases (backspace-space-backspace).
- `ECHOK`, `ECHOKE`: KILL erases the line visually.
- `ECHONL`: echo NL even if `ECHO` is off.
- `ECHOCTL`: echo control characters as `^X` (Linux/BSD). That is why
  pressing `^C` shows `^C` on your screen.
- `ISIG`: generate signals for INTR, QUIT, SUSP characters.
- `IEXTEN`: enable implementation-defined extensions (`^V`, `^W`, `^R`,
  `^O` on some systems).
- `NOFLSH`: do not flush queues on INTR/QUIT/SUSP.
- `TOSTOP`: send `SIGTTOU` to background processes that write.

**c_iflag** (input processing):

- `ICRNL`: translate CR to NL on input. This is why pressing Enter (which
  sends CR, `\r`, from the terminal) gives your program `\n`.
- `INLCR`: translate NL to CR. `IGNCR`: ignore CR.
- `IXON`: enable XON/XOFF output flow control (`^S` stops output, `^Q`
  resumes). This is why `^S` "freezes" a terminal. Most people want it
  off; `stty -ixon` in your shell rc disables it.
- `IXOFF`: send XON/XOFF to the device when the input queue fills.
- `IXANY`: any character restarts output.
- `ISTRIP`: strip the 8th bit (from the 7-bit days; kills UTF-8).
- `INPCK`, `PARMRK`, `IGNPAR`: parity checking (serial only).
- `BRKINT`, `IGNBRK`: what to do on a serial BREAK.
- `IUTF8` (Linux): the line discipline knows characters are UTF-8, so
  ERASE removes a whole multibyte character instead of a single byte.
- `IMAXBEL`: ring the bell when the input buffer is full.

**c_oflag** (output processing):

- `OPOST`: enable output processing at all. Clearing it disables every
  other output flag.
- `ONLCR`: map NL to CR-NL on output. This is the one that matters. In raw
  mode with `OPOST` off, `printf("hello\n")` moves down one line *without
  returning to column 0*, giving the "staircase" effect. TUI programs
  either keep `OPOST` on, or write `\r\n` explicitly.
- `OCRNL`, `ONOCR`, `ONLRET`: other CR/NL variations.
- `TABDLY`/`XTABS`: expand tabs to spaces.

**c_cflag** (control modes, mostly hardware):

- `CSIZE` (`CS5`..`CS8`): character size; you want `CS8`.
- `CSTOPB`, `PARENB`, `PARODD`: stop bits and parity.
- `CREAD`: enable receiver.
- `HUPCL`: hang up (drop DTR) on last close.
- `CLOCAL`: ignore modem control lines.
- `CRTSCTS` (Linux/BSD): hardware flow control.

**c_cc** (special characters), indexed by:

`VINTR` (`^C`), `VQUIT` (`^\`), `VERASE` (`^?`), `VKILL` (`^U`), `VEOF`
(`^D`), `VEOL`, `VEOL2`, `VSTART` (`^Q`), `VSTOP` (`^S`), `VSUSP` (`^Z`),
`VWERASE` (`^W`), `VREPRINT` (`^R`), `VLNEXT` (`^V`), `VDISCARD` (`^O`),
`VMIN`, `VTIME`. Setting an entry to `_POSIX_VDISABLE` (0 on Linux)
disables that function.

### 4.5 stty: termios from the shell

`stty` reads and changes the termios settings of its *standard input*. It
is the best way to explore the flags. Run `stty -a`:

```text
$ stty -a
speed 38400 baud; rows 48; columns 160; line = 0;
intr = ^C; quit = ^\; erase = ^?; kill = ^U; eof = ^D; eol = <undef>;
eol2 = <undef>; swtch = <undef>; start = ^Q; stop = ^S; susp = ^Z;
rprnt = ^R; werase = ^W; lnext = ^V; discard = ^O; min = 1; time = 0;
-parenb -parodd -cmspar cs8 -hupcl -cstopb cread -clocal -crtscts
-ignbrk -brkint -ignpar -parmrk -inpck -istrip -inlcr -igncr icrnl ixon
-ixoff -iuclc -ixany -imaxbel iutf8
opost -olcuc -ocrnl onlcr -onocr -onlret -ofill -ofdel nl0 cr0 tab0 bs0
vt0 ff0
isig icanon iexten echo echoe echok -echonl -noflsh -xcase -tostop
-echoprt echoctl echoke -flusho -extproc
```

A leading `-` means the flag is off. Things to notice:

- "speed 38400 baud" on a PTY is meaningless.
- "rows 48; columns 160" are not termios at all; they come from the
  window size (`TIOCGWINSZ`, chapter 8), which `stty` shows for
  convenience.
- `line = 0` is the line discipline number (`N_TTY`).

Useful experiments (do them in a terminal you can close if things go
wrong):

```text
$ stty -echo; read -r secret; stty echo; echo "got: $secret"
$ stty raw -echo; dd bs=1 count=5 2>/dev/null | od -c; stty sane
$ stty -icanon min 1 time 0; dd bs=1 count=3 2>/dev/null; stty icanon
$ stty intr ^X              # now ^X interrupts, ^C is a normal char
$ stty sane                 # reset to reasonable defaults
$ stty -g                   # save settings in a compact form
$ saved=$(stty -g); stty raw; ...; stty "$saved"
```

The second line is the most instructive: in raw mode, press keys like
arrow keys, Enter, `^C` and see the raw bytes. You will see that Up is
`033 [ A` (ESC, `[`, `A`) and Enter is `\r` (no `ICRNL` in raw mode).

If you ever leave a terminal in a broken state (no echo, staircase output),
type `stty sane` followed by `^J` (Ctrl+J, a literal NL, since Enter may be
sending a CR that is no longer translated), or the `reset` command.

### 4.6 Special characters and signals

When `ISIG` is on, the line discipline watches for three characters:

- `VINTR` (`^C`): send `SIGINT` to the foreground process group.
- `VQUIT` (`^\`): send `SIGQUIT`.
- `VSUSP` (`^Z`): send `SIGTSTP`.

The signal goes to the whole *foreground process group* of the terminal,
not to "the program reading the terminal". Chapter 5 explains process
groups. Unless `NOFLSH` is set, the input and output queues are flushed
too, which is why output stops abruptly when you press `^C`.

The character itself is not passed to the reader. With `ISIG` off (raw
mode), the reader gets the byte (`0x03` for `^C`) and can decide what to
do. Editors use this to bind `^C`, `^Z` and `^\` to their own commands. If a
raw-mode program wants to keep "`^C` exits", it must do it itself, which
is why you can get stuck in a raw-mode program with a bug.

There is no "ISIG" for `^D`: EOF is not a signal, it is just how canonical
mode handles a line. In raw mode `^D` is the byte `0x04`.

### 4.7 Control characters and the keyboard

A terminal sends bytes, not key events. The mapping is old and lossy:

- Printable keys send their character (UTF-8 encoded on a modern
  terminal).
- Ctrl+letter sends the letter's code with bits 5 and 6 cleared: Ctrl+A is
  `0x01`, Ctrl+C is `0x03`, Ctrl+[ is `0x1b` (ESC). That is why Ctrl+[
  works as Escape in vim, Ctrl+I is Tab (`0x09`), Ctrl+M is CR (`0x0d`)
  and Ctrl+H is Backspace (`0x08`) in some setups.
- Backspace sends `0x7f` (DEL, `^?`) on most modern terminals, `0x08`
  (`^H`) on some. The `erase` setting must match, or Backspace prints
  `^?`. This used to be an endless source of trouble; today it is mostly
  settled on `^?`.
- Enter sends `\r` (`0x0d`), which `ICRNL` turns into `\n`.
- Alt+key sends ESC followed by the key (the "meta sends escape"
  convention), so Alt+b is `\e b`.
- Function keys, arrows, Home, End and so on send escape sequences:
  `\e[A` for Up, `\e[1;5A` for Ctrl+Up, `\eOP` for F1, `\e[3~` for Delete.
  They differ between terminals and modes (see chapter 7).

So there is no way, in the classic encoding, to distinguish Ctrl+I from
Tab, Ctrl+M from Enter, Ctrl+Shift+A from Ctrl+A, or to receive a key
*release*. Modern terminals offer opt-in protocols to fix this, such as the
*kitty keyboard protocol* and xterm's `modifyOtherKeys` (chapter 7).

### 4.8 Who reads the terminal: canonical mode and readline

If canonical mode gives line editing for free, why do shells, the Python
REPL and `psql` use their own line editors (GNU Readline, libedit, zsh's
ZLE, Rust's rustyline/reedline, Raku's Terminal::LineEditor or Readline)?
Because the kernel's editing is minimal: no cursor movement inside the
line, no history, no completion, no multi-line editing, no UTF-8 aware
cursor positioning beyond `IUTF8`. A line editor puts the terminal in
non-canonical mode (and turns off `ECHO`), reads bytes one by one,
maintains its own buffer, and redraws the line itself with escape
sequences. When the line is accepted, it restores the terminal settings
and returns the line to the program.

This is why a program run *by* your shell sees the terminal in canonical
mode: the shell restores the settings before running each command. If a
program crashes while the terminal is in raw mode, the shell may or may
not repair it. Bash does not save and restore the terminal settings around
commands by default; zsh has `ttyctl -f` to freeze them. Hence `reset`.

### 4.9 What every raw-mode program must do

From all of the above, a checklist that every chapter's raw-mode example
follows:

1. Check that the fd is a terminal (`isatty`). If not, either fail or fall
   back to a line-oriented mode.
2. Save the original termios with `tcgetattr`.
3. Install handlers so that the settings are restored on every exit path:
   normal return, `exit()`, fatal signals (`SIGINT` if `ISIG` is kept,
   `SIGTERM`, `SIGHUP`, `SIGQUIT`), and panics or exceptions in higher-level
   languages.
4. Handle `SIGTSTP` (`^Z`) properly if signals are enabled: restore the
   terminal, stop yourself, and re-enter raw mode on `SIGCONT`.
5. Modify a *copy* of the termios and apply it with `TCSAFLUSH`.
6. Handle `SIGWINCH` if you draw full-screen.
7. On exit: show the cursor again, leave the alternate screen, disable mouse
   and other modes you turned on (chapter 7), and restore termios with
   `TCSAFLUSH` or `TCSADRAIN`.

Steps 3 and 4 are where most hand-written TUIs fall short. Libraries
(ncurses, crossterm, Bubble Tea, Terminal::UI) do most of it, and each
language chapter shows the manual way first so that you know what the
library is doing.

---

## 5. Sessions, process groups and job control

### 5.1 Why process groups exist

You type `sort big.txt | uniq -c | sort -rn | head` and press `^C`. Four
processes must die, not just the one reading the terminal (there is none:
`sort` reads a file). And while that pipeline runs in the background
(`&`), `^C` must *not* kill it. The kernel needs a notion of "the set of
processes that make up the job in the foreground". That notion is the
*process group*.

The hierarchy:

```text
 session (SID = PID of session leader, usually the shell or login process)
 |  controlling terminal: /dev/pts/3
 |  foreground process group: PGID 4012
 |
 +-- process group 3990 (the shell itself)
 |     3990 zsh
 +-- process group 4012 (foreground job)     <-- gets ^C, ^Z, ^\
 |     4012 sort
 |     4013 uniq
 |     4014 sort
 |     4015 head
 +-- process group 4020 (background job: make &)
       4020 make
       4031 cc1
```

Definitions:

- A **process group** is a set of processes identified by a process group
  ID (PGID), which is the PID of the group's first member, the *group
  leader*. Signals can be sent to a whole group with `kill(-pgid, sig)` or
  `killpg(pgid, sig)`.
- A **session** is a set of process groups, identified by a session ID
  (SID), the PID of the *session leader*. Typically, one login (one
  terminal window, one ssh connection) is one session.
- A session can have one **controlling terminal**, and a terminal can be
  the controlling terminal of at most one session.
- Among the process groups of a session with a controlling terminal, one is
  the **foreground process group**. The others are background groups.

Inspect them with `ps`:

```text
$ sleep 100 | cat &
$ ps -o pid,ppid,pgid,sid,tpgid,tty,stat,comm
    PID    PPID    PGID     SID   TPGID TT       STAT COMMAND
   3990    3985    3990    3990    4101 pts/3    Ss   zsh
   4050    3990    4050    3990    4101 pts/3    S    sleep
   4051    3990    4050    3990    4101 pts/3    S    cat
   4101    3990    4101    3990    4101 pts/3    R+   ps
```

- `PGID`: `sleep` and `cat` share group 4050; `ps` has its own group 4101.
- `SID`: everybody is in the shell's session, 3990.
- `TPGID`: the terminal's foreground process group. It is 4101: `ps` is in
  the foreground while it runs. The `+` in `STAT` marks foreground
  processes; `s` marks a session leader.

### 5.2 The system calls

- `setsid()`: create a new session and a new process group, with the
  caller as leader of both, and *no* controlling terminal. Fails if the
  caller is already a process group leader (that is why daemons fork
  first: the child is never a group leader).
- `setpgid(pid, pgid)`: put process `pid` into group `pgid` (creating it if
  `pgid == pid`). Only allowed within the same session, and only for
  yourself or a child that has not yet called `exec`.
- `getpgrp()`, `getpgid(pid)`, `getsid(pid)`: queries.
- `tcgetpgrp(fd)`: the foreground process group of the terminal `fd`.
- `tcsetpgrp(fd, pgid)`: make `pgid` the foreground group. Only allowed
  for a process whose controlling terminal is `fd`; if the caller is in a
  background group, it receives `SIGTTOU` unless it blocks or ignores it.
- `tcgetsid(fd)`: the session of the terminal.
- `ioctl(fd, TIOCSCTTY, 0)`: make the terminal the controlling terminal of
  the calling session leader (Linux/BSD).
- `ioctl(fd, TIOCNOTTY)`: give up the controlling terminal.

### 5.3 How a process acquires a controlling terminal

On Linux (System V behavior), when a session leader *without* a controlling
terminal opens a terminal device that is not already the controlling
terminal of another session, and `O_NOCTTY` is not given, that terminal
becomes its controlling terminal. On the BSDs and macOS, opening is not
enough: the leader must call `ioctl(fd, TIOCSCTTY, 0)`. Portable code does
both: `setsid()`, open the slave, then `ioctl(TIOCSCTTY)` (harmless on Linux
if the open already did it).

That gives the standard recipe for starting a program on a new PTY, used
by every terminal emulator and by `login_tty(3)`:

```c
/* in the child, after fork() */
setsid();                          /* new session, no ctty */
int s = open(slave_name, O_RDWR);  /* becomes ctty on Linux */
ioctl(s, TIOCSCTTY, 0);            /* make sure (BSD needs it) */
dup2(s, 0); dup2(s, 1); dup2(s, 2);
if (s > 2) close(s);
execvp(prog, argv);
```

Conversely, programs that open terminals without wanting to adopt them
(for example a daemon opening a serial port) pass `O_NOCTTY`.

### 5.4 /dev/tty

The special file `/dev/tty` refers to the controlling terminal of whatever
process opens it. If the process has no controlling terminal, `open`
fails with `ENXIO`. It is the reliable way to reach the user when stdin and
stdout are redirected: `ssh`, `sudo`, `gpg`, `less`, `fzf` and `vim -`
all use it. A quick test for "do I have a controlling terminal?" is to
try opening it.

```text
$ setsid -w sh -c 'echo hi > /dev/tty'
sh: 1: cannot create /dev/tty: No such device or address
```

`setsid(1)` runs a command in a new session, which has no controlling
terminal, so `/dev/tty` fails.

### 5.5 Job control: what the shell does

When an interactive shell with job control runs a pipeline:

1. It forks each process of the pipeline.
2. Each child calls `setpgid(0, pgid)` to join the job's group (the first
   child's PID). The *parent* also calls `setpgid(child, pgid)` for each
   child. Both do it to avoid a race: whichever runs first wins, and the
   other call is harmless. Without the double call, the parent might call
   `tcsetpgrp` before the child is in the group, or the child might `exec`
   before the parent sets its group.
3. For a foreground job, the shell calls `tcsetpgrp(tty, pgid)` to give the
   terminal to the job.
4. Children reset signal dispositions that the shell changed (the shell
   ignores `SIGINT`, `SIGQUIT`, `SIGTSTP`, `SIGTTIN`, `SIGTTOU` for
   itself) back to default, then `exec`.
5. The shell waits with `waitpid(-pgid, &status, WUNTRACED)` to be told
   when the job exits *or stops*.
6. When the job is done or stopped, the shell takes the terminal back with
   `tcsetpgrp(tty, shell_pgid)` and restores its own termios settings (and
   saves the job's, so that `fg` can restore them: this is how `vim`
   survives `^Z` / `fg` with its raw mode intact, together with vim's own
   handling).

For `fg %1`: the shell calls `tcsetpgrp(tty, job_pgid)`, restores the
job's termios, sends `SIGCONT` to the group (`kill(-pgid, SIGCONT)`), and
waits. For `bg %1`: it only sends `SIGCONT`, without giving the terminal.

### 5.6 Background processes and the terminal

What happens when a background job touches the terminal?

- **Reading**: a process in a background group that reads from its
  controlling terminal is sent `SIGTTIN`, which stops it by default. The
  shell reports "suspended (tty input)". If the process ignores or blocks
  `SIGTTIN`, or its group is orphaned, `read` fails with `EIO` instead.
- **Writing**: allowed by default. If `TOSTOP` is set (`stty tostop`),
  writing sends `SIGTTOU` and stops the job.
- **Changing termios** (`tcsetattr`, `tcsetpgrp`, `tcflush` ...) from the
  background always sends `SIGTTOU`, regardless of `TOSTOP`, unless the
  process ignores or blocks it. That is why a full-screen program started in
  the background stops immediately: it tries to set raw mode.

```text
$ vim &
[1] + suspended (tty output)  vim
$ cat &
[2] + suspended (tty input)  cat
```

Shells themselves rely on this: a shell starting in the background of
another shell checks whether it is in the foreground
(`tcgetpgrp(0) == getpgrp()`), and if not, sends itself `SIGTTIN` until it
is.

### 5.7 SIGHUP and hangup

When the terminal goes away, the processes using it must be told:

- When a *controlling process* (session leader with a controlling terminal)
  exits, the kernel sends `SIGHUP` (followed by `SIGCONT`) to the
  foreground process group, and the terminal is disassociated from the
  session.
- When a hangup is detected on the terminal device (modem carrier lost, or
  for a PTY, the master is closed), `SIGHUP` is sent to the controlling
  process (session leader).
- Interactive shells, on receiving `SIGHUP`, typically resend `SIGHUP` to
  all their jobs before exiting (bash: "huponexit" for normal exits,
  always on `SIGHUP`). That is why closing a terminal window kills the
  programs you started from it, unless they used `nohup`, `disown` or
  `setsid`.

After the hangup, reads on the slave return 0 (EOF) and writes fail with
`EIO`. A process that ignores `SIGHUP` and keeps trying to write to its
dead terminal gets errors.

`nohup cmd` sets `SIGHUP` to ignored and redirects stdout to `nohup.out` if
it was a terminal. `disown` (bash/zsh) removes a job from the shell's job
table, so the shell does not forward `SIGHUP` to it, but the kernel may
still send one if the job is in the foreground group when the terminal goes
away. `setsid cmd` runs the command in a new session with no terminal, the
most thorough option.

### 5.8 Orphaned process groups

A subtle rule (POSIX): a process group is *orphaned* when no member has a
parent in a different group of the same session. Typically, when the shell
exits and leaves a stopped background job behind, nobody remains who could
ever send it `SIGCONT`. To prevent processes stuck in stopped state forever,
when a process group becomes orphaned and contains a stopped process, the
kernel sends `SIGHUP` followed by `SIGCONT` to every member.

Also, members of an orphaned group cannot be stopped by `SIGTSTP`,
`SIGTTIN` or `SIGTTOU` from the terminal: those signals are discarded, and
reads from the terminal return `EIO` instead of stopping the process.

You rarely deal with this directly, but it explains strange behaviors when
writing shells, and when a terminal program run from a script that
exits suddenly gets `EIO` errors.

### 5.9 Daemons and the double fork

The classic recipe to detach a daemon from its terminal:

1. `fork()`, parent exits: the child is not a group leader and is
   adopted by init (or the nearest subreaper).
2. `setsid()`: new session, no controlling terminal.
3. `fork()` again, first child exits: the grandchild is not a session
   leader, so it can never acquire a controlling terminal by opening one
   (System V rule). This is the "double fork".
4. `chdir("/")`, `umask(0)`, reopen fds 0, 1, 2 on `/dev/null`.

With systemd, none of this is needed: services are started detached by
the service manager, and should *not* daemonize themselves. But the recipe
shows the rules of sessions and controlling terminals in action.

### 5.10 Seeing it all with a small C program

This program prints its own IDs and the terminal's view of things. Run it
in different contexts (foreground, background, in a pipeline, under
`setsid`).

```c
// file: c/ids.c
#define _POSIX_C_SOURCE 200809L
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <string.h>
#include <termios.h>
#include <unistd.h>

int main(void)
{
    printf("pid=%d ppid=%d pgid=%d sid=%d\n",
           (int)getpid(), (int)getppid(), (int)getpgrp(), (int)getsid(0));

    int fd = open("/dev/tty", O_RDONLY | O_NOCTTY);
    if (fd == -1) {
        printf("no controlling terminal (%s)\n", strerror(errno));
        return 0;
    }
    pid_t fg = tcgetpgrp(fd);
    printf("ctty=%s foreground_pgid=%d tty_sid=%d -> I am in the %s\n",
           ttyname(fd), (int)fg, (int)tcgetsid(fd),
           fg == getpgrp() ? "FOREGROUND" : "background");
    close(fd);
    return 0;
}
```

```text
$ cc -Wall -o ids c/ids.c
$ ./ids
pid=5001 ppid=3990 pgid=5001 sid=3990
ctty=/dev/pts/3 foreground_pgid=5001 tty_sid=3990 -> I am in the FOREGROUND
$ ./ids &
pid=5002 ppid=3990 pgid=5002 sid=3990
ctty=/dev/pts/3 foreground_pgid=3990 tty_sid=3990 -> I am in the background
$ ./ids | cat
pid=5003 ppid=3990 pgid=5003 sid=3990
ctty=/dev/pts/3 foreground_pgid=5003 tty_sid=3990 -> I am in the FOREGROUND
$ setsid ./ids
pid=5005 ppid=3990 pgid=5005 sid=5005
no controlling terminal (No such device or address)
```

In the pipeline, `ids` and `cat` are both in group 5003, the foreground
group. Note that `setsid(1)` forks first if it is a group leader, which is
the case when run from an interactive shell, so the PID shown may differ
from the one the shell reported.

### 5.11 Summary

- Signals from the keyboard go to the *foreground process group*.
- A pipeline is one process group; the shell gives it the terminal with
  `tcsetpgrp`.
- A session has at most one controlling terminal; `setsid` + `open`
  (+ `TIOCSCTTY`) attaches one.
- Background groups that read the terminal get `SIGTTIN`; that change
  terminal settings get `SIGTTOU`.
- When the terminal or its controlling process goes away, `SIGHUP` is
  sent.
- `/dev/tty` is the controlling terminal, whatever the standard fds are.

---

## 6. Pseudo-terminals

### 6.1 The idea

A pseudo-terminal is a pair of character devices connected back to back:

```text
  terminal emulator / ssh / tmux / expect           shell / vim / any program
  +--------------------------+                       +------------------------+
  |   master fd  (ptmx)      |                       |  slave fd (/dev/pts/N) |
  |                          |   write -> input ---> |  read                  |
  |                          |                       |                        |
  |   read  <--- output <--- |                       |  write                 |
  +--------------------------+                       +------------------------+
                         \______ kernel: line discipline on slave side ______/
```

The slave side is a full terminal device: it has termios settings, a line
discipline, a window size, a foreground process group. A program cannot
distinguish it from a hardware terminal, except by its name or by asking
about things that make no sense on a PTY (like modem lines).

The master side is a plain bidirectional byte stream, with a few ioctls.
Bytes written to the master are *input* for the slave: they go through the
line discipline exactly as if typed on a keyboard (with echo, editing,
`^C` turning into `SIGINT`, CR to NL, and so on). Bytes written by programs
to the slave go through output processing (`ONLCR`) and can be read from
the master.

This one mechanism is behind:

- **terminal emulators**: the master is connected to a window;
- **ssh, telnet, rlogin**: the server-side `sshd` holds the master and
  sends its data over the network;
- **tmux, screen**: the multiplexer server holds one master per pane, and
  is itself a client of the outer terminal;
- **script, asciinema, ttyrec**: record everything that passes through the
  master;
- **expect, pexpect, rexpect**: drive interactive programs by writing to
  the master and matching what comes out;
- **unbuffer**, `script -c`: make a program believe it is interactive;
- **IDEs, Emacs `M-x term`, Jupyter terminals, web terminals (ttyd,
  gotty, xterm.js backends)**;
- **container runtimes**: `docker run -t` and `kubectl exec -t` allocate
  a PTY for the container's process;
- **sudo**: with `use_pty` (default in recent versions), `sudo` runs the
  command in a new PTY to prevent the command from injecting input into the
  user's terminal (`TIOCSTI` attacks);
- **CI systems and test harnesses** that need to exercise TUIs.

### 6.2 Opening a PTY: the POSIX way

The standard sequence (Unix98 PTYs):

```c
int master = posix_openpt(O_RDWR | O_NOCTTY);  /* opens /dev/ptmx */
grantpt(master);                 /* set slave ownership/permissions */
unlockpt(master);                /* allow the slave to be opened */
char *name = ptsname(master);    /* e.g. "/dev/pts/7" (static buffer) */
int slave = open(name, O_RDWR | O_NOCTTY);
```

- `posix_openpt` opens the multiplexer `/dev/ptmx`. Each open creates a new
  master/slave pair. On Linux it is literally `open("/dev/ptmx", flags)`.
- `grantpt` changes the owner of the slave device to the real UID of the
  caller and its mode to `0620` (group `tty`). On Linux with devpts
  mounted with appropriate options, this is already done by the kernel and
  `grantpt` is effectively a no-op (glibc checks and does nothing more).
- `unlockpt` clears a lock flag (`TIOCSPTLCK`) that prevents the slave from
  being opened until the master is set up.
- `ptsname` returns the slave's path. It is not thread-safe; glibc has
  `ptsname_r`. On Linux the underlying ioctl is `TIOCGPTN` (get pty
  number).
- Since Linux 4.13 you can open the slave directly from the master with
  `ioctl(master, TIOCGPTPEER, O_RDWR | O_NOCTTY)`, which avoids looking up
  the path (and races with path-based attacks in containers).

Older interfaces you will see in existing code:

- **BSD PTYs**: try `/dev/ptyp0`, `/dev/ptyp1`, ... until an `open`
  succeeds, then open the matching `/dev/ttyp0`. Obsolete and insecure;
  Linux removed support (`CONFIG_LEGACY_PTYS`) in most distributions.
- **`openpty(&master, &slave, name, termios, winsize)`**: BSD function,
  also in glibc (`<pty.h>`, link with `-lutil` on older glibc; merged into
  libc in glibc 2.34). It does all the steps and optionally sets the
  initial termios and window size. Convenient and widely available.
- **`forkpty(&master, name, termios, winsize)`**: `openpty` + `fork` +
  `login_tty` in the child. Returns 0 in the child (which is already
  connected to the slave as its controlling terminal on fds 0 to 2) and
  the child's PID in the parent. This is what most C programs use.
- **`login_tty(fd)`**: `setsid`, `TIOCSCTTY`, `dup2` onto 0, 1, 2, close.

### 6.3 The devpts filesystem

On Linux, slaves live in the `devpts` filesystem:

```text
$ mount | grep devpts
devpts on /dev/pts type devpts (rw,nosuid,noexec,relatime,gid=5,mode=620,ptmxmode=000)
$ ls -l /dev/ptmx /dev/pts/
crw-rw-rw- 1 root tty  5, 2 Nov 22 09:00 /dev/ptmx
/dev/pts/:
crw--w---- 1 cog  tty  136, 0 Nov 22 10:00 0
crw--w---- 1 cog  tty  136, 3 Nov 22 10:05 3
c--------- 1 root root   5, 2 Nov 22 09:00 ptmx
```

- `/dev/ptmx` is world read-write; anybody can create a PTY.
- Each slave is created with the owner of the process that opened the
  master, group `tty`, mode `0620`: the owner reads and writes, the `tty`
  group can write (so that `write(1)` and `wall` can send messages to your
  terminal, if you allow it with `mesg y`).
- The number of PTYs is limited by `/proc/sys/kernel/pty/max` (4096 by
  default) and `/proc/sys/kernel/pty/nr` shows how many are in use.
- Containers mount their own instance of devpts (`newinstance`), so PTY
  numbers in a container are independent from the host's.

### 6.4 Data flow in detail

Let us trace a keystroke and its echo through a PTY in canonical mode,
with default settings (`ICANON ECHO ICRNL ONLCR`):

1. The emulator writes `l` to the master.
2. The slave's line discipline receives `l`. `ECHO` is on, so it queues `l`
   for *output*; that output becomes readable on the master. `ICANON` is
   on, so `l` is stored in the line buffer.
3. The emulator reads `l` from the master and displays it.
4. The emulator writes `\r` (Enter).
5. The line discipline translates `\r` into `\n` (`ICRNL`), stores it,
   echoes it. On output, the echoed `\n` is translated into `\r\n`
   (`ONLCR`). The line `l\n` is now complete and becomes readable.
6. The program's `read()` on the slave returns `l\n`.

The emulator sees `l` then `\r\n` from the master. Note that *the
emulator* gets the echo, it never sees the "real" input line: it only knows
what it wrote and what came back.

This has an important consequence for programs that drive other programs
through a PTY (like `expect`): what you read from the master includes the
*echo of what you wrote*, mixed with the program's output, in an order
that depends on timing. If you send `password\r` to a program that turned
echo off, you will not see it echoed. If you send it to a program with echo
on, you will. Robust automation either turns echo off on the slave before
starting the child, or matches patterns that tolerate the echo.

### 6.5 What the master can do

Useful operations on the master fd:

- `read`/`write`: the data streams.
- `ioctl(master, TIOCSWINSZ, &ws)`: set the window size of the slave. The
  kernel sends `SIGWINCH` to the slave's foreground process group if the
  size changed. Terminal emulators do this when you resize the window;
  `ssh` forwards size changes to the server, where `sshd` does it.
- `ioctl(master, TIOCGWINSZ, &ws)`: read the window size.
- `tcgetattr(master, ...)`: on Linux, this returns the *slave's* termios
  settings. So the master can see whether the slave is in canonical mode,
  whether echo is on, etc. `ssh` and some password-prompt detectors use
  this ("echo is off: the program is probably asking for a password").
- `ioctl(master, TIOCPKT, &one)`: *packet mode*. Each `read` on the master
  starts with a status byte: 0 for normal data, or flags such as
  `TIOCPKT_FLUSHREAD`, `TIOCPKT_STOP`, `TIOCPKT_START`, `TIOCPKT_NOSTOP`,
  `TIOCPKT_DOSTOP`. `rlogind` used it to forward flow-control state. On
  Linux there is also `TIOCPKT_IOCTL`, set when the slave's termios
  changes (with `EXTPROC`).
- `ioctl(master, TIOCSIG, sig)`: send a signal to the slave's foreground
  process group (Linux 2.6.36+), as if the user typed the corresponding
  character, even if `ISIG` is off.
- `tcgetpgrp(master)`: on Linux, returns the foreground process group of
  the slave. This is how terminal emulators and `tmux` show the name of
  the program running in the foreground ("vim", "htop") in the title or
  status line: they read `/proc/<pgid>/comm` or `/proc/<pgid>/cmdline`.
- `ioctl(master, TIOCGPTN, &n)`: the PTY number.
- `ioctl(master, TIOCGPTPEER, flags)`: open the slave (see above).

### 6.6 End of file and EIO

When every fd on the slave is closed (the shell and all its children have
exited, or closed their terminal fds), the master reports end-of-file. On
Linux, this is reported as an *error*: `read(master)` returns `-1` with
`errno == EIO`. On BSD and macOS, it usually returns 0. Portable code treats
both as EOF.

```c
ssize_t n = read(master, buf, sizeof buf);
if (n == 0 || (n == -1 && errno == EIO)) {
    /* child side is gone: EOF */
}
```

Why `EIO`? Historically, a hangup on a terminal device was an I/O error,
and the Linux PTY master reports the slave's close as a hangup. Go's
`creack/pty`, Rust's `portable-pty` and Python's `pty` module all contain
code to translate `EIO` into EOF.

A related trap: **data loss at exit**. Suppose the child writes its last
output and exits immediately. On Linux, the data is in the slave's output
buffer; the master can read it as long as the master is open. But if you
check for child exit (via `SIGCHLD`/`waitpid`) and stop reading as soon as
the child is dead, you may miss the final output. Always drain the master
until `EIO`/0 before considering the session finished. Conversely, if a
*grandchild* keeps the slave open (a background process started by the
shell), you will not get `EIO` even though the child has exited, so you
need both signals: child exit for the status, EOF for the end of output.

Another trap, on the *slave* side this time: if the master is closed while
a program is still running on the slave, the program gets `SIGHUP` (if it
is the session leader or in the foreground group); reads return 0 and
writes return `EIO`.

### 6.7 Writing to the master: buffering and blocking

The master's input direction has a limited buffer (a few KiB of line
discipline buffer, and the PTY's flip buffers). If the program on the slave
does not read its input (say it is busy, or in canonical mode and the line
buffer is full), writes to the master eventually block. Meanwhile, if the
program writes a lot of output and you do not read the master, the program
blocks on its writes. That is the same two-way deadlock as with pipes
(section 3.6), and the same remedy applies: always read and write
concurrently, with `poll` or with two threads.

In canonical mode the line discipline will also *drop* input beyond 4095
characters in a line. If you pipe a large file into a program through a
PTY in canonical mode (for example `cat > file` on the slave), long lines
get truncated, and since the kernel echoes everything back, you also need
to read twice the data. To send bulk data through a PTY, put the slave in
raw mode first.

### 6.8 Terminal settings on a new PTY

A new PTY's slave starts with the kernel's default termios on Linux:
`ICANON ECHO ECHOE ECHOK ISIG IEXTEN ECHOCTL ECHOKE ICRNL IXON OPOST ONLCR
CS8 CREAD B38400` and the default special characters. The window size is
0x0. Programs started on it should get a sensible window size, so set
`TIOCSWINSZ` before starting the child (or pass a `winsize` to `openpty`/
`forkpty`). Some programs misbehave with 0x0 (division by zero in layout
code, or falling back to 80x24 silently).

Two common customizations when starting a child on a PTY for automation:

- copy the termios of the *real* terminal (if any) to the new slave, so
  that a user's special keys (erase character etc.) match: that is what
  `script` does;
- disable `ECHO` for automation, so that you do not read back your own
  input.

### 6.9 The terminal emulator's main loop

Every PTY "host" has the same structure. In pseudo-code:

```text
master, child = spawn_on_pty(program, size)
set raw mode on our own terminal (if we are running inside one)
loop:
    wait until one of these is ready:
        our stdin / keyboard / window events  -> write bytes to master
        master readable                        -> read bytes, process,
                                                  write to screen / log
        SIGWINCH on our terminal               -> TIOCSWINSZ on master
        child exited (SIGCHLD)                 -> remember status
    if master gave EOF/EIO: break
restore our terminal
waitpid(child) and exit with its status
```

"Process" in the master-readable case depends on the program:

- `script` writes the bytes unchanged to stdout and to a log file;
- `expect` appends them to a buffer and matches patterns;
- `tmux` and terminal emulators *parse* them as VT escape sequences and
  update a screen model, then render that model (to a window, or as escape
  sequences on the outer terminal);
- `ssh` encrypts them and sends them on the network.

You will write this loop in C (chapter 12), Raku (chapter 17), Rust
(chapter 22) and Go (chapter 27), and compare them in chapter 29.

### 6.10 Window size propagation

Who knows the window size, and how does it flow?

```text
  window system: user drags the corner
        |
        v
  terminal emulator: computes rows/cols from pixel size and font
        |  ioctl(master, TIOCSWINSZ, {rows, cols, xpix, ypix})
        v
  kernel: stores winsize in the tty; if changed, SIGWINCH to fg pgrp
        |
        v
  program on slave (vim): SIGWINCH handler sets a flag;
        main loop: ioctl(0, TIOCGWINSZ) -> redraw
```

For a nested setup (tmux inside ssh inside a terminal emulator), each hop
repeats the dance: the local `ssh` client gets `SIGWINCH` from its terminal,
reads the new size, sends a "window-change" message to the server; `sshd`
calls `TIOCSWINSZ` on its master; the remote tmux client gets `SIGWINCH`,
tells the tmux server, which recomputes pane sizes and calls `TIOCSWINSZ`
on each pane's master, and each pane's program gets `SIGWINCH`.

### 6.11 Security notes

- **TIOCSTI**: an ioctl that injects a character into a terminal's input
  queue, as if typed. A program that can write to your terminal fd (for
  example, a command run with `su` that shares your terminal) could inject
  commands that your shell would execute after the program exits. Linux
  6.2 added `CONFIG_LEGACY_TIOCSTI` and the `dev.tty.legacy_tiocsti`
  sysctl to disable it, and many distributions disable it now. OpenBSD
  removed it. This is also why `sudo` and `su` use a fresh PTY.
- **Escape sequence injection**: anything printed to a terminal is
  interpreted. A file name or log line containing escape sequences can
  change the window title, redefine keys on some old terminals, or (with
  bugs in emulators) do worse. Tools that print untrusted data to a
  terminal should sanitize control characters (`ls` does with `-q`/`-b`,
  `less` by default shows them as `^[`).
- **Leaked master fds**: a child that inherits a PTY master can read
  everything the user types in that terminal. Always set close-on-exec on
  masters.
- **Permissions**: slaves are `0620` with group `tty`; programs like
  `write` are setgid `tty`. `mesg n` removes group write permission.

### 6.12 PTYs on other systems

- **macOS**: same POSIX API; `posix_openpt` returns a master on
  `/dev/ptmx`, slaves are `/dev/ttys000` and so on. `read` on the master
  after slave close returns 0 or `EIO` depending on version. Watch out for
  `poll` on PTYs: it was broken on old macOS versions; `select` was the
  safe choice.
- **FreeBSD/OpenBSD/NetBSD**: `posix_openpt` and `openpty`; slaves in
  `/dev/pts/N` on FreeBSD. `TIOCSCTTY` required.
- **Windows**: there were no PTYs until Windows 10 1809, which added the
  *ConPTY* API (`CreatePseudoConsole`). It translates the Windows console
  API to VT sequences. Libraries like `portable-pty` (Rust, from WezTerm),
  `node-pty` and Go's `charmbracelet/x/conpty` wrap both. This document
  covers Unix only, but the Rust and Go libraries shown are portable.

---

## 7. Talking to the screen: escape sequences

The kernel's terminal layer knows nothing about colors, cursor positions or
the screen. Those are handled by the *terminal emulator* (or the hardware
terminal), which parses the byte stream coming out of the master and
interprets control characters and escape sequences. This chapter covers
what a program can send, and what it receives back.

### 7.1 Notation

The standards and the xterm documentation (`ctlseqs`, "XTerm Control
Sequences" by Thomas Dickey, the de facto reference) use this notation:

| Name | Bytes | Meaning |
|------|-------|---------|
| ESC | `0x1b` | escape |
| CSI | `ESC [` | control sequence introducer |
| OSC | `ESC ]` | operating system command |
| DCS | `ESC P` | device control string |
| ST | `ESC \` | string terminator |
| BEL | `0x07` | bell (also ends OSC) |
| SS3 | `ESC O` | single shift 3 |
| APC | `ESC _` | application program cmd |

In source code, ESC is written `\033` or `\x1b` in C, `\e` in many shells,
Raku (`"\e"`) and Perl, `\x1b` or `\u{1b}` in Rust, `\x1b` or `\033` in Go.

ECMA-48 also defines 8-bit C1 controls (CSI as the single byte `0x9b`),
but they conflict with UTF-8, so in practice everybody uses the 7-bit
forms. Never emit 8-bit C1 controls to a UTF-8 terminal.

A CSI sequence has the form:

```text
CSI  [private-marker]  params  [intermediate]  final
ESC [      ?           1;2;3       (space)       h
```

- parameters: decimal numbers separated by `;` (and, in newer
  sequences, sub-parameters separated by `:`);
- an optional private marker `?`, `>`, `<` or `=` right after CSI marks
  vendor-specific (DEC private) sequences;
- the final byte, in the range `@` to `~`, selects the function.

Missing parameters take a default value, usually 1 for movement and 0 for
other functions: `CSI H` is "cursor to 1;1".

### 7.2 Control characters (C0)

The terminal interprets the ASCII control characters:

| Char | Hex | Effect |
|------|-----|--------|
| BEL | 07 | bell / visual flash |
| BS | 08 | cursor left one |
| HT | 09 | next tab stop |
| LF | 0a | down one line (scroll at bottom) |
| VT, FF | 0b, 0c | treated as LF |
| CR | 0d | column 0 |
| SO, SI | 0e, 0f | switch charsets G1/G0 |
| ESC | 1b | starts a sequence |

LF only moves down. That is why the kernel's `ONLCR` translation exists,
and why raw-mode programs with `OPOST` off must write `\r\n`.

### 7.3 Cursor movement

| Sequence | Name | Effect |
|----------|------|--------|
| `CSI n A` | CUU | up n |
| `CSI n B` | CUD | down n |
| `CSI n C` | CUF | right n |
| `CSI n D` | CUB | left n |
| `CSI n E` | CNL | down n, column 1 |
| `CSI n F` | CPL | up n, column 1 |
| `CSI n G` | CHA | to column n |
| `CSI r;c H` | CUP | to row r, column c |
| `CSI r d` | VPA | to row r |
| `ESC 7` | DECSC | save cursor |
| `ESC 8` | DECRC | restore cursor |
| `CSI s` | SCOSC | save (ANSI.SYS) |
| `CSI u` | SCORC | restore |

Rows and columns are 1-based. Movement stops at the screen edges (no
wrapping, no scrolling), except for LF and the `ESC D`/`ESC M` index
functions.

`CSI s`/`CSI u` conflict with other uses in some terminals (and `CSI u`
is reused by the kitty keyboard protocol in a different context);
`ESC 7`/`ESC 8` are the safe choice for save/restore.

### 7.4 Erasing and editing

| Sequence | Name | Effect |
|----------|------|--------|
| `CSI 0 J` | ED | clear to end of screen |
| `CSI 1 J` | ED | clear to start of screen |
| `CSI 2 J` | ED | clear whole screen |
| `CSI 3 J` | ED | clear scrollback (xterm) |
| `CSI 0 K` | EL | clear to end of line |
| `CSI 1 K` | EL | clear to start of line |
| `CSI 2 K` | EL | clear whole line |
| `CSI n L` | IL | insert n lines |
| `CSI n M` | DL | delete n lines |
| `CSI n @` | ICH | insert n blanks |
| `CSI n P` | DCH | delete n chars |
| `CSI n X` | ECH | erase n chars |
| `CSI t;b r` | DECSTBM | scroll region |
| `CSI n S` | SU | scroll up n |
| `CSI n T` | SD | scroll down n |

`CSI 2 J` does not move the cursor; combine it with `CSI H`. The `clear`
command sends `CSI H CSI 2 J` and, with recent ncurses, `CSI 3 J` to clear
the scrollback too.

The scroll region (`DECSTBM`) restricts scrolling to lines t..b. Programs
like `less` and status-line tools use it to keep a fixed line at the
bottom while the rest scrolls.

### 7.5 SGR: colors and attributes

`CSI params m` is *Select Graphic Rendition*. Parameters accumulate; `0`
resets everything.

| Param | Effect | Reset by |
|-------|--------|----------|
| 0 | reset all | |
| 1 | bold | 22 |
| 2 | dim/faint | 22 |
| 3 | italic | 23 |
| 4 | underline | 24 |
| 5 | blink | 25 |
| 7 | reverse | 27 |
| 8 | hidden | 28 |
| 9 | strikethrough | 29 |
| 30-37 | fg color | 39 |
| 40-47 | bg color | 49 |
| 90-97 | bright fg | 39 |
| 100-107 | bright bg | 49 |

The eight basic colors are, in order: black, red, green, yellow, blue,
magenta, cyan, white. Their actual appearance depends on the terminal's
palette (and the user's theme).

Extended colors:

- 256 colors: `CSI 38;5;n m` (foreground) and `CSI 48;5;n m`
  (background). Indices 0 to 15 are the basic and bright colors, 16 to 231
  a 6x6x6 color cube (`16 + 36r + 6g + b` with r, g, b in 0..5), 232 to 255
  a grayscale ramp.
- Truecolor (24-bit): `CSI 38;2;r;g;b m` and `CSI 48;2;r;g;b m`. The
  standard (ITU T.416) form uses colons: `CSI 38:2::r:g:b m` (note the
  empty color-space id). Most terminals accept both; the semicolon form is
  more widely supported.
- Underline styles and colors (kitty, VTE, WezTerm, Ghostty, foot ...):
  `CSI 4:3 m` for a curly underline, `CSI 58;2;r;g;b m` for its color.

There is no reliable way to know if a terminal supports truecolor. The
convention is the environment variable `COLORTERM=truecolor` (or
`24bit`), set by the emulator. Libraries also consult terminfo (`Tc`,
`RGB` capabilities) and query the terminal (`DECRQSS`, XTGETTCAP), and
degrade colors otherwise. The `NO_COLOR` environment variable
(no-color.org) asks programs not to emit colors at all; `FORCE_COLOR` and
`CLICOLOR_FORCE` ask them to emit colors even on non-terminals.

Example from the shell:

```text
$ printf '\e[1;31mbold red\e[0m normal \e[38;5;208morange\e[0m \e[38;2;0;128;255mazure\e[0m\n'
```

### 7.6 Modes: DECSET and DECRST

`CSI ? n h` sets (enables) DEC private mode n, `CSI ? n l` resets it. The
ones every TUI uses:

| Mode | Effect when set |
|------|-----------------|
| `?1` | application cursor keys |
| `?7` | auto-wrap (default on) |
| `?25` | show cursor (default on) |
| `?47`, `?1047` | alternate screen |
| `?1048` | save/restore cursor |
| `?1049` | save cursor + alt screen + clear |
| `?1000` | mouse: press/release |
| `?1002` | mouse: + drag |
| `?1003` | mouse: + all motion |
| `?1004` | focus in/out events |
| `?1006` | SGR mouse encoding |
| `?2004` | bracketed paste |
| `?2026` | synchronized output |

And a few ANSI (non-private) modes: `CSI 4 h` insert mode, `CSI 20 h`
automatic newline (LNM).

**The alternate screen** (`?1049`) is why `vim`, `less` and `htop` do not
leave their output in your scrollback: they switch to a second screen
buffer on start and back to the main one on exit, and the main screen
reappears as it was. If a TUI crashes without switching back, you are left
on the alternate screen with no scrollback; `reset` or `tput rmcup` fixes
it.

**Application cursor keys** (`?1`, "DECCKM"): in normal mode, the arrow
keys send `CSI A` etc. In application mode they send `SS3 A` (`ESC O A`).
Readline and ncurses switch to application mode (through the terminfo
`smkx` capability), which is why the key sequences in terminfo (`kcuu1=\EOA`)
do not match what you see in `cat -v` at the shell prompt (`^[[A`).

**Synchronized output** (`?2026`): the program announces "I am about to
redraw; do not display partial updates until I reset this mode". It
prevents tearing in fast-updating TUIs. Supported by most modern
emulators; ignored harmlessly by others.

### 7.7 Input: what keys send

What the program reads from the terminal for each key (xterm-compatible,
normal cursor mode):

| Key | Bytes | Shown by `cat -v` |
|-----|-------|-------------------|
| Up | `ESC [ A` | `^[[A` |
| Down | `ESC [ B` | `^[[B` |
| Right | `ESC [ C` | `^[[C` |
| Left | `ESC [ D` | `^[[D` |
| Home | `ESC [ H` | `^[[H` |
| End | `ESC [ F` | `^[[F` |
| Insert | `ESC [ 2 ~` | `^[[2~` |
| Delete | `ESC [ 3 ~` | `^[[3~` |
| PgUp | `ESC [ 5 ~` | `^[[5~` |
| PgDn | `ESC [ 6 ~` | `^[[6~` |
| F1-F4 | `ESC O P`..`S` | `^[OP` |
| F5 | `ESC [ 1 5 ~` | `^[[15~` |
| F6-F8 | `[17~` `[18~` `[19~` | |
| F9-F12 | `[20~` `[21~` `[23~` `[24~` | |
| Tab | `0x09` | `^I` |
| Shift+Tab | `ESC [ Z` | `^[[Z` |
| Enter | `0x0d` | `^M` |
| Backspace | `0x7f` | `^?` |
| Esc | `0x1b` | `^[` |

Modifiers are encoded as a parameter: `ESC [ 1 ; m X` where `m` is 1 +
(1 for Shift, 2 for Alt, 4 for Ctrl, 8 for Meta). So Ctrl+Up is
`ESC [ 1 ; 5 A`, Shift+Up is `ESC [ 1 ; 2 A`, Ctrl+Shift+Delete is
`ESC [ 3 ; 6 ~`.

**The ESC ambiguity.** When the program reads a lone `0x1b`, is it the
Escape key, or the beginning of a sequence whose next bytes have not arrived
yet? Over a slow link (ssh) they can arrive in separate reads. Programs use
a timeout: if no further byte arrives within, say, 25 to 50 ms, it was the
Escape key. Vim's `ttimeoutlen`, tmux's `escape-time` (default 500 ms in
old versions, hence the classic "Esc is slow in vim inside tmux"), and
Bubble Tea's and crossterm's parsers all have this. The kitty keyboard
protocol removes the ambiguity by encoding Escape as `CSI 27 u`.

**Alt and Meta.** Alt+x is sent as `ESC x`, which is also ambiguous with
Escape followed quickly by x. Again, the timeout decides.

### 7.8 Mouse reporting

When a mouse mode is enabled, the terminal sends mouse events as input.
The modern encoding is SGR (`?1006`):

```text
CSI < button ; column ; row M      (press, or motion)
CSI < button ; column ; row m      (release)
```

`button` is 0 (left), 1 (middle), 2 (right), plus 32 for motion, 64 for
the wheel (64 up, 65 down), plus 4/8/16 for Shift/Meta/Ctrl. Coordinates are
1-based. The older X10 encoding (`CSI M` followed by three bytes `32+b`,
`32+x`, `32+y`) cannot represent columns beyond 223 and breaks UTF-8,
which is why every new program should use `?1006`.

To enable, a program typically sends `CSI ? 1000 h CSI ? 1002 h
CSI ? 1006 h`, and disables them in reverse at exit. When mouse reporting
is on, the terminal stops doing its own text selection (usually Shift+drag
still selects).

### 7.9 Bracketed paste

With `?2004` enabled, the terminal wraps pasted text in `CSI 200 ~` and
`CSI 201 ~`. The program can then insert the text literally instead of
interpreting it as typed keys: a pasted newline does not execute a command
in the shell, and a pasted `:q!` does not quit vim. Bash, zsh, fish, vim,
neovim and most line editors enable it.

Security note: the terminal should strip `CSI 201 ~` from the pasted text
itself, otherwise malicious clipboard content could "end" the paste early
and inject commands. Modern emulators do.

### 7.10 Queries and replies

Some sequences ask the terminal a question; the answer arrives *as input*,
on the same channel as keystrokes:

| Query | Reply | Meaning |
|-------|-------|---------|
| `CSI 6 n` | `CSI r ; c R` | cursor position |
| `CSI c` | `CSI ? 6x ; ... c` | primary DA |
| `CSI > c` | `CSI > ... c` | secondary DA |
| `CSI 18 t` | `CSI 8 ; h ; w t` | size in chars |
| `CSI 14 t` | `CSI 4 ; h ; w t` | size in pixels |
| `CSI ? u` | `CSI ? flags u` | kitty keyboard |
| `OSC 10 ; ? ST` | `OSC 10 ; rgb:... ST` | fg color |
| `OSC 11 ; ? ST` | `OSC 11 ; rgb:... ST` | bg color |
| `CSI ? 2026 $ p` | `CSI ? 2026 ; s $ y` | mode state |

Reading the reply is tricky:

- The terminal must be in non-canonical mode with echo off, otherwise the
  reply waits for Enter and is echoed on screen.
- The reply may be mixed with keys the user is typing. Parse carefully and
  keep the other bytes.
- A terminal that does not support the query never answers. Always use a
  timeout. A common trick is to send the query you care about followed by
  *primary device attributes* (`CSI c`), which every terminal answers: if
  the DA reply arrives first, the other query is not supported.

Two common uses: detecting a dark or light background (`OSC 11`) to choose
a color scheme (Bubble Tea's `tea.RequestBackgroundColor`, Lip Gloss's
`HasDarkBackground`), and measuring the width a string actually takes
by printing it and asking for the cursor position.

### 7.11 OSC sequences

Operating system commands carry strings. They end with ST (`ESC \`) or BEL.

| Sequence | Effect |
|----------|--------|
| `OSC 0 ; text ST` | icon name + window title |
| `OSC 2 ; text ST` | window title |
| `OSC 7 ; file://host/path ST` | current directory |
| `OSC 8 ; params ; uri ST` | hyperlink start |
| `OSC 8 ; ; ST` | hyperlink end |
| `OSC 52 ; c ; base64 ST` | set clipboard |
| `OSC 4 ; n ; color ST` | set palette entry |
| `OSC 133 ; A ST` ... | shell integration marks |
| `OSC 9 ; text ST` | notification (some) |

Hyperlinks (`OSC 8`) are worth showing:

```text
$ printf '\e]8;;https://example.com\e\\a link\e]8;;\e\\\n'
```

`OSC 52` lets a program running over ssh (or in tmux) put text into your
*local* clipboard. Many emulators restrict it to writes only, or ask for
confirmation, since reading the clipboard from a remote program would be a
security risk.

`OSC 133` (from FinalTerm, adopted by iTerm2, kitty, WezTerm, Ghostty, VS
Code ...) lets the shell mark where the prompt, the command and the output
start, so the emulator can jump between prompts or select a command's
output.

These numbers come from several unrelated sources, with collisions:
7.16 tells who defined which, and where to find the specifications.

### 7.12 Character width and Unicode

The terminal is a grid of cells. Most characters occupy one cell, but:

- East Asian wide characters (CJK) and most emoji occupy *two* cells;
- combining characters (accents as separate code points, U+0301) occupy
  zero cells: they modify the previous cell;
- zero-width joiners combine several emoji into one glyph (family emoji,
  flags with regional indicators), whose width depends on the terminal;
- control characters have no width.

The program must know the width of what it prints to place the cursor.
Libraries use `wcwidth()` tables (C), `unicode-width` (Rust), `go-runewidth`
or `uniseg` / `displaywidth` (Go), `Text::...` modules or `.chars` plus a
width table in Raku. If the program and the terminal disagree, the display
gets corrupted: the cursor is one cell off, lines wrap at the wrong
place. Recent terminals support *mode 2027* (grapheme clustering), which a
program can query and enable to agree on the width of grapheme clusters.

Raku is interesting here because its `Str` type works with graphemes by
default: `"e\x[301]".chars` is 1, which matches what a terminal that does
grapheme clustering will draw.

### 7.13 The kitty keyboard protocol

Classic key encoding cannot represent many key combinations, nor key
release events. The kitty keyboard protocol (now supported by kitty,
foot, WezTerm, Ghostty, Alacritty, iTerm2, Rio, and recent versions of
others) fixes this. The program enables it with `CSI > flags u` (push)
and disables it with `CSI < u` (pop). Flags:

| Flag | Meaning |
|------|---------|
| 1 | disambiguate escape codes |
| 2 | report event types (press/repeat/release) |
| 4 | report alternate keys (shifted, base layout) |
| 8 | report all keys as escape codes |
| 16 | report associated text |

With flag 1, keys that were ambiguous are sent as `CSI code ; mods u`:
Escape is `CSI 27 u`, Ctrl+I is `CSI 105 ; 5 u` while Tab stays `0x09`,
Ctrl+Shift+A is distinguishable from Ctrl+A. Bubble Tea v2 and crossterm
support it, and it is the reason modern TUIs can bind more keys.

### 7.14 Graphics

Several protocols display images in the terminal:

- **Sixel** (DEC, 1980s, revived): a DCS sequence that encodes a bitmap
  six pixels high per row. Supported by xterm (with options), foot,
  WezTerm, mlterm, Windows Terminal, recent Konsole, and others.
- **Kitty graphics protocol**: APC sequences carrying PNG or raw pixel
  data, with placement, z-index, animation. Supported by kitty, Ghostty,
  WezTerm (partially), Konsole (partially).
- **iTerm2 inline images**: `OSC 1337 ; File=... ST`.

Out of scope for this tutorial, but now you know what the long
base64-filled sequences in a TUI's output are.

### 7.15 Parsing what the terminal sends: a state machine

To *receive* input properly, a TUI needs a parser that turns a byte stream
into key, mouse, paste and reply events. To *display* output properly, a
terminal emulator needs a parser that turns the byte stream into screen
operations. Both are state machines. Paul Flo Williams documented the
DEC-compatible parser state machine used by most emulators (on
vt100.net): states `ground`, `escape`, `escape_intermediate`,
`csi_entry`, `csi_param`, `csi_intermediate`, `csi_ignore`,
`dcs_*`, `osc_string`, `sos_pm_apc_string`, with actions `print`,
`execute`, `collect`, `param`, `esc_dispatch`, `csi_dispatch`, `hook`,
`put`, `unhook`, `osc_start`, `osc_put`, `osc_end`.

You will see implementations: `Terminal::ANSIParser` in Raku is a
compact version; the Rust `vte` crate (used by Alacritty) and Go's
`charmbracelet/x/ansi` parser implement it fully. In chapter 31 we use a
simplified parser to build a tiny terminal multiplexer.

### 7.16 Where OSC numbers come from

Section 7.11 listed OSC sequences as if they came from one standard.
They do not. The number after `OSC` is chosen by whoever invents the
sequence. There are several sources, no registry, and the occasional
collision.

**ECMA-48 defines the envelope, not the contents.**
[ECMA-48](https://ecma-international.org/publications-and-standards/standards/ecma-48/)
(5th edition, 1991, identical to ISO/IEC 6429) defines five *control
strings*:

- OSC, operating system command;
- DCS, device control string;
- APC, application program command;
- PM, privacy message;
- SOS, start of string.

Each starts with its introducer (`ESC ]` for OSC, or the single byte
0x9D) and ends with ST, the string terminator (`ESC \`, or 0x9C). For
OSC, the standard leaves the meaning of the string to the operating
system. It defines no numbers, and not even the `Ps ; Pt` shape that
everybody uses: that shape comes from xterm. The standard also limits
the string to the bytes 0x08–0x0D and 0x20–0x7E, so a UTF-8 window
title is, strictly speaking, outside the standard. Every modern
terminal accepts one anyway.

This has two practical consequences:

- **Only the 7-bit forms work.** The 8-bit introducers 0x9D and 0x9C
  are also UTF-8 continuation bytes. Terminals in UTF-8 mode therefore
  recognize only `ESC ]` and `ESC \`.
- **BEL is a second terminator.** ECMA-48 does not allow BEL (0x07)
  there, but xterm accepted it from the start, and every emulator
  followed. xterm answers a query with the terminator the query used.

**xterm is the de facto registry.** Thomas Dickey's
[XTerm Control Sequences](https://invisible-island.net/xterm/ctlseqs/ctlseqs.html)
documents what xterm does. Almost every emulator claims to be xterm
(`TERM=xterm-256color`), so its numbers became the common base:

| OSC     | Meaning           |
|---------|-------------------|
| 0, 1, 2 | icon and title    |
| 3       | X property        |
| 4       | palette color     |
| 5, 6    | special colors    |
| 10–19   | dynamic colors    |
| 22      | pointer shape     |
| 46      | log file          |
| 50      | font              |
| 52      | clipboard         |
| 104–119 | reset colors      |

Some details:

- **Titles.** 0 sets both the icon name and the window title, 1 only
  the icon name, and 2 only the window title.
- **Dynamic colors** (10–19). 10 is the default foreground, 11 the
  background, 12 the cursor, 13 and 14 the mouse pointer, and 17 and
  19 the selection highlight. 15, 16 and 18 are for the Tektronix
  window that xterm still emulates.
- **Queries.** A `?` in place of a value asks for the current value.
  The answer uses the X11 color syntax, `rgb:RRRR/GGGG/BBBB`.
- **Resets.** 104, 110, 111 and 112 undo what 4, 10, 11 and 12 set.
- **Clipboard.** In OSC 52, the first parameter names the X
  selection: `c` is the clipboard and `p` is the primary selection.

**Other emulators took the free numbers.** Numbers that xterm does
not use were taken by whoever needed them:

| OSC  | Meaning           | Origin        |
|------|-------------------|---------------|
| 7    | current directory | Terminal.app  |
| 8    | hyperlink         | VTE, iTerm2   |
| 9    | notification      | iTerm2        |
| 9;N  | many commands     | ConEmu        |
| 99   | notification      | kitty         |
| 133  | prompt marks      | FinalTerm     |
| 633  | shell integration | VS Code       |
| 777  | notification      | urxvt         |
| 1337 | many commands     | iTerm2        |
| 3008 | context           | systemd       |

- **OSC 7** carries `file://HOST/PATH`, with the path
  percent-encoded. macOS Terminal and VTE (the library behind GNOME
  Terminal) popularized it. With it, a new tab or split opens in the
  same directory, and the host part tells the terminal when the
  directory is on another machine. Windows Terminal used ConEmu's
  `OSC 9 ; 9 ; PATH` for the same job.
- **OSC 8** hyperlinks were specified by Egmont Koblinger in 2017 for
  GNOME Terminal, together with iTerm2
  ([the specification](https://gist.github.com/egmontkob/eb114294efbcd5adb1944c9f3cb5feda)).
  The optional `id=` parameter joins the pieces of one link that a
  full-screen program draws in several places.
- **OSC 9 collides.** iTerm2 reads `OSC 9 ; TEXT` as "show TEXT as a
  notification". ConEmu reads `OSC 9 ; N ; ...` as command number N:
  9;4 is a progress bar and 9;9 the current directory. The terminal
  cannot tell `OSC 9 ; 4 ; 1 ; 50` (progress at 50 %) from a
  notification that reads "4;1;50". The progress bar escaped ConEmu
  (Windows Terminal draws it in the tab), so terminals that support
  both have to guess.
- **Notifications have three protocols.** These are iTerm2's OSC 9,
  urxvt's `OSC 777 ; notify ; TITLE ; BODY`, and kitty's OSC 99. Only
  kitty's has identifiers, urgency and a report when the notification
  is clicked.
- **OSC 133** comes from FinalTerm, an experimental terminal of 2013.
  The shell sends `A` where the prompt starts, `B` where the command
  starts, `C` where the output starts, and `D;STATUS` at the end. The
  terminal can then jump from prompt to prompt, select one command's
  output, and mark failed commands. VS Code needed more (the exact
  command line, for example) and defined OSC 633 with the same
  letters plus its own.
- **OSC 1337** is iTerm2's grab bag: `File=` for inline images
  (7.14), `SetUserVar=`, `CurrentDir=`, `SetMark` and a few dozen
  more. WezTerm implements some of them.
- **OSC 3008** is the most recent. It appeared with systemd 257 in
  2024, and is specified by the
  [UAPI group](https://uapi-group.org/specifications/specs/osc_context/).
  Tools that change context (`ssh`, a container, a VM, `run0` for
  privileges) announce where the following output comes from, so
  that the terminal can show it.

**There is no standards body.** The closest thing is the
[terminal-wg](https://gitlab.freedesktop.org/terminal-wg/specifications)
project at freedesktop.org. There, emulator authors file proposals and
argue about them: hyperlinks, semantic prompts, and many more that
never reached consensus. Otherwise, the documentation of the terminal
that invented a sequence is its specification. That means kitty's
protocol extensions, iTerm2's "proprietary escape codes" page, and
the Windows Terminal documentation. A practical rule: look in
ctlseqs first; if xterm does not have the number, read the inventor's
page.

**Detecting support is guesswork.** Modes can be queried (`DECRQM`,
B.9), but there is no general way to ask whether an OSC is supported.
Unknown OSC sequences are dropped silently, which is convenient: a
shell can always emit OSC 7 and 133, and terminals that do not know
them ignore them. A query is different, because an unsupported query
is never answered (7.10). terminfo knows a few:

- the standard `tsl`, `fsl` and `hs` capabilities, for a status line
  that some entries use for the title;
- the extended `Ms` capability (OSC 52), set by tmux;
- the extended `Cs` and `Cr` capabilities (cursor color), also set by
  tmux.

For the rest, programs look at environment variables:

- `TERM_PROGRAM`, set to `iTerm.app`, `WezTerm`, `vscode`, `ghostty`
  or `tmux`;
- `KITTY_WINDOW_ID`;
- `VTE_VERSION`;
- `WT_SESSION`, for Windows Terminal.

These variables cross `ssh` badly, and they lie inside a multiplexer.

**Multiplexers stand in the middle.** tmux and screen are terminals
(chapter 31), so they parse every OSC their programs send.

- **What recent tmux implements.** That includes titles (with
  `set-titles on`), the colors 4, 10, 11 and 12, OSC 7, OSC 8 and
  OSC 52 (with `set-clipboard on`). It also reads the OSC 133 marks,
  for `next-prompt` and `previous-prompt` in copy mode.
- **What it drops.** It drops everything else: an iTerm2 image or a
  kitty notification sent inside tmux never reaches the outer
  terminal.
- **Passthrough.** To reach the outer terminal, wrap the sequence in
  tmux's own DCS and double every ESC inside it. This needs
  `allow-passthrough on` (tmux 3.3 and later):

```sh
# a notification for the terminal outside tmux
printf '\ePtmux;\e\e]9;build done\a\e\\'
```

(muxi, in 31.2, implements only the titles: its `osc` state swallows
the rest.)

**Shell integration in practice.** A few lines in `~/.zshrc` emit
OSC 7 and OSC 133 from the prompt hooks:

```zsh
# OSC 7 and OSC 133 for zsh: add to ~/.zshrc
autoload -Uz add-zsh-hook
_osc_precmd() {
  local st=$?
  print -n "\e]133;D;$st\e\\"                    # last command ended
  print -n "\e]7;file://$HOST${PWD// /%20}\e\\"  # current directory
  print -n "\e]133;A\e\\"                        # prompt starts
}
_osc_preexec() { print -n "\e]133;C\e\\" }       # output starts
add-zsh-hook precmd _osc_precmd
add-zsh-hook preexec _osc_preexec
PS1='%~ %# '$'%{\e]133;B\e\\%}'                  # input starts
```

`%{...%}` tells zsh that the sequence takes no room on the screen
(7.12). Only spaces are percent-encoded, which is enough for most
paths. The sequences of a session that ran `false`, `cd /etc` and
`exit`, extracted from a `script` log with `cat -v`:

```text
^[]133;D;0
^[]7;file://om/usr/share
^[]133;A
^[]133;B
^[]133;C
^[]133;D;1
^[]7;file://om/usr/share
^[]133;A
^[]133;B
^[]133;C
^[]133;D;0
^[]7;file://om/etc
^[]133;A
^[]133;B
^[]133;C
```

`D;1` is the status of `false`. The first `D;0` comes before any
command; terminals ignore a `D` without a `C`.

A query, from a shell script. Raw mode with `min 0 time 5` makes the
read return after half a second of silence, so a terminal that does
not answer costs half a second:

```sh
#!/bin/sh
# osc11.sh: ask the terminal for its background color (OSC 11).
old=$(stty -g)
stty raw -echo min 0 time 5   # a read returns after 0.5 s of silence
printf '\033]11;?\033\\' > /dev/tty
reply=$(dd bs=100 count=1 2>/dev/null < /dev/tty)
stty "$old"
printf '%s\n' "$reply" | cat -v
```

In a tmux pane with `window-style 'bg=#102030'`:

```console
$ ./osc11.sh
^[]11;rgb:1010/2020/3030^[\
```

The query ended with ST, and so does the answer. Each 8-bit channel
is written as 16 bits, with the byte repeated.

**OSC sequences are a security matter.** Text printed to a terminal
is code for the terminal. A `cat` of an untrusted file, a log line
that contains user input, or a file name with an ESC in it can send
any OSC:

- **Title reporting.** xterm's `CSI 21 t` sends the title back as
  input, as if typed. Combined with `OSC 2`, a file could type a
  command into your shell. This was one of the terminal emulator
  vulnerabilities published in 2003. xterm now disables title
  reporting by default, and most emulators never implemented it.
- **Clipboard.** Reading through OSC 52 would let any program, even
  one on a remote machine, read your clipboard. Most terminals refuse
  to read, and some ask before writing.
- **Hyperlinks.** With OSC 8, the text of a link and its URI can
  differ, as in HTML. Terminals show the URI on hover.
- **Unterminated strings.** A stray `ESC ]` without a terminator
  makes the terminal swallow the following output, up to a BEL, an
  ST or a length limit. muxi's parser has the same state.

The defense is the same as for any injection: do not print untrusted
text raw. `less` shows control characters as `^[` unless told
otherwise (`-r`). GNU `ls` quotes a file name containing ESC as
`$'\033'` when its output is a terminal. `cat -v` makes everything
visible.

---

## 8. Window size, terminfo and terminal capabilities

### 8.1 The window size

The kernel stores, for each terminal, a `struct winsize`:

```c
struct winsize {
    unsigned short ws_row;     /* rows, in characters */
    unsigned short ws_col;     /* columns, in characters */
    unsigned short ws_xpixel;  /* width, in pixels (often 0) */
    unsigned short ws_ypixel;  /* height, in pixels (often 0) */
};
```

- `ioctl(fd, TIOCGWINSZ, &ws)` reads it (on any fd referring to the
  terminal, master or slave). POSIX.1-2024 added `tcgetwinsize()` and
  `tcsetwinsize()` as portable wrappers, available in recent libcs.
- `ioctl(fd, TIOCSWINSZ, &ws)` sets it. If the size changes, the kernel
  sends `SIGWINCH` to the foreground process group.
- The kernel does nothing else with it. It is pure metadata, maintained
  by whoever runs the terminal.

Programs find the size, in order of preference:

1. `TIOCGWINSZ` on the terminal (stdin, stdout, stderr, or `/dev/tty`).
2. The `LINES` and `COLUMNS` environment variables (set by some shells; not
   exported by default in bash, and stale after a resize).
3. terminfo `lines`/`cols` (rarely meaningful).
4. Asking the terminal: move the cursor to 999;999 (`CSI 999;999H`),
   query its position (`CSI 6 n`), restore. Works over a serial line where
   nobody sets `TIOCSWINSZ`. `resize(1)` from xterm does that and then
   sets the kernel value.
5. 80x24 as a last resort.

### 8.2 SIGWINCH handling

`SIGWINCH` is ignored by default, so programs that care must install a
handler. The standard pattern in C:

```c
static volatile sig_atomic_t resized = 1;  /* 1: compute size at start */

static void on_winch(int sig) { (void)sig; resized = 1; }

/* in main: */
struct sigaction sa = { .sa_handler = on_winch };
sigemptyset(&sa.sa_mask);
sigaction(SIGWINCH, &sa, NULL);    /* no SA_RESTART: we want EINTR */

/* in the main loop: */
if (resized) {
    resized = 0;
    struct winsize ws;
    ioctl(STDOUT_FILENO, TIOCGWINSZ, &ws);
    redraw(ws.ws_row, ws.ws_col);
}
```

Installing it *without* `SA_RESTART` makes a blocked `read` or `poll`
return `EINTR` when the window is resized, so the loop can redraw at once.
Even so, there is the race we discussed for the self-pipe trick: if the
signal arrives between the flag check and the call to `poll`, the redraw
waits until the next key. The self-pipe trick or `signalfd` fixes it.
Languages with runtimes deliver `SIGWINCH` as an event: a Raku `Supply`
from `signal(SIGWINCH)`, a channel in Go (`signal.Notify`), a stream in
tokio (`signal(SignalKind::window_change())`), an event in crossterm
(`Event::Resize`), a `tea.WindowSizeMsg` in Bubble Tea.

A newer alternative: mode `?2048` (in-band resize notifications, proposed
by the Contour terminal and implemented in several others). When enabled,
the terminal sends `CSI 48 ; rows ; cols ; ypix ; xpix t` as *input* when
the size changes. This works even over transports that do not forward
`SIGWINCH`, like a serial line.

### 8.3 TERM and terminfo

The `TERM` environment variable names the terminal type: `xterm-256color`,
`tmux-256color`, `screen`, `linux`, `xterm-kitty`, `alacritty`,
`foot`, `xterm-ghostty`, `vt100`, `dumb`. It is set by the terminal
emulator for the shell it starts, and forwarded by `ssh` to the remote
side.

The *terminfo* database maps each name to a set of *capabilities*:

- booleans: `am` (automatic margins), `bce` (background color erase),
  `Tc` or `RGB` (truecolor, extensions);
- numbers: `colors#256`, `cols#80`, `lines#24`;
- strings: `clear=\E[H\E[2J`, `cup=\E[%i%p1%d;%p2%dH` (cursor
  position, with a small stack-based parameter language), `smcup`/`rmcup`
  (enter/exit alternate screen), `smkx`/`rmkx` (keypad mode), `kcuu1`
  (what the Up key sends), `setaf` (set foreground color), `sgr0` (reset
  attributes).

Compiled entries live in `/usr/share/terminfo/x/xterm-256color` (or
`/usr/share/terminfo/78/...` on macOS), and user entries in
`~/.terminfo`. Tools:

```text
$ infocmp -1 xterm-256color | head        # decompile an entry
$ tput cols                                 # query capability
$ tput setaf 1; echo red; tput sgr0        # use capability
$ tput cup 5 10                            # move cursor (0-based!)
$ toe -a | grep kitty                      # list known entries
$ tic -x myterm.info                        # compile an entry
```

When you ssh to a server that does not know your terminal's `TERM`
(`xterm-kitty`, `xterm-ghostty`, `alacritty`), programs there complain
"unknown terminal type" or misbehave. Fixes: install the terminfo entry on
the server (`infocmp -x | ssh host -- tic -x -`), or set `TERM` to a
common value like `xterm-256color` for that connection.

### 8.4 Do you need terminfo today?

Strictly speaking, almost every terminal in use today understands the
xterm subset of escape sequences. Many modern libraries therefore hardcode
the common sequences and use terminfo only for corner cases, or not at
all:

- **ncurses** (C): full terminfo, everything through the database.
- **crossterm** (Rust): hardcodes ANSI sequences; no terminfo.
- **termion** (Rust): hardcoded sequences.
- **Bubble Tea / Lip Gloss** (Go): hardcoded sequences (`charmbracelet/x/
  ansi`), color profile detected from `TERM`, `COLORTERM`, `NO_COLOR`
  and terminfo when available.
- **Terminal::ANSI** (Raku): hardcoded sequences.

The pragmatic approach used in this tutorial: emit the common xterm
sequences, detect color support through `COLORTERM`/`TERM`/`NO_COLOR`, and
treat `TERM=dumb` (Emacs shell buffers, some CI systems) as "no escape
sequences at all".

### 8.5 Detecting capabilities at run time

Beyond static databases, terminals can be queried:

- **Primary DA** (`CSI c`): the terminal's conformance level and features.
- **XTVERSION** (`CSI > 0 q`): name and version of the emulator
  (`DCS > | kitty(0.36.0) ST`).
- **DECRQM** (`CSI ? mode $ p`): is a given mode supported and set?
- **XTGETTCAP** (`DCS + q hex-name ST`): ask the terminal for its own
  terminfo capability values. Works over ssh even when the remote terminfo
  database is out of date.
- **Kitty keyboard query** (`CSI ? u`).

Libraries such as `Terminal::Capabilities` (Raku) and the Charm `x/term`
packages do some of this for you.

### 8.6 The environment around a terminal program

A checklist of environment variables a careful terminal program looks at:

| Variable | Meaning |
|----------|---------|
| `TERM` | terminal type |
| `COLORTERM` | `truecolor`/`24bit` |
| `NO_COLOR` | disable color if set |
| `FORCE_COLOR` | force color |
| `COLUMNS`, `LINES` | size override |
| `LANG`, `LC_ALL`, `LC_CTYPE` | encoding (UTF-8?) |
| `TERM_PROGRAM` | emulator name (some) |
| `TMUX`, `STY` | inside tmux / screen |
| `SSH_TTY` | ssh session with PTY |
| `PAGER`, `LESS` | pager preferences |

### 8.7 Putting Part I together

Before we write code, here is the complete picture of everything that
happens when you run `vim notes.txt` in a terminal, resize the window and
press `^Z`:

1. The shell (in the foreground process group of `/dev/pts/3`) reads your
   line in its own raw mode, restores canonical mode, forks.
2. The child calls `setpgid` to create a new group, the shell calls
   `tcsetpgrp` to give it the terminal, the child execs vim.
3. vim calls `isatty`, `tcgetattr` to save the termios, sets raw mode with
   `tcsetattr(TCSAFLUSH)`, installs handlers for `SIGWINCH`, `SIGTSTP`,
   `SIGCONT`, `SIGHUP`, `SIGTERM`, reads `TERM` and terminfo, reads the
   window size with `TIOCGWINSZ`, sends `smcup` (alternate screen), `smkx`,
   enables bracketed paste and maybe mouse, and draws the screen.
4. You resize the window. The emulator calls `TIOCSWINSZ` on the master;
   the kernel sends `SIGWINCH` to vim's process group; vim's main loop
   wakes up, reads the new size, redraws.
5. You press `^Z`. vim is in raw mode with `ISIG` off, so it reads byte
   `0x1a` itself, recognizes its suspend command, restores the terminal
   (leaves the alternate screen, resets modes, restores the saved termios)
   and sends `SIGTSTP` to itself.
6. The kernel stops vim. The shell, waiting with `WUNTRACED`, is woken
   up, sees that the job stopped, takes the terminal back with
   `tcsetpgrp`, prints `[1]+ Stopped vim notes.txt` and shows a prompt.
7. You type `fg`. The shell gives the terminal back to vim's group and
   sends `SIGCONT`. vim's `SIGCONT` handler re-enters raw mode and the
   alternate screen and redraws.
8. You type `:q`. vim restores the terminal and exits. The shell's
   `waitpid` returns, the shell takes the terminal back, and so on.

Every element of this list appears somewhere in the code that follows.

---

# Part II: Languages

---

## 9. C: the ecosystem

C is the native language of Unix. Every system call has a C prototype, every
man page in section 2 and 3 is written for C, and every other language in
this tutorial ends up calling the same functions through some kind of
foreign function interface. Learning the C version first is the fastest
way to understand what the others do for you.

### 9.1 Compilers and the C library

On Linux you have two compilers:

- **GCC** (`gcc`), the GNU Compiler Collection;
- **Clang** (`clang`), the LLVM front-end. It accepts nearly all of GCC's
  options and often gives better diagnostics.

`cc` is usually a link to one of them. Both compile C, but the functions
you call (`open`, `printf`, `tcsetattr`, `forkpty`) come from the **C
library**, which is separate:

- **glibc** (GNU C Library): the standard on most Linux distributions.
- **musl**: small, strict, used by Alpine Linux and for static binaries.
- On the BSDs and macOS, the system libc.

Most of what we do is POSIX and works with any of them. Some functions are
BSD extensions (`openpty`, `forkpty`, `login_tty`, `cfmakeraw`), available
in glibc and musl, and on the BSDs, but declared in different headers:

| Function | glibc/musl | BSD | macOS |
|----------|-----------|-----|-------|
| `openpty` | `<pty.h>` | `<libutil.h>`* | `<util.h>` |
| `forkpty` | `<pty.h>` | `<libutil.h>`* | `<util.h>` |
| `login_tty` | `<utmp.h>` | `<libutil.h>`* | `<util.h>` |

\* `<util.h>` on OpenBSD and NetBSD, `<libutil.h>` on FreeBSD.

With glibc older than 2.34, these functions live in `libutil` and you must
link with `-lutil`. Since glibc 2.34 they are in libc itself, but
`-lutil` still works (the library exists as an empty stub). For
portability, keep `-lutil` in your build commands when you use them.

### 9.2 Feature test macros

glibc hides functions that are not in the standard you ask for. If you
compile with `-std=c11` (strict ISO C), even `fileno` and `fdopen` are not
declared. Define a *feature test macro* at the very top of the file,
before any `#include`:

- `#define _POSIX_C_SOURCE 200809L`: POSIX.1-2008 functions.
- `#define _XOPEN_SOURCE 700`: POSIX + XSI extensions (includes
  `posix_openpt`, `grantpt`, `ptsname`).
- `#define _DEFAULT_SOURCE`: BSD and SVID extensions (`cfmakeraw`).
- `#define _GNU_SOURCE`: everything, including GNU extensions
  (`pipe2`, `ptsname_r`, `F_SETPIPE_SZ`).

With `-std=gnu11` or `-std=gnu17` (GCC's default), most of these are
visible anyway, but defining the macro documents what you depend on. The
examples in this tutorial each define the macro they need and compile with
`-std=c17` or the default.

### 9.3 Compiling and running

A single file:

```text
$ cc -std=c17 -Wall -Wextra -O2 -g -o fdinfo c/fdinfo.c
$ ./fdinfo
```

- `-Wall -Wextra`: warnings. Always use them. Add `-Werror` in CI.
- `-O2`: optimize. `-O0` (the default) for debugging.
- `-g`: debug information, for `gdb` and readable crash backtraces.
- `-o name`: output file name (default `a.out`).
- `-lutil`: link with libutil (for `forkpty` on older systems).
- `-fsanitize=address,undefined`: AddressSanitizer and UBSan, which find
  memory errors at run time. Use them during development.

Running it is just `./name`. To see the system calls it makes, use
`strace ./name`. To debug, `gdb ./name`.

### 9.4 Build systems

For one-file programs, a compile command is enough. Beyond that:

- **make**: the classic. A minimal `Makefile` for the C examples:

  ```make
  # file: c/Makefile
  CC      ?= cc
  CFLAGS  ?= -std=c17 -Wall -Wextra -O2 -g
  LDLIBS  ?= -lutil

  PROGS = fdinfo ids pipe_capacity pipe_basic pipeline popen_demo \
          bidir rawkeys getpass_demo winsize ptyspawn ptyscript \
          ptyexpect minishell ttylog

  all: $(PROGS)

  # These three share pty_spawn from ptyopen.c (chapter 12).
  ptyscript ptyexpect ttylog: ptyopen.o
  ptyopen.o ptyscript ptyexpect ttylog: ptyopen.h

  clean:
  	rm -f $(PROGS) *.o

  .PHONY: all clean
  ```

  Make's built-in rules know how to build `foo` from `foo.c` using
  `$(CC) $(CFLAGS) foo.c -o foo $(LDLIBS)`, so you do not need to write
  one rule per program. The built-in rule links all the prerequisites
  (`$^`), so the line `ptyscript ...: ptyopen.o` is enough to compile
  `ptyopen.c` once and link it into the three programs that use it.
  Note that recipe lines must start with a tab.

- **CMake**: generates Makefiles or Ninja files, standard for larger C and
  C++ projects. `cmake -B build && cmake --build build`.
- **Meson**: a faster, more modern alternative, used by GNOME, systemd and
  many others. `meson setup build && meson compile -C build`.
- **pkg-config**: tells you the compiler flags for a library:
  `cc $(pkg-config --cflags --libs ncursesw) app.c`.

### 9.5 Libraries for terminals

The C world for terminal work:

- **libc**: everything in this tutorial except TUI drawing: `termios`,
  `openpty`, `poll`, `ioctl`.
- **ncurses**: the reference implementation of curses, with terminfo.
  Provides windows, panels, menus, forms, color pairs, input decoding
  (`keypad`). Link with `-lncursesw` (the `w` is the wide-character, UTF-8
  aware version; always use it). Very portable, a bit dated in API style.
- **GNU Readline** (`-lreadline`): line editing with history and
  completion, used by bash, gdb, Python's REPL. GPL. **libedit**
  (`-ledit`, BSD license) is an alternative with a Readline compatibility
  layer. **linenoise** and **replxx** are tiny embeddable alternatives.
- **notcurses**: a modern TUI library with true color, images and
  multimedia; heavy but impressive.
- **termbox2**: a single-header minimal library, a good choice when
  ncurses is too much.
- **libvterm**: a terminal emulator library (parses escape sequences into a
  screen model). Used by neovim's `:terminal` and others.
- **libuv** and **libevent**: event loops, which wrap `epoll`/`kqueue`, and
  include TTY and process abstractions. libuv is what MoarVM, the Raku
  virtual machine, uses.

### 9.6 Documentation

The man pages are the documentation. Install the `man-pages` package (on
Arch: `man-pages`; on Debian: `manpages-dev` and `manpages-posix-dev`).
The sections that matter:

- section 2: system calls (`man 2 pipe`, `man 2 ioctl`, `man 2 setsid`);
- section 3: library functions (`man 3 termios`, `man 3 openpty`,
  `man 3 posix_openpt`);
- section 4: devices (`man 4 tty`, `man 4 pts`, `man 4 console_codes`
  for the Linux console's escape sequences);
- section 7: overviews (`man 7 pipe`, `man 7 pty`, `man 7 signal`,
  `man 7 credentials` for sessions and groups);
- `man 2const TIOCSWINSZ` and `man 2 ioctl_tty` (older systems:
  `man 4 tty_ioctl`) for terminal ioctls;
- POSIX versions: `man 3p tcsetattr` (from the `man-pages-posix`
  package) for the portable specification.

Other references: *The Linux Programming Interface* by Michael Kerrisk
(chapters 44 on pipes, 34 on process groups and sessions, 62 on terminals
and 64 on pseudo-terminals are the best written explanation of all this),
*Advanced Programming in the UNIX Environment* by Stevens and Rago, and
the xterm control sequences document (`ctlseqs`).

### 9.7 Error handling conventions

System calls return -1 (or `NULL`) and set `errno` on error. A few rules
used in all the C code here:

- Check every return value. Use `perror("name")` or
  `fprintf(stderr, "...: %s\n", strerror(errno))` to report.
- `EINTR`: a blocking call was interrupted by a signal handler. Retry,
  unless you installed the handler precisely to interrupt the call.
- `EAGAIN`: a non-blocking call would block. Wait with `poll` and retry.
- After `fork()`, in the child, use `_exit()` rather than `exit()` if
  `exec` fails, so that stdio buffers inherited from the parent are not
  flushed twice and `atexit` handlers do not run in the child.
- `write` can write less than requested (on pipes, terminals, sockets).
  Loop until everything is written.

Two helpers used throughout the C chapters:

```c
/* Write all of buf, retrying on partial writes and EINTR. */
static int write_all(int fd, const void *buf, size_t len)
{
    const char *p = buf;
    while (len > 0) {
        ssize_t n = write(fd, p, len);
        if (n == -1) {
            if (errno == EINTR) continue;
            return -1;
        }
        p += n;
        len -= (size_t)n;
    }
    return 0;
}

/* Die with a message including errno. */
static void die(const char *what)
{
    perror(what);
    exit(1);
}
```

They are repeated in each listing so that every file compiles on its own.

---

## 10. C: pipes, fork and exec

### 10.1 A pipe between parent and child

The simplest useful program: the parent sends a message to the child
through a pipe.

```c
// file: c/pipe_basic.c
#define _DEFAULT_SOURCE
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/wait.h>
#include <unistd.h>

static void die(const char *what) { perror(what); exit(1); }

int main(void)
{
    int p[2];
    if (pipe(p) == -1) die("pipe");

    pid_t pid = fork();
    if (pid == -1) die("fork");

    if (pid == 0) {                       /* child: reader */
        close(p[1]);                      /* not writing */
        char buf[128];
        ssize_t n;
        while ((n = read(p[0], buf, sizeof buf)) > 0) {
            printf("child got %zd bytes: %.*s", n, (int)n, buf);
            fflush(stdout);
        }
        if (n == -1) die("read");
        printf("child: EOF\n");
        fflush(stdout);                   /* _exit does not flush stdio */
        close(p[0]);
        _exit(0);
    }

    /* parent: writer */
    close(p[0]);                          /* not reading */
    const char *msgs[] = { "hello\n", "from\n", "the parent\n" };
    for (size_t i = 0; i < 3; i++) {
        if (write(p[1], msgs[i], strlen(msgs[i])) == -1) die("write");
        usleep(100 * 1000);               /* 100 ms between messages */
    }
    close(p[1]);                          /* child sees EOF */

    int status;
    if (waitpid(pid, &status, 0) == -1) die("waitpid");
    printf("parent: child exited with %d\n", WEXITSTATUS(status));
    return 0;
}
```

```text
$ cc -Wall -o pipe_basic c/pipe_basic.c && ./pipe_basic
child got 6 bytes: hello
child got 5 bytes: from
child got 11 bytes: the parent
child: EOF
parent: child exited with 0
```

The last two lines always come in this order, because the parent prints
only after `waitpid` returns. Without the `usleep`, the three messages
might arrive in a single `read` of 22 bytes, because pipes do not preserve
message boundaries. Try removing it.

Things to observe:

- Both processes close the end they do not use.
- The child uses `_exit`, not `exit` or `return`, after `fork`.
- The child calls `fflush(stdout)` because its stdout may be a pipe (if you
  run `./pipe_basic | cat`), in which case it would be fully buffered and
  the order of lines between parent and child would change. Try
  `./pipe_basic | cat` with and without the `fflush`.

### 10.2 Running a pipeline: `ls -l /usr/bin | grep zip | wc -l`

Now a generic pipeline runner: it takes commands separated by `|` on its
command line (quoted so that the shell does not interpret them) and runs
them connected by pipes, as a shell would.

```c
// file: c/pipeline.c
#define _POSIX_C_SOURCE 200809L
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/wait.h>
#include <unistd.h>

#define MAXCMDS 16

static void die(const char *what) { perror(what); exit(1); }

/*
 * argv layout: pipeline cmd1 args... '|' cmd2 args... '|' cmd3 ...
 * We split argv in place by replacing each "|" with NULL.
 */
int main(int argc, char **argv)
{
    char **cmds[MAXCMDS];
    int ncmds = 0;

    if (argc < 2) {
        fprintf(stderr, "usage: %s cmd [args] '|' cmd [args] ...\n", argv[0]);
        return 2;
    }
    cmds[ncmds++] = &argv[1];
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "|") == 0) {
            argv[i] = NULL;
            if (ncmds == MAXCMDS) { fprintf(stderr, "too many\n"); return 2; }
            cmds[ncmds++] = &argv[i + 1];
        }
    }

    pid_t pids[MAXCMDS];
    int prev_read = -1;               /* read end of the previous pipe */

    for (int i = 0; i < ncmds; i++) {
        int p[2] = { -1, -1 };
        if (i < ncmds - 1 && pipe(p) == -1) die("pipe");

        pid_t pid = fork();
        if (pid == -1) die("fork");
        if (pid == 0) {
            if (prev_read != -1) {            /* stdin from previous */
                dup2(prev_read, STDIN_FILENO);
                close(prev_read);
            }
            if (p[1] != -1) {                 /* stdout to next */
                dup2(p[1], STDOUT_FILENO);
                close(p[1]);
                close(p[0]);
            }
            execvp(cmds[i][0], cmds[i]);
            fprintf(stderr, "exec %s: %s\n", cmds[i][0], strerror(errno));
            _exit(127);
        }
        pids[i] = pid;

        /* parent: close what we no longer need */
        if (prev_read != -1) close(prev_read);
        if (p[1] != -1) close(p[1]);
        prev_read = p[0];
    }

    int last_status = 0;
    for (int i = 0; i < ncmds; i++) {
        int status;
        if (waitpid(pids[i], &status, 0) == -1) die("waitpid");
        if (WIFEXITED(status))
            last_status = WEXITSTATUS(status);
        else if (WIFSIGNALED(status))
            last_status = 128 + WTERMSIG(status);
        fprintf(stderr, "[%s: %s %d]\n", cmds[i][0],
                WIFEXITED(status) ? "exit" : "signal",
                WIFEXITED(status) ? WEXITSTATUS(status) : WTERMSIG(status));
    }
    return last_status;
}
```

```text
$ cc -Wall -o pipeline c/pipeline.c
$ ./pipeline ls /usr/bin '|' grep zip '|' wc -l
12
[ls: exit 0]
[grep: exit 0]
[wc: exit 0]
$ ./pipeline yes '|' head -n 2
y
y
[yes: signal 13]
[head: exit 0]
```

The second run shows `SIGPIPE` (signal 13) killing `yes`. The pipeline's
status is the last command's, as in a shell without `pipefail`.

The fd bookkeeping is the heart of it. At each iteration, the parent holds
at most one fd: the read end of the previous pipe, which it hands to the
next child and then closes. If you forget `close(p[1])` in the parent,
`wc` never terminates. Try it, and look at the hung process with
`ls -l /proc/$(pgrep -n wc)/fd` from another terminal and
`ls -l /proc/$(pgrep -n pipeline)/fd`: you will see the parent holding the
pipe's write end.

### 10.3 popen and pclose

The C library has a high-level shortcut for "run a command and read its
output" (or "write its input"):

```c
// file: c/popen_demo.c
#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <sys/wait.h>

int main(void)
{
    FILE *f = popen("ls /usr/bin | head -n 5", "r");
    if (!f) { perror("popen"); return 1; }

    char line[256];
    int n = 0;
    while (fgets(line, sizeof line, f))
        printf("%2d: %s", ++n, line);

    int status = pclose(f);
    if (status == -1) { perror("pclose"); return 1; }
    printf("exit status: %d\n", WEXITSTATUS(status));

    FILE *w = popen("tr a-z A-Z", "w");
    if (!w) { perror("popen"); return 1; }
    fputs("this goes to tr's stdin\n", w);
    pclose(w);
    return 0;
}
```

`popen` runs the command through `/bin/sh -c`, so it supports shell
syntax, and also means you must never pass untrusted strings to it
(shell injection). It is one-directional: `"r"` or `"w"`, not both.
`pclose` waits for the command and returns its status in `waitpid` format.

Run it as `./popen_demo | cat` and the uppercase line from `tr` comes out
*first*. Our own `printf` output sits in a fully buffered `stdout` (it is
a pipe now) until exit, while `tr` writes directly to the shared pipe.
Mixing output from a parent and its children on the same pipe is
another place where you need to flush (`fflush(stdout)` before `popen`).

Under the hood, glibc implements `popen` with `posix_spawn` (or `vfork`
and `exec`), a pipe, and `fdopen`.

### 10.4 posix_spawn

`fork` + `exec` copies (lazily, copy-on-write) the whole address space of
the parent, which is fast but not free for large processes, and dangerous
in multithreaded programs (only the calling thread exists in the child, and
locks held by other threads stay locked). `posix_spawn` combines both
steps, with a list of *file actions* (open, close, dup2) and *attributes*
(process group, signal mask, signal defaults, new session on recent
glibc):

```c
#include <spawn.h>
extern char **environ;

posix_spawn_file_actions_t fa;
posix_spawn_file_actions_init(&fa);
posix_spawn_file_actions_adddup2(&fa, p[1], STDOUT_FILENO);
posix_spawn_file_actions_addclose(&fa, p[0]);
posix_spawn_file_actions_addclose(&fa, p[1]);

posix_spawnattr_t at;
posix_spawnattr_init(&at);
sigset_t def; sigemptyset(&def); sigaddset(&def, SIGPIPE);
posix_spawnattr_setsigdefault(&at, &def);
posix_spawnattr_setflags(&at, POSIX_SPAWN_SETSIGDEF);

pid_t pid;
char *args[] = { "ls", "-l", NULL };
int err = posix_spawnp(&pid, "ls", &fa, &at, args, environ);
/* err is an errno value, not -1 */
```

On Linux, glibc implements `posix_spawn` with `clone(CLONE_VM |
CLONE_VFORK)`, which avoids copying page tables. Rust's `Command` and Go's
`os/exec` use `posix_spawn` or an equivalent `clone`-based fast path when
they can.

### 10.5 Two-way communication without deadlock

To both feed input to a child and read its output, use two pipes and
`poll`. This program sends a large input (one million lines) through
`sort -n` (which reads everything before writing anything) and then
`tr` (which writes as it reads), and prints statistics. With
sequential I/O it would deadlock with `tr`; with `poll` it works with
both.

```c
// file: c/bidir.c
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <poll.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/wait.h>
#include <unistd.h>

static void die(const char *what) { perror(what); exit(1); }

/* Start argv with stdin and stdout connected to new pipes. */
static pid_t spawn2(char **argv, int *to_child, int *from_child)
{
    int in[2], out[2];
    if (pipe2(in, O_CLOEXEC) == -1 || pipe2(out, O_CLOEXEC) == -1)
        die("pipe2");
    pid_t pid = fork();
    if (pid == -1) die("fork");
    if (pid == 0) {
        /* dup2 clears FD_CLOEXEC on the new fd, so 0 and 1 survive exec */
        dup2(in[0], STDIN_FILENO);
        dup2(out[1], STDOUT_FILENO);
        signal(SIGPIPE, SIG_DFL);
        execvp(argv[0], argv);
        _exit(127);
    }
    close(in[0]);
    close(out[1]);
    *to_child = in[1];
    *from_child = out[0];
    return pid;
}

int main(int argc, char **argv)
{
    char *dflt[] = { "tr", "0-9", "a-j", NULL };
    char **cmd = argc > 1 ? &argv[1] : dflt;

    signal(SIGPIPE, SIG_IGN);     /* get EPIPE instead of dying */

    int to, from;
    pid_t pid = spawn2(cmd, &to, &from);
    fcntl(to, F_SETFL, O_NONBLOCK);

    /* Prepare 1,000,000 lines of input: about 6.9 MB. */
    size_t cap = 8 << 20, len = 0;
    char *input = malloc(cap);
    if (!input) die("malloc");
    for (int i = 1000000; i > 0; i--)
        len += (size_t)sprintf(input + len, "%d\n", i);

    size_t sent = 0, received = 0, lines = 0;
    char buf[65536];
    struct pollfd pf[2] = {
        { .fd = to,   .events = POLLOUT },
        { .fd = from, .events = POLLIN  },
    };

    while (pf[0].fd != -1 || pf[1].fd != -1) {
        if (poll(pf, 2, -1) == -1) {
            if (errno == EINTR) continue;
            die("poll");
        }
        if (pf[0].fd != -1 && (pf[0].revents & (POLLOUT | POLLERR))) {
            ssize_t n = write(to, input + sent, len - sent);
            if (n > 0) sent += (size_t)n;
            else if (n == -1 && errno != EAGAIN) {
                fprintf(stderr, "write: %s\n", strerror(errno));
                sent = len;                  /* give up on input */
            }
            if (sent == len) { close(to); pf[0].fd = -1; }
        }
        if (pf[1].fd != -1 && (pf[1].revents & (POLLIN | POLLHUP))) {
            ssize_t n = read(from, buf, sizeof buf);
            if (n > 0) {
                received += (size_t)n;
                for (ssize_t i = 0; i < n; i++) lines += buf[i] == '\n';
            } else if (n == 0) {
                close(from); pf[1].fd = -1;   /* EOF */
            } else if (errno != EINTR) die("read");
        }
    }

    int status;
    waitpid(pid, &status, 0);
    printf("sent %zu bytes, received %zu bytes in %zu lines, status %d\n",
           sent, received, lines, WEXITSTATUS(status));
    free(input);
    return 0;
}
```

```text
$ cc -Wall -O2 -o bidir c/bidir.c
$ ./bidir
sent 6888896 bytes, received 6888896 bytes in 1000000 lines, status 0
$ ./bidir sort -n
sent 6888896 bytes, received 6888896 bytes in 1000000 lines, status 0
```

Points to note:

- `pipe2(..., O_CLOEXEC)`: the pipe fds do not leak into the child beyond
  what `dup2` puts on 0 and 1 (`dup2` creates the new fd *without*
  `FD_CLOEXEC`).
- The write end is non-blocking, so a `write` never blocks the loop; we
  write as much as fits each time `poll` says there is room.
- Setting a negative fd in a `pollfd` makes `poll` ignore that entry,
  which is a tidy way to retire a direction.
- We ignore `SIGPIPE` in the parent so that a child that exits early
  produces `EPIPE` rather than killing us, and we restore the default in the
  child before `exec`.
- `POLLHUP` on the read end comes with the remaining data: we keep reading
  until `read` returns 0.

### 10.6 A FIFO server

Two programs communicating through a named pipe. The server creates the
FIFO and prints every line it receives; clients are just `echo ... >
fifo`.

```c
// file: c/fifo_server.c
#define _POSIX_C_SOURCE 200809L
#include <errno.h>
#include <fcntl.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>

static const char *path;
static void cleanup(int sig) { unlink(path); _exit(128 + sig); }

int main(int argc, char **argv)
{
    path = argc > 1 ? argv[1] : "/tmp/demo.fifo";
    if (mkfifo(path, 0600) == -1 && errno != EEXIST) {
        perror("mkfifo");
        return 1;
    }
    signal(SIGINT, cleanup);
    signal(SIGTERM, cleanup);

    /* O_RDWR: we are also a writer, so we never see EOF between clients.
       This is Linux behavior; POSIX leaves O_RDWR on a FIFO undefined. */
    int fd = open(path, O_RDWR);
    if (fd == -1) { perror("open"); return 1; }
    FILE *f = fdopen(fd, "r");

    printf("listening on %s (Ctrl+C to stop)\n", path);
    char line[4096];
    unsigned long n = 0;
    while (fgets(line, sizeof line, f)) {
        printf("%5lu: %s", ++n, line);
        fflush(stdout);
    }
    return 0;
}
```

```text
$ ./fifo_server &
listening on /tmp/demo.fifo (Ctrl+C to stop)
$ echo hello > /tmp/demo.fifo
    1: hello
$ seq 3 > /tmp/demo.fifo
    2: 1
    3: 2
    4: 3
```

If you replace `O_RDWR` with `O_RDONLY`, the server stops after the first
client: `fgets` sees EOF when `echo` closes its end.

### 10.7 Reading a child's stdout and stderr separately

A last pipe pattern: capture stdout and stderr of a child separately
without deadlock. It is `bidir.c` with two read ends and no write end, so
here is only the loop, as an exercise to complete (see Appendix E):

```c
struct pollfd pf[2] = {
    { .fd = out_fd, .events = POLLIN },
    { .fd = err_fd, .events = POLLIN },
};
int open_count = 2;
while (open_count > 0) {
    poll(pf, 2, -1);
    for (int i = 0; i < 2; i++) {
        if (pf[i].fd == -1 || !(pf[i].revents & (POLLIN | POLLHUP)))
            continue;
        ssize_t n = read(pf[i].fd, buf, sizeof buf);
        if (n <= 0) { close(pf[i].fd); pf[i].fd = -1; open_count--; }
        else append(i == 0 ? &out : &err, buf, n);
    }
}
```

---

## 11. C: termios and raw mode

### 11.1 Reading a password without echo

The first termios program everyone writes: turn off echo, read a line,
turn echo back on. Note that it reads from and writes to `/dev/tty`, not
stdin/stdout, so it works even when the program is used in a pipeline
(`./getpass_demo | sha256sum`).

```c
// file: c/getpass_demo.c
#define _POSIX_C_SOURCE 200809L
#include <fcntl.h>
#include <signal.h>
#include <stdio.h>
#include <string.h>
#include <termios.h>
#include <unistd.h>

static int tty_fd = -1;
static struct termios saved;
static volatile sig_atomic_t restored = 1;

static void restore(void)
{
    if (!restored) {
        tcsetattr(tty_fd, TCSAFLUSH, &saved);
        restored = 1;
    }
}

static void on_signal(int sig)
{
    restore();                       /* tcsetattr is async-signal-safe */
    signal(sig, SIG_DFL);
    raise(sig);                      /* die from the same signal */
}

/* Read a line from the terminal with echo off. Returns length or -1. */
static ssize_t read_secret(const char *prompt, char *buf, size_t size)
{
    tty_fd = open("/dev/tty", O_RDWR | O_NOCTTY);
    if (tty_fd == -1) return -1;

    if (tcgetattr(tty_fd, &saved) == -1) return -1;
    struct termios t = saved;
    t.c_lflag &= ~(tcflag_t)(ECHO | ECHOE | ECHOK);
    t.c_lflag |= ECHONL;             /* still echo the final newline */

    signal(SIGINT, on_signal);
    signal(SIGTERM, on_signal);
    signal(SIGHUP, on_signal);
    signal(SIGQUIT, on_signal);

    restored = 0;
    if (tcsetattr(tty_fd, TCSAFLUSH, &t) == -1) return -1;

    (void)write(tty_fd, prompt, strlen(prompt));
    ssize_t n = read(tty_fd, buf, size - 1);
    restore();
    close(tty_fd);

    if (n <= 0) return -1;
    if (buf[n - 1] == '\n') n--;
    buf[n] = '\0';
    return n;
}

int main(void)
{
    char pw[256];
    ssize_t n = read_secret("Password: ", pw, sizeof pw);
    if (n < 0) { fprintf(stderr, "no password read\n"); return 1; }
    printf("you typed %zd characters\n", n);
    memset(pw, 0, sizeof pw);         /* (see explicit_bzero) */
    return 0;
}
```

Details:

- `ECHONL` echoes the newline even with `ECHO` off, so the cursor moves to
  the next line when the user presses Enter, as with `sudo`.
- `TCSAFLUSH` discards anything typed before the prompt (type-ahead), so
  that a password cannot be "pre-typed" accidentally.
- We restore the terminal from the signal handler and then re-raise the
  signal so that the exit status is correct (the shell sees "killed by
  SIGINT", which matters for scripts: bash stops a loop when a child dies
  of SIGINT).
- The obsolete `getpass(3)` does all this but is deprecated by POSIX;
  `readpassphrase(3)` (BSD, libbsd on Linux) is the modern equivalent.
- A real implementation would also loop on `read` to handle a line split
  across reads (not possible in canonical mode, but possible if `ICANON`
  were off) and handle `EINTR`.

### 11.2 Raw mode and decoding keys

Now the core of every TUI: enter raw mode, read bytes, decode them into
keys. This program prints what each key sends, in hex and as a decoded
name, until you press `q`. It handles `^Z` and resize, and restores
the terminal on every exit path.

```c
// file: c/rawkeys.c
#define _DEFAULT_SOURCE
#include <errno.h>
#include <poll.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <termios.h>
#include <unistd.h>

static struct termios orig;
static int raw_on = 0;

static void raw_disable(void)
{
    if (raw_on) {
        /* bracketed paste off, show cursor */
        (void)!write(STDOUT_FILENO, "\x1b[?2004l\x1b[?25h", 14);
        tcsetattr(STDIN_FILENO, TCSAFLUSH, &orig);
        raw_on = 0;
    }
}

static void raw_enable(void)
{
    struct termios t = orig;
    /* Equivalent to cfmakeraw(&t), spelled out: */
    t.c_iflag &= ~(tcflag_t)(IGNBRK | BRKINT | PARMRK | ISTRIP
                             | INLCR | IGNCR | ICRNL | IXON);
    t.c_oflag &= ~(tcflag_t)OPOST;
    t.c_lflag &= ~(tcflag_t)(ECHO | ECHONL | ICANON | ISIG | IEXTEN);
    t.c_cflag &= ~(tcflag_t)(CSIZE | PARENB);
    t.c_cflag |= CS8;
    t.c_cc[VMIN] = 1;
    t.c_cc[VTIME] = 0;
    tcsetattr(STDIN_FILENO, TCSAFLUSH, &t);
    raw_on = 1;
    (void)!write(STDOUT_FILENO, "\x1b[?2004h", 8);   /* bracketed paste */
}

static volatile sig_atomic_t got_winch = 0, got_cont = 0;

static void on_winch(int s) { (void)s; got_winch = 1; }
static void on_cont(int s)  { (void)s; got_cont = 1; }

static void on_fatal(int sig)
{
    raw_disable();
    signal(sig, SIG_DFL);
    raise(sig);
}

static void suspend_self(void)
{
    raw_disable();
    /* default action of SIGTSTP stops the process; we resume after it */
    signal(SIGTSTP, SIG_DFL);
    raise(SIGTSTP);
    /* ...stopped here until fg/SIGCONT... */
}

/* Printf that ends lines with \r\n, since OPOST is off. */
static void out(const char *fmt, ...) __attribute__((format(printf, 1, 2)));
#include <stdarg.h>
static void out(const char *fmt, ...)
{
    char buf[512];
    va_list ap;
    va_start(ap, fmt);
    int n = vsnprintf(buf, sizeof buf - 2, fmt, ap);
    va_end(ap);
    if (n < 0) return;
    if ((size_t)n > sizeof buf - 3) n = (int)sizeof buf - 3;
    buf[n++] = '\r';
    buf[n++] = '\n';
    (void)!write(STDOUT_FILENO, buf, (size_t)n);
}

static const char *csi_name(char final, int p1)
{
    switch (final) {
    case 'A': return "Up";    case 'B': return "Down";
    case 'C': return "Right"; case 'D': return "Left";
    case 'H': return "Home";  case 'F': return "End";
    case 'Z': return "Shift+Tab";
    case 'P': return "F1";    case 'Q': return "F2";
    case 'R': return "F3";    case 'S': return "F4";
    case '~':
        switch (p1) {
        case 2: return "Insert"; case 3: return "Delete";
        case 5: return "PageUp"; case 6: return "PageDown";
        case 15: return "F5"; case 17: return "F6"; case 18: return "F7";
        case 19: return "F8"; case 20: return "F9"; case 21: return "F10";
        case 23: return "F11"; case 24: return "F12";
        case 200: return "PasteStart"; case 201: return "PasteEnd";
        }
    }
    return "?";
}

static const char *mod_name(int m)
{
    static const char *names[] = {
        "", "", "Shift+", "Alt+", "Shift+Alt+", "Ctrl+", "Ctrl+Shift+",
        "Ctrl+Alt+", "Ctrl+Shift+Alt+",
    };
    return (m >= 0 && m <= 8) ? names[m] : "Mod?+";
}

/* Decode one key starting at buf[0]; returns number of bytes used. */
static size_t decode(const unsigned char *b, size_t n)
{
    if (b[0] == 0x1b) {
        if (n == 1) { out("Escape"); return 1; }
        if (b[1] == '[' || b[1] == 'O') {
            /* CSI or SS3: parameters then a final byte in 0x40..0x7e */
            size_t i = 2;
            int params[4] = { 0 }, np = 0;
            while (i < n && ((b[i] >= '0' && b[i] <= '9') || b[i] == ';')) {
                if (b[i] == ';') { if (np < 3) np++; }
                else params[np] = params[np] * 10 + (b[i] - '0');
                i++;
            }
            if (i >= n) { out("incomplete sequence"); return n; }
            char final = (char)b[i];
            int mod = np >= 1 ? params[1] : 0;
            out("%s%s", mod_name(mod), csi_name(final, params[0]));
            return i + 1;
        }
        out("Alt+%c", b[1]);
        return 2;
    }
    if (b[0] == '\r') { out("Enter"); return 1; }
    if (b[0] == '\t') { out("Tab"); return 1; }
    if (b[0] == 0x7f) { out("Backspace"); return 1; }
    if (b[0] < 0x20) { out("Ctrl+%c", b[0] + '@'); return 1; }
    /* A UTF-8 character: work out its length from the lead byte. */
    size_t len = b[0] < 0x80 ? 1 : b[0] < 0xe0 ? 2 : b[0] < 0xf0 ? 3 : 4;
    if (len > n) len = n;
    out("char '%.*s'", (int)len, (const char *)b);
    return len;
}

int main(void)
{
    if (!isatty(STDIN_FILENO)) {
        fprintf(stderr, "stdin is not a terminal\n");
        return 1;
    }
    tcgetattr(STDIN_FILENO, &orig);
    atexit(raw_disable);

    struct sigaction sa = { 0 };
    sigemptyset(&sa.sa_mask);
    sa.sa_handler = on_winch; sigaction(SIGWINCH, &sa, NULL);
    sa.sa_handler = on_cont;  sigaction(SIGCONT, &sa, NULL);
    sa.sa_handler = on_fatal;
    sigaction(SIGTERM, &sa, NULL);
    sigaction(SIGHUP, &sa, NULL);

    raw_enable();
    out("Press keys (q to quit, Ctrl+Z to suspend).");

    unsigned char buf[256];
    for (;;) {
        if (got_winch) {
            got_winch = 0;
            struct winsize ws;
            if (ioctl(STDOUT_FILENO, TIOCGWINSZ, &ws) == 0)
                out("resize: %d rows x %d cols", ws.ws_row, ws.ws_col);
        }
        if (got_cont) {
            got_cont = 0;
            raw_enable();
            out("resumed");
        }

        struct pollfd pfd = { .fd = STDIN_FILENO, .events = POLLIN };
        if (poll(&pfd, 1, -1) == -1) {
            if (errno == EINTR) continue;   /* a signal: loop to handle */
            break;
        }
        ssize_t n = read(STDIN_FILENO, buf, sizeof buf);
        if (n <= 0) break;

        char hex[3 * sizeof buf + 1] = "";
        for (ssize_t i = 0; i < n; i++)
            sprintf(hex + 3 * i, "%02x ", buf[i]);
        out("bytes: %s", hex);

        if (n == 1 && buf[0] == 'q') break;
        if (n == 1 && buf[0] == 0x1a) { suspend_self(); continue; }
        if (n == 1 && buf[0] == 0x03) { out("(Ctrl+C: use q to quit)"); }

        size_t off = 0;
        while (off < (size_t)n)
            off += decode(buf + off, (size_t)n - off);
    }
    return 0;          /* atexit restores the terminal */
}
```

```text
$ cc -Wall -Wextra -o rawkeys c/rawkeys.c && ./rawkeys
Press keys (q to quit, Ctrl+Z to suspend).
bytes: 61
char 'a'
bytes: 1b 5b 41
Up
bytes: 1b 5b 31 3b 35 43
Ctrl+Right
bytes: c3 a9
char 'é'
bytes: 1b
Escape
bytes: 1b 5b 32 30 30 7e 68 65 6c 6c 6f 1b 5b 32 30 31 7e
PasteStart
char 'h'
char 'e'
char 'l'
char 'l'
char 'o'
PasteEnd
resize: 40 rows x 120 cols
```

What this program demonstrates:

- **One `read` may contain several keys**, as in the paste, or a part of
  a key. The decoder loops over the buffer. A production decoder also
  keeps incomplete sequences for the next read, with an ESC timeout.
- **`OPOST` off** means we must write `\r\n`. The `out` helper does it.
  Try replacing `\r\n` with `\n` to see the staircase.
- **Suspend**: with `ISIG` off, `^Z` arrives as byte `0x1a`. We restore
  the terminal and stop ourselves with `SIGTSTP`'s default action. When
  the shell sends `SIGCONT` (after `fg`), the handler sets a flag, `poll`
  returns `EINTR`, and we re-enter raw mode.
- **Signals and poll**: `sigaction` without `SA_RESTART` lets `poll` return
  `EINTR`, so the loop notices `SIGWINCH` at once. There is still a tiny
  race (signal between the flag check and `poll`); chapter 12 uses the
  self-pipe trick to remove it.
- **atexit**: `raw_disable` runs on `exit()` and on return from `main`.
  It does not run on `_exit()`, on crashes or on uncaught signals. For
  `SIGTERM` and `SIGHUP`, we restore explicitly; for `SIGSEGV` you would
  need to do the same (it is async-signal-safe to call `tcsetattr`).

### 11.3 The window size

```c
// file: c/winsize.c
#define _DEFAULT_SOURCE
#include <signal.h>
#include <stdio.h>
#include <sys/ioctl.h>
#include <unistd.h>

static volatile sig_atomic_t changed = 1;
static void on_winch(int s) { (void)s; changed = 1; }

int main(void)
{
    struct sigaction sa = { .sa_handler = on_winch };
    sigemptyset(&sa.sa_mask);
    sigaction(SIGWINCH, &sa, NULL);

    printf("Resize the window; Ctrl+C to quit.\n");
    for (;;) {
        if (changed) {
            changed = 0;
            struct winsize ws;
            if (ioctl(STDOUT_FILENO, TIOCGWINSZ, &ws) == -1) {
                perror("TIOCGWINSZ");
                return 1;
            }
            printf("%3d rows x %3d cols (%d x %d pixels)\n",
                   ws.ws_row, ws.ws_col, ws.ws_xpixel, ws.ws_ypixel);
        }
        pause();               /* sleep until a signal arrives */
    }
}
```

`pause()` returns after any caught signal. The pixel size is filled in by
most modern emulators (kitty, foot, WezTerm, Ghostty, xterm) and is 0 in
others. Programs that display images need it to compute the size of a
cell in pixels.

### 11.4 A tiny full-screen program

Combining raw mode, escape sequences and the window size: a program that
draws a box around the screen, centers a message, follows the arrow keys
with a marker, and redraws on resize. It uses the alternate screen and
hides the cursor, and undoes both on exit.

```c
// file: c/boxdraw.c
#define _DEFAULT_SOURCE
#include <errno.h>
#include <poll.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <termios.h>
#include <unistd.h>

static struct termios orig;
static int rows = 24, cols = 80, x = 10, y = 5;
static volatile sig_atomic_t winch = 1;

/* Output buffer: build a whole frame, then write it once. */
static char obuf[1 << 16];
static size_t olen;
static void put(const char *s) {
    size_t n = strlen(s);
    if (olen + n < sizeof obuf) { memcpy(obuf + olen, s, n); olen += n; }
}
static void putf(const char *fmt, int a, int b) {
    char tmp[64]; snprintf(tmp, sizeof tmp, fmt, a, b); put(tmp);
}
static void flush_out(void) {
    size_t off = 0;
    while (off < olen) {
        ssize_t n = write(STDOUT_FILENO, obuf + off, olen - off);
        if (n <= 0 && errno != EINTR) break;
        if (n > 0) off += (size_t)n;
    }
    olen = 0;
}

static void leave(void)
{
    put("\x1b[?25h\x1b[?1049l");      /* show cursor, main screen */
    flush_out();
    tcsetattr(STDIN_FILENO, TCSAFLUSH, &orig);
}

static void on_winch(int s) { (void)s; winch = 1; }

static void draw(void)
{
    put("\x1b[?2026h");               /* begin synchronized update */
    put("\x1b[H\x1b[2J");             /* home, clear */
    for (int c = 1; c <= cols; c++) {
        putf("\x1b[%d;%dH-", 1, c);
        putf("\x1b[%d;%dH-", rows, c);
    }
    for (int r = 1; r <= rows; r++) {
        putf("\x1b[%d;%dH|", r, 1);
        putf("\x1b[%d;%dH|", r, cols);
    }
    const char *msg = "arrows move, q quits";
    int mr = rows / 2, mc = (cols - (int)strlen(msg)) / 2;
    if (mc < 2) mc = 2;
    putf("\x1b[%d;%dH", mr, mc);
    put("\x1b[1;36m"); put(msg); put("\x1b[0m");
    putf("\x1b[%d;%dH", y, x);
    put("\x1b[7m@\x1b[0m");
    char status[64];
    snprintf(status, sizeof status, " %dx%d  @%d,%d ", cols, rows, x, y);
    putf("\x1b[%d;%dH", rows, 3);
    put(status);
    put("\x1b[?2026l");               /* end synchronized update */
    flush_out();
}

int main(void)
{
    if (!isatty(STDIN_FILENO) || !isatty(STDOUT_FILENO)) {
        fprintf(stderr, "needs a terminal\n");
        return 1;
    }
    tcgetattr(STDIN_FILENO, &orig);
    struct termios t = orig;
    cfmakeraw(&t);
    t.c_lflag |= ISIG;                /* keep Ctrl+C working */
    t.c_oflag |= OPOST;               /* keep \n -> \r\n */
    tcsetattr(STDIN_FILENO, TCSAFLUSH, &t);
    atexit(leave);
    signal(SIGINT, exit);             /* exit() runs atexit handlers;
                                         not strictly async-signal-safe,
                                         acceptable for a demo */
    struct sigaction sa = { .sa_handler = on_winch };
    sigemptyset(&sa.sa_mask);
    sigaction(SIGWINCH, &sa, NULL);

    put("\x1b[?1049h\x1b[?25l");      /* alt screen, hide cursor */

    for (;;) {
        if (winch) {
            winch = 0;
            struct winsize ws;
            if (ioctl(STDOUT_FILENO, TIOCGWINSZ, &ws) == 0 && ws.ws_row) {
                rows = ws.ws_row;
                cols = ws.ws_col;
            }
        }
        if (x < 2) x = 2;
        if (x > cols - 1) x = cols - 1;
        if (y < 2) y = 2;
        if (y > rows - 1) y = rows - 1;
        draw();

        struct pollfd p = { .fd = STDIN_FILENO, .events = POLLIN };
        if (poll(&p, 1, -1) == -1) continue;     /* EINTR: resize */
        unsigned char b[16];
        ssize_t n = read(STDIN_FILENO, b, sizeof b);
        if (n <= 0) break;
        if (b[0] == 'q') break;
        if (n >= 3 && b[0] == 0x1b && b[1] == '[') {
            switch (b[2]) {
            case 'A': y--; break;
            case 'B': y++; break;
            case 'C': x++; break;
            case 'D': x--; break;
            }
        }
    }
    return 0;
}
```

This program redraws everything on each key, which is fine for a demo and
wasteful for anything big. Real libraries keep a model of the screen
(what is currently displayed) and a model of the next frame, compute the
difference, and emit only the escape sequences needed to change the cells
that differ. ncurses calls this `doupdate`; ratatui calls it diffing
buffers; Bubble Tea v2 uses a cell-based renderer (from the ultraviolet
library) that does the same.

Also note the *output buffer*: we build the whole frame in memory and
write it in one go. Writing escape sequences one `write` at a time makes
the terminal render intermediate states (flicker) and costs a system call
for each piece. With `?2026` (synchronized output) around the frame, a
supporting terminal displays the whole frame atomically.

---

## 12. C: pseudo-terminals

### 12.1 Spawning a program on a PTY

The first step: run a command on a new PTY and capture its output, showing
that the command believes it is on a terminal.

```c
// file: c/ptyspawn.c
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <pty.h>             /* forkpty; <util.h> on macOS/OpenBSD */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/wait.h>
#include <termios.h>
#include <unistd.h>

int main(int argc, char **argv)
{
    char *dflt[] = { "ls", "--color=auto", "/", NULL };
    char **cmd = argc > 1 ? &argv[1] : dflt;

    struct winsize ws = { .ws_row = 24, .ws_col = 60 };
    int master;
    pid_t pid = forkpty(&master, NULL, NULL, &ws);
    if (pid == -1) { perror("forkpty"); return 1; }

    if (pid == 0) {
        /* child: fds 0,1,2 are the slave, which is our ctty */
        execvp(cmd[0], cmd);
        fprintf(stderr, "exec: %s\n", strerror(errno));
        _exit(127);
    }

    /* parent: read everything the child writes, show it escaped */
    char buf[4096];
    size_t total = 0;
    for (;;) {
        ssize_t n = read(master, buf, sizeof buf);
        if (n > 0) {
            total += (size_t)n;
            for (ssize_t i = 0; i < n; i++) {
                unsigned char c = (unsigned char)buf[i];
                if (c == '\n')       fputs("\\n\n", stdout);
                else if (c == '\r')  fputs("\\r", stdout);
                else if (c == 0x1b)  fputs("\\e", stdout);
                else if (c < 0x20)   printf("^%c", c + '@');
                else                 putchar(c);
            }
            continue;
        }
        if (n == 0) break;                   /* BSD-style EOF */
        if (errno == EINTR) continue;
        if (errno == EIO) break;             /* Linux: slave closed */
        perror("read");
        break;
    }
    close(master);

    int status;
    waitpid(pid, &status, 0);
    printf("--- %zu bytes, exit status %d\n", total, WEXITSTATUS(status));
    return 0;
}
```

```text
$ cc -Wall -o ptyspawn c/ptyspawn.c -lutil
$ ./ptyspawn
\e[0m\e[01;36mbin\e[0m   \e[01;34mboot\e[0m  \e[01;34metc\e[0m   ... \r\n
...
--- 343 bytes, exit status 0
$ ./ptyspawn tty
/dev/pts/9\r\n
--- 12 bytes, exit status 0
$ ./ptyspawn stty size
24 60\r\n
--- 7 bytes, exit status 0
```

Observe:

- `ls --color=auto` emitted colors and columns, because its stdout is a
  terminal. Compare with `ls --color=auto / | cat -v`.
- Every line ends with `\r\n`: the `ONLCR` output processing of the
  slave's line discipline.
- `stty size` reports the window size we passed to `forkpty`.
- The loop ends on `EIO` (Linux) or 0 (BSD).

### 12.2 Doing it by hand: posix_openpt

`forkpty` hides the steps. Here they are, explicitly, as a function you
can reuse in your own programs. It returns the master fd and the child PID.

```c
// file: c/ptyopen.h
#ifndef PTYOPEN_H
#define PTYOPEN_H
#include <sys/ioctl.h>
#include <sys/types.h>
#include <termios.h>

/*
 * Start argv[0] on a new pseudo-terminal.
 * term: initial termios for the slave (NULL: kernel default)
 * ws:   initial window size (NULL: 0x0)
 * Returns child pid, stores master fd in *master_out. -1 on error.
 */
pid_t pty_spawn(char *const argv[], const struct termios *term,
                const struct winsize *ws, int *master_out);
#endif
```

```c
// file: c/ptyopen.c
#define _XOPEN_SOURCE 700
#define _DEFAULT_SOURCE
#include "ptyopen.h"
#include <errno.h>
#include <fcntl.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

pid_t pty_spawn(char *const argv[], const struct termios *term,
                const struct winsize *ws, int *master_out)
{
    int master = posix_openpt(O_RDWR | O_NOCTTY);
    if (master == -1) return -1;
    if (grantpt(master) == -1 || unlockpt(master) == -1) goto fail;

    /* close-on-exec on the master, so the child does not inherit it */
    if (fcntl(master, F_SETFD, FD_CLOEXEC) == -1) goto fail;

    char *name = ptsname(master);
    if (!name) goto fail;
    char slave_name[64];
    snprintf(slave_name, sizeof slave_name, "%s", name);

    pid_t pid = fork();
    if (pid == -1) goto fail;

    if (pid == 0) {
        /* child */
        if (setsid() == -1) _exit(126);
        int slave = open(slave_name, O_RDWR);   /* becomes ctty (Linux) */
        if (slave == -1) _exit(126);
#ifdef TIOCSCTTY
        ioctl(slave, TIOCSCTTY, 0);               /* required on BSD */
#endif
        if (term) tcsetattr(slave, TCSANOW, term);
        if (ws) ioctl(slave, TIOCSWINSZ, ws);
        dup2(slave, 0);
        dup2(slave, 1);
        dup2(slave, 2);
        if (slave > 2) close(slave);

        /* reset signals the parent may have changed */
        signal(SIGPIPE, SIG_DFL);
        signal(SIGINT, SIG_DFL);
        signal(SIGQUIT, SIG_DFL);
        signal(SIGTSTP, SIG_DFL);
        signal(SIGTTIN, SIG_DFL);
        signal(SIGTTOU, SIG_DFL);
        signal(SIGCHLD, SIG_DFL);
        signal(SIGWINCH, SIG_DFL);

        execvp(argv[0], argv);
        fprintf(stderr, "exec %s: %s\r\n", argv[0], strerror(errno));
        _exit(127);
    }

    *master_out = master;
    return pid;

fail:;
    int e = errno;
    close(master);
    errno = e;
    return -1;
}
```

Why set the termios and window size in the child, on the slave, rather
than in the parent on the master? Either works on Linux; doing it on the
slave in the child is the most portable, and it happens before `exec`, so
the program never sees intermediate values. `forkpty` does it in the parent
before forking.

A subtle point about the parent: once the child has opened the slave, the
parent never opens it at all. That is important. If the *parent* had the
slave open, the master would never see EOF/EIO when the child exits,
because the parent's own fd would keep the slave alive. (Some programs
deliberately keep a slave fd open to avoid losing output, see section
6.6; then they must use `SIGCHLD` to detect exit.)

### 12.3 A `script` clone

`script(1)` records a terminal session: it runs a shell on a new PTY,
puts the *real* terminal in raw mode, and copies bytes in both directions,
also writing the output to a file. It is the canonical PTY program, and
the first project we will port to every language. This version:

- copies the real terminal's termios and size to the new PTY;
- forwards `SIGWINCH`;
- uses the self-pipe trick to handle signals in the `poll` loop;
- writes a typescript file;
- exits with the child's status.

```c
// file: c/ptyscript.c
#define _GNU_SOURCE
#include "ptyopen.h"
#include <errno.h>
#include <fcntl.h>
#include <poll.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/wait.h>
#include <termios.h>
#include <time.h>
#include <unistd.h>

static int sig_w = -1;                  /* self-pipe write end */
static struct termios saved_tty;
static int tty_raw = 0;

static void on_signal(int sig)
{
    int e = errno;
    unsigned char b = (unsigned char)sig;
    (void)!write(sig_w, &b, 1);
    errno = e;
}

static void restore_tty(void)
{
    if (tty_raw) {
        tcsetattr(STDIN_FILENO, TCSAFLUSH, &saved_tty);
        tty_raw = 0;
    }
}

static int write_all(int fd, const char *p, size_t n)
{
    while (n > 0) {
        ssize_t w = write(fd, p, n);
        if (w == -1) {
            if (errno == EINTR) continue;
            if (errno == EAGAIN) {          /* non-blocking peer */
                struct pollfd pf = { .fd = fd, .events = POLLOUT };
                poll(&pf, 1, -1);
                continue;
            }
            return -1;
        }
        p += w;
        n -= (size_t)w;
    }
    return 0;
}

int main(int argc, char **argv)
{
    const char *logname = "typescript";
    int opt;
    while ((opt = getopt(argc, argv, "o:")) != -1) {
        if (opt == 'o') logname = optarg;
        else { fprintf(stderr, "usage: %s [-o file] [cmd...]\n", argv[0]);
               return 2; }
    }
    char *shell = getenv("SHELL");
    char *dflt[] = { shell ? shell : "/bin/sh", NULL };
    char **cmd = optind < argc ? &argv[optind] : dflt;

    int is_tty = isatty(STDIN_FILENO);
    struct winsize ws = { .ws_row = 24, .ws_col = 80 };
    if (is_tty) {
        tcgetattr(STDIN_FILENO, &saved_tty);
        ioctl(STDIN_FILENO, TIOCGWINSZ, &ws);
    }

    int log = open(logname, O_WRONLY | O_CREAT | O_TRUNC | O_CLOEXEC, 0644);
    if (log == -1) { perror(logname); return 1; }
    time_t now = time(NULL);
    dprintf(log, "Script started on %s", ctime(&now));

    /* self-pipe */
    int sp[2];
    if (pipe2(sp, O_CLOEXEC | O_NONBLOCK) == -1) { perror("pipe2"); return 1; }
    sig_w = sp[1];
    struct sigaction sa = { .sa_handler = on_signal };
    sigemptyset(&sa.sa_mask);
    sa.sa_flags = SA_RESTART;           /* poll still returns EINTR */
    sigaction(SIGWINCH, &sa, NULL);
    sigaction(SIGCHLD, &sa, NULL);
    sigaction(SIGTERM, &sa, NULL);
    sigaction(SIGHUP, &sa, NULL);

    int master;
    pid_t child = pty_spawn(cmd, is_tty ? &saved_tty : NULL, &ws, &master);
    if (child == -1) { perror("pty_spawn"); return 1; }

    if (is_tty) {
        struct termios raw = saved_tty;
        cfmakeraw(&raw);
        tcsetattr(STDIN_FILENO, TCSAFLUSH, &raw);
        tty_raw = 1;
        atexit(restore_tty);
    }

    fprintf(stderr, "Script started, output log file is '%s'.\r\n", logname);

    struct pollfd pf[3] = {
        { .fd = STDIN_FILENO, .events = POLLIN },
        { .fd = master,       .events = POLLIN },
        { .fd = sp[0],        .events = POLLIN },
    };
    char buf[8192];
    int child_status = 0, child_done = 0;

    for (;;) {
        if (poll(pf, 3, -1) == -1) {
            if (errno == EINTR) continue;
            perror("poll");
            break;
        }

        /* signals first */
        if (pf[2].revents & POLLIN) {
            unsigned char s;
            while (read(sp[0], &s, 1) == 1) {
                if (s == SIGWINCH && is_tty) {
                    struct winsize w;
                    if (ioctl(STDIN_FILENO, TIOCGWINSZ, &w) == 0)
                        ioctl(master, TIOCSWINSZ, &w);
                } else if (s == SIGCHLD) {
                    if (waitpid(child, &child_status, WNOHANG) == child)
                        child_done = 1;
                } else if (s == SIGTERM || s == SIGHUP) {
                    kill(child, SIGHUP);
                }
            }
        }

        /* user -> child */
        if (pf[0].revents & (POLLIN | POLLHUP)) {
            ssize_t n = read(STDIN_FILENO, buf, sizeof buf);
            if (n > 0) {
                write_all(master, buf, (size_t)n);
            } else {
                /* stdin EOF (not a tty): send EOF char, stop polling it */
                if (!is_tty) {
                    char eof = 4;                /* ^D */
                    write_all(master, &eof, 1);
                }
                pf[0].fd = -1;
            }
        }

        /* child -> user and log */
        if (pf[1].revents & (POLLIN | POLLHUP | POLLERR)) {
            ssize_t n = read(master, buf, sizeof buf);
            if (n > 0) {
                write_all(STDOUT_FILENO, buf, (size_t)n);
                write_all(log, buf, (size_t)n);
            } else if (n == 0 || errno == EIO) {
                break;                          /* slave side closed */
            } else if (errno != EINTR && errno != EAGAIN) {
                perror("read master");
                break;
            }
        }
    }

    restore_tty();
    if (!child_done) waitpid(child, &child_status, 0);
    now = time(NULL);
    dprintf(log, "\nScript done on %s", ctime(&now));
    close(log);
    fprintf(stderr, "Script done.\n");

    if (WIFEXITED(child_status)) return WEXITSTATUS(child_status);
    if (WIFSIGNALED(child_status)) return 128 + WTERMSIG(child_status);
    return 1;
}
```

```text
$ cc -Wall -o ptyscript c/ptyscript.c c/ptyopen.c -lutil
$ ./ptyscript -o session.log
Script started, output log file is 'session.log'.
$ echo hello; tty
hello
/dev/pts/11
$ vim            # works, fully interactive
$ exit
Script done.
$ cat -v session.log | head
```

Points worth studying:

- **Raw mode on our own terminal**. We do *not* want our terminal's line
  discipline to process the user's keys: they must reach the child's line
  discipline (the slave) untouched, which will do the processing exactly
  once. With our terminal in raw mode, `^C` arrives as `0x03`, we forward
  it to the master, and the *slave's* line discipline turns it into
  `SIGINT` for the child's foreground job. Similarly, echo is done by the
  slave, and the echoed characters come back through the master to our
  stdout.
- **Output processing** happens on the slave too (`ONLCR`), and our
  terminal's `OPOST` is off, so the `\r\n` are passed through unchanged.
- **The self-pipe** turns `SIGWINCH`, `SIGCHLD`, `SIGTERM` and `SIGHUP` into
  readable bytes. `SA_RESTART` does not affect `poll` on Linux (it always
  returns `EINTR` when interrupted by a handler), so we loop.
- **Exit condition**: EOF/EIO on the master, not the child's death. When
  the shell exits, all fds on the slave are closed (unless a background
  process keeps it), and we get `EIO` after draining the remaining output.
- **Non-terminal stdin**: if you run `echo 'ls; exit' | ./ptyscript`,
  stdin is a pipe. We do not enter raw mode, and at EOF we send `^D` to the
  child, which the slave's line discipline turns into EOF for the shell.

### 12.4 An expect-like driver in C

The other big use of PTYs is automation. Here is a minimal "expect": start
a program, wait for a pattern in its output (with a timeout), send a
response. We drive Python's REPL as an example, but any interactive
program works.

```c
// file: c/ptyexpect.c
#define _GNU_SOURCE
#include "ptyopen.h"
#include <errno.h>
#include <poll.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

typedef struct {
    int fd;
    pid_t pid;
    char buf[65536];
    size_t len;
} Session;

static long now_ms(void)
{
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec * 1000L + ts.tv_nsec / 1000000L;
}

/* Wait until `pattern` appears in the output. Consumes output up to and
   including the match; the text before the match is copied to `before`
   (if not NULL). Returns 0 on match, -1 on timeout, -2 on EOF. */
static int expect(Session *s, const char *pattern, int timeout_ms,
                  char *before, size_t before_size)
{
    long deadline = now_ms() + timeout_ms;
    for (;;) {
        s->buf[s->len] = '\0';
        char *hit = strstr(s->buf, pattern);
        if (hit) {
            size_t pre = (size_t)(hit - s->buf);
            if (before && before_size > 0) {
                size_t k = pre < before_size - 1 ? pre : before_size - 1;
                memcpy(before, s->buf, k);
                before[k] = '\0';
            }
            size_t used = pre + strlen(pattern);
            memmove(s->buf, s->buf + used, s->len - used);
            s->len -= used;
            return 0;
        }
        long left = deadline - now_ms();
        if (left <= 0) return -1;

        struct pollfd pf = { .fd = s->fd, .events = POLLIN };
        int r = poll(&pf, 1, (int)left);
        if (r == -1 && errno == EINTR) continue;
        if (r <= 0) return -1;

        if (s->len >= sizeof s->buf - 1) {        /* drop oldest half */
            size_t half = s->len / 2;
            memmove(s->buf, s->buf + half, s->len - half);
            s->len -= half;
        }
        ssize_t n = read(s->fd, s->buf + s->len, sizeof s->buf - 1 - s->len);
        if (n > 0) s->len += (size_t)n;
        else if (n == 0 || errno == EIO) return -2;
    }
}

static void send_str(Session *s, const char *str)
{
    size_t n = strlen(str);
    while (n > 0) {
        ssize_t w = write(s->fd, str, n);
        if (w <= 0) { if (errno == EINTR) continue; return; }
        str += w; n -= (size_t)w;
    }
}

int main(void)
{
    char *argv[] = { "python3", "-q", NULL };
    struct termios t;
    /* start from sane defaults, but without echo: we do not want to read
       back what we send */
    memset(&t, 0, sizeof t);
    t.c_iflag = ICRNL | IXON | IUTF8;
    t.c_oflag = OPOST | ONLCR;
    t.c_cflag = CS8 | CREAD;
    t.c_lflag = ICANON | ISIG | IEXTEN;          /* no ECHO */
    t.c_cc[VINTR] = 3; t.c_cc[VQUIT] = 28; t.c_cc[VERASE] = 127;
    t.c_cc[VKILL] = 21; t.c_cc[VEOF] = 4; t.c_cc[VMIN] = 1;
    t.c_cc[VSUSP] = 26;
    cfsetispeed(&t, B38400);
    cfsetospeed(&t, B38400);
    struct winsize ws = { .ws_row = 24, .ws_col = 80 };

    /* plain prompts: no colors, no fancy line editor (Python 3.13+) */
    setenv("PYTHON_BASIC_REPL", "1", 1);
    setenv("TERM", "dumb", 1);

    Session s = { 0 };
    s.pid = pty_spawn(argv, &t, &ws, &s.fd);
    if (s.pid == -1) { perror("spawn"); return 1; }

    const char *exprs[] = { "6 * 7", "sum(range(101))", "2 ** 100" };
    if (expect(&s, ">>> ", 5000, NULL, 0) != 0) {
        fprintf(stderr, "no prompt\n");
        return 1;
    }
    for (size_t i = 0; i < 3; i++) {
        send_str(&s, "print(");
        send_str(&s, exprs[i]);
        send_str(&s, ")\r");
        /* the answer is everything before the next prompt */
        char answer[1024];
        long t0 = now_ms();
        if (expect(&s, ">>> ", 5000, answer, sizeof answer) != 0) break;
        answer[strcspn(answer, "\r\n")] = '\0';     /* first line */
        printf("%-16s => %-32s (%ld ms)\n", exprs[i], answer, now_ms() - t0);
    }
    send_str(&s, "\x04");                 /* ^D: EOF, python exits */
    int st;
    waitpid(s.pid, &st, 0);
    printf("python exited with %d\n", WEXITSTATUS(st));
    return 0;
}
```

```text
$ cc -Wall -o ptyexpect c/ptyexpect.c c/ptyopen.c
$ ./ptyexpect
6 * 7            => 42                               (1 ms)
sum(range(101))  => 5050                             (0 ms)
2 ** 100         => 1267650600228229401496703205376  (0 ms)
python exited with 0
```

The answer is everything between our input and the next prompt. Because
echo is off on the slave, we do not see `print(6 * 7)` echoed back; with
echo on, the first line of `answer` would be the echoed command. The
Raku, Rust and Go versions in chapter 30 use regular expressions instead
of plain substrings.

Things to know about driving a REPL through a PTY:

- Python's REPL behaves differently on a terminal and on a pipe (no
  prompt on a pipe). That is precisely why a PTY is needed.
- Recent Python versions (3.13+) have a new REPL with colors and its own
  line editor, which emits escape sequences around the prompt. Without the
  two `setenv` calls, the "answers" captured above are cursor movements and
  color codes such as `\e[0m\e[4D\e[?12l\e[?25h`. Setting
  `PYTHON_BASIC_REPL=1` and `TERM=dumb` in the child's environment gives a
  simpler, more scriptable prompt. Every automation tool has to deal with
  this kind of thing: disable fancy features with environment variables
  (`TERM=dumb`, `NO_COLOR=1`, `PAGER=cat`).
- We send `\r`, not `\n`: that is what a keyboard sends. With `ICRNL` on
  the slave, either works for canonical mode, but a raw-mode line editor
  may only accept `\r`.
- Turning echo off at spawn time is only a default: a line editor that
  sets its own termios turns it on again or does its own echo. Expect
  patterns must tolerate seeing your input echoed.

---

## 13. C: a tiny job-control shell

This chapter brings chapters 3 to 5 together in one program: a minimal
shell with pipelines, foreground and background jobs, `^C`, `^Z`, `fg`,
`bg` and `jobs`. It is about 300 lines, and almost every line maps to a
rule from Part I. The structure follows the "Implementing a Job Control
Shell" section of the GNU C Library manual, which is the classic reference.

Limitations, to keep it short: no quoting (words are split on spaces), no
redirections except pipes, no variables, a fixed maximum number of jobs.

### 13.1 Design

- The shell puts itself in its own process group and takes the terminal
  (`tcsetpgrp`). It ignores the job-control signals so that `^C` and `^Z`
  do not affect it.
- Each command line is a *job*: one process group containing every process
  of the pipeline.
- For a foreground job, the shell gives the terminal to the job's group,
  waits until every process has exited or stopped, then takes the
  terminal back and restores its termios.
- For a background job (`&`), it does not give the terminal and does not
  wait. It reaps finished background jobs before each prompt with
  `waitpid(-1, ..., WNOHANG)`.
- `fg %n` gives the terminal to job n, restores *its* saved termios,
  sends `SIGCONT`, and waits. `bg %n` sends `SIGCONT` only.

### 13.2 The code

```c
// file: c/minishell.c
#define _POSIX_C_SOURCE 200809L
#include <errno.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/wait.h>
#include <termios.h>
#include <unistd.h>

#define MAXJOBS   32
#define MAXPROCS  16
#define MAXARGS   64

typedef struct {
    pid_t pid;
    int   done;      /* exited or killed */
    int   stopped;
    int   status;
} Proc;

typedef struct {
    int    used;
    char   cmdline[256];
    pid_t  pgid;
    Proc   procs[MAXPROCS];
    int    nprocs;
    struct termios tmodes;   /* saved terminal modes of a stopped job */
    int    notified;
} Job;

static Job   jobs[MAXJOBS];
static int   shell_terminal = STDIN_FILENO;
static pid_t shell_pgid;
static struct termios shell_tmodes;
static int   interactive;

/* ---------- job bookkeeping ---------- */

static int job_is_stopped(Job *j)
{
    for (int i = 0; i < j->nprocs; i++)
        if (!j->procs[i].done && !j->procs[i].stopped) return 0;
    return 1;
}

static int job_is_done(Job *j)
{
    for (int i = 0; i < j->nprocs; i++)
        if (!j->procs[i].done) return 0;
    return 1;
}

/* Record the status returned by waitpid for pid. Returns 0 if found. */
static int mark_status(pid_t pid, int status)
{
    for (int k = 0; k < MAXJOBS; k++) {
        Job *j = &jobs[k];
        if (!j->used) continue;
        for (int i = 0; i < j->nprocs; i++) {
            Proc *p = &j->procs[i];
            if (p->pid != pid) continue;
            p->status = status;
            if (WIFSTOPPED(status)) {
                p->stopped = 1;
            } else {
                p->done = 1;
                if (WIFSIGNALED(status) && WTERMSIG(status) != SIGPIPE
                    && WTERMSIG(status) != SIGINT)
                    fprintf(stderr, "%d: terminated by signal %d\n",
                            (int)pid, WTERMSIG(status));
            }
            return 0;
        }
    }
    return -1;
}

/* Reap children without blocking; used before each prompt. */
static void update_status(void)
{
    int status;
    pid_t pid;
    while ((pid = waitpid(-1, &status, WUNTRACED | WNOHANG)) > 0)
        mark_status(pid, status);
}

/* Block until every process of j has exited or stopped. */
static void wait_for_job(Job *j)
{
    while (!job_is_stopped(j)) {
        int status;
        pid_t pid = waitpid(-j->pgid, &status, WUNTRACED);
        if (pid == -1) {
            if (errno == EINTR) continue;
            if (errno == ECHILD) break;
            perror("waitpid");
            break;
        }
        mark_status(pid, status);
    }
}

static void print_job(int n, Job *j, const char *state)
{
    fprintf(stderr, "[%d] %-10s %s\n", n + 1, state, j->cmdline);
}

/* Report and free jobs that are done; report newly stopped jobs. */
static void do_job_notification(void)
{
    update_status();
    for (int k = 0; k < MAXJOBS; k++) {
        Job *j = &jobs[k];
        if (!j->used) continue;
        if (job_is_done(j)) {
            if (j->notified >= 0)               /* background job */
                print_job(k, j, "Done");
            j->used = 0;
        } else if (job_is_stopped(j) && !j->notified) {
            print_job(k, j, "Stopped");
            j->notified = 1;
        }
    }
}

/* ---------- foreground / background ---------- */

static void put_in_foreground(Job *j, int cont)
{
    tcsetpgrp(shell_terminal, j->pgid);
    if (cont) {
        tcsetattr(shell_terminal, TCSADRAIN, &j->tmodes);
        if (kill(-j->pgid, SIGCONT) == -1) perror("kill (SIGCONT)");
    }
    wait_for_job(j);

    /* take the terminal back */
    tcsetpgrp(shell_terminal, shell_pgid);
    tcgetattr(shell_terminal, &j->tmodes);       /* save the job's modes */
    tcsetattr(shell_terminal, TCSADRAIN, &shell_tmodes);
}

static void put_in_background(Job *j, int cont)
{
    if (cont && kill(-j->pgid, SIGCONT) == -1) perror("kill (SIGCONT)");
}

static void continue_job(Job *j, int foreground)
{
    for (int i = 0; i < j->nprocs; i++) j->procs[i].stopped = 0;
    j->notified = foreground ? -1 : 0;     /* -1: no "Done" report */
    if (foreground) put_in_foreground(j, 1);
    else            put_in_background(j, 1);
}

/* ---------- launching ---------- */

static void launch_process(char **argv, pid_t pgid, int infd, int outfd,
                           int foreground)
{
    if (interactive) {
        pid_t pid = getpid();
        if (pgid == 0) pgid = pid;
        setpgid(pid, pgid);                    /* child side of the race */
        if (foreground) tcsetpgrp(shell_terminal, pgid);

        signal(SIGINT, SIG_DFL);
        signal(SIGQUIT, SIG_DFL);
        signal(SIGTSTP, SIG_DFL);
        signal(SIGTTIN, SIG_DFL);
        signal(SIGTTOU, SIG_DFL);
        signal(SIGCHLD, SIG_DFL);
    }
    if (infd != STDIN_FILENO)  { dup2(infd, STDIN_FILENO);   close(infd); }
    if (outfd != STDOUT_FILENO) { dup2(outfd, STDOUT_FILENO); close(outfd); }

    execvp(argv[0], argv);
    fprintf(stderr, "%s: %s\n", argv[0], strerror(errno));
    _exit(127);
}

static void launch_job(Job *j, char **cmds[], int ncmds, int foreground)
{
    int infd = STDIN_FILENO;
    for (int i = 0; i < ncmds; i++) {
        int p[2] = { -1, -1 };
        int outfd = STDOUT_FILENO;
        if (i < ncmds - 1) {
            if (pipe(p) == -1) { perror("pipe"); return; }
            outfd = p[1];
        }

        pid_t pid = fork();
        if (pid == 0) {
            if (p[0] != -1) close(p[0]);
            launch_process(cmds[i], j->pgid, infd, outfd, foreground);
        } else if (pid < 0) {
            perror("fork");
            return;
        }

        j->procs[j->nprocs++] = (Proc){ .pid = pid };
        if (interactive) {
            if (!j->pgid) j->pgid = pid;
            setpgid(pid, j->pgid);              /* parent side of the race */
        }

        if (infd != STDIN_FILENO) close(infd);
        if (outfd != STDOUT_FILENO) close(outfd);
        infd = p[0];
    }

    if (!interactive)       wait_for_job(j);
    else if (foreground)    put_in_foreground(j, 0);
    else {
        fprintf(stderr, "[%d] %d\n", (int)(j - jobs) + 1, (int)j->pgid);
        put_in_background(j, 0);
    }
}

/* ---------- parsing and builtins ---------- */

static Job *find_job(const char *arg)
{
    int n = -1;
    if (arg && arg[0] == '%') n = atoi(arg + 1) - 1;
    else if (arg) n = atoi(arg) - 1;
    else {                                        /* most recent job */
        for (int k = MAXJOBS - 1; k >= 0; k--)
            if (jobs[k].used) { n = k; break; }
    }
    if (n < 0 || n >= MAXJOBS || !jobs[n].used) {
        fprintf(stderr, "no such job\n");
        return NULL;
    }
    return &jobs[n];
}

static int builtin(char **argv)
{
    if (strcmp(argv[0], "exit") == 0) exit(argv[1] ? atoi(argv[1]) : 0);
    if (strcmp(argv[0], "cd") == 0) {
        const char *dir = argv[1] ? argv[1] : getenv("HOME");
        if (chdir(dir) == -1) perror("cd");
        return 1;
    }
    if (strcmp(argv[0], "jobs") == 0) {
        update_status();
        for (int k = 0; k < MAXJOBS; k++)
            if (jobs[k].used)
                print_job(k, &jobs[k],
                          job_is_stopped(&jobs[k]) ? "Stopped" : "Running");
        return 1;
    }
    if (strcmp(argv[0], "fg") == 0 || strcmp(argv[0], "bg") == 0) {
        Job *j = find_job(argv[1]);
        if (j) {
            int fg = argv[0][0] == 'f';
            fprintf(stderr, "%s\n", j->cmdline);
            continue_job(j, fg);
        }
        return 1;
    }
    return 0;
}

static void init_shell(void)
{
    interactive = isatty(shell_terminal);
    if (!interactive) return;

    /* Loop until we are in the foreground. */
    while (tcgetpgrp(shell_terminal) != (shell_pgid = getpgrp()))
        kill(-shell_pgid, SIGTTIN);

    signal(SIGINT, SIG_IGN);
    signal(SIGQUIT, SIG_IGN);
    signal(SIGTSTP, SIG_IGN);
    signal(SIGTTIN, SIG_IGN);
    signal(SIGTTOU, SIG_IGN);

    /* Put ourselves in our own process group and grab the terminal. */
    shell_pgid = getpid();
    if (setpgid(shell_pgid, shell_pgid) == -1 && errno != EPERM) {
        perror("setpgid");
        exit(1);
    }
    tcsetpgrp(shell_terminal, shell_pgid);
    tcgetattr(shell_terminal, &shell_tmodes);
}

int main(void)
{
    init_shell();
    char line[1024];

    for (;;) {
        do_job_notification();
        if (interactive) { fputs("msh$ ", stderr); fflush(stderr); }
        if (!fgets(line, sizeof line, stdin)) {
            if (ferror(stdin) && errno == EINTR) { clearerr(stdin); continue; }
            break;                                   /* EOF: ^D */
        }
        line[strcspn(line, "\n")] = '\0';

        Job *j = NULL;
        for (int k = 0; k < MAXJOBS; k++)
            if (!jobs[k].used) { j = &jobs[k]; break; }
        if (!j) { fprintf(stderr, "too many jobs\n"); continue; }

        memset(j, 0, sizeof *j);
        snprintf(j->cmdline, sizeof j->cmdline, "%.255s", line);
        j->tmodes = shell_tmodes;

        /* split into words and commands */
        static char *words[MAXARGS + MAXPROCS + 2];
        char **cmds[MAXPROCS];
        int nw = 0, nc = 0, foreground = 1;
        char *save, *tok = strtok_r(line, " \t", &save);
        if (!tok) continue;
        cmds[nc++] = &words[0];
        for (; tok; tok = strtok_r(NULL, " \t", &save)) {
            if (strcmp(tok, "&") == 0) { foreground = 0; continue; }
            if (strcmp(tok, "|") == 0 && nc < MAXPROCS) {
                words[nw++] = NULL;
                cmds[nc++] = &words[nw];
                continue;
            }
            if (nw < MAXARGS) words[nw++] = tok;
        }
        words[nw] = NULL;
        if (!cmds[0][0]) continue;

        if (nc == 1 && builtin(cmds[0])) continue;

        j->used = 1;
        if (!foreground) j->notified = 0;
        else j->notified = -1;               /* do not print "Done" */
        launch_job(j, cmds, nc, foreground);
        if (foreground && job_is_stopped(j) && !job_is_done(j))
            j->notified = 0;                 /* report "Stopped" */
    }
    if (interactive) fputs("\n", stderr);
    return 0;
}
```

### 13.3 Trying it

```text
$ cc -Wall -o minishell c/minishell.c && ./minishell
msh$ ls /usr/bin | grep zip | wc -l
12
msh$ sleep 30 &
[1] 7120
msh$ vim notes.txt
        (press ^Z in vim)
[2] Stopped    vim notes.txt
msh$ jobs
[1] Running    sleep 30 &
[2] Stopped    vim notes.txt
msh$ fg %2
vim notes.txt
        (vim comes back, exactly as you left it; :q)
msh$ cat
        (press ^C: cat dies, the shell survives)
msh$ sleep 1 &
[2] 7133
msh$
[2] Done       sleep 1 &
msh$ ^D
```

### 13.4 What to notice

- **Double `setpgid`**: once in the child (`launch_process`) and once in
  the parent (`launch_job`), for the race described in 5.5. Same for
  `tcsetpgrp` in the child for foreground jobs.
- **The shell ignores `SIGTTOU`**, otherwise its own `tcsetpgrp` calls,
  made while it is in the background (when a job has the terminal), would
  stop it.
- **Signal dispositions reset in the child.** An ignored signal stays
  ignored across `exec`. Without the reset, `^C` would not kill commands
  started from this shell.
- **Saving the job's termios** when it stops (`tcgetattr` after
  `wait_for_job`) and restoring it on `fg`. vim also restores its own
  settings on `SIGCONT`, but programs that do not handle `SIGCONT`
  rely on the shell for this.
- **`waitpid(-pgid, ..., WUNTRACED)`** waits for any process of the job,
  and reports stops as well as exits.
- **`kill(-pgid, SIGCONT)`** continues the whole pipeline at once.
- **`SIGINT` reports**: we do not print "terminated by signal 2" for `^C`,
  nor for `SIGPIPE`, which are normal ways for pipeline members to die.

A real shell adds: redirections (`<`, `>`, `2>&1`, `<<`), quoting and
expansion, a line editor in raw mode (which means it must restore cooked
mode before running each job and re-enter raw mode at each prompt),
`SIGCHLD` handling for asynchronous notifications, `wait`, `disown`,
`$?`, `huponexit`, and handling of `SIGHUP` (forwarding it to jobs).

### 13.5 Exercises for the C part

See Appendix E for full statements. In short:

1. Add `<` and `>` redirections to `minishell`.
2. Make `ptyscript` record timing information (like `script -T`) so that
   a session can be replayed at the original speed.
3. Write `ptyreplay`, which reads such a file and replays it.
4. Rewrite `ptyscript`'s loop with `epoll` and `signalfd` instead of `poll`
   and the self-pipe.
5. Make `rawkeys` handle sequences split across `read` calls, with an
   ESC timeout of 50 ms.

---

## 14. Raku: the ecosystem

Raku (formerly Perl 6) is a multi-paradigm language with gradual typing,
grammars, a rich object system, first-class concurrency (promises,
supplies, channels) and Unicode at the grapheme level. Its main
implementation is **Rakudo**, which runs on the **MoarVM** virtual machine
(a JVM backend exists but is less maintained). For our purposes, the
interesting parts are:

- `Proc` and `Proc::Async`: running processes with pipes, with an
  asynchronous, event-driven API built on libuv;
- **supplies** and `react`/`whenever`: a clean way to handle several
  event sources at once (process output, signals, timers, input), which is
  exactly what PTY programs need;
- **NativeCall**: calling C functions from libc directly, without writing
  any C. We use it for `termios`, `openpty`/`forkpty`, `ioctl` and the rest.

### 14.1 Rakudo Star and installing

There are several ways to install Raku:

- **Rakudo Star**: a distribution bundling Rakudo, the `zef` module
  manager and a curated set of modules (including several Terminal
  modules), released periodically. Install it from rakudo.org, or build
  it from source with its `bin/rstar` tool.
- **rakubrew**: a version manager, like `rbenv` or `pyenv`.
- **System packages**: `pacman -S rakudo` on Arch, `apt install rakudo` on
  Debian/Ubuntu (often older versions).
- **Docker**: the `rakudo-star` image.

On the machine used for this tutorial, Rakudo Star 2026.08 is installed in
the user's home directory:

```text
$ raku -v
Welcome to Rakudo™ Star v2026.08.
Implementing the Raku® Programming Language v6.d.
Built on MoarVM version 2026.08.
$ which raku zef
~/git/rakudo---star/bin/raku
~/git/rakudo---star/share/perl6/site/bin/zef
```

### 14.2 Running Raku code

Raku is compiled to MoarVM bytecode at load time; there is no separate
compile step for scripts:

```text
$ raku hello.raku              # run a script
$ raku -e 'say "hi"'           # one-liner
$ raku -c hello.raku           # syntax check only ("Syntax OK")
$ raku                         # REPL
$ raku --ll-exception x.raku   # low-level backtrace on errors
$ raku -I lib bin/app.raku     # add a module search path
```

Make a script executable with a shebang line `#!/usr/bin/env raku` and
`chmod +x`.

Startup time is noticeable (around 0.1 to 0.2 seconds for a trivial
script; more when loading many modules for the first time, since modules are
precompiled on first use and cached).

Raku source files use the extensions `.raku` (scripts), `.rakumod`
(modules) and `.rakutest` (tests); older `.p6`, `.pm6` and `.t` extensions
still work.

### 14.3 zef and modules

`zef` is the module manager. Modules come from the **Raku ecosystem**
(raku.land is the browsable index; the zef ecosystem is the main
repository, older modules may come from the "p6c" or "cpan" ecosystems).

```text
$ zef search Terminal               # find modules
$ zef info Term::termios            # describe one
$ zef install Terminal::LineEditor  # install (with dependencies)
$ zef list --installed              # what is installed
$ zef locate Terminal::ANSI         # where is it on disk
$ zef uninstall Some::Module
```

Module names in this tutorial, and what they are for:

| Module | Purpose |
|--------|---------|
| `NativeCall` | call C (core) |
| `Term::termios` | termios wrapper |
| `Terminal::ANSI` | escape sequences |
| `Terminal::ANSIColor` | colors |
| `Terminal::ANSIParser` | parse VT input |
| `Terminal::LineEditor` | readline-like |
| `Terminal::UI` | TUI framework |
| `Terminal::Capabilities` | feature detection |
| `Readline` | GNU Readline binding |

`NativeCall` comes with Rakudo itself. The others come from the ecosystem
(several are bundled with Rakudo Star). You can check what is installed:

```text
$ zef list --installed | grep -i term
Term::termios:ver<0.2.8>:auth<zef:krunen>
Terminal-API:ver<1.0.5>:auth<zef:patrickb>
Terminal::ANSI:ver<0.0.24>:auth<cpan:bduggan>
Terminal::ANSIColor:ver<0.14>:auth<zef:raku-community-modules>
Terminal::ANSIParser:ver<0.0.4>:auth<zef:japhb>
Terminal::Capabilities:ver<0.0.21>:auth<zef:japhb>
Terminal::LineEditor:ver<0.0.23>:auth<zef:japhb>
Terminal::UI:ver<0.1.14>:auth<zef:bduggan>
```

### 14.4 Project layout

A Raku distribution (installable package) looks like this:

```text
MyTerm/
  META6.json          # name, version, dependencies, provides
  lib/MyTerm.rakumod
  lib/MyTerm/Pty.rakumod
  bin/myterm          # scripts installed on PATH
  t/01-basic.rakutest
  README.md
```

A minimal `META6.json`:

```json
{
  "name": "MyTerm",
  "version": "0.0.1",
  "auth": "zef:yourname",
  "description": "Terminal experiments",
  "depends": ["Term::termios"],
  "provides": {
    "MyTerm": "lib/MyTerm.rakumod",
    "MyTerm::Pty": "lib/MyTerm/Pty.rakumod"
  },
  "license": "Artistic-2.0"
}
```

Then:

```text
$ raku -Ilib bin/myterm          # run without installing
$ zef test .                     # run t/ with the prove-like runner
$ prove6 -l t/                   # if App::Prove6 is installed
$ zef install .                  # install the distribution locally
```

For this tutorial, scripts are single files in `raku/`, and shared code
goes into `raku/lib/`. Run them with `raku -I raku/lib raku/script.raku`.

### 14.5 Documentation

- docs.raku.org: the language and type documentation. The pages for
  `Proc`, `Proc::Async`, `IO::Handle`, `Supply`, `signal`, `react`, and
  the NativeCall guide (`/language/nativecall`) are the most relevant.
- `rakudoc Proc::Async` (if the `rakudoc` tool is installed) shows the
  same documentation in the terminal.
- raku.land: module pages, each with its README.
- The source of a module is often the best documentation:
  `zef locate Term::termios` gives you its path.

### 14.6 Raku features we rely on

If you know Perl, Python or Ruby, most of Raku reads naturally. A few
features that matter in this tutorial:

- **Sigils**: `$x` scalar, `@a` array, `%h` hash, `&f` code.
- **Strings vs bufs**: a `Str` is text (graphemes); a `Buf`/`Blob` is
  bytes. Terminal and pipe I/O is bytes; you decode with `.decode` and
  encode with `.encode`. Many I/O methods offer both (`.read` returns a
  `Buf`, `.get`/`.lines` return `Str`).
- **`given`/`when`**, smartmatch `~~`, regexes `/.../` and grammars.
- **`react`/`whenever`**: an event loop in two keywords:

  ```raku
  react {
      whenever $proc.stdout { .print }        # each chunk of output
      whenever signal(SIGWINCH) { say "resized" }
      whenever Promise.in(5) { done }          # stop the loop
  }
  ```

  Each `whenever` subscribes to a `Supply` (or a `Promise` or `Channel`);
  the blocks run one at a time (no locking needed inside a `react`).
- **`start { ... }`**: run code on the thread pool, returning a `Promise`.
- **`LEAVE`** phaser: run code when a block is exited, however it is
  exited (return, exception). Ideal for restoring the terminal. `END`
  phasers run at program exit.
- **`CATCH`** blocks for exceptions; `try` to ignore one.
- **NativeCall**: `sub isatty(int32 --> int32) is native {*}` declares a
  C function from libc. More in chapter 17.

---

## 15. Raku: pipes and processes

Raku has two process APIs:

- `run` and `shell` return a `Proc`. They are synchronous: they start the
  child, connect pipes if you ask for them, and let you read and write
  through ordinary `IO::Handle`s. The exit status is available when the
  process has finished (closing its output handle waits for it).
- `Proc::Async` is the event-driven API. You subscribe to the child's
  output as `Supply`s, write to its stdin with methods that return
  `Promise`s, and get a `Promise` that is kept when the child exits.

Both go through libuv (MoarVM's event loop library), which affects one
detail you may notice: the "pipes" between Raku and its children are not
`pipe(2)` pipes but **Unix domain socket pairs**. We will see that in
15.3.

### 15.1 `run`: the basics

`run` takes the program and its arguments as a list. There is no shell
involved, so there is no quoting problem: each element is one `argv`
entry. Named arguments say which standard streams to capture: `:out`,
`:err`, `:in`, or `:merge` (stderr into stdout).

```raku
# file: raku/run_basic.raku
# run: synchronous process execution, with and without captured output.

# 1. Inherit stdin/stdout/stderr: like system(3) but without a shell.
my $p = run 'echo', 'hello from echo';
say "exit code: ", $p.exitcode;

# 2. Capture stdout (a pipe is created behind the scenes).
my $ls = run 'ls', '-1', '/usr/bin', :out;
my @lines = $ls.out.lines;          # reads until EOF
$ls.out.close;                       # closing also waits for the process
say "ls listed {+@lines} entries";

# 3. Capture both stdout and stderr, as separate pipes.
my $both = run 'sh', '-c', 'echo out; echo err >&2; exit 3', :out, :err;
my $out = $both.out.slurp(:close);
my $err = $both.err.slurp(:close);
say "out={$out.chomp} err={$err.chomp} exit={$both.exitcode}";

# 4. Merge stderr into stdout (like 2>&1).
my $merged = run 'sh', '-c', 'echo one; echo two >&2', :merge;
say "merged: ", $merged.out.slurp(:close).lines.join(',');

# 5. A failing command: the Proc is a failure in boolean context.
my $f = run 'false';
say "false succeeded? ", so $f;
say "exit code of false: ", $f.exitcode;

# 6. Feed stdin from a string.
my $sort = run 'sort', :in, :out;
$sort.in.say: $_ for <pear apple fig>;
$sort.in.close;                      # EOF for sort
say "sorted: ", $sort.out.slurp(:close).lines.join(' ');

# 7. The shell, when you need its syntax (beware of quoting!).
my $sh = shell 'echo $HOME | wc -c', :out;
say "length of \$HOME + newline: ", $sh.out.slurp(:close).trim;
```

Run it:

```text
$ raku raku/run_basic.raku
hello from echo
exit code: 0
ls listed 4103 entries
out=out err=err exit=3
merged: one,two
false succeeded? False
exit code of false: 1
sorted: apple fig pear
length of $HOME + newline: 10
```

Things to notice:

- Without `:out`, the child inherits our stdout: `echo`'s output appears
  directly, without going through Raku.
- `.out.lines` reads lazily until EOF. `.slurp(:close)` reads everything
  and closes the handle in one call. **Closing the output handle waits for
  the process** (like `pclose`), and only then is `.exitcode` meaningful.
- With both `:out` and `:err`, reading one completely and then the other
  can deadlock if the child fills the other pipe first (chapter 3, "the
  two-pipe deadlock"). Here the outputs are tiny, so it is fine. For
  anything large, use `Proc::Async`, which reads both at once.
- `so $proc` (boolean context) is `True` when the exit code is 0 and no
  signal killed the child.
- `shell` runs `/bin/sh -c` with one string. Use it only when you need
  shell syntax, and never interpolate untrusted data into it.

### 15.2 Failure is an exception, eventually

A `Proc` whose command failed is a "failure waiting to happen": if you
ignore it (put it in *sink* context), Raku throws `X::Proc::Unsuccessful`.

```raku
# file: raku/sinkfail.raku
# A Proc that failed throws when it is "sunk" (used in void context).
run 'ls', '/nonexistent';           # throws X::Proc::Unsuccessful
say "not reached";
CATCH {
    when X::Proc::Unsuccessful {
        say "caught: exit code ", .proc.exitcode;
    }
}
```

```text
$ raku raku/sinkfail.raku
ls: cannot access '/nonexistent': No such file or directory
caught: exit code 2
```

This is like `set -e` in the shell, but only for the commands whose
result you drop. Assigning the `Proc` to a variable (as `my $f = run
'false'` above) means you take responsibility for checking it.

### 15.3 Pipelines

To connect two children, pass the `.out` handle of the first as the
`:in` of the second:

```raku
# file: raku/pipeline.raku
# Build "ls -1 /usr/bin | grep zip | wc -l" without a shell.
# Passing one Proc's .out as the next one's :in connects them directly
# with a pipe: the data does not go through Raku.

my $ls   = run 'ls', '-1', '/usr/bin', :out;
my $grep = run 'grep', 'zip', :in($ls.out), :out;
my $wc   = run 'wc', '-l', :in($grep.out), :out;

say "matches: ", $wc.out.slurp(:close).trim;

# Check every stage, like "set -o pipefail".
for $ls, $grep, $wc -> $p {
    printf "%-5s exit %d\n", $p.command[0], $p.exitcode;
}
```

```text
$ raku raku/pipeline.raku
matches: 23
ls    exit 0
grep  exit 0
wc    exit 0
```

Does the data flow through Raku? It does not: Rakudo hands the file
descriptor of the first child's output to the second child as its
stdin. We can check, and see what kind of file it is, by asking the
children to describe their own descriptors:

```text
$ raku -e '
    my $a = run "sh", "-c", "readlink /proc/\$\$/fd/1 >&2; echo x", :out;
    my $b = run "sh", "-c", "readlink /proc/\$\$/fd/0 >&2; cat",
                :in($a.out), :out;
    say "raku has: ",
        dir("/proc/$*PID/fd").map(*.readlink).grep(/socket/).join(" ");
    print $b.out.slurp(:close);'
socket:[20064164]
socket:[20064163]
raku has: socket:[20064163] socket:[20064166]
x
```

The first child writes into socket 20064164; its peer, 20064163, is the
second child's stdin, and Raku also holds it (that is the `$a.out` handle).
So:

- The connection is direct, kernel to kernel, as in a shell pipeline.
- It is a **socket pair**, not a pipe. Programs rarely care, but a few do:
  `[ -p /dev/stdin ]` is false, `stat` reports a socket, and `splice(2)`
  tricks that require a pipe do not apply. Writing to a socket whose peer
  is closed still raises `SIGPIPE`, so pipeline semantics are preserved.
- Because Raku keeps a copy of the read end, the second child would not
  see EOF *because of Raku* if the first child's write end stayed open
  somewhere; here it does not matter since the write end is only in the
  first child. (In C, forgetting to close a write end in the parent is
  the classic pipeline hang, chapter 10.)

### 15.4 `Proc::Async` and `react`

`Proc::Async` gives you:

| Member | Type |
|--------|------|
| `.stdout` | `Supply` |
| `.stderr` | `Supply` |
| `.ready` | `Promise` |
| `.start` | `Promise` |
| `.write`, `.say` | `Promise` |
| `.close-stdin` | method |
| `.kill` | method |

- `.stdout` and `.stderr` emit `Str` chunks (or `Blob`s with `:bin`).
  `.stdout.lines` gives one line per emit.
- `.ready` is kept with the PID once the process is running.
- `.start` launches the process and returns a Promise kept with a `Proc`
  when it exits.
- `.write`/`.say` need `:w` in the constructor (to create the stdin pipe).

A `react` block with one `whenever` per event source is the idiomatic
way to drive it. This example reads stdout and stderr *at the same time*
(no deadlock), and enforces a timeout:

```raku
# file: raku/async_proc.raku
# Proc::Async: run a child, read stdout and stderr as they arrive,
# and enforce a timeout. No threads to manage, no deadlock.

my $proc = Proc::Async.new: 'sh', '-c', q:to/END/;
    for i in 1 2 3 4 5; do
        echo "tick $i"
        [ $i = 3 ] && echo "warning at 3" >&2
        sleep 0.3
    done
    END

my $timeout = @*ARGS[0] // 10;

react {
    whenever $proc.stdout.lines -> $line {
        say "OUT: $line";
    }
    whenever $proc.stderr.lines -> $line {
        say "ERR: $line";        # say, not note: see below
    }
    whenever $proc.ready -> $pid {
        say "started pid $pid";
    }
    whenever $proc.start -> $result {
        # $result is a Proc; .exitcode and .signal are filled in
        say "finished: exit {$result.exitcode} signal {$result.signal}";
        done;
    }
    whenever Promise.in($timeout) {
        say "timeout after {$timeout}s, sending SIGTERM";
        $proc.kill: SIGTERM;
    }
}
```

```text
$ raku raku/async_proc.raku
started pid 824368
OUT: tick 1
OUT: tick 2
OUT: tick 3
ERR: warning at 3
OUT: tick 4
OUT: tick 5
finished: exit 0 signal 0
$ raku raku/async_proc.raku 0.7
started pid 824487
OUT: tick 1
OUT: tick 2
OUT: tick 3
ERR: warning at 3
timeout after 0.7s, sending SIGTERM
finished: exit 0 signal 15
```

Why `say` for the error lines rather than `note` (which writes to
stderr)? Because Raku's stdout is **buffered when it is not a terminal**,
and stderr is not. If you redirect the output to a file or a pipe, `note`
lines would appear *before* the `say` lines that preceded them. We
wanted the demo's ordering to be readable in a pipe as well. This is the
stdio buffering problem of chapter 2, in Raku clothes.

Notes:

- The order of the `whenever`s does not matter: they are all set up
  before any event is processed, and their blocks run one at a time
  (a `react` is like a single-threaded event loop, even though the
  events arrive from other threads).
- `done` ends the `react` block. Without it, the block ends by itself
  when every `whenever` source is finished, which is often what you want
  but a timer like `Promise.in` keeps it alive.
- After a kill, `.exitcode` is 0 and `.signal` is the signal number:
  check both.

### 15.5 Talking to a coprocess

A *coprocess* is a child you write to and read from. The trap is
buffering on the child's side (chapter 3): many programs fully buffer
their output when stdout is a pipe, so your question goes out and the
answer stays in the child's buffer.

```raku
# file: raku/bidir.raku
# Talk to a coprocess through its stdin and stdout.
# The coprocess is a tiny Python calculator. "-u" makes its stdout
# unbuffered: without it, Python would keep the answers in its buffer
# (stdout is not a terminal) and we would wait forever. Chapter 3.

my $calc = Proc::Async.new: :w, 'python3', '-u', '-c', q:to/END/;
    import sys, math
    for line in sys.stdin:
        print(eval(line, vars(math)))
    END

my $answers = Channel.new;
$calc.stdout.lines.tap: { $answers.send: $_ };
my $done = $calc.start;
await $calc.ready;

for '2**64', '4*atan(1)', 'sqrt(2)', '7/3' -> $expr {
    await $calc.say: $expr;               # write returns a Promise
    say "$expr = ", $answers.receive;     # blocks until a line arrives
}

$calc.close-stdin;                         # EOF: the loop ends
say "calculator exited with ", (await $done).exitcode;
```

```text
$ raku raku/bidir.raku
2**64 = 18446744073709551616
4*atan(1) = 3.141592653589793
sqrt(2) = 1.4142135623730951
7/3 = 2.3333333333333335
calculator exited with 0
```

Remove the `'-u',` and the program hangs forever after the first
question (try it with `timeout 3 raku ...`): Python holds `2**64`'s
answer in its 8 KiB buffer, waiting for more output to fill it. The
cures are the ones from chapter 3: an option of the child (`-u`,
`--line-buffered`, `stdbuf -oL` for C programs that use stdio defaults),
or a PTY, which makes the child believe it talks to a terminal (chapter
17 and 30).

Two Raku idioms are worth noticing here: a `Channel` turns the
asynchronous `Supply` of answers into something you can `.receive` from
synchronously, and `await` on the write `Promise` makes sure each
question is sent before we wait for the answer.

### 15.6 Signals

In Raku, a signal is a `Supply`: `signal(SIGINT)` emits each time the
signal arrives. Subscribing to it installs a handler; until you subscribe,
the default action applies (for `SIGINT`, death).

```raku
# file: raku/signals.raku
# Signals as a Supply. Try ^C (SIGINT), or from another terminal:
#   kill -HUP <pid>   kill -USR1 <pid>   kill -TERM <pid>
say "pid $*PID; press ^C three times to quit";
my $count = 0;
react {
    whenever signal(SIGINT) {
        $count++;
        say "\ngot SIGINT #$count";
        done if $count >= 3;
    }
    whenever signal(SIGHUP, SIGUSR1) -> $sig {
        say "got $sig";                    # a Signal enum value
    }
    whenever signal(SIGTERM) {
        say "SIGTERM: cleaning up and exiting";
        done;
    }
    whenever Supply.interval(2) -> $n {
        say "still alive ($n)";
    }
}
say "bye";
```

```text
$ raku raku/signals.raku &
pid 826095; press ^C three times to quit
still alive (0)
$ kill -INT %1; kill -HUP %1; kill -USR1 %1
got SIGINT #1
got SIGHUP
got SIGUSR1
still alive (1)
$ kill -TERM %1
SIGTERM: cleaning up and exiting
bye
```

The handler code does not run in a signal handler context (MoarVM catches
the signal through libuv and queues an event), so you can do anything in
the `whenever` block: allocate, print, take locks. This is the self-pipe
trick of chapter 3, done for you.

### 15.7 SIGPIPE and the broken pipe

What happens when a Raku program writes into a pipe whose reader has
gone?

```text
$ raku -e 'loop { say "y" }' | head -2
y
y
Failed to write 8192 bytes to filehandle: Broken pipe
  in block <unit> at -e line 1

Unhandled exception: Failed to write 8192 bytes to filehandle: Broken pipe
   at SETTING::src/core.c/Exception.rakumod:715
   ...
```

MoarVM **ignores `SIGPIPE`**, so the `write` fails with `EPIPE` and Raku
throws an exception (chapter 3 explained both behaviours). The message
is ugly, and the exit status is 1, which a shell with `pipefail` will
report as an error. The C behaviour, "die quietly from `SIGPIPE`", is
what users expect from a filter.

Catching the exception is not quite enough: when the program then
exits, Raku flushes stdout's buffer, and that write fails again. The
reliable way out is `_exit(2)`, which ends the process without any
cleanup:

```raku
# file: raku/epipe.raku
# Behave like a well-mannered Unix filter when the reader goes away:
#   raku epipe.raku | head -3
# MoarVM ignores SIGPIPE, so a write to a closed pipe throws instead of
# killing us. Exiting normally would flush stdout's buffer again and
# throw again, so we leave with _exit(2), which skips all cleanup.
use NativeCall;
sub _exit(int32) is native {*}

for 1..* -> $n {
    say "line $n";
    CATCH {
        when .message.contains('Broken pipe') { _exit 0 }
    }
}
```

```text
$ raku raku/epipe.raku | head -3; echo "raku status: ${PIPESTATUS[0]}"
line 1
line 2
line 3
raku status: 0
```

(In zsh, use `${pipestatus[1]}`.) For a command-line tool that is meant
to be used in pipelines, this is worth the four lines.

### 15.8 Summary of the process API

| Need | Raku |
|------|------|
| run, wait | `run` |
| capture output | `run :out` |
| shell syntax | `shell` |
| pipeline | `:in($p.out)` |
| async I/O | `Proc::Async` |
| timeout | `Promise.in` |
| signals | `signal(...)` |
| exit status | `.exitcode` |
| killed by | `.signal` |

A few more things you may need:

- **Environment**: `run 'env', :env(%*ENV, FOO => 'bar')`. `%*ENV` is the
  process environment, modifiable in place.
- **Working directory**: `run 'ls', :cwd('/tmp')`.
- **Binary data**: `run ..., :out, :bin` gives `Blob`s instead of `Str`s.
  The default decoding is UTF-8; use `:enc<latin-1>` for other encodings.
- **Process ID and parent**: `$*PID`; there is no `getppid` built in, use
  NativeCall (chapter 17).
- **`fork`**: there is none, on purpose. MoarVM is multi-threaded (even a
  "single-threaded" Raku program has a spesh optimizer thread and an
  event loop thread), and `fork` in a multi-threaded process is only safe
  if the child immediately `exec`s. Starting processes always goes through
  libuv's `uv_spawn`, which does fork+exec in C. Chapter 17 deals with the
  consequence for PTYs.

---

## 16. Raku: terminals and termios

### 16.1 Is this a terminal?

`$*IN.t`, `$*OUT.t` and `$*ERR.t` return `True` if the handle is a
terminal (they call `isatty`):

```text
$ raku -e 'say $*IN.t, " ", $*OUT.t'
True True
$ raku -e 'say $*IN.t, " ", $*OUT.t' < /dev/null | cat
False False
```

Use this to decide whether to emit colors, show a progress bar, or
prompt the user, exactly as `ls` and `grep` do.

### 16.2 Term::termios

`Term::termios` (by Karl Rune Nilsen, bundled with Rakudo Star) is a thin
NativeCall binding of `tcgetattr`, `tcsetattr` and `cfmakeraw`, with
helpers to set and clear flags by name. The object *is* the C structure
(a `CStruct`), so `getattr` fills it in place.

| Method | C equivalent |
|--------|--------------|
| `.getattr` | `tcgetattr` |
| `.setattr(:NOW)` | `TCSANOW` |
| `.setattr(:DRAIN)` | `TCSADRAIN` |
| `.setattr(:FLUSH)` | `TCSAFLUSH` |
| `.makeraw` | `cfmakeraw` |
| `.set_lflags(...)` | `c_lflag \|=` |
| `.unset_lflags(...)` | `c_lflag &= ~` |

There are `set_`/`unset_` methods for the four flag words (`iflags`,
`oflags`, `cflags`, `lflags`), taking flag names as strings
(`<ECHO ICANON>`). The control characters are attributes:
`$t.cc_VMIN`, `$t.cc_VTIME`, `$t.cc_VINTR`, and so on.

The flag values come from a small C helper that the module compiles at
install time, so they are right for your platform. (Inside the module, a
Perl-style table of Linux values is used as a fallback.)

### 16.3 Showing raw keys

The Raku version of chapter 11's `rawkeys`:

```raku
# file: raku/rawkeys.raku
# Show the bytes each key sends, in raw mode. Press q to quit.
use Term::termios;

die "stdin is not a terminal\n" unless $*IN.t;

my $saved := Term::termios.new(fd => 0).getattr;   # := binds, no copy
my $raw   := Term::termios.new(fd => 0).getattr;
$raw.makeraw;                                      # cfmakeraw(3)
$raw.setattr(:FLUSH);

# Whatever happens (exception, ^C is off anyway), restore the terminal.
END $saved.setattr(:DRAIN);

print "raw mode: press keys, q quits\r\n";
loop {
    my $buf = $*IN.read(32);            # returns what one read(2) gave
    last unless $buf;
    my $hex  = $buf.list.fmt('%02x', ' ');
    my $text = (try $buf.decode('utf8')) // '(not UTF-8)';
    my $show = $text.comb.map({ .ord < 32 || .ord == 127
                                ?? '^' ~ chr(.ord +^ 64) !! $_ }).join;
    print "{$buf.elems} byte(s): $hex   $show\r\n";
    last if $buf.list eqv (0x71,);       # 'q'
}
print "bye\r\n";
```

```text
$ raku raku/rawkeys.raku
raw mode: press keys, q quits
1 byte(s): 61   a
3 byte(s): 1b 5b 41   ^[[A
1 byte(s): 03   ^C
2 byte(s): c3 a9   é
1 byte(s): 71   q
bye
```

Remarks:

- `:=` *binds* the termios objects. With `=`, it would also work (the
  object is a reference type), but binding makes it clear that we keep
  one object.
- `$*IN.read(32)` reads *up to* 32 bytes and returns what one `read(2)`
  call returns, which is what we want: one key, or one escape sequence
  (usually, see chapter 7).
- `END` runs at program exit, including after `die`. It does not run if
  the process is killed by a signal, which raw mode makes less likely
  (`^C` is just byte 3 now), but `kill` from elsewhere still can.
- In raw mode `OPOST` is off, so `"\n"` does not return the carriage:
  we print `"\r\n"`.

### 16.4 Reading a password

`$*IN.get` reads a line in canonical mode; turning `ECHO` off is all that
is needed:

```raku
# file: raku/getpass.raku
# Read a password without echo, like getpass(3).
use Term::termios;

sub getpass(Str $prompt = 'Password: ' --> Str) {
    my $tty = open '/dev/tty', :rw;      # the terminal, even if stdin is not
    my $fd  = $tty.native-descriptor;
    my $saved := Term::termios.new(:$fd).getattr;
    my $t     := Term::termios.new(:$fd).getattr;
    $t.unset_lflags(<ECHO>);
    $t.set_lflags(<ECHONL>);             # but do echo the final newline
    $t.setattr(:FLUSH);                  # also discards type-ahead
    LEAVE { $saved.setattr(:DRAIN); $tty.close }
    $tty.print($prompt);
    $tty.get;
}

my $pw = getpass();
say "you typed {$pw.chars} characters";
```

```text
$ raku raku/getpass.raku
Password:
you typed 7 characters
```

Opening `/dev/tty` instead of using `$*IN` is what `getpass(3)` does too:
it works even when stdin is redirected (`some-cmd | raku getpass.raku`)
because `/dev/tty` is the process's controlling terminal (chapter 5).
`LEAVE` restores the modes whichever way the sub is left.

### 16.5 A NativeCall helper module

Several things are not available in core Raku: the window size,
`ttyname`, process groups and sessions, `tcgetpgrp`. NativeCall makes them
one line each. Here is the helper module used by the rest of the Raku
chapters. Its last part, `fd-supply`, is explained in 17.2 and 17.3:

```raku
# file: raku/lib/Tty.rakumod
# Small NativeCall layer over the libc calls this tutorial needs.
# Constants are for Linux (x86_64 and aarch64); see chapter 17.
unit module Tty;
use NativeCall;

class Winsize is repr('CStruct') is export {
    has uint16 $.ws_row is rw;
    has uint16 $.ws_col is rw;
    has uint16 $.ws_xpixel is rw;
    has uint16 $.ws_ypixel is rw;
}

constant TIOCGWINSZ is export = 0x5413;
constant TIOCSWINSZ is export = 0x5414;
constant TIOCSCTTY  is export = 0x540E;

# ioctl is variadic in C; NativeCall needs one declaration per use.
sub ioctl-winsize(int32, ulong, Winsize --> int32)
    is native is symbol('ioctl') {*}

sub isatty(int32 --> int32) is native is export {*}
sub getpid(--> int32) is native is export {*}
sub getppid(--> int32) is native is export {*}
sub getpgrp(--> int32) is native is export {*}
sub getsid(int32 --> int32) is native is export {*}
sub tcgetpgrp(int32 --> int32) is native is export {*}
sub ttyname(int32 --> Str) is native is export {*}
sub strerror(int32 --> Str) is native {*}
sub errno-ptr(--> Pointer[int32]) is native is symbol('__errno_location') {*}

sub errno(--> Int) is export { errno-ptr().deref }
sub errstr(--> Str) is export { strerror(errno()) }

#| Return (rows, cols) of the terminal on fd, or Nil.
sub term-size(Int $fd = 1) is export {
    my $ws = Winsize.new;
    return Nil if ioctl-winsize($fd, TIOCGWINSZ, $ws) == -1;
    ($ws.ws_row, $ws.ws_col);
}

#| Set the window size of a terminal (typically a PTY master).
sub set-term-size(Int $fd, Int $rows, Int $cols) is export {
    my $ws = Winsize.new(ws_row => $rows, ws_col => $cols);
    ioctl-winsize($fd, TIOCSWINSZ, $ws) == -1
        and die "TIOCSWINSZ: {errstr}";
}

# ---- Reading a file descriptor without blocking a thread ----
class PollFd is repr('CStruct') {
    has int32 $.fd;
    has int16 $.events;
    has int16 $.revents;
}
constant POLLIN = 0x001;
sub poll(PollFd, uint64, int32 --> int32) is native {*}
sub native-read(int32, Buf, size_t --> ssize_t)
    is native is symbol('read') {*}

#| A Supply of the bytes that arrive on $fd. A timer checks the fd with
#| poll(2) and a zero timeout, and reads only when data is waiting, so no
#| thread ever sits blocked inside a native call (see 17.3 for why that
#| matters). The Supply is done at end of file or on error (EIO on a
#| PTY master whose slave side is closed everywhere).
sub fd-supply(Int $fd, Real :$every = 0.01 --> Supply) is export {
    supply {
        my $pfd = PollFd.new(:$fd, events => POLLIN);
        my $buf = Buf.new; $buf[4095] = 0;
        whenever Supply.interval($every) {
            while poll($pfd, 1, 0) > 0 {
                my $n = native-read($fd, $buf, 4096);
                if $n <= 0 { done }            # EOF (0) or error (-1)
                emit $buf.subbuf(0, $n);
            }
        }
    }
}
```

Some NativeCall points shown here:

- `is native` without a library name means "the C library and whatever
  is already loaded into the process".
- `is symbol('ioctl')` lets the Raku name differ from the C name. `ioctl`
  is variadic (`int ioctl(int fd, unsigned long request, ...)`), and
  NativeCall cannot call variadic functions generically: you declare one
  non-variadic signature per way you call it. On x86_64 and aarch64 Linux,
  calling a variadic function through a fixed signature works for these
  argument types (an assumption that holds for the common ABIs, but is
  not guaranteed by C).
- A `CStruct` class maps to a C `struct`; passing an object passes a
  pointer to it.
- `errno` is a thread-local variable in glibc, reached through
  `__errno_location()`. Read it immediately after the failed call: any
  other native call (or the VM itself) may change it.
- The `ioctl` request numbers (`TIOCGWINSZ` and friends) are Linux
  values. On macOS and the BSDs they differ (`TIOCGWINSZ` is
  `0x40087468` on macOS). A portable module would compute them with a
  small C helper at install time, as `Term::termios` does.

### 16.6 Window size and SIGWINCH

```raku
# file: raku/winsize.raku
# Print the terminal size now and each time it changes (SIGWINCH).
use lib $*PROGRAM.parent.add('lib');
use Tty;

my $fd = 1;
die "stdout is not a terminal\n" unless isatty($fd);
say "tty {ttyname($fd)}: {term-size($fd).join('x')} (rows x cols)";
say "resize the window; ^C to quit";
react {
    whenever signal(SIGWINCH) {
        say "SIGWINCH: now {term-size($fd).join('x')}";
    }
    whenever signal(SIGINT) { done }
}
```

```text
$ raku raku/winsize.raku
tty /dev/pts/13: 30x100 (rows x cols)
resize the window; ^C to quit
SIGWINCH: now 40x120
^C
```

`use lib $*PROGRAM.parent.add('lib')` adds the `lib` directory next to
the script to the module search path, so the script works from any
current directory.

### 16.7 Where am I? Sessions and process groups

```raku
# file: raku/ids.raku
# The process's place in the session/process-group hierarchy (chapter 5).
use lib $*PROGRAM.parent.add('lib');
use Tty;

my $tty = isatty(0) ?? ttyname(0) !! '(none)';
say "pid  {getpid}   ppid {getppid}";
say "pgid {getpgrp}   sid  {getsid(0)}";
say "tty  $tty";
if isatty(0) {
    my $fg = tcgetpgrp(0);
    say "foreground pgid of the tty: $fg ",
        ($fg == getpgrp() ?? '(us: we are in the foreground)' !! '(not us)');
}
```

```text
$ raku raku/ids.raku
pid  829506   ppid 829505
pgid 829506   sid  829505
tty  /dev/pts/13
foreground pgid of the tty: 829506 (us: we are in the foreground)
$ raku raku/ids.raku < /dev/null &
pid  829537   ppid 829503
pgid 829537   sid  829503
tty  (none)
```

Compare with the C version in chapter 5: same system calls, same
answers. Note `getpgrp()` with parentheses: a bare `getpgrp ??` would be
parsed as a call with arguments (Raku subs are list operators), and the
compiler complains.

---

## 17. Raku: pseudo-terminals through NativeCall

There is no PTY module in Rakudo Star, so we build one. The C functions
are easy to reach with NativeCall. The hard part is the child.

### 17.1 The problem with fork

In C (chapter 12), the child side of a PTY is set up between `fork` and
`exec`: `setsid()`, `ioctl(slave, TIOCSCTTY)`, `dup2` the slave onto 0,
1 and 2. Raku cannot run code there:

- There is no `fork` in Raku.
- Calling `fork()` through NativeCall would clone a multi-threaded
  virtual machine into a child where only one thread exists. Any lock held
  by another thread at that instant (in the allocator, the GC, the event
  loop) stays locked forever in the child. POSIX allows only
  async-signal-safe calls in that situation, and running Raku code is
  certainly not one of them.
- `forkpty` through NativeCall has the same problem: in the child, it
  returns into the VM.

So the child must be started by libuv (`run` or `Proc::Async`), and
something must make the slave its controlling terminal. Two solutions:

1. **A helper program** that does `setsid` + `TIOCSCTTY` and then execs
   the real command. util-linux ships one: `setsid --ctty` (`-c`), which
   "sets the controlling terminal to the current one", that is, to its
   stdin. So we start `setsid -c cmd args...` with stdin, stdout and
   stderr bound to the slave.
2. **A small C library** with a `spawn_on_pty` function that does
   fork+exec in C and is called through NativeCall. Fork-then-exec from
   C is fine (that is what libuv does), as long as the child calls only
   async-signal-safe functions before `exec`.

We use solution 1, and leave 2 as exercise E.17. On macOS and the BSDs,
which lack util-linux's `setsid`, solution 2 (or `script -q /dev/null
cmd`) is the way.

### 17.2 The Pty class

The master side: `posix_openpt`, `grantpt`, `unlockpt`, `ptsname`, then
`read` and `write` on the master fd. The slave side: Raku opens
`/dev/pts/N` by name, which gives a normal `IO::Handle` that
`Proc::Async` can bind to the child's standard streams.

```raku
# file: raku/lib/Pty.rakumod
# A pseudo-terminal for Raku, using NativeCall for the master side and
# Proc::Async to start the child on the slave side (chapter 17).
use NativeCall;
use Tty;
unit class Pty;

constant O_RDWR   = 0o2;
constant O_NOCTTY = 0o400;

sub posix_openpt(int32 --> int32) is native {*}
sub grantpt(int32 --> int32)      is native {*}
sub unlockpt(int32 --> int32)     is native {*}
sub ptsname(int32 --> Str)        is native {*}
sub native-write(int32, Blob, size_t --> ssize_t)
    is native is symbol('write') {*}
sub native-close(int32 --> int32) is native is symbol('close') {*}

has Int $.master;           # master fd (a plain integer)
has Str $.slave-name;       # e.g. /dev/pts/7
has Proc::Async $.proc;
has Supply $!output;
has Promise $.exited;

#| Open a PTY pair and start @cmd on the slave side.
method spawn(*@cmd, Int :$rows = 24, Int :$cols = 80) {
    my $m = posix_openpt(O_RDWR +| O_NOCTTY);
    die "posix_openpt: {errstr}" if $m < 0;
    grantpt($m) == 0 && unlockpt($m) == 0
        or die "grantpt/unlockpt: {errstr}";
    my $name = ptsname($m);
    set-term-size($m, $rows, $cols);

    # The child: "setsid -c" (util-linux) makes a new session and
    # makes its stdin, the slave, the controlling terminal. This is
    # the setsid() + ioctl(TIOCSCTTY) of chapter 6, done by a tiny
    # helper, because forking a running MoarVM is not safe.
    my $slave = open $name, :rw;
    my $proc = Proc::Async.new('setsid', '-c', |@cmd);
    $proc.bind-stdin($slave);
    $proc.bind-stdout($slave);
    $proc.bind-stderr($slave);

    my $self = self.bless(master => $m, slave-name => $name,
                          proc => $proc);
    $self!start($slave);
    $self;
}

method !start($slave) {
    $!exited = $!proc.start;
    await $!proc.ready;
    $slave.close;            # only the child keeps the slave open now
    # An on-demand Supply: polling starts when it is tapped, so no byte
    # can be emitted before someone listens. Tap it once (see 17.3).
    $!output = fd-supply($!master);
}

#| Output of the child, as a Supply of Blobs (bytes).
method output(--> Supply) { $!output }

#| Send bytes or text to the child, as if typed.
multi method write(Blob $b) { native-write($!master, $b, $b.elems) }
multi method write(Str $s)  { self.write($s.encode) }

method resize(Int $rows, Int $cols) {
    set-term-size($!master, $rows, $cols);   # the kernel sends SIGWINCH
}

method close { native-close($!master) }
```

`self.bless` is how a Raku class method constructs an object from its
attributes, after preparing them (here: after opening the PTY).

The master fd is a plain integer, not an `IO::Handle`: Raku has no
public way to wrap an existing file descriptor in a handle (opening
`/proc/self/fd/N` does not help: for `/dev/ptmx` it would allocate a
*new* PTY). So reading and writing go through NativeCall `read` and
`write`, and reading is turned into a `Supply` by `fd-supply`, the last function
of the `Tty` module:

```raku
# (the end of raku/lib/Tty.rakumod, listed in full in 16.5)
sub fd-supply(Int $fd, Real :$every = 0.01 --> Supply) is export {
    supply {
        my $pfd = PollFd.new(:$fd, events => POLLIN);
        my $buf = Buf.new; $buf[4095] = 0;
        whenever Supply.interval($every) {
            while poll($pfd, 1, 0) > 0 {
                my $n = native-read($fd, $buf, 4096);
                if $n <= 0 { done }            # EOF (0) or error (-1)
                emit $buf.subbuf(0, $n);
            }
        }
    }
}
```

Every 10 ms, it asks `poll(2)` (with a timeout of zero: never wait)
whether data is waiting, and reads it if so. Why not simply a thread
that blocks in `read`? The next section tells the story.

### 17.3 A war story: blocking native calls

The first version of this class started a thread with `start { loop {
native-read(...) } }`, blocking in `read(2)` until output arrived. It
worked in simple tests. Then the `script` clone of 17.5 hung, but only
sometimes:

- with `whenever signal(SIGWINCH)` in its `react` block, never finishing;
- without it, finishing fine;
- when stdin was a terminal (another thread blocked in `$*IN.read`),
  hanging at exit;
- when stdin was a pipe at EOF, finishing.

The common factor: **a thread sitting inside a blocking native call
while the rest of the program allocates memory**. MoarVM's garbage
collector is "stop the world": when a collection is needed, every thread
must reach a safe point and cooperate. A thread inside a long native call
cannot cooperate until the call returns. (MoarVM does mark threads as
"blocked" around its *own* blocking operations, like waiting on a lock,
so that the collector can proceed without them; our reading of the
symptoms, which we have not confirmed in the MoarVM source, is that a
NativeCall `read` that never returns, or a blocking `$*IN.read` in some
code paths, is not always treated that way.) Setting up a signal
handler allocates, triggers a collection, and the whole VM waits for a
thread that is waiting for data that will never come.

Polling with a zero timeout avoids the question entirely: no thread
ever waits in native code. The cost is latency (up to 10 ms, invisible
to a human) and a few hundred cheap system calls per second while
running. Rakudo's own async I/O (sockets, `Proc::Async`, files) does not
have this problem, because libuv waits in its single event-loop thread,
which MoarVM knows about.

We found three more details along the way:

- `IO::Handle.Supply` on `$*IN` (`$*IN.Supply(:bin, :size(1024))`) is
  not a substitute: it is meant for reading files in chunks, and on a pipe
  it waited for end of file before emitting anything.
- When a thread emits into a `Supplier` *while a `react` block is still
  subscribing to its sources*, events can be lost (a `Supplier` does not
  remember emits before a tap), and in our tests it also deadlocked with
  a `signal` subscription. `Supplier::Preserving` buffers early values;
  `fd-supply` avoids the issue by being an on-demand `supply` block,
  which starts polling only when tapped.
- The same race came back in a subtler form. A first version of
  `Pty!start` stored `fd-supply($!master).share`, so that several
  subscribers could see the output. `.share` turns the on-demand supply
  into a *live* one, and `Supply.interval` emits its first tick
  immediately, on another thread. In about one run out of three, that
  tick read the child's output, and sometimes the end of file too,
  before the `whenever` of `ptyspawn.raku` was attached. The output was
  lost, and when the `done` was lost as well the program hung forever.
  Tracing with `note` made it vanish (the extra output changed the
  timing), but running the program 20 times in a loop caught it. Without
  `.share`, the failure rate in 40 runs dropped from about 30% to zero.
  The price: tap `$pty.output` only once; two taps would start two
  pollers that steal bytes from each other.

Takeaway for any Raku program that calls into C: **keep native calls
short**. If a C function may block, call it with a timeout in a loop, or
use a non-blocking variant, or do the waiting in a separate process.

### 17.4 Spawning a command on a PTY

```raku
# file: raku/ptyspawn.raku
# Run a command on a new PTY and show what it writes, escaped.
use lib $*PROGRAM.parent.add('lib');
use Pty;

my @cmd = @*ARGS ?? @*ARGS !! ('sh', '-c', 'tty; stty size; ls --color=auto -d /');
my $pty = Pty.spawn(|@cmd, rows => 30, cols => 100);
say "child on {$pty.slave-name}";

my $total = 0;
my ($status, $eof);
react {
    # The child may exit before we have read all of its output (it is
    # still in the master's buffer): finish only when both have happened.
    whenever $pty.output -> $blob {
        $total += $blob.elems;
        print visible($blob);
        LAST { $eof = True; done if $status.defined }
    }
    whenever $pty.exited -> $proc {
        $status = $proc.exitcode;
        done if $eof;
    }
}
say "\n[exit code $status; $total bytes]";

#| Make control characters visible, keeping newlines.
#| Note: "\r\n" is ONE grapheme in Raku, so it is handled first.
sub visible(Blob $b --> Str) {
    $b.decode('utf8-c8')
      .subst("\r\n", "^M\n", :g)
      .subst(/<[\x00..\x09 \x0b..\x1f]>/, { '^' ~ chr(.Str.ord +^ 64) }, :g)
}
```

```text
$ raku raku/ptyspawn.raku
child on /dev/pts/13
/dev/pts/13^M
30 100^M
^[[0m^[[01;34m/^[[0m^M

[exit code 0; 40 bytes]
$ raku raku/ptyspawn.raku python3 -c 'import sys; print(sys.stdin.isatty(), sys.stdout.isatty())'
child on /dev/pts/13
True True^M

[exit code 0; 11 bytes]
```

Everything from chapter 6 is visible: `tty` names the slave, `stty size`
reports the size we set on the master, `ls --color=auto` colors its
output because stdout is a terminal, and every newline arrives as
`\r\n` (`^M` then newline) because the slave's line discipline has
`OPOST` and `ONLCR` on.

Two Raku-specific details:

- **`"\r\n"` is one character in Raku.** Raku strings are sequences of
  *graphemes*, and Unicode defines CR LF as a single grapheme cluster. So
  a regex for `\r` does not match inside `"\r\n"`, `.chars` counts it as
  one, and `.comb` returns it as one element. `visible` therefore
  replaces `"\r\n"` first. Work on `Blob`s (bytes) when exact bytes
  matter.
- **`utf8-c8`** is a Rakudo encoding that decodes UTF-8 but keeps
  invalid bytes (as special graphemes) instead of throwing. Terminal
  output may cut a multi-byte character across two reads, or contain
  binary junk; plain `utf8` decoding would die on it.
- The `react` block ends only when **both** the output is finished (EIO
  on the master) and the process has exited. Either can happen first:
  the child may exit while its last output is still in the master's
  buffer.

### 17.5 `script` in Raku

Now the full relay: our terminal in raw mode, keys to the child, output
to the screen and to a log, window size changes forwarded.

```raku
# file: raku/ptyscript.raku
# A small script(1): run a shell on a PTY, relay the keyboard to it and
# its output to the screen, and record the output in a log file.
#   raku ptyscript.raku [-o LOGFILE] [COMMAND ARGS...]
use lib $*PROGRAM.parent.add('lib');
use Term::termios;
use Tty;
use Pty;

sub MAIN(*@cmd, Str :o(:$log) = 'typescript') {
    @cmd ||= %*ENV<SHELL> // '/bin/sh';
    my $interactive = isatty(0).Bool;
    my ($rows, $cols) = $interactive ?? term-size(0) !! (24, 80);

    my $pty = Pty.spawn(|@cmd, :$rows, :$cols);
    my $logfh = open $log, :w, :bin;
    note "Script started, output log file is '$log'.";

    # Our own terminal goes raw: every key goes to the child unchanged,
    # including ^C and ^Z, which the child's line discipline interprets.
    my $saved;
    if $interactive {
        $saved = Term::termios.new(fd => 0).getattr;
        Term::termios.new(fd => 0).getattr.makeraw.setattr(:FLUSH);
    }
    LEAVE { $saved.setattr(:DRAIN) if $saved }     # also on exceptions

    my ($status, $eof);
    $*OUT.out-buffer = False;            # write through, we are a relay
    react {
        whenever fd-supply(0) -> $keys {
            $pty.write($keys);
            LAST { $pty.write("\x04") }          # our stdin hit EOF: send ^D
        }
        whenever $pty.output -> $blob {
            $*OUT.write($blob);
            $logfh.write($blob);
            LAST { $eof = True; done if $status.defined }
        }
        whenever signal(SIGWINCH) {
            $pty.resize(|term-size(0)) if $interactive;
        }
        whenever $pty.exited -> $proc {
            $status = $proc.exitcode;
            done if $eof;
        }
    }
    $logfh.close;
    $saved.setattr(:DRAIN) if $saved;
    $saved = Nil;
    note "Script done, exit status $status.";
    exit $status;
}
```

A test where stdin is not a terminal (the commands come from a pipe):

```text
$ printf 'echo hello from $(tty)\nstty size\nexit 3\n' |
    raku raku/ptyscript.raku -o log.txt sh
Script started, output log file is 'log.txt'.
sh-5.3$ echo hello from $(tty)
hello from /dev/pts/13
sh-5.3$ stty size
24 80
sh-5.3$ exit 3
exit
Script done, exit status 3.
$ echo $?
3
```

And interactively, in a 33x90 terminal, typing `stty size`, then
`sleep 10` interrupted by `^C`, then `exit 4`:

```text
$ raku raku/ptyscript.raku -o log2.txt sh
Script started, output log file is 'log2.txt'.
sh-5.3$ stty size
33 90
sh-5.3$ sleep 10
^C
sh-5.3$ exit 4
exit
Script done, exit status 4.
```

How it works:

- `sub MAIN` turns the signature into a command-line parser: `*@cmd`
  collects the positional arguments, `Str :o(:$log)` accepts `-o FILE`
  and `--log=FILE`. `raku ptyscript.raku --help` prints a usage message
  generated from the signature. (Options must come before the positional
  arguments, unlike GNU tools.)
- `^C` reached `sleep` through the child's line discipline: our terminal
  is raw, so byte 3 went to the master, and the *slave's* `ISIG` turned it
  into `SIGINT` for the foreground process group of the slave's session.
  This is the PTY version of chapter 5's job control, and it is why a
  `script` (or `ssh`, or `tmux`) must put its own terminal in raw mode.
- When our stdin reaches EOF (pipe case), we send `^D` (byte 4) to the
  child, which its line discipline turns into EOF for the shell. Plain
  `close` of the master would hang up the child instead (`SIGHUP`).
- `$*OUT.out-buffer = False`: a relay must not keep output in a buffer.
- `LEAVE` restores our terminal whatever happens, even an exception.
  Setting `$saved = Nil` after the explicit restore avoids restoring
  twice.

### 17.6 Is the log faithful?

The log contains exactly the bytes the child wrote, escapes included. We
will analyze it with `Terminal::ANSIParser` in 18.4. Replay it with `cat
log.txt` in a terminal of the same size and you see the session again
(without the timing, see exercise E.13).

---

## 18. Raku: TUIs with the Terminal modules

Rakudo Star comes with a family of terminal modules. They are mostly
pure Raku, which makes them easy to read, and they cover the layers of
chapter 7:

- **Terminal::ANSIColor**: SGR attributes and colors, as functions and
  markup.
- **Terminal::ANSI**: cursor movement, scrolling regions, alternate
  screen, with an optional "virtual screen".
- **Terminal::ANSIParser**: a byte- or codepoint-level parser of VT
  sequences, built from the DEC state machine at vt100.net.
- **Terminal::LineEditor**: a pure-Raku line editor with history.
- **Terminal::UI**: panes, frames, key bindings, scrolling lists.
- **Terminal::Capabilities**: what the terminal supports (colors,
  symbols), from `$TERM` and friends.
- **Readline**: a NativeCall binding to GNU Readline.

### 18.1 Colors: Terminal::ANSIColor

```raku
# file: raku/colors.raku
use Terminal::ANSIColor;

say colored('error', 'bold red');             # attribute + color
say colored('note',  'black on_yellow');      # background with on_
say colored('256',   '208');                  # 256-color palette index
say colored('rgb',   '255,105,180');          # 24-bit color
say colored('under', 'underline'), ' plain';

# Without wrapping: color() returns the escape sequence only
print color('green'), 'green text', color('reset'), "\n";

# Strip escapes, e.g. to compute the visible width
say colorstrip(colored('abc', 'red')).chars;  # 3
```

```text
$ raku raku/colors.raku | cat -v
^[[1;31merror^[[0m
^[[30;43mnote^[[0m
^[[38;5;208m256^[[0m
^[[38;2;255;105;180mrgb^[[0m
^[[4munder^[[0m plain
^[[32mgreen text^[[0m
3
```

The attribute names are the classic Perl `Term::ANSIColor` ones: the 8
basic colors, `on_` backgrounds, `bold`, `faint`, `italic`,
`underline`, `inverse`, `strike`, numbers for 256 colors, triples for
24-bit color. There are no `bright_` names in this version (use the
numbers 8 to 15 of the 256-color palette instead, for example `'9'` for
bright red).

Decide whether to use colors with `$*OUT.t` and the `NO_COLOR`
convention (no-color.org): if the environment variable `NO_COLOR` is set
and not empty, do not color.

### 18.2 Cursor control: Terminal::ANSI

Terminal::ANSI's functions *print* their sequence (they do not return
it; most return `True`, which is the first trap: `print
start-of-line()` prints "True"). To get the strings instead, wrap calls
in `tget { ... }`. Here is a multi-line progress display, with three
threads drawing concurrently:

```raku
# file: raku/progress.raku
# Three concurrent "downloads", each with its own progress bar line,
# drawn with Terminal::ANSI and colored with Terminal::ANSIColor.
use Terminal::ANSI;
use Terminal::ANSIColor;

my @names = <alpha beta gamma>;
my $width = 40;

hide-cursor;
END show-cursor;                    # always give the cursor back
signal(SIGINT).tap: { show-cursor; print "\n"; exit 130 }

print "\n" x @names;                # reserve one line per task
cursor-up(+@names);
save-cursor;                        # remember where line 0 is

my $lock = Lock.new;                # several threads draw: serialize
sub draw(Int $row, Str $name, Real $frac) {
    $lock.protect: {
        restore-cursor;
        cursor-down($row) if $row;
        my $done = ($frac * $width).Int;
        start-of-line;               # these subs print; they return Bool
        print sprintf('%-6s ', $name),
              colored('█' x $done, 'green'),
              colored('░' x ($width - $done), 'faint'),
              sprintf(' %3d%%', $frac * 100),
              "\e[K";                   # erase to end of line (see text)
    }
}

await @names.kv.map: -> $i, $name {
    start {
        my $speed = (0.01, 0.02, 0.035)[$i];
        for 0..100 -> $p {
            draw($i, $name, $p / 100);
            sleep $speed;
        }
    }
}
restore-cursor;
cursor-down(+@names);
say colored('all done', 'bold');
```

```text
$ raku raku/progress.raku
alpha  ████████████████████████████████████████ 100%
beta   ████████████████████████████████████████ 100%
gamma  ████████████████████████████████████████ 100%
all done
```

Points to notice:

- **`erase-to-end-of-line` is buggy** in Terminal::ANSI 0.0.24: it sends
  `ESC [ 2 J`, which erases the *whole screen*, instead of `ESC [ K`. The
  demo prints `"\e[K"` itself. Always look at the bytes your library
  sends (`| cat -v`, or the logger of chapter 32) when the screen does
  something strange.
- `save-cursor`/`restore-cursor` use `CSI s` / `CSI u` (the SCO
  variants). They are widely supported, but `ESC 7` / `ESC 8` (DEC) are
  the more portable pair.
- Several threads print: the `Lock` makes each "move cursor, draw line"
  sequence atomic. Without it, one thread's cursor movement interleaves
  with another's drawing and the bars end up on the wrong lines.
- The cursor is hidden while drawing and restored in an `END` block and
  on `SIGINT`. A program that hides the cursor and dies leaves the user
  without a cursor (`tput cnorm` or `reset` brings it back).

### 18.3 A line editor: Terminal::LineEditor

`Terminal::LineEditor` (by Geoffrey Broadwell) is a readline-like line
editor written in Raku. A Rakudo with the REPL support for it uses it
when it is the only line-editing module installed, or when
`RAKUDO_LINE_EDITOR=LineEditor` is set.

```raku
# file: raku/lineedit.raku
# A REPL-like loop with line editing and history, in pure Raku.
# Keys: arrows, Home/End, ^A ^E ^K ^U ^W, Up/Down for history, ^D quits.
use Terminal::LineEditor;
use Terminal::LineEditor::RawTerminalInput;

my $history = $*HOME.add('.lineedit-demo-history');
my $cli = Terminal::LineEditor::CLIInput.new;
$cli.load-history($history) if $history.e;

loop {
    my $in = $cli.prompt('calc> ');
    last without $in;                         # ^D on an empty line
    next unless $in.trim;
    $cli.add-history($in);
    # Evaluate simple arithmetic only: digits, operators, parentheses.
    if $in ~~ /^ <[\d\s+\-*/().]>+ $/ {
        say (try $in.EVAL) // "error: {$!.message}";
    }
    else {
        say "only arithmetic, please";
    }
}
$cli.save-history($history);
say "\nbye";
```

```text
$ raku raku/lineedit.raku
calc> 1+2
3
calc> 6*7
42
calc> foo
only arithmetic, please
calc> 6+1          (Up twice recalls "6*7", two backspaces, "+1")
7
calc> ^D
bye
```

How does it know the terminal width and where the prompt ends? It
*asks the terminal*. Look at the first bytes it writes:

```text
calc> ^[[6n^[7^[[9999;9999H^[[6n^[8
```

- `ESC [ 6 n` is the **cursor position report** request (DSR 6). The
  terminal answers with `ESC [ row ; col R` *on the input side*, as if
  typed.
- `ESC 7`, `ESC [ 9999 ; 9999 H`, `ESC [ 6 n`, `ESC 8`: save the cursor,
  move it far beyond the bottom right corner (the terminal clamps it to
  the last row and column), ask where it is (that is the size!), and
  restore the cursor. This trick works over serial lines and `ssh`
  without `TIOCGWINSZ`.

This has consequences for testing: a program driven through a PTY by
another program (chapter 30) will **hang waiting for the answer** unless
the driver answers. We hit exactly that while testing this chapter, and
the test driver now replies `ESC [ 24 ; 80 R` to a query that follows a
move to 9999;9999, and `ESC [ 5 ; 1 R` to the others. Real terminals,
`tmux` and `screen` all answer; some minimal emulators do not.

Inside, the module has a `start` thread that reads `$*IN` one byte at a
time, a parser (Terminal::ANSIParser) that turns bytes into keys and
query answers, and a decoder `react` that dispatches them. Reading the
module (`zef locate Terminal::LineEditor`) is a good lesson in structuring
a terminal input layer.

If you prefer the real GNU Readline (with your `~/.inputrc` bindings, vi
mode, and so on), the `Readline` module wraps it:

```raku
# file: raku/readline.raku
use Readline;
my $rl = Readline.new;
while $rl.readline('rl> ') -> $line {
    $rl.add-history($line);
    say "GOT [$line]";
}
say "\nbye";
```

GNU Readline does the raw mode, the editing, and the bracketed paste
mode (`ESC [ ? 2004 h` before the prompt, `ESC [ ? 2004 l` after): the
same sequences we saw from bash in 17.5, since bash uses Readline too.

### 18.4 Parsing what programs send: Terminal::ANSIParser

To *understand* terminal output (in a test, a recorder, a terminal
emulator), you need a parser that splits a byte stream into text and
control sequences, robustly, even when a sequence is cut in the middle.
`Terminal::ANSIParser` implements the state machine described by Paul
Flo Williams at vt100.net, which is what real VT terminals do.

`make-ansi-parser` returns a closure; feed it one codepoint (or one byte,
with `:raw-bytes`) at a time, and it calls your `emit-item` with plain
codepoints (`Int`) and sequence objects (`CSI`, `OSC`, `DCS`,
`SimpleEscape`, ...). Feeding the undefined `Int` signals the end of
input.

```raku
# file: raku/ansistats.raku
# Parse a terminal recording (a typescript) with Terminal::ANSIParser and
# report which escape sequences it contains, and its plain text.
#   raku ansistats.raku typescript
use Terminal::ANSIParser;

sub MAIN(Str $file, Bool :$text) {
    my %count;
    my $plain = '';
    my &parse := make-ansi-parser(emit-item => -> $item {
        given $item {
            when Terminal::ANSIParser::CSI          { %count{"CSI  " ~ .Str.substr(2)}++ }
            when Terminal::ANSIParser::OSC          { %count{"OSC  " ~ .Str.substr(2, 10)}++ }
            when Terminal::ANSIParser::SimpleEscape { %count{"ESC  " ~ .Str.substr(1)}++ }
            when Terminal::ANSIParser::Sequence     { %count{.^name.split('::')[*-1]}++ }
            when Int:D                              { $plain ~= chr($_) }
        }
    });
    parse($_) for $file.IO.slurp.ords;      # one codepoint at a time
    parse(Int);                     # end of input: flush, emits Int too

    say "sequences:";
    printf "  %5d  %s\n", .value, .key.raku.substr(1, *-1)
        for %count.sort(-*.value);
    say "\nplain text:\n", $plain.subst("\r\n", "\n", :g) if $text;
}
```

On the log recorded by our `script` clone in 17.5:

```text
$ raku raku/ansistats.raku --text log2.txt
sequences:
      3  CSI  ?2004l
      2  CSI  ?2004h

plain text:
stty size
33 90
sh-5.3$ sleep 10
^C
sh-5.3$ exit 4
exit
```

(Bash prints `?2004h`, bracketed paste on, before each prompt, and
`?2004l` when a command line is accepted.)

A small catch, discovered by running the code: when the parser is
flushed with `parse(Int)`, it emits the undefined `Int` too, so a `when
Int` branch must be written `when Int:D` (defined integers only), or
`chr` fails on the type object. In Raku, `Int` in a signature or a smart
match accepts both defined values and the type object; `:D` and `:U`
restrict to one or the other. You will meet this constantly.

### 18.5 Panes and lists: Terminal::UI

`Terminal::UI` (by Brian Duggan) provides a screen of frames divided
into panes, each pane a scrollable list of lines that can be selected,
with key bindings and callbacks. It uses the alternate screen and restores
everything at shutdown.

```raku
# file: raku/peek.raku
# A two-pane file viewer with Terminal::UI.
#   raku peek.raku [DIR]
# j/k or arrows move, Enter shows the file, Tab switches pane,
# h shows the help, q quits.
use Terminal::UI 'ui';

sub MAIN(Str $dir = '.') {
    ui.setup: ratios => (1, 2);               # top third, bottom two thirds
    my ($list, $view) = ui.panes;

    for dir($dir).sort -> $path {
        my $kind = $path.d ?? '/' !! '';
        $list.put: $path.basename ~ $kind, meta => %( :$path );
    }

    # Enter on a line of the top pane: show the file in the bottom pane.
    $list.on: select => -> :%meta {
        my $path = %meta<path>;
        $view.clear;
        if $path.d {
            $view.put: "[directory with {$path.dir.elems} entries]";
        }
        else {
            my @lines = (try $path.lines.head(200)) // ("[cannot read: $!]",);
            $view.put($_) for @lines;
        }
    };

    ui.interact;           # the key loop; returns when q is pressed
    ui.shutdown;           # leave the alternate screen, restore the tty
}
```

```text
$ raku raku/peek.raku demo
┌──────────────────────────────────────────────────────────────────────────────┐
│a.txt                                                                         │
│b.txt                                                                         │
│sub/                                                                          │
│                                                                              │
├──────────────────────────────────────────────────────────────────────────────┤
│second file                                                                   │
│                                                                              │
...
└──────────────────────────────────────────────────────────────────────────────┘
```

(`demo` contains two small files and a directory; we pressed `j` to
select `b.txt`, then Enter.)

The model:

- `use Terminal::UI 'ui'` exports a ready-made `ui` object.
- `ui.setup` creates the screen. `:2panes` splits it evenly; `ratios =>
  (1, 2)` gives proportions; `heights => [...]` gives exact heights.
- `$pane.put($line, meta => %(...))` appends a line and attaches data
  to it. The `select` callback receives the current line's metadata if
  it declares a `:%meta` named parameter (the module inspects the
  callback's signature to decide what to pass).
- `ui.interact` runs the key loop (a `react` over the key `Supply`)
  until `q`; `ui.shutdown` restores the terminal.
- Callbacks registered with `.on` run in a separate thread (`start`);
  `.on-sync` runs them in the key loop.

### 18.6 Detecting capabilities: Terminal::Capabilities

```raku
# file: raku/caps.raku
use Terminal::Capabilities;
use Terminal::Capabilities::Autodetect;

my ($caps, $terminal, $version) = terminal-env-detect;
say "terminal: $terminal ", $version // '';
say "symbol set: ", $caps.symbol-set;
say "256 colors: ", $caps.color8bit;
say "24-bit color: ", $caps.color24bit;
say "emoji: ", $caps.emoji-text;
```

It guesses from `$TERM`, `$COLORTERM`, `$TERM_PROGRAM` and other
variables, because a program cannot easily ask a terminal what it
supports (the query-and-answer technique of 18.3 exists for some
features, but many terminals do not answer, so a program must wait with
a timeout). Use it to choose between ASCII, box drawing and full Unicode
symbols, or between 16, 256 and 24-bit colors.

### 18.7 Raku: summary

| Topic | Raku tool |
|-------|-----------|
| processes | `run`, `Proc::Async` |
| events | `react`/`whenever` |
| termios | `Term::termios` |
| syscalls | NativeCall |
| PTY | NativeCall + `setsid -c` |
| colors | `Terminal::ANSIColor` |
| cursor | `Terminal::ANSI` |
| parsing | `Terminal::ANSIParser` |
| line edit | `Terminal::LineEditor` |
| TUI | `Terminal::UI` |

Raku's strengths here are the event model (`react` makes PTY relays and
process supervision short and correct) and NativeCall, which makes any
libc function one line away. Its weaknesses are the startup time, the
lack of `fork` (by design), the need to be careful with blocking native
calls (17.3), and a smaller, less polished module ecosystem: we found and
worked around one bug (18.2) and two traps (18.3, 18.4) in a single
chapter. Read the source of the modules you use; it is short and clear.

---

## 19. Rust: the ecosystem

Rust is a compiled systems language with C's level of control and a type
system that rules out whole classes of bugs (use after free, data races,
forgetting to close a file descriptor). For our topic it has a strong
standard library for processes, and a few excellent crates for the rest:
`nix` for POSIX calls, `crossterm` for terminals, `ratatui` for full
screen interfaces.

### 19.1 Installing: rustup

The usual way to install Rust is **rustup**, the toolchain manager:

```sh
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

It installs into `~/.rustup` (toolchains) and `~/.cargo` (the `cargo`
tool, installed binaries, the crate cache), and adds `~/.cargo/bin` to
your `PATH`. Distributions also package `rustup` itself (`pacman -S
rustup`, `brew install rustup`), which is better than the distribution's
`rustc` package if you want current versions.

| Command | Purpose |
|---------|---------|
| `rustup update` | upgrade |
| `rustup toolchain` | list, add |
| `rustup component` | add tools |
| `rustup doc --std` | local docs |
| `rustup target` | cross targets |

Rust has a new stable release every six weeks. Compatibility is taken
seriously: code that compiled with Rust 1.0 still compiles. Larger
language changes come with **editions** (2015, 2018, 2021, 2024), chosen
per crate in `Cargo.toml`; crates of different editions link together
without problems. The examples here use edition 2024 and were tested with
Rust 1.99.

Components worth adding: `clippy` (the linter), `rustfmt` (the
formatter), `rust-src` and `rust-analyzer` (for editor support through
LSP). Recent rustup installs the first two by default.

### 19.2 Cargo: build tool and package manager

Every Rust project is a **package** described by `Cargo.toml`. Cargo
downloads dependencies, compiles, runs tests, generates documentation.

```text
$ cargo new hello
    Creating binary (application) `hello` package
$ cd hello
$ tree
.
├── Cargo.toml
└── src
    └── main.rs
$ cargo run
   Compiling hello v0.1.0 (/home/me/hello)
    Finished `dev` profile [unoptimized + debuginfo] target(s) in 0.31s
     Running `target/debug/hello`
Hello, world!
```

| Command | Effect |
|---------|--------|
| `cargo build` | debug build |
| `cargo build -r` | release build |
| `cargo run` | build, run |
| `cargo check` | type check |
| `cargo test` | run tests |
| `cargo add` | add dependency |
| `cargo doc --open` | API docs |
| `cargo clippy` | lint |
| `cargo fmt` | format |
| `cargo install` | install a tool |

Some details:

- Builds go to `target/debug/` or `target/release/`. A debug build of our
  ratatui program is 17 MB (debug info, no optimization); the release
  build is 1 MB. The release build is often 10 to 50 times faster for
  computation, which does not matter for I/O-bound terminal programs but
  matters a lot for, say, a terminal emulator's parser.
- `cargo run -- ARGS` passes `ARGS` to the program (the `--` separates
  them from cargo's own options). `cargo run -q` hides cargo's messages.
- **Several programs in one package**: every file `src/bin/NAME.rs` is a
  binary named `NAME`, run with `cargo run --bin NAME`. Code shared by the
  binaries goes in `src/lib.rs`, a library crate named after the package,
  that the binaries `use` like any other crate. That is how the examples
  of this part are organized.
- `Cargo.lock` records the exact versions resolved. Commit it for
  applications, so that everybody builds the same thing.
- The first build downloads and compiles every dependency (163 crates in
  the tree for our examples, mostly pulled in by ratatui and
  portable-pty): about a minute. Later builds only recompile what changed.

### 19.3 Crates: crates.io, docs.rs, lib.rs

Libraries are **crates**, published on <https://crates.io>. The API
documentation of every published crate is built automatically on
<https://docs.rs>. <https://lib.rs> is an alternative index with better
categories and search. To add one:

```text
$ cargo add nix --features term,process,signal,fs,poll,ioctl
$ cargo add libc crossterm ratatui signal-hook portable-pty
```

Many crates have **features**, optional parts compiled only when asked
for; `nix` puts each group of system calls behind a feature to keep
compile times down. `cargo add` writes the dependency in `Cargo.toml`:

```toml
# file: rust/Cargo.toml
[package]
name = "termtut"
version = "0.1.0"
edition = "2024"

[dependencies]
crossterm = "0.29.0"
libc = "0.2.191"
nix = { version = "0.32.0", features = ["term", "process", "signal", "fs", "poll", "ioctl"] }
portable-pty = "0.9.0"
ratatui = "0.30.2"
regex = "1.13.2"
signal-hook = "0.4.6"
```

The version requirement `"0.29.0"` means "0.29.0 or any later
compatible version", where for 0.x versions only the patch number may
change. Crates follow semantic versioning: before 1.0, a change of minor
version (0.29 to 0.30) may break the API, and it often does in the
terminal crates. Check the changelog when you upgrade.

The crates used in this part:

| Crate | Role |
|-------|------|
| `libc` | raw C bindings |
| `nix` | safe POSIX API |
| `signal-hook` | signals |
| `crossterm` | terminal I/O |
| `ratatui` | TUI widgets |
| `portable-pty` | PTY, also Windows |

Others you will meet:

- **`rustix`**: like `nix`, a safe POSIX API, but it can make system
  calls without libc on Linux. It is under `std`-level crates such as
  `tempfile` and under the terminal crates `termwiz` and `termina`.
- **`tokio`**: the main asynchronous runtime. `tokio::process` is an
  async version of `std::process`, `tokio::signal` an async signal API.
  Use it when one program must juggle many processes or connections.
- **`termion`**: an older, Unix-only alternative to crossterm.
- **`termwiz`**: WezTerm's terminal library (with a terminal emulator
  model and surfaces). `portable-pty` comes from the same project.
- **`vte`**: the parser used by the Alacritty terminal, a Rust
  implementation of the vt100.net state machine (chapter 7).
- **`expectrl`** and **`rexpect`**: `expect`-like automation.

### 19.4 std, libc, nix: three levels

To call `tcgetattr` from Rust, there are three ways:

1. **`libc::tcgetattr(fd, &mut termios)`**: the C function, declared in
   Rust. It is `unsafe` (the compiler cannot check the pointer), returns
   `-1` and sets `errno` on error, and uses C types (`libc::termios`,
   `c_int`). Every libc function and constant is there, for every
   platform.
2. **`nix::sys::termios::tcgetattr(fd)`**: a safe wrapper. It takes
   anything that implements `AsFd` (a borrowed file descriptor, see
   below), returns `Result<Termios, Errno>`, and uses Rust types (flags
   are `bitflags`, so `LocalFlags::ECHO | LocalFlags::ICANON`).
3. **The standard library**, when it has the feature: `std::process` for
   processes, `std::io::IsTerminal` for `isatty`, `std::io::pipe` for
   pipes. No terminal modes or PTYs, though.

Use the highest level available, and drop down when you need to.

**File descriptor ownership.** Rust 1.63 introduced types that make the
ownership of file descriptors explicit, and modern crates use them:

| Type | Meaning |
|------|---------|
| `RawFd` | a plain `c_int` |
| `OwnedFd` | closes on drop |
| `BorrowedFd<'a>` | a loan |
| `AsFd` | "has an fd" |

An `OwnedFd` is closed exactly once, when it is dropped, so you cannot
leak it or close it twice. A `BorrowedFd<'a>` cannot outlive the owner.
`File`, `Stdin`, `ChildStdout`, `UnixStream` all implement `AsFd`, and
you can convert an `OwnedFd` into a `File` or a `Stdio` and back. That is
how the examples pass PTY descriptors around without a single `close`.

**Errors.** Fallible functions return `Result<T, E>`. The `?` operator
returns the error to the caller (converting it if needed). `main` can
return a `Result` too, and then an error ends the program with a message
and exit status 1. In the examples, `main` returns `Result<(),
Box<dyn std::error::Error>>`, a box that can hold any error type.
Larger programs use the `anyhow` crate (applications) or `thiserror`
(libraries).

**`unsafe`.** Some operations cannot be checked by the compiler: calling
C functions with raw pointers, `fork`, code in a `pre_exec` closure.
They must be written inside an `unsafe` block, which is a promise by the
programmer. The examples keep these blocks to a line or two, with a
comment saying why they are correct.

### 19.5 The example project

All the Rust examples live in one package. Create it like this, then
put each listing in its file:

```text
$ cargo new --name termtut rust
$ cd rust
$ rm src/main.rs
$ mkdir src/bin
$ cargo add nix --features term,process,signal,fs,poll,ioctl
$ cargo add libc crossterm ratatui signal-hook portable-pty
```

```text
rust/
├── Cargo.toml
├── rustfmt.toml
└── src/
    ├── lib.rs            shared helpers (chapter 21)
    └── bin/
        ├── run.rs        chapter 20
        ├── pipeline.rs
        ├── merge.rs
        ├── forkexec.rs
        ├── sigpipe.rs
        ├── signals.rs
        ├── rawkeys.rs    chapter 21
        ├── ttyinfo.rs
        ├── ptyspawn.rs   chapter 22
        ├── ptyscript.rs
        ├── portable.rs
        ├── events.rs     chapter 23
        └── ptop.rs
```

`rustfmt.toml` makes `cargo fmt` wrap lines at 80 columns, so that the
code fits in this document:

```toml
# file: rust/rustfmt.toml
max_width = 80
```

Run any example with `cargo run -q --bin NAME -- ARGS`, or build them all
(`cargo build`) and run `target/debug/NAME`. All of them were tested,
and `cargo clippy` reports nothing.

---

## 20. Rust: pipes and processes

### 20.1 `std::process::Command`

`Command` is a builder: you set the program, arguments, environment,
working directory and standard streams, then start it with one of three
methods:

| Method | Returns |
|--------|---------|
| `.status()` | `ExitStatus` |
| `.output()` | `Output` |
| `.spawn()` | `Child` |

- `.status()` runs the program with inherited streams and waits.
- `.output()` captures stdout and stderr (stdin is `/dev/null` by
  default here), waits, and returns all three together.
- `.spawn()` starts the program and returns a `Child` at once; you
  interact with it through `child.stdin`, `child.stdout`,
  `child.stderr` (`Option`s, present when you asked for pipes) and finish
  with `.wait()` or `.wait_with_output()`.

Each stream is configured with a `Stdio`: `Stdio::inherit()` (the
default for `status` and `spawn`), `Stdio::piped()`, `Stdio::null()`, or
`Stdio::from(x)` where `x` is a `File`, an `OwnedFd`, a `ChildStdout`,
or one end of a pipe.

```rust
// file: rust/src/bin/run.rs
//! std::process::Command: run, capture, feed stdin, check the status.
use std::io::Write;
use std::os::unix::process::ExitStatusExt; // .signal(), Unix only
use std::process::{Command, Stdio};

fn main() -> std::io::Result<()> {
    // 1. Inherit our stdin/stdout/stderr, wait for the exit status.
    let st = Command::new("echo").arg("hello from echo").status()?;
    println!("exit code: {:?}", st.code());

    // 2. Capture stdout and stderr. output() reads both pipes at the
    //    same time (no two-pipe deadlock), then waits.
    let out = Command::new("sh")
        .args(["-c", "echo out; echo err >&2; exit 3"])
        .output()?;
    println!(
        "stdout={:?} stderr={:?} code={:?}",
        String::from_utf8_lossy(&out.stdout).trim_end(),
        String::from_utf8_lossy(&out.stderr).trim_end(),
        out.status.code()
    );

    // 3. Write to the child's stdin, read its stdout.
    let mut sort = Command::new("sort")
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .spawn()?;
    {
        let mut stdin = sort.stdin.take().expect("piped");
        stdin.write_all(b"pear\napple\nfig\n")?;
    } // stdin is dropped here: the pipe closes and sort sees EOF
    let sorted = sort.wait_with_output()?;
    print!("sorted:\n{}", String::from_utf8_lossy(&sorted.stdout));

    // 4. Killed by a signal: code() is None and signal() says which.
    let mut sleeper = Command::new("sleep").arg("10").spawn()?;
    sleeper.kill()?; // sends SIGKILL
    let st = sleeper.wait()?;
    println!(
        "sleep: code={:?} signal={:?} success={} ({st})",
        st.code(),
        st.signal(),
        st.success()
    );

    // 5. A missing program is an error from spawn, not an exit status.
    match Command::new("no-such-program").status() {
        Ok(st) => println!("unexpected: {st}"),
        Err(e) => println!("spawn failed: {e} (kind {:?})", e.kind()),
    }

    // 6. Environment and working directory.
    let out = Command::new("sh")
        .args(["-c", "echo $GREETING from $(pwd)"])
        .env("GREETING", "bonjour")
        .current_dir("/usr")
        .output()?;
    print!("{}", String::from_utf8_lossy(&out.stdout));
    Ok(())
}
```

```text
$ cargo run -q --bin run
hello from echo
exit code: Some(0)
stdout="out" stderr="err" code=Some(3)
sorted:
apple
fig
pear
sleep: code=None signal=Some(9) success=false (signal: 9 (SIGKILL))
spawn failed: No such file or directory (os error 2) (kind NotFound)
bonjour from /usr
```

Points to notice:

- **Arguments are a list**, there is no shell, so no quoting. To use
  shell syntax, run `sh -c` explicitly, as in part 2.
- **`code()` is an `Option`.** A process killed by a signal has no exit
  code; `ExitStatusExt::signal()` (a Unix-only extension trait) gives the
  signal number. The `Display` implementation of `ExitStatus` shows
  either.
- **Closing a pipe is dropping it.** `sort` only produces output when
  its input ends. The block `{ let mut stdin = sort.stdin.take()...; }`
  moves the pipe's write end out of the `Child`, writes, and drops it at
  the closing brace, which closes the descriptor. Forgetting this (or
  keeping the `ChildStdin` in a variable that lives too long) is the
  Rust form of the classic "the reader never gets EOF" bug.
- **`output()` and `wait_with_output()` read stdout and stderr
  concurrently** (the standard library uses `poll` on Unix), so the
  two-pipe deadlock of chapter 3 cannot happen there. But in example 3,
  we write the whole input *before* reading any output. That is fine for
  three words; with megabytes, `sort` would not care (it reads all its
  input first), but a filter like `cat` would fill its output pipe while
  we are still writing, and both processes would block. The fix is to
  write from a separate thread:

  ```rust
  let mut stdin = child.stdin.take().unwrap();
  let writer = std::thread::spawn(move || stdin.write_all(&data));
  let output = child.wait_with_output()?;   // reads while we write
  writer.join().unwrap()?;
  ```

- **A failed `exec` is an error of `spawn`**, with the `errno` of
  `execvp` (here `ENOENT`). The standard library reports it through a
  close-on-exec pipe between the parent and the child: if `exec`
  succeeds, the pipe is closed without data; if it fails, the child
  writes `errno` in it before exiting. That is the trick of chapter 10,
  implemented for you.
- **`Child` does not kill or wait on drop.** If you drop a `Child`
  without calling `wait`, the process continues to run and becomes a
  zombie when it exits (until our process exits too). Always `wait`.

### 20.2 Pipelines

```rust
// file: rust/src/bin/pipeline.rs
//! ls -1 /usr/bin | grep zip | wc -l, without a shell.
use std::process::{Command, Stdio};

fn main() -> std::io::Result<()> {
    let mut ls = Command::new("ls")
        .args(["-1", "/usr/bin"])
        .stdout(Stdio::piped())
        .spawn()?;
    // take() moves the read end out of `ls`: after the next spawn, the
    // only copy of it is in grep. (If we kept one, nothing would break
    // here, but a copy of a *write* end kept by mistake means no EOF.)
    let mut grep = Command::new("grep")
        .arg("zip")
        .stdin(Stdio::from(ls.stdout.take().unwrap()))
        .stdout(Stdio::piped())
        .spawn()?;
    let wc = Command::new("wc")
        .arg("-l")
        .stdin(Stdio::from(grep.stdout.take().unwrap()))
        .output()?;
    print!("matches: {}", String::from_utf8_lossy(&wc.stdout));
    // Reap every child, and look at every status (like PIPESTATUS).
    println!("ls    {}", ls.wait()?);
    println!("grep  {}", grep.wait()?);
    println!("wc    {}", wc.status);
    Ok(())
}
```

```text
$ cargo run -q --bin pipeline
matches: 23
ls    exit status: 0
grep  exit status: 0
wc    exit status: 0
```

`Stdio::from(ChildStdout)` passes the read end of the first pipe to the
next child. The data does not go through our process: as in the shell,
the kernel connects `ls` and `grep` directly. And because `take()` moved
the `ChildStdout` out of `ls`, and `Stdio::from` consumed it, our process
closes its copy as soon as `grep` is spawned (the standard library closes
the parent's copies of the descriptors it passed). The ownership system
does the bookkeeping that chapter 10 did by hand in C.

### 20.3 One pipe for two streams: `std::io::pipe`

Since Rust 1.87, `std::io::pipe()` creates an anonymous pipe and returns
a `(PipeReader, PipeWriter)`. With it we can do `2>&1`: give the same
write end to stdout and stderr.

```rust
// file: rust/src/bin/merge.rs
//! 2>&1: send a child's stdout and stderr into one pipe, std::io::pipe.
use std::io::Read;
use std::process::Command;

fn main() -> std::io::Result<()> {
    let (mut reader, writer) = std::io::pipe()?; // Rust 1.87+
    let mut cmd = Command::new("sh");
    cmd.args(["-c", "echo one; echo two >&2; echo three"])
        .stdout(writer.try_clone()?)
        .stderr(writer);
    let mut child = cmd.spawn()?;
    // The Command still owns both write ends. Drop it, or the pipe has a
    // writer forever and read_to_string never sees EOF.
    if std::env::args().nth(1).as_deref() != Some("--hang") {
        drop(cmd);
    }
    let mut all = String::new();
    reader.read_to_string(&mut all)?;
    child.wait()?;
    print!("{all}");
    Ok(())
}
```

```text
$ cargo run -q --bin merge
one
two
three
$ timeout 3 cargo run -q --bin merge -- --hang; echo $?
124
```

The `--hang` variant shows a subtle trap. A `Command` keeps the `Stdio`s
it was given, so that you can spawn it several times. Here these are our
two copies of the write end. As long as `cmd` lives, the pipe has a
writer, and `read_to_string` waits forever for an EOF that cannot come.
The `Child` has nothing to do with it; the `Command` does. In the earlier
examples, `Stdio::piped()` does not have the problem: the pipe is
created at spawn time, and the parent's write end is closed then.

### 20.4 The low level: fork and exec with nix

The standard library does not expose `fork`. Most of the time you do not
need it. When you do (to write a shell, a daemon, or to understand what
`Command` does), `nix` has it:

```rust
// file: rust/src/bin/forkexec.rs
//! The C way in Rust, with nix: pipe(2), fork(2), dup2(2), execvp(3),
//! waitpid(2). Output: what `date +%Y` printed, and how it exited.
use nix::sys::wait::{WaitStatus, waitpid};
use nix::unistd::{ForkResult, dup2_stdout, execvp, fork, pipe, read};

fn main() -> nix::Result<()> {
    let (rd, wr) = pipe()?; // two OwnedFd: closed when dropped
    // fork is unsafe: in a multi-threaded process the child may only call
    // async-signal-safe functions until it execs. We only do that.
    match unsafe { fork() }? {
        ForkResult::Child => {
            drop(rd);
            dup2_stdout(&wr).expect("dup2");
            drop(wr);
            let argv = [c"date", c"+%Y"]; // C string literals (&CStr)
            let _ = execvp(argv[0], &argv);
            // Only reached if exec failed. _exit: no destructors, no
            // flushing of buffers that belong to the parent.
            unsafe { libc::_exit(127) }
        }
        ForkResult::Parent { child } => {
            drop(wr); // essential, or read() never returns 0
            let mut out = Vec::new();
            let mut buf = [0u8; 256];
            loop {
                let n = read(&rd, &mut buf)?;
                if n == 0 {
                    break;
                }
                out.extend_from_slice(&buf[..n]);
            }
            print!("child said: {}", String::from_utf8_lossy(&out));
            match waitpid(child, None)? {
                WaitStatus::Exited(pid, code) => {
                    println!("{pid} exited with {code}")
                }
                WaitStatus::Signaled(pid, sig, _core) => {
                    println!("{pid} killed by {sig}")
                }
                other => println!("{other:?}"),
            }
        }
    }
    Ok(())
}
```

```text
$ cargo run -q --bin forkexec
child said: 2026
935245 exited with 0
```

This is chapter 10's C program, line for line, with three improvements:

- The descriptors are `OwnedFd`s: `drop(wr)` closes the write end, and
  everything else is closed automatically.
- `waitpid` returns an `enum`, `WaitStatus`, with one variant per case
  (`Exited`, `Signaled`, `Stopped`, `Continued`...). The compiler forces
  you to handle all of them (here, with a catch-all `other`).
- `fork` is marked `unsafe`, with the reason in its documentation: after
  `fork` in a multi-threaded program, the child has only one thread, and
  any lock held by another thread (in `malloc`, for example) stays locked.
  Until `exec`, the child may only call async-signal-safe functions. Our
  child calls `dup2`, `close`, `execvp` and `_exit`, which are safe; but
  `execvp` searching the `PATH` allocates nothing in glibc only by an
  implementation detail, and `expect("dup2")` would allocate and print if
  it failed. A careful program prepares everything (the `CString`s, the
  path) *before* forking. `c"date"` is a C string literal (Rust 1.77),
  already NUL-terminated, so nothing is allocated in the child.

`Command` handles all this, and on Linux it uses `posix_spawn` when it
can (glibc implements it with `clone(CLONE_VFORK)`), which is faster
than `fork` for large processes. Use `fork` only when you need the child
to run Rust code that `Command` cannot express, and keep that code
minimal. The `std::os::unix::process::CommandExt` trait covers most
needs: `pre_exec` (a closure run in the child before `exec`, used in
chapter 22), `process_group`, `uid`/`gid`, `arg0`, `exec` (replace the
current process).

### 20.5 SIGPIPE: Rust's surprise

The Rust runtime sets `SIGPIPE` to "ignore" before `main` runs. A write
to a broken pipe then fails with `EPIPE`, and `println!`, which panics on
write errors, panics:

```rust
// file: rust/src/bin/sigpipe.rs
//! Rust programs ignore SIGPIPE. Three ways to behave in `| head`:
//!   sigpipe | head -3             println! panics: "Broken pipe"
//!   sigpipe --default | head -3   die from SIGPIPE, silently, like C
//!   sigpipe --handle | head -3    see the EPIPE error, exit(0)
use std::io::{self, ErrorKind, Write};

fn main() {
    let mode = std::env::args().nth(1).unwrap_or_default();
    if mode == "--default" {
        // Undo what the Rust runtime did before main: SIG_IGN -> SIG_DFL.
        unsafe { libc::signal(libc::SIGPIPE, libc::SIG_DFL) };
    }
    if mode == "--handle" {
        let mut out = io::stdout().lock();
        for i in 1..=u64::MAX {
            if let Err(e) = writeln!(out, "line {i}") {
                if e.kind() == ErrorKind::BrokenPipe {
                    std::process::exit(0); // the reader is gone: done
                }
                eprintln!("write error: {e}");
                std::process::exit(1);
            }
        }
    }
    for i in 1..=u64::MAX {
        println!("line {i}");
    }
}
```

```text
$ cargo run -q --bin sigpipe | head -3
line 1
line 2
line 3

thread 'main' (935246) panicked at /rustc/b940084d.../library/std/src/io/stdio.rs:1168:9:
failed printing to stdout: Broken pipe (os error 32)
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
$ echo ${PIPESTATUS[0]}
101
$ cargo run -q --bin sigpipe -- --default | head -3 >/dev/null
$ echo ${PIPESTATUS[0]}
141
$ cargo run -q --bin sigpipe -- --handle | head -3 >/dev/null
$ echo ${PIPESTATUS[0]}
0
```

Three ways out:

1. **Restore the default** (`--default`): the process dies from
   `SIGPIPE`, silently, with status 128 + 13 = 141, like `cat` or `yes`.
   This is what most command-line filters should do. A nightly compiler
   option, `-Zon-broken-pipe=kill`, does the same at build time; until it
   is stable, one `libc::signal` call at the start of `main` is the way.
2. **Handle the error** (`--handle`): use `writeln!` (which returns a
   `Result`) instead of `println!` (which panics), and treat
   `ErrorKind::BrokenPipe` as a normal end.
3. **Do nothing**: fine for programs that are not meant for pipelines,
   but users will report the panic as a bug as soon as they type `|
   head`.

Why does Rust ignore `SIGPIPE`? Because a network server must not die
when a client disconnects: with `SIGPIPE` ignored, the `write` fails and
the server handles the error for that one connection. Python, Raku and Go
(for non-stdout descriptors) made the same choice; C kept the Unix
default.

Note that **children inherit** an ignored signal disposition across
`exec` (chapter 4). A Rust program that starts a shell pipeline with
`Command` passes "SIGPIPE ignored" to it, and then `yes | head` in that
shell prints an error instead of stopping quietly. The standard library
resets `SIGPIPE` to the default in children it spawns, for this reason;
if you `fork`+`exec` yourself (20.4), do it in the child.

### 20.6 Signals with signal-hook

A signal handler may only call async-signal-safe functions, which rules
out almost everything, including allocation and locking (chapter 4). The
`signal-hook` crate installs handlers that only write to a pipe (the
self-pipe trick) and gives you the signals in normal code:

```rust
// file: rust/src/bin/signals.rs
//! Receive signals as an iterator (signal-hook). The real handler only
//! writes to a pipe; this loop runs in normal context.
use signal_hook::consts::{SIGHUP, SIGINT, SIGTERM, SIGUSR1};
use signal_hook::iterator::Signals;

fn main() -> std::io::Result<()> {
    let mut signals = Signals::new([SIGINT, SIGTERM, SIGHUP, SIGUSR1])?;
    println!("pid {}; ^C three times to quit", std::process::id());
    let mut ints = 0;
    for sig in signals.forever() {
        match sig {
            SIGINT => {
                ints += 1;
                println!("got SIGINT #{ints}");
                if ints == 3 {
                    break;
                }
            }
            SIGTERM => {
                println!("SIGTERM: cleaning up");
                break;
            }
            SIGHUP => println!("got SIGHUP"),
            other => println!("got signal {other}"),
        }
    }
    println!("bye");
    Ok(())
}
```

```text
$ cargo run -q --bin signals &
pid 935253; ^C three times to quit
$ kill -INT %1; kill -HUP %1; kill -USR1 %1; kill -TERM %1
got SIGINT #1
got SIGHUP
got signal 10
SIGTERM: cleaning up
bye
```

`signal-hook` offers several interfaces for different program shapes:

- `iterator::Signals`: an iterator (blocking `forever()`, or `pending()`
  to poll), usually run in a dedicated thread that forwards signals to
  the rest of the program through a channel.
- `flag::register(SIGTERM, Arc<AtomicBool>)`: set a flag that the main
  loop checks. Simplest for "stop cleanly when asked".
- `low_level::pipe::register(SIGWINCH, fd)`: write a byte to a
  descriptor of yours, to wake up a `poll` loop (chapter 22 uses it).
- `signal-hook-tokio`, `signal-hook-mio`: integration with event loops.

`ctrlc` is a smaller crate for the common case of `SIGINT`/`SIGTERM`
only.

---

## 21. Rust: termios and raw mode

### 21.1 Is it a terminal?

`std::io::IsTerminal` (Rust 1.70) adds `.is_terminal()` to anything with
a file descriptor: `io::stdin().is_terminal()`,
`io::stdout().is_terminal()`, `File::is_terminal()`. It calls `isatty`
on Unix (and checks the console mode on Windows). Use it to decide
whether to color output, show progress bars or prompt.

### 21.2 A raw mode guard

The pattern of chapter 11, "save the modes, change them, *restore them
whatever happens*", maps directly to a Rust type whose destructor
restores the terminal. The shared library of our package starts with it:

```rust
// file: rust/src/lib.rs
//! Helpers shared by the examples: raw mode with a guard, window size.
use nix::sys::termios::{SetArg, Termios, cfmakeraw, tcgetattr, tcsetattr};
use std::os::fd::{AsFd, AsRawFd, BorrowedFd};

/// Puts a terminal in raw mode; the Drop impl restores the old mode,
/// on normal return, on `?` and on panic (but not on process::exit).
pub struct RawMode<'fd> {
    fd: BorrowedFd<'fd>,
    saved: Termios,
}

impl<'fd> RawMode<'fd> {
    pub fn enable(fd: BorrowedFd<'fd>) -> nix::Result<Self> {
        let saved = tcgetattr(fd)?;
        let mut raw = saved.clone();
        cfmakeraw(&mut raw); // ~ICANON ~ECHO ~ISIG ~IXON ~OPOST, CS8...
        tcsetattr(fd, SetArg::TCSAFLUSH, &raw)?;
        Ok(RawMode { fd, saved })
    }
}

impl Drop for RawMode<'_> {
    fn drop(&mut self) {
        let _ = tcsetattr(self.fd, SetArg::TCSADRAIN, &self.saved);
    }
}

// nix generates a typed wrapper for ioctls; "bad" means the request
// number does not follow the _IOR() encoding, which is true of the old
// terminal ioctls on Linux.
nix::ioctl_read_bad!(tiocgwinsz, libc::TIOCGWINSZ, libc::winsize);
nix::ioctl_write_ptr_bad!(tiocswinsz, libc::TIOCSWINSZ, libc::winsize);

/// (rows, cols) of the terminal on `fd`.
pub fn window_size(fd: impl AsFd) -> nix::Result<(u16, u16)> {
    let mut ws: libc::winsize = unsafe { std::mem::zeroed() };
    unsafe { tiocgwinsz(fd.as_fd().as_raw_fd(), &mut ws) }?;
    Ok((ws.ws_row, ws.ws_col))
}

/// Set the window size of a terminal, typically a PTY master.
pub fn set_window_size(fd: impl AsFd, rows: u16, cols: u16) -> nix::Result<()> {
    let ws = libc::winsize {
        ws_row: rows,
        ws_col: cols,
        ws_xpixel: 0,
        ws_ypixel: 0,
    };
    unsafe { tiocswinsz(fd.as_fd().as_raw_fd(), &ws) }?;
    Ok(())
}

/// Show control characters as ^X, keep newlines. For byte dumps.
pub fn visible(bytes: &[u8]) -> String {
    let text = String::from_utf8_lossy(bytes);
    let mut s = String::new();
    for c in text.chars() {
        match c {
            '\n' => s.push('\n'),
            c if (c as u32) < 32 => {
                s.push('^');
                s.push(char::from(c as u8 ^ 64));
            }
            '\x7f' => s.push_str("^?"),
            c => s.push(c),
        }
    }
    s
}

use std::io;
use std::os::fd::OwnedFd;
use std::os::unix::process::CommandExt;
use std::process::{Child, Command, Stdio};

/// Mark a descriptor close-on-exec, so that children do not inherit it.
pub fn set_cloexec(fd: impl AsFd) -> nix::Result<()> {
    use nix::fcntl::{FcntlArg, FdFlag, fcntl};
    fcntl(fd.as_fd(), FcntlArg::F_SETFD(FdFlag::FD_CLOEXEC))?;
    Ok(())
}

/// Start `argv` with the PTY slave as its stdin, stdout, stderr and
/// controlling terminal. Consumes the slave: when this returns, only the
/// child holds it, so reading the master gives EIO when the child (and
/// any process that inherited the slave) is gone.
pub fn spawn_on_pty(argv: &[String], slave: OwnedFd) -> io::Result<Child> {
    let mut cmd = Command::new(&argv[0]);
    cmd.args(&argv[1..])
        .stdin(Stdio::from(slave.try_clone()?))
        .stdout(Stdio::from(slave.try_clone()?))
        .stderr(Stdio::from(slave));
    // pre_exec runs in the child between fork and exec. Only
    // async-signal-safe calls are allowed there: setsid and ioctl are.
    unsafe {
        cmd.pre_exec(|| {
            nix::unistd::setsid()?; // new session, no controlling tty yet
            // Our stdin is the slave: make it the controlling terminal.
            if libc::ioctl(0, libc::TIOCSCTTY as _, 0) == -1 {
                return Err(io::Error::last_os_error());
            }
            Ok(())
        });
    }
    cmd.spawn()
    // cmd is dropped here, and with it the parent's copies of the slave.
}
```

The rest of `lib.rs` (`set_cloexec`, `spawn_on_pty`) is for chapter 22.

How `RawMode` works:

- `enable` saves the current `Termios`, applies `cfmakeraw` to a copy,
  and installs it with `TCSAFLUSH` (discard pending input). It returns a
  guard value that holds the saved modes.
- When the guard goes out of scope, `Drop::drop` reinstalls the saved
  modes. That happens on normal return, on early return with `?`, and
  during the unwinding of a panic.
- It does **not** happen on `std::process::exit` (which does not run
  destructors), on `abort`, or when the process is killed by a signal.
  In raw mode `^C` is not a signal, so the main risk is a `kill` from
  elsewhere; a program can handle `SIGTERM` with signal-hook and return
  normally.
- The guard keeps a `BorrowedFd<'fd>`: the borrow checker guarantees
  that the descriptor stays open as long as the guard exists.

**ioctls in nix.** `nix::ioctl_read_bad!(tiocgwinsz, libc::TIOCGWINSZ,
libc::winsize)` generates an `unsafe fn tiocgwinsz(fd: c_int, data: *mut
winsize) -> nix::Result<c_int>`. The macros come in families
(`ioctl_read!`, `ioctl_write_ptr!`, `ioctl_none!`...) that compute the
request number from the type and direction, as the C `_IOR()` macros do.
The `_bad` variants take a precomputed number, needed for the terminal
ioctls whose numbers predate that encoding. The call stays `unsafe`
because nix cannot check that the pointer type matches what the kernel
expects for that request.

### 21.3 Showing raw keys

```rust
// file: rust/src/bin/rawkeys.rs
//! Show the bytes each key sends, in raw mode. Press q to quit.
use std::io::{self, IsTerminal, Write};
use std::os::fd::AsFd;
use termtut::{RawMode, visible};

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let stdin = io::stdin();
    if !stdin.is_terminal() {
        return Err("stdin is not a terminal".into());
    }
    let _raw = RawMode::enable(stdin.as_fd())?;
    let mut out = io::stdout().lock();
    write!(out, "raw mode: press keys, q quits\r\n")?;
    out.flush()?;
    let mut buf = [0u8; 32];
    loop {
        // One read(2): one key, or one escape sequence (usually).
        let n = nix::unistd::read(&stdin, &mut buf)?;
        if n == 0 {
            break;
        }
        let hex: Vec<String> =
            buf[..n].iter().map(|b| format!("{b:02x}")).collect();
        write!(
            out,
            "{n} byte(s): {}   {}\r\n",
            hex.join(" "),
            visible(&buf[..n])
        )?;
        out.flush()?;
        if &buf[..n] == b"q" {
            break;
        }
    }
    write!(out, "bye\r\n")?;
    Ok(()) // _raw is dropped here: the terminal is restored
}
```

```text
$ cargo run -q --bin rawkeys
raw mode: press keys, q quits
1 byte(s): 61   a
3 byte(s): 1b 5b 41   ^[[A
1 byte(s): 03   ^C
2 byte(s): c3 a9   é
1 byte(s): 71   q
bye
```

The output is identical to the C and Raku versions, which is the point:
the bytes come from the terminal, whatever the language.

Note the explicit `"\r\n"` (no `OPOST` in raw mode) and the explicit
`flush()`: `io::stdout()` is line-buffered in Rust, *always*, even when
it is not a terminal. Our lines end with `\r\n`, so they would be flushed
anyway, but output without a newline (a prompt, a cursor movement) stays
in the buffer until `flush()`. Rust's `stdout` never switches to full
buffering, unlike C's stdio; for heavy output to a pipe or file, wrap it
in a `BufWriter` yourself. `stderr` is unbuffered.

We read with `nix::unistd::read` rather than `io::stdin().read()`
because `Stdin` has an internal 8 KiB buffer: a large read on it can
return bytes that belong to several keys, and later key presses can sit
in that buffer while `poll` on the descriptor says nothing is pending.
Mixing `poll` with a buffered reader is a classic bug; read the
descriptor directly.

### 21.4 Process groups, sessions and the window size

```rust
// file: rust/src/bin/ttyinfo.rs
//! Where am I? Process ids, the controlling terminal and its size.
//! With --watch, report window size changes (SIGWINCH) until ^C.
use nix::unistd::{getpgrp, getpid, getppid, getsid, tcgetpgrp, ttyname};
use signal_hook::consts::{SIGINT, SIGWINCH};
use signal_hook::iterator::Signals;
use std::io::{self, IsTerminal};
use termtut::window_size;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    println!("pid  {:<8} ppid {}", getpid(), getppid());
    println!("pgid {:<8} sid  {}", getpgrp(), getsid(None)?);
    let stdin = io::stdin();
    if !stdin.is_terminal() {
        println!("stdin is not a terminal");
        return Ok(());
    }
    println!("tty  {}", ttyname(&stdin)?.display());
    let fg = tcgetpgrp(&stdin)?;
    let who = if fg == getpgrp() {
        "us"
    } else {
        "another group"
    };
    println!("foreground pgid {fg} ({who})");
    let (rows, cols) = window_size(&stdin)?;
    println!("size {rows}x{cols}");

    if std::env::args().any(|a| a == "--watch") {
        let mut signals = Signals::new([SIGWINCH, SIGINT])?;
        println!("resize the window; ^C to quit");
        for sig in signals.forever() {
            if sig == SIGINT {
                break;
            }
            let (rows, cols) = window_size(&stdin)?;
            println!("SIGWINCH: now {rows}x{cols}");
        }
    }
    Ok(())
}
```

```text
$ cargo run -q --bin ttyinfo -- --watch
pid  943698   ppid 943697
pgid 943698   sid  943541
tty  /dev/pts/14
foreground pgid 943698 (us)
size 24x80
resize the window; ^C to quit
SIGWINCH: now 40x120
^C
```

`^C` ends the program cleanly, not by killing it: we asked signal-hook
for `SIGINT`, so it is delivered to the iterator and we `break`. The
`^C` printed on the screen is the terminal's echo (`ECHOCTL`), not ours.

---

## 22. Rust: pseudo-terminals

Rust can do what C does: open a PTY pair, fork, make the slave the
controlling terminal in the child, exec. And thanks to
`CommandExt::pre_exec`, we do not even need a raw `fork`.

### 22.1 Starting a child on a PTY

`nix::pty::openpty` calls the libc `openpty(3)`, which opens
`/dev/ptmx`, unlocks the slave and opens it too, optionally setting the
window size and the termios. We get two `OwnedFd`s.

The child setup is in `spawn_on_pty`, in `lib.rs` (21.2):

- The slave becomes the child's stdin, stdout and stderr
  (`Stdio::from(OwnedFd)`; `try_clone` duplicates the descriptor).
- The `pre_exec` closure runs in the child, after `fork` and after the
  standard streams are in place, just before `exec`. It calls `setsid()`
  (new session, no controlling terminal) then `ioctl(0, TIOCSCTTY, 0)`
  (make stdin, the slave, the controlling terminal). Exactly chapter 12.
- `pre_exec` is `unsafe` because of the post-fork restrictions: only
  async-signal-safe calls. `setsid` and `ioctl` are system calls, fine.
  `io::Error::last_os_error()` only reads `errno`.
- When `spawn_on_pty` returns, the `Command` and its three `Stdio`s have
  been dropped: our process no longer holds the slave. This matters for
  the next point.

```rust
// file: rust/src/bin/ptyspawn.rs
//! Run a command on a new PTY and show what it writes, escaped.
//!   ptyspawn [CMD ARGS...]
use nix::pty::{Winsize, openpty};
use std::fs::File;
use std::io::Read;
use termtut::{set_cloexec, spawn_on_pty, visible};

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let mut argv: Vec<String> = std::env::args().skip(1).collect();
    if argv.is_empty() {
        argv = [
            "sh",
            "-c",
            "tty; stty size; ls --color=auto -d /; ls -l /proc/self/fd",
        ]
        .map(String::from)
        .to_vec();
    }
    let ws = Winsize {
        ws_row: 30,
        ws_col: 100,
        ws_xpixel: 0,
        ws_ypixel: 0,
    };
    let pty = openpty(&ws, None)?;
    // openpty does not set close-on-exec: without this, the child (and
    // all its descendants) would inherit the master and the slave.
    set_cloexec(&pty.master)?;
    set_cloexec(&pty.slave)?;

    let mut child = spawn_on_pty(&argv, pty.slave)?;
    println!("child pid {}", child.id());

    let mut master = File::from(pty.master);
    let mut out = Vec::new();
    let mut buf = [0u8; 4096];
    loop {
        match master.read(&mut buf) {
            Ok(0) => break,
            Ok(n) => out.extend_from_slice(&buf[..n]),
            // EIO: the slave is closed everywhere (Linux's "EOF").
            Err(e) if e.raw_os_error() == Some(libc::EIO) => break,
            Err(e) => return Err(e.into()),
        }
    }
    let status = child.wait()?;
    print!("{}", visible(&out));
    println!("\n[{status}; {} bytes]", out.len());
    Ok(())
}
```

```text
$ cargo run -q --bin ptyspawn
child pid 941058
/dev/pts/14^M
30 100^M
^[[0m^[[01;34m/^[[0m^M
total 0^M
lrwx------ 1 cog cog 64 Nov 22 17:47 0 -> /dev/pts/14^M
lrwx------ 1 cog cog 64 Nov 22 17:47 1 -> /dev/pts/14^M
lrwx------ 1 cog cog 64 Nov 22 17:47 2 -> /dev/pts/14^M
lr-x------ 1 cog cog 64 Nov 22 17:47 3 -> /proc/941058/fd^M

[exit status: 0; 273 bytes]
```

The last command lists the child's open descriptors: 0, 1 and 2 on the
slave, and 3 is `ls` reading its own `/proc/self/fd` directory. Nothing
else. Here is the same run with the two `set_cloexec` lines removed:

```text
$ cargo run -q --bin ptyspawn -- sh -c 'ls -l /proc/self/fd | tail -n +2'
child pid 941644
lrwx------ 1 cog cog 64 Nov 22 17:47 0 -> /dev/pts/14^M
l-wx------ 1 cog cog 64 Nov 22 17:47 1 -> pipe:[20234778]^M
lrwx------ 1 cog cog 64 Nov 22 17:47 2 -> /dev/pts/14^M
lrwx------ 1 cog cog 64 Nov 22 17:47 3 -> /dev/ptmx^M
lrwx------ 1 cog cog 64 Nov 22 17:47 4 -> /dev/pts/14^M
...
```

Descriptors 3 and 4 are the master and the original slave, inherited
through `exec`. A child holding the *master* of its own terminal is a
real problem: if it starts a daemon that keeps running, our side never
sees the PTY close, and a misbehaving child could even read its own
input. The Rust standard library opens everything with `O_CLOEXEC`, but
descriptors coming from C functions (`openpty`, here) do not have it.
Whenever you get a descriptor from libc, ask yourself whether children
should inherit it. (`posix_openpt(O_RDWR | O_NOCTTY | O_CLOEXEC)` sets
it atomically, for the master.)

**Reading until EIO.** When every process holding the slave has closed
it, reading the master on Linux fails with `EIO` instead of returning
0. That is our "end of file". It only works if *we* do not hold the
slave: hence the care with `Command` dropping.

### 22.2 `script` in Rust: one thread, `poll`

The Raku version (17.5) used `react` with three event sources. In Rust,
without an async runtime, the classical tool is `poll(2)` on the three
descriptors:

- the master (output of the child),
- our stdin (the keyboard, or a pipe),
- the read end of a socket pair where signal-hook writes a byte on
  `SIGWINCH` (the self-pipe trick).

```rust
// file: rust/src/bin/ptyscript.rs
//! A small script(1): run a command on a PTY, relay keys and output,
//! log the output, forward window size changes. One thread, poll(2).
//!   ptyscript [-o LOG] [CMD ARGS...]
use nix::errno::Errno;
use nix::poll::{PollFd, PollFlags, PollTimeout, poll};
use nix::pty::{Winsize, openpty};
use signal_hook::consts::SIGWINCH;
use std::fs::File;
use std::io::{self, IsTerminal, Read, Write};
use std::os::fd::AsFd;
use std::os::unix::net::UnixStream;
use std::os::unix::process::ExitStatusExt;
use std::process::ExitCode;
use termtut::{
    RawMode, set_cloexec, set_window_size, spawn_on_pty, window_size,
};

fn main() -> Result<ExitCode, Box<dyn std::error::Error>> {
    // Arguments: [-o LOG] [CMD ARGS...]
    let mut args: Vec<String> = std::env::args().skip(1).collect();
    let mut log_path = String::from("typescript");
    if args.first().map(String::as_str) == Some("-o") {
        if args.len() < 2 {
            return Err("-o needs a file name".into());
        }
        log_path = args.remove(1);
        args.remove(0);
    }
    if args.is_empty() {
        args.push(std::env::var("SHELL").unwrap_or_else(|_| "/bin/sh".into()));
    }

    let stdin = io::stdin();
    let interactive = stdin.is_terminal();
    let (rows, cols) = if interactive {
        window_size(&stdin)?
    } else {
        (24, 80)
    };
    let pty = openpty(
        &Winsize {
            ws_row: rows,
            ws_col: cols,
            ws_xpixel: 0,
            ws_ypixel: 0,
        },
        None,
    )?;
    set_cloexec(&pty.master)?;
    set_cloexec(&pty.slave)?;
    let mut child = spawn_on_pty(&args, pty.slave)?;
    let mut master = File::from(pty.master);

    let mut log = File::create(&log_path)?;
    let mut out = io::stdout().lock();
    writeln!(out, "Script started, output log file is '{log_path}'.")?;

    // The self-pipe trick, done by signal-hook: on SIGWINCH, the handler
    // writes a byte into `sig_w`; poll(2) wakes up on `sig_r`.
    let (mut sig_r, sig_w) = UnixStream::pair()?;
    sig_r.set_nonblocking(true)?;
    signal_hook::low_level::pipe::register(SIGWINCH, sig_w)?;

    let raw = if interactive {
        Some(RawMode::enable(stdin.as_fd())?)
    } else {
        None
    };
    let mut stdin_open = true;
    let mut buf = [0u8; 4096];
    let ready = PollFlags::POLLIN | PollFlags::POLLHUP | PollFlags::POLLERR;
    loop {
        let mut fds = vec![
            PollFd::new(master.as_fd(), PollFlags::POLLIN),
            PollFd::new(sig_r.as_fd(), PollFlags::POLLIN),
        ];
        if stdin_open {
            fds.push(PollFd::new(stdin.as_fd(), PollFlags::POLLIN));
        }
        match poll(&mut fds, PollTimeout::NONE) {
            Err(Errno::EINTR) => continue, // a signal interrupted poll
            r => r?,
        };
        let ev: Vec<PollFlags> = fds
            .iter()
            .map(|f| f.revents().unwrap_or(PollFlags::empty()))
            .collect();
        drop(fds); // release the borrows of master, sig_r and stdin

        // 1. Output of the child: to the screen and to the log.
        if ev[0].intersects(ready) {
            match master.read(&mut buf) {
                Ok(0) => break,
                Err(e) if e.raw_os_error() == Some(libc::EIO) => break,
                Err(e) => return Err(e.into()),
                Ok(n) => {
                    out.write_all(&buf[..n])?;
                    out.flush()?;
                    log.write_all(&buf[..n])?;
                }
            }
        }
        // 2. Window size changed: copy our size to the PTY. The kernel
        //    then sends SIGWINCH to the child's foreground process group.
        if ev[1].contains(PollFlags::POLLIN) {
            while sig_r.read(&mut buf).is_ok() {} // drain
            if interactive {
                let (rows, cols) = window_size(&stdin)?;
                set_window_size(&master, rows, cols)?;
            }
        }
        // 3. Keyboard (or pipe) to the child, as if typed.
        if stdin_open && ev[2].intersects(ready) {
            let n = nix::unistd::read(&stdin, &mut buf)?;
            if n == 0 {
                // Our input is finished: type ^D (VEOF) for the child.
                stdin_open = false;
                master.write_all(b"\x04")?;
            } else {
                master.write_all(&buf[..n])?;
            }
        }
    }

    drop(raw); // restore our terminal before the final message
    let status = child.wait()?;
    let code = status
        .code()
        .unwrap_or_else(|| 128 + status.signal().unwrap_or(0));
    writeln!(out, "Script done, exit status {code}.")?;
    Ok(ExitCode::from(code as u8))
}
```

With input from a pipe:

```text
$ printf 'echo hello from $(tty)\nstty size\nexit 3\n' |
    cargo run -q --bin ptyscript -- -o log.txt sh
Script started, output log file is 'log.txt'.
echo hello from $(tty)
stty size
exit 3
sh-5.3$ echo hello from $(tty)
hello from /dev/pts/14
sh-5.3$ stty size
24 80
sh-5.3$ exit 3
exit
Script done, exit status 3.
$ echo $?
3
```

Interactively, typing `stty size`, then `sleep 10`, `^C`, and `exit 4`:

```text
$ cargo run -q --bin ptyscript -- -o log2.txt sh
Script started, output log file is 'log2.txt'.
sh-5.3$ stty size
24 80
sh-5.3$ sleep 10
^C
sh-5.3$ exit 4
exit
Script done, exit status 4.
```

(The log file, and the raw output, also contain `ESC [ ? 2004 h` before
each prompt and `ESC [ ? 2004 l` after each command: bash turning
bracketed paste on while it reads a line, and off while the command runs.
Your terminal interprets them, so they are invisible above.)

Why are the three commands printed twice in the first run? Because they
arrived **before the shell was ready**. Our program wrote the whole pipe
content to the master at once. At that moment, the slave was still in
its default mode, canonical with `ECHO` on (bash had not yet switched it
to raw mode for its line editor, Readline). So the *line discipline*
echoed the three lines immediately, and stored them. Then bash started,
printed its prompt, read the first line, and Readline displayed it again
after the prompt. The Raku version, slower to start polling, usually
wrote the lines after bash had disabled echo, so we did not see the
effect there. Real `script` behaves like ours; `expect`-like tools avoid
it by waiting for the prompt before typing (chapter 30).

Design notes:

- **`poll` and borrows.** `PollFd::new` borrows the descriptor, so the
  vector of `PollFd`s borrows `master`, `sig_r` and `stdin`. We copy the
  `revents` out and `drop(fds)` before reading or writing, which ends the
  borrows. Rebuilding the vector each time around the loop is cheap (it
  is three structs).
- **`EINTR`**. `poll` returns `EINTR` when a signal handler ran during
  the call (here, signal-hook's `SIGWINCH` handler). The loop simply
  polls again, and finds the byte in the socket.
- **Which events count.** `POLLIN` means data; but when the child exits,
  the master reports `POLLHUP` (and `read` gives `EIO`). We read on any
  of `POLLIN | POLLHUP | POLLERR` so that the end is detected.
- **Window size.** On `SIGWINCH`, we copy our size to the master with
  `TIOCSWINSZ`. The kernel then sends `SIGWINCH` to the foreground
  process group *of the PTY*, and the child redraws. We tested it with
  the `ttyinfo --watch` program as the child:

  ```text
  $ ptyscript -o /dev/null target/debug/ttyinfo --watch
  ...
  size 24x80
  resize the window; ^C to quit
  SIGWINCH: now 40x120
  ^CScript done, exit status 0.
  ```

- **Blocking writes.** `master.write_all` blocks if the child does not
  read its input and the PTY's input buffer is full (about 4 KiB in
  canonical mode). While we block there, we do not read the child's
  output: if the child is itself blocked writing output, we have the
  two-pipe deadlock. Pasting a large text into a program that does not
  read it would do it. A robust relay sets the master to non-blocking
  mode, keeps a queue of pending input, and polls for `POLLOUT` when the
  queue is not empty. Exercise E.18.
- **Exit status.** A child killed by a signal has no code; like the
  shell, we report 128 + the signal number.

### 22.3 Portable PTYs: portable-pty

`portable-pty`, from the WezTerm terminal emulator, hides the platform
differences behind traits: Unix PTYs on Linux and macOS, ConPTY on
Windows 10 and later. Its `CommandBuilder` is like `Command`, and
`spawn_command` does the session and controlling-terminal setup.

```rust
// file: rust/src/bin/portable.rs
//! The same idea with portable-pty (from WezTerm): one API for Unix
//! PTYs and Windows ConPTY. Blocking reads, so a reader thread.
use portable_pty::{CommandBuilder, PtySize, native_pty_system};
use std::io::Read;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let pty_system = native_pty_system();
    let pair = pty_system.openpty(PtySize {
        rows: 24,
        cols: 80,
        pixel_width: 0,
        pixel_height: 0,
    })?;

    let mut cmd = CommandBuilder::new("python3");
    cmd.args([
        "-c",
        "import os,sys; print(sys.stdout.isatty(), os.get_terminal_size())",
    ]);
    let mut child = pair.slave.spawn_command(cmd)?;
    drop(pair.slave); // as always: drop our copy of the slave

    let mut reader = pair.master.try_clone_reader()?;
    let thread = std::thread::spawn(move || {
        let mut out = Vec::new();
        let mut buf = [0u8; 1024];
        // Ends with Ok(0) or an EIO error, depending on the platform.
        while let Ok(n) = reader.read(&mut buf) {
            if n == 0 {
                break;
            }
            out.extend_from_slice(&buf[..n]);
        }
        out
    });
    let status = child.wait()?;
    drop(pair.master); // lets the reader finish on every platform
    let out = thread.join().unwrap();
    print!("{}", String::from_utf8_lossy(&out).replace("\r\n", "\n"));
    println!("[{status:?}]");
    Ok(())
}
```

```text
$ cargo run -q --bin portable
True os.terminal_size(columns=80, lines=24)
[ExitStatus { code: 0, signal: None }]
```

The reader returned by `try_clone_reader` is a blocking `Read`, so the
usual structure is one thread for reading output and the main thread for
writing input and waiting (`take_writer` gives the writer). That is the
architecture of most Rust terminal emulators and of tools such as
`expectrl`. For an async program, wrap the reader in a task with
`tokio::task::spawn_blocking`, or use the master's raw descriptor
(`as_raw_fd()`) with `tokio::io::unix::AsyncFd`.

When should you use which?

| Need | Crate |
|------|-------|
| Linux/macOS only | `nix` |
| also Windows | `portable-pty` |
| async | `tokio` + `nix` |
| automation | `expectrl` |

---

## 23. Rust: TUIs with crossterm and ratatui

### 23.1 crossterm

crossterm is a cross-platform terminal library: raw mode, cursor,
colors, the alternate screen, and **input events** decoded from the
escape sequences of chapter 7 (or from the Windows console API). Most
Rust TUI programs use it, directly or through ratatui.

Its output API is a set of **commands** (`cursor::MoveTo(x, y)`,
`terminal::Clear(...)`, `style::SetForegroundColor(...)`) that implement
`Display` as their escape sequence. Two macros send them:

- `execute!(out, cmd1, cmd2, ...)`: write the commands and flush.
- `queue!(out, cmd1, cmd2, ...)`: write them to the buffer only; flush
  later. Building a whole frame with `queue!` and flushing once avoids
  flicker (chapter 7, "draw a frame in one write").

Its input API: `event::read()` blocks until an `Event` arrives;
`event::poll(timeout)` waits at most `timeout` and returns `true` if an
event is ready.

```rust
// file: rust/src/bin/events.rs
//! crossterm: raw mode, alternate screen, colors, and decoded input
//! events (keys, mouse, resize, focus, paste). Esc or q quits.
use crossterm::event::{
    self, DisableBracketedPaste, DisableFocusChange, DisableMouseCapture,
    EnableBracketedPaste, EnableFocusChange, EnableMouseCapture, Event,
    KeyCode,
};
use crossterm::style::Stylize;
use crossterm::{cursor, execute, queue, terminal};
use std::io::{self, Write};

fn main() -> io::Result<()> {
    let mut out = io::stdout();
    terminal::enable_raw_mode()?;
    execute!(
        out,
        terminal::EnterAlternateScreen,
        EnableMouseCapture,
        EnableBracketedPaste,
        EnableFocusChange,
        cursor::Hide
    )?;
    // Restore the terminal even if the code below panics.
    let default_hook = std::panic::take_hook();
    std::panic::set_hook(Box::new(move |info| {
        let _ = restore();
        default_hook(info);
    }));

    let result = run(&mut out);
    restore()?;
    result
}

fn run(out: &mut io::Stdout) -> io::Result<()> {
    let (cols, rows) = terminal::size()?;
    let mut lines: Vec<String> = vec![format!(
        "size {cols}x{rows}; press keys, click, resize, paste; q quits"
    )];
    loop {
        // Redraw: title, then the last events, newest at the bottom.
        let (_, rows) = terminal::size()?;
        queue!(
            out,
            terminal::Clear(terminal::ClearType::All),
            cursor::MoveTo(0, 0)
        )?;
        write!(out, "{}", " crossterm events ".black().on_cyan().bold())?;
        let keep = rows.saturating_sub(2) as usize;
        let start = lines.len().saturating_sub(keep);
        for (i, line) in lines[start..].iter().enumerate() {
            queue!(out, cursor::MoveTo(0, i as u16 + 1))?;
            write!(out, "{line}")?;
        }
        out.flush()?;

        let ev = event::read()?; // blocks; event::poll(timeout) does not
        let text = match &ev {
            Event::Key(k) => format!(
                "{} {:?} {:?} {:?}",
                "key".green(),
                k.code,
                k.modifiers,
                k.kind
            ),
            Event::Mouse(m) => format!(
                "{} {:?} at {},{}",
                "mouse".yellow(),
                m.kind,
                m.column,
                m.row
            ),
            Event::Resize(c, r) => format!("{} {c}x{r}", "resize".magenta()),
            Event::Paste(s) => format!("{} {s:?}", "paste".cyan()),
            Event::FocusGained => "focus gained".blue().to_string(),
            Event::FocusLost => "focus lost".blue().to_string(),
        };
        lines.push(text);
        if let Event::Key(k) = ev
            && matches!(k.code, KeyCode::Char('q') | KeyCode::Esc)
        {
            return Ok(()); // a "let chain" (edition 2024)
        }
    }
}

fn restore() -> io::Result<()> {
    execute!(
        io::stdout(),
        cursor::Show,
        DisableFocusChange,
        DisableBracketedPaste,
        DisableMouseCapture,
        terminal::LeaveAlternateScreen
    )?;
    terminal::disable_raw_mode()
}
```

The screen, after pressing `a`, Up, pasting the word "pasted", and
clicking at column 10, row 5:

```text
 crossterm events
size 80x24; press keys, click, resize, paste; q quits
key Char('a') KeyModifiers(0x0) Press
key Up KeyModifiers(0x0) Press
paste "pasted"
mouse Down(Left) at 9,4
```

What it sends to the terminal at startup, and when it quits:

```text
^[[?1049h                   alternate screen
^[[?1000h ^[[?1002h ^[[?1003h  mouse: clicks, drags, all motion
^[[?1015h ^[[?1006h         mouse coordinates: urxvt and SGR formats
^[[?2004h                   bracketed paste
^[[?1004h                   focus events
^[[?25l                     hide the cursor
...
^[[?25h ^[[?1004l ^[[?2004l ^[[?1006l ^[[?1015l
^[[?1003l ^[[?1002l ^[[?1000l ^[[?1049l
```

Every mode that is turned on is turned off at the end, in reverse order.
If the program died without that, the terminal would stay in the
alternate screen, report mouse motion as garbage characters, and so on;
`reset` fixes it. Hence the restore function called both normally and
from a **panic hook**: by default, a panic prints its message *on the
alternate screen*, which then disappears, and leaves the terminal in raw
mode. Installing a hook that restores the terminal first, then calls the
default hook, makes the panic message readable.

Things worth knowing about crossterm:

- **Coordinates are 0-based**, `(column, row)`: the click at the
  terminal's column 10, row 5 (SGR mouse report `ESC [ < 0 ; 10 ; 5 M`)
  is `at 9,4`.
- **Colors**: the named colors (`.green()`, `.on_cyan()`, from the
  `Stylize` trait) are sent as **256-color** indexes (`ESC [ 38 ; 5 ; 10
  m`), not as the classic `ESC [ 32 m`. They look the same in modern
  terminals. `Color::Rgb { r, g, b }` sends 24-bit color.
- **Key events** have a `kind` (`Press`, `Repeat`, `Release`). Only
  `Press` is reported unless you enable the kitty keyboard protocol
  (`PushKeyboardEnhancementFlags`), which also distinguishes keys that
  legacy encoding confuses (`^I` and Tab, `^M` and Enter, `^[` and Esc).
  On Windows, `Release` events come by default: filter on
  `KeyEventKind::Press`, as ptop does below.
- **Resize** arrives as an event (crossterm handles `SIGWINCH` itself).
- `event::read` must not be mixed with reading stdin otherwise: crossterm
  has its own buffer of parsed events.

### 23.2 ratatui: immediate-mode TUIs

ratatui (a community fork of the earlier `tui-rs`) draws widgets
(paragraphs, lists, tables, charts, gauges, tabs) into a buffer the size
of the screen. You describe the whole screen in a `draw` closure, every
frame; ratatui compares the new buffer with the previous one and sends
only the cells that changed. This is **immediate mode**: there is no
widget tree to keep in sync with your data. Your application owns its
state; the drawing code is a pure function of it.

The skeleton:

```rust
fn main() -> std::io::Result<()> {
    ratatui::run(|terminal| loop {
        terminal.draw(|frame| frame.render_widget("hello", frame.area()))?;
        if crossterm::event::read()?.is_key_press() {
            break Ok(());
        }
    })
}
```

`ratatui::run` initializes the terminal (raw mode, alternate screen, a
panic hook that restores the terminal), calls your closure with a
`Terminal`, and restores everything when the closure returns: the
crossterm boilerplate of 23.1, done once.

### 23.3 A process viewer for this tutorial

Our ratatui example shows the concepts of part 1 live: for every
process with a controlling terminal, its process group, session,
terminal, whether it is in the foreground of that terminal, and what its
descriptors 0, 1 and 2 are connected to.

```rust
// file: rust/src/bin/ptop.rs
//! ptop: the process table seen through the eyes of this tutorial.
//! Sessions, process groups, controlling terminals, foreground groups,
//! and where each process's stdin/stdout/stderr go (tty, pipe, file).
//! Keys: Up/Down (or j/k) select, t toggles "only processes with a tty",
//! q quits. Refreshes every second.
//!   ptop [TTY]     e.g. ptop pts/3: only the processes on that terminal
use crossterm::event::{self, Event, KeyCode, KeyEventKind};
use ratatui::layout::{Constraint, Layout};
use ratatui::style::{Color, Modifier, Style, Stylize};
use ratatui::text::Line;
use ratatui::widgets::{Block, Paragraph, Row, Table, TableState};
use ratatui::{DefaultTerminal, Frame};
use std::fs;
use std::time::Duration;

/// The fields of /proc/PID/stat that matter here.
struct Proc {
    pid: i32,
    comm: String,
    state: char,
    ppid: i32,
    pgrp: i32,
    sid: i32,
    tty: Option<String>, // decoded tty_nr
    tpgid: i32,          // foreground process group of that tty
}

impl Proc {
    fn read(pid: i32) -> Option<Proc> {
        let stat = fs::read_to_string(format!("/proc/{pid}/stat")).ok()?;
        // "1234 (some name) S 1 1234 ...": the name may contain spaces
        // and parentheses, so split at the *last* ')'.
        let open = stat.find('(')?;
        let close = stat.rfind(')')?;
        let comm = stat[open + 1..close].to_string();
        let f: Vec<&str> = stat[close + 2..].split(' ').collect();
        let num = |i: usize| f.get(i).and_then(|s| s.parse::<i32>().ok());
        Some(Proc {
            pid,
            comm,
            state: f.first()?.chars().next()?,
            ppid: num(1)?,
            pgrp: num(2)?,
            sid: num(3)?,
            tty: decode_tty(num(4)?),
            tpgid: num(5)?,
        })
    }

    /// In the foreground of its terminal?
    fn foreground(&self) -> bool {
        self.tty.is_some() && self.pgrp == self.tpgid
    }
}

/// tty_nr packs a device number: major in bits 8-15, minor in bits
/// 0-7 and 20-31. Unix 98 PTY slaves have majors 136-143.
fn decode_tty(nr: i32) -> Option<String> {
    if nr == 0 {
        return None;
    }
    let nr = nr as u32;
    let major = (nr >> 8) & 0xfff;
    let minor = (nr & 0xff) | ((nr >> 12) & 0xfff00);
    Some(match major {
        136..=143 => format!("pts/{}", (major - 136) * 256 + minor),
        4 if minor < 64 => format!("tty{minor}"),
        4 => format!("ttyS{}", minor - 64),
        _ => format!("{major}:{minor}"),
    })
}

/// What fd N of a process is: "tty", "pipe", "socket", "null", a path.
fn fd_kind(pid: i32, fd: u32) -> String {
    match fs::read_link(format!("/proc/{pid}/fd/{fd}")) {
        Err(_) => "-".into(), // closed, or not ours to see
        Ok(p) => {
            let s = p.to_string_lossy().into_owned();
            if s.starts_with("/dev/pts/") || s.starts_with("/dev/tty") {
                "tty".into()
            } else if s.starts_with("pipe:") {
                "pipe".into()
            } else if s.starts_with("socket:") {
                "sock".into()
            } else if s == "/dev/null" {
                "null".into()
            } else if s.starts_with("/dev/ptmx") {
                "ptmx".into()
            } else {
                "file".into()
            }
        }
    }
}

struct App {
    procs: Vec<Proc>,
    state: TableState,
    only_tty: bool,
    tty_filter: Option<String>,
}

impl App {
    fn refresh(&mut self) {
        let selected = self
            .state
            .selected()
            .and_then(|i| self.procs.get(i))
            .map(|p| p.pid);
        let mut procs: Vec<Proc> = fs::read_dir("/proc")
            .into_iter()
            .flatten()
            .flatten()
            .filter_map(|e| e.file_name().to_str()?.parse::<i32>().ok())
            .filter_map(Proc::read)
            .filter(|p| !self.only_tty || p.tty.is_some())
            .filter(|p| self.tty_filter.is_none() || p.tty == self.tty_filter)
            .collect();
        // Group the table by session, then process group, then pid.
        procs.sort_by_key(|p| (p.sid, p.pgrp, p.pid));
        self.procs = procs;
        // Keep the same process selected across refreshes if possible.
        let idx = selected
            .and_then(|pid| self.procs.iter().position(|p| p.pid == pid))
            .unwrap_or(0);
        self.state.select(if self.procs.is_empty() {
            None
        } else {
            Some(idx)
        });
    }

    fn draw(&mut self, frame: &mut Frame) {
        let [top, bottom, help] = Layout::vertical([
            Constraint::Min(5),
            Constraint::Length(4),
            Constraint::Length(1),
        ])
        .areas(frame.area());

        let header = Row::new([
            "PID", "PPID", "PGID", "SID", "TTY", "S", "0 1 2", "COMMAND",
        ])
        .style(Style::new().add_modifier(Modifier::BOLD).fg(Color::Yellow));
        let rows = self.procs.iter().map(|p| {
            let fds = format!(
                "{} {} {}",
                fd_kind(p.pid, 0),
                fd_kind(p.pid, 1),
                fd_kind(p.pid, 2)
            );
            let mut cmd = p.comm.clone();
            if p.pid == p.sid {
                cmd.push_str(" *"); // session leader
            }
            let row = Row::new([
                p.pid.to_string(),
                p.ppid.to_string(),
                p.pgrp.to_string(),
                p.sid.to_string(),
                p.tty.clone().unwrap_or_else(|| "?".into()),
                p.state.to_string(),
                fds,
                cmd,
            ]);
            if p.foreground() {
                row.style(Style::new().fg(Color::Green))
            } else {
                row
            }
        });
        let widths = [
            Constraint::Length(7),
            Constraint::Length(7),
            Constraint::Length(7),
            Constraint::Length(7),
            Constraint::Length(8),
            Constraint::Length(1),
            Constraint::Length(14),
            Constraint::Fill(1),
        ];
        let title = match (&self.tty_filter, self.only_tty) {
            (Some(t), _) => format!(" processes on {t} "),
            (None, true) => " processes with a tty ".into(),
            (None, false) => " all processes ".into(),
        };
        let table = Table::new(rows, widths)
            .header(header)
            .block(Block::bordered().title(title))
            .row_highlight_style(Style::new().reversed())
            .highlight_symbol("> ");
        frame.render_stateful_widget(table, top, &mut self.state);

        // Details of the selected process.
        let detail = match self.state.selected().and_then(|i| self.procs.get(i))
        {
            None => vec![Line::from("no process")],
            Some(p) => {
                let cmdline = fs::read(format!("/proc/{}/cmdline", p.pid))
                    .map(|b| String::from_utf8_lossy(&b).replace('\0', " "))
                    .unwrap_or_default();
                let fd = |n| {
                    fs::read_link(format!("/proc/{}/fd/{n}", p.pid))
                        .map(|t| t.display().to_string())
                        .unwrap_or_else(|_| "-".into())
                };
                vec![
                    Line::from(format!("cmdline: {}", cmdline.trim_end())),
                    Line::from(format!(
                        "stdin: {}  stdout: {}  stderr: {}",
                        fd(0),
                        fd(1),
                        fd(2)
                    )),
                ]
            }
        };
        frame.render_widget(
            Paragraph::new(detail).block(Block::bordered().title(" selected ")),
            bottom,
        );
        frame.render_widget(
            Line::from(concat!(
                " ↑↓/jk select  t tty only  q quit",
                "   green: foreground group   *: session leader"
            ))
            .dim(),
            help,
        );
    }

    fn run(&mut self, terminal: &mut DefaultTerminal) -> std::io::Result<()> {
        loop {
            self.refresh();
            terminal.draw(|f| self.draw(f))?;
            // Wait for input at most one second, then refresh anyway.
            if !event::poll(Duration::from_secs(1))? {
                continue;
            }
            if let Event::Key(k) = event::read()? {
                if k.kind != KeyEventKind::Press {
                    continue;
                }
                match k.code {
                    KeyCode::Char('q') | KeyCode::Esc => return Ok(()),
                    KeyCode::Down | KeyCode::Char('j') => {
                        self.state.select_next()
                    }
                    KeyCode::Up | KeyCode::Char('k') => {
                        self.state.select_previous()
                    }
                    KeyCode::Char('t') => self.only_tty = !self.only_tty,
                    _ => {}
                }
            }
        }
    }
}

fn main() -> std::io::Result<()> {
    let tty_filter = std::env::args()
        .nth(1)
        .map(|t| t.trim_start_matches("/dev/").to_string());
    let mut app = App {
        procs: Vec::new(),
        state: TableState::default(),
        only_tty: true,
        tty_filter,
    };
    // ratatui::run: init (raw mode, alternate screen, panic hook),
    // call the closure, restore.
    ratatui::run(|terminal| app.run(terminal))
}
```

Running it in a shell where `sleep 60 | cat &` was started in the
background, and selecting `sleep`:

```text
$ sleep 60 | cat &
$ cargo run -q --bin ptop -- $(tty)
┌ processes on pts/15 ─────────────────────────────────────────────────────────────┐
│  PID     PPID    PGID    SID     TTY      S 0 1 2          COMMAND               │
│  949491  949490  949491  949491  pts/15   S tty tty tty    bash *                │
│> 949496  949491  949496  949491  pts/15   S tty pipe tty   sleep                 │
│  949497  949491  949496  949491  pts/15   S pipe tty tty   cat                   │
│  949499  949491  949499  949491  pts/15   R tty tty tty    ptop                  │
│                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────┘
┌ selected ────────────────────────────────────────────────────────────────────────┐
│cmdline: sleep 60                                                                 │
│stdin: /dev/pts/15  stdout: pipe:[20244970]  stderr: /dev/pts/15                  │
└──────────────────────────────────────────────────────────────────────────────────┘
 ↑↓/jk select  t tty only  q quit   green: foreground group   *: session leader
```

Read it with chapters 3 to 5 in mind:

- `bash` is the **session leader** (PID = SID = 949491) of the session
  attached to `pts/15`.
- The background job `sleep 60 | cat` is **one process group**, 949496,
  led by its first process: the shell put both processes in it.
- `sleep`'s stdout and `cat`'s stdin are the two ends of one **pipe**.
- `ptop` itself has its own group, 949499, which is the **foreground
  group** of `pts/15` (shown in green on screen): the shell gave it the
  terminal with `tcsetpgrp`. If you press `^C`... nothing, since ptop is
  in raw mode; it is `q` that quits. In cooked mode, `^C` would send
  `SIGINT` to group 949499 only, and the background job would survive.

How it is built:

- **`/proc/PID/stat`** gives everything in one line: state, parent, group,
  session, `tty_nr` (the controlling terminal as a device number) and
  `tpgid` (the foreground group of that terminal). The command name is
  in parentheses and may contain spaces and parentheses itself, hence the
  `rfind(')')`. `ps` and `top` parse the same file.
- **`/proc/PID/fd/N`** are symbolic links to what the descriptor is
  open on: a path, or `pipe:[inode]`, `socket:[inode]`. Two processes
  connected by the same pipe show the same inode. We can only read them
  for our own processes (unless root), which is why some rows show `-`.
- **Layout**: `Layout::vertical([...]).areas(frame.area())` splits the
  screen into three areas; `Constraint::Min(5)` takes what remains,
  `Length(n)` is fixed.
- **Stateful widgets**: a `Table` with a `TableState` (which row is
  selected, and the scroll offset) is drawn with
  `render_stateful_widget`. The state lives in our `App` between frames;
  `select_next`/`select_previous` move the selection, and ratatui scrolls
  to keep it visible.
- **Refresh without threads**: `event::poll(1s)` waits for a key at most
  one second; if none comes, we loop, re-read `/proc`, and redraw. Since
  ratatui only sends the cells that changed, a redraw where nothing
  changed sends almost nothing.

### 23.4 Testing TUIs

Two techniques were used for this chapter:

- **ratatui's `TestBackend`**: `Terminal::new(TestBackend::new(80, 24))`
  draws into memory; `terminal.backend().buffer()` can be compared with
  an expected screen in a unit test. No terminal needed.
- **A real terminal emulator, headless**: run the program in a
  detached `tmux` session of a known size, send keys with `tmux
  send-keys`, and capture the screen as text with `tmux capture-pane
  -p`. The ptop screenshot above was made that way:

  ```sh
  tmux -L test new-session -d -x 84 -y 16 -s s 'bash --norc'
  tmux -L test send-keys -t s 'sleep 60 | cat & ptop $(tty)' Enter
  sleep 1.2
  tmux -L test send-keys -t s j
  tmux -L test capture-pane -p -t s
  tmux -L test kill-server
  ```

  `-L test` uses a private tmux server (a separate socket), so the test
  cannot disturb your own tmux sessions.

### 23.5 Rust: summary

| Topic | Rust tool |
|-------|-----------|
| processes | `std::process` |
| pipes | `std::io::pipe` |
| fork/exec | `nix::unistd` |
| signals | `signal-hook` |
| termios | `nix::sys::termios` |
| PTY | `nix::pty` |
| PTY, Windows | `portable-pty` |
| terminal I/O | `crossterm` |
| TUI | `ratatui` |

Rust's strengths here: ownership makes descriptor bookkeeping (who closes
what, and when) a compile-time matter; `Drop` guards make terminal
restoration reliable; the standard library's `Command` does the
fork/exec dance correctly, including the close-on-exec error pipe and the
`SIGPIPE` reset. The traps are few but real: `SIGPIPE` ignored by
default, `println!` panicking on a closed pipe, the `Command` that keeps
its pipe ends alive, C-created descriptors without `O_CLOEXEC`.

---

## 24. Go: the ecosystem

Go is a compiled, garbage-collected language designed at Google for
servers and command-line tools. It is a natural fit for our subject:
its standard library has a good process API, its goroutines make the
"copy bytes in both directions at once" problem of PTYs trivial, and the
Charm libraries (Bubble Tea and friends) are among the best TUI toolkits
in any language. Many well-known terminal programs are written in Go:
`fzf`, `lazygit`, `glow`, `gum`, `k9s`, the GitHub CLI.

### 24.1 Installing

Download the archive from <https://go.dev/dl/> and unpack it in
`/usr/local`, or use your package manager (`pacman -S go`, `apt install
golang`, `brew install go`). Distribution packages are fine for Go, which
keeps strong compatibility guarantees. The examples were tested with Go
1.27.

```text
$ go version
go version go1.27.4 linux/amd64
$ go env GOPATH GOPROXY
/home/me/go
https://proxy.golang.org,direct
```

There is one tool, `go`, and it does everything:

| Command | Purpose |
|---------|---------|
| `go run` | build, run |
| `go build` | compile |
| `go install` | install tool |
| `go test` | run tests |
| `go vet` | static checks |
| `gofmt -w` | format |
| `go mod tidy` | sync deps |
| `go get` | add a dep |
| `go doc` | API docs |

A Go release comes every six months (February and August), and the **Go
1 compatibility promise** says that programs keep compiling. The `go`
line in `go.mod` states the language version a module needs. Since Go
1.21, the `go` command can even download a newer toolchain by itself
when a module asks for it (the `toolchain` directive).

### 24.2 Modules and packages

Code is organized in **packages** (a directory of `.go` files with the
same `package` line) inside a **module** (a tree of packages with a
`go.mod` file at its root). Package `main` with a `func main()` is a
program. A module is named by an import path, usually its repository URL;
for local experiments any name works:

```text
$ mkdir go && cd go
$ go mod init termtut
go: creating new go.mod: module termtut
```

Our examples use one module with one directory per program, the usual
layout for a repository with several commands:

```text
go/
├── go.mod
├── go.sum
└── cmd/
    ├── run/main.go         chapter 25
    ├── pipeline/main.go
    ├── merge/main.go
    ├── sigpipe/main.go
    ├── signals/main.go
    ├── rawkeys/main.go     chapter 26
    ├── ttyinfo/main.go
    ├── getpass/main.go
    ├── lineedit/main.go
    ├── ptyspawn/main.go    chapter 27
    ├── ptyscript/main.go
    ├── expect/main.go
    ├── launcher/main.go    chapter 28
    └── sshtty/main.go
```

```text
$ go run ./cmd/run                 build in a cache, run
$ go build -o bin/ ./cmd/...       build all programs into bin/
$ bin/run
```

**Dependencies** come from their source repositories, through a
**module proxy** (`proxy.golang.org` by default) that caches them, and
are checked against a public **checksum database** (`sum.golang.org`).
There is no central registry where packages are "published": a module
exists as soon as it has a tagged version in a public repository.
<https://pkg.go.dev> indexes them and shows their documentation.

```text
$ go get github.com/creack/pty@v1.1.24
$ go get golang.org/x/term@latest
$ go get charm.land/bubbletea/v2@latest
```

After `go mod tidy`, the `require` block of our `go.mod` lists the direct
dependencies (and, in a second block, 60-odd indirect ones):

```text
module termtut

go 1.27.4

require (
	charm.land/bubbles/v2 v2.2.1
	charm.land/bubbletea/v2 v2.1.0
	charm.land/lipgloss/v2 v2.0.6
	charm.land/log/v2 v2.0.1
	charm.land/ssh v0.4.3
	charm.land/wish/v2 v2.0.5
	github.com/creack/pty v1.1.24
	golang.org/x/sys v0.50.0
	golang.org/x/term v0.47.0
)
```

Some rules of Go versioning that surprise newcomers:

- **Major versions are part of the import path.** Version 2 of Bubble
  Tea is `charm.land/bubbletea/v2`, a different path from v1, so a program
  can even use both. Forgetting the `/v2` silently gets you v1.
- **Minimal version selection**: Go uses the *lowest* version that
  satisfies every requirement, not the newest available. Builds are
  reproducible without a lock file; `go.sum` holds only checksums.
- **Vanity import paths**: `charm.land/...` and `golang.org/x/...` are
  not hosting sites, but HTML pages that redirect the `go` tool to the
  real repository. The Charm libraries moved from
  `github.com/charmbracelet/...` to `charm.land/...` with their v2
  releases; old tutorials use the old paths and the v1 APIs.
- The `golang.org/x/...` modules (`x/term`, `x/sys`, `x/crypto`) are
  maintained by the Go team but outside the standard library, with looser
  compatibility rules.

### 24.3 Building

```text
$ go build -o bin/ ./cmd/...
$ ls -l bin/run bin/launcher bin/sshtty
-rwxr-xr-x 1 me me  3076209 Nov 22 18:04 bin/run
-rwxr-xr-x 1 me me  6036144 Nov 22 18:04 bin/launcher
-rwxr-xr-x 1 me me 11232606 Nov 22 18:04 bin/sshtty
$ file bin/run
bin/run: ELF 64-bit LSB executable, x86-64, ..., statically linked
```

- Binaries are **statically linked** by default (Go has its own runtime
  and, for most programs, does not use libc; `os/user` and `net` can use
  cgo for name resolution). Copy the file to another Linux machine and it
  runs.
- They are large: 3 MB for a program that runs `echo`, because the
  runtime and the reflection data for `fmt` are included.
  `-ldflags='-s -w'` removes the symbol tables (6.0 MB to 4.1 MB for the
  launcher).
- Compilation is fast: building the launcher and its 70 dependencies
  from an empty cache takes 7 seconds here; rebuilding after an edit, a
  fraction of a second.
- **Cross-compiling** is a matter of environment variables:
  `GOOS=darwin GOARCH=arm64 go build ./cmd/run` builds a macOS binary.
  Code that is specific to a system goes in files with build constraints
  (`//go:build linux`, or a name like `pty_linux.go`).

### 24.4 The language in one page

Enough Go to read the examples:

- **Errors are values.** Functions return `(result, error)`; you check
  `if err != nil`. `errors.Is(err, syscall.EPIPE)` tests for a specific
  error in a chain of wrapped errors, `errors.As(err, &target)` extracts
  a specific error type (we use it for `*exec.ExitError`).
- **`defer f()`** runs `f` when the surrounding function returns,
  normally or by panic. It is how files are closed and terminals restored.
  **But `os.Exit` does not run deferred calls**, so the usual structure
  is `func main() { os.Exit(run()) }`, with the defers in `run`.
- **Goroutines** (`go f()`) are cheap threads managed by the runtime,
  scheduled onto a few OS threads. A blocking `read` in one goroutine does
  not block the others.
- **Channels** (`chan T`) pass values between goroutines; `select` waits
  on several channels at once. Signals arrive on channels too.
- **Interfaces** are satisfied implicitly. The two that matter here are
  `io.Reader` and `io.Writer`; `*os.File`, network connections, SSH
  sessions and `bytes.Buffer` all implement them, and
  `io.Copy(dst, src)` moves bytes from any reader to any writer.

**Go and `fork`.** The Go runtime is always multi-threaded (garbage
collector, scheduler), and a forked child of a multi-threaded process may
only call async-signal-safe functions until it execs (chapter 10). So Go
does not offer `fork` at all. It offers **fork-and-exec in one call**
(`syscall.ForkExec`, used by `os.StartProcess`, used by `os/exec`),
implemented on Linux with `clone(CLONE_VFORK | CLONE_VM)` and a child
side written with raw system calls only. Everything a child needs before
`exec` (new session, controlling terminal, process group, credentials)
is requested declaratively in a `syscall.SysProcAttr` struct. You will
see it in chapter 27.

---

## 25. Go: pipes and processes

### 25.1 os/exec

`exec.Command(name, args...)` returns a `*exec.Cmd`, a struct you fill
in before starting it:

| Field | Meaning |
|-------|---------|
| `Stdin` | `io.Reader` |
| `Stdout` | `io.Writer` |
| `Stderr` | `io.Writer` |
| `Env` | environment |
| `Dir` | directory |
| `ExtraFiles` | fds 3, 4... |
| `SysProcAttr` | setsid etc. |

and then one of:

| Method | Effect |
|--------|--------|
| `Run()` | start, wait |
| `Output()` | capture stdout |
| `CombinedOutput()` | stdout+stderr |
| `Start()` | start only |
| `Wait()` | wait |

```go
// file: go/cmd/run/main.go
// os/exec: the four ways of running a program.
package main

import (
	"bytes"
	"errors"
	"fmt"
	"io"
	"os"
	"os/exec"
	"strings"
	"syscall"
	"time"
)

func main() {
	// 1. Inherit our stdin, stdout and stderr; just wait.
	cmd := exec.Command("echo", "hello from echo")
	cmd.Stdout = os.Stdout // nil would mean /dev/null
	if err := cmd.Run(); err != nil {
		fmt.Println("run:", err)
	}
	fmt.Println("exit code:", cmd.ProcessState.ExitCode())

	// 2. Capture stdout and stderr separately.
	var stdout, stderr bytes.Buffer
	cmd = exec.Command("sh", "-c", "echo out; echo err >&2; exit 3")
	cmd.Stdout, cmd.Stderr = &stdout, &stderr
	err := cmd.Run()
	var exitErr *exec.ExitError
	if errors.As(err, &exitErr) {
		fmt.Printf("stdout=%q stderr=%q code=%d\n",
			strings.TrimSpace(stdout.String()),
			strings.TrimSpace(stderr.String()), exitErr.ExitCode())
	}

	// 3. Feed stdin from a string, get stdout as bytes.
	cmd = exec.Command("sort")
	cmd.Stdin = strings.NewReader("pear\napple\nfig\n")
	out, err := cmd.Output()
	if err != nil {
		panic(err)
	}
	fmt.Print("sorted:\n", string(out))

	// 4. Start, then kill: no exit code, a signal instead.
	cmd = exec.Command("sleep", "10")
	if err := cmd.Start(); err != nil {
		panic(err)
	}
	time.Sleep(100 * time.Millisecond)
	cmd.Process.Kill()
	err = cmd.Wait()
	ws := cmd.ProcessState.Sys().(syscall.WaitStatus)
	fmt.Printf("sleep: %v; code=%d signaled=%v signal=%v\n",
		err, cmd.ProcessState.ExitCode(), ws.Signaled(), ws.Signal())

	// 5. A program that does not exist: the error comes from LookPath.
	err = exec.Command("no-such-program").Run()
	fmt.Printf("run failed: %v (ErrNotFound: %v)\n",
		err, errors.Is(err, exec.ErrNotFound))

	// 6. Write to stdin through a pipe, read stdout through another.
	cmd = exec.Command("tr", "a-z", "A-Z")
	in, _ := cmd.StdinPipe()
	outPipe, _ := cmd.StdoutPipe()
	cmd.Start()
	go func() {
		defer in.Close() // EOF for tr
		io.WriteString(in, "shout\n")
	}()
	b, _ := io.ReadAll(outPipe) // read everything before Wait
	cmd.Wait()
	fmt.Print("tr: ", string(b))

	// 7. Environment and working directory.
	cmd = exec.Command("sh", "-c", `echo "$GREETING from $(pwd)"`)
	cmd.Env = append(os.Environ(), "GREETING=bonjour")
	cmd.Dir = "/usr"
	cmd.Stdout = os.Stdout
	cmd.Run()
}
```

```text
$ go run ./cmd/run
hello from echo
exit code: 0
stdout="out" stderr="err" code=3
sorted:
apple
fig
pear
sleep: signal: killed; code=-1 signaled=true signal=killed
run failed: exec: "no-such-program": executable file not found in $PATH (ErrNotFound: true)
tr: SHOUT
bonjour from /usr
```

The rules that make `os/exec` simple and sometimes surprising:

- **A nil stream is `/dev/null`**, not the parent's stream. Unlike
  Rust's `Command::status()`, a Go `Cmd` inherits nothing by default; you
  write `cmd.Stdout = os.Stdout` to inherit.
- **Any `io.Reader` or `io.Writer` works**, not only files. If the value
  is an `*os.File`, the child gets that descriptor directly. Otherwise
  (a `bytes.Buffer`, a `strings.Reader`), `os/exec` creates a pipe and a
  goroutine that copies between the pipe and your value, and `Wait`
  waits for that copying to finish. This is why example 2 can capture
  stdout and stderr into two buffers with no risk of the two-pipe
  deadlock: two goroutines drain the two pipes concurrently.
- **That `Wait` can hang** if the child starts a background process that
  inherits the pipe: the copying goroutine waits for EOF, which only
  comes when the grandchild exits too. `cmd.WaitDelay` (Go 1.20) bounds
  that wait. The same applies to `Output()` and `CombinedOutput()`.
- **`ExitCode()` is -1** when the process was killed by a signal. To get
  the signal, look at the system-specific `syscall.WaitStatus`.
- **`exec.Command` looks up the program with `exec.LookPath`** when it is
  created; a failure is reported by `Run` or `Start`. Since Go 1.19,
  `LookPath` refuses to run a program found through a relative `PATH`
  entry such as `.` (error `exec.ErrDot`), a security fix for a classic
  Windows problem.
- **`StdinPipe` and `StdoutPipe`** return the parent's ends of new pipes.
  The documentation insists on an ordering rule: read everything from
  `StdoutPipe` *before* calling `Wait`, since `Wait` closes the pipe.
  And close the `StdinPipe` writer when done, or the child waits for
  more input forever. Example 6 writes from a goroutine, so that a
  large input cannot block us while the child's output pipe fills up.
- **No shell.** Arguments go directly to `execve`. `sh -c` is explicit.
- **`exec.CommandContext(ctx, ...)`** kills the child (with `SIGKILL`, or
  whatever function you put in `cmd.Cancel`) when the context is
  cancelled: the idiomatic timeout.
- All descriptors Go opens are **close-on-exec**. To pass more than 0, 1
  and 2 to a child, put files in `cmd.ExtraFiles`: the first one becomes
  descriptor 3 in the child.

### 25.2 Pipelines

```go
// file: go/cmd/pipeline/main.go
// ls /usr/bin | grep -c '^z' -- two ways.
package main

import (
	"fmt"
	"os"
	"os/exec"
	"strings"
)

func main() {
	// With StdoutPipe: the read end goes to grep, the kernel does the rest.
	ls := exec.Command("ls", "/usr/bin")
	grep := exec.Command("grep", "-c", "^z")
	r, err := ls.StdoutPipe()
	if err != nil {
		panic(err)
	}
	grep.Stdin = r
	var out strings.Builder
	grep.Stdout = &out
	must(ls.Start())
	must(grep.Start())
	must(ls.Wait()) // closes our copy of the read end too
	must(grep.Wait())
	fmt.Print("matches (StdoutPipe): ", out.String())

	// With os.Pipe: we own both ends and must close them ourselves.
	pr, pw, err := os.Pipe()
	must(err)
	ls = exec.Command("ls", "/usr/bin")
	grep = exec.Command("grep", "-c", "^z")
	ls.Stdout, grep.Stdin = pw, pr
	grep.Stdout = os.Stdout
	must(ls.Start())
	must(grep.Start())
	pw.Close() // otherwise grep never sees EOF
	pr.Close()
	fmt.Print("matches (os.Pipe):    ")
	must(ls.Wait())
	must(grep.Wait())
}

func must(err error) {
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
```

```text
$ go run ./cmd/pipeline
matches (StdoutPipe): 41
matches (os.Pipe):    41
```

With `StdoutPipe`, `os/exec` creates the pipe, gives the write end to
`ls` and closes the parent's copy of it at `Start`. The read end is an
`*os.File`, so `grep` receives it directly as its stdin (no copying
goroutine). With `os.Pipe` we create both ends and must close our copies
after the `Start`s, exactly as in C: an extra copy of the write end in
our process means `grep` never sees EOF.

### 25.3 Merging stdout and stderr

```go
// file: go/cmd/merge/main.go
// 2>&1 into one pipe; the CombinedOutput shortcut; the Cmd.Wait trap.
package main

import (
	"bufio"
	"fmt"
	"os"
	"os/exec"
)

const script = "echo one; echo two >&2; echo three"

func main() {
	// The easy way.
	out, _ := exec.Command("sh", "-c", script).CombinedOutput()
	fmt.Printf("combined: %q\n", out)

	// By hand, to read the lines as they come.
	r, w, err := os.Pipe()
	if err != nil {
		panic(err)
	}
	cmd := exec.Command("sh", "-c", script)
	cmd.Stdout, cmd.Stderr = w, w // the same *os.File: one descriptor
	if err := cmd.Start(); err != nil {
		panic(err)
	}
	w.Close() // the child has its copy; drop ours
	sc := bufio.NewScanner(r)
	for sc.Scan() {
		fmt.Println("line:", sc.Text())
	}
	cmd.Wait()
}
```

```text
$ go run ./cmd/merge
combined: "one\ntwo\nthree\n"
line: one
line: two
line: three
```

Setting `Stdout` and `Stderr` to the **same `*os.File`** gives the child
the same descriptor twice, like `2>&1`, and the lines stay in order.
`CombinedOutput` does the same with a buffer: when `Stdout` and `Stderr`
are the same writer (compared with `==`), `os/exec` uses one pipe and
one goroutine for both.

### 25.4 SIGPIPE in Go

Go's rule, from the `os/signal` documentation: if a program writes to a
broken pipe on descriptor **1 or 2**, it is killed by `SIGPIPE`, like a
C program. On **any other** descriptor (a socket, a pipe you created),
the write fails with `EPIPE` and the program continues, like Rust. The
intent is that command-line tools behave in pipelines, and servers do
not die when a client goes away.

```go
// file: go/cmd/sigpipe/main.go
// Write lines forever; run it as "sigpipe | head -3".
package main

import (
	"bufio"
	"errors"
	"fmt"
	"os"
	"os/signal"
	"syscall"
)

func main() {
	if len(os.Args) > 1 && os.Args[1] == "--ignore" {
		// With SIGPIPE ignored, the write fails with EPIPE instead.
		signal.Ignore(syscall.SIGPIPE)
	}
	w := bufio.NewWriter(os.Stdout)
	for i := 1; ; i++ {
		fmt.Fprintf(w, "line %d\n", i)
		if err := w.Flush(); err != nil {
			fmt.Fprintln(os.Stderr, "write error:", err,
				errors.Is(err, syscall.EPIPE))
			os.Exit(0)
		}
	}
}
```

```text
$ ./sigpipe | head -3; echo ${PIPESTATUS[0]}
line 1
line 2
line 3
141
$ ./sigpipe --ignore | head -3; echo ${PIPESTATUS[0]}
line 1
line 2
line 3
write error: write /dev/stdout: broken pipe true
0
```

So Go gets the conventional behavior by default (status 141, silence),
which is what you want for filters. Calling `signal.Notify` for `SIGPIPE`
or `signal.Ignore` changes it: the write returns `EPIPE`, and you handle
it like any error.

### 25.5 Signals

```go
// file: go/cmd/signals/main.go
// Signals arrive as values on a channel.
package main

import (
	"fmt"
	"os"
	"os/signal"
	"syscall"
)

func main() {
	fmt.Printf("pid %d; ^C three times to quit\n", os.Getpid())
	ch := make(chan os.Signal, 8)
	signal.Notify(ch, syscall.SIGINT, syscall.SIGTERM, syscall.SIGHUP,
		syscall.SIGUSR1)
	ints := 0
	for sig := range ch {
		switch sig {
		case syscall.SIGINT:
			ints++
			fmt.Printf("got SIGINT #%d\n", ints)
			if ints == 3 {
				goto done
			}
		case syscall.SIGTERM:
			fmt.Println("SIGTERM: cleaning up")
			goto done
		default:
			fmt.Printf("got %v (%d)\n", sig, sig.(syscall.Signal))
		}
	}
done:
	signal.Stop(ch) // a second ^C would now kill us the normal way
	fmt.Println("bye")
}
```

```text
$ ./signals &
pid 971981; ^C three times to quit
$ kill -INT %1; kill -HUP %1; kill -USR1 %1; kill -TERM %1
got SIGINT #1
got hangup (1)
got user defined signal 1 (10)
SIGTERM: cleaning up
bye
```

`signal.Notify` is the only signal API you need. The Go runtime installs
real handlers for every signal and turns their arrival into values sent
on your channel (with a non-blocking send, so the channel must be
buffered: a signal that arrives while the channel is full is dropped).
Your code runs in a normal goroutine and can do anything. Other functions
worth knowing:

- `signal.Stop(ch)` stops delivery to `ch`; when no channel wants a
  signal, its default action is restored.
- `signal.Ignore(sigs...)` and `signal.Reset(sigs...)`.
- `signal.NotifyContext(ctx, os.Interrupt)` returns a context cancelled
  on the first `^C`: perfect with `exec.CommandContext`.

A subtle point about **children and `^C`**: the terminal sends `SIGINT`
to the whole foreground process group, so a Go program and the children
it started with `os/exec` all receive it (they are in the same group,
unless `SysProcAttr.Setpgid` is set). If your program catches `SIGINT` to
clean up, the children have already been interrupted. Shells and editors
that run interactive children ignore `SIGINT` while waiting for them.

Signals that Go programs get by default and C programs do not: the Go
runtime uses `SIGURG` internally to preempt goroutines, so `strace` of a
Go program shows a stream of them. They are harmless, and a reason not
to use `SIGURG` for anything in Go programs.

---

## 26. Go: terminals with x/term

The standard library knows nothing about terminals. The
`golang.org/x/term` package, maintained by the Go team, covers the
basics, and `golang.org/x/sys/unix` gives access to every system call
and ioctl:

| Function | Purpose |
|----------|---------|
| `IsTerminal` | isatty |
| `MakeRaw` | raw mode |
| `Restore` | restore modes |
| `GetSize` | window size |
| `ReadPassword` | no echo |
| `NewTerminal` | line editor |

### 26.1 Raw mode

```go
// file: go/cmd/rawkeys/main.go
// Raw mode with x/term: show the bytes each key sends.
package main

import (
	"fmt"
	"os"
	"strings"

	"golang.org/x/term"
)

func main() {
	fd := int(os.Stdin.Fd())
	if !term.IsTerminal(fd) {
		fmt.Fprintln(os.Stderr, "stdin is not a terminal")
		os.Exit(1)
	}
	old, err := term.MakeRaw(fd)
	if err != nil {
		panic(err)
	}
	defer term.Restore(fd, old) // runs on return, and on panic

	fmt.Print("raw mode: press keys, q quits\r\n")
	buf := make([]byte, 32)
	for {
		n, err := os.Stdin.Read(buf)
		if err != nil || n == 0 {
			return
		}
		b := buf[:n]
		hex := make([]string, n)
		for i, c := range b {
			hex[i] = fmt.Sprintf("%02x", c)
		}
		fmt.Printf("%d byte(s): %s   %s\r\n", n, strings.Join(hex, " "),
			visible(b))
		if n == 1 && b[0] == 'q' {
			fmt.Print("bye\r\n")
			return
		}
	}
}

// visible shows control characters as ^X.
func visible(b []byte) string {
	var sb strings.Builder
	for _, r := range string(b) {
		switch {
		case r < 0x20:
			sb.WriteString("^" + string(rune(r+'@')))
		case r == 0x7f:
			sb.WriteString("^?")
		default:
			sb.WriteRune(r)
		}
	}
	return sb.String()
}
```

```text
$ go run ./cmd/rawkeys
raw mode: press keys, q quits
1 byte(s): 61   a
3 byte(s): 1b 5b 41   ^[[A
1 byte(s): 03   ^C
2 byte(s): c3 a9   é
1 byte(s): 71   q
bye
```

`term.MakeRaw` does what `cfmakeraw` does (chapter 11): it turns off
`ICANON`, `ECHO`, `ISIG`, `IEXTEN`, the input translations and `OPOST`,
and sets `VMIN = 1`, `VTIME = 0`. It returns the previous state, an
opaque `*term.State` to give back to `term.Restore`, here with `defer`.

Remember the trap of 24.4: a `defer` does not run on `os.Exit`, nor when
the program is killed by a signal. `log.Fatal` calls `os.Exit`, so a
`log.Fatal` in raw mode leaves the terminal raw. Return errors to `main`
instead, restore, then exit.

Go's `os.Stdout` is **not buffered** (each `Print` is one `write`), so no
flushing is needed; for heavy output, wrap it in a `bufio.Writer`. And
`os.Stdin.Read` reads the descriptor directly, so it mixes well with raw
mode: a read returns what the terminal had, one key or a whole escape
sequence.

### 26.2 Sessions, foreground group, window size

`x/sys/unix` has the generic ioctl helpers: `IoctlGetInt`,
`IoctlSetPointerInt`, `IoctlGetWinsize`, `IoctlSetWinsize`,
`IoctlGetTermios`, `IoctlSetTermios`. With them, any terminal ioctl of
chapter 4 is one line.

```go
// file: go/cmd/ttyinfo/main.go
// Process group, session, controlling terminal, window size.
package main

import (
	"fmt"
	"os"
	"os/signal"
	"syscall"

	"golang.org/x/sys/unix"
	"golang.org/x/term"
)

func main() {
	fd := int(os.Stdin.Fd())
	sid, _ := unix.Getsid(0)
	fmt.Printf("pid  %-8d ppid %d\n", os.Getpid(), os.Getppid())
	fmt.Printf("pgid %-8d sid  %d\n", unix.Getpgrp(), sid)
	if !term.IsTerminal(fd) {
		fmt.Println("stdin is not a terminal")
		return
	}
	name, _ := os.Readlink("/proc/self/fd/0") // Go has no ttyname()
	fmt.Println("tty ", name)
	fg, err := unix.IoctlGetInt(fd, unix.TIOCGPGRP) // tcgetpgrp()
	if err != nil {
		panic(err)
	}
	who := "another group"
	if fg == unix.Getpgrp() {
		who = "us"
	}
	fmt.Printf("foreground pgid %d (%s)\n", fg, who)
	ws, _ := unix.IoctlGetWinsize(fd, unix.TIOCGWINSZ)
	fmt.Printf("size %dx%d\n", ws.Row, ws.Col)

	if len(os.Args) > 1 && os.Args[1] == "--watch" {
		fmt.Println("resize the window; ^C to quit")
		ch := make(chan os.Signal, 1)
		signal.Notify(ch, syscall.SIGWINCH, syscall.SIGINT)
		for sig := range ch {
			if sig == syscall.SIGINT {
				fmt.Println()
				return
			}
			w, h, _ := term.GetSize(fd) // the portable way
			fmt.Printf("SIGWINCH: now %dx%d\n", h, w)
		}
	}
}
```

```text
$ go run ./cmd/ttyinfo --watch
pid  974627   ppid 974626
pgid 974627   sid  974627
tty  /dev/pts/14
foreground pgid 974627 (us)
size 24x80
resize the window; ^C to quit
SIGWINCH: now 40x120
^C
```

(That run was under the 24x80 test harness, which resizes its PTY to
40x120 after a moment; in a terminal emulator, resize the window.)

Note `go run`: it builds the program and runs it as a **child**, in the
same process group. So `ppid` is the `go` command, and `^C` reaches both.

### 26.3 Passwords

```go
// file: go/cmd/getpass/main.go
// Read a password from the terminal, even when stdin is redirected.
package main

import (
	"fmt"
	"os"

	"golang.org/x/term"
)

func main() {
	tty, err := os.OpenFile("/dev/tty", os.O_RDWR, 0)
	if err != nil {
		fmt.Fprintln(os.Stderr, "no controlling terminal:", err)
		os.Exit(1)
	}
	defer tty.Close()
	fmt.Fprint(tty, "Password: ")
	pw, err := term.ReadPassword(int(tty.Fd())) // echo off, then restored
	fmt.Fprintln(tty)
	if err != nil {
		panic(err)
	}
	fmt.Printf("read %d characters\n", len([]rune(string(pw))))
}
```

```text
$ echo data | go run ./cmd/getpass
Password:
read 8 characters
```

`ReadPassword` turns off `ECHO` (keeping `ICANON`, so the line is still
editable with backspace), reads a line, and restores the modes. We open
`/dev/tty` so that the prompt works when stdin is a pipe, as `ssh` and
`sudo` do (chapter 5). The count is in runes: the test typed `hunter2é`,
nine bytes, eight characters.

### 26.4 A line editor in the box

`term.NewTerminal` wraps any `io.ReadWriter` (in raw mode) in a small
line editor, written for `golang.org/x/crypto/ssh` servers: arrows,
history, Home/End, `^A` `^E` `^K` `^U` `^W` `^L`, bracketed paste, a
completion callback. Writes to the `Terminal` are converted for raw
mode (`\n` to `\r\n`) and redrawn around the input line, so a goroutine
can print while the user types.

```go
// file: go/cmd/lineedit/main.go
// x/term's small line editor: history, arrows, ^A ^E ^K ^W, tab completion.
package main

import (
	"fmt"
	"io"
	"os"
	"strings"

	"golang.org/x/term"
)

var words = []string{"help", "history", "hello", "quit"}

func main() {
	fd := int(os.Stdin.Fd())
	old, err := term.MakeRaw(fd)
	if err != nil {
		panic(err)
	}
	defer term.Restore(fd, old)

	// The Terminal writes to the screen itself (in raw mode, with \r\n).
	rw := struct {
		io.Reader
		io.Writer
	}{os.Stdin, os.Stdout}
	t := term.NewTerminal(rw, "> ")
	if w, h, err := term.GetSize(fd); err == nil {
		t.SetSize(w, h)
	}
	t.AutoCompleteCallback = complete
	for {
		line, err := t.ReadLine()
		if err == io.EOF { // ^D on an empty line
			fmt.Fprintln(t, "bye")
			return
		}
		if err != nil {
			panic(err)
		}
		switch line {
		case "quit":
			return
		case "history":
			for i := t.History.Len() - 1; i >= 0; i-- {
				fmt.Fprintf(t, "  %s\n", t.History.At(i))
			}
		default:
			// Writes to t are converted: \n becomes \r\n.
			fmt.Fprintf(t, "you typed %q\n", line)
		}
	}
}

// complete is called for every key; we only act on Tab.
func complete(line string, pos int, key rune) (string, int, bool) {
	if key != '\t' {
		return "", 0, false
	}
	var hits []string
	for _, w := range words {
		if strings.HasPrefix(w, line[:pos]) {
			hits = append(hits, w)
		}
	}
	if len(hits) != 1 {
		return "", 0, false
	}
	return hits[0] + line[pos:], len(hits[0]), true
}
```

A session: `hello world` and Enter; Up and Enter (history); `his` and
Tab, which completes to `history`, and Enter; `st`, then `^A` to go to
the start of the line, `echo ` and Enter; `qu`, Tab and Enter. What the
screen shows at the end:

```text
$ go run ./cmd/lineedit
> hello world
you typed "hello world"
> hello world
you typed "hello world"
> history
  hello world
  hello world
  history
> echo st
you typed "echo st"
> quit
```

In the raw byte stream you can see how the editor redraws: after `^A`,
each inserted character is written followed by the rest of the line
(`st`) and `ESC [ 2 D` (cursor left two columns), and Tab rewrites the
word after moving back over the prefix (`his`, `ESC [ 3 D`, `history`).

It is limited (no Unicode width handling for wide characters, no
multi-line input, no syntax coloring), but it has no dependencies and
works over any stream, which makes it handy for SSH servers (chapter 28)
and debug consoles. For a full readline, look at
`github.com/chzyer/readline`, `github.com/peterh/liner`, or the Bubbles
`textinput` and `textarea` components.

---

## 27. Go: pseudo-terminals with creack/pty

`github.com/creack/pty` is the PTY package almost every Go program uses
(including the Charm SSH libraries, Docker's CLI and many terminal
emulators). It is small:

| Function | Purpose |
|----------|---------|
| `Open()` | master, slave |
| `Start(cmd)` | run on new pty |
| `StartWithSize` | same, sized |
| `Setsize` | TIOCSWINSZ |
| `GetsizeFull` | TIOCGWINSZ |
| `InheritSize` | copy size |

### 27.1 Starting a child

`pty.Start(cmd)` does, in order: `pty.Open()` (open `/dev/ptmx`,
`grantpt`, `unlockpt`, open the slave); set `cmd.Stdin`, `Stdout` and
`Stderr` to the slave if they are nil; set
`cmd.SysProcAttr.Setsid = true` and `Setctty = true` (new session, slave
as controlling terminal: chapter 12); `cmd.Start()`; close the slave in
the parent; return the master as an `*os.File`.

```go
// file: go/cmd/ptyspawn/main.go
// Run a command on a new pty; print what it writes, with \r made visible.
package main

import (
	"bytes"
	"errors"
	"fmt"
	"io"
	"os"
	"os/exec"
	"syscall"

	"github.com/creack/pty"
)

func main() {
	args := os.Args[1:]
	if len(args) == 0 {
		args = []string{"sh", "-c",
			"tty; stty size; ls --color=auto -d /; ls -l /proc/self/fd"}
	}
	cmd := exec.Command(args[0], args[1:]...)
	// Start: open a pair, set the size, put the slave on 0, 1 and 2,
	// and set SysProcAttr.Setsid and Setctty for the child.
	ptmx, err := pty.StartWithSize(cmd, &pty.Winsize{Rows: 30, Cols: 100})
	if err != nil {
		panic(err)
	}
	defer ptmx.Close()
	fmt.Println("child pid", cmd.Process.Pid)

	var all bytes.Buffer
	_, err = io.Copy(&all, ptmx)
	// The end of the output is an EIO error on Linux, not a plain EOF.
	if err != nil && !errors.Is(err, syscall.EIO) {
		panic(err)
	}
	out := bytes.ReplaceAll(all.Bytes(), []byte("\r"), []byte("^M"))
	out = bytes.ReplaceAll(out, []byte("\x1b"), []byte("^["))
	os.Stdout.Write(out)
	err = cmd.Wait()
	fmt.Printf("\n[%v; %d bytes]\n", errOr(err), all.Len())
}

func errOr(err error) any {
	if err == nil {
		return "exit status 0"
	}
	return err
}
```

```text
$ go run ./cmd/ptyspawn
child pid 976204
/dev/pts/14^M
30 100^M
^[[0m^[[01;34m/^[[0m^M
total 0^M
lrwx------ 1 me me 64 Nov 22 17:56 0 -> /dev/pts/14^M
lrwx------ 1 me me 64 Nov 22 17:56 1 -> /dev/pts/14^M
lrwx------ 1 me me 64 Nov 22 17:56 2 -> /dev/pts/14^M
lr-x------ 1 me me 64 Nov 22 17:56 3 -> /proc/976204/fd^M

[exit status 0; 273 bytes]
```

The same 273 bytes as the Rust version, byte for byte (chapter 22):
same commands, same terminal size, same line discipline. And the child's
descriptors are clean without any effort: Go opens everything,
`/dev/ptmx` included, with `O_CLOEXEC`.

Points worth knowing:

- **The end is `EIO`.** `io.Copy` stops at the first error, and on Linux
  that is `EIO` when the slave is closed by all processes. On macOS the
  master returns EOF (`io.Copy` returns `nil`). Accept both.
- **`SysProcAttr` declares what the child does before `exec`.** The
  fields related to our subject:

  | Field | Child does |
  |-------|------------|
  | `Setsid` | `setsid()` |
  | `Setctty` | `TIOCSCTTY` |
  | `Ctty` | which fd |
  | `Setpgid` | `setpgid` |
  | `Pgid` | which group |
  | `Foreground` | `tcsetpgrp` |
  | `Noctty` | `TIOCNOTTY` |
  | `Pdeathsig` | parent death |

  `Ctty` is a descriptor number *in the child*, usually 0. `Foreground`
  puts the child's new process group in the foreground of the terminal
  `Ctty`: with `Setpgid`, it is what a job-control shell does for a
  foreground job (chapter 13). `Pdeathsig` (Linux) sends a signal to the
  child when the parent thread dies, useful to avoid orphans.
- **The master is a blocking descriptor.** One would expect the Go
  runtime to manage it like a socket, with `epoll` (its "netpoller"),
  deadlines and a `Close` that wakes up a pending `Read`. It does not:
  creack/pty (v1.1.24 here) calls `ptmx.Fd()` for its `ioctl`s, and
  `Fd()` switches an `*os.File` back to blocking mode, for good. We
  measured the consequences:

  - `ptmx.SetReadDeadline` returns `nil` and does nothing: a `Read`
    with a 300 ms deadline lasted 3 s, until the child exited, and then
    returned `EIO`.
  - `ptmx.Close()` does not interrupt a goroutine blocked in `Read`. The
    real `close` is even postponed until that `Read` returns, so the
    child gets no hangup: close and wait took 4.9 s instead of an
    instant `SIGHUP`.
  - Each goroutine blocked in `Read` holds an OS thread.

  The fix is one line after `Start`, the recipe of the library's own
  tests:

  ```go
  // Back to non-blocking: deadlines and Close work again.
  syscall.SetNonblock(int(ptmx.Fd()), true)
  ```

  Calling `Fd()` here is harmless: the switch to blocking mode has
  already happened. After it, the same `Read` returns "i/o timeout"
  after 300 ms, and `Close` makes it return "file already closed" at
  once. For a short program that reads until `EIO`, as in 27.2, it
  makes no difference; for a long-lived one that must stop sessions,
  like the multiplexer of chapter 31, it is essential.

### 27.2 `script` in Go: goroutines instead of `poll`

The C, Raku and Rust versions of `script` were all event loops waiting on
several descriptors. In Go, each direction is a goroutine running
`io.Copy`, and the runtime does the waiting:

```go
// file: go/cmd/ptyscript/main.go
// A small script(1): run a command on a pty, relay the terminal, log output.
// Usage: ptyscript [-o LOG] [CMD ARGS...]
package main

import (
	"errors"
	"flag"
	"fmt"
	"io"
	"os"
	"os/exec"
	"os/signal"
	"syscall"

	"github.com/creack/pty"
	"golang.org/x/term"
)

func main() {
	logPath := flag.String("o", "typescript", "log file")
	flag.Parse()
	args := flag.Args()
	if len(args) == 0 {
		shell := os.Getenv("SHELL")
		if shell == "" {
			shell = "/bin/sh"
		}
		args = []string{shell}
	}
	os.Exit(run(*logPath, args))
}

func run(logPath string, args []string) int {
	log, err := os.Create(logPath)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		return 1
	}
	defer log.Close()
	fmt.Printf("Script started, output log file is '%s'.\n", logPath)

	cmd := exec.Command(args[0], args[1:]...)
	// A pty starts as 0x0; give it a sensible size if we have none to copy.
	ptmx, err := pty.StartWithSize(cmd, &pty.Winsize{Rows: 24, Cols: 80})
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		return 1
	}
	defer ptmx.Close()

	stdin := int(os.Stdin.Fd())
	interactive := term.IsTerminal(stdin)
	var saved *term.State
	if interactive {
		// Copy our window size now, and again on every SIGWINCH.
		winch := make(chan os.Signal, 1)
		signal.Notify(winch, syscall.SIGWINCH)
		go func() {
			for range winch {
				pty.InheritSize(os.Stdin, ptmx)
			}
		}()
		winch <- syscall.SIGWINCH
		defer signal.Stop(winch)

		if saved, err = term.MakeRaw(stdin); err != nil {
			fmt.Fprintln(os.Stderr, err)
			return 1
		}
		// Restore on every return path, panics included. Restoring
		// twice is harmless.
		defer term.Restore(stdin, saved)
	}

	// Keyboard -> child. This goroutine may stay blocked in Read after
	// the child exits; that is fine, we exit soon after.
	go func() {
		io.Copy(ptmx, os.Stdin)
		if !interactive {
			ptmx.Write([]byte{4}) // ^D: end of input for the child
		}
	}()

	// Child -> screen and log, until EIO.
	_, err = io.Copy(io.MultiWriter(os.Stdout, log), ptmx)
	if err != nil && !errors.Is(err, syscall.EIO) {
		fmt.Fprintln(os.Stderr, err)
	}

	code := 0
	if err := cmd.Wait(); err != nil {
		var ee *exec.ExitError
		if !errors.As(err, &ee) {
			fmt.Fprintln(os.Stderr, err)
			return 1
		}
		ws := ee.Sys().(syscall.WaitStatus)
		if ws.Signaled() {
			code = 128 + int(ws.Signal())
		} else {
			code = ws.ExitStatus()
		}
	}
	if interactive {
		term.Restore(stdin, saved) // before printing in cooked mode
	}
	fmt.Printf("Script done, exit status %d.\n", code)
	return code
}
```

```text
$ printf 'echo hello from $(tty)\nstty size\nexit 3\n' |
    go run ./cmd/ptyscript -o log.txt sh
Script started, output log file is 'log.txt'.
echo hello from $(tty)
stty size
exit 3
sh-5.3$ echo hello from $(tty)
hello from /dev/pts/14
sh-5.3$ stty size
24 80
sh-5.3$ exit 3
exit
Script done, exit status 3.
```

Interactively (`stty size`, `sleep 10`, `^C`, `exit 4`), and with the
`ttyinfo --watch` program as the child, resized from 24x80 to 40x120:

```text
$ ptyscript -o /dev/null sh
Script started, output log file is '/dev/null'.
sh-5.3$ stty size
24 80
sh-5.3$ sleep 10
^C
sh-5.3$ exit 4
exit
Script done, exit status 4.
$ ptyscript -o /dev/null ttyinfo --watch
Script started, output log file is '/dev/null'.
...
size 24x80
resize the window; ^C to quit
SIGWINCH: now 40x120
^C
Script done, exit status 0.
```

The structure, in 110 lines:

- `io.MultiWriter(os.Stdout, log)` is the `tee`: every write goes to
  both.
- The keyboard goroutine is never stopped. When the child exits, it is
  still blocked reading our stdin; we just return from `run` and exit.
  A long-running program would have to make that goroutine stop
  (closing the master makes its `Write` fail on the next key). A read of
  a terminal cannot simply be interrupted: on `os.Stdin`,
  `SetReadDeadline` fails with "file type does not support deadline",
  because `os.Stdin` is a blocking descriptor not managed by the
  netpoller. A non-blocking `dup` of descriptor 0 wrapped with
  `os.NewFile` does accept deadlines (we checked: "i/o timeout after
  300ms"), but `O_NONBLOCK` is shared with the shell through the open
  file description, so it must be cleared before exiting. The tidy
  solution is `muesli/cancelreader`, which Bubble Tea uses for this
  exact purpose: it waits with `epoll` (or `select`) on the descriptor
  and on a pipe it writes to when you call `Cancel`.
- `SIGWINCH` handling is a goroutine reading a channel, calling
  `pty.InheritSize(os.Stdin, ptmx)`, which is `GetsizeFull` on one and
  `Setsize` on the other. We send ourselves a fake `SIGWINCH` value at
  the start, to copy the initial size.
- When stdin is not a terminal, we start with 24x80, because a new PTY
  has a size of 0x0 (and `stty size` would print `0 0`, and full-screen
  programs would fail).
- The `run` function returns an exit code and `main` calls `os.Exit`:
  the deferred `term.Restore` and `Close` calls run before the exit.

**A race you should know about.** With input from a pipe, we write
`^D` (the `VEOF` character) to the master when our input ends, so that
the shell exits. Try it with input that does *not* end with `exit`:

```text
$ printf 'stty size\n' | timeout 5 ptyscript -o /dev/null sh >/dev/null
$ echo $?
124
$ (printf 'stty size\n'; sleep 1) | ptyscript -o /dev/null sh >/dev/null
$ echo $?
0
```

Without the delay, the program hangs (the Rust and Raku versions behave
the same). The `^D` arrived while the slave was still in canonical mode,
before bash started: the line discipline treated it as an end-of-file
mark and stored it, after the line `stty size`. Then bash started and
its line editor switched the terminal to non-canonical mode; the pending
end-of-file mark is not a character, and in non-canonical mode it is not
delivered as anything. The `^D` is lost, and bash waits forever. With
the delay, `^D` arrives while Readline is reading in raw mode, as a byte
`0x04`, which Readline treats as end of input on an empty line.

So a PTY is not a pipe: what a byte *means* depends on the mode the
child has set *at the moment it arrives*. Tools that drive interactive
programs do not write ahead blindly; they wait for the program to be
ready, typically by recognizing its prompt. That is the job of the next
program.

### 27.3 A small `expect`

`expect` (Don Libes, 1990, in Tcl) automates interactive programs:
spawn the program on a PTY, *expect* some output (a regular expression,
with a timeout), *send* some input, repeat. It is the standard tool for
testing REPLs and for automating programs that insist on a terminal
(`passwd`, `ssh` password prompts, installers).

```go
// file: go/cmd/expect/main.go
// A tiny expect: drive an interactive program through a pty.
package main

import (
	"bytes"
	"fmt"
	"os"
	"os/exec"
	"regexp"
	"time"

	"github.com/creack/pty"
)

// Session collects the child's output in a buffer, fed by a goroutine.
type Session struct {
	pty   *os.File
	cmd   *exec.Cmd
	chunk chan []byte // output, as it arrives; closed at the end
	buf   bytes.Buffer
}

func Spawn(name string, args ...string) (*Session, error) {
	cmd := exec.Command(name, args...)
	cmd.Env = append(os.Environ(), "TERM=dumb") // no colors, please
	f, err := pty.StartWithSize(cmd, &pty.Winsize{Rows: 24, Cols: 80})
	if err != nil {
		return nil, err
	}
	s := &Session{pty: f, cmd: cmd, chunk: make(chan []byte)}
	go func() {
		for {
			b := make([]byte, 4096)
			n, err := f.Read(b)
			if n > 0 {
				s.chunk <- b[:n]
			}
			if err != nil { // EIO: the child is gone
				close(s.chunk)
				return
			}
		}
	}()
	return s, nil
}

// Expect waits until re matches the pending output; it returns the
// submatches and drops everything up to the end of the match.
func (s *Session) Expect(re *regexp.Regexp, d time.Duration) ([]string, error) {
	deadline := time.After(d)
	for {
		if loc := re.FindSubmatchIndex(s.buf.Bytes()); loc != nil {
			m := make([]string, len(loc)/2)
			for i := range m {
				if loc[2*i] >= 0 {
					m[i] = string(s.buf.Bytes()[loc[2*i]:loc[2*i+1]])
				}
			}
			s.buf.Next(loc[1])
			return m, nil
		}
		select {
		case b, ok := <-s.chunk:
			if !ok {
				return nil, fmt.Errorf("EOF waiting for %v", re)
			}
			s.buf.Write(b)
		case <-deadline:
			return nil, fmt.Errorf("timeout waiting for %v; have %q",
				re, s.buf.String())
		}
	}
}

// ExpectEOF waits for the end of the output.
func (s *Session) ExpectEOF(d time.Duration) error {
	deadline := time.After(d)
	for {
		select {
		case b, ok := <-s.chunk:
			if !ok {
				return nil
			}
			s.buf.Write(b)
		case <-deadline:
			return fmt.Errorf("timeout waiting for EOF")
		}
	}
}

func (s *Session) Send(text string) error {
	_, err := s.pty.WriteString(text)
	return err
}

func main() {
	prompt := regexp.MustCompile(`>>> $`)
	s, err := Spawn("python3", "-q")
	check(err)
	_, err = s.Expect(prompt, 5*time.Second)
	check(err)

	for _, expr := range []string{"6 * 7", "2 ** 100", "len('héllo')"} {
		check(s.Send(expr + "\r")) // \r: what the Enter key sends
		// The echo of our input, then the result line, then a prompt.
		m, err := s.Expect(regexp.MustCompile(`\r\n(.*)\r\n>>> $`),
			5*time.Second)
		check(err)
		fmt.Printf("%-14s = %s\n", expr, m[1])
	}

	// Too short a timeout. Note the pattern: "late" alone would match
	// the echo of our own input, print('late').
	check(s.Send("import time; time.sleep(2); print('late')\r"))
	late := regexp.MustCompile(`\r\nlate\r\n>>> $`)
	_, err = s.Expect(late, 500*time.Millisecond)
	fmt.Println("error:", err)
	_, err = s.Expect(late, 5*time.Second) // the output is still coming
	fmt.Println("second try:", err)

	check(s.Send("\x04")) // ^D at the prompt: Python exits
	fmt.Println("end:", s.ExpectEOF(5*time.Second))
	fmt.Println("wait:", s.cmd.Wait())
}

func check(err error) {
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
```

```text
$ go run ./cmd/expect
6 * 7          = 42
2 ** 100       = 1267650600228229401496703205376
len('héllo')   = 5
error: timeout waiting for \r\nlate\r\n>>> $; have "import time; time.sleep(2); print('late')\r\n"
second try: <nil>
end: <nil>
wait: <nil>
```

What this small program has to get right is the whole craft of
`expect`:

- **Everything is a stream of bytes.** There are no "messages": the
  output arrives in chunks of any size, so we accumulate in a buffer
  and match the regular expression against the buffer, after each new
  chunk. A match consumes the buffer up to its end.
- **Our input is echoed.** The PTY's line discipline echoes what we
  send (here Python's line editor does, in raw mode). So after sending
  `6 * 7\r`, the output is `6 * 7\r\n42\r\n>>> `. A pattern like `late`
  matches the echo of `print('late')` before Python even ran it; the
  first version of this program had exactly that bug. Anchor patterns
  on `\r\n` (and remember that the terminal's `ONLCR` turns `\n` into
  `\r\n`) or on the prompt.
- **Press Enter with `\r`**, as a keyboard does; the line discipline's
  `ICRNL` turns it into `\n` for programs in canonical mode, and
  programs in raw mode expect `\r`.
- **Set `TERM=dumb`** to discourage colors and other escape sequences
  in the output. Python 3.13+ has its own line editor that colors the
  prompt when the terminal allows it; with `TERM=dumb` it falls back to
  plain output. Many programs also honor `NO_COLOR=1`.
- **Wait for the prompt before sending**: the `^D` at the end is sent
  only after `>>> ` came back, so it is read by Python's line editor and
  not lost (27.2).
- **A timeout is not an error of the program**: after the first timeout,
  the output is still coming, and a second `Expect` gets it.
- **The reader goroutine** sends chunks on an unbuffered channel. If
  the caller stops calling `Expect`, the goroutine blocks, and the child
  blocks when the PTY buffer fills up: back-pressure, as with a pipe. A
  real library would let you close the session and drain. Note that
  with the blocking master of 27.1, closing it would not even stop that
  goroutine while it sits in `Read`: a library must make the master
  non-blocking first.

Go libraries for this: `github.com/Netflix/go-expect` (used by the
`survey` prompt library for its tests) and
`github.com/google/goexpect`. Chapter 30 builds a more complete driver.

---

## 28. Go: the Charm stack

Charm (charm.sh) publishes a family of Go libraries for terminal
applications. Their version 2 releases, under the `charm.land` import
paths, are used here:

| Module | Role |
|--------|------|
| `bubbletea/v2` | TUI framework |
| `lipgloss/v2` | styling, layout |
| `bubbles/v2` | components |
| `wish/v2` | SSH apps |
| `log/v2` | pretty logging |
| `huh/v2` | forms |
| `glamour/v2` | Markdown |

And programs built with them that are useful for shell scripts: `gum`
(prompts, spinners and filters as commands), `glow` (Markdown reader),
`vhs` (records terminal sessions as GIFs from a script, driving a real
terminal emulator through a PTY), `soft-serve` (a Git server with a TUI
over SSH).

### 28.1 Bubble Tea: the Elm architecture

A Bubble Tea program is a **model** with three methods:

```go
type Model interface {
	Init() Cmd                  // first command to run, or nil
	Update(Msg) (Model, Cmd)    // handle one message, return the new model
	View() View                 // render the model
}
```

- **Messages** (`Msg`, any type) are events: a key press
  (`tea.KeyPressMsg`), a mouse event, a window size change
  (`tea.WindowSizeMsg`), a paste, focus changes, or your own types.
- **`Update`** is the only place where the state changes. It returns the
  new model and, optionally, a **command**.
- **Commands** (`Cmd`, a `func() Msg`) are how side effects happen: the
  runtime runs each command in its own goroutine, and the message it
  returns is fed back to `Update`. Timers (`tea.Tick`), HTTP requests,
  running a program: all commands. `tea.Quit` is a command.
- **`View`** returns what the screen should look like, as a value. The
  **renderer** compares it with the previous frame and sends only the
  differences (a cell-based renderer in v2, like curses).

This is the architecture of the Elm language, and the same idea as
ratatui's immediate mode (23.2) pushed further: even the event loop is
the library's. The model is a plain value; `Update` is easy to unit
test without a terminal.

What Bubble Tea does with the terminal, which you now know how to do by
hand:

- At start: raw mode (`MakeRaw`) on the input if it is a terminal,
  hide the cursor, enable bracketed paste, query the terminal for its
  capabilities (with `ESC [ c`, and others) and its background color.
- A goroutine reads the input and parses escape sequences (keys,
  mouse, focus, paste, terminal replies) into messages. This parser
  lives in `charmbracelet/ultraviolet`.
- `SIGWINCH` is turned into `WindowSizeMsg`. One is sent at startup.
- `^C` is a key, not a signal (`ISIG` is off): your `Update` decides.
  If a `SIGINT` does arrive (from `kill`), `Run` returns
  `tea.ErrInterrupted`.
- At exit, and on panic: everything is restored.

**Version 2 changes** that matter if you read older code: the view is a
`tea.View` struct, not a string, and terminal features are declared in
it instead of being turned on and off with commands (`v.AltScreen =
true` instead of `tea.EnterAltScreen`; also `MouseMode`, `ReportFocus`,
`WindowTitle`, `Cursor`, `KeyboardEnhancements`); key messages are
`tea.KeyPressMsg` and `tea.KeyReleaseMsg`; the kitty keyboard protocol
is used when the terminal supports it.

### 28.2 Lip Gloss and Bubbles

**Lip Gloss** styles strings: colors, bold, padding, borders, widths,
alignment; it measures the visible width of strings (skipping escape
sequences, counting wide characters as two cells) and joins blocks
horizontally or vertically. A style is a value; `style.Render(s)`
returns `s` wrapped in escape sequences.

```go
title := lipgloss.NewStyle().Bold(true).
	Foreground(lipgloss.Color("#FAFAFA")).
	Background(lipgloss.Color("#7D56F4")).Padding(0, 1)
fmt.Println(title.Render("launcher"))
```

Colors are given as `"#RRGGBB"` or as an ANSI index (`"9"` is bright
red). Lip Gloss v2 does not decide alone how to render them: the
**color profile** of the output (true color, 256 colors, 16 colors, or
none) is detected from the environment (`COLORTERM`, `TERM`, `NO_COLOR`)
and from whether the output is a terminal, and the colors are
downsampled to it. In a Bubble Tea program, the program does that for
the whole view. With `lipgloss.Println` outside Bubble Tea, the same
detection applies to stdout: piped output gets no escape sequences.

**Bubbles** are ready-made components, each a small model with its own
`Update` and `View` that you embed in yours and forward messages to:
`textinput`, `textarea`, `list` (with filtering), `table`, `viewport`
(a scrollable pane), `spinner`, `progress`, `paginator`, `filepicker`,
`timer`, `stopwatch`, `help`, `key` (key bindings).

### 28.3 Giving the terminal to a child: `tea.ExecProcess`

A TUI that runs other interactive programs (an editor, a pager, a shell)
must **hand over the terminal**: restore the modes it changed, leave the
alternate screen, stop reading the input, let the child run in the
foreground, then take everything back. That is `tea.ExecProcess`. Our
example is a launcher: type a command, press Enter, the command runs with
the real terminal, then you come back to the TUI.

```go
// file: go/cmd/launcher/main.go
// Bubble Tea v2: a command launcher that hands the terminal to its children.
package main

import (
	"fmt"
	"os"
	"os/exec"
	"time"

	"charm.land/bubbles/v2/textinput"
	tea "charm.land/bubbletea/v2"
	"charm.land/lipgloss/v2"
)

var (
	title = lipgloss.NewStyle().Bold(true).
		Foreground(lipgloss.Color("#FAFAFA")).
		Background(lipgloss.Color("#7D56F4")).Padding(0, 1)
	okStyle  = lipgloss.NewStyle().Foreground(lipgloss.Color("10"))
	errStyle = lipgloss.NewStyle().Foreground(lipgloss.Color("9"))
	dim      = lipgloss.NewStyle().Faint(true)
)

// doneMsg reports the end of a command run with ExecProcess.
type doneMsg struct {
	cmdline string
	err     error
	took    time.Duration
}

// tickMsg drives the clock, to show that the program is alive.
type tickMsg time.Time

type model struct {
	input   textinput.Model
	history []string // one line per command run, newest last
	now     time.Time
}

func newModel() model {
	in := textinput.New()
	in.Prompt = "$ "
	in.Placeholder = "a shell command, e.g. vi, top, ls -l"
	in.SetWidth(50)
	in.Focus()
	return model{input: in, now: time.Now()}
}

func tick() tea.Cmd {
	return tea.Tick(time.Second, func(t time.Time) tea.Msg {
		return tickMsg(t)
	})
}

func (m model) Init() tea.Cmd { return tick() }

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.KeyPressMsg:
		switch msg.String() {
		case "ctrl+c", "ctrl+d", "esc":
			return m, tea.Quit
		case "enter":
			line := m.input.Value()
			if line == "" {
				return m, nil
			}
			m.input.Reset()
			// Leave the terminal to the child; get it back afterwards.
			// The child runs on the normal screen; wait for Enter
			// before going back to the alternate one.
			c := exec.Command("sh", "-c",
				line+`; s=$?; printf '\n[Enter] '; read _; exit $s`)
			start := time.Now()
			return m, tea.ExecProcess(c, func(err error) tea.Msg {
				return doneMsg{line, err, time.Since(start)}
			})
		}
	case doneMsg:
		status := okStyle.Render("ok")
		if msg.err != nil {
			status = errStyle.Render(msg.err.Error())
		}
		m.history = append(m.history, fmt.Sprintf("%s  %s  %s", status,
			msg.cmdline, dim.Render(msg.took.Round(time.Millisecond).String())))
		return m, nil
	case tickMsg:
		m.now = time.Time(msg)
		return m, tick()
	}
	var cmd tea.Cmd
	m.input, cmd = m.input.Update(msg)
	return m, cmd
}

func (m model) View() tea.View {
	s := title.Render("launcher") + " " +
		dim.Render(m.now.Format("15:04:05")) + "\n\n"
	for _, h := range m.history {
		s += "  " + h + "\n"
	}
	s += "\n" + m.input.View() + "\n\n" +
		dim.Render("enter runs, esc quits") + "\n"
	v := tea.NewView(s)
	v.AltScreen = true
	v.WindowTitle = "launcher"
	return v
}

func main() {
	if _, err := tea.NewProgram(newModel()).Run(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
```

A session in a 80x12 terminal: `echo hi`, then `ls -d /usr; false`,
then `cat` (typing `abc`, Enter, `^D`). While a command runs, the normal
screen shows the child's output:

```text
$ launcher
hi
[Enter]
/usr
[Enter]
abc
abc
[Enter]
```

and back in the launcher (the alternate screen):

```text
 launcher  18:01:44

  ok  echo hi  606ms
  exit status 1  ls -d /usr; false  604ms
  ok  cat  2.423s

$ a shell command, e.g. vi, top, ls -l

enter runs, esc quits
```

How the handover works (from `exec.go` in Bubble Tea):

1. `ExecProcess` returns a command; when `Update` returns it, the
   program calls `releaseTerminal`: stop the input reader (this is
   where `cancelreader` is needed: a goroutine blocked in `read` on the
   terminal must be woken up), restore the original termios, show the
   cursor, leave the alternate screen.
2. It sets the child's stdin and stdout to the program's input and
   output (the terminal) if they are nil, and runs it with `cmd.Run()`.
   The child is in our process group, which is the foreground group: it
   can read the terminal, and `^C` reaches it (and us; Bubble Tea ignores
   it, since it is in the middle of `Run`).
3. When the child exits: raw mode again, alternate screen again, a full
   redraw, and the callback's message goes to `Update`.

The `printf '[Enter]'; read _` added to each command keeps its output on
screen until you press Enter, since returning to the alternate screen
hides it. Programs such as `ranger` and `lazygit` do the same. Our first
version used the inline mode (no alternate screen) and printed results
with `tea.Printf`; the children's output was then overwritten by the
redraw, because the renderer assumes that it knows what is on the screen
below its view. Inline mode and children writing to the terminal do not
mix well.

The clock in the title, updated every second by a `tea.Tick` command,
stops while a child runs: the program is blocked in `cmd.Run()`, and no
messages are processed until it returns.

### 28.4 Wish: TUIs over SSH

**Wish** is an SSH server library (built on `charm.land/ssh`, a fork of
`gliderlabs/ssh`, itself built on `golang.org/x/crypto/ssh`). It serves
applications instead of shells: `ssh` to the server, and you get a
Bubble Tea program, one per connection. The `bubbletea` middleware does
the wiring.

This is where all the pieces of the tutorial meet. The SSH client is a
program in raw mode on *your* terminal, relaying keys and window size
changes over the network. On the server side, the SSH protocol's
`pty-req` asks for a terminal, with a `TERM` value, a size and a list of
termios settings. A server can then do one of two things:

- **Allocate a real PTY** (as OpenSSH's `sshd` does): the program runs
  on the slave, with a real line discipline, and the server copies
  between the master and the network.
- **Emulate one**: give the program the network channel directly, and
  translate `\n` into `\r\n` on output. No line discipline, no echo, no
  signals; enough for a Bubble Tea program that does its own input
  handling. This is Wish's default.

Our server uses a real PTY (`ssh.AllocatePty()`) and accepts two kinds
of sessions: without a command, a Bubble Tea app showing what the
server sees; with a command, it runs the command on the PTY like
`sshd`.

```go
// file: go/cmd/sshtty/main.go
// An SSH server, with Wish: a Bubble Tea app per connection, on a real pty.
// "ssh -p 2222 localhost" shows the app; "ssh -t -p 2222 localhost CMD"
// runs CMD on the session's pty, like sshd.
package main

import (
	"errors"
	"fmt"
	"net"
	"os"
	"os/exec"
	"os/signal"
	"syscall"
	"time"

	tea "charm.land/bubbletea/v2"
	"charm.land/log/v2"
	"charm.land/ssh"
	"charm.land/wish/v2"
	"charm.land/wish/v2/activeterm"
	bm "charm.land/wish/v2/bubbletea"
	"charm.land/wish/v2/logging"
	"golang.org/x/term"
)

func main() {
	srv, err := wish.NewServer(
		wish.WithAddress(net.JoinHostPort("localhost", "2222")),
		wish.WithHostKeyPath(".ssh/sshtty_ed25519"), // created if missing
		ssh.AllocatePty(), // a real pty per session, not an emulation
		wish.WithMiddleware( // the last one listed runs first
			bm.Middleware(appHandler),
			commandMiddleware,
			activeterm.Middleware(), // refuse sessions without a pty
			logging.Middleware(),
		),
	)
	if err != nil {
		log.Fatal(err)
	}
	log.Info("listening", "addr", srv.Addr)
	go func() {
		err := srv.ListenAndServe()
		if err != nil && !errors.Is(err, ssh.ErrServerClosed) {
			log.Fatal(err)
		}
	}()
	stop := make(chan os.Signal, 1)
	signal.Notify(stop, os.Interrupt, syscall.SIGTERM)
	<-stop
	log.Info("stopping")
	srv.Close()
}

// commandMiddleware runs "ssh host CMD" on the session's pty.
func commandMiddleware(next ssh.Handler) ssh.Handler {
	return func(s ssh.Session) {
		if s.RawCommand() == "" {
			next(s) // no command: the Bubble Tea app
			return
		}
		pty, _, _ := s.Pty()
		// Like sshd: the command line goes to a shell.
		cmd := exec.CommandContext(s.Context(), "sh", "-c", s.RawCommand())
		cmd.Env = append(s.Environ(), "TERM="+pty.Term)
		// New session, pty slave as controlling terminal: ^C works.
		// The server resizes the pty itself on "window-change" requests.
		if err := pty.Start(cmd, ssh.WithJobControl()); err != nil {
			wish.Fatalln(s, err)
			return
		}
		code := 0
		if err := cmd.Wait(); err != nil {
			code = 1
			if ee, ok := err.(*exec.ExitError); ok {
				code = ee.ExitCode()
			}
		}
		s.Exit(code)
	}
}

// appHandler creates one Bubble Tea model per connection.
func appHandler(s ssh.Session) (tea.Model, []tea.ProgramOption) {
	pty, _, _ := s.Pty()
	m := model{
		slave: pty.Slave,
		user:  s.User(),
		addr:  s.RemoteAddr().String(),
		term:  pty.Term,
		tty:   pty.Name(),
		w:     pty.Window.Width,
		h:     pty.Window.Height,
	}
	return m, bm.MakeOptions(s) // input/output: the pty slave
}

type model struct {
	slave                 *os.File
	user, addr, term, tty string
	w, h                  int
	keys                  []string
}

// sizeMsg carries the pty's size, polled: see the text for why.
type sizeMsg struct{ w, h int }

func (m model) pollSize() tea.Cmd {
	return tea.Tick(250*time.Millisecond, func(time.Time) tea.Msg {
		w, h, _ := term.GetSize(int(m.slave.Fd()))
		return sizeMsg{w, h}
	})
}

func (m model) Init() tea.Cmd { return m.pollSize() }

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		m.w, m.h = msg.Width, msg.Height
	case sizeMsg:
		if msg.w != m.w || msg.h != m.h {
			m.w, m.h = msg.w, msg.h
		}
		return m, m.pollSize()
	case tea.KeyPressMsg:
		if k := msg.String(); k == "q" || k == "ctrl+c" {
			return m, tea.Quit
		}
		m.keys = append(m.keys, msg.String())
		if len(m.keys) > 8 {
			m.keys = m.keys[1:]
		}
	}
	return m, nil
}

func (m model) View() tea.View {
	v := tea.NewView(fmt.Sprintf(
		"user %s from %s\nTERM %s on %s (server side)\nsize %dx%d\n"+
			"keys %v\n\nresize, type keys; q quits\n",
		m.user, m.addr, m.term, m.tty, m.h, m.w, m.keys))
	v.AltScreen = true
	return v
}
```

```text
$ go run ./cmd/sshtty &
2026/11/22 18:03:47 INFO  listening addr=localhost:2222
$ ssh -p 2222 localhost
```

The app, after typing `a`, Up and `^X` and resizing the terminal from
70x10 to 90x12:

```text
user cog from 127.0.0.1:33476
TERM tmux-256color on /dev/pts/15 (server side)
size 12x90
keys [a up ctrl+x]

resize, type keys; q quits
```

And with a command (`-t` forces the client to request a PTY, which it
does not do by default when a command is given):

```text
$ ssh -t -p 2222 localhost 'tty; stty size; ps -o pid,pgid,sid,tpgid,tty,comm; exit 7'
/dev/pts/15
12 90
    PID    PGID     SID   TPGID TT       COMMAND
1001628 1001628 1001628 1001628 pts/15   sh
1001631 1001628 1001628 1001628 pts/15   ps
$ echo $?
7
```

`sh` is a session leader on the server's `pts/15` and its own
foreground group (`ssh.WithJobControl()` sets `Setsid` and `Setctty`),
the exit code travels back through the SSH protocol's `exit-status`
message, and the server log shows each connection:

```text
INFO  cog connect 127.0.0.1:33476 false [] tmux-256color 70 10 SSH-2.0-OpenSSH_10.6
INFO  127.0.0.1:33476 disconnect 2.948539776s
```

Notes:

- **Middlewares** wrap each other; with `wish.WithMiddleware(a, b, c)`,
  `c` runs first and calls `b`, which calls `a`. So the logging runs
  first, then the check that a PTY was requested (`activeterm`), then
  our command handler, which falls through to the Bubble Tea app when
  there is no command.
- **Authentication**: without any authentication option, Wish accepts
  every connection, which is fine on `localhost` for a demo and nowhere
  else. Use `wish.WithPublicKeyAuth` or `WithAuthorizedKeys`.
- **The host key** is generated on first start in
  `.ssh/sshtty_ed25519`. Clients will warn the first time
  (`StrictHostKeyChecking`), as with any SSH server.
- **Why the app polls the PTY size.** With a real PTY, the SSH library
  starts a goroutine that reads the session's window-change channel and
  resizes the PTY. The Bubble Tea middleware reads *the same channel*
  to send `WindowSizeMsg`. Each change goes to only one of them, so the
  app missed about half of the resizes in our tests. And since the
  program is not a process attached to that PTY, it gets no `SIGWINCH`
  either. Our model therefore asks the PTY for its size four times a
  second (`term.GetSize` on the slave). This is an observation about
  `charm.land/ssh` 0.4.3 and `wish` 2.0.5 from reading their source and
  testing; with the default emulated PTY, the problem does not exist.
- The command path does not need any of this: the library resizes the
  PTY, and the kernel sends `SIGWINCH` to the foreground group of the
  PTY, our `sh`.

### 28.5 Testing Bubble Tea programs

- **Unit tests of `Update`**: build a model, call `Update` with
  messages (`tea.KeyPressMsg{Code: 'q'}`, `tea.WindowSizeMsg{...}`),
  and check the returned model and command. No terminal involved.
- **`teatest`** (in `github.com/charmbracelet/x/exp/teatest`) runs a
  whole program with fake input and output, and compares the final
  output with a golden file.
- **A real terminal**: as in 23.4, run the program in a detached tmux
  session and capture the screen. The screens in this chapter were made
  that way, including the SSH sessions (`ssh` inside tmux).
- **VHS** (by Charm) scripts a terminal session (`Type "ls"`, `Enter`,
  `Sleep 1s`) and renders it to a GIF, a video, or a text file for
  golden tests.

### 28.6 Go: summary

| Topic | Go tool |
|-------|---------|
| processes | `os/exec` |
| pipes | `os.Pipe` |
| child setup | `SysProcAttr` |
| signals | `os/signal` |
| termios | `x/term` |
| ioctls | `x/sys/unix` |
| PTY | `creack/pty` |
| TUI | Bubble Tea |
| styling | Lip Gloss |
| SSH apps | Wish |

Go's strengths here: goroutines turn every relay (PTY, SSH, pipes) into
a few `io.Copy` calls; the netpoller makes blocking reads cheap; all
descriptors are close-on-exec; `SIGPIPE` behaves well by default; static
binaries are easy to deploy. Its traps: no `fork` (so no code between
fork and exec except what `SysProcAttr` offers), a nil `Cmd.Stdout` that
means `/dev/null`, `Wait` hanging on a grandchild that holds a pipe,
`defer` skipped by `os.Exit` and `log.Fatal`, and reads of a terminal
that cannot be cancelled without help.

---
# Part III — Projects

Part I explained the machinery; Part II showed it from four languages.
Part III builds larger programs, each one a classic of the Unix
terminal world in miniature:

- chapter 29 compares the four `script` programs of Part II, then
  extends the Rust one into a recorder and a player of terminal
  sessions, in the format of asciinema;
- chapter 30 builds an `expect`: a library to drive interactive
  programs from code, in Rust and in Raku;
- chapter 31 builds `muxi`, a terminal multiplexer in Go, with its own
  small terminal emulator;
- chapter 32 is about debugging: the tools to look at terminals,
  process groups and pipes, and a C logger of what crosses a PTY;
- chapter 33 compares the four languages for this kind of work.

All the programs of this part were run on the machine described in the
introduction; the transcripts are real. When a run happens in a
terminal, it was done in a private `tmux` server driven by a script
(30.8 shows how), and the screen was captured as text.

## 29. Project: `script` in four languages

### 29.1 One program, four times

Chapters 12 (C), 17 (Raku), 22 (Rust) and 27 (Go) each wrote the same
program: a small `script(1)`. It is the smallest program that uses
every part of the terminal machinery:

1. open a PTY pair, and give the slave the size of our terminal;
2. start a command in a new session, with the slave as its controlling
   terminal and as its standard input, output and error;
3. put our own terminal in raw mode, so that every key goes to the
   child unchanged, `^C` and `^Z` included: the line discipline of the
   PTY, not ours, turns them into signals;
4. relay in both directions: keyboard to master, master to screen and
   to a log file;
5. copy our window size to the PTY on every `SIGWINCH`;
6. stop when reading the master fails with `EIO` (every slave
   descriptor is closed), reap the child, restore the terminal, and
   exit with the child's status.

The four versions have the same behavior. They differ in where the
difficulty went:

| Concern   | C          | Raku        | Rust        | Go           |
|-----------|------------|-------------|-------------|--------------|
| Lines     | 179 (+85)  | 53 (+147)   | 133 (+108)  | 110          |
| PTY setup | own        | `setsid -c` | own         | creack/pty   |
| Relay     | `poll`     | `react`     | `poll`      | goroutines   |
| Signals   | self-pipe  | `signal()`  | signal-hook | `Notify`     |
| Raw mode  | termios    | Term::termios | nix       | x/term       |
| Restore   | `atexit`   | `LEAVE`     | `Drop`      | `defer`      |

The numbers in parentheses are the shared helpers: `ptyopen.c` and
`ptyopen.h` in C, `Pty.rakumod` and `Tty.rakumod` in Raku, the
`termtut` library crate (`lib.rs`) in Rust. The Raku helpers are the
largest because they also wrap, through NativeCall, the C functions
that Raku has no built-in for (`isatty`, `tcgetpgrp`, `ioctl`, `poll`,
`read`). Go needs no helper of its
own because creack/pty and `golang.org/x/term` already are those
helpers.

### 29.2 Starting the child

The heart of the matter is the code that runs in the child between
`fork` and `exec` (chapter 6): `setsid()`, then `ioctl(TIOCSCTTY)` on
the slave, then the three `dup2`s, then `exec`. The four languages
reach it differently:

- **C** writes it directly (`pty_spawn` in `ptyopen.c`). Nothing is
  hidden, and every mistake is possible: forgetting `O_CLOEXEC` on the
  master leaks it into the child, which then keeps its own terminal
  open and never sees `EIO` (chapter 12 showed the hang).
- **Rust** writes the same code in a `pre_exec` closure of
  `std::process::Command` (`spawn_on_pty` in `lib.rs`). The closure is
  `unsafe` for a good reason: it runs in the child of a `fork`, where
  only async-signal-safe functions may be called. `Command` does the
  rest: `dup2`s, error reporting from the child through a pipe, `exec`.
- **Go** cannot run code between `fork` and `exec` at all: the runtime
  is multi-threaded, and Go gives no hook there. Instead,
  `syscall.SysProcAttr` describes what the child must do, with
  `Setsid`, `Setctty` and `Ctty`, and the runtime's own fork code does
  it. creack/pty fills these fields for you.
- **Raku** has no `fork` either (MoarVM is multi-threaded too) and no
  equivalent of `SysProcAttr` in `Proc::Async`. Chapter 17 used the
  util-linux command `setsid -c` as a trampoline: `Proc::Async` starts
  `setsid -c CMD` with the slave as its three standard descriptors,
  and `setsid` does the `setsid()` and `TIOCSCTTY` before executing the
  real command. One more process image, but no C code. (Exercise E.17
  replaces it with a small C library called through NativeCall.)

### 29.3 The relay

The relay is where the programming models differ most.

- **C and Rust** use one thread and `poll` on three descriptors: stdin,
  the master, and the read end of a self-pipe (C) or the socket of
  signal-hook (Rust) that turns signals into readable bytes. The loop
  is explicit, and everything is in one place: when the master reports
  `EIO`, the loop ends, and nobody else is reading anything.
- **Go** uses two goroutines and `io.Copy`: one copies stdin to the
  master, the main one copies the master to stdout and the log through
  `io.MultiWriter`. It is the shortest code, and it hides a problem
  that 27.2 discussed: the stdin goroutine cannot be stopped. It is
  blocked in `read(0)` when the child exits. The program exits anyway,
  so it does not matter here; in a long-running program (chapter 31)
  it does.
- **Raku** uses `react` with four `whenever` blocks: keys, output,
  `SIGWINCH`, and the exit of the child. It is the most declarative,
  and the subtle part is the end: the output supply ends (`EIO`) and
  the process exits as two separate events, in either order, and the
  program must wait for both before it can print the status. The two
  flags `$eof` and `$status` do exactly that.

A detail common to all four: what happens when our standard input is
not a terminal, as in `echo ls | ptyscript`. The input reaches its end
of file, but the child must not see "end of file" as a closed
descriptor: the master is still open, since we need the output. So
each version sends `^D` (`\x04`) to the master, which the line
discipline of the PTY turns into an end of file for the child's
`read`, if the child is in canonical mode (chapter 4).

### 29.4 Errors and cleanup

Every version must restore the terminal, whatever happens. A program
that dies in raw mode leaves the user with a terminal that echoes
nothing and ignores `Enter` (32.9 shows how to recover).

- **C** registers `restore_tty` with `atexit`. It runs on `exit` and on
  return from `main`, not on a crash or on a fatal signal: a complete
  program would also catch `SIGTERM` and `SIGHUP` (ours does, through
  the self-pipe, and turns them into a hangup of the child).
- **Rust** wraps raw mode in a `RawMode` value whose `Drop` restores
  the terminal: it runs on return and on panic (with the default
  `panic = "unwind"`), not on `process::exit`. Hence the pattern of
  dropping it explicitly before printing the final message.
- **Go** uses `defer term.Restore`, which runs on return and on panic,
  not on `os.Exit`. That is why `main` calls `os.Exit(run())`: the
  deferred calls of `run` all execute before the exit.
- **Raku** uses a `LEAVE` phaser, which runs when the block is left,
  normally or by an exception.

### 29.5 What the user sees

The four programs behave the same way, with one difference in what
you type. In the C, Rust and Go versions, `^C` while the child runs a
command interrupts that command, and `^D` at the shell prompt ends the
session. Exactly the same for Raku: the relay copies bytes, and the
line discipline of the PTY does the rest. That is the point of a
pseudo-terminal: our program needs to know nothing about signals,
echo, or line editing.

Start-up time and memory are another matter. On the machine of this
tutorial (C compiled by GCC 16.2 with `-O2`, Rust 1.99 in release
mode, Go 1.27, Rakudo Star 2026.08), running `ptyscript -o /dev/null
true` with its input from `/dev/null` (best of five runs), and reading
`VmRSS` in `/proc/PID/status` while the program relays `sleep`:

| Version | Time     | Memory  | Threads | Binary  |
|---------|----------|---------|---------|---------|
| C       | 1.1 ms   | 1.9 MB  | 1       | 35 KB   |
| Rust    | 1.1 ms   | 2.3 MB  | 1       | 588 KB  |
| Go      | 1.7 ms   | 5.5 MB  | 5       | 3.3 MB  |
| Raku    | 296 ms   | 253 MB  | 8       | script  |

The C and Rust binaries link the C library dynamically (Rust also
`libgcc_s`, for unwinding); the Go binary is static and runs on any
Linux of the same architecture. The Raku start-up time is the cost of
loading the compiler, the runtime and the precompiled modules; for an
interactive tool it is noticeable, for a long session it is not.
Chapter 33 comes back to these numbers.

### 29.6 Recording with timing: the asciicast format

A typescript keeps the bytes but not the time: replaying it shows the
whole session at once. util-linux `script` can record the timing in a
separate file (`--log-timing`), and `scriptreplay` replays it. Its
classic timing format is one line per chunk of output, the delay
before it and its size in bytes:

```console
$ script -q --log-timing tm.txt --log-out out.txt \
    -c 'printf "a\n"; sleep 0.3; printf "b\n"' </dev/null >/dev/null
$ cat tm.txt
0.010119 3
0.292404 3
```

(`a\n` became three bytes, `a\r\n`: the `onlcr` flag of the PTY.) With
`--log-io`, the newer "advanced" format also records the input and
some metadata, one event per line, `O` for output, `I` for input, `H`
for header information:

```text
H 0.000000 START_TIME 2026-11-22 18:26:00+01:00
H 0.000000 SHELL /usr/bin/zsh
H 0.000000 COMMAND printf x
O 0.010183 1
H 0.000000 DURATION 0.020294
H 0.000000 EXIT_CODE 0
```

The format that won on the web, though, is the one of
[asciinema](https://asciinema.org): **asciicast**. Version 2 (the one
we implement; the current asciinema 3 writes version 3, with relative
times, and still reads version 2) is newline-delimited JSON. The
[specification](https://docs.asciinema.org/manual/asciicast/v2/) says,
in short:

- the first line is a JSON object, the header, with at least
  `version` (2), `width` and `height` (the terminal size in columns and
  rows), and optionally `timestamp` (Unix time of the start),
  `command`, `title`, `env` (usually `TERM` and `SHELL`) and others;
- every other line is an event, a JSON array of three elements: the
  time in seconds since the start (a float), the type, and the data,
  a string;
- the types are `"o"` (data written to the terminal), `"i"` (data
  typed, recorded only on request), `"r"` (a resize, the data is
  `"COLSxROWS"`) and `"m"` (a marker, for navigation).

Since the data is a JSON string, it must be valid Unicode: a recorder
must decode the output as UTF-8, and that raises the problem we met
in several chapters: a read can cut a character in two. A recorder
that decodes each chunk separately writes two replacement characters
instead of one `é`.

### 29.7 `ptyrec`: the recorder

`ptyrec` is the Rust `ptyscript` of chapter 22, with an asciicast
writer instead of a typescript. It depends on the same `termtut`
library (`spawn_on_pty`, `RawMode`, `window_size`, `set_window_size`,
`set_cloexec`, all from chapter 22) and on signal-hook:

```rust
// file: rust/src/bin/ptyrec.rs
//! Record a terminal session in the asciicast v2 format of asciinema:
//! a JSON header line, then one JSON array per event:
//!   [seconds, "o", "output"]   [seconds, "i", "input"]
//!   [seconds, "r", "COLSxROWS"]
//!   ptyrec [-i] FILE.cast [CMD ARGS...]      (-i: record input too)
use nix::errno::Errno;
use nix::poll::{PollFd, PollFlags, PollTimeout, poll};
use nix::pty::{Winsize, openpty};
use signal_hook::consts::SIGWINCH;
use std::fs::File;
use std::io::{self, BufWriter, IsTerminal, Read, Write};
use std::os::fd::AsFd;
use std::os::unix::net::UnixStream;
use std::os::unix::process::ExitStatusExt;
use std::process::ExitCode;
use std::time::{Instant, SystemTime, UNIX_EPOCH};
use termtut::{
    RawMode, set_cloexec, set_window_size, spawn_on_pty, window_size,
};

/// Escape a string for JSON. Control characters (ESC among them)
/// become \u00XX; everything else is kept as UTF-8.
fn json_str(s: &str) -> String {
    let mut out = String::with_capacity(s.len() + 2);
    out.push('"');
    for c in s.chars() {
        match c {
            '"' => out.push_str("\\\""),
            '\\' => out.push_str("\\\\"),
            '\n' => out.push_str("\\n"),
            '\r' => out.push_str("\\r"),
            '\t' => out.push_str("\\t"),
            c if (c as u32) < 0x20 => {
                out.push_str(&format!("\\u{:04x}", c as u32))
            }
            c => out.push(c),
        }
    }
    out.push('"');
    out
}

/// Turns a stream of byte chunks into valid UTF-8 strings: a character
/// cut between two reads is kept for the next chunk, invalid bytes
/// become U+FFFD.
#[derive(Default)]
struct Utf8Stream {
    pending: Vec<u8>,
}

impl Utf8Stream {
    fn push(&mut self, bytes: &[u8]) -> String {
        self.pending.extend_from_slice(bytes);
        let mut out = String::new();
        loop {
            match std::str::from_utf8(&self.pending) {
                Ok(s) => {
                    out.push_str(s);
                    self.pending.clear();
                    return out;
                }
                Err(e) => {
                    let good = e.valid_up_to();
                    // SAFETY: from_utf8 just checked this prefix
                    out.push_str(unsafe {
                        std::str::from_utf8_unchecked(&self.pending[..good])
                    });
                    match e.error_len() {
                        None => {
                            // incomplete character at the end: wait
                            self.pending.drain(..good);
                            return out;
                        }
                        Some(bad) => {
                            out.push('\u{fffd}');
                            self.pending.drain(..good + bad);
                        }
                    }
                }
            }
        }
    }
}

struct Recorder {
    file: BufWriter<File>,
    start: Instant,
}

impl Recorder {
    fn event(&mut self, kind: &str, data: &str) -> io::Result<()> {
        let t = self.start.elapsed().as_secs_f64();
        writeln!(self.file, "[{t:.6}, \"{kind}\", {}]", json_str(data))
    }
}

fn main() -> Result<ExitCode, Box<dyn std::error::Error>> {
    let mut args: Vec<String> = std::env::args().skip(1).collect();
    let record_input = args.first().map(String::as_str) == Some("-i");
    if record_input {
        args.remove(0);
    }
    if args.is_empty() {
        return Err("usage: ptyrec [-i] FILE.cast [CMD ARGS...]".into());
    }
    let path = args.remove(0);
    if args.is_empty() {
        args.push(std::env::var("SHELL").unwrap_or_else(|_| "/bin/sh".into()));
    }

    let stdin = io::stdin();
    if !stdin.is_terminal() {
        return Err("ptyrec: stdin must be a terminal".into());
    }
    let (rows, cols) = window_size(&stdin)?;
    let pty = openpty(
        &Winsize {
            ws_row: rows,
            ws_col: cols,
            ws_xpixel: 0,
            ws_ypixel: 0,
        },
        None,
    )?;
    set_cloexec(&pty.master)?;
    set_cloexec(&pty.slave)?;
    let mut child = spawn_on_pty(&args, pty.slave)?;
    let mut master = File::from(pty.master);

    let mut rec = Recorder {
        file: BufWriter::new(File::create(&path)?),
        start: Instant::now(),
    };
    let now = SystemTime::now().duration_since(UNIX_EPOCH)?.as_secs();
    let term = std::env::var("TERM").unwrap_or_default();
    let shell = std::env::var("SHELL").unwrap_or_default();
    writeln!(
        rec.file,
        "{{\"version\": 2, \"width\": {cols}, \"height\": {rows}, \
         \"timestamp\": {now}, \"command\": {}, \
         \"env\": {{\"TERM\": {}, \"SHELL\": {}}}}}",
        json_str(&args.join(" ")),
        json_str(&term),
        json_str(&shell)
    )?;
    eprintln!("ptyrec: recording to {path}; exit the shell to stop.");

    let (mut sig_r, sig_w) = UnixStream::pair()?;
    sig_r.set_nonblocking(true)?;
    signal_hook::low_level::pipe::register(SIGWINCH, sig_w)?;

    let raw = RawMode::enable(stdin.as_fd())?;
    let mut out = io::stdout().lock();
    let (mut out_utf8, mut in_utf8) =
        (Utf8Stream::default(), Utf8Stream::default());
    let mut buf = [0u8; 4096];
    let ready = PollFlags::POLLIN | PollFlags::POLLHUP | PollFlags::POLLERR;
    loop {
        let mut fds = [
            PollFd::new(master.as_fd(), PollFlags::POLLIN),
            PollFd::new(sig_r.as_fd(), PollFlags::POLLIN),
            PollFd::new(stdin.as_fd(), PollFlags::POLLIN),
        ];
        match poll(&mut fds, PollTimeout::NONE) {
            Err(Errno::EINTR) => continue,
            r => r?,
        };
        let ev = fds.map(|f| f.revents().unwrap_or(PollFlags::empty()));

        if ev[0].intersects(ready) {
            let n = match master.read(&mut buf) {
                Ok(0) => break,
                Err(e) if e.raw_os_error() == Some(libc::EIO) => break,
                r => r?,
            };
            out.write_all(&buf[..n])?;
            out.flush()?;
            let text = out_utf8.push(&buf[..n]);
            if !text.is_empty() {
                rec.event("o", &text)?;
            }
        }
        if ev[1].contains(PollFlags::POLLIN) {
            while sig_r.read(&mut buf).is_ok() {}
            let (rows, cols) = window_size(&stdin)?;
            set_window_size(&master, rows, cols)?;
            rec.event("r", &format!("{cols}x{rows}"))?;
        }
        if ev[2].intersects(ready) {
            let n = nix::unistd::read(&stdin, &mut buf)?;
            if n == 0 {
                break;
            }
            master.write_all(&buf[..n])?;
            if record_input {
                let text = in_utf8.push(&buf[..n]);
                rec.event("i", &text)?;
            }
        }
    }
    drop(raw);
    rec.file.flush()?;
    let status = child.wait()?;
    let code = status
        .code()
        .unwrap_or_else(|| 128 + status.signal().unwrap_or(0));
    eprintln!(
        "ptyrec: {:.1}s recorded in {path}.",
        rec.start.elapsed().as_secs_f64()
    );
    Ok(ExitCode::from(code as u8))
}
```

Points to notice:

- **`json_str`** is a complete JSON string encoder for our needs. JSON
  forbids raw control characters in strings (U+0000 to U+001F); the
  common ones have short escapes (`\n`, `\r`, `\t`), the others
  become `\u00XX`. ESC, the most frequent control character in a
  terminal session, becomes `\u001b`, as in the files asciinema
  writes. Everything else, including non-ASCII text, is copied as
  UTF-8, which JSON allows.
- **`Utf8Stream`** solves the cut character. `std::str::from_utf8`
  reports, on failure, how many bytes are valid (`valid_up_to`) and
  whether the error is a truly invalid sequence (`error_len` is
  `Some(n)`: skip `n` bytes, emit U+FFFD) or just an incomplete one at
  the end (`None`: keep the bytes for the next chunk). Two instances
  are used, one per direction, since input and output are independent
  streams.
- **Time** is measured with `Instant`, a monotonic clock, from the
  start of the recording: if the system clock is changed during the
  session (NTP, daylight saving time), the recording is not affected.
  Only the `timestamp` of the header uses the wall clock.
- **The events are written in order of arrival**, so the times are
  increasing, as the specification requires.
- **The input is relayed even when it is not recorded**: `-i` only
  decides whether `"i"` events are written. Recording input means
  recording passwords, which is why asciinema does not do it by
  default either.
- **The output is written to the screen first**, then recorded: the
  user should never wait for the file system.

A session, run in an 80x24 tmux window which was resized to 60x20
during the recording (the tmux driver of 30.8 types the commands):

```console
$ target/release/ptyrec -i demo.cast bash --norc; echo status=$?
ptyrec: recording to demo.cast; exit the shell to stop.
bash-5.3$ PS1='$ '
$ printf 'caf\303'; sleep 0.5; printf '\251\n'
café
$ tput cols
80
$ tput cols; exit 3
60
exit
ptyrec: 4.5s recorded in demo.cast.
status=3
```

The `printf` command is the test of `Utf8Stream`: it writes the first
byte of `é` (octal 303), waits half a second, then writes the second
(251). The beginning of `demo.cast`:

```text
{"version": 2, "width": 80, "height": 24, "timestamp": 1795368227, "command": "bash --norc", "env": {"TERM": "tmux-256color", "SHELL": "/usr/bin/zsh"}}
[0.001054, "o", "\u001b[?2004hbash-5.3$ "]
[0.803834, "i", "PS1='$ '\r"]
[0.804086, "o", "PS1='$ '\r\n\u001b[?2004l\r"]
[0.804126, "o", "\u001b[?2004h$ "]
[1.608361, "i", "printf 'caf\\303'; sleep 0.5; printf '\\251\\n'\r"]
[1.608635, "o", "printf 'caf\\303'; sleep 0.5; printf '\\251\\n'\r\n\u001b[?2004l\r"]
[1.608687, "o", "caf"]
[2.110322, "o", "é\r\n"]
[2.110337, "o", "\u001b[?2004h$ "]
```

Reading it:

- The input event `"PS1='$ '\r"` ends with `\r`: the Enter key sends a
  carriage return (chapter 4); the line discipline turns it into `\n`
  for the shell (`icrnl`) and echoes `\r\n`.
- Bash surrounds each line it reads with `ESC [?2004h` and
  `ESC [?2004l`: it turns *bracketed paste* on while it waits for a
  line, so that a pasted text arrives framed by `ESC [200~` and
  `ESC [201~` and is not executed line by line, and off while a
  command runs (Appendix B).
- At 1.608687 the output is `"caf"`, and the `é` comes whole at
  2.110322: the first byte waited half a second in `Utf8Stream`.
- The echo of the input arrives 0.3 ms after the input itself: the
  time for the line discipline of the PTY and for bash.

Further down, the resize:

```text
[3.715414, "r", "60x20"]
```

### 29.8 `ptyplay`: the player

Playing a recording is simpler: read the header, then write each
`"o"` event at its time. Two options of asciinema's player are worth
having: a speed factor, and a maximum idle time, so that the five
minutes you spent reading documentation in the middle of a session
are replayed as one second.

```rust
// file: rust/src/bin/ptyplay.rs
//! Replay an asciicast v2 recording at its original pace.
//!   ptyplay [-s SPEED] [-i MAX_IDLE] FILE.cast
//! -s 2 plays twice as fast; -i 1 shortens every pause to 1 s at most.
//! Only "o" (output) events are played; "r" events are reported.
use std::fs::File;
use std::io::{self, BufRead, BufReader, Write};
use std::thread::sleep;
use std::time::{Duration, Instant};

/// Parse a JSON string literal at the start of `s` (which starts with
/// a quote). Returns the string and the rest of the input.
fn parse_json_str(s: &str) -> Option<(String, &str)> {
    let mut out = String::new();
    let mut chars = s.strip_prefix('"')?.char_indices();
    let rest = s.strip_prefix('"')?;
    let hex4 = |it: &mut std::str::CharIndices| -> Option<u32> {
        let h: String =
            (0..4).filter_map(|_| it.next().map(|(_, c)| c)).collect();
        u32::from_str_radix(&h, 16).ok()
    };
    while let Some((i, c)) = chars.next() {
        match c {
            '"' => return Some((out, &rest[i + 1..])),
            '\\' => match chars.next()?.1 {
                'n' => out.push('\n'),
                'r' => out.push('\r'),
                't' => out.push('\t'),
                'b' => out.push('\u{8}'),
                'f' => out.push('\u{c}'),
                'u' => {
                    let mut u = hex4(&mut chars)?;
                    if (0xd800..0xdc00).contains(&u) {
                        // UTF-16 surrogate pair: 😀
                        chars.next();
                        chars.next();
                        let lo = hex4(&mut chars)?;
                        u = 0x10000 + ((u - 0xd800) << 10) + (lo - 0xdc00);
                    }
                    out.push(char::from_u32(u).unwrap_or('\u{fffd}'));
                }
                c => out.push(c), // \" \\ \/
            },
            c => out.push(c),
        }
    }
    None
}

/// Parse an event line: [1.234, "o", "data"]
fn parse_event(line: &str) -> Option<(f64, String, String)> {
    let s = line.trim().strip_prefix('[')?;
    let (t, s) = s.split_once(',')?;
    let (kind, s) = parse_json_str(s.trim_start())?;
    let s = s.trim_start().strip_prefix(',')?.trim_start();
    let (data, _) = parse_json_str(s)?;
    Some((t.trim().parse().ok()?, kind, data))
}

/// Extract an integer field from the header (good enough for
/// "width": 80; a real program would use serde_json).
fn header_int(header: &str, key: &str) -> Option<u64> {
    let at = header.find(&format!("\"{key}\""))? + key.len() + 2;
    let digits: String = header[at..]
        .trim_start_matches([':', ' '])
        .chars()
        .take_while(char::is_ascii_digit)
        .collect();
    digits.parse().ok()
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let mut args = std::env::args().skip(1);
    let (mut speed, mut max_idle, mut path) = (1.0_f64, f64::INFINITY, None);
    while let Some(a) = args.next() {
        match a.as_str() {
            "-s" => speed = args.next().ok_or("-s needs a value")?.parse()?,
            "-i" => {
                max_idle = args.next().ok_or("-i needs a value")?.parse()?
            }
            _ => path = Some(a),
        }
    }
    let path =
        path.ok_or("usage: ptyplay [-s SPEED] [-i MAX_IDLE] FILE.cast")?;
    let mut lines = BufReader::new(File::open(&path)?).lines();
    let header = lines.next().ok_or("empty file")??;
    if header_int(&header, "version") != Some(2) {
        return Err("not an asciicast v2 file".into());
    }
    let w = header_int(&header, "width").unwrap_or(0);
    let h = header_int(&header, "height").unwrap_or(0);
    if let Ok((rows, cols)) = termtut::window_size(io::stdout())
        && (cols as u64, rows as u64) != (w, h)
    {
        eprintln!(
            "ptyplay: recorded at {w}x{h}, this terminal is {cols}x{rows}"
        );
    }

    let mut out = io::stdout().lock();
    let start = Instant::now();
    let (mut last_t, mut clock) = (0.0_f64, 0.0_f64); // file time, play time
    for line in lines {
        let line = line?;
        let Some((t, kind, data)) = parse_event(&line) else {
            continue; // blank or unknown line
        };
        clock += (t - last_t).min(max_idle) / speed;
        last_t = t;
        let due = Duration::from_secs_f64(clock);
        if let Some(wait) = due.checked_sub(start.elapsed()) {
            sleep(wait);
        }
        match kind.as_str() {
            "o" => {
                out.write_all(data.as_bytes())?;
                out.flush()?;
            }
            "r" => eprint!("\r\n[ptyplay: resized to {data}]\r\n"),
            _ => {} // "i" (input) and "m" (markers) are not played
        }
    }
    Ok(())
}
```

Notes:

- **No JSON library.** A real program would use `serde_json`; the
  hand-written parser is here because it is short, and because it
  shows what the escapes of `json_str` become. It handles the
  surrogate pairs that other recorders produce for characters beyond
  U+FFFF (JSON's `\u` escapes are UTF-16 code units: 😀 is
  `😀`).
- **An absolute clock.** The naive player sleeps for each delay in
  turn, and the time spent writing accumulates: a recording with
  10 000 events plays noticeably slower than real time. `ptyplay`
  computes when each event is due (`clock`) and sleeps until then,
  so errors do not accumulate.
- **The size.** A recording made at 80x24 replayed in a 100x40
  terminal is mostly fine (lines are shorter than the screen); the
  other way round, lines wrap and full-screen programs are a mess.
  `ptyplay` warns. The real asciinema player, in the browser, simply
  creates a terminal of the right size: it is a terminal emulator
  written in Rust and compiled to WebAssembly, the same idea as the
  emulator of chapter 31.

Replaying the session above at double speed, in the same 80x24
window:

```console
$ clear; time target/release/ptyplay -s 2 demo.cast
bash-5.3$ PS1='$ '
$ printf 'caf\303'; sleep 0.5; printf '\251\n'
café
$ tput cols
80
$
[ptyplay: resized to 60x20]
$ tput cols; exit 3
60
exit
real	0m2.262s
```

The recording lasted 4.5 s; played at speed 2 it took 2.26 s. The
`"r"` event cannot be replayed (a program cannot resize the terminal
it runs in, in general: some emulators accept `ESC [8;ROWS;COLSt`,
most ignore it), so it is reported.

asciinema itself is not installed on this machine, so we did not check
that it plays our files; the format above follows the specification,
and the files have the shape of those asciinema 2 writes. Exercise E.13 asks for the
same player in Raku, E.28 for a `"m"` marker key in `ptyrec`.

### 29.9 What the four versions teach

- The **system calls are the same** in every language: `openpty` (or
  `posix_openpt`, `grantpt`, `unlockpt`, `ptsname`), `setsid`,
  `ioctl(TIOCSCTTY)`, `tcgetattr`/`tcsetattr`, `ioctl(TIOCGWINSZ)` and
  `TIOCSWINSZ`, `poll` or its equivalent, `read`, `write`, `waitpid`.
  Learning them once, in C, makes every library readable.
- **The hard part is the end**: knowing when the session is over
  (`EIO` and the exit of the child are two events), stopping the
  threads or tasks that still block, restoring the terminal on every
  path, and passing on the exit status.
- **Language runtimes get in the way of `fork`.** C and Rust can run
  code in the child; Go and Raku cannot, and depend on a description
  of what to do (Go) or on a helper program (Raku).
- **Descriptor hygiene matters**: `O_CLOEXEC` everywhere, the slave
  closed in the parent after the spawn, otherwise no `EIO`, ever.

## 30. Project: an `expect`-like driver

### 30.1 Programs that want a human

Some programs insist on a terminal. `passwd`, `ssh` asking for a
password, `gpg` asking for a passphrase, installers asking questions,
REPLs: they read from `/dev/tty` rather than standard input, or they
check `isatty(0)` and behave differently without one, or they switch
the terminal to non-canonical mode and expect keys. Driving them from
a script with a pipe fails: there is no terminal for them.

In 1990, Don Libes of NIST wrote **Expect**, a Tcl extension that runs
a program on a pseudo-terminal and lets a script wait for text and
answer it:

```tcl
spawn passwd
expect "password:"
send "$old\r"
expect "New password:"
send "$new\r"
```

The idea was copied everywhere: Pexpect for Python (the most used
today), `Expect.pm` for Perl, `expectrl` and `rexpect` for Rust,
`go-expect` and `goexpect` for Go. Chapter 12 wrote a first
`ptyexpect` in C with literal strings, and chapter 27 one in Go. This
chapter builds a more complete one, with regular expressions,
alternatives, timeouts, end of file, job control and an interactive
mode, in Rust; then the same in Raku.

### 30.2 The design of an expect library

Every expect library has the same few parts:

- **a session**: the master side of a PTY, the child process, and a
  **buffer** of output received but not yet consumed;
- **`expect(pattern)`**: read output into the buffer until the pattern
  matches it, or the timeout expires, or the output ends. On success,
  return the match and **consume** the buffer up to the end of the
  match, so that the next `expect` starts after it. The text before
  the match is usually the interesting part: the answer to the last
  command;
- **`expect_any(patterns)`**: the same with several patterns, to handle
  alternatives ("password:" or "Permission denied" or "Are you sure
  you want to continue connecting"). When several match, the one that
  matches **earliest in the buffer** must win, not the first in the
  list: otherwise a pattern can skip over output that another pattern
  should have handled;
- **`send`**: write to the master; typing Enter is sending `\r`, not
  `\n` (the line discipline maps one to the other, `icrnl`, but only
  `\r` is what a keyboard sends, and programs in raw mode see the
  difference);
- **timeouts** that are not fatal: the output may still arrive later.
  The error should contain the unmatched output: it is the only clue
  when a script fails;
- **end of file**: when the child closes the terminal, reading the
  master fails with `EIO`. An `expect` that waits for something that
  will never come must fail at once, not wait for the timeout;
- **interact**: give the keyboard to the user, for the parts a script
  cannot do, and take it back on an escape key.

And three decisions about the child's terminal:

- **`TERM=dumb`**: programs that see a dumb terminal do not send
  colors, do not move the cursor, and do not redraw. The output is
  then plain text that patterns can match. With `TERM=xterm-256color`,
  a prompt can come as `ESC[1;32m>>> ESC[0m`, or be redrawn character
  by character;
- **the size**: 24x80 is the default. A PTY created without a size is
  0x0, and some programs then wrap every character on its own line;
- **echo**: the terminal echoes what we send, so the output contains
  our own input. This is the first trap of 30.5.

### 30.3 The Rust project

The driver is a binary of the `termtut` crate, with two files in
`src/bin/drive/`: `expect.rs`, the library part, and `main.rs`, three
example scenarios. It needs the `regex` crate, added with:

```console
$ cargo add regex
```

The complete `Cargo.toml` of the crate is now:

```toml
# file: rust/Cargo.toml
[package]
name = "termtut"
version = "0.1.0"
edition = "2024"

[dependencies]
crossterm = "0.29.0"
libc = "0.2.191"
nix = { version = "0.32.0", features = ["term", "process", "signal", "fs", "poll", "ioctl"] }
portable-pty = "0.9.0"
ratatui = "0.30.2"
regex = "1.13.2"
signal-hook = "0.4.6"
```

The `regex` crate has two APIs: `regex::Regex` matches `&str`, and
`regex::bytes::Regex` matches `&[u8]`. We use the second: the output
of a program is bytes, not necessarily valid UTF-8, and it can stop in
the middle of a character. With the bytes API, a pattern still matches
UTF-8 text (`é` in a pattern matches the two bytes of `é`), and the
buffer never needs to be decoded until a match is returned.

### 30.4 `expect.rs`

```rust
// file: rust/src/bin/drive/expect.rs
//! A small expect library: start a program on a PTY, wait for
//! patterns in its output, send it input, hand it the keyboard.
use nix::errno::Errno;
use nix::poll::{PollFd, PollFlags, PollTimeout, poll};
use nix::pty::{Winsize, openpty};
use regex::bytes::Regex;
use std::fmt;
use std::fs::File;
use std::io::{self, Read, Write};
use std::os::fd::{AsFd, AsRawFd};
use std::process::{Child, ExitStatus};
use std::time::{Duration, Instant};
use termtut::{
    RawMode, set_cloexec, set_window_size, spawn_on_pty, window_size,
};

#[derive(Debug)]
pub enum Error {
    /// Nothing matched in time; `seen` is the unmatched output.
    Timeout {
        waited: Duration,
        seen: String,
    },
    /// The program closed the terminal before anything matched.
    Eof {
        seen: String,
    },
    Io(io::Error),
}

impl fmt::Display for Error {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        match self {
            Error::Timeout { waited, seen } => {
                write!(
                    f,
                    "timeout after {waited:?}; unmatched output: {seen:?}"
                )
            }
            Error::Eof { seen } => {
                write!(f, "end of output; unmatched: {seen:?}")
            }
            Error::Io(e) => write!(f, "{e}"),
        }
    }
}

impl std::error::Error for Error {}

impl From<io::Error> for Error {
    fn from(e: io::Error) -> Self {
        Error::Io(e)
    }
}

impl From<Errno> for Error {
    fn from(e: Errno) -> Self {
        Error::Io(e.into())
    }
}

/// A successful match.
pub struct Match {
    /// Which of the patterns matched (for expect_any).
    pub index: usize,
    /// The output before the match: typically the answer to a command.
    pub before: String,
    /// The matched text, and the capture groups.
    pub text: String,
    pub groups: Vec<Option<String>>,
}

pub struct Session {
    master: File,
    child: Child,
    buf: Vec<u8>, // output received and not consumed by a match yet
    eof: bool,
    pub timeout: Duration,
    log: Option<Box<dyn Write>>,
}

fn lossy(b: &[u8]) -> String {
    String::from_utf8_lossy(b).into_owned()
}

impl Session {
    /// Start `argv` on a new 24x80 PTY, with TERM=dumb so that programs
    /// keep their output plain (no colors, no cursor movement).
    pub fn spawn(argv: &[&str]) -> Result<Session, Error> {
        let ws = Winsize {
            ws_row: 24,
            ws_col: 80,
            ws_xpixel: 0,
            ws_ypixel: 0,
        };
        let pty = openpty(&ws, None)?;
        set_cloexec(&pty.master)?;
        set_cloexec(&pty.slave)?;
        let mut full = vec!["env".to_string(), "TERM=dumb".to_string()];
        full.extend(argv.iter().map(|s| s.to_string()));
        let child = spawn_on_pty(&full, pty.slave)?;
        Ok(Session {
            master: File::from(pty.master),
            child,
            buf: Vec::new(),
            eof: false,
            timeout: Duration::from_secs(5),
            log: None,
        })
    }

    /// Copy everything the program writes to `w` (a file, stderr...).
    pub fn log_to(&mut self, w: impl Write + 'static) {
        self.log = Some(Box::new(w));
    }

    /// Wait at most `wait` for output, and add it to the buffer.
    fn fill(&mut self, wait: Duration) -> Result<(), Error> {
        let ms = wait.as_millis().clamp(1, i32::MAX as u128) as i32;
        let timeout = PollTimeout::try_from(ms).unwrap_or(PollTimeout::MAX);
        let mut fds = [PollFd::new(self.master.as_fd(), PollFlags::POLLIN)];
        match poll(&mut fds, timeout) {
            Ok(0) | Err(Errno::EINTR) => return Ok(()), // nothing yet
            r => r?,
        };
        let mut chunk = [0u8; 4096];
        match self.master.read(&mut chunk) {
            Ok(0) => self.eof = true,
            Err(e) if e.raw_os_error() == Some(libc::EIO) => self.eof = true,
            Err(e) => return Err(e.into()),
            Ok(n) => {
                if let Some(log) = &mut self.log {
                    log.write_all(&chunk[..n])?;
                    log.flush()?;
                }
                self.buf.extend_from_slice(&chunk[..n]);
            }
        }
        Ok(())
    }

    /// Wait until one of the patterns matches the output. If several
    /// match, the one that matches earliest in the output wins. The
    /// output up to the end of the match is consumed.
    pub fn expect_any(&mut self, patterns: &[&Regex]) -> Result<Match, Error> {
        let start = Instant::now();
        let deadline = start + self.timeout;
        loop {
            let best = patterns
                .iter()
                .enumerate()
                .filter_map(|(i, re)| re.captures(&self.buf).map(|c| (i, c)))
                .min_by_key(|(_, c)| c.get(0).map_or(0, |m| m.start()));
            if let Some((index, caps)) = best {
                let all = caps.get(0).expect("group 0 always exists");
                let found = Match {
                    index,
                    before: lossy(&self.buf[..all.start()]),
                    text: lossy(all.as_bytes()),
                    groups: caps
                        .iter()
                        .skip(1)
                        .map(|g| g.map(|g| lossy(g.as_bytes())))
                        .collect(),
                };
                let end = all.end();
                self.buf.drain(..end);
                return Ok(found);
            }
            if self.eof {
                return Err(Error::Eof {
                    seen: lossy(&self.buf),
                });
            }
            let now = Instant::now();
            if now >= deadline {
                return Err(Error::Timeout {
                    waited: now - start,
                    seen: lossy(&self.buf),
                });
            }
            self.fill(deadline - now)?;
        }
    }

    /// Wait for one pattern (a regular expression).
    pub fn expect(&mut self, pattern: &str) -> Result<Match, Error> {
        let re = Regex::new(pattern).expect("invalid pattern");
        self.expect_any(&[&re])
    }

    /// Wait for the end of the output; return what was not consumed.
    pub fn expect_eof(&mut self) -> Result<String, Error> {
        let deadline = Instant::now() + self.timeout;
        while !self.eof {
            let now = Instant::now();
            if now >= deadline {
                return Err(Error::Timeout {
                    waited: self.timeout,
                    seen: lossy(&self.buf),
                });
            }
            self.fill(deadline - now)?;
        }
        Ok(lossy(&std::mem::take(&mut self.buf)))
    }

    /// Type some text. Use "\r" for the Enter key.
    pub fn send(&mut self, s: &str) -> Result<(), Error> {
        self.master.write_all(s.as_bytes())?;
        Ok(())
    }

    pub fn send_line(&mut self, s: &str) -> Result<(), Error> {
        self.send(&format!("{s}\r"))
    }

    /// Type a control character: send_control('c') is ^C.
    pub fn send_control(&mut self, c: char) -> Result<(), Error> {
        self.master
            .write_all(&[c.to_ascii_uppercase() as u8 ^ 0x40])?;
        Ok(())
    }

    /// The foreground process group of the PTY (TIOCGPGRP works on the
    /// master side too): tells which job owns the terminal.
    pub fn foreground(&self) -> i32 {
        unsafe { libc::tcgetpgrp(self.master.as_raw_fd()) }
    }

    /// Wait until the foreground group is no longer `old`: the shell
    /// gave the terminal to a job, or took it back.
    pub fn wait_foreground_change(&mut self, old: i32) -> Result<i32, Error> {
        let deadline = Instant::now() + self.timeout;
        loop {
            let fg = self.foreground();
            if fg != old {
                return Ok(fg);
            }
            if Instant::now() >= deadline {
                return Err(Error::Timeout {
                    waited: self.timeout,
                    seen: lossy(&self.buf),
                });
            }
            self.fill(Duration::from_millis(10))?;
        }
    }

    /// Give the keyboard to the user until they type `escape`, or the
    /// program ends. Output not consumed yet is shown first.
    pub fn interact(&mut self, escape: u8) -> Result<(), Error> {
        let stdin = io::stdin();
        let mut out = io::stdout();
        out.write_all(&std::mem::take(&mut self.buf))?;
        out.flush()?;
        if let Ok((rows, cols)) = window_size(&stdin) {
            set_window_size(&self.master, rows, cols)?;
        }
        let _raw = RawMode::enable(stdin.as_fd())?;
        let mut chunk = [0u8; 4096];
        while !self.eof {
            let mut fds = [
                PollFd::new(self.master.as_fd(), PollFlags::POLLIN),
                PollFd::new(stdin.as_fd(), PollFlags::POLLIN),
            ];
            match poll(&mut fds, PollTimeout::NONE) {
                Err(Errno::EINTR) => continue,
                r => r?,
            };
            let ev = fds.map(|f| f.revents().unwrap_or(PollFlags::empty()));
            if !ev[0].is_empty() {
                match self.master.read(&mut chunk) {
                    Ok(0) => self.eof = true,
                    Err(e) if e.raw_os_error() == Some(libc::EIO) => {
                        self.eof = true
                    }
                    Err(e) => return Err(e.into()),
                    Ok(n) => {
                        out.write_all(&chunk[..n])?;
                        out.flush()?;
                    }
                }
            }
            if !ev[1].is_empty() {
                let n = nix::unistd::read(&stdin, &mut chunk)?;
                let keys = &chunk[..n];
                if let Some(i) = keys.iter().position(|&b| b == escape) {
                    self.master.write_all(&keys[..i])?;
                    return Ok(()); // _raw restores the terminal
                }
                if n == 0 {
                    return Ok(());
                }
                self.master.write_all(keys)?;
            }
        }
        Ok(())
    }

    /// Wait for the program to exit.
    pub fn wait(&mut self) -> io::Result<ExitStatus> {
        self.child.wait()
    }
}
```

The parts, in order:

- **`Error`** has three cases, and the two interesting ones carry the
  unmatched output. With `Display`, a failing script prints, for
  example, `timeout after 5s; unmatched output: "msh$ "`: you see at
  once that the program was waiting for input.
- **`Session::spawn`** creates the PTY with `openpty` from nix and
  starts the program with `spawn_on_pty`, from chapter 22, through
  `env TERM=dumb`: `env` sets the variable and executes the program,
  which avoids touching the environment of our own process.
- **`fill`** is the only function that reads. It waits with `poll` for
  at most the remaining time, reads one chunk, and appends it to the
  buffer. `EIO` and a read of zero bytes both mean end of file. When
  a log is set (`log_to`), the raw output is copied there: the
  transcript of a session is the best debugging tool for a driver.
- **`expect_any`** tries every pattern on the whole buffer, keeps the
  match that starts earliest (`min_by_key` on the start offset), and
  only then reads more. Re-matching the whole buffer after each chunk
  is quadratic in theory; in practice buffers are small, because each
  match consumes them. A library for big outputs would limit the
  buffer (Pexpect has `maxread` and `searchwindowsize`).
- **`send_control`** computes the control character the way a
  keyboard does: the letter's code with bit 6 cleared, `'C'` (0x43)
  becomes 0x03. `^[` is ESC, `^?` (0x3F ^ 0x40 = 0x7F) is DEL.
- **`foreground`** calls `tcgetpgrp` on the master. The foreground
  process group of a terminal can be read from either side; it tells
  us which job owns the terminal. We need it for job control (30.5).
- **`interact`** is the relay of `ptyscript`, without the log, with an
  escape byte. Before starting, it copies our window size to the PTY:
  the program ran at 80x24 while it was driven, and now a human with
  a different window is looking at it.

### 30.5 Three scenarios

`main.rs` uses the library in three ways:

```rust
// file: rust/src/bin/drive/main.rs
//! Drive interactive programs with the expect module.
//!   drive shell PATH     test the job control of minishell (chapter 13)
//!   drive password       answer a password prompt
//!   drive interact       set up python, then hand over the keyboard
mod expect;
use expect::{Error, Session};
use regex::bytes::Regex;
use std::time::{Duration, Instant};

const PROMPT: &str = r"msh\$ ";

fn shell(path: &str) -> Result<(), Error> {
    let mut s = Session::spawn(&[path])?;
    s.log_to(std::fs::File::create("drive.log")?);
    s.expect(PROMPT)?;
    let shell_pgid = s.foreground();
    println!("shell ready, foreground group {shell_pgid}");

    // Start a job; ^Z must wait until the job owns the terminal: a ^Z
    // typed before that stops nothing (the shell ignores SIGTSTP).
    s.send_line("sleep 30")?;
    let job = s.wait_foreground_change(shell_pgid)?;
    println!("job running, foreground group {job}");
    s.send_control('z')?;
    let m = s.expect(r"\[(\d+)\] +Stopped +(.*)\r\n")?;
    println!(
        "job [{}] stopped: {:?}",
        m.groups[0].as_deref().unwrap_or("?"),
        m.groups[1].as_deref().unwrap_or("?")
    );
    s.expect(PROMPT)?;
    assert_eq!(
        s.foreground(),
        shell_pgid,
        "the shell took the terminal back"
    );

    s.send_line("jobs")?;
    let m = s.expect(PROMPT)?;
    println!("jobs said: {:?}", m.before);

    s.send_line("fg")?;
    s.wait_foreground_change(shell_pgid)?;
    let t = Instant::now();
    s.send_control('c')?;
    let m = s.expect(PROMPT)?;
    println!("^C: {:?}, prompt after {:?}", m.before, t.elapsed());

    s.send_line("echo pipes work | tr a-z A-Z")?;
    s.expect(r"tr a-z A-Z\r\n")?; // the echo of our line, first
    let m = s.expect(r"([A-Z ]+)\r\n")?;
    println!("pipeline: {:?}", m.groups[0].as_deref().unwrap_or(""));
    s.expect(PROMPT)?;

    s.send_line("exit 5")?;
    s.expect_eof()?;
    println!("minishell exited: {}", s.wait()?);
    Ok(())
}

fn password() -> Result<(), Error> {
    let code = "import getpass; p = getpass.getpass('Password: '); \
                print('got', len(p), 'characters')";
    let mut s = Session::spawn(&["python3", "-c", code])?;
    let m = s.expect_any(&[
        &Regex::new("(?i)password: ").unwrap(),
        &Regex::new("(?i)error").unwrap(),
    ])?;
    if m.index == 1 {
        return Err(Error::Eof { seen: m.text });
    }
    s.send_line("s3cret-é")?;
    let m = s.expect(r"got (\d+) characters")?;
    println!(
        "before the answer: {:?} (no echo of the password)",
        m.before
    );
    println!(
        "python counted {} characters",
        m.groups[0].as_deref().unwrap_or("?")
    );
    s.expect_eof()?;
    println!("exit: {}", s.wait()?);
    Ok(())
}

fn interact() -> Result<(), Error> {
    let mut s = Session::spawn(&["python3", "-q"])?;
    s.timeout = Duration::from_secs(10);
    s.expect(">>> ")?;
    s.send_line("import math, os")?;
    s.expect(">>> ")?;
    s.send_line("x = math.pi")?;
    s.expect(">>> ")?;
    println!("[python is ready with x = pi; ^] gives control back]");
    s.send("\r")?; // to get a fresh prompt on the screen
    s.interact(0x1d)?; // ^]
    println!("\r\n[back in the driver]");
    s.send_line("print('driver says', round(x, 2))")?;
    let m = s.expect(r"driver says (.*)\r\n")?;
    println!("python answered {}", m.groups[0].as_deref().unwrap_or("?"));
    s.send_control('d')?;
    s.expect_eof()?;
    println!("exit: {}", s.wait()?);
    Ok(())
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<String> = std::env::args().skip(1).collect();
    match args.iter().map(String::as_str).collect::<Vec<_>>()[..] {
        ["shell", path] => shell(path)?,
        ["password"] => password()?,
        ["interact"] => interact()?,
        _ => return Err("usage: drive shell PATH | password | interact".into()),
    }
    Ok(())
}
```

**`drive shell PATH`** drives `minishell`, the job-control shell of
chapter 13. Its prompt is `msh$ `, on standard error (which is the
terminal too). The run:

```console
$ cargo run -q --release --bin drive -- shell ../build/c/minishell
shell ready, foreground group 1056937
job running, foreground group 1056938
job [1] stopped: "sleep 30"
jobs said: "jobs\r\n[1] Stopped    sleep 30\r\n"
^C: "fg\r\nsleep 30\r\n^C", prompt after 231µs
pipeline: "PIPES WORK"
minishell exited: exit status: 5
```

Each line tells a story:

- `jobs said` shows the **echo**: the output after our `send_line`
  starts with `jobs\r\n`, our own command echoed by the line
  discipline (`echo` is on, `onlcr` turns the `\n` into `\r\n`).
- `^C` arrives in the output as the two characters `^C`: it is the
  `echoctl` flag of the line discipline, which echoes control
  characters visibly. The prompt came back 231 µs after the `^C` was
  sent: the line discipline sent `SIGINT` to the foreground group,
  `sleep` died, the shell's `waitpid` returned, the shell took the
  terminal back and printed its prompt.
- The exit status 5 is `exit 5`, passed through `waitpid`.

The scenario fell into two traps while it was written, and they are
the two classic traps of expect scripts.

**The echo trap.** The first version sent `echo pipes work | tr a-z
A-Z` and then expected `([A-Z ]+)\r\n`, an uppercase line. It
matched, and returned `"Z"`. The echo of the command line,
`echo pipes work | tr a-z A-Z\r\n`, ends with an uppercase `Z`
followed by `\r\n`; the regular expression found it first, long
before the real output. The fix is in the code: first expect the end
of the echo (`tr a-z A-Z\r\n`), then the result. The general rule:
**after sending a line, consume its echo before matching the
answer**. Pexpect users meet the same trap; some drivers turn echo off
on the PTY instead (`stty -echo` in the child, or `tcsetattr` on the
slave before starting), which works for programs that do not set
their own terminal modes.

**The job-control race.** The first version sent `sleep 30\r` and
immediately `^Z`. The `^Z` arrived while minishell was still between
`fork` and `tcsetpgrp`: the line discipline sent `SIGTSTP` to the
foreground group, which was still the shell's, and the shell ignores
`SIGTSTP` (chapter 13). The `^Z` was lost, `sleep` ran for 30 seconds,
and the `expect` for "Stopped" timed out. A human never sees this
race: nobody types that fast. The fix is `wait_foreground_change`:
poll `tcgetpgrp` on the master until the foreground group is no longer
the shell's. Waiting for output would not work: `sleep` prints
nothing. The output shows the change, from 1056937 (the shell) to
1056938 (the job, a new process group whose ID is the PID of its
first process).

`drive.log` (written by `log_to`) holds the raw transcript; its key
part, with `cat -v`:

```text
msh$ sleep 30^M
^Z[1] Stopped    sleep 30^M
msh$ jobs^M
```

**`drive password`** answers the prompt of Python's `getpass`, which
opens `/dev/tty` and turns echo off:

```console
$ cargo run -q --release --bin drive -- password
before the answer: "\r\n" (no echo of the password)
python counted 8 characters
exit: exit status: 0
```

The output between the prompt and the answer is only `\r\n`: `getpass`
turned `echo` off, so the password was not echoed, but it echoes a
newline itself after reading. Python counted 8 characters for
`s3cret-é`: the PTY passes UTF-8 bytes through, and `iutf8` (on by
default on Linux) makes the line discipline treat the two bytes of
`é` as one character for erasing. The `expect_any` call shows the
alternative: if the program printed an error instead of the prompt,
the second pattern would match.

**`drive interact`** prepares a Python session, then hands it over:

```text
[python is ready with x = pi; ^] gives control back]

>>> x * 2
6.283185307179586
>>> os.get_terminal_size()
os.terminal_size(columns=80, lines=16)
>>> 
[back in the driver]
python answered 3.14
exit: exit status: 0
```

This ran in an 80x16 tmux window, and Python reports 80x16: `interact`
copied the window size to the PTY when it took over (the PTY was
created at 80x24). The human typed `x * 2` and `os.get_terminal_size()`,
then `^]`, and the driver continued with `print` and `^D`.

### 30.6 A Raku version

The Raku version builds on `Pty.rakumod` from chapter 17: `Pty.spawn`
starts the program on a PTY through `setsid -c` and gives a `Supply`
of output chunks (`Blob`s), and `write` sends text. The `Expect` class
adds the buffer and the matching, with Raku regexes, which are a good
fit: named captures, grammars and Unicode-aware matching come for
free.

```raku
# file: raku/lib/Expect.rakumod
# A small expect for Raku: a Pty (chapter 17), a buffer of decoded
# text, and Raku regexes to wait for.
use Pty;
unit class Expect;

class X::Expect::Timeout is Exception {
    has $.seen;
    method message { "timeout; unmatched output: {$!seen.raku}" }
}
class X::Expect::EOF is Exception {
    has $.seen;
    method message { "end of output; unmatched: {$!seen.raku}" }
}

has Pty $.pty;
has Real $.timeout is rw = 5;
has Str $!text = '';               # decoded output not consumed yet
has Bool $!eof = False;
has Channel $!chunks = Channel.new;
has Buf $!pending = Buf.new;      # bytes of an incomplete character

# UTF-8 arrives in arbitrary chunks. Returns the length of the longest
# prefix of $b made of complete characters.
sub complete-utf8(Buf $b --> Int) {
    my $n = $b.elems;
    for 1 .. min(4, $n) -> $back {
        my $byte = $b[$n - $back];
        next if $byte +& 0xC0 == 0x80;        # continuation byte
        my $len = $byte < 0x80 ?? 1 !! $byte >= 0xF0 ?? 4
               !! $byte >= 0xE0 ?? 3 !! 2;
        return $len > $back ?? $n - $back !! $n;
    }
    $n
}

method spawn(*@cmd) {
    my $pty = Pty.spawn('env', 'TERM=dumb', |@cmd);
    my $self = self.bless(:$pty);
    $self!listen;
    $self
}

method !listen {
    my $chunks = $!chunks;
    $!pty.output.tap:
        -> $blob { $chunks.send($blob) },
        done => { $chunks.close },
        quit => { $chunks.close };
}

# Move what has arrived into $!text. Returns False when there is
# nothing more to come.
method !drain(--> Bool) {
    while $!chunks.poll -> $blob {
        $!pending.append($blob);
    }
    my $done = $!chunks.closed.status ~~ Kept;
    my $k = $done ?? $!pending.elems !! complete-utf8($!pending);
    # utf8-c8: invalid bytes become special graphemes instead of dying.
    # Concatenation re-forms a grapheme split between two chunks.
    $!text ~= $!pending.subbuf(0, $k).decode('utf8-c8');
    $!pending = $!pending.subbuf($k);
    $!eof = True if $done;
    !$!eof
}

#| Wait for $re in the output. Returns the Match; .prematch is what
#| came before it. The output up to the end of the match is consumed.
method expect(Regex $re --> Match) {
    my $deadline = now + $!timeout;
    loop {
        my $more = self!drain;
        if $!text ~~ $re {
            my $m = $/;
            $!text = $!text.substr($m.to);
            return $m;
        }
        X::Expect::EOF.new(seen => $!text).throw unless $more;
        X::Expect::Timeout.new(seen => $!text).throw if now > $deadline;
        sleep 0.01;
    }
}

method expect-eof(--> Str) {
    my $deadline = now + $!timeout;
    while self!drain {
        X::Expect::Timeout.new(seen => $!text).throw if now > $deadline;
        sleep 0.01;
    }
    my $rest = $!text;
    $!text = '';
    $rest
}

method send(Str $s)      { $!pty.write($s) }
method send-line(Str $s) { $!pty.write("$s\r") }
method send-control(Str $c) { $!pty.write(chr($c.uc.ord +^ 0x40)) }
method exitcode { (await $!pty.exited).exitcode }
```

And a script that drives Python:

```raku
# file: raku/expect.raku
# Drive python3 with the Expect class: questions, answers, a timeout.
use lib $*PROGRAM.parent.add('lib');
use Expect;

my $py = Expect.spawn('python3', '-q');
my $prompt = rx/ '>>> ' $ /;
$py.expect($prompt);

for '6 * 7', '2 ** 64', "'naïve'.upper()", 'len("👍🏽")' -> $q {
    $py.send-line($q);
    $py.expect(rx/ "\r\n" /);                 # the echo of our line
    my $m = $py.expect($prompt);
    printf "%-16s → %s\n", $q, $m.prematch.trim;
}

# Captures: named and numbered groups work as usual.
$py.send-line('print("version", __import__("sys").version_info[:2])');
my $m = $py.expect(rx/ 'version (' (\d+) ', ' (\d+) ')' /);
say "python {$m[0]}.{$m[1]}";
$py.expect($prompt);

# A timeout, then the output arrives anyway.
$py.timeout = 0.5;
$py.send-line('import time; time.sleep(1); print("late")');
try {
    $py.expect(rx/ ^^ 'late' \r? $$ /);
    CATCH { when X::Expect::Timeout { say "timeout: {.seen.raku}" } }
}
$py.timeout = 5;
$py.expect(rx/ ^^ 'late' /);
say 'second try: matched';

$py.send-control('d');
$py.expect-eof;
say "python exited with {$py.exitcode}";
```

The run:

```console
$ raku expect.raku
6 * 7            → 42
2 ** 64          → 18446744073709551616
'naïve'.upper()  → 'NAÏVE'
len("👍🏽")         → 2
python 3.14
timeout: "import time; time.sleep(1); print(\"late\")\r\n"
second try: matched
python exited with 0
```

(`len("👍🏽")` is 2 for Python, which counts code points: the thumb and
the skin-tone modifier. For Raku, `"👍🏽".chars` is 1: Raku strings are
sequences of graphemes. The table is misaligned on that line for the
same reason: `printf` pads by graphemes, the terminal draws the emoji
two columns wide.)

The design differs from the Rust one in two ways:

- **The reading is asynchronous.** The output `Supply` is tapped once,
  in `!listen`, and each chunk is sent to a `Channel`. `expect` polls
  the channel (`!drain`), matches, and sleeps 10 ms between attempts.
  A version without polling would `await` the channel with a timeout
  (`Promise.anyof` of a receive and a `Promise.in`); the polling
  version is easier to read, and 10 ms is invisible next to the
  latency of a human-oriented program.
- **The buffer is text, not bytes.** Raku regexes work on `Str`, so
  the bytes must be decoded, and the cut character problem of 29.6
  comes back.

The first version used the streaming decoder of Raku, which exists
for exactly this purpose:

```raku
my $d = Encoding::Registry.find('utf8').decoder;
$d.add-bytes(Blob.new(0x63, 0x61, 0x66, 0xc3));   # "caf" + half of é
say $d.consume-available-chars.raku;              # "ca"
$d.add-bytes(Blob.new(0xa9, 0x21));               # rest of é, "!"
say $d.consume-available-chars.raku;              # "fé"
```

It keeps the incomplete `é` for later, as it should, but notice the
first result: `"ca"`, not `"caf"`. The decoder also holds back the
**last complete character**, because the next chunk could start with
a combining character (U+0301, the combining acute accent, for
example) that would turn `f` into the grapheme `f́`: since a `Str` is
made of graphemes, the decoder cannot decide what `f` is until it sees
what follows. That is correct, and it broke the driver: Python's
prompt `>>> ` was always waiting in the decoder without its final
space, and the pattern `'>>> ' $` timed out:

```text
timeout; unmatched output: "warning: can't use pyrepl: (5, \"terminal
doesn't have the required clear capability\"); TERM=dumb\r\n>>>"
```

(The warning is the new Python 3.14 REPL, which needs a capable
terminal, falling back to the basic one with `TERM=dumb`.)

The fix is `complete-utf8`: find the end of the last complete UTF-8
character by looking at the last four bytes at most (a leading byte
tells the length of its sequence: `0xxxxxxx` 1, `110xxxxx` 2,
`1110xxxx` 3, `11110xxx` 4; continuation bytes are `10xxxxxx`),
decode up to there, and keep the rest. The text then ends where the
program's output ends. If a grapheme is split between two chunks, the
concatenation `$!text ~= ...` re-forms it: Raku normalizes the string
when it is built, and a combining character appended to `f` joins it.

The decoding uses `utf8-c8`, Raku's variant of UTF-8 that does not
fail on invalid bytes: they become special graphemes that encode back
to the same bytes. A driver must not die because a program printed
a Latin-1 byte.

The other differences from the Rust version are of style:

- the patterns are Raku regexes, `rx/ '>>> ' $ /`; `$m.prematch` is
  the text before the match (Rust's `before`), and `$m[0]` the first
  capture;
- the errors are exception classes, `X::Expect::Timeout` and
  `X::Expect::EOF`, caught with `CATCH` and `when`, and they carry the
  unmatched text in `.seen`;
- `exitcode` awaits the `Promise` of the process exit.

Exercise E.16 asks for `expect-any` with the earliest-match rule, and
for `interact`.

### 30.7 Go

Section 27.3 wrote a Go `expect` with the same structure: a goroutine
reads the master and sends chunks on a channel; `Expect` selects on
the channel and a timer. It shows a third way to read with a timeout:
neither `poll` (Rust) nor polling a channel (Raku), but a `select` on
two channels. Remember the warning of 27.1: with creack/pty, make the
master non-blocking if the session must be closed while the reader
goroutine waits.

For real work, use a library:

- **Python**: [Pexpect](https://pexpect.readthedocs.io), the reference,
  with `pexpect.spawn`, `expect` with lists and `pexpect.TIMEOUT` and
  `pexpect.EOF` as patterns, `interact`; and `pexpect.replwrap` for
  REPLs.
- **Rust**: `expectrl` (with async support and a `repl` module) and
  `rexpect`.
- **Go**: `github.com/Netflix/go-expect` and `github.com/google/goexpect`.
- **Raku**: no maintained module at the time of writing; the class of
  this chapter is a starting point.
- **Tcl**: the original Expect, still maintained, with `autoexpect`
  which writes a script by watching you.

### 30.8 Testing full-screen programs with tmux

An expect library matches text in a stream. For a full-screen program
(an editor, `top`, a TUI made with Bubble Tea or Ratatui), the stream
is a mess of cursor movements; what you want to test is the **screen**:
what is at row 5, column 10. That needs a terminal emulator, like the
one of chapter 31. The simplest way to get one is to use tmux: it is
a terminal emulator with a command-line interface.

- `tmux -L NAME` uses a private server (socket `NAME`), so the tests do
  not touch the user's tmux sessions;
- `new-session -d -x 80 -y 24` creates a detached session of a given
  size;
- `send-keys` types text or named keys (`Enter`, `C-c`, `Up`, `F1`,
  `M-x`);
- `capture-pane -p` prints the screen as text; with `-e`, with the
  escape sequences of colors and attributes;
- `resize-window -x 60 -y 16` changes the size, which sends `SIGWINCH`
  to the program;
- `display -p '#{pane_tty}'` gives the PTY of the pane, so that
  another process can inspect it (32.2).

This tutorial was verified that way. The helper used for most
screenshots:

```sh
#!/bin/bash
# tshot.sh COLS ROWS 'cmd' key1 key2 ... : run cmd in a private tmux,
# send keys (0.6 s apart), print the screen. A SHOT argument prints
# the screen at that point.
X=$1 Y=$2 CMD=$3; shift 3
tm() { tmux -L tshot "$@"; }
tm kill-server 2>/dev/null
tm new-session -d -x "$X" -y "$Y" -s s "bash --norc"
sleep 0.3
tm send-keys -t s "$CMD" Enter
sleep 1.2
for k in "$@"; do
  if [ "$k" = SHOT ]; then tm capture-pane -p -t s; echo "-----"
  else tm send-keys -t s "$k"; sleep 0.6; fi
done
tm capture-pane -p -t s
tm kill-server
```

For example, `tshot.sh 80 20 'c/ttylog t.log sh' 'stty -a | head -2'
Enter 'cat' Enter 'héllo' Enter C-c 'exit 3' Enter` produced the log
of 32.5. The fixed delays make it simple and slow; a robust version
would poll `capture-pane` until the expected text appears, which is
what an expect library does with a stream. For Go TUIs, the Charm
project has `teatest` (in `charmbracelet/x/exp/teatest`), which runs a
Bubble Tea model without a terminal and compares the final output
with a golden file; Ratatui has a `TestBackend` that renders into a
buffer of cells (chapter 23).

### 30.9 Summary

- Run the program on a PTY, with `TERM=dumb` and a size.
- Keep a buffer; match patterns against it; consume up to the match.
- Several patterns: the earliest match in the buffer wins.
- Consume the echo of what you send before matching the answer.
- Timeouts and end of file are errors that carry the unmatched output.
- Do not race the program: wait for a sign that it is ready (a prompt,
  or the foreground group for job control).
- Decode UTF-8 only up to the last complete character.
- Log the raw transcript.

## 31. Project: a terminal multiplexer in miniature

### 31.1 What a multiplexer is

`screen` (1987) and `tmux` (2007) run several programs in one
terminal, each in its own window or pane, and let you switch between
them, split the screen, and **detach**: leave the programs running,
log out, and attach again later from another terminal. To do that, a
multiplexer must be a terminal for its programs, and a program for
your terminal:

- for each pane, it creates a **PTY**, and starts a program on it, as
  `script` does;
- it reads what each program writes to its PTY and **interprets** it,
  exactly as a terminal emulator does: it keeps, for each pane, a grid
  of cells (characters with colors and attributes), a cursor, modes;
- it **draws** these grids, side by side or one above the other, on
  the real terminal, with escape sequences of its own, plus a status
  line;
- it reads the **keyboard**, looks for its own commands (after a
  prefix key: `^B` in tmux, `^A` in screen), and sends the other keys
  to the PTY of the active pane;
- it tells each program the **size of its pane**, with `TIOCSWINSZ` on
  its PTY, and again when the real terminal is resized.

The second point is why multiplexers are hard: they contain a complete
terminal emulator, and programs use a lot of escape sequences. tmux's
`input.c`, its parser, is about 3 000 lines; its screen code (`grid.c`,
`screen-write.c`, `tty.c`) much more.

`muxi` does all of this except detaching, in about 950 lines of Go,
with two panes stacked vertically. It is enough to run a shell, `ls
--color`, `less`, `top`, `vim` with syntax colors, or another `muxi`.

```text
   ┌──────────────── real terminal (raw mode, alternate screen) ─┐
   │  pane 1: Screen (vt.go)  ◄── output ─── PTY 1 ── vim        │
   │──────── status line ────────────────────────────────────────│
   │  pane 2: Screen (vt.go)  ◄── output ─── PTY 2 ── bash       │
   └─────────────────────────────────────────────────────────────┘
        keyboard ──► prefix ^B? ──► commands (o, q)
                          └──────► active pane's PTY
```

### 31.2 The emulator: `vt.go`

A terminal emulator has two parts: a **parser**, which splits the byte
stream into printable characters, control characters and escape
sequences, and a **screen model**, which applies them to a grid.

The parser is a state machine. The classic description is the one
Paul Flo Williams drew of the DEC VT500 parser
([vt100.net/emu/dec_ansi_parser](https://vt100.net/emu/dec_ansi_parser)),
which most emulators follow, more or less. `muxi` uses a simplified
version with eight states:

| State      | After          | Ends with                  |
|------------|----------------|----------------------------|
| ground     | normal text    | ESC starts a sequence      |
| esc        | ESC            | one byte: `7`, `M`, `[`... |
| escInter   | `ESC (` etc.   | final byte (ignored)       |
| csi        | `ESC [`        | final byte `@`-`~`         |
| osc        | `ESC ]`        | BEL or `ESC \`             |
| oscEsc     | ESC in OSC     | `\`                        |
| str        | DCS, APC, PM   | `ESC \` (ignored)          |
| strEsc     | ESC in a str   | any byte                   |

In the **ground** state, the parser also assembles UTF-8: a character
can be cut between two reads, as in chapters 29 and 30, and the
parser keeps the bytes in `s.utf` until the character is complete. A
malformed sequence becomes U+FFFD, the replacement character, as in
real terminals.

A **CSI** sequence is `ESC [`, optional private markers (`?`, `>`),
parameters (digits separated by `;`), and a final byte: `ESC [ 1 ; 31
m` is SGR (Select Graphic Rendition) with parameters 1 (bold) and 31
(red). `csiDispatch` is a `switch` on the final byte, like every
emulator's: cursor movement (`A` to `H`, `d`, `f`), erasing (`J`,
`K`, `X`), inserting and deleting characters and lines (`@`, `P`,
`L`, `M`), scrolling (`S`, `T`, `r` for the scroll region), modes
(`h`, `l`), colors and attributes (`m`), and queries (`n`, `c`).

The **screen model** has the details that make or break an emulator:

- **Pending wrap.** When a character is written in the last column,
  the cursor does not move to the next line: it stays in the last
  column, with a flag, `wrapNext`. Only the next printable character
  wraps. Without this, a program that writes exactly 80 characters
  and then `\r\n` would get an empty line, and every full-screen
  program writing the last column would scroll the screen. A carriage
  return or a cursor movement clears the flag. This is the most
  common bug of hand-written emulators.
- **The scroll region** (`ESC [ top ; bottom r`): a line feed on the
  bottom line of the region scrolls only the region. `vim` and `less`
  use it to scroll the text without redrawing the status line;
  `reverseIndex` (`ESC M`) scrolls the other way when the cursor is on
  the top line of the region.
- **The alternate screen** (mode 1049): a second grid, without
  scrollback in real terminals, that full-screen programs use so that
  the shell session is intact when they exit. Mode 1049 also saves
  the cursor on entry and restores it on exit; 47 and 1047 are older
  variants.
- **Saved cursor** (`ESC 7` and `ESC 8`, or `CSI s` and `CSI u`): the
  position and the attributes.
- **Replies.** Some sequences are questions: `ESC [ 6 n` asks for the
  cursor position (the answer is `ESC [ row ; col R`), `ESC [ c` asks
  "what are you?" (Device Attributes; `muxi` answers like a VT100 with
  advanced video, `ESC [ ? 1 ; 2 c`). The answers are written to the
  PTY, as if typed. Programs that ask and do not get an answer wait:
  some for a timeout (vim, for a fraction of a second), some forever.
  `TakeReply` gives the answers to the main loop, which writes them
  to the master.
- **Colors.** `Attr` keeps the foreground and background as an
  `int32`: -1 for the default color, 0 to 255 for the palette (16
  basic colors and the 240 of the 256-color cube and gray ramp), and
  24-bit colors with a flag bit (`trueColor`). SGR parameters `38;5;N`
  and `38;2;R;G;B` (and `48` for backgrounds) set them.
- **REP** (`CSI b`): repeat the last character. ncurses uses it to
  draw lines of the same character (it is in the `xterm-256color`
  terminfo entry as `rep`), so an emulator that claims to be an xterm
  must support it.

The whole file:

```go
// file: go/cmd/muxi/vt.go
package main

import (
	"fmt"
	"unicode/utf8"
)

// Attr is the graphic rendition of a cell (what SGR sets).
// Colors: -1 is the default color, 0-255 the palette,
// trueColor|0xRRGGBB a 24-bit color.
type Attr struct {
	FG, BG                              int32
	Bold, Faint, Italic, Under, Reverse bool
}

const trueColor = 1 << 24

var defAttr = Attr{FG: -1, BG: -1}

// Cell is one character position on the screen.
type Cell struct {
	R rune
	A Attr
}

type grid [][]Cell

func newGrid(w, h int) grid {
	g := make(grid, h)
	for y := range g {
		g[y] = blankRow(w, defAttr)
	}
	return g
}

func blankRow(w int, a Attr) []Cell {
	row := make([]Cell, w)
	for x := range row {
		row[x] = Cell{' ', Attr{FG: -1, BG: a.BG}}
	}
	return row
}

// parser states
const (
	stGround = iota
	stEsc
	stEscInter
	stCSI
	stOSC
	stOSCEsc
	stStr // DCS, SOS, PM, APC: ignored up to ST
	stStrEsc
)

// Screen is a small VT100/xterm-like terminal emulator.
// Feed it what a program writes; read the cells and the cursor.
type Screen struct {
	W, H          int
	main, alt     grid
	g             grid // the grid in use: main or alt
	inAlt         bool
	X, Y          int  // cursor position, 0-based
	wrapNext      bool // cursor sits past the last column
	attr          Attr
	top, bot      int // scroll region, inclusive rows
	savedX        int
	savedY        int
	savedAttr     Attr
	autowrap      bool
	CursorVisible bool
	AppCursor     bool // DECCKM: arrows send ESC O A, not ESC [ A
	Title         string
	last          rune   // last printed character, for REP
	reply         []byte // answers to queries, for the program

	state  int
	params []int // -1: parameter omitted
	cur    int
	digits bool
	priv   byte // '?', '>', '<' or '=' after CSI
	osc    []byte
	utf    []byte
}

func NewScreen(w, h int) *Screen {
	s := &Screen{W: w, H: h}
	s.reset()
	return s
}

func (s *Screen) reset() {
	s.main, s.alt = newGrid(s.W, s.H), newGrid(s.W, s.H)
	s.g, s.inAlt = s.main, false
	s.X, s.Y, s.wrapNext = 0, 0, false
	s.attr = defAttr
	s.top, s.bot = 0, s.H-1
	s.autowrap, s.CursorVisible, s.AppCursor = true, true, false
}

// Cells returns the visible grid. Do not modify it.
func (s *Screen) Cells() [][]Cell { return s.g }

// TakeReply returns, and forgets, the answers to the program's queries.
func (s *Screen) TakeReply() []byte {
	r := s.reply
	s.reply = nil
	return r
}

// Resize keeps the top-left part of both grids.
func (s *Screen) Resize(w, h int) {
	resize := func(old grid) grid {
		g := newGrid(w, h)
		for y := 0; y < h && y < len(old); y++ {
			copy(g[y], old[y])
		}
		return g
	}
	s.main, s.alt = resize(s.main), resize(s.alt)
	s.g = s.main
	if s.inAlt {
		s.g = s.alt
	}
	s.W, s.H = w, h
	s.top, s.bot = 0, h-1
	s.X, s.Y = min(s.X, w-1), min(s.Y, h-1)
	s.wrapNext = false
}

// Feed interprets a chunk of output. Escape sequences and UTF-8
// characters may be split across calls: the state is kept.
func (s *Screen) Feed(data []byte) {
	for _, b := range data {
		s.feedByte(b)
	}
}

func (s *Screen) feedByte(b byte) {
	switch s.state {
	case stGround:
		s.ground(b)
	case stEsc:
		s.escape(b)
	case stEscInter:
		if b >= 0x30 { // final byte of ESC ( B and the like
			s.state = stGround
		}
	case stCSI:
		s.csiByte(b)
	case stOSC:
		switch b {
		case 0x07:
			s.oscDispatch()
		case 0x1b:
			s.state = stOSCEsc
		default:
			if len(s.osc) < 4096 {
				s.osc = append(s.osc, b)
			}
		}
	case stOSCEsc: // ESC \ (ST) ends the string
		s.oscDispatch()
	case stStr:
		if b == 0x1b {
			s.state = stStrEsc
		}
	case stStrEsc:
		s.state = stGround
	}
}

func (s *Screen) ground(b byte) {
	if len(s.utf) > 0 || b >= 0x80 {
		if b >= 0x80 && b < 0xc0 && len(s.utf) > 0 {
			s.utf = append(s.utf, b) // continuation byte
		} else if b >= 0xc0 {
			if len(s.utf) > 0 {
				s.put(utf8.RuneError) // previous one was cut short
			}
			s.utf = append(s.utf[:0], b)
		} else if b >= 0x80 { // stray continuation byte
			s.put(utf8.RuneError)
			return
		} else { // ASCII byte in the middle of a character
			s.put(utf8.RuneError)
			s.utf = s.utf[:0]
			s.ground(b)
			return
		}
		if utf8.FullRune(s.utf) {
			r, _ := utf8.DecodeRune(s.utf)
			s.utf = s.utf[:0]
			s.put(r)
		}
		return
	}
	switch b {
	case 0x1b:
		s.state = stEsc
	case '\r':
		s.X, s.wrapNext = 0, false
	case '\n', 0x0b, 0x0c:
		s.lineFeed()
	case '\b':
		if s.X > 0 {
			s.X--
		}
		s.wrapNext = false
	case '\t':
		s.X = min((s.X/8+1)*8, s.W-1)
	default:
		if b >= 0x20 && b < 0x7f {
			s.put(rune(b))
		} // other C0 controls (BEL, NUL...) and DEL: ignored
	}
}

func (s *Screen) put(r rune) {
	if s.wrapNext {
		s.wrapNext = false
		if s.autowrap {
			s.X = 0
			s.lineFeed()
		}
	}
	s.g[s.Y][s.X] = Cell{r, s.attr}
	s.last = r
	if s.X == s.W-1 {
		s.wrapNext = true // xterm's "pending wrap" state
	} else {
		s.X++
	}
}

func (s *Screen) lineFeed() {
	s.wrapNext = false
	if s.Y == s.bot {
		s.scrollUp(1)
	} else if s.Y < s.H-1 {
		s.Y++
	}
}

func (s *Screen) reverseIndex() {
	if s.Y == s.top {
		s.scrollDown(1)
	} else if s.Y > 0 {
		s.Y--
	}
}

// scrollUp moves the lines of the scroll region up by n.
func (s *Screen) scrollUp(n int) { s.scrollRegion(s.top, n) }

// scrollDown moves them down by n.
func (s *Screen) scrollDown(n int) { s.scrollRegion(s.top, -n) }

// scrollRegion scrolls rows from..bot; n > 0 scrolls up.
func (s *Screen) scrollRegion(from, n int) {
	rows := s.g[from : s.bot+1]
	if n > 0 {
		n = min(n, len(rows))
		copy(rows, rows[n:])
		for i := len(rows) - n; i < len(rows); i++ {
			rows[i] = blankRow(s.W, s.attr)
		}
	} else {
		n = min(-n, len(rows))
		copy(rows[n:], rows)
		for i := 0; i < n; i++ {
			rows[i] = blankRow(s.W, s.attr)
		}
	}
}

func (s *Screen) escape(b byte) {
	s.state = stGround
	switch b {
	case '[':
		s.state = stCSI
		s.params, s.cur, s.digits, s.priv = s.params[:0], 0, false, 0
	case ']':
		s.state = stOSC
		s.osc = s.osc[:0]
	case 'P', 'X', '^', '_':
		s.state = stStr
	case '(', ')', '*', '+', '#', '%', ' ':
		s.state = stEscInter
	case '7':
		s.saveCursor()
	case '8':
		s.restoreCursor()
	case 'D':
		s.lineFeed()
	case 'E':
		s.X = 0
		s.lineFeed()
	case 'M':
		s.reverseIndex()
	case 'c':
		s.reset()
	} // ESC = and ESC > (keypad modes) and the rest: ignored
}

func (s *Screen) saveCursor() {
	s.savedX, s.savedY, s.savedAttr = s.X, s.Y, s.attr
}

func (s *Screen) restoreCursor() {
	s.X, s.Y, s.attr = min(s.savedX, s.W-1), min(s.savedY, s.H-1), s.savedAttr
	s.wrapNext = false
}

func (s *Screen) csiByte(b byte) {
	switch {
	case b >= '0' && b <= '9':
		s.cur = s.cur*10 + int(b-'0')
		s.digits = true
	case b == ';' || b == ':':
		s.pushParam()
	case b >= '<' && b <= '?':
		s.priv = b
	case b >= 0x20 && b <= 0x2f:
		// intermediate bytes (CSI ! p, CSI SP q...): kept in priv
		s.priv = b
	case b >= 0x40 && b <= 0x7e:
		s.pushParam()
		s.state = stGround
		s.csiDispatch(b)
	case b == 0x1b:
		s.state = stEsc
	case b == 0x18 || b == 0x1a: // CAN, SUB: abort
		s.state = stGround
	}
}

func (s *Screen) pushParam() {
	if s.digits {
		s.params = append(s.params, s.cur)
	} else {
		s.params = append(s.params, -1)
	}
	s.cur, s.digits = 0, false
}

// p returns parameter i, or def if it is omitted or 0.
func (s *Screen) p(i, def int) int {
	if i < len(s.params) && s.params[i] > 0 {
		return s.params[i]
	}
	return def
}

func clamp(v, lo, hi int) int { return max(lo, min(v, hi)) }

func (s *Screen) csiDispatch(f byte) {
	if s.priv == '?' && (f == 'h' || f == 'l') {
		for _, m := range s.params {
			s.setMode(m, f == 'h')
		}
		return
	}
	if s.priv == '>' && f == 'c' { // secondary device attributes
		s.reply = append(s.reply, "\x1b[>0;0;0c"...)
		return
	}
	if s.priv != 0 {
		return // other private or intermediate sequences: ignored
	}
	s.wrapNext = false
	switch f {
	case 'A':
		s.Y = clamp(s.Y-s.p(0, 1), 0, s.H-1)
	case 'B', 'e':
		s.Y = clamp(s.Y+s.p(0, 1), 0, s.H-1)
	case 'C', 'a':
		s.X = clamp(s.X+s.p(0, 1), 0, s.W-1)
	case 'D':
		s.X = clamp(s.X-s.p(0, 1), 0, s.W-1)
	case 'E':
		s.X, s.Y = 0, clamp(s.Y+s.p(0, 1), 0, s.H-1)
	case 'F':
		s.X, s.Y = 0, clamp(s.Y-s.p(0, 1), 0, s.H-1)
	case 'G', '`':
		s.X = clamp(s.p(0, 1)-1, 0, s.W-1)
	case 'd':
		s.Y = clamp(s.p(0, 1)-1, 0, s.H-1)
	case 'H', 'f':
		s.Y = clamp(s.p(0, 1)-1, 0, s.H-1)
		s.X = clamp(s.p(1, 1)-1, 0, s.W-1)
	case 'J':
		s.eraseDisplay(s.p(0, 0))
	case 'K':
		s.eraseLine(s.p(0, 0))
	case '@': // insert blank characters
		row := s.g[s.Y]
		n := min(s.p(0, 1), s.W-s.X)
		copy(row[s.X+n:], row[s.X:])
		s.blank(row[s.X : s.X+n])
	case 'P': // delete characters
		row := s.g[s.Y]
		n := min(s.p(0, 1), s.W-s.X)
		copy(row[s.X:], row[s.X+n:])
		s.blank(row[s.W-n:])
	case 'X': // erase characters
		s.blank(s.g[s.Y][s.X:min(s.X+s.p(0, 1), s.W)])
	case 'L', 'M': // insert or delete lines, inside the region
		if s.Y >= s.top && s.Y <= s.bot {
			n := s.p(0, 1)
			if f == 'L' {
				n = -n
			}
			s.scrollRegion(s.Y, n)
			s.X = 0
		}
	case 'S':
		s.scrollUp(s.p(0, 1))
	case 'T':
		s.scrollDown(s.p(0, 1))
	case 'b': // REP: repeat the last character
		for range min(s.p(0, 1), s.W*s.H) {
			s.put(s.last)
		}
	case 'm':
		s.sgr()
	case 'r':
		top, bot := s.p(0, 1)-1, s.p(1, s.H)-1
		if top < bot && bot < s.H {
			s.top, s.bot = top, bot
			s.X, s.Y = 0, 0
		}
	case 's':
		s.saveCursor()
	case 'u':
		s.restoreCursor()
	case 'n': // device status report
		switch s.p(0, 0) {
		case 5:
			s.reply = append(s.reply, "\x1b[0n"...)
		case 6:
			s.reply = fmt.Appendf(s.reply, "\x1b[%d;%dR", s.Y+1, s.X+1)
		}
	case 'c': // primary device attributes: "VT100 with AVO"
		s.reply = append(s.reply, "\x1b[?1;2c"...)
	} // anything else (CSI t, CSI h/l, CSI q...): ignored
}

func (s *Screen) blank(cells []Cell) {
	for i := range cells {
		cells[i] = Cell{' ', Attr{FG: -1, BG: s.attr.BG}}
	}
}

func (s *Screen) eraseDisplay(mode int) {
	switch mode {
	case 0: // from the cursor to the end
		s.eraseLine(0)
		for y := s.Y + 1; y < s.H; y++ {
			s.blank(s.g[y])
		}
	case 1: // from the start to the cursor
		s.eraseLine(1)
		for y := 0; y < s.Y; y++ {
			s.blank(s.g[y])
		}
	case 2, 3: // everything (3: and the scrollback, which we lack)
		for y := range s.g {
			s.blank(s.g[y])
		}
	}
}

func (s *Screen) eraseLine(mode int) {
	row := s.g[s.Y]
	switch mode {
	case 0:
		s.blank(row[s.X:])
	case 1:
		s.blank(row[:s.X+1])
	case 2:
		s.blank(row)
	}
}

func (s *Screen) setMode(m int, on bool) {
	switch m {
	case 1:
		s.AppCursor = on
	case 7:
		s.autowrap = on
	case 25:
		s.CursorVisible = on
	case 47, 1047, 1049: // alternate screen
		if m == 1049 && on {
			s.saveCursor()
		}
		s.inAlt = on
		if on {
			s.g = s.alt
			for y := range s.g {
				s.blank(s.g[y])
			}
		} else {
			s.g = s.main
		}
		if m == 1049 && !on {
			s.restoreCursor()
		}
	} // mouse, bracketed paste, focus... (1000, 2004, 1004): ignored
}

func (s *Screen) oscDispatch() {
	s.state = stGround
	// OSC 0 ; title  and  OSC 2 ; title  set the window title
	if len(s.osc) > 2 && (s.osc[0] == '0' || s.osc[0] == '2') && s.osc[1] == ';' {
		s.Title = string(s.osc[2:])
	}
}

func (s *Screen) sgr() {
	ps := s.params
	if len(ps) == 0 {
		ps = []int{0}
	}
	color := func(i int) (int32, int) { // after 38 or 48
		if i+2 < len(ps) && ps[i+1] == 5 {
			return int32(max(ps[i+2], 0)), 2
		}
		if i+4 < len(ps) && ps[i+1] == 2 {
			r, g, b := max(ps[i+2], 0), max(ps[i+3], 0), max(ps[i+4], 0)
			return int32(trueColor | r<<16 | g<<8 | b), 4
		}
		return -1, len(ps) // malformed: skip the rest
	}
	a := &s.attr
	for i := 0; i < len(ps); i++ {
		switch n := max(ps[i], 0); {
		case n == 0:
			*a = defAttr
		case n == 1:
			a.Bold = true
		case n == 2:
			a.Faint = true
		case n == 3:
			a.Italic = true
		case n == 4:
			a.Under = true
		case n == 7:
			a.Reverse = true
		case n == 22:
			a.Bold, a.Faint = false, false
		case n == 23:
			a.Italic = false
		case n == 24:
			a.Under = false
		case n == 27:
			a.Reverse = false
		case n >= 30 && n <= 37:
			a.FG = int32(n - 30)
		case n == 38:
			c, skip := color(i)
			a.FG, i = c, i+skip
		case n == 39:
			a.FG = -1
		case n >= 40 && n <= 47:
			a.BG = int32(n - 40)
		case n == 48:
			c, skip := color(i)
			a.BG, i = c, i+skip
		case n == 49:
			a.BG = -1
		case n >= 90 && n <= 97:
			a.FG = int32(n - 90 + 8)
		case n >= 100 && n <= 107:
			a.BG = int32(n - 100 + 8)
		}
	}
}
```

What is missing, compared with a real emulator:

- **Wide characters.** CJK ideographs and most emoji take two columns
  (`wcwidth` returns 2). `muxi` puts every character in one cell, so a
  line with Chinese text is misaligned. A real emulator stores the
  character in the first cell and a placeholder in the second, and
  handles the cases where a wide character does not fit at the end of
  a line. Exercise E.29.
- **Combining characters.** `e` followed by U+0301 must stay in one
  cell. `muxi` gives U+0301 its own cell.
- **Scrollback**, **tab stops** other than every 8 columns, **insert
  mode** (mode 4), **origin mode** (mode 6), **mouse reporting**,
  **bracketed paste**, **focus events**, **the Kitty keyboard
  protocol**, character sets (`ESC ( 0` for line drawing: `muxi`
  ignores it, so old programs draw boxes with `qqqq`), and dozens of
  less common sequences.

Even so, the result is good enough for everyday programs, because they
use a small part of the repertoire.

### 31.3 The multiplexer: `main.go`

The main program:

```go
// file: go/cmd/muxi/main.go
// muxi: a terminal multiplexer in miniature. Two panes, one above the
// other, each running a command on its own pseudo-terminal, drawn
// through the small emulator of vt.go. ^B o switches panes, ^B q quits,
// ^B ^B sends a ^B.
package main

import (
	"fmt"
	"os"
	"os/exec"
	"os/signal"
	"strings"
	"syscall"
	"time"

	"github.com/creack/pty"
	"golang.org/x/term"
)

const prefix = 0x02 // ^B, as in tmux

type pane struct {
	name   string
	cmd    *exec.Cmd
	ptmx   *os.File
	scr    *Screen
	row0   int // first row on the real screen
	dirty  bool
	exited string // non-empty once the child is gone
}

type output struct {
	p    *pane
	data []byte // nil at the end
}

type mux struct {
	panes     []*pane
	active    int
	w, h      int
	out       strings.Builder
	appCursor bool // DECCKM state of the real terminal
}

func main() { os.Exit(run()) }

func run() int {
	cmds := os.Args[1:]
	if len(cmds) > 2 {
		fmt.Fprintln(os.Stderr, "usage: muxi [command [command]]")
		return 2
	}
	shell := os.Getenv("SHELL")
	if shell == "" {
		shell = "/bin/sh"
	}
	for len(cmds) < 2 {
		cmds = append(cmds, shell)
	}
	if !term.IsTerminal(0) || !term.IsTerminal(1) {
		fmt.Fprintln(os.Stderr, "muxi: stdin and stdout must be a terminal")
		return 1
	}
	w, h, err := term.GetSize(1)
	if err != nil || h < 5 {
		fmt.Fprintln(os.Stderr, "muxi: terminal too small")
		return 1
	}
	m := &mux{w: w, h: h}
	outc := make(chan output, 16)
	for _, c := range cmds {
		p := &pane{name: c}
		m.panes = append(m.panes, p)
	}
	m.layout()
	for _, p := range m.panes {
		if err := p.start(outc); err != nil {
			fmt.Fprintln(os.Stderr, "muxi:", err)
			return 1
		}
	}

	saved, err := term.MakeRaw(0)
	if err != nil {
		fmt.Fprintln(os.Stderr, "muxi:", err)
		return 1
	}
	defer term.Restore(0, saved)
	// alternate screen, clear; on exit: main screen, normal cursor keys
	os.Stdout.WriteString("\x1b[?1049h\x1b[H\x1b[2J")
	defer os.Stdout.WriteString("\x1b[?1l\x1b[?25h\x1b[?1049l")

	inc := make(chan []byte)
	go func() {
		for {
			buf := make([]byte, 1024)
			n, err := os.Stdin.Read(buf)
			if err != nil {
				close(inc)
				return
			}
			inc <- buf[:n]
		}
	}()
	winch := make(chan os.Signal, 1)
	signal.Notify(winch, syscall.SIGWINCH)
	tick := time.NewTicker(15 * time.Millisecond)
	defer tick.Stop()

	waitingPrefix := false
	for {
		select {
		case o := <-outc:
			if o.data == nil {
				o.p.exited = o.p.wait()
				if m.panes[m.active] == o.p {
					m.active = 1 - m.active
				}
				if m.allExited() {
					m.render()
					return 0
				}
				m.dirtyAll()
				continue
			}
			o.p.scr.Feed(o.data)
			if r := o.p.scr.TakeReply(); r != nil {
				o.p.ptmx.Write(r) // answers to ESC [ 6 n and friends
			}
			o.p.dirty = true
		case in, ok := <-inc:
			if !ok {
				return 0
			}
			var fwd []byte
			for _, b := range in {
				switch {
				case waitingPrefix:
					waitingPrefix = false
					switch b {
					case 'o':
						if m.panes[1-m.active].exited == "" {
							m.active = 1 - m.active
							m.dirtyAll()
						}
					case 'q':
						m.closeAll()
						return 0
					case prefix:
						fwd = append(fwd, b)
					}
				case b == prefix:
					waitingPrefix = true
				default:
					fwd = append(fwd, b)
				}
			}
			if p := m.panes[m.active]; len(fwd) > 0 && p.exited == "" {
				p.ptmx.Write(fwd)
			}
		case <-winch:
			w, h, err := term.GetSize(1)
			if err == nil && h >= 5 {
				m.w, m.h = w, h
				m.layout()
				os.Stdout.WriteString("\x1b[2J")
			}
		case <-tick.C:
			m.render()
		}
	}
}

// layout gives each pane its rows (and its pty its size); the status
// line sits between the two panes.
func (m *mux) layout() {
	h0 := (m.h - 1) / 2
	sizes := []int{h0, m.h - 1 - h0}
	row := 0
	for i, p := range m.panes {
		p.row0 = row
		row += sizes[i] + 1
		if p.scr == nil {
			p.scr = NewScreen(m.w, sizes[i])
		} else {
			p.scr.Resize(m.w, sizes[i])
		}
		if p.ptmx != nil {
			pty.Setsize(p.ptmx, &pty.Winsize{Rows: uint16(sizes[i]), Cols: uint16(m.w)})
		}
		p.dirty = true
	}
}

func (p *pane) start(outc chan<- output) error {
	p.cmd = exec.Command("sh", "-c", "exec "+p.name)
	p.cmd.Env = append(os.Environ(), "TERM=xterm-256color", "MUXI=1")
	ws := &pty.Winsize{Rows: uint16(p.scr.H), Cols: uint16(p.scr.W)}
	ptmx, err := pty.StartWithSize(p.cmd, ws)
	if err != nil {
		return err
	}
	// creack/pty leaves the master in blocking mode; in non-blocking
	// mode, Go's poller handles it, and Close interrupts a pending Read.
	if err := syscall.SetNonblock(int(ptmx.Fd()), true); err != nil {
		return err
	}
	p.ptmx = ptmx
	go func() {
		for {
			buf := make([]byte, 4096)
			n, err := ptmx.Read(buf)
			if n > 0 {
				outc <- output{p, buf[:n]}
			}
			if err != nil { // EIO: the child and its children are gone
				outc <- output{p, nil}
				return
			}
		}
	}()
	return nil
}

func (p *pane) wait() string {
	p.ptmx.Close()
	if err := p.cmd.Wait(); err != nil {
		return err.Error()
	}
	return "exit status 0"
}

// closeAll hangs up the terminals: the kernel sends SIGHUP to each
// session, as when a terminal window is closed.
func (m *mux) closeAll() {
	for _, p := range m.panes {
		if p.exited == "" {
			p.ptmx.Close()
			p.cmd.Wait()
		}
	}
}

func (m *mux) allExited() bool {
	for _, p := range m.panes {
		if p.exited == "" {
			return false
		}
	}
	return true
}

func (m *mux) dirtyAll() {
	for _, p := range m.panes {
		p.dirty = true
	}
}

// render redraws the panes that changed, in one write, as one
// synchronized update (mode 2026) so that the terminal shows no
// half-drawn frame.
func (m *mux) render() {
	b := &m.out
	b.Reset()
	b.WriteString("\x1b[?2026h\x1b[?25l")
	redrawn := false
	for _, p := range m.panes {
		if p.dirty {
			m.drawPane(p)
			p.dirty, redrawn = false, true
		}
	}
	if !redrawn {
		return
	}
	m.drawStatus()
	act := m.panes[m.active]
	if act.scr.AppCursor != m.appCursor { // keys must match the pane
		m.appCursor = act.scr.AppCursor
		b.WriteString(map[bool]string{true: "\x1b[?1h", false: "\x1b[?1l"}[m.appCursor])
	}
	fmt.Fprintf(b, "\x1b[%d;%dH", act.row0+act.scr.Y+1, act.scr.X+1)
	if act.scr.CursorVisible && act.exited == "" {
		b.WriteString("\x1b[?25h")
	}
	b.WriteString("\x1b[?2026l")
	os.Stdout.WriteString(b.String())
}

func (m *mux) drawPane(p *pane) {
	b := &m.out
	for y, row := range p.scr.Cells() {
		fmt.Fprintf(b, "\x1b[%d;1H", p.row0+y+1)
		last := Attr{FG: -2}
		for _, c := range row {
			if c.A != last {
				b.WriteString(sgr(c.A))
				last = c.A
			}
			b.WriteRune(c.R)
		}
	}
	b.WriteString("\x1b[0m")
}

func (m *mux) drawStatus() {
	var s strings.Builder
	s.WriteString(" muxi ")
	for i, p := range m.panes {
		name := p.name
		if t := p.scr.Title; t != "" {
			name = t
		}
		if p.exited != "" {
			name += " (" + p.exited + ")"
		}
		mark := " "
		if i == m.active {
			mark = "*"
		}
		fmt.Fprintf(&s, " %s%d:%s ", mark, i+1, truncate(name, 24))
	}
	s.WriteString("  ^B o switch  ^B q quit")
	line := truncate(s.String(), m.w)
	line += strings.Repeat(" ", max(m.w-len([]rune(line)), 0))
	fmt.Fprintf(&m.out, "\x1b[%d;1H\x1b[0;7m%s\x1b[0m", m.panes[1].row0, line)
}

func truncate(s string, n int) string {
	r := []rune(s)
	if len(r) > n {
		return string(r[:n])
	}
	return s
}

// sgr turns an Attr into the escape sequence that selects it.
func sgr(a Attr) string {
	s := "\x1b[0"
	for _, f := range []struct {
		on   bool
		code string
	}{{a.Bold, "1"}, {a.Faint, "2"}, {a.Italic, "3"}, {a.Under, "4"}, {a.Reverse, "7"}} {
		if f.on {
			s += ";" + f.code
		}
	}
	return s + color(a.FG, 30) + color(a.BG, 40) + "m"
}

func color(c int32, base int) string {
	switch {
	case c < 0:
		return ""
	case c < 8:
		return fmt.Sprintf(";%d", base+int(c))
	case c < 16:
		return fmt.Sprintf(";%d", base+60+int(c)-8)
	case c < 256:
		return fmt.Sprintf(";%d;5;%d", base+8, c)
	default:
		return fmt.Sprintf(";%d;2;%d;%d;%d", base+8, c>>16&0xff, c>>8&0xff, c&0xff)
	}
}
```

How it works:

- **Starting the panes.** `layout` computes the size of each pane
  (the screen height minus one line for the status line, split in
  two), and `start` runs each command through `sh -c "exec CMD"` on a
  PTY of that size, with `TERM=xterm-256color` (the emulator
  understands enough of it) and `MUXI=1` in the environment (so that
  a shell can tell it is inside muxi, as tmux sets `TMUX`). Then it
  makes the master **non-blocking**: as 27.1 explained, creack/pty
  leaves it blocking, and then closing it would not interrupt the
  reader goroutine.
- **One goroutine per pane** reads the master and sends `output{p,
  data}` values on a channel; at end of file (`EIO`), it sends `nil`
  data. A goroutine reads the keyboard and sends chunks on another
  channel.
- **The main loop** is a `select` on four channels: output of the
  panes, keyboard, `SIGWINCH`, and a 15 ms ticker. All the state
  (screens, active pane, prefix flag) is owned by this one goroutine,
  so there are no locks.
- **Output** is fed to the pane's `Screen`, and the pane is marked
  dirty. Nothing is drawn yet: a program can write a screen in many
  small chunks, and drawing after each would be slow and would show
  half-drawn screens. The **ticker** redraws the dirty panes at most
  every 15 ms, about 66 frames per second.
- **Rendering** writes, for each dirty pane, every row: a cursor
  movement, then the cells, with an SGR sequence each time the
  attributes change. It is wrapped in `ESC [ ? 2026 h` and `ESC [ ?
  2026 l`, **synchronized output**: terminals that support it (kitty,
  foot, WezTerm, iTerm2, Alacritty, tmux itself...) show the frame
  only when it is complete, and the others ignore the sequences.
  Then the cursor is placed where the active pane's cursor is, and
  hidden if that pane hid it.
- **Cursor keys.** A program like `vim` or `less` sends `ESC [ ? 1 h`
  (DECCKM, application cursor keys, part of `smkx` in terminfo) to
  ask for `ESC O A` instead of `ESC [ A` for the Up key. The emulator
  records the mode, and the renderer sets the same mode on the real
  terminal for the active pane, so that the real terminal sends the
  keys the program expects.
- **The keyboard.** Bytes are scanned for the prefix `^B` (0x02).
  After it, `o` switches to the other pane, `q` quits, and `^B` sends
  a literal `^B`. Other keys are sent to the active pane. The prefix
  state survives across reads: `^B` and `o` can arrive in two chunks.
- **Resizing.** On `SIGWINCH`, `layout` computes the new sizes, resizes
  the screens, and calls `pty.Setsize` on each master, which does
  `TIOCSWINSZ`: the kernel then sends `SIGWINCH` to the foreground
  process group of each PTY, and the programs redraw.
- **Ending.** When a pane's program exits, its reader gets `EIO`; the
  pane is marked exited (with its status), the focus moves to the
  other pane, and when both have exited, `muxi` exits. `^B q` instead
  calls `closeAll`, which closes the masters: for the kernel, the
  terminal was hung up, and it sends `SIGHUP` to the session of each
  pane, which is what happens when you close a terminal window.

### 31.4 Running it

```console
$ PS1='$ ' muxi 'vim -u NONE -c "syntax on" cmd/muxi/vt.go' 'bash --norc'
```

The test (`tools/muxtest.sh`, built on the tmux technique of 30.8)
starts `muxi` with `vim` on its own source in the top pane and `bash`
in the bottom pane, in an 80x24 window. It switches to the bottom
pane with `^B o`, prints colors and non-ASCII characters, switches
back with `^B o`, and types `20G` in vim. `tmux capture-pane -p -e`
then gives the screen with its escape sequences; through `cat -v`, a
few lines:

```text
^[[38;5;130mconst^[[39m trueColor = ^[[31m1^[[39m << ^[[31m24^[[39m
"cmd/muxi/vt.go" 580 lines, 12280 bytes
^[[7m muxi  *1:vim -u NONE -c "syntax o   2:bash --norc   ^B o switch  ^B q quit
^[[0mbash-5.3$ printf '\033[1;31mred\033[0m \033[38;5;208morange\033[0m \033[7mrev\03
3[0m M-CM-)M-bM-^FM-^R\n'
^[[1m^[[31mred^[[0m ^[[38;5;208morange^[[39m ^[[7mrev^[[0m M-CM-)M-bM-^FM-^R
```

The first line is vim's syntax highlighting (`const` in color 130 of
the 256-color palette, the numbers in red), drawn by vim into the
emulator of `muxi`, then redrawn by `muxi` on tmux's terminal. The
status line is in reverse video, the active pane marked with `*`. In
the bottom pane, `red` is bold and red, `orange` is color 208, `rev`
is in reverse video, and `é→` went through as UTF-8 (`M-CM-)` is
`é`, `M-bM-^FM-^R` is `→`, as `cat -v` shows bytes above 127).

Then the test resizes the tmux window to 60x16. `muxi` gets
`SIGWINCH`, gives each pane its new size, and vim and bash redraw:

```text
const trueColor = 1 << 24

var defAttr = Attr{FG: -1, BG: -1}

// Cell is one character position on the screen.
type Cell struct {

 muxi  *1:vim -u NONE -c "syntax o   2:bash --norc   ^B o sw
bash-5.3$ printf '\033[1;31mred\033[0m \033[38;5;208morange\
3[0m é→\n'
red orange rev é→
bash-5.3$ PS1='$ '
$
```

Finally `:q` in vim, `exit` in bash: the panes exit one after the
other, `muxi` restores the main screen, and the shell shows
`muxi=0`. In an earlier test, `^B q` with `sleep 1234` in a pane:
`muxi` exited at once, and `sleep` was gone, killed by the `SIGHUP`
of the hangup. Without the non-blocking master, the same `^B q` hung
until `sleep` ended by itself, as 27.1 described: that is how the
problem was found.

Other checks made by hand in muxi: `tput cols` and `tput lines` in a
pane print the pane's size (80 and 11 in an 80x24 window: 23 lines
minus the status line, split in two); `tty` prints a different
`/dev/pts/N` in each pane; `less` uses the alternate screen and the
shell's output is back when it exits; `seq 1000` scrolls correctly.

### 31.5 From muxi to tmux

What a real multiplexer adds, and how:

- **Detaching.** tmux is two processes: a **server**, which owns the
  PTYs, the programs and the screens, and a **client**, which is
  attached to your terminal. They talk over a Unix-domain socket
  (`/tmp/tmux-UID/default`). When you detach, the client exits and the
  server keeps running; `tmux attach` starts a new client. The client
  sends its terminal (the file descriptor itself, with `SCM_RIGHTS`,
  as ancillary data on the socket) to the server, which then writes
  to it directly. Exercise E.31 sketches this design for muxi.
- **Damage tracking.** muxi redraws whole rows of dirty panes. tmux
  compares the new screen with what the terminal already shows, and
  sends only the differences, with the cheapest sequences (erase to
  end of line instead of spaces, scroll regions instead of
  redrawing).
- **Its own `TERM`.** tmux sets `TERM=tmux-256color` (or
  `screen-256color`) in its panes, describing what its emulator
  supports, and translates to whatever the outer terminal supports,
  using the outer terminal's terminfo entry. muxi lies a little by
  claiming `xterm-256color`, and passes some sequences through without
  checking that the outer terminal supports them.
- **Copy mode and scrollback**, **many windows and panes** with
  layouts, **a command language** and configuration file, **key
  tables**, **hooks**, **mouse support**, **passthrough** of sequences
  for the outer terminal (`ESC P tmux; ... ESC \`), and so on: tmux
  is about 80 000 lines of C.

## 32. Debugging terminals and pipes

Terminal problems are hard to debug because the symptom (a key that
does nothing, a program that hangs, a garbled screen) is far from the
cause (a mode, a process group, a byte). This chapter collects the
tools, from the simplest. All outputs are real, captured on this
machine in a tmux pane (`/dev/pts/17`), except for 32.7 (`strace`,
`ltrace` and `lsof` are not installed here).

### 32.1 Which terminal, which modes

`tty` prints the name of the terminal on standard input; `stty -a`
prints all its settings:

```console
$ tty
/dev/pts/17
$ stty -a
speed 38400 baud; rows 50; columns 100; line = 0;
intr = ^C; quit = ^\; erase = ^?; kill = ^U; eof = ^D; eol = <undef>;
eol2 = <undef>; swtch = <undef>; start = ^Q; stop = ^S; susp = ^Z; rprnt = ^R;
werase = ^W; lnext = ^V; discard = ^O; min = 1; time = 0;
-parenb -parodd -cmspar cs8 -hupcl -cstopb cread -clocal -crtscts
-ignbrk -brkint -ignpar -parmrk -inpck -istrip -inlcr -igncr icrnl ixon -ixoff
-iuclc -ixany -imaxbel iutf8
opost -olcuc -ocrnl onlcr -onocr -onlret -ofill -ofdel nl0 cr0 tab0 bs0 vt0 ff0
isig icanon iexten echo echoe echok -echonl -noflsh -xcase -tostop -echoprt
echoctl echoke -flusho -extproc
```

How to read it (Appendix A has every flag):

- the first line: the speed (meaningless for a PTY, but reported), the
  **window size** (`rows 50; columns 100`): if it is `0`, programs
  will misbehave, see 32.9;
- the next three lines: the **special characters**; a `^?` erase
  means the Backspace key must send DEL (0x7F), which is the modern
  convention;
- then the flags, by group: control (`c_cflag`), input (`c_iflag`),
  output (`c_oflag`), local (`c_lflag`). The ones to check first:
  `icanon` (line mode), `echo`, `isig` (^C and friends are signals),
  `icrnl` (Enter gives `\n`), `opost` and `onlcr` (`\n` is written as
  `\r\n`), `ixon` (^S freezes the output!), `iutf8`.

`stty -a < /dev/pts/N` shows the settings of another terminal you own:
`stty` works on its standard input. This is how to look at the modes a
program has set while it runs: from another terminal, while the
program has its own terminal in raw mode. (In 32.5, `ttylog` does the
same thing continuously from the master side.)

### 32.2 Who owns the terminal

`ps` with the right columns shows sessions and process groups:

```console
$ ps -o pid,ppid,pgid,sid,tpgid,tty,stat,wchan:16,comm -t pts/17
    PID    PPID    PGID     SID   TPGID TT       STAT WCHAN            COMMAND
1073367 1073366 1073367 1073367 1073487 pts/17   Ss   do_wait          bash
1073475 1073367 1073475 1073367 1073487 pts/17   S    hrtimer_nanoslee sleep
1073476 1073367 1073475 1073367 1073487 pts/17   S    pipe_wait_readab cat
1073487 1073367 1073487 1073367 1073487 pts/17   S+   hrtimer_nanoslee sleep
1073489 1073367 1073487 1073367 1073487 pts/17   S+   pipe_wait_readab cat
```

This was taken from outside, while an interactive bash in
`/dev/pts/17` ran `sleep 1234 | cat &` and then `sleep 1235 | cat`
in the foreground. The columns:

- **PGID**: the process group. Each pipeline is one group, named
  after its first process: the background job is 1073475, the
  foreground job 1073487.
- **SID**: the session, named after its leader, bash (1073367). All
  the processes of a terminal session have the same SID.
- **TPGID**: the foreground process group of the terminal, the same
  for every process of the terminal: 1073487, the foreground job.
- **STAT**: `S` sleeping, `R` running, `T` stopped, `Z` zombie; `s`
  session leader; `+` member of the foreground group. The quick way to
  see which job owns the terminal is the `+`.
- **WCHAN**: the kernel function in which the process sleeps (see
  32.3).

The same terminal after `^C`, then `cat` (reading the terminal), then
`^Z`:

```console
    PID    PGID   TPGID STAT COMMAND
1073367 1073367 1073367 Ss+  bash
1073475 1073475 1073367 S    sleep
1073476 1073475 1073367 S    cat
1073539 1073539 1073367 T    cat
```

The foreground job was killed by `^C`; the new `cat` is stopped (`T`)
by `^Z`; bash took the terminal back: TPGID is its own PGID, and it
has the `+`. bash's own view:

```console
$ jobs -l
[1]- 1073475 Running                    sleep 1234
     1073476                          | cat &
[2]+ 1073539 Stopped                    cat
```

A surprise awaits when the same commands run in a **script**. A shell
script runs without job control, so a background job stays in the
script's process group, and so does the foreground:

```console
    PID    PPID    PGID     SID   TPGID TT       STAT COMMAND
1072604 1072603 1072604 1072604 1072663 pts/17   Ss   bash
1072663 1072604 1072663 1072604 1072663 pts/17   S+   dbg32.sh
1072666 1072663 1072663 1072604 1072663 pts/17   S+   sleep
1072667 1072663 1072663 1072604 1072663 pts/17   S+   cat
1072685 1072663 1072663 1072604 1072663 pts/17   R+   ps
```

Everything is in group 1072663, the script's, which the interactive
shell made the foreground group: a `^C` would kill the "background"
job too. And there was a second surprise: in the same script, `cat >
/dev/null &` exited immediately. Without job control, the shell
redirects the standard input of a background command to `/dev/null`
(POSIX requires it), precisely because the command could not be
stopped by `SIGTTIN` if it read the terminal: it is in the foreground
group.

### 32.3 `/proc`: descriptors, states, terminals

Linux describes every process in `/proc/PID`. For terminal and pipe
problems, four entries answer most questions.

**`/proc/PID/fd`**: where each descriptor points. For the `cat` of
the script's pipeline:

```console
$ ls -l /proc/1072667/fd
lr-x------ 1 cog cog 64 Nov 22 18:24 0 -> pipe:[20408528]
l-wx------ 1 cog cog 64 Nov 22 18:24 1 -> .../dbg32.out
l-wx------ 1 cog cog 64 Nov 22 18:24 2 -> .../dbg32.out
lr-x------ 1 cog cog 64 Nov 22 18:24 3 -> pipe:[20404194]
l-wx------ 1 cog cog 64 Nov 22 18:24 4 -> pipe:[20404194]
```

(Paths shortened.) Standard input is a pipe, with inode 20408528; the
`sleep` at the other end has a descriptor pointing to the same
`pipe:[20408528]`, which is how you find the two ends of a pipe
without `lsof`. And look at descriptors 3 and 4: both ends of
**another** pipe, inherited by `cat`. Neither `cat` nor the script
opened it: it was inherited from the program that started the script,
through every `fork` and `exec` since, because nobody marked it
close-on-exec (2.7). `cat` neither knows nor cares, but this is a
descriptor leak: if `cat` were the reader of
that pipe, it would never see end of file, because it holds the write
end itself. Section 3.6 showed this deadlock in a hand-made pipeline;
here is a leak of the same kind in the wild. When a pipeline hangs, look at the `fd`
directories of its processes for write ends that should not be there.

**`/proc/PID/fdinfo/N`**: the position and the flags of a descriptor:

```text
pos:	0
flags:	00
mnt_id:	18
ino:	20408528
```

`flags` is octal: `00` is `O_RDONLY` without `O_NONBLOCK` (which would
be `04000`). The question "who set my terminal to non-blocking?" (the
shell that exits when a program crashes, chapter 2) is answered here.

**`/proc/PID/stat`**: one line, with, among others, field 5 the
process group, 6 the session, 7 the controlling terminal as a device
number, 8 the foreground group of that terminal:

```text
pid 1072667 comm (cat) state S pgrp 1072663 session 1072604 tty_nr 34833 tpgid 1072663
```

`tty_nr` 34833 is 136 × 256 + 17: major 136 (the Unix 98 PTY slaves),
minor 17, so `/dev/pts/17`. (The encoding puts the low 8 bits of the
minor number in the low byte, the major in the next 12 bits, and the
high bits of the minor above that.)

**`/proc/PID/wchan`**, or the `wchan` column of `ps`: the kernel
function where the process sleeps. It tells what it is waiting for:

| wchan                  | Waiting for                  |
|------------------------|------------------------------|
| `pipe_wait_readable`   | data in a pipe               |
| `pipe_wait_writable`   | room in a pipe               |
| `wait_woken`           | input from a terminal        |
| `do_wait`              | a child (`waitpid`)          |
| `hrtimer_nanosleep`    | the end of a `sleep`         |
| `do_sys_poll`          | `poll` on descriptors        |
| `do_signal_stop`       | `SIGCONT` (stopped)          |

The first, third, fourth and fifth rows are in the outputs above; the
others are the names in current kernels, but kernel function names
change between versions. For example, a `cat` reading the terminal
showed:

```text
cat 1073539 fd0 -> /dev/pts/17 state=S (sleeping) wchan=wait_woken
```

`wait_woken` is generic (the terminal's `n_tty_read` sleeps with it),
which is why the descriptor matters too. A process "hung" in
`pipe_wait_writable` is a writer whose reader does not read: the
pipe is full (64 KiB by default; `/proc/sys/fs/pipe-max-size` is the
maximum a program can request with `F_SETPIPE_SZ`, 1 MiB here).

`/proc/PID/stack` would show the whole kernel stack, but it is
readable only by root:

```console
$ cat /proc/self/stack
cat: /proc/self/stack: Permission denied
```

### 32.4 Seeing the bytes

Most terminal mysteries are solved by looking at the exact bytes.
Four tools:

- `cat -v` shows control characters as `^X`, DEL as `^?`, bytes above
  127 as `M-` followed by the byte minus 128; `cat -A` also shows tabs
  as `^I` and line ends as `$`:

  ```console
  $ printf 'tab\there\033[1mbold\033[0m é\r\n' | cat -v
  tab	here^[[1mbold^[[0m M-CM-)^M
  $ printf 'tab\there\033[1mbold\033[0m é\r\n' | cat -A
  tab^Ihere^[[1mbold^[[0m M-CM-)^M$
  ```

  `^[` is ESC, `^M` is the carriage return. `M-CM-)` is the two bytes
  of `é`, 0xC3 and 0xA9, unreadable but recognizable.
- `od -c` and `xxd` show every byte, as characters and in hexadecimal:

  ```console
  $ printf '\033[1mB\033[0m é\n' | od -An -c
   033   [   1   m   B 033   [   0   m     303 251  \n
  $ printf '\033[1mB\033[0m é\n' | xxd
  00000000: 1b5b 316d 421b 5b30 6d20 c3a9 0a         .[1mB.[0m ...
  ```

- `showkey -a` (from the kbd package) prints what each key sends, in
  decimal, octal and hexadecimal. It puts the terminal in raw mode,
  and `^D` ends it:

  ```console
  $ showkey -a
  Press any keys - Ctrl-D will terminate this program
  a 	 97 0141 0x61
  ^[[A 	 27 0033 0x1b
   	 91 0133 0x5b
   	 65 0101 0x41
  ^[OP 	 27 0033 0x1b
   	 79 0117 0x4f
   	 80 0120 0x50
  ^[x 	 27 0033 0x1b
   	120 0170 0x78
  ^A 	  1 0001 0x01
  ^? 	127 0177 0x7f
  ^[[1~ 	 27 0033 0x1b
   	 91 0133 0x5b
   	 49 0061 0x31
   	126 0176 0x7e
  é 	195 0303 0xc3
   	169 0251 0xa9
  ^D 	  4 0004 0x04
  ```

  The keys were `a`, Up, F1, Alt-x, Ctrl-A, Backspace, Home, `é`, in
  tmux. Up is `ESC [ A` (normal cursor mode: showkey does not send
  `smkx`), F1 is `ESC O P`, Alt-x is ESC followed by `x` (the "meta
  sends escape" convention), Backspace is DEL, Home is `ESC [ 1 ~`
  (tmux's choice; xterm sends `ESC [ H`), and `é` is two bytes. If a
  key does nothing in a program, start here: does it send anything,
  and what?
- the **`^V` prefix** in a shell or in vim's insert mode: the next
  key is inserted literally, so `^V` then Up shows `^[[A`. It is the
  `lnext` character of the line discipline, and readline honors it
  too.

To see what a **program writes**, redirect it to a file and look at
the file with `cat -v`. Many programs change their behavior when the
output is not a terminal, though (no colors, no cursor movement):
`script -q -c CMD /dev/null | cat -v` runs it on a PTY and shows the
result, or `ttylog`.

### 32.5 `ttylog`: logging both directions

`script` records the output; `ptyrec -i` records both directions but
in JSON. For debugging, a readable log of everything that crosses the
terminal, with timestamps, is more useful, and so is knowing what the
terminal **modes** were at each moment: whether the program was in
canonical mode when the key arrived explains most "lost key" bugs.
The master side of a PTY can see both: `tcgetattr` on the master
returns the settings of the PTY (Linux shares one `termios` between
the two sides), and `tcgetpgrp` on the master returns the foreground
process group (30.4).

`ttylog` is a `ptyscript` that logs:

- `<` lines: output of the program, escaped, cut at each newline;
- `>` lines: input, what was typed;
- `=` lines: changes of the modes (the flags that matter for input:
  `icanon`, `echo`, `isig`, `icrnl`, `opost`, and `VMIN`/`VTIME`), of
  the foreground process group, with the name of its leader, and of
  the window size.

```c
// file: c/ttylog.c
/*
 * ttylog: run a command on a PTY, like ptyscript, and log everything
 * that crosses the terminal, readably, with timestamps:
 *   <  output of the program        >  input (keys)
 *   =  changes of the terminal mode and of the foreground job,
 *      seen from the master side (tcgetattr and tcgetpgrp work there)
 * Usage: ttylog LOGFILE [cmd args...]
 */
#define _GNU_SOURCE
#include "ptyopen.h"
#include <fcntl.h>
#include <poll.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/wait.h>
#include <termios.h>
#include <time.h>
#include <unistd.h>

static FILE *lg;
static struct timespec t0;
static struct termios saved;
static int raw_on;

static double elapsed(void)
{
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return (double)(t.tv_sec - t0.tv_sec) + (t.tv_nsec - t0.tv_nsec) / 1e9;
}

/* Log a chunk of bytes as a quoted string: ESC is \e, other controls
 * are \r \n \t or ^X, bytes >= 0x80 are copied (UTF-8 stays readable).
 * A new log line starts after each \n of the data. */
static void log_bytes(char dir, const unsigned char *p, size_t n)
{
    fprintf(lg, "%8.3f %c \"", elapsed(), dir);
    for (size_t i = 0; i < n; i++) {
        unsigned char c = p[i];
        switch (c) {
        case 0x1b: fputs("\\e", lg); break;
        case '\r': fputs("\\r", lg); break;
        case '\t': fputs("\\t", lg); break;
        case '"':  fputs("\\\"", lg); break;
        case '\\': fputs("\\\\", lg); break;
        case '\n':
            fputs("\\n\"", lg);
            if (i + 1 < n) fprintf(lg, "\n%8s %c \"", "", dir);
            else { fputc('\n', lg); return; }
            break;
        default:
            if (c < 0x20) fprintf(lg, "^%c", c ^ 0x40);
            else if (c == 0x7f) fputs("^?", lg);
            else fputc(c, lg);
        }
    }
    fputs("\"\n", lg);
}

/* Describe the flags that matter for a program's input. */
static void mode_string(const struct termios *t, char *out, size_t n)
{
    snprintf(out, n, "%cicanon %cecho %cisig %cicrnl %copost min=%d time=%d",
             t->c_lflag & ICANON ? '+' : '-', t->c_lflag & ECHO ? '+' : '-',
             t->c_lflag & ISIG ? '+' : '-', t->c_iflag & ICRNL ? '+' : '-',
             t->c_oflag & OPOST ? '+' : '-', t->c_cc[VMIN], t->c_cc[VTIME]);
}

static void comm_of(pid_t pid, char *out, size_t n)
{
    char path[64];
    snprintf(path, sizeof path, "/proc/%d/comm", (int)pid);
    FILE *f = fopen(path, "r");
    out[0] = 0;
    if (f) {
        if (fgets(out, (int)n, f)) out[strcspn(out, "\n")] = 0;
        fclose(f);
    }
}

/* Log the mode and the foreground job when they change. */
static void check_state(int master)
{
    static char last_mode[128];
    static pid_t last_fg = -1;
    struct termios t;
    char mode[128];
    if (tcgetattr(master, &t) == 0) {
        mode_string(&t, mode, sizeof mode);
        if (strcmp(mode, last_mode) != 0) {
            fprintf(lg, "%8.3f = mode %s\n", elapsed(), mode);
            strcpy(last_mode, mode);
        }
    }
    pid_t fg = tcgetpgrp(master);
    if (fg > 0 && fg != last_fg) {
        char comm[64];
        comm_of(fg, comm, sizeof comm);
        fprintf(lg, "%8.3f = foreground %d (%s)\n", elapsed(), (int)fg, comm);
        last_fg = fg;
    }
}

static void restore(void)
{
    if (raw_on) tcsetattr(STDIN_FILENO, TCSAFLUSH, &saved);
}

static volatile sig_atomic_t winch;
static void on_winch(int sig) { (void)sig; winch = 1; }

int main(int argc, char **argv)
{
    if (argc < 2) {
        fprintf(stderr, "usage: %s LOGFILE [cmd args...]\n", argv[0]);
        return 2;
    }
    lg = fopen(argv[1], "we");                 /* e: O_CLOEXEC */
    if (!lg) { perror(argv[1]); return 1; }
    setvbuf(lg, NULL, _IOLBF, 0);
    char *shell = getenv("SHELL");
    char *dflt[] = { shell ? shell : "/bin/sh", NULL };
    char **cmd = argc > 2 ? &argv[2] : dflt;

    int is_tty = isatty(STDIN_FILENO);
    struct winsize ws = { .ws_row = 24, .ws_col = 80 };
    if (is_tty) {
        tcgetattr(STDIN_FILENO, &saved);
        ioctl(STDIN_FILENO, TIOCGWINSZ, &ws);
    }
    clock_gettime(CLOCK_MONOTONIC, &t0);
    fprintf(lg, "# ttylog: %s, %dx%d\n", cmd[0], ws.ws_col, ws.ws_row);

    /* SIGWINCH without SA_RESTART: poll returns EINTR, we look at the
     * flag. (A signal arriving just before poll would wait for the next
     * event or the 100 ms timeout: acceptable here.) */
    struct sigaction sa = { .sa_handler = on_winch };
    sigemptyset(&sa.sa_mask);
    sigaction(SIGWINCH, &sa, NULL);

    int master;
    pid_t child = pty_spawn(cmd, is_tty ? &saved : NULL, &ws, &master);
    if (child == -1) { perror("pty_spawn"); return 1; }
    if (is_tty) {
        struct termios raw = saved;
        cfmakeraw(&raw);
        tcsetattr(STDIN_FILENO, TCSAFLUSH, &raw);
        raw_on = 1;
        atexit(restore);
    }

    struct pollfd pf[2] = {
        { .fd = STDIN_FILENO, .events = POLLIN },
        { .fd = master, .events = POLLIN },
    };
    unsigned char buf[4096];
    for (;;) {
        check_state(master);
        int r = poll(pf, 2, 100);        /* 100 ms: catch mode changes */
        if (winch) {
            winch = 0;
            if (ioctl(STDIN_FILENO, TIOCGWINSZ, &ws) == 0) {
                ioctl(master, TIOCSWINSZ, &ws);
                fprintf(lg, "%8.3f = resize %dx%d\n", elapsed(),
                        ws.ws_col, ws.ws_row);
            }
        }
        if (r <= 0) continue;            /* timeout or EINTR */
        if (pf[0].revents & (POLLIN | POLLHUP)) {
            ssize_t n = read(STDIN_FILENO, buf, sizeof buf);
            if (n > 0) {
                log_bytes('>', buf, (size_t)n);
                if (write(master, buf, (size_t)n) != n) perror("write");
            } else {
                pf[0].fd = -1;           /* end of input: stop reading */
            }
        }
        if (pf[1].revents & (POLLIN | POLLHUP | POLLERR)) {
            ssize_t n = read(master, buf, sizeof buf);
            if (n <= 0) break;           /* EIO: the slave is closed */
            log_bytes('<', buf, (size_t)n);
            for (ssize_t off = 0, w; off < n; off += w)
                if ((w = write(STDOUT_FILENO, buf + off, (size_t)(n - off))) <= 0)
                    break;
        }
    }
    int status;
    waitpid(child, &status, 0);
    restore();
    raw_on = 0;
    fprintf(lg, "%8.3f # exit status %d\n", elapsed(),
            WIFEXITED(status) ? WEXITSTATUS(status) : 128 + WTERMSIG(status));
    return WIFEXITED(status) ? WEXITSTATUS(status) : 128 + WTERMSIG(status);
}
```

The modes are checked before each `poll`, and `poll` waits at most
100 ms, so a change of mode is seen within 100 ms, or as soon as a
byte crosses the terminal. That is not exact: a program can change
the mode and change it back between two checks, and the log would
not show it. Exact tracing needs `strace -e ioctl` (32.7).

A log of a short session with `sh` (bash in POSIX mode), recorded with
the tmux driver: `stty -a | head -2`, then `cat` with a line of input
and `^C`, then `vim -u NONE -c q` (vim starts and quits at once), then
`exit 3`:

```text
# ttylog: sh, 80x20
   0.000 = mode +icanon +echo +isig +icrnl +opost min=1 time=0
   0.001 < "\e[?2004hsh-5.3$ "
   0.001 = mode -icanon -echo +isig -icrnl +opost min=1 time=0
   0.001 = foreground 1063575 (sh)
   1.205 > "stty -a | head -2"
   1.205 < "stty -a | head -2"
   1.811 > "\r"
   1.811 < "\r\n"
         < "\e[?2004l\r"
   1.811 = mode +icanon +echo +isig +icrnl +opost min=1 time=0
   1.816 < "speed 38400 baud; rows 20; columns 80; line = 0;\r\n"
         < "intr = ^C; quit = ^\; erase = ^?; kill = ^U; eof = ^D; eol = <undef>;\r\n"
   1.816 = foreground 1063659 ()
   1.816 < "\e[?2004hsh-5.3$ "
   1.816 = mode -icanon -echo +isig -icrnl +opost min=1 time=0
   1.816 = foreground 1063575 (sh)
   2.416 > "cat"
   2.416 < "cat"
   3.021 > "\r"
   3.021 < "\r\n"
         < "\e[?2004l\r"
   3.021 = mode +icanon +echo +isig +icrnl +opost min=1 time=0
   3.121 = foreground 1063731 (cat)
   3.625 > "héllo"
   3.625 < "héllo"
   4.230 > "\r"
   4.230 < "\r\n"
   4.230 < "héllo\r\n"
   4.836 > "^C"
   4.836 < "^C"
   4.836 < "\r\n"
   4.836 = foreground 1063575 (sh)
   4.836 < "\e[?2004hsh-5.3$ "
   4.836 = mode -icanon -echo +isig -icrnl +opost min=1 time=0
   5.441 > "vim -u NONE -c q"
   5.441 < "vim -u NONE -c q"
   6.047 > "\r"
   6.047 < "\r\n"
         < "\e[?2004l\r"
   6.047 = mode +icanon +echo +isig +icrnl +opost min=1 time=0
   6.079 < "\e[?1049h\e[?1h\e=\e[?2004h"
   6.079 = mode -icanon -echo -isig -icrnl +opost min=1 time=0
   6.079 = foreground 1063917 (vim)
   6.079 < "\e[1;20r\e[27m\e[24m\e[23m\e[0m\e[H\e[J\e[20;1H\e[?2004l"
   6.079 = mode +icanon +echo +isig +icrnl +opost min=1 time=0
   6.079 < "\e[?2004l\e[?1l\e>\e[?1049l"
   6.079 < "\e[?2004hsh-5.3$ "
   6.079 = mode -icanon -echo +isig -icrnl +opost min=1 time=0
   6.079 = foreground 1063575 (sh)
   6.652 > "exit 3"
   6.652 < "exit 3"
   7.257 > "\r"
   7.257 < "\r\n"
         < "\e[?2004l\rexit\r\n"
   7.257 = mode +icanon +echo +isig +icrnl +opost min=1 time=0
   7.258 # exit status 3
```

What it shows:

- **readline's modes.** While bash waits for a command, the PTY is in
  `-icanon -echo +isig -icrnl`: readline reads keys one by one and
  echoes them itself, but leaves `isig` on, so `^C` is still a signal.
  `-icrnl` lets it see Enter as `\r`. When you press Enter, readline
  restores the original modes (`+icanon +echo +icrnl`) **before**
  running the command: the command starts in the cooked mode it
  expects. That is the rule of 4.9 (restore what you changed
  before giving the terminal to someone else), seen from outside.
- **The echo of the typed line comes from readline**, character by
  character, at the same time as the input (`> "cat"` and `< "cat"`
  at 2.416). The echo of `héllo`, while `cat` runs, comes from the
  **line discipline**, since `echo` is on and the terminal is in
  canonical mode; `cat` receives the line only at Enter, at 4.230, and
  writes it back: `< "héllo\r\n"`.
- **`^C`** is a byte, `> "^C"` (0x03), turned by the line discipline
  into `SIGINT` for the foreground group (cat) and echoed as `^C`
  (`echoctl`). The foreground goes back to `sh` at the same moment.
- **The foreground group of the pipeline**: `foreground 1063659 ()`.
  The group of `stty -a | head -2` is named after `stty`, which had
  already exited when `ttylog` read `/proc/1063659/comm`: a process
  group outlives its leader as long as one member is alive. (`head`
  was still running.)
- **The 100 ms delay**: the mode changed to canonical at 3.021, but the
  new foreground group (`cat`) appears at 3.121, one `poll` timeout
  later, because nothing crossed the terminal in between.
- **vim** switches to `-isig` (it handles `^C` and `^Z` itself), turns
  on the alternate screen (`?1049h`), application cursor keys (`?1h`)
  and keypad (`ESC =`): together they are `smcup` and `smkx` of its
  terminfo entry. It sets the scroll region to the whole screen
  (`ESC [1;20r`), clears, quits (`-c q`) and undoes everything in
  reverse order.
- **The exit status**, 3, passed through `waitpid`.

### 32.6 `TERM` and terminfo

Many display bugs are a `TERM` that does not match the terminal. The
program reads the terminfo entry named by `TERM` and sends the
sequences it lists; if the entry describes another terminal, the
sequences are wrong.

- `echo $TERM` and `infocmp` show the entry in use; `infocmp -1`
  prints one capability per line, easy to `grep`:

  ```console
  $ echo $TERM
  tmux-256color
  $ infocmp -1 | grep -E 'kcuu1|smkx|rmkx|cup=|smcup|rmcup|colors|kbs|setaf'
  	colors#0x100,
  	cup=\E[%i%p1%d;%p2%dH,
  	kbs=^?,
  	kcuu1=\EOA,
  	rmcup=\E[?1049l,
  	rmkx=\E[?1l\E>,
  	setaf=\E[%?%p1%{8}%<%t3%p1%d%e%p1%{16}%<%t9%p1%{8}%-%d%e38;5;%p1%d%;m,
  	smcup=\E[?1049h,
  	smkx=\E[?1h\E=,
  ```

  `kcuu1=\EOA`: in keypad mode (after `smkx`), Up sends `ESC O A`;
  `kbs=^?`: Backspace sends DEL; `colors#0x100`: 256 colors. The
  `setaf` string is a small program in terminfo's stack language: for
  colors below 8 it emits `3N`, below 16 `9(N-8)`, otherwise `38;5;N`
  (Appendix B).
- `tput` runs these programs for you:

  ```console
  $ tput cols; tput lines; tput colors
  100
  50
  256
  $ tput cup 5 10 | cat -v
  ^[[6;11H
  $ tput setaf 1 | cat -v
  ^[[31m
  $ tput smcup | cat -v
  ^[[?1049h
  ```

  `cup 5 10` becomes `ESC [6;11H`: terminfo counts from 0, the
  terminal from 1 (the `%i` in `cup`).
- With a dumb or unknown terminal, `tput` fails, and the exit status
  tells why:

  ```console
  $ TERM=dumb tput cup 5 10; echo "status $?"
  status 1
  $ TERM=nosuch tput cols; echo "status $?"
  tput: unknown terminal "nosuch"
  status 3
  ```

  Status 1: the capability is absent (a dumb terminal cannot move the
  cursor); status 3: no entry for that `TERM`. Over `ssh`, the second
  case is frequent: your local terminal is, say, `xterm-kitty` or
  `alacritty`, the remote machine has no entry for it, and programs
  fall back to something poor or refuse to start. Copy the entry
  (`infocmp -x | ssh host tic -x -`) or set `TERM=xterm-256color` for
  that connection.
- `toe -a` lists all the entries known on the machine; 1863 here.

### 32.7 Tracing system calls

`strace` shows the system calls of a process; it is the most powerful
tool for terminal and pipe problems. It is not installed on the
machine of this tutorial, so the commands below were **not run here**;
they are given for reference, with the options that matter:

```sh
# every ioctl on terminals (modes, size, process groups), decoded
strace -f -e trace=ioctl -o trace.txt vim file.txt

# reads and writes, with the data, 200 bytes at most per call
strace -f -e trace=read,write -s 200 -o trace.txt prog

# attach to a running process that seems hung: what is it doing?
strace -p PID
```

With `-e trace=ioctl`, strace decodes `TCGETS`, `TCSETSW`,
`TIOCGWINSZ`, `TIOCSPGRP` and so on, so you see exactly when a
program changes the terminal modes and to what: the exact version of
the `=` lines of `ttylog`. `-f` follows children, which matters for
shells and for anything that forks. A process blocked in `read(0,` is
waiting for input; in `write(1,` for the reader of its output; in
`wait4(` for a child; in `ioctl(0, TCSETSW` for the output to drain.

`ltrace` traces library calls (`tcsetattr`, `tgetent`, `setupterm`).
`lsof -p PID` lists open files, and `lsof /dev/pts/17` the processes
using a terminal; without it, `/proc/*/fd` does the same:

```sh
# which processes have /dev/pts/17 open?
for p in /proc/[0-9]*; do
  ls -l "$p/fd" 2>/dev/null | grep -q '/dev/pts/17$' && echo "${p#/proc/}"
done
```

`fuser /dev/pts/17` (psmisc) does the same, and `fuser -k` kills
them, which is the brutal way to free a stuck terminal.

### 32.8 Common symptoms

Appendix F has a longer list; these are the classics.

- **Nothing is echoed, Enter does nothing (or makes "staircase"
  output).** A program left the terminal in raw mode or with `-echo`.
  See 32.9.
- **The terminal is frozen.** Try `^Q`: `^S` (`ixon`) stops the output
  until `^Q`. Many people type `^S` by accident (it is "save" in other
  editors).
- **Backspace prints `^?` or `^H`.** The `erase` character
  (`stty -a`) does not match what the key sends (`showkey -a`). Fix
  with `stty erase '^?'` (or `'^H'`), or in the terminal emulator's
  settings.
- **Arrow keys print `^[[A` or `^[OA`.** The program reads the
  terminal in canonical mode and does not decode keys: a plain `read`
  or a program without readline. Use `rlwrap PROG` to add line
  editing to it.
- **Full-screen programs draw garbage, lines wrap wrong.** `TERM` does
  not match the terminal (32.6), or the size is wrong: compare `stty
  size` with the real window. A size of `0 0` happens on PTYs created
  without a size (a `docker exec -t` that does not pass it, a
  hand-made `ptyscript` that forgets `TIOCSWINSZ`); `stty rows 40 cols
  120` fixes it for the session.
- **A background job stops with "Stopped (tty input)"** or **"tty
  output"**: it tried to read the terminal (`SIGTTIN`) or to write
  with `tostop` set, or to change the modes (`SIGTTOU`, chapter 5).
  Bring it to the foreground with `fg`.
- **A pipeline never ends.** A write end of a pipe is still open
  somewhere: look at `/proc/*/fd` for `pipe:[N]` with the same `N`
  (32.3).
- **A program waits forever at start.** It sent a query (cursor
  position `ESC [6n`, device attributes, background color `ESC ]11;?`)
  and the terminal does not answer: a multiplexer, a serial console, a
  terminal emulator that does not implement it. Press a key, or run
  it with `TERM=dumb`.
- **Output appears all at once at the end.** The program buffers its
  output because standard output is a pipe (2.13): `stdbuf -oL`,
  `unbuffer` (from Expect), `script -q -c`, or the language's flush.

### 32.9 Recovering a broken terminal

When a program dies in raw mode, the shell's prompt comes back but the
terminal is useless: no echo, Enter sends `\r` that nobody turns into
`\n` (with `-icrnl`), output goes in a staircase (with `-opost`). In
order of strength:

1. **`stty sane`**, typed blind, ended with `^J` (line feed, which
   works when Enter does not: with `-icrnl`, the shell gets `\r` and
   waits for the end of the line). `stty sane` resets the modes to
   reasonable defaults, but keeps the special characters and the
   size. In bash with readline, Enter usually works anyway, because
   readline sets its own modes for the line: if the prompt reacts,
   just type the command.
2. **`tput rmcup; tput cnorm; tput sgr0`**, or the raw sequences
   `printf '\e[?1049l\e[?25h\e[0m'`: leave the alternate screen, show
   the cursor, reset the colors. A program that crashed while drawing
   leaves these on, and the modes are not the problem.
3. **`reset`** (from ncurses): `stty sane`, plus the terminal's
   initialization strings, plus a full reset of the emulator (RIS,
   `ESC c`), which also clears mouse modes, the keypad mode,
   character sets (the "my terminal prints line-drawing characters
   instead of letters" problem after `cat`ing a binary file: a
   `ESC ( 0` or a `^N` was in it), the scroll region, and the screen.
   It is slow on purpose (it waits a second); `tput reset` is the same.
4. Close the window. With `tmux`, `tmux respawn-pane -k` restarts the
   program of a pane.

To make your own programs safe: restore in every exit path (29.4),
catch `SIGTERM`, `SIGHUP`, `SIGINT` (if `isig` is off you will not get
it anyway) and restore before dying, and do not restore what you did
not change (save the original modes, do not "reset to sane").

## 33. Comparing the four languages

This last chapter puts the four languages side by side, for the kind
of programs this tutorial is about: programs that talk to terminals,
start processes, and move bytes between descriptors. It is opinionated;
the facts behind the opinions are in the chapters cited.

### 33.1 Access to the system

| Need          | C      | Raku       | Rust      | Go          |
|---------------|--------|------------|-----------|-------------|
| termios       | native | module     | nix       | x/term, x/sys |
| PTY           | native | NativeCall | nix       | creack/pty  |
| fork          | yes    | no         | yes       | no          |
| poll          | native | NativeCall | nix       | runtime     |
| signals       | manual | Supply     | crates    | channel     |
| ioctl         | native | NativeCall | nix       | x/sys/unix  |

- **C** has everything, directly, and nothing else: no strings, no
  error handling, no event loop. Every system call of this tutorial
  is a C function; the manual pages are written for C.
- **Rust** reaches everything through `libc` (raw bindings, `unsafe`)
  and `nix` (safe wrappers, `Result`s, owned descriptors). With
  `OwnedFd` and `BorrowedFd`, the type system tracks who closes a
  descriptor, which removes a class of bugs (double close, leak) that
  C programs have. `fork` is possible but `unsafe`, and the
  `pre_exec` closure is the practical way to run code in the child.
- **Go** has a portable layer (`os`, `os/exec`, `os/signal`) and a
  low-level one (`syscall`, frozen, and `golang.org/x/sys/unix`,
  maintained). The runtime owns threads, signals and `fork`: you
  describe what you want (`SysProcAttr`) instead of doing it. Mostly
  a good trade, with surprises when a library's descriptor is not in
  the runtime's poller (27.1).
- **Raku** has the most comfortable high level (`run`, `Proc::Async`,
  supplies, `react`) and the least direct low level: what is not in
  the language goes through NativeCall, with C signatures written by
  hand (`Tty.rakumod`). No `fork`; process creation goes through
  libuv in MoarVM, and the PTY session setup needs a helper (29.2).

### 33.2 Concurrency models

The central problem of this tutorial's programs is waiting for several
things at once: keyboard, child output, signals, child exit, timers.

- **C**: `poll` (or `epoll`, `select`), plus the self-pipe trick or
  `signalfd` for signals. Explicit, single-threaded, predictable,
  verbose. Each new source is a new descriptor in the array.
- **Rust**: the same `poll`, through nix, with signal-hook to turn
  signals into a readable descriptor. Or async Rust (Tokio), which
  this tutorial did not use: Tokio has `AsyncFd` for any descriptor,
  `tokio::process` with `kill_on_drop`, and `tokio::signal`, at the
  cost of a large dependency and of async's complexity. For a relay,
  `poll` is enough.
- **Go**: goroutines and channels, with `select` as the "wait for any
  of these". Each blocking read is a goroutine; the main loop selects
  on channels. The code is short and clear (31.3), and the problem is
  stopping a goroutine blocked in a read, which needs the descriptor
  to be in the netpoller (non-blocking) or a trick like
  `cancelreader`.
- **Raku**: supplies and `react`/`whenever`, which is the closest of
  the four to how one thinks about the problem ("whenever a key
  arrives, ..., whenever the child exits, ..."). The `react` block
  ends when you say `done` or when all supplies are done. The
  difficulty is in the corners: the order of events, and the
  interaction between supplies backed by threads and code that
  expects to run on one thread.

### 33.3 Errors

- **C**: return values and `errno`. Every call must be checked, and
  `EINTR` and `EAGAIN` handled where they can happen. Forgetting is
  silent.
- **Rust**: `Result` and `?`; the compiler refuses to ignore an error
  silently (an unused `Result` is a warning). `Errno` from nix is an
  enum, so `match` on `EIO` or `EINTR` is natural.
- **Go**: `error` values, checked with `if err != nil`; `errors.Is`
  for `syscall.EIO`. Ignoring an error is easy (`_`), and `go vet` and
  linters catch some cases.
- **Raku**: exceptions (`X::...` classes), and failures (`Failure`),
  lazy exceptions that explode when used. Asynchronous errors arrive
  through `quit` blocks of supplies or broken promises, which is easy
  to forget: an error in a `whenever` can end the whole `react`.

### 33.4 Shipping a program

- **C**: one small binary, dynamically linked against the C library;
  portable source if you stick to POSIX, with `#ifdef`s for the
  differences (`openpty` in `<pty.h>` on Linux, `<util.h>` on macOS
  and the BSDs, `<libutil.h>` on FreeBSD).
- **Rust**: one binary, linked dynamically to the C library by
  default, or fully static with the `x86_64-unknown-linux-musl`
  target. `cargo build --release` and copy. Cross-compilation needs a
  linker for the target (`cross` or `cargo-zigbuild` make it easy).
- **Go**: one static binary (with `CGO_ENABLED=0`, the default when
  cross-compiling), and trivial cross-compilation:
  `GOOS=darwin GOARCH=arm64 go build`. The best of the four for
  distributing tools, which is why so many terminal tools are in Go.
- **Raku**: the user needs Rakudo and the modules (`zef install`).
  Rakudo Star bundles the compiler and a set of modules, which helps.
  No standalone binary.

### 33.5 Terminal UI libraries

| Need          | C        | Raku          | Rust      | Go          |
|---------------|----------|---------------|-----------|-------------|
| Line editing  | readline | Linenoise     | rustyline | many        |
| Full screen   | ncurses  | Terminal::Print | Ratatui | Bubble Tea  |
| Styling       | manual   | Terminal::ANSIColor | crossterm | Lip Gloss |
| Widgets       | dialog   | few           | many      | Bubbles     |

(The "many" for Go line editing: `charm.land/bubbles` has a text
input, and `peterh/liner`, `chzyer/readline` and `x/term`'s small
`Terminal` exist.)

- **C** has the reference libraries (ncurses, readline), stable and
  everywhere, with old APIs.
- **Rust** has the best-designed modern stack: crossterm for the
  terminal, Ratatui for immediate-mode layouts and widgets, with a
  large ecosystem around them.
- **Go** has the Charm stack (Bubble Tea, Lip Gloss, Bubbles, Huh,
  Wish for SSH apps), the most polished for building a TUI quickly,
  with the Elm architecture (chapter 28), plus tcell and tview.
- **Raku** has modules for the basics (`Terminal::ANSIColor`,
  `Terminal::Print`, `Linenoise`, `Terminal::LineEditor`), fewer
  and less maintained; for serious TUIs, NativeCall to ncurses is an
  option.

### 33.6 Which one?

- **To learn how terminals work**, write C, at least once: no layer
  hides the system calls, and every other library is a wrapper around
  what you wrote.
- **For a robust low-level tool** (a PTY relay, a multiplexer, a
  terminal emulator), Rust: control as precise as C's, with owned
  descriptors and `Result`s, and no runtime that owns your threads.
  Alacritty, WezTerm and Zellij are in Rust.
- **For a TUI application or a tool to distribute**, Go: fast to
  write, static binaries, the Charm stack, and goroutines that fit
  the "many things at once" problem, with the PTY caveats of 27.1.
  Many popular TUIs (lazygit, k9s, glow, gum) are in Go.
- **For scripting and glue**, Raku: `run` and `Proc::Async` with
  supplies make pipelines and process supervision concise, the regex
  engine and grammars are ideal for parsing program output (chapter
  30), and Unicode handling is the most correct of the four. Its
  start-up time (29.5) and its thin low-level layer make it a weaker
  choice for interactive low-level tools.

And whatever the language: the kernel is the same. A PTY is a pair of
descriptors and a line discipline between them; a pipe is a buffer
with two ends; a job is a process group; a terminal is a program that
reads bytes and draws cells. Everything else is libraries.

---

# Appendices

---

## Appendix A. termios reference

This appendix lists the fields of `struct termios` on Linux, with the
values of the constants (octal, as in `<bits/termios-*.h>`), what
each flag does, and its usual setting. The values were printed by a
small C program on x86-64 Linux with glibc; other architectures (and
other systems) use different values, which is one reason never to
hard-code them. `stty` names are the flag names in lower case, with
`-` to turn a flag off.

```c
struct termios {
    tcflag_t c_iflag;    /* input modes */
    tcflag_t c_oflag;    /* output modes */
    tcflag_t c_cflag;    /* control modes (hardware) */
    tcflag_t c_lflag;    /* local modes (line discipline) */
    cc_t     c_line;     /* line discipline number (Linux) */
    cc_t     c_cc[NCCS]; /* special characters; NCCS is 32 */
    speed_t  c_ispeed;   /* input speed (glibc) */
    speed_t  c_ospeed;   /* output speed (glibc) */
};
```

Use only the functions to read and change it: `tcgetattr`,
`tcsetattr`, `cfmakeraw`, `cfsetispeed`, `cfsetospeed`, `cfgetispeed`,
`cfgetospeed`. Rust's nix has the same names, as `Termios` with typed
flag sets (`InputFlags`, `OutputFlags`, `ControlFlags`, `LocalFlags`)
and `SpecialCharacterIndices`; Go's `golang.org/x/sys/unix` has
`unix.Termios` with fields `Iflag`, `Oflag`, `Cflag`, `Lflag`, `Cc`,
and the constants under the same C names; Raku's `Term::termios` has
methods `set_iflags`, `unset_lflags` and so on, taking the names as
strings.

### A.1 `c_iflag`: input modes

These act on bytes coming from the terminal (the keyboard side),
before the line discipline sees them as characters.

| Flag    | Octal   | Usual |
|---------|---------|-------|
| IGNBRK  | 0000001 | off   |
| BRKINT  | 0000002 | on    |
| IGNPAR  | 0000004 | off   |
| PARMRK  | 0000010 | off   |
| INPCK   | 0000020 | off   |
| ISTRIP  | 0000040 | off   |
| INLCR   | 0000100 | off   |
| IGNCR   | 0000200 | off   |
| ICRNL   | 0000400 | on    |
| IUCLC   | 0001000 | off   |
| IXON    | 0002000 | on    |
| IXANY   | 0004000 | off   |
| IXOFF   | 0010000 | off   |
| IMAXBEL | 0020000 | on    |
| IUTF8   | 0040000 | on    |

- **IGNBRK**: ignore a BREAK condition on the line (a serial line held
  at zero for longer than a character). PTYs have no real BREAK.
- **BRKINT**: if BREAK is not ignored, flush the queues and send
  `SIGINT` to the foreground group. Otherwise it is read as a NUL byte
  (or `\377 \0 \0` with PARMRK).
- **IGNPAR**, **PARMRK**, **INPCK**: parity error handling, for serial
  lines with parity: ignore bad characters, mark them with `\377 \0`,
  enable the check. Irrelevant on PTYs.
- **ISTRIP**: clear the eighth bit of every byte. It destroys UTF-8;
  it is a relic of 7-bit lines. `cfmakeraw` turns it off.
- **INLCR**: translate NL (`\n`) to CR on input. Almost never used.
- **IGNCR**: ignore CR on input. Almost never used.
- **ICRNL**: translate CR to NL on input. The Enter key sends `\r`;
  with ICRNL, programs read `\n`. In raw mode it is off, and the
  program sees `\r` (chapter 11).
- **IUCLC**: map upper case to lower case on input, for terminals
  that had only upper case. Linux-specific, not in POSIX.
- **IXON**: XON/XOFF flow control on output: `^S` (VSTOP) stops the
  output, `^Q` (VSTART) restarts it. The cause of "frozen" terminals
  (32.8). Turned off by `cfmakeraw`, and by most editors.
- **IXANY**: any character restarts stopped output, not only `^Q`.
- **IXOFF**: XON/XOFF flow control on input: the system sends `^S`
  to the terminal when its input buffer is nearly full. For serial
  lines.
- **IMAXBEL**: ring the bell when the input buffer is full (4096
  characters per line in canonical mode on Linux), instead of
  silently discarding. Linux ignores the flag and always rings; it is
  kept for compatibility.
- **IUTF8**: the input is UTF-8. It affects only canonical-mode
  editing: with it, the ERASE character erases a whole multibyte
  character, not just its last byte. Terminal emulators set it when
  the locale is UTF-8. Linux-specific (since 2.6.4).

### A.2 `c_oflag`: output modes

These act on bytes written to the terminal by programs.

| Flag   | Octal   | Usual |
|--------|---------|-------|
| OPOST  | 0000001 | on    |
| OLCUC  | 0000002 | off   |
| ONLCR  | 0000004 | on    |
| OCRNL  | 0000010 | off   |
| ONOCR  | 0000020 | off   |
| ONLRET | 0000040 | off   |
| OFILL  | 0000100 | off   |
| OFDEL  | 0000200 | off   |
| TABDLY | 0014000 | TAB0  |

- **OPOST**: enable output processing. When it is off, all the other
  output flags are ignored: bytes go out unchanged. `cfmakeraw` turns
  it off, so a raw-mode program must write `\r\n` itself, or the
  output goes down in a staircase.
- **OLCUC**: map lower case to upper case (Linux-specific).
- **ONLCR**: map NL to CR NL on output. The reason a program can
  write `\n` and the cursor goes to the start of the next line; the
  reason the output of a program on a PTY contains `\r\n` (chapter 6).
- **OCRNL**: map CR to NL. **ONOCR**: do not output CR in column 0.
  **ONLRET**: NL also does a CR (for terminals where it does).
- **OFILL**, **OFDEL**: send fill characters instead of timed
  delays, and use DEL as fill character: for terminals that needed
  time after a carriage return.
- **TABDLY**: tab delay; the value TAB3 (also called XTABS) expands
  tabs into spaces on output. Linux also has NLDLY, CRDLY, BSDLY,
  VTDLY, FFDLY for the other delays (`nl0 cr0 tab0 bs0 vt0 ff0` in
  `stty -a`), all useless on modern terminals.

### A.3 `c_cflag`: control modes

These describe the hardware line. On a PTY, the line discipline
accepts them and ignores most.

| Flag    | Octal        | Usual  |
|---------|--------------|--------|
| CSIZE   | 0000060      | (mask) |
| CS8     | 0000060      | set    |
| CSTOPB  | 0000100      | off    |
| CREAD   | 0000200      | on     |
| PARENB  | 0000400      | off    |
| PARODD  | 0001000      | off    |
| HUPCL   | 0002000      | varies |
| CLOCAL  | 0004000      | varies |
| CRTSCTS | 020000000000 | off    |

- **CSIZE**: the mask for the character size, one of CS5, CS6, CS7,
  CS8. Always CS8 today.
- **CSTOPB**: two stop bits instead of one.
- **CREAD**: enable the receiver. Without it no input is received.
- **PARENB**, **PARODD**: generate and check parity, odd instead of
  even.
- **HUPCL**: hang up (lower the modem control lines) when the last
  process closes the device. On a serial line connected to a modem,
  this ends the call.
- **CLOCAL**: ignore the modem control lines. Without it, `open`
  waits for the carrier, and losing the carrier sends `SIGHUP` to the
  session. With a PTY, "losing the carrier" is the master being
  closed, and the hangup happens regardless of CLOCAL.
- **CRTSCTS**: hardware flow control (RTS/CTS lines). Not in POSIX.
- The **speed** is set with `cfsetispeed` and `cfsetospeed`, with
  constants such as B9600, B38400, B115200. B0 means "hang up". On a
  PTY the speed is only reported (`stty` says 38400) and has no
  effect.

### A.4 `c_lflag`: local modes

These control the line discipline itself: canonical mode, echo,
signals. They are the flags that matter for the programs of this
tutorial.

| Flag    | Octal   | Usual |
|---------|---------|-------|
| ISIG    | 0000001 | on    |
| ICANON  | 0000002 | on    |
| ECHO    | 0000010 | on    |
| ECHOE   | 0000020 | on    |
| ECHOK   | 0000040 | on    |
| ECHONL  | 0000100 | off   |
| NOFLSH  | 0000200 | off   |
| TOSTOP  | 0000400 | off   |
| ECHOCTL | 0001000 | on    |
| ECHOPRT | 0002000 | off   |
| ECHOKE  | 0004000 | on    |
| FLUSHO  | 0010000 | off   |
| PENDIN  | 0040000 | off   |
| IEXTEN  | 0100000 | on    |
| EXTPROC | 0200000 | off   |

- **ISIG**: the characters INTR (`^C`), QUIT (`^\`) and SUSP (`^Z`)
  generate `SIGINT`, `SIGQUIT` and `SIGTSTP` for the foreground
  process group, instead of being read. Turned off by raw mode; full
  screen programs often turn it off to handle these keys themselves
  (vim does; `less` does not).
- **ICANON**: canonical mode: input is collected into lines, with
  editing (ERASE, KILL, WERASE, REPRINT, LNEXT), and `read` returns
  only complete lines (or at EOF, `^D`). Off: `read` returns as soon
  as VMIN and VTIME allow (A.5).
- **ECHO**: echo input characters. Off for passwords, and in raw mode
  (the program draws what it wants).
- **ECHOE**: with ICANON, ERASE erases the previous character on the
  screen (backspace, space, backspace), instead of echoing the ERASE
  character.
- **ECHOK**: with ICANON, echo a newline after KILL. With **ECHOKE**,
  erase the whole line on the screen instead.
- **ECHONL**: with ICANON, echo NL even if ECHO is off. For password
  prompts that still want the cursor to move to the next line.
- **NOFLSH**: do not flush the input and output queues when a signal
  is generated by INTR, QUIT or SUSP.
- **TOSTOP**: send `SIGTTOU` to a background process that writes to
  the terminal (chapter 5). Off by default: background jobs can write.
- **ECHOCTL**: echo control characters as `^X` (`^C` is shown as
  `^C`). Not in POSIX, but everywhere.
- **ECHOPRT**: show erased characters between `\` and `/`, for
  hardcopy terminals. Off.
- **FLUSHO**: output is being discarded; toggled by the DISCARD
  character (`^O`) on systems that implement it. Linux does not
  implement DISCARD; the flag exists.
- **PENDIN**: input is reprinted at the next read (set by the system
  when switching to canonical mode with pending input, on some
  systems; Linux does not implement it).
- **IEXTEN**: enable implementation-defined input processing:
  on Linux, the WERASE, REPRINT, LNEXT and DISCARD characters, and
  some extended behavior of ISIG. Raw mode turns it off so that `^V`
  and `^W` are read as bytes.
- **EXTPROC**: external processing: the line editing is done by
  someone else (for `telnet` and `rlogin` servers with the LINEMODE
  option). Linux supports it on PTYs; in practice unused.

### A.5 `c_cc`: special characters, VMIN and VTIME

| Index    | Value | Default | stty    |
|----------|-------|---------|---------|
| VINTR    | 0     | `^C`    | intr    |
| VQUIT    | 1     | `^\`    | quit    |
| VERASE   | 2     | `^?`    | erase   |
| VKILL    | 3     | `^U`    | kill    |
| VEOF     | 4     | `^D`    | eof     |
| VTIME    | 5     | 0       | time    |
| VMIN     | 6     | 1       | min     |
| VSWTC    | 7     | none    | swtch   |
| VSTART   | 8     | `^Q`    | start   |
| VSTOP    | 9     | `^S`    | stop    |
| VSUSP    | 10    | `^Z`    | susp    |
| VEOL     | 11    | none    | eol     |
| VREPRINT | 12    | `^R`    | rprnt   |
| VDISCARD | 13    | `^O`    | discard |
| VWERASE  | 14    | `^W`    | werase  |
| VLNEXT   | 15    | `^V`    | lnext   |
| VEOL2    | 16    | none    | eol2    |

The index values are Linux's; on the BSDs and macOS they differ (VMIN
and VTIME are 16 and 17 there, for example). A character set to
`_POSIX_VDISABLE` (0 on Linux, shown as `<undef>` by `stty`) is
disabled. With `stty`, `stty intr '^X'` changes a character and
`stty intr undef` disables it.

What they do:

- **VINTR**, **VQUIT**, **VSUSP**: with ISIG, send `SIGINT`,
  `SIGQUIT`, `SIGTSTP` to the foreground group. QUIT's default action
  writes a core file.
- **VERASE**: erase the previous character (ICANON). **VWERASE**: the
  previous word (ICANON and IEXTEN). **VKILL**: the whole line.
- **VEOF**: with ICANON, makes the pending input available to `read`
  without a newline. On an empty line, `read` returns 0: end of file.
  That is why `^D` ends `cat` only at the start of a line; elsewhere,
  it sends the partial line, and a second `^D` sends end of file.
- **VEOL**, **VEOL2**: additional line delimiters, like NL.
- **VSTART**, **VSTOP**: XON and XOFF, with IXON.
- **VREPRINT**: reprint the current line (useful after a background
  job wrote over it). **VLNEXT**: the next character is taken
  literally. **VDISCARD**: toggle discarding of output (not on Linux).
- **VSWTC**: the switch character of the old `shl` layers system;
  unused by Linux.

**VMIN and VTIME** matter only in non-canonical mode. They say when
`read` returns, `MIN` a count of bytes and `TIME` in tenths of a
second:

| MIN | TIME | `read` returns                         |
|-----|------|----------------------------------------|
| 0   | 0    | at once, with what is there (or 0)     |
| >0  | 0    | when MIN bytes are available           |
| 0   | >0   | when a byte arrives, or after TIME (0) |
| >0  | >0   | MIN bytes, or TIME after the last byte |

In the last case, the timer starts at the first byte and restarts at
each byte: it is an inter-byte timeout, so `read` can still block
forever if nothing arrives. Programs that want a timeout usually use
MIN=1, TIME=0 and `poll` instead; it is clearer and works with
several descriptors. Note that a `read` never returns more than the size requested.

### A.6 What `cfmakeraw` changes

`cfmakeraw` is the de facto definition of raw mode (it comes from
BSD; check your system's POSIX edition before relying on it in
portable code). On glibc it does,
checked by running it on a structure with every bit set:

```c
t->c_iflag &= ~(IGNBRK | BRKINT | PARMRK | ISTRIP
                | INLCR | IGNCR | ICRNL | IXON);
t->c_oflag &= ~OPOST;
t->c_lflag &= ~(ECHO | ECHONL | ICANON | ISIG | IEXTEN);
t->c_cflag &= ~(CSIZE | PARENB);
t->c_cflag |= CS8;
t->c_cc[VMIN] = 1;
t->c_cc[VTIME] = 0;
```

The cleared bits were 02753 (input), 01 (output) and 0100113 (local),
which are exactly those masks. Rust's `nix::sys::termios::cfmakeraw`
calls the C function; Go's `x/term.MakeRaw` does the same
assignments itself (its source has the same list, in `term_unix.go`);
Raku's `Term::termios` has `makeraw`, which calls `cfmakeraw`.

The older vocabulary, still used by `stty` and by documentation:

- **cooked**: the default, ICANON and ECHO and ISIG on.
- **cbreak** (or "rare"): ICANON off, so characters arrive one by one,
  but ISIG on, so `^C` still works, and usually ECHO off. `stty
  cbreak` is `-icanon`; `stty -a` after it shows `isig -icanon ... echo`
  (it leaves echo alone).
- **raw**: everything off, as above. `stty raw` is close to
  `cfmakeraw` but not equal: in a PTY, after `stty raw`, `stty -a`
  shows `-opost -isig -icanon` but still `echo` and `iexten`. That is
  why the classic shell idiom is `stty raw -echo`.

### A.7 What `stty sane` sets

`stty sane` (GNU coreutils) sets the flags to the values most
programs expect. Saved with `stty -g` in a PTY after `stty raw` and
`stty sane`:

```text
2102:5:f00bf:8a3b:3:1c:7f:15:4:0:1:0:11:13:1a:0:12:f:17:16:0:0:...
```

The `-g` format is the four flag words in hexadecimal, then the
special characters in hexadecimal. Decoded:

- input `0x2102`: BRKINT, ICRNL, IMAXBEL;
- output `0x5`: OPOST, ONLCR;
- local `0x8a3b`: ISIG, ICANON, ECHO, ECHOE, ECHOK, ECHOCTL, ECHOKE,
  IEXTEN;
- characters: `^C` (0x3), `^\` (0x1c), `^?` (0x7f), `^U` (0x15), `^D`
  (0x4), TIME 0, MIN 1, ..., `^Q` (0x11), `^S` (0x13), `^Z` (0x1a),
  ..., `^R` (0x12), `^O` (0xf), `^W` (0x17), `^V` (0x16).

Note what is absent: IXON is **not** set by `stty sane` in this
output (the flow control stays as it was: off here, since `stty raw`
turned it off), and neither is IUTF8. The coreutils documentation
lists exactly what `sane` touches; `info stty` has the list.

### A.8 `tcsetattr` actions and other calls

| Call        | Does                                  |
|-------------|---------------------------------------|
| `tcsetattr` | set attributes, see actions below     |
| `tcdrain`   | wait until output is transmitted      |
| `tcflush`   | discard input, output or both         |
| `tcflow`    | suspend or resume input or output     |
| `tcsendbreak` | send a BREAK                        |
| `tcgetpgrp` | foreground process group              |
| `tcsetpgrp` | set the foreground process group      |
| `tcgetsid`  | session of the terminal               |

The actions of `tcsetattr`:

- **TCSANOW**: change at once.
- **TCSADRAIN**: after all output written so far has been transmitted.
  Use it when the change affects output (OPOST).
- **TCSAFLUSH**: like TCSADRAIN, and discard the input received but
  not read. Use it when entering or leaving raw mode, so that keys
  typed before do not leak into the new mode; it is what most programs
  do.

`tcsetattr` returns success if **any** of the requested changes was
made, so a careful program calls `tcgetattr` after it and compares.

And the `ioctl`s that have no termios wrapper:

| ioctl        | Does                                 |
|--------------|--------------------------------------|
| TIOCGWINSZ   | get the window size                  |
| TIOCSWINSZ   | set it; sends SIGWINCH               |
| TIOCSCTTY    | make it the controlling terminal     |
| TIOCNOTTY    | give up the controlling terminal     |
| TIOCGPTN     | PTY number of a master               |
| TIOCSPTLCK   | lock or unlock the slave             |
| TIOCGPTPEER  | open the slave from the master       |
| TIOCPKT      | packet mode on the master            |
| TIOCSTI      | fake input (disabled by default)     |
| FIONREAD     | bytes available to read              |
| TIOCOUTQ     | bytes waiting in the output queue    |

- **TIOCGPTPEER** (Linux 4.13): opens the slave of a master without
  going through the file system, which avoids races with the path in
  `/dev/pts` (for containers).
- **TIOCPKT**: in packet mode, each `read` on the master starts with a
  status byte: 0 for data, or flags such as TIOCPKT_STOP and
  TIOCPKT_START (flow control changed) or TIOCPKT_FLUSHREAD. `rlogin`
  servers used it to forward `^S` and `^Q` handling to the client.
- **TIOCSTI** pushes a byte into the input queue as if typed; it was
  a security problem (a program in a `su` session could type commands
  in the parent shell) and Linux 6.2 added a build option and the
  `dev.tty.legacy_tiocsti` sysctl to disable it, which many
  distributions do.

## Appendix B. Escape sequence reference

This is a working reference for the sequences that programs send to
terminals and that terminals send back, as implemented by xterm and
by the emulators that follow it (most of them). The authority is
"XTerm Control Sequences" by Thomas Dickey
([invisible-island.net/xterm/ctlseqs/ctlseqs.html](https://invisible-island.net/xterm/ctlseqs/ctlseqs.html)),
with ECMA-48 behind it for the standard part. Where this appendix
quotes a terminfo capability, it is from the `xterm-256color` entry
of ncurses on the machine of this tutorial (`infocmp -1x
xterm-256color`).

Notation: `ESC` is 0x1B, `CSI` is `ESC [`, `OSC` is `ESC ]`, `DCS`
is `ESC P`, `ST` (string terminator) is `ESC \`, `BEL` is 0x07. `Pn`
is a number, `Ps` a selector, `Pm` a list of numbers separated by
`;`. A missing number means the default, usually 1 (0 for selectors).
Numbers count from 1: row 1, column 1 is the top left corner.

### B.1 C0 control characters

The bytes 0x00 to 0x1F. A terminal acts on a few of them and ignores
the rest.

| Byte | Name | Key  | Action                    |
|------|------|------|---------------------------|
| 0x00 | NUL  | `^@` | ignored                   |
| 0x05 | ENQ  | `^E` | answerback (usually none) |
| 0x07 | BEL  | `^G` | bell; also ends OSC       |
| 0x08 | BS   | `^H` | cursor left one           |
| 0x09 | HT   | `^I` | next tab stop             |
| 0x0A | LF   | `^J` | line feed (maybe scroll)  |
| 0x0B | VT   | `^K` | like LF                   |
| 0x0C | FF   | `^L` | like LF                   |
| 0x0D | CR   | `^M` | column 1                  |
| 0x0E | SO   | `^N` | use G1 character set      |
| 0x0F | SI   | `^O` | use G0 character set      |
| 0x18 | CAN  | `^X` | cancel a sequence         |
| 0x1A | SUB  | `^Z` | cancel a sequence         |
| 0x1B | ESC  | `^[` | start a sequence          |
| 0x7F | DEL  | `^?` | ignored                   |

Remarks:

- LF moves down only; the move to column 1 that you see comes from
  the line discipline's ONLCR (A.2), which turns `\n` into `\r\n`
  before the terminal gets it.
- BS does not erase. Erasing on screen (ECHOE) is `BS SP BS`.
- SO with G1 set to the DEC line drawing set (`ESC ) 0`) is how old
  programs draw boxes; a stray SO in binary output is why `cat` of a
  binary file can leave the terminal printing line-drawing
  characters. `SI`, or `reset`, fixes it.
- The **key** column is what you type to produce the byte, which is
  how the key `^[` becomes ESC, and why Ctrl-[ and Escape are the
  same key for a terminal program. Control-letter is the letter with
  bit 6 cleared (`'A' ^ 0x40` is 1), which is the `send-control`
  helper of chapter 30.

### B.2 Escape sequences without CSI

| Sequence  | Name    | Action                         |
|-----------|---------|--------------------------------|
| `ESC 7`   | DECSC   | save cursor and attributes     |
| `ESC 8`   | DECRC   | restore them                   |
| `ESC D`   | IND     | index: down, scroll if needed  |
| `ESC E`   | NEL     | next line (CR LF)              |
| `ESC H`   | HTS     | set a tab stop here            |
| `ESC M`   | RI      | reverse index: up, scroll down |
| `ESC c`   | RIS     | full reset                     |
| `ESC =`   | DECKPAM | keypad application mode        |
| `ESC >`   | DECKPNM | keypad numeric mode            |
| `ESC ( C` | SCS     | designate G0 charset           |
| `ESC ) C` | SCS     | designate G1 charset           |
| `ESC # 8` | DECALN  | fill screen with `E`           |

For SCS, `C` is `B` for US ASCII (the normal set) and `0` for the DEC
special graphics (line drawing): in it, `q` is `─`, `x` is `│`, `l`,
`k`, `m`, `j` are the corners `┌ ┐ └ ┘`, `n` is `┼`, `t`, `u`, `v`,
`w` are the tees. This is the `acsc` capability of terminfo. The
`sgr0` of `xterm-256color` starts with `ESC ( B` for that reason.

### B.3 CSI: cursor movement

| Sequence       | Name | Action                          |
|----------------|------|---------------------------------|
| `CSI Pn A`     | CUU  | up Pn rows                      |
| `CSI Pn B`     | CUD  | down Pn rows                    |
| `CSI Pn C`     | CUF  | right Pn columns                |
| `CSI Pn D`     | CUB  | left Pn columns                 |
| `CSI Pn E`     | CNL  | down Pn rows, to column 1       |
| `CSI Pn F`     | CPL  | up Pn rows, to column 1         |
| `CSI Pn G`     | CHA  | to column Pn                    |
| `CSI Pr;Pc H`  | CUP  | to row Pr, column Pc            |
| `CSI Pr;Pc f`  | HVP  | same as CUP                     |
| `CSI Pn d`     | VPA  | to row Pn                       |
| `CSI Pn I`     | CHT  | forward Pn tab stops            |
| `CSI Pn Z`     | CBT  | back Pn tab stops               |
| `CSI s`        | SCOSC| save cursor (like `ESC 7`)      |
| `CSI u`        | SCORC| restore cursor (like `ESC 8`)   |

Cursor movements stop at the margins: `CSI 100 C` on an 80-column
screen goes to column 80, and does not wrap. `CSI H` alone goes home
(1,1). The terminfo names: `cup` (CUP), `cuu1`, `cud1`, `cuf1`,
`cub1` and with a count `cuu`, `cud`, `cuf`, `cub`; `hpa` (CHA), `vpa`
(VPA), `home`, `sc` and `rc`.

`CSI s` conflicts with DECSLRM (set left and right margins) when the
left/right margin mode is on; prefer `ESC 7` and `ESC 8`, which also
save the attributes.

### B.4 CSI: erasing, inserting, deleting, scrolling

| Sequence       | Name  | Action                         |
|----------------|-------|--------------------------------|
| `CSI 0 J`      | ED    | erase from cursor to end       |
| `CSI 1 J`      | ED    | erase from start to cursor     |
| `CSI 2 J`      | ED    | erase whole screen             |
| `CSI 3 J`      | ED    | erase scrollback (xterm)       |
| `CSI 0 K`      | EL    | erase to end of line           |
| `CSI 1 K`      | EL    | erase to start of line         |
| `CSI 2 K`      | EL    | erase whole line               |
| `CSI Pn X`     | ECH   | erase Pn characters            |
| `CSI Pn @`     | ICH   | insert Pn blanks               |
| `CSI Pn P`     | DCH   | delete Pn characters           |
| `CSI Pn L`     | IL    | insert Pn lines                |
| `CSI Pn M`     | DL    | delete Pn lines                |
| `CSI Pn S`     | SU    | scroll up Pn lines             |
| `CSI Pn T`     | SD    | scroll down Pn lines           |
| `CSI Pt;Pb r`  | DECSTBM | set scroll region            |
| `CSI Pn b`     | REP   | repeat last character Pn times |

Remarks:

- Erasing does not move the cursor. `CSI 2 J` does not go home
  either: the `clear` capability is `ESC [H ESC [2J`, both.
- Erased cells take the **current background color** (the "back
  color erase" property, `bce` in terminfo). A program that sets a
  blue background and erases the screen gets a blue screen.
- `CSI 0 K` is `el` in terminfo, `CSI 0 J` is `ed`. Writing `CSI K`
  without a number means 0. (A library that sends `CSI 2 J` when
  asked to erase to the end of the line clears the whole screen
  instead: this is the `Terminal::ANSI` issue mentioned at the end of
  this tutorial.)
- IL, DL, ICH and DCH work inside the scroll region and the line
  respectively; lines pushed out disappear.
- DECSTBM moves the cursor home. Without parameters it resets the
  region to the whole screen. In terminfo, `csr`.
- REP repeats the last printed graphic character. terminfo's `rep`
  for xterm is `%p1%c\E[%p2%{1}%-%db`: print the character, then
  repeat it count − 1 times.

### B.5 SGR: colors and attributes

`CSI Pm m` sets the graphic rendition. Several parameters can be
combined: `CSI 1;4;31 m` is bold, underlined, red. `CSI m` alone is
`CSI 0 m`.

| Ps  | Effect               | Undo  |
|-----|----------------------|-------|
| 0   | reset all            |       |
| 1   | bold                 | 22    |
| 2   | dim (faint)          | 22    |
| 3   | italic               | 23    |
| 4   | underline            | 24    |
| 5   | blink                | 25    |
| 7   | reverse video        | 27    |
| 8   | invisible            | 28    |
| 9   | crossed out          | 29    |
| 21  | double underline     | 24    |
| 53  | overline             | 55    |

Note that 22 undoes both bold and dim. Some old terminals took 21 as
"bold off"; today it is double underline.

Colors:

| Ps          | Effect                          |
|-------------|---------------------------------|
| 30–37       | foreground, colors 0–7          |
| 38;5;N      | foreground, color N of 256      |
| 38;2;R;G;B  | foreground, 24-bit              |
| 39          | default foreground              |
| 40–47       | background, colors 0–7          |
| 48;5;N      | background, color N of 256      |
| 48;2;R;G;B  | background, 24-bit              |
| 49          | default background              |
| 90–97       | foreground, colors 8–15         |
| 100–107     | background, colors 8–15         |
| 58;5;N      | underline color (kitty, others) |
| 59          | default underline color         |

The eight basic colors are, in order: black, red, green, yellow,
blue, magenta, cyan, white; 8 to 15 are the bright versions. The
actual colors are chosen by the user's theme, which is the point:
programs that use 0–15 adapt to dark and light themes.

The 256-color palette: 0–15 are the 16 colors above; 16–231 are a
6×6×6 cube, color `16 + 36r + 6g + b` with `r`, `g`, `b` from 0 to 5;
232–255 are 24 grays from dark to light. The standard ISO 8613-6 form
of the extended colors uses colons (`38:2::R:G:B`, with an empty
color space field); most terminals accept both, and the
semicolon form is the common one.

Underline styles: `CSI 4:3 m` is a curly underline (kitty, WezTerm,
foot, VTE, and others: the `Smulx` capability), `4:0` none, `4:1`
single, `4:2` double, `4:4` dotted, `4:5` dashed. Terminals that do
not know the colon form may take it as plain `4`.

The terminfo `setaf` of `xterm-256color` is

```text
\E[%?%p1%{8}%<%t3%p1%d%e%p1%{16}%<%t9%p1%{8}%-%d%e38;5;%p1%d%;m
```

and does: if the color (p1) is below 8, emit `3` then the color; else
if below 16, emit `9` then color − 8; else `38;5;` then the color.
24-bit colors have no standard terminfo capability; the extensions
`RGB` and `Tc`, and the `setrgbf` and `setrgbb` strings, signal them
in some entries. Programs mostly check `COLORTERM=truecolor` (or
`24bit`) in the environment.

### B.6 Modes

`CSI Pm h` sets ANSI modes and `CSI Pm l` resets them; with `?`
(`CSI ? Pm h`), DEC private modes. The ones a TUI programmer meets:

| Mode   | Name       | When set                         |
|--------|------------|----------------------------------|
| 4      | IRM        | insert mode                      |
| 20     | LNM        | LF also does CR (rare)           |
| ?1     | DECCKM     | application cursor keys          |
| ?3     | DECCOLM    | 132 columns (if allowed)         |
| ?5     | DECSCNM    | reverse screen (flash)           |
| ?6     | DECOM      | origin mode: rows from region    |
| ?7     | DECAWM     | autowrap at the right margin     |
| ?12    |            | blinking cursor                  |
| ?25    | DECTCEM    | cursor visible                   |
| ?47    |            | alternate screen (old)           |
| ?1000  |            | mouse: clicks                    |
| ?1002  |            | mouse: clicks and drags          |
| ?1003  |            | mouse: all motion                |
| ?1004  |            | focus in/out events              |
| ?1006  |            | mouse: SGR encoding              |
| ?1047  |            | alternate screen                 |
| ?1048  |            | save/restore cursor              |
| ?1049  |            | 1048 + 1047 + clear              |
| ?2004  |            | bracketed paste                  |
| ?2026  |            | synchronized output              |

Remarks:

- **?1049** is what full-screen programs use (`smcup` and `rmcup` in
  terminfo): save the cursor, switch to the alternate screen, clear
  it; and on reset, switch back and restore the cursor. The alternate
  screen has no scrollback in xterm, and the main screen is left
  intact, which is why the shell session reappears when `vim` or
  `less` exits. `less -X` and `git config core.pager 'less -FRX'`
  disable it for programs whose output you want to keep.
- **?1** and keypad mode (`ESC =`) are `smkx` in terminfo:
  `\E[?1h\E=`. They change what the arrow keys and keypad send (B.8).
  A program that sends `smkx` must send `rmkx` on exit, or the shell
  gets `ESC O A` for the Up key, which readline usually handles, but
  other programs may not.
- **?25** hides the cursor (`civis`) and shows it (`cnorm`). A program
  that dies with the cursor hidden is a classic: `tput cnorm` (32.9).
- **?7**: with autowrap off, characters written past the right margin
  overwrite the last column. Useful when drawing a status line that
  must not wrap.
- **?2026** (synchronized output): between `CSI ? 2026 h` and `CSI ?
  2026 l` the terminal does not repaint, so a frame appears at once
  (31.3). A terminal reports support with DECRQM (B.9).
- To query a mode: `CSI ? Pn $ p` (DECRQM); the answer is `CSI ? Pn ;
  Ps $ y`, with Ps 1 set, 2 reset, 0 not recognized, 3 permanently
  set, 4 permanently reset.

### B.7 OSC: operating system commands

`OSC Ps ; Pt BEL` or `OSC Ps ; Pt ST`. Both terminators are common;
`ST` is the standard one, `BEL` the older xterm one.

| Ps  | Action                                    |
|-----|-------------------------------------------|
| 0   | set window title and icon name            |
| 2   | set window title                          |
| 4   | set or query palette colors               |
| 7   | current directory (`file://host/path`)    |
| 8   | hyperlink                                 |
| 10  | set or query default foreground           |
| 11  | set or query default background           |
| 12  | set or query cursor color                 |
| 52  | set or query the clipboard (base64)       |
| 104 | reset palette colors                      |
| 133 | shell integration marks                   |

Examples:

```sh
printf '\e]2;my title\a'                     # window title
printf '\e]8;;https://example.com\e\\link\e]8;;\e\\\n'   # hyperlink
printf '\e]52;c;%s\a' "$(printf hello | base64)"         # copy "hello"
printf '\e]11;?\a'                           # ask the background color
```

The last one is a **query**: the terminal answers on the input, like
a key press, with `OSC 11 ; rgb:RRRR/GGGG/BBBB ST`. Programs use it to
choose a light or dark theme. Reading the answer needs raw mode and a
timeout, because terminals that do not support the query do not
answer at all (the "program waits forever at start" symptom of 32.8).

**OSC 8** hyperlinks: `OSC 8 ; params ; URI ST` starts a link, the
text follows, and `OSC 8 ; ; ST` ends it. `ls --hyperlink`, `gcc`
diagnostics and many tools emit them when the terminal is known to
support them.

**OSC 52** lets a program write to the system clipboard through the
terminal, which works over `ssh` and in `tmux` (with `set-clipboard
on`). Reading the clipboard (`?` instead of the data) is disabled by
most terminals for security. The terminfo extension `Ms` describes it:
`\E]52;%p1%s;%p2%s\007`.

**OSC 133** marks the prompt, the command and the output (`A`, `B`,
`C`, `D;status`), so that the terminal can jump between commands and
know their exit statuses. It comes from FinalTerm; kitty, WezTerm,
foot, iTerm2, Windows Terminal and others support it. **OSC 7** tells
the terminal the current directory, so that a new tab opens in the
same place.

For the origin of each number (ECMA-48, xterm, iTerm2, kitty,
ConEmu, FinalTerm, systemd) and the collisions between them, see 7.16.

### B.8 What keys send

With `TERM=xterm-256color`, normal cursor mode (`?1l`) and
application mode (`?1h`, after `smkx`):

| Key       | Normal    | Application |
|-----------|-----------|-------------|
| Up        | `CSI A`   | `ESC O A`   |
| Down      | `CSI B`   | `ESC O B`   |
| Right     | `CSI C`   | `ESC O C`   |
| Left      | `CSI D`   | `ESC O D`   |
| Home      | `CSI H`   | `ESC O H`   |
| End       | `CSI F`   | `ESC O F`   |

Other keys, the same in both modes:

| Key       | Sends       | terminfo |
|-----------|-------------|----------|
| Insert    | `CSI 2 ~`   | kich1    |
| Delete    | `CSI 3 ~`   | kdch1    |
| PageUp    | `CSI 5 ~`   | kpp      |
| PageDown  | `CSI 6 ~`   | knp      |
| F1–F4     | `ESC O P`–`S` | kf1–kf4 |
| F5        | `CSI 15 ~`  | kf5      |
| F6–F8     | `CSI 17~`–`19~` | kf6–kf8 |
| F9, F10   | `CSI 20~`, `21~` | kf9, kf10 |
| F11, F12  | `CSI 23~`, `24~` | kf11, kf12 |
| Shift-Tab | `CSI Z`     | kcbt     |
| Backspace | `^?` (DEL)  | kbs      |
| Enter     | `^M` (CR)   |          |
| Tab       | `^I`        |          |
| Escape    | `ESC`       |          |

The gaps in the F-key numbers (16, 22) are historical, from the DEC
VT220 keyboard. Terminals disagree on Home and End (tmux sent `CSI 1
~` for Home in 32.4), which is why programs read terminfo or accept
all the common forms.

**Modifiers** are encoded as a parameter: `CSI 1 ; M X` for the cursor
keys and `CSI N ; M ~` for the tilde keys, with `M` = 1 + the sum of
Shift (1), Alt (2), Ctrl (4), Meta (8):

| M | Modifiers   | Up              |
|---|-------------|-----------------|
| 2 | Shift       | `CSI 1;2 A`     |
| 3 | Alt         | `CSI 1;3 A`     |
| 4 | Shift-Alt   | `CSI 1;4 A`     |
| 5 | Ctrl        | `CSI 1;5 A`     |
| 6 | Shift-Ctrl  | `CSI 1;6 A`     |
| 7 | Alt-Ctrl    | `CSI 1;7 A`     |

The terminfo names are `kUP` (Shift-Up), `kUP3` (Alt), `kUP5` (Ctrl),
and so on; similarly `kRIT5` is Ctrl-Right. They are "extended"
capabilities, shown by `infocmp -x`. F-keys with modifiers appear as
`kf13` and up: `kf13` is Shift-F1, `CSI 1;2 P`; `kf25` is Ctrl-F1.

**Alt** with a character key usually sends ESC followed by the key
(`ESC x` for Alt-x), which is ambiguous with a real Escape followed
by `x`. Programs resolve it with a timeout: if `x` arrives within a
few tens of milliseconds after ESC, it is Alt-x. Vim's `ttimeoutlen`,
tmux's `escape-time` and the 50 ms of exercise E.11 are that timeout.

**Ctrl** with a letter sends the control character; with other keys
it is limited: Ctrl-1 sends nothing special, Ctrl-I is Tab, Ctrl-M
is Enter. The **kitty keyboard protocol** (`CSI > 1 u` to push the
"disambiguate" flag, `CSI < u` to pop) fixes this: keys are then
reported as `CSI codepoint ; modifiers u`, so Ctrl-I and Tab differ
and Escape is `CSI 27 u`, without timeout. It is supported by kitty,
foot, WezTerm, Ghostty, Alacritty and others, and by programs such as
Neovim, Helix and the newer versions of Bubble Tea.

### B.9 Queries and their answers

The answers arrive on the terminal's input, so the program reads them
like keys (in raw mode, with a timeout).

| Query        | Asks for           | Answer               |
|--------------|--------------------|----------------------|
| `CSI 5 n`    | status             | `CSI 0 n` (OK)       |
| `CSI 6 n`    | cursor position    | `CSI row;col R`      |
| `CSI c`      | primary DA         | `CSI ? Pm c`         |
| `CSI > c`    | secondary DA       | `CSI > Pp;Pv;Pc c`   |
| `CSI > q`    | version (XTVERSION)| `DCS > \| text ST`   |
| `CSI 14 t`   | size in pixels     | `CSI 4;h;w t`        |
| `CSI 18 t`   | size in characters | `CSI 8;rows;cols t`  |
| `CSI ? Pn $ p` | mode state       | `CSI ? Pn;Ps $ y`    |
| `CSI ? u`    | kitty keyboard     | `CSI ? flags u`      |
| `OSC 11;? ST`| background color   | `OSC 11;rgb:... ST`  |

Remarks:

- **CSI 6 n** (`u7` in terminfo, with the answer format in `u6`) is
  the oldest trick to find the terminal size without `TIOCGWINSZ`:
  move the cursor to 999;999 and ask where it is. `resize` (from
  xterm) does that on serial consoles.
- **Primary DA** (`u9`) answers with a list of features: `CSI ? 1 ; 2
  c` is "VT100 with advanced video", which `muxi` answers (31.2);
  xterm answers `CSI ? 64 ; ... c`, a VT420 class with a list. Since
  every terminal answers DA, programs send their query (say, OSC 11
  or the kitty keyboard query) **followed by DA**: if the DA answer
  comes first, the terminal does not support the first query, and
  there is no need for a timeout.
- **XTVERSION** returns the name and version, `DCS > | XTerm(390) ST`
  or `DCS > | tmux 3.5a ST`.

### B.10 Mouse reporting

Mouse events are input too. Enable a mode (B.6) and an encoding:

- **?1000**: report button presses and releases; **?1002**: also
  motion while a button is pressed; **?1003**: all motion.
- **?1006** (SGR encoding): each event is `CSI < b ; x ; y M` for a
  press and `CSI < b ; x ; y m` (lower case) for a release, with `b`
  the button (0 left, 1 middle, 2 right, 64 and 65 the wheel, plus 4
  for Shift, 8 Alt, 16 Ctrl, 32 for motion) and `x`, `y` the cell,
  from 1. The `kmous` capability of `xterm-256color` is `\E[<`.
  terminfo's `XM` capability is the string that turns it on:
  `\E[?1006;1000%?%p1%{1}%=%th%el%;`.
- The legacy encoding (without 1006) is `CSI M` followed by three
  bytes, each the value + 32, which cannot express columns beyond 223
  and is not valid UTF-8: always use 1006.

While mouse reporting is on, the terminal does not select text on a
click; Shift-click usually bypasses the program. A program that dies
with mouse reporting on leaves the terminal printing `^[[<0;12;5M`
garbage on every click: `reset`, or `printf '\e[?1000l\e[?1002l\e[?1003l\e[?1006l'`.

### B.11 Bracketed paste and focus events

**Bracketed paste** (`?2004`): when set, the terminal surrounds
pasted text with `CSI 200 ~` and `CSI 201 ~` (`PS` and `PE` in
terminfo; `BE` and `BD` are the strings to enable and disable it).
The program then knows that the text was pasted, not typed:

- a shell does not execute pasted lines as soon as their newline
  arrives, so pasting a command with an `rm` in it does not run it
  before you look at it;
- an editor does not auto-indent pasted code (the "staircase paste"
  of old vim);
- the program can treat the paste as one event, not as thousands of
  keys.

bash (readline 8.1 and later, `enable-bracketed-paste` on by default)
turns it on while it reads a command: that is the `\e[?2004h` at the
start of each prompt and the `\e[?2004l` before each command in the
`ttylog` log of 32.5. A program that receives `CSI 200 ~` and does
not know it shows `^[[200~` at the start of the pasted text: the
mode was left on by a program that crashed.

Security: a pasted text that contains `CSI 201 ~` could end the
bracket early and have the rest executed; terminals now filter that
sequence out of pasted text (xterm, VTE and kitty among them), and so
should a program that implements
"paste" on behalf of a user.

**Focus events** (`?1004`): the terminal sends `CSI I` when its window
gains focus and `CSI O` when it loses it. Vim uses them to reload
files changed outside; tmux forwards them with `focus-events on`.

### B.12 The terminfo string language

terminfo capabilities with parameters are small programs for a stack
machine, interpreted by `tparm` (C), `tput` (shell), and the terminfo
libraries of other languages. The operators that appear in practice:

| Code       | Meaning                               |
|------------|---------------------------------------|
| `%p1`–`%p9`| push parameter i                      |
| `%d`       | pop and print as decimal              |
| `%c`       | pop and print as a character          |
| `%s`       | pop and print as a string             |
| `%i`       | add 1 to parameters 1 and 2           |
| `%{n}`     | push the constant n                   |
| `%'c'`     | push the character constant c         |
| `%+ %- %* %/ %m` | arithmetic                      |
| `%< %> %=` | comparisons                           |
| `%A %O %!` | logical and, or, not                  |
| `%? c %t a %e b %;` | if c then a else b           |
| `%Pa`, `%ga` | set, get variable a                 |
| `%%`       | a literal `%`                         |
| `$<n>`     | delay of n milliseconds (padding)     |

Read `cup=\E[%i%p1%d;%p2%dH` as: increment the parameters (terminfo
counts from 0, the terminal from 1), print parameter 1, `;`,
parameter 2, `H`. The `$<100/>` in xterm's `flash` is a padding
delay, a relic of slow lines; ncurses applies it with timing, not
with NUL characters, on fast terminals.

## Appendix C. Signals reference

The numbers are those of Linux on x86-64 and arm64 (printed with
`sigabbrev_np` by the same program as Appendix A); some differ on
other architectures (Alpha, MIPS, SPARC) and on the BSDs and macOS,
so always use the names. `kill -l` prints the list for the current
system.

### C.1 The table

Default actions: **term** terminates; **core** terminates and dumps
core (if `ulimit -c` allows it, and on systemd machines the dump goes
to `systemd-coredump`); **ign** ignores; **stop** stops the process;
**cont** continues it if stopped.

| No | Name    | Default | Cause                       |
|----|---------|---------|-----------------------------|
| 1  | SIGHUP  | term    | terminal hung up            |
| 2  | SIGINT  | term    | `^C` (VINTR)                |
| 3  | SIGQUIT | core    | `^\` (VQUIT)                |
| 4  | SIGILL  | core    | illegal instruction         |
| 5  | SIGTRAP | core    | breakpoint                  |
| 6  | SIGABRT | core    | `abort()`                   |
| 7  | SIGBUS  | core    | bad memory access           |
| 8  | SIGFPE  | core    | arithmetic error            |
| 9  | SIGKILL | term    | `kill -9`; cannot be caught |
| 10 | SIGUSR1 | term    | user-defined                |
| 11 | SIGSEGV | core    | invalid memory reference    |
| 12 | SIGUSR2 | term    | user-defined                |
| 13 | SIGPIPE | term    | write to a broken pipe      |
| 14 | SIGALRM | term    | `alarm()` timer             |
| 15 | SIGTERM | term    | polite termination request  |
| 16 | SIGSTKFLT | term  | unused                      |
| 17 | SIGCHLD | ign     | a child stopped or exited   |
| 18 | SIGCONT | cont    | continue (`fg`, `bg`)       |
| 19 | SIGSTOP | stop    | stop; cannot be caught      |
| 20 | SIGTSTP | stop    | `^Z` (VSUSP)                |
| 21 | SIGTTIN | stop    | background read from tty    |
| 22 | SIGTTOU | stop    | background write or ioctl   |
| 23 | SIGURG  | ign     | urgent socket data          |
| 24 | SIGXCPU | core    | CPU time limit              |
| 25 | SIGXFSZ | core    | file size limit             |
| 26 | SIGVTALRM | term  | virtual timer               |
| 27 | SIGPROF | term    | profiling timer             |
| 28 | SIGWINCH | ign    | window size changed         |
| 29 | SIGIO   | term    | I/O possible (SIGPOLL)      |
| 30 | SIGPWR  | term    | power failure               |
| 31 | SIGSYS  | core    | bad system call             |

Real-time signals are 34 to 64 (`SIGRTMIN` to `SIGRTMAX`; glibc
reserves 32 and 33 for threads, which is why `SIGRTMIN` is 34 and not
32). They queue (several instances are delivered), unlike the
standard ones.

### C.2 The terminal signals in detail

- **SIGHUP**: sent by the kernel to the **session leader** when the
  terminal hangs up: the modem dropped the line, the terminal emulator
  window was closed, the master side of a PTY was closed (31.3). The
  kernel also sends SIGHUP followed by SIGCONT to a process group
  that becomes **orphaned** while it has stopped members (chapter 5).
  And when the session leader that controls the terminal exits, the
  kernel sends SIGHUP to the foreground process group of that
  terminal (see `_exit(2)`). Without job control, a command started
  with `&` stays in that group, so `sh -c 'sleep 100 & exit'` kills
  its `sleep` too (E.10 has a measured example). Shells forward SIGHUP to their jobs when they get it (bash also on
  exit, with `shopt -s huponexit`); `nohup` and `disown` are the ways
  out. Daemons conventionally reinterpret SIGHUP as "reload your
  configuration", since they have no terminal to lose.
- **SIGINT**, **SIGQUIT**, **SIGTSTP**: sent by the line discipline
  to the **foreground process group** when it reads VINTR, VQUIT or
  VSUSP with ISIG set. Every process of the group gets it, which is
  how one `^C` kills every command of a pipeline. Interactive shells
  ignore them for themselves.
- **SIGTTIN**: sent to a background process group that reads from its
  controlling terminal. If the process ignores or blocks SIGTTIN, or
  if its group is orphaned, `read` fails with `EIO` instead.
- **SIGTTOU**: sent to a background process group that writes to the
  terminal with TOSTOP set, or that changes the terminal's settings
  (`tcsetattr`, `tcsetpgrp`, `tcflush`...) even without TOSTOP. A
  shell that gives the terminal to a job with `tcsetpgrp` from the
  background must ignore or block SIGTTOU first; it is the most
  common bug in hand-written shells (chapter 13).
- **SIGCONT**: continues a stopped process, whatever its disposition;
  a handler, if any, runs after the continuation. Programs that set
  raw mode catch it to set raw mode again after `fg`, since the shell
  restored the cooked mode when the job was stopped.
- **SIGWINCH**: sent to the foreground process group when the window
  size changes (`TIOCSWINSZ`, done by the terminal emulator or by
  the program on the master side). Ignored by default, so programs
  that do not care are not killed.
- **SIGPIPE**: sent to a process that writes to a pipe (or socket)
  whose read ends are all closed; the write also fails with `EPIPE`.
  The default action ends the process silently, which is what makes
  `yes | head -1` terminate. Chapter 3 and the language chapters
  (15.7, 20.5, 25.4) show how each language handles it.
- **SIGCHLD**: sent to the parent when a child exits, stops or
  continues. Ignored by default, but **setting it to `SIG_IGN`
  explicitly** has a special meaning: children are reaped
  automatically and never become zombies, and `wait` then fails with
  `ECHILD`. Go's and Raku's runtimes install their own handlers.

### C.3 The rules

- **Dispositions across `fork`**: the child inherits the handlers,
  the ignored signals and the signal mask.
- **Across `exec`**: caught signals are reset to their default
  (handlers do not exist in the new program), ignored signals stay
  ignored, and the mask is kept. Hence the rule: before `exec`ing a
  command, a shell resets the signals it ignores (SIGINT, SIGTSTP,
  SIGTTOU...) to the default, or the command could not be
  interrupted. And a program started with SIGPIPE ignored (Python
  does that, then its child commands inherit it unless it resets it)
  gets `EPIPE` errors instead of dying quietly.
- **Pending signals**: a standard signal sent several times while
  blocked is delivered once.
- **Handlers** must call only **async-signal-safe** functions
  (`write`, `_exit`, `kill`, `tcsetattr`, `signal`... the list is in
  `signal-safety(7)`); not `printf`, not `malloc`. The safe patterns
  are to set a `volatile sig_atomic_t` flag, to write a byte to a
  self-pipe (3.12), or to use `signalfd` and not handle the signal
  asynchronously at all.
- **`SA_RESTART`**: with it, slow system calls interrupted by the
  handler are restarted; without it they fail with `EINTR`. A program
  that wants `poll` to return on SIGWINCH installs the handler
  without SA_RESTART (as `ttylog` does). Some calls are never
  restarted: `poll`, `select`, `nanosleep`, `epoll_wait`...
  (`signal(7)` has the list).
- **Exit status**: a process killed by signal N appears to the shell
  as status 128 + N: `^C` gives 130, `kill` (SIGTERM) gives 143, a
  segmentation fault 139. `waitpid` gives the exact information:
  `WIFSIGNALED(status)` and `WTERMSIG(status)`, and `WCOREDUMP`.

### C.4 Catching signals in each language

| Language | Mechanism                                |
|----------|------------------------------------------|
| C        | `sigaction`, `signalfd`, self-pipe       |
| Raku     | `signal(SIGWINCH).tap` or `whenever`     |
| Rust     | `signal-hook` crate (flags, iterator)    |
| Go       | `signal.Notify(ch, syscall.SIGWINCH)`    |

- **C**: `sigaction` with a handler that sets a flag, or `signalfd`
  on Linux to read signals as data from a descriptor (exercise E.10).
- **Raku**: `signal(SIGINT)` returns a `Supply` of signals; in a
  `react` block, `whenever signal(SIGINT) { ... }` (15.6). The handler
  code runs on a thread of the pool, not in signal context, so it can
  do anything.
- **Rust**: no safe signal API in std. The `signal-hook` crate offers
  `flag::register` (set an `AtomicBool`), `iterator::Signals` (a
  thread receives them), and `low_level::pipe` (the self-pipe trick)
  (20.6). `ctrlc` is a small crate just for `^C`.
- **Go**: `signal.Notify` delivers signals to a channel, read in a
  `select` (25.5). `signal.Ignore` and `signal.Reset` change the
  disposition; `signal.NotifyContext` cancels a context on a signal.
  The runtime itself handles SIGPIPE specially: a write to a broken
  pipe on descriptors 1 and 2 kills the program, on other descriptors
  it returns `EPIPE` (25.4).

### C.5 Sending signals

- From the shell: `kill -TERM PID`, `kill -INT -PGID` (a negative
  number is a process group: the whole job), `kill %1` (a job of the
  shell), `pkill -f PATTERN` (by name; beware of matching more than
  intended).
- From C: `kill(pid, sig)`, `kill(-pgid, sig)` or `killpg(pgid,
  sig)`, `raise(sig)` for oneself, `pthread_kill` for a thread,
  `sigqueue` with a value for real-time signals.
- From the terminal: the special characters of A.5, for the
  foreground group.
- On a PTY master: writing `^C` does the same as typing it (the line
  discipline sees it). Linux also has `TIOCSIG` on the master, which
  sends a signal to the foreground group of the slave directly,
  whatever the modes.
- `kill -0 PID` sends nothing and tells whether the process exists
  (and whether you may signal it).

## Appendix D. Glossary

**Alternate screen.** A second screen buffer of the terminal, without
scrollback, used by full-screen programs so that the shell session is
intact when they exit. Mode `?1049` (B.6); `smcup` and `rmcup`.

**ANSI escape sequence.** Informal name for the control sequences of
ECMA-48 (ANSI X3.64), and by extension for all the sequences of
xterm. See *CSI*, *OSC*.

**Application mode.** A mode in which the cursor keys (DECCKM) or the
keypad (DECKPAM) send `ESC O x` instead of `CSI x` or digits (B.8).
Turned on by `smkx`.

**asciicast.** The JSON-lines recording format of asciinema: a header
line, then one `[time, type, data]` array per event (29.6).

**Async-signal-safe.** A function that may be called from a signal
handler: it does not take locks or use global state that the
interrupted code could be modifying. `signal-safety(7)` has the list.

**Background process group.** Any process group of a session other
than the foreground one. It gets `SIGTTIN` if it reads the terminal,
and `SIGTTOU` if it writes with `tostop` or changes the modes.

**Bracketed paste.** A mode (`?2004`) in which the terminal surrounds
pasted text with `CSI 200 ~` and `CSI 201 ~` (B.11).

**Buffering (stdio).** The C library collects output in a buffer and
writes it in large blocks: line by line if the output is a terminal,
by blocks of a few KiB otherwise (2.13). The reason output "appears
late" in pipes.

**Canonical mode (cooked mode).** The line discipline mode (ICANON)
in which input is edited and delivered a line at a time (4.2).

**cbreak mode.** Non-canonical mode with signals still enabled:
characters arrive one by one, `^C` still interrupts (A.6).

**Cell.** One character position on the screen, with its character,
its colors and attributes. Wide characters take two cells.

**Charm.** The company and the set of Go libraries (Bubble Tea, Lip
Gloss, Bubbles, Huh, Wish, Glamour...) at `charm.land` (chapter 28).

**Close-on-exec.** A descriptor flag (`FD_CLOEXEC`, `O_CLOEXEC`) that
closes the descriptor automatically at `exec` (2.7). Rust and Go set
it on every descriptor they create.

**Controlling terminal.** The terminal associated with a session.
Its line discipline sends job-control signals to the session's
processes, and `/dev/tty` refers to it. Acquired by the session
leader with `TIOCSCTTY` (or by opening a terminal without
`O_NOCTTY`).

**Coprocess.** A process whose standard input and output are both
connected to the parent, through two pipes (or a PTY), so that the
parent can have a conversation with it (15.5). bash has a `coproc`
keyword.

**CSI.** Control Sequence Introducer: `ESC [` (or the single byte
0x9B in 8-bit mode, rarely used). Starts most sequences: cursor
movement, erasing, SGR, modes.

**DA (Device Attributes).** A query (`CSI c`) to which the terminal
answers with its identity and features (B.9).

**Damage tracking.** Redrawing only the parts of the screen that
changed. The job of curses and of multiplexers (31.5).

**Descriptor (file descriptor).** A small integer that indexes the
process's table of open files (2.1). Shared by `fork`, preserved
across `exec` unless close-on-exec.

**Detach.** Leave the programs of a multiplexer running, without a
terminal attached, to reattach later (31.5).

**Device number.** A pair (major, minor) identifying a device: 136
and up for PTY slaves, 4 for the virtual consoles and serial ports, 5
for `/dev/tty` and `/dev/ptmx` (32.3).

**ECMA-48.** The standard for control functions in character sets
(also ISO 6429), the base of the ANSI escape sequences.

**EOF character.** VEOF, `^D` by default. In canonical mode it
delivers the pending line without a newline; on an empty line, the
`read` returns 0, which programs take as end of file (A.5).

**EIO.** The error returned by `read` on a PTY master when the slave
side has been closed by all processes: the usual "the program ended"
signal (chapter 6). Also returned to an orphaned background process
reading its terminal.

**Emulator (terminal emulator).** A program that does the job of a
hardware terminal: it interprets the output of programs into a grid
of cells and draws it, and turns key presses into bytes. xterm,
kitty, foot, Alacritty, WezTerm, Ghostty, GNOME Terminal, Konsole...
It holds the master side of a PTY.

**EPIPE.** The error of a write to a pipe or socket without readers,
along with `SIGPIPE`.

**Escape timeout.** The delay a program waits after receiving ESC to
decide whether it is the Escape key or the start of a sequence (B.8).

**Expect.** Don Libes' Tcl program (1990) that drives interactive
programs through a PTY by waiting for patterns and sending answers;
also the generic name for this technique and its libraries (chapter
30).

**FIFO (named pipe).** A pipe with a name in the file system, created
by `mkfifo`, which unrelated processes can open (3.8).

**Foreground process group.** The process group of a session that
may read from the terminal, and receives the signals of the special
characters. Set with `tcsetpgrp`; read with `tcgetpgrp` (chapter 5).

**fork.** The system call that duplicates the calling process. The
child gets copies of the descriptors, the signal dispositions, the
memory (copy-on-write).

**Hangup.** The loss of the connection to the terminal: the modem
line was dropped, or the PTY master was closed. Causes `SIGHUP` to
the session leader and `EIO` or end of file for readers.

**ICANON, ECHO, ISIG...** Flags of `struct termios` (Appendix A).

**ioctl.** The catch-all system call for device-specific operations,
such as `TIOCGWINSZ` (A.8). termios functions are wrappers around
ioctls on Linux.

**Job.** A shell's name for a pipeline it started, run as one process
group, which can be put in the foreground (`fg`), background (`bg`),
or stopped (`^Z`).

**Job control.** The ability to stop, continue and move jobs between
foreground and background, built on process groups, the foreground
group of the terminal, and the signals SIGTSTP, SIGTTIN, SIGTTOU,
SIGCONT (chapter 5).

**Line discipline.** The kernel module between the terminal driver
and the processes, which implements editing, echo, special
characters and signals: `N_TTY` on Linux (chapter 4). Other line
disciplines exist (for serial protocols like PPP or SLIP), but
terminals use `N_TTY`.

**Line editing (readline).** Editing done by the program itself, in
raw or cbreak mode: cursor movement in the line, history, completion.
GNU readline, libedit, linenoise, and the editors in chapters 18 and
26.

**Master (PTY master, multiplexor).** The side of a PTY held by the
program playing the terminal: what is written to it is input for the
slave, what is read from it is the slave's output. Opened from
`/dev/ptmx` (chapter 6).

**Multiplexer.** A program that runs several programs, each on its own
PTY, in one terminal: screen, tmux, Zellij (chapter 31).

**NativeCall.** Raku's foreign function interface: declare a C
function with `is native` and call it (chapter 17).

**Non-blocking I/O.** With `O_NONBLOCK`, a `read` or `write` that
would wait fails with `EAGAIN` instead. The flag is on the open file
description, so it is shared by every process that shares it (2.8).

**OSC.** Operating System Command: `ESC ]`, for window titles,
colors, clipboard, hyperlinks (B.7).

**Open file description.** The kernel object created by `open`: it
holds the offset and the status flags (such as `O_NONBLOCK`).
Descriptors point to it; `dup` and `fork` share it.

**Orphaned process group.** A process group in which no member has a
parent in another group of the same session: nobody is left to
continue it (typically, after its shell exited). The kernel sends
SIGHUP and SIGCONT to it if it has stopped members.

**Packet mode.** `TIOCPKT` on a PTY master: reads are prefixed with a
status byte (A.8).

**Pipe.** A one-way byte channel in the kernel, with a buffer (64 KiB
by default on Linux) and two descriptors, a read end and a write end
(chapter 3).

**PIPE_BUF.** The size (4096 bytes on Linux) up to which writes to a
pipe are atomic: never interleaved with other writers' (3.3).

**Process group.** A set of processes, identified by the PID of its
leader, that receive terminal signals together: the processes of a
job. Set with `setpgid`.

**PTY (pseudo-terminal).** A pair of devices, master and slave, that
behaves like a terminal connected to a program instead of hardware
(chapter 6).

**Raw mode.** Non-canonical mode with echo, signals and input and
output processing off: the program gets every byte as typed, and
writes bytes that reach the terminal unchanged (A.6).

**Readline.** See *line editing*. Also the GNU library of that name.

**Reaping.** Calling `wait` or `waitpid` for a child that has exited,
which frees its process table entry. Until then it is a *zombie*.

**Scroll region.** A range of lines, set with DECSTBM, to which
scrolling is limited (31.2, B.4).

**Session.** A set of process groups, created by `setsid`, usually
one login or one terminal window, with at most one controlling
terminal. Identified by the PID of its leader (chapter 5).

**Session leader.** The process that created the session; usually
the shell. When it exits, the terminal is disassociated and the
foreground group gets SIGHUP.

**SGR.** Select Graphic Rendition, `CSI ... m`: colors and attributes
(B.5).

**Slave (PTY slave, subsidiary).** The side of a PTY that the program
uses as its terminal: `/dev/pts/N`. Newer documentation says
"subsidiary" or "secondary" or "peer"; this tutorial uses the
traditional terms of the APIs (`ptsname`, `TIOCGPTPEER`...).

**Special characters.** The characters of `c_cc` that the line
discipline interprets: INTR, QUIT, ERASE, KILL, EOF... (A.5).

**splice.** A Linux system call that moves data between a pipe and
another descriptor without copying it through user space (3.11).

**stty.** The command that shows and changes termios settings for its
standard input (4.5, A.7).

**Synchronized output.** Mode `?2026`: the terminal waits for the end
of a frame before painting it (B.6).

**termcap.** The predecessor of terminfo: one text file
(`/etc/termcap`) with two-letter capability names. Still the API of
some programs (`tgetent`), emulated by ncurses.

**terminfo.** The database describing terminals' capabilities and
sequences, compiled by `tic` into `/usr/share/terminfo`, read through
`TERM` (chapter 8, B.12).

**termios.** The POSIX structure and functions to control terminal
settings (Appendix A).

**TERM.** The environment variable naming the terminal type, which
programs use to find its terminfo entry.

**TTY.** Teletypewriter; any terminal device. `/dev/ttyN` are the
virtual consoles, `/dev/ttyS*` the serial ports, `/dev/pts/*` the PTY
slaves, `/dev/tty` the controlling terminal of the process.

**TUI.** Text user interface: a full-screen program in a terminal.

**UTF-8.** The encoding of Unicode used by terminals: 1 to 4 bytes
per code point, ASCII unchanged. Decoders must handle characters cut
between two reads (29.3, 30.6, 31.2).

**VMIN, VTIME.** The non-canonical read conditions (A.5).

**wcwidth.** The function that tells how many columns a character
takes: 0 (combining), 1, or 2 (wide); terminals and programs must
agree on it, or lines are misaligned.

**Window size.** The rows and columns (and optionally pixels) stored
in the terminal (`struct winsize`), set by the emulator with
`TIOCSWINSZ`, read with `TIOCGWINSZ` (chapter 8).

**Zombie.** A process that has exited but has not been reaped by its
parent. `ps` shows it with state `Z` and `<defunct>`.

## Appendix E. Exercises

The exercises are numbered across the whole tutorial, so that the
chapters can refer to them:

- E.1 to E.5: concepts (Part I);
- E.6 to E.11: C;
- E.12 to E.17: Raku;
- E.18 to E.22: Rust;
- E.23 to E.27: Go;
- E.28 to E.36: projects (Part III).

Each one has a statement, hints, and what to check to know that it
works. None of them needs more than the tools of the tutorial. The
difficulty is marked from ★ (an hour) to ★★★ (a weekend).

### Part I: concepts

**E.1 ★ Who holds the pipe?** Run `sleep 100 | sleep 200 &` in an
interactive shell. Using only `/proc` (no `lsof`), find the inode of
the pipe, and list every process that has a descriptor on it, with the
descriptor number and the direction (read or write end).

- Hint: `readlink /proc/PID/fd/N` gives `pipe:[INODE]`; the
  permission bits of the link (`lr-x` or `l-wx`, 32.3) give the
  direction, and so does the `flags` line of `fdinfo`.
- Check: you find exactly two descriptors, unless your shell leaked
  one (32.3).

**E.2 ★ Measure the pipe.** Write a shell pipeline (no C) that
measures the capacity of a pipe: a writer that writes one byte at a
time and reports how many it wrote, and a reader that never reads.
Then change the capacity with Python's `fcntl.F_SETPIPE_SZ` and check
that the measurement follows. Compare with `pipe_capacity.c` (3.7).

- Hint: `dd if=/dev/zero bs=1 count=1000000 status=progress | sleep
  10` shows the progress stopping. Where?
- Check: 65536 bytes by default on Linux. The maximum is in
  `/proc/sys/fs/pipe-max-size`.

**E.3 ★ The line discipline by hand.** In a terminal, run `stty -icanon
min 3 time 20; cat -v; stty sane`, type one character and wait, then
type three characters quickly. Explain what you see with the VMIN and
VTIME table of A.5. Then try `min 0 time 20`, and `min 0 time 0`.

- Check: with `min 0 time 0`, `cat` exits at once. Why? (`read`
  returns 0, which `cat` takes as end of file.)

**E.4 ★★ Job control by hand.** Without using `&`, `fg` or `bg`,
reproduce job control from a C or Python program: start `cat` in a new
process group, make it the foreground group of the terminal, wait
until it is stopped by `^Z` (`waitpid` with `WUNTRACED`), take the
terminal back, print "stopped", wait for a key, give the terminal
back and send `SIGCONT`.

- Hint: you will be stopped by `SIGTTOU` when calling `tcsetpgrp`
  from the background. That is chapter 5's lesson; chapter 13 has the
  answer.
- Check: `cat` echoes lines again after the continuation.

**E.5 ★★ Escape sequence explorer.** Write a program (any language)
that reads its standard input (or a file) and prints every escape
sequence it finds on its own line, with its name from Appendix B
(CUP, SGR, ED, DECSET...) and its parameters decoded: `CSI 1;31 m` →
`SGR bold, fg red`. Run it on the output of `ls --color=always`, on a
`script` log of a `vim` session, and on `tput` output.

- Hint: the state machine of 31.2 is all you need for the parsing.
  Raku users may use `Terminal::ANSIParser` (18.4).
- Check: every byte of the input is accounted for, either as text or
  inside a sequence.

### C

**E.6 ★ stdout and stderr separately (10.7).** Complete the loop of
10.7 into a program `capture CMD ARGS...` that runs a command with
two pipes, one for its standard output and one for its standard
error, reads both with `poll` until both are closed, then prints:

```text
exit status 1
stdout: 2 lines, 23 bytes
stderr: 1 line, 31 bytes
--- stderr ---
ls: cannot access 'x': No such file or directory
```

- Hint: close the write ends in the parent before the loop, or the
  loop never ends (3.6). Mark the read ends close-on-exec.
- Check: `capture sh -c 'yes | head -c 1000000; yes err | head -c
  1000000 >&2'` finishes, with 1 000 000 bytes on each side. A
  version that reads stdout to the end, then stderr, deadlocks on it:
  try it, and explain why.

**E.7 ★ Redirections for minishell.** Add `< file`, `> file` and `>>
file` to `minishell` (chapter 13), for every command of a pipeline
(only the first may have `<` and only the last `>`, but check that).

- Hint: open the files in the child, after `fork` and before `exec`,
  and `dup2` them over 0 or 1. Opening them in the parent works too,
  but then they must be closed in the parent and marked
  close-on-exec.
- Check: `ls | sort -r > out` then `cat < out`. And a missing file
  must give an error message without killing the shell.

**E.8 ★★ Timing for ptyscript.** Make `ptyscript` write a timing file,
in the format of `script -T` (`advanced` format, 29.6): for each
chunk of output, a line `O delay length`, and `I delay length` for
input, plus the `H` header lines of the original if you like.

- Hint: `clock_gettime(CLOCK_MONOTONIC)` before each write; delays in
  seconds with 6 decimals.
- Check: `scriptreplay --log-out typescript --log-timing timing`
  (from util-linux) replays your recording.

**E.9 ★★ ptyreplay.** Write `ptyreplay TIMING TYPESCRIPT [SPEED]`,
which replays a recording made by E.8 (or by `script -T`) at its
original pace, or faster. Add a maximum pause (like `-i` of
`ptyplay`, 29.8).

- Hint: read the timing lines one by one; for each, sleep, then copy
  `length` bytes of the typescript to standard output.
- Check: the output is byte for byte the typescript (`cmp` on a
  redirected output).

**E.10 ★★ epoll and signalfd.** Rewrite the main loop of `ptyscript`
with `epoll` instead of `poll`, and `signalfd` instead of the
SIGWINCH handler and the self-pipe: block SIGWINCH and SIGCHLD with
`sigprocmask`, create a `signalfd` for them, and add it to the epoll
set. When SIGCHLD arrives, reap the child.

- Hint: block the signals **before** creating the child, and unblock
  them in the child before `exec` (the mask is inherited
  across `fork` and `exec`, C.3): a shell started with SIGCHLD blocked misbehaves.
- Check: resizing the window still works; `ptyscript` exits when the
  child exits even if the child left a grandchild holding the slave
  open (`sh -c 'trap "" HUP; sleep 100 & exit'`): with `poll` on the
  master only, it would wait 100 seconds. Why is the `trap` needed?
  Which behavior is right?

**E.11 ★★ Keys split across reads.** `rawkeys` (chapter 11) decodes
the keys in each `read`, but a sequence can arrive in two reads
(over a slow `ssh`, or when keys are pasted). Make it keep an
incomplete sequence between reads, and decide that a lone ESC is the
Escape key if nothing follows within 50 ms.

- Hint: use `poll` with a 50 ms timeout when the buffer ends with an
  incomplete sequence, and an infinite timeout otherwise. B.8 lists
  the forms to recognize.
- Check: drive it with a PTY driver (chapter 30) that sends `\e`,
  waits 10 ms, sends `[A`: it must print Up. With 100 ms between the
  two: Escape, then `[`, then `A`.

### Raku

**E.12 ★ A tee with supplies.** Write `rtee.raku FILE CMD...`: run a
command with `Proc::Async`, copy its standard output to both your
standard output and `FILE`, and its standard error to your standard
error prefixed by `[err] `. End with the command's exit code.

- Hint: `$proc.stdout(:bin)` and `$proc.stderr` are supplies; use a
  `react` block with two `whenever`s and one for `$proc.start`.
- Check: `rtee out.txt sh -c 'echo a; echo b >&2; exit 3'` prints
  both lines, `out.txt` has `a`, and `$?` is 3.

**E.13 ★★ A Raku player.** Write `rplay.raku FILE.cast` that plays an
asciicast v2 recording (29.6), like `ptyplay`, with the `-s` (speed)
and `-i` (max idle) options. Use `from-json` from the JSON::Fast
module for the lines (the built-in one is deprecated). Then
make it able to replay a `script -T` recording as well (E.8), choosing
the format from the first line.

- Hint: `sleep` takes fractional seconds. Use `$*OUT.write($str.encode)`
  with `$*OUT.flush`, or set `$*OUT.out-buffer = False`.
- Check: replay a recording of `ptyrec` (29.7) and of `script -T`;
  compare with `ptyplay` playing the same file.

**E.14 ★ Unicode at the terminal.** Write a Raku program that reads
lines from the terminal in canonical mode and prints, for each line,
its number of bytes, code points, graphemes (`.chars`), and terminal
columns. Test it with `é`, `e` + U+0301, `👍🏽`, `漢字`, and a tab.

- Hint: there is no `wcwidth` in core; NativeCall to the C library's
  `wcwidth` (after `setlocale`, which needs NativeCall too), or a
  table of East Asian Width ranges.
- Check: `"👍🏽"` is 8 bytes, 2 code points and 1 grapheme. glibc's
  `wcwidth` gives 2 + 2 = 4 columns, while a terminal that handles
  grapheme clusters draws it in 2. Compare the columns with what your
  terminal shows: they disagree sometimes, and that is the point of
  the exercise.

**E.15 ★★ A pager.** Write a minimal `less` in Raku: read a file,
switch to the alternate screen and raw mode with `Term::termios`, show
one screen, and handle Space, `b`, `j`, `k`, `q`, and the arrow keys.
Handle SIGWINCH by redrawing.

- Hint: `Terminal::ANSI` for the cursor movements; restore the
  terminal in a `LEAVE` phaser and on `SIGINT` (even though `isig` is
  off, a `kill -INT` can arrive).
- Check: the shell session reappears unchanged after `q`; `kill
  -TERM` restores the terminal too.

**E.16 ★★ `expect-any` and `interact` for Expect.rakumod.** Add to the
`Expect` class of chapter 30:

- `expect-any(*@regexes --> Pair)`: wait until one of the patterns
  matches, and return the index of the pattern and the `Match`. If
  several match, the one that matches **earliest in the text** wins,
  as in the Rust version (30.4), not the first of the list;
- `interact(:$escape = "\x1d")`: give the terminal to the user, in raw
  mode, relaying keys to the program and its output to the screen,
  until the escape key or the end of the program.

- Hint: for the earliest match, try all the patterns and keep the
  match with the smallest `.from`. For `interact`, a `react` block
  with `whenever` on the keyboard (`$*IN.Supply(:bin)` after raw mode,
  or the `Tty` module's poll) and on the output channel.
- Check: the `password` and `interact` scenarios of 30.5, translated
  to Raku.

**E.17 ★★★ A C helper for spawning on a PTY.** Replace the
`setsid -c` trick of 17.1 (solution 1) with solution 2: a small C
library, `libspawnpty.so`, with a function
`int spawn_on_pty(const char *path, char **argv, int slave)` that
forks, and in the child calls `setsid`, `ioctl(slave, TIOCSCTTY, 0)`,
`dup2`s the slave and `execvp`s; call it from Raku with NativeCall.

- Hint: the child must use only async-signal-safe functions between
  `fork` and `exec`, because MoarVM is multithreaded: no `malloc`, no
  `printf`. Prepare `argv` in the parent. Passing a `CArray[Str]`
  from Raku gives a `char **`. Build with `gcc -shared -fPIC`.
- Check: `Pty.spawn` with the new helper runs `bash`, and job control
  works in it (`sleep 10`, `^Z`, `fg`).

### Rust

**E.18 ★★ A relay that never blocks (22.2).** The relay of `ptyscript`
writes keyboard input to the master with a blocking `write_all`: if the
program does not read its input and the PTY's input buffer is full,
the relay blocks and stops copying the output too. Make the master
non-blocking, keep a queue of pending input, and poll for `POLLOUT`
on the master only when the queue is not empty.

- Hint: `nix::fcntl::fcntl(fd, F_SETFL(OFlag::O_NONBLOCK))`, a
  `VecDeque<u8>`, and `ErrorKind::WouldBlock` on write. Then think
  about `^C`: it is now in the queue, behind the paste.
- Check: run `sleep 30` in it and paste 100 KiB of text: the output
  (nothing) and `^C` must still work. Without the fix, `^C` is stuck
  behind the paste.

**E.19 ★ `isatty` everywhere.** Write `ttyinfo2`, which prints for
each of the descriptors 0, 1, 2 whether it is a terminal
(`std::io::IsTerminal`), and if so its name (`nix::unistd::ttyname`),
size, and the foreground process group; and otherwise what it is
(pipe, file, socket, `/dev/null`), using `fstat`.

- Check: `ttyinfo2 < /dev/null | cat 2>&1` reports a character
  device that is not a terminal, a pipe, and a pipe.

**E.20 ★★ A pipeline builder.** Write `pipe!` (or a function
`pipeline(&[&[&str]])`) that runs `N` commands connected by pipes, as
a shell does, using `std::process::Command` and `Stdio::from` with
the child's `ChildStdout`. Then make it report the exit status of
every command, like bash's `PIPESTATUS`.

- Hint: 20.2 shows two commands. Keep the `Child`s in a `Vec` and
  `wait` them all, in order.
- Check: `false | true | sh -c 'exit 3'` reports 1, 0, 3.

**E.21 ★★ Async relay.** Rewrite `ptyscript` with Tokio: wrap the
master in `tokio::io::unix::AsyncFd`, use `tokio::signal::unix` for
SIGWINCH, and `tokio::select!` in the main loop. Compare the code
size and the binary size with the `poll` version.

- Hint: the master must be non-blocking for `AsyncFd`. Standard input
  in raw mode can be read with `tokio::io::stdin()` (which uses a
  thread) or another `AsyncFd`.
- Check: same behavior as the `poll` version, including the exit
  status and the restoration of the terminal.

**E.22 ★★ A ratatui log viewer.** Write a ratatui program that runs a
command and shows its output in a scrolling list, with stdout lines
in the default color and stderr lines in red, and a status line with
the number of lines and the exit status when the command ends.
Scroll with the arrow keys and PageUp/PageDown.

- Hint: two reader threads sending lines on an `mpsc` channel; the
  main loop polls crossterm events with a timeout and drains the
  channel (23.3 has the structure).
- Check: `cargo run -- sh -c 'for i in $(seq 500); do echo $i; echo
  err$i >&2; done'`: 1000 lines, interleaved, colored.

### Go

**E.23 ★ The exit status, precisely.** Write a Go program `status CMD
ARGS...` that runs a command and prints how it ended: exit code,
or signal name and whether it dumped core, using
`(*exec.ExitError).Sys().(syscall.WaitStatus)`.

- Check: `status sh -c 'kill -SEGV $$'` says `signal: segmentation
  fault (core dumped)` or without core depending on `ulimit -c`.

**E.24 ★★ Cancel a blocked read.** Write a Go program that reads
standard input in a goroutine and stops after 3 seconds without
input, **without** leaving the goroutine blocked. Do it three ways:
(a) `os.Stdin.SetReadDeadline` (and explain the error you get);
(b) a non-blocking duplicate of the descriptor wrapped with
`os.NewFile`; (c) `poll` on the descriptor with
`golang.org/x/sys/unix` before each `read`.

- Hint: 27.2 has the answers for (a) and (b). For (b), observe that
  setting `O_NONBLOCK` on the duplicate changes the original too, and
  what that means for the shell after the program exits (2.8).
- Check: after the program, `cat` still works in the same terminal.
  If it gets `EAGAIN`, (b) left the terminal non-blocking: restore it.

**E.25 ★★ A Bubble Tea process monitor.** Write a Bubble Tea program
that lists the processes of the current terminal (those whose
`/proc/PID/stat` has your `tty_nr`, 32.3), with PID, PGID, state, and
command, refreshed every second; mark the foreground group; and lets
you send SIGCONT, SIGSTOP or SIGTERM to the selected one with keys.

- Hint: `tea.Tick` for the refresh, `bubbles/table` for the list.
- Check: start `sleep 1000 &` in the terminal, run the monitor, stop
  and continue `sleep` from it, and see the state change in `jobs`.

**E.26 ★★ A Wish quiz.** Make a Wish SSH server (28.4) that serves a
small Bubble Tea quiz, and shows each client's terminal type, size and
whether it supports colors (from the `ssh.Pty` request). Connect with
two `ssh` clients of different sizes and resize them.

- Check: each client sees its own size, and resizing updates it.
  Watch for the race on the window-change channel mentioned in the
  final notes of this tutorial: does a resize arriving just after the
  start get lost?

**E.27 ★★★ A PTY recorder in Go.** Port `ptyrec` (29.7) to Go with
creack/pty: same command line, same asciicast output, `-i` for input
recording, `"r"` events on resize. Use one goroutine per direction
and one for signals, and a single goroutine that writes the file
(fed by a channel), so that the events are in order.

- Hint: remember 27.1: set the master non-blocking, or closing it
  will not wake the reader.
- Check: `ptyplay` (Rust) plays the Go recordings, and vice versa.

### Projects

**E.28 ★ Markers in ptyrec.** Add a key to `ptyrec`: when the user
types `^]` followed by `m`, record a marker event `[t, "m", ""]`
(asciicast v2 supports `"m"` events) instead of sending the keys to
the program; `^]` twice sends one `^]`. Make `ptyplay` stop at
markers when given `-m`, and continue on a key press.

- Hint: the same prefix logic as `muxi` (31.3), including a prefix
  split between two reads.
- Check: the marker appears in the file; `ptyplay -m` pauses there.

**E.29 ★★★ Wide characters in muxi.** Make `muxi`'s emulator handle
characters of width 2: store the character in the first cell and a
continuation marker in the second; wrap before a wide character that
does not fit in the last column; when one half of a wide character is
overwritten, erase the other half. Use `github.com/mattn/go-runewidth`
or `golang.org/x/text/width` for the widths.

- Check: `echo 漢字テスト` in a pane is aligned with the status line;
  `vim` on a file with Japanese text scrolls without garbage.

**E.30 ★★ Scrollback in muxi.** Keep the lines that scroll off the top
of the main screen (not the alternate screen) in a ring buffer of
1000 lines per pane, and add a copy mode: `^B [` shows the history
with PageUp/PageDown, `q` leaves it.

- Hint: the scroll function of `vt.go` is the only place where lines
  leave the screen; only full-screen scrolls (region = whole screen)
  should feed the history, as in tmux.
- Check: `seq 2000` then `^B [`: you can go back to 1001.

**E.31 ★★★ Detaching muxi.** Split `muxi` into a server and a client,
like tmux (31.5): the server owns the PTYs and the screens and listens
on a Unix-domain socket in `$XDG_RUNTIME_DIR`; the client puts the
terminal in raw mode, connects, and relays keys to the server and
screen updates to the terminal; `^B d` detaches (the client exits,
the server keeps running), and `muxi attach` starts a new client.

- Hint: the simplest protocol: the client sends its window size then
  raw keys; the server sends rendered frames (the output of `render`).
  The tmux way is better but harder: pass the terminal descriptor
  itself with `SCM_RIGHTS` (`unix.UnixRights` in Go) and let the
  server write to it.
- Check: start `top` in a pane, detach, close the terminal, open
  another one, attach: `top` is still running, at the new size.

**E.32 ★★ A test harness.** Using `drive` (Rust) or `Expect.rakumod`,
write tests for `minishell` (chapter 13): job control (^Z, `fg`,
`bg`, `jobs`), a pipeline, a command not found, `exit` with a status,
and `^C` on a long pipeline (both commands must die). Run them in a
loop 100 times and fix the timing races they reveal (30.5).

- Check: 100 green runs out of 100.

**E.33 ★★ Expect in Go.** Rewrite the Rust `drive` program (chapter 30)
in Go, with the three scenarios, using `regexp` and a goroutine
reading the master into a buffer protected by a mutex, signalled with
a condition variable or a channel.

- Check: the outputs of the three scenarios are the same as in 30.5.

**E.34 ★★ ttylog with strace precision.** `ttylog` (32.5) polls the
modes every 100 ms and can miss quick changes. Use packet mode
(`TIOCPKT`, A.8) with the `TIOCPKT_IOCTL` bit (Linux: set when the
slave's termios changes, if `EXTPROC` is on) to be told of every
change instead. Find out from the kernel source (`drivers/tty/pty.c`
and `n_tty.c`) exactly when this bit is set, and whether it is
enough.

- Check: compare the logs of a `vim` session with and without the
  change. This is a research exercise: the answer may be "not
  without EXTPROC", and that is an acceptable result if you can show
  why.

**E.35 ★★ A terminal emulator in a window.** Take `vt.go` from `muxi`
and draw its screen in a graphical window instead of a terminal (with
Ebitengine, Gio or SDL), with a fixed-width font. Start a shell on a
PTY, map key presses to bytes (B.8), and handle resizing. You have
written a terminal emulator.

- Check: `vim`, `htop` and `muxi` run in it.

**E.36 ★★★ The same program four times.** Pick one program of this
tutorial that exists in only one or two languages (`ttylog`, `muxi`,
`drive`), and write it in the other languages. Measure as in 29.5:
lines of code, binary size, start-up time, memory. Do the results
change the conclusions of chapter 33?

### Selected solutions

Seventeen exercises are solved below, at least two per language,
plus two in plain shell. E.9 comes after E.8 and E.10 because it
replays their recordings. Each was compiled and run on the machine
of this tutorial. The outputs shown are real.

#### E.1 in sh: `whopipe.sh`

The script starts from one descriptor known to be on the pipe and
reads its link, `pipe:[INODE]`. It then reads the links of every
descriptor of every process and keeps those that are equal. The
direction comes from the `flags` line of `fdinfo`. The flags are in
octal, and their last digit is the access mode: 0 for read, 1 for
write, 2 for both.

```sh
# file: sh/whopipe.sh
# E.1: list every descriptor, in every process, on the pipe that
# PID's descriptor FD is (default: the stdout of PID).
#   sh whopipe.sh PID [FD]
pid=$1 fd=${2:-1}
link=$(readlink /proc/$pid/fd/$fd) || exit 1
case $link in pipe:*) ;; *) echo "$link is not a pipe" >&2; exit 1 ;; esac
echo "$link"
for d in /proc/[0-9]*/fd/*; do
  [ "$(readlink "$d" 2>/dev/null)" = "$link" ] || continue
  p=${d#/proc/} p=${p%%/*} n=${d##*/}
  flags=$(awk '/^flags/ { print $2 }' /proc/$p/fdinfo/$n 2>/dev/null)
  case $flags in *1) dir=write ;; *2) dir=both ;; *) dir=read ;; esac
  printf '  pid %-8s fd %-3s %s  flags %s  %-5s  %s\n' "$p" "$n" \
    "$(stat -c %A "$d")" "$flags" "$dir" "$(tr '\0' ' ' < /proc/$p/cmdline)"
done
```

Run in an interactive bash, on a PTY:

```console
$ sleep 100 | sleep 200 &
[1] 1225692
$ sleep 0.2; sh whopipe.sh $(pgrep -fx 'sleep 100')
pipe:[20606139]
  pid 1225691  fd 1   l-wx------  flags 01  write  sleep 100
  pid 1225692  fd 0   lr-x------  flags 00  read   sleep 200
$ kill %1
```

There are exactly two descriptors. bash closed its own copies of both
ends after the two `fork`s, as a shell must: an open write end in
the shell would keep `sleep 200` from ever seeing the end of file.
The `sleep 0.2` gives the children time to `exec`. Before that,
they are still copies of bash, and `pgrep -fx 'sleep 100'` finds
nothing. The permission bits
of the link (`l-wx`, `lr-x`) show the same thing as the flags.
`readlink` on another user's process fails, so as a normal user the
scan only sees your own processes. That is enough here.

#### E.2 in sh: measuring the pipe

`dd` with `bs=1` writes one byte per `write`. `sleep` never reads.
`dd` stops in a `write` once the pipe is full. `timeout -s INT`
interrupts it, and GNU `dd` prints its counters when it gets SIGINT:

```console
$ timeout -s INT 1 dd if=/dev/zero bs=1 count=2000000 | sleep 2
65537+0 records in
65536+0 records out
65536 bytes (66 kB, 64 KiB) copied, 0.995503 s, 65.8 kB/s
```

That is 65,536 bytes, as `pipe_capacity.c` found (3.7). One more
record was read than written: the 65,537th byte is the one `dd` was
trying to write when the signal came.

The hint suggested `status=progress`, but it does not help. With
`status=progress` and a 3.5 s timeout, `dd` printed no progress line
at all, only the same three final lines. The first update is due
after one second, `dd` checks for it between copies, and by then it
is already stuck in the blocked `write`. The SIGINT statistics are
exact.

To change the capacity, the writer must call `fcntl` on its own
standard output before it starts writing. A small Python prefix does
that, then becomes `dd` with `exec`. The descriptor, and the pipe,
stay the same:

```console
$ python3 -c '
import fcntl, os, sys
n = fcntl.fcntl(1, fcntl.F_SETPIPE_SZ, int(sys.argv[1]))
print("capacity", n, file=sys.stderr)
os.execvp("timeout", ["timeout", "-s", "INT", "2",
                      "dd", "if=/dev/zero", "bs=1", "count=2000000"])
' 1048576 | sleep 3
capacity 1048576
1048577+0 records in
1048576+0 records out
1048576 bytes (1.0 MB, 1.0 MiB) copied, 1.99979 s, 524 kB/s
```

With 4096 the measurement gives 4096 bytes. The kernel rounds a
request up to a power of two number of pages: 1000 gives 4096, and
100,000 gives 131,072. Above `/proc/sys/fs/pipe-max-size` (1,048,576
here), an unprivileged process gets `EPERM`. A request of 2,000,000
failed with `PermissionError: [Errno 1] Operation not permitted`.

#### E.6 in C: `capture`

```c
// file: c/capture.c
/*
 * capture: run a command, collect its stdout and stderr separately
 * (two pipes, one poll loop), then report. Solution of exercise E.6.
 * Usage: capture CMD [ARGS...]
 */
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <poll.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/wait.h>
#include <unistd.h>

struct buf { char *data; size_t len, cap; };

static void append(struct buf *b, const char *p, size_t n)
{
    if (b->len + n > b->cap) {
        b->cap = (b->len + n) * 2;
        b->data = realloc(b->data, b->cap);
        if (!b->data) { perror("realloc"); exit(1); }
    }
    memcpy(b->data + b->len, p, n);
    b->len += n;
}

static size_t count_lines(const struct buf *b)
{
    size_t n = 0;
    for (size_t i = 0; i < b->len; i++) n += b->data[i] == '\n';
    return n;
}

int main(int argc, char **argv)
{
    if (argc < 2) {
        fprintf(stderr, "usage: capture CMD [ARGS...]\n");
        return 2;
    }
    int out[2], err[2];
    if (pipe2(out, O_CLOEXEC) == -1 || pipe2(err, O_CLOEXEC) == -1) {
        perror("pipe2"); return 1;
    }
    pid_t pid = fork();
    if (pid == -1) { perror("fork"); return 1; }
    if (pid == 0) {
        /* dup2 clears close-on-exec on the new descriptors 1 and 2;
         * the original pipe descriptors are closed by exec. */
        dup2(out[1], 1);
        dup2(err[1], 2);
        execvp(argv[1], &argv[1]);
        dprintf(2, "capture: %s: %s\n", argv[1], strerror(errno));
        _exit(127);
    }
    close(out[1]);   /* without these two closes, the loop never ends */
    close(err[1]);

    struct buf bufs[2] = { 0 };
    struct pollfd pf[2] = {
        { .fd = out[0], .events = POLLIN },
        { .fd = err[0], .events = POLLIN },
    };
    int open_count = 2;
    char chunk[65536];
    while (open_count > 0) {
        if (poll(pf, 2, -1) == -1) {
            if (errno == EINTR) continue;
            perror("poll"); return 1;
        }
        for (int i = 0; i < 2; i++) {
            if (pf[i].fd == -1 || !(pf[i].revents & (POLLIN | POLLHUP)))
                continue;
            ssize_t n = read(pf[i].fd, chunk, sizeof chunk);
            if (n <= 0) { close(pf[i].fd); pf[i].fd = -1; open_count--; }
            else append(&bufs[i], chunk, (size_t)n);
        }
    }
    int status;
    waitpid(pid, &status, 0);
    if (WIFEXITED(status)) printf("exit status %d\n", WEXITSTATUS(status));
    else printf("killed by signal %d\n", WTERMSIG(status));
    for (int i = 0; i < 2; i++) {
        size_t n = count_lines(&bufs[i]);
        printf("%s: %zu line%s, %zu bytes\n", i ? "stderr" : "stdout",
               n, n == 1 ? "" : "s", bufs[i].len);
    }
    if (bufs[1].len > 0 && bufs[1].len <= 4096) {
        printf("--- stderr ---\n");
        fwrite(bufs[1].data, 1, bufs[1].len, stdout);
    }
    return 0;
}
```

```console
$ gcc -Wall -Wextra -O2 -o capture capture.c
$ ./capture ls -d / x
exit status 2
stdout: 1 line, 2 bytes
stderr: 1 line, 49 bytes
--- stderr ---
ls: cannot access 'x': No such file or directory
$ ./capture sh -c 'yes | head -c 1000000; yes err | head -c 1000000 >&2'
exit status 0
stdout: 500000 lines, 1000000 bytes
stderr: 250000 lines, 1000000 bytes
$ ./capture nosuchcmd
exit status 127
stdout: 0 lines, 0 bytes
stderr: 1 line, 46 bytes
--- stderr ---
capture: nosuchcmd: No such file or directory
```

The second command is the one that matters. A simpler version reads
standard output to the end, and only then reads standard error:

```c
while ((n = read(out[0], chunk, sizeof chunk)) > 0) append(&bufs[0], chunk, n);
while ((n = read(err[0], chunk, sizeof chunk)) > 0) append(&bufs[1], chunk, n);
```

That version hangs on the second command. `timeout 5` kills it, with
status 124. The child fills the stderr pipe (64 KiB, 3.7) and blocks
in `write`. It never closes its stdout, so the parent waits for an
end of file that never comes: the deadlock of 10.7. The
`poll` loop reads whichever pipe has data, so neither pipe can fill
up.

Three details:

- The two `close` calls after `fork` are needed. Without them, the
  parent itself holds the write ends, and `read` never returns 0.
- `pipe2(..., O_CLOEXEC)` makes `exec` close the original pipe
  descriptors in the child. `dup2` clears the flag on 1 and 2.
- When `exec` fails, the child writes its own error message and
  exits with 127, as a shell does. The parent does not need a
  separate channel to learn about the failure. (`posix_spawn` and
  Go's `os/exec` do use one: a close-on-exec pipe that stays silent
  if `exec` succeeds.)

#### E.8 and E.10 in C: `ptyscript2`

One program answers both exercises: `ptyscript` rewritten around
`epoll` and `signalfd`, writing a timing file as well.

```c
// file: c/ptyscript2.c
/*
 * ptyscript2: ptyscript with epoll and signalfd instead of poll and
 * a self-pipe (exercise E.10), which also writes a timing file in the
 * "advanced" format of script -T (exercise E.8).
 *   ptyscript2 [-o typescript] [-t timing] [cmd args...]
 *   scriptreplay --log-out typescript --log-timing timing
 * It stops when the child exits, even if a grandchild keeps the PTY.
 */
#define _GNU_SOURCE
#include "ptyopen.h"
#include <errno.h>
#include <fcntl.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/epoll.h>
#include <sys/ioctl.h>
#include <sys/signalfd.h>
#include <sys/wait.h>
#include <termios.h>
#include <time.h>
#include <unistd.h>

static struct termios saved_tty;
static int tty_raw;

static void restore_tty(void)
{
    if (tty_raw) {
        tcsetattr(STDIN_FILENO, TCSAFLUSH, &saved_tty);
        tty_raw = 0;
    }
}

static int write_all(int fd, const char *p, size_t n)
{
    while (n > 0) {
        ssize_t w = write(fd, p, n);
        if (w == -1 && errno == EINTR) continue;
        if (w == -1) return -1;
        p += w;
        n -= (size_t)w;
    }
    return 0;
}

/* ---- timing file (E.8) ---------------------------------------- */

static FILE *timing;
static struct timespec last;            /* time of the previous entry */

static double since_last(void)
{
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    double d = (double)(t.tv_sec - last.tv_sec)
             + (double)(t.tv_nsec - last.tv_nsec) / 1e9;
    last = t;
    return d;
}

/* One line per chunk: stream (O or I), delay since the previous line
 * of any stream, length in bytes. */
static void timing_entry(char stream, size_t len)
{
    if (timing) fprintf(timing, "%c %.6f %zu\n", stream, since_last(), len);
}

/* Header lines: H delay NAME value. scriptreplay ignores those it
 * does not need, but they document the recording. */
static void timing_header(const char *name, const char *value)
{
    if (timing) fprintf(timing, "H %.6f %s %s\n", 0.0, name, value);
}

/* ---- main ------------------------------------------------------- */

static void copy_output(int master, int log)
{
    char buf[8192];
    ssize_t n = read(master, buf, sizeof buf);
    if (n <= 0) return;
    timing_entry('O', (size_t)n);
    write_all(STDOUT_FILENO, buf, (size_t)n);
    write_all(log, buf, (size_t)n);
}

int main(int argc, char **argv)
{
    const char *logname = "typescript", *timingname = NULL;
    int opt;
    while ((opt = getopt(argc, argv, "+o:t:")) != -1) {
        if (opt == 'o') logname = optarg;
        else if (opt == 't') timingname = optarg;
        else {
            fprintf(stderr, "usage: %s [-o log] [-t timing] [cmd...]\n",
                    argv[0]);
            return 2;
        }
    }
    char *shell = getenv("SHELL");
    char *dflt[] = { shell ? shell : "/bin/sh", NULL };
    char **cmd = optind < argc ? &argv[optind] : dflt;

    int is_tty = isatty(STDIN_FILENO);
    struct winsize ws = { .ws_row = 24, .ws_col = 80 };
    if (is_tty) {
        tcgetattr(STDIN_FILENO, &saved_tty);
        ioctl(STDIN_FILENO, TIOCGWINSZ, &ws);
    }

    int log = open(logname, O_WRONLY | O_CREAT | O_TRUNC | O_CLOEXEC, 0644);
    if (log == -1) { perror(logname); return 1; }
    time_t now = time(NULL);
    char date[64];
    strftime(date, sizeof date, "%Y-%m-%d %H:%M:%S%z", localtime(&now));
    dprintf(log, "Script started on %s [COMMAND=\"%s\"]\n", date, cmd[0]);
    if (timingname) {
        timing = fopen(timingname, "we");
        if (!timing) { perror(timingname); return 1; }
        clock_gettime(CLOCK_MONOTONIC, &last);
        timing_header("START_TIME", date);
        timing_header("COMMAND", cmd[0]);
        timing_header("TIMING_LOG", timingname);
        timing_header("OUTPUT_LOG", logname);
        char size[32];
        snprintf(size, sizeof size, "%d", ws.ws_col);
        timing_header("COLUMNS", size);
        snprintf(size, sizeof size, "%d", ws.ws_row);
        timing_header("LINES", size);
    }

    int master;
    pid_t child = pty_spawn(cmd, is_tty ? &saved_tty : NULL, &ws, &master);
    if (child == -1) { perror("pty_spawn"); return 1; }

    /* Block the signals and receive them on a descriptor. We block
     * them after the fork, so the child starts with a normal mask.
     * A SIGCHLD sent before sigprocmask is lost (its default action
     * is to ignore it): the waitpid below catches that case. */
    sigset_t mask;
    sigemptyset(&mask);
    sigaddset(&mask, SIGCHLD);
    sigaddset(&mask, SIGWINCH);
    sigaddset(&mask, SIGTERM);
    sigaddset(&mask, SIGHUP);
    sigprocmask(SIG_BLOCK, &mask, NULL);
    int sfd = signalfd(-1, &mask, SFD_CLOEXEC);
    if (sfd == -1) { perror("signalfd"); return 1; }

    int status = 0, done = waitpid(child, &status, WNOHANG) == child;

    if (is_tty) {
        struct termios raw = saved_tty;
        cfmakeraw(&raw);
        tcsetattr(STDIN_FILENO, TCSAFLUSH, &raw);
        tty_raw = 1;
        atexit(restore_tty);
    }

    int ep = epoll_create1(EPOLL_CLOEXEC);
    struct epoll_event ev = { .events = EPOLLIN };
    ev.data.fd = STDIN_FILENO;
    /* EPERM: a regular file cannot be in an epoll set. Then read it
     * all at once (only when stdin is not a terminal, of course). */
    int stdin_polled = epoll_ctl(ep, EPOLL_CTL_ADD, STDIN_FILENO, &ev) == 0;
    ev.data.fd = master;
    epoll_ctl(ep, EPOLL_CTL_ADD, master, &ev);
    ev.data.fd = sfd;
    epoll_ctl(ep, EPOLL_CTL_ADD, sfd, &ev);

    char buf[8192];
    int stdin_open = 1;
    while (!done) {
        if (!stdin_polled && stdin_open) {      /* a file: copy it */
            ssize_t n;
            while ((n = read(STDIN_FILENO, buf, sizeof buf)) > 0) {
                timing_entry('I', (size_t)n);
                write_all(master, buf, (size_t)n);
            }
            write_all(master, "\x04", 1);      /* ^D: end of input */
            stdin_open = 0;
        }
        struct epoll_event evs[4];
        int n = epoll_wait(ep, evs, 4, -1);
        if (n == -1 && errno == EINTR) continue;
        if (n == -1) { perror("epoll_wait"); break; }

        for (int i = 0; i < n; i++) {
            int fd = evs[i].data.fd;
            if (fd == sfd) {
                struct signalfd_siginfo si;
                while (read(sfd, &si, sizeof si) == sizeof si) {
                    if (si.ssi_signo == SIGWINCH && is_tty) {
                        struct winsize w;
                        if (ioctl(STDIN_FILENO, TIOCGWINSZ, &w) == 0)
                            ioctl(master, TIOCSWINSZ, &w);
                    } else if (si.ssi_signo == SIGCHLD) {
                        /* Several SIGCHLDs can merge into one: reap
                         * with WNOHANG, never assume one per child. */
                        if (waitpid(child, &status, WNOHANG) == child)
                            done = 1;
                    } else if (si.ssi_signo == SIGTERM
                               || si.ssi_signo == SIGHUP) {
                        kill(child, SIGHUP);
                    }
                    if (done) break;
                }
            } else if (fd == STDIN_FILENO) {
                ssize_t r = read(STDIN_FILENO, buf, sizeof buf);
                if (r > 0) {
                    timing_entry('I', (size_t)r);
                    write_all(master, buf, (size_t)r);
                } else {
                    epoll_ctl(ep, EPOLL_CTL_DEL, STDIN_FILENO, NULL);
                    if (!is_tty) write_all(master, "\x04", 1);
                }
            } else if (fd == master) {
                if (evs[i].events & EPOLLIN) {
                    copy_output(master, log);
                } else if (evs[i].events & EPOLLHUP) {
                    /* Nobody has the slave open any more. */
                    epoll_ctl(ep, EPOLL_CTL_DEL, master, NULL);
                }
            }
        }
    }

    /* The child is gone. Copy what it wrote before exiting, without
     * waiting for a grandchild that may hold the slave forever. */
    fcntl(master, F_SETFL, fcntl(master, F_GETFL) | O_NONBLOCK);
    for (;;) {
        ssize_t n = read(master, buf, sizeof buf);
        if (n <= 0) break;
        timing_entry('O', (size_t)n);
        write_all(STDOUT_FILENO, buf, (size_t)n);
        write_all(log, buf, (size_t)n);
    }

    restore_tty();
    int code = WIFEXITED(status) ? WEXITSTATUS(status)
                                 : 128 + WTERMSIG(status);
    now = time(NULL);
    strftime(date, sizeof date, "%Y-%m-%d %H:%M:%S%z", localtime(&now));
    dprintf(log, "\nScript done on %s [COMMAND_EXIT_CODE=\"%d\"]\n",
            date, code);
    if (timing) {
        char c[16];
        snprintf(c, sizeof c, "%d", code);
        timing_header("EXIT_CODE", c);
        fclose(timing);
    }
    return code;
}
```

It is built like `ptyscript`, with the `ptyopen.o` of chapter 12:

```console
$ gcc -Wall -Wextra -O2 -o ptyscript2 ptyscript2.c ptyopen.o
$ ptyscript2 -o ts -t tm sh -c 'printf "caf\303"; sleep 0.5; printf "\251\n"; exit 3' < /dev/null
café
$ echo $?
3
$ cat tm
H 0.000000 START_TIME 2026-11-22 18:56:11+0100
H 0.000000 COMMAND sh
H 0.000000 TIMING_LOG tm
H 0.000000 OUTPUT_LOG ts
H 0.000000 COLUMNS 80
H 0.000000 LINES 24
O 0.001213 4
O 0.501182 3
H 0.000000 EXIT_CODE 3
$ scriptreplay --log-out ts --log-timing tm | cat -v
cafM-CM-)^M
```

The timing file has two output entries, 4 bytes (`caf` and the first
byte of `é`) and then 3 bytes (the second byte, `\r`, `\n`) half a
second later. `scriptreplay` from util-linux 2.42 replays the file,
skipping the "Script started" line of the log as it does for `script`.

The test of E.10 needs a grandchild that keeps the slave open after
the child exits. `sh -c 'sleep 100 & exit'` is not enough: when the
shell, which is the session leader, exits, the kernel sends SIGHUP to
the foreground process group of the terminal (C.2). Without job
control, the background `sleep` is in that same group and dies with
the shell. With `trap "" HUP`, the `sleep` ignores the hangup and
lives on (an ignored disposition survives `exec`). Only the `real`
line of each `time` is shown:

```console
$ time ptyscript -o ts1 -- sh -c 'trap "" HUP; sleep 6.32 & sleep 0.1; exit 3' < /dev/null
real    0m6.324s
$ time ptyscript2 -o ts2 -- sh -c 'trap "" HUP; sleep 6.33 & sleep 0.1; exit 3' < /dev/null
real    0m0.104s
$ time script -q -c 'trap "" HUP; sleep 4.34 & sleep 0.1; exit 3' ts3 < /dev/null
real    0m0.116s
```

`ptyscript` waits for the end of file on the master, which comes only
when the last holder of the slave exits. `ptyscript2` stops when its
child exits. util-linux `script` stops too. So the answer to "which
is right?" is that `script` chose the child, and the leftover
`sleep` keeps a terminal that nobody reads. (The `--` is needed for
`ptyscript`, whose `getopt` would otherwise take `-c` as its own
option: GNU `getopt` permutes the arguments unless the option string
starts with `+`, as in `ptyscript2`.)

Details of the solution:

- **The signal mask is set after the fork.** The hint of the
  exercise blocks the signals first and unblocks them in the child.
  That needs a change in `pty_spawn`, because a blocked mask is
  inherited across `fork` and `exec`. Blocking them after the fork
  works with the unchanged `pty_spawn`, but it has a race: a child
  that exits at once sends SIGCHLD before the mask is set, and the
  default action for SIGCHLD is to ignore it. The `waitpid(...,
  WNOHANG)` right after `signalfd` catches that case.
- **One SIGCHLD can stand for several children.** Standard signals
  do not queue. Here there is only one child, but the reaping still
  uses `WNOHANG` in a loop driven by the signal, never "one signal,
  one `wait`".
- **epoll refuses regular files** (`EPERM`). With `ptyscript2 <
  file`, standard input cannot be added to the epoll set. The program
  then copies the file into the PTY at once, which `poll` would have
  done anyway: a regular file is always "ready". `/dev/null` is
  refused too. In both cases, and at the end of a pipe, the program
  then types `^D`, as `ptyscript` does, so that `ptyscript2 cat <
  file` ends.
- **The output after the child's exit is not lost.** The child may
  exit while some of its output is still in the PTY. The final loop
  reads the master in non-blocking mode until `EAGAIN`, so nothing
  can make it wait.
- **The timing deltas are measured between entries**, whatever the
  stream, as in the advanced format of `script`. The header lines
  (`H`) have a delay of 0. `COLUMNS` and `LINES` let a player warn
  about a different window size, like the asciicast header.

#### E.9 in C: `ptyreplay`

The player reads the timing file line by line. For each entry it
sleeps for the delay (divided by the speed, and capped by `-i`), then
copies the given number of bytes from the typescript to standard
output. It reads two formats:

- The **classic** format of `script -t` is `DELAY LENGTH` per line.
- The **advanced** format of `script -T` and `ptyscript2 -t` is
  `TYPE DELAY LENGTH`. Only the `O` entries are copied.

```c
// file: c/ptyreplay.c
/*
 * ptyreplay: replay a typescript at the pace of its timing file.
 *   ptyreplay [-s SPEED] [-i MAX_PAUSE] TIMING TYPESCRIPT
 * Two timing formats are read:
 *   classic (script -t):    DELAY LENGTH
 *   advanced (script -T, ptyscript2 -t):  TYPE DELAY LENGTH|TEXT
 * In the advanced format only O (output) entries are played: I
 * (input) entries only wait, H (header) and S (signal) entries are
 * ignored.
 */
#define _GNU_SOURCE
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

static void usage(const char *me)
{
    fprintf(stderr, "usage: %s [-s SPEED] [-i MAX_PAUSE] TIMING TYPESCRIPT\n",
            me);
    exit(2);
}

/* Sleep for a number of seconds, resuming after signals. */
static void pause_for(double s)
{
    if (s <= 0) return;
    struct timespec t = { .tv_sec = (time_t)s,
                          .tv_nsec = (long)((s - (time_t)s) * 1e9) };
    while (nanosleep(&t, &t) == -1 && errno == EINTR) {}
}

/* Copy n bytes from `in` to standard output (or skip them). */
static int copy(FILE *in, long n, int show)
{
    char buf[4096];
    while (n > 0) {
        size_t want = n < (long)sizeof buf ? (size_t)n : sizeof buf;
        size_t got = fread(buf, 1, want, in);
        if (got == 0) return -1;             /* typescript too short */
        if (show && fwrite(buf, 1, got, stdout) != got) return -1;
        n -= (long)got;
    }
    return fflush(stdout);
}

int main(int argc, char **argv)
{
    double speed = 1, max_pause = -1;
    int opt;
    while ((opt = getopt(argc, argv, "+s:i:")) != -1) {
        switch (opt) {
        case 's': speed = atof(optarg); break;
        case 'i': max_pause = atof(optarg); break;
        default: usage(argv[0]);
        }
    }
    if (argc - optind != 2 || speed <= 0) usage(argv[0]);
    FILE *timing = fopen(argv[optind], "r");
    if (!timing) { perror(argv[optind]); return 1; }
    FILE *ts = fopen(argv[optind + 1], "r");
    if (!ts) { perror(argv[optind + 1]); return 1; }

    /* The typescript starts with a "Script started ..." line, which
     * the timing file does not count. */
    char *line = NULL;
    size_t cap = 0;
    if (getline(&line, &cap, ts) > 0 &&
        strncmp(line, "Script started", 14) != 0)
        rewind(ts);                          /* no header: keep it */

    long entries = 0, bytes = 0;
    while (getline(&line, &cap, timing) > 0) {
        char type = 'O';
        double delay;
        long len;
        if (line[0] >= 'A' && line[0] <= 'Z') {          /* advanced */
            type = line[0];
            if (type == 'H' || type == 'S') continue;
            if (sscanf(line + 1, "%lf %ld", &delay, &len) != 2) continue;
        } else if (sscanf(line, "%lf %ld", &delay, &len) != 2) {
            fprintf(stderr, "ptyreplay: bad timing line: %s", line);
            return 1;
        }
        /* The delay counts from the previous entry of any stream, so
         * an I entry still takes its time, though its bytes are in
         * another file. */
        if (max_pause >= 0 && delay > max_pause) delay = max_pause;
        pause_for(delay / speed);
        if (type == 'I') continue;
        if (copy(ts, len, 1) == -1) {
            fprintf(stderr, "ptyreplay: typescript ends early\n");
            return 1;
        }
        entries++;
        bytes += len;
    }
    free(line);
    fprintf(stderr, "ptyreplay: %ld entries, %ld bytes\n", entries, bytes);
    return 0;
}
```

The first test replays the recording of `ptyscript2`, at three paces
(only the `real` line of `time` is kept):

```console
$ ptyscript2 -o ts -t tm sh -c 'for i in 1 2 3; do echo "line $i"; sleep 0.4; done; printf "caf\303"; sleep 0.3; printf "\251\n"' < /dev/null > /dev/null
$ grep -v '^H' tm
O 0.001194 8
O 0.400798 8
O 0.402209 8
O 0.402251 4
O 0.301759 3
$ time ptyreplay tm ts > out
ptyreplay: 5 entries, 31 bytes
real    0m1.510s
$ time ptyreplay -s 4 tm ts > out
real    0m0.378s
$ time ptyreplay -i 0.1 tm ts > out
real    0m0.403s
$ tail -n +2 ts | head -c 31 | cmp - out && echo identical
identical
```

The pauses add up to 1.5 s: 1.508 s in the file, 0.377 s at speed 4,
and 0.4 s when each of the four pauses is capped at 0.1 s. The output
is the typescript without its first line ("Script started") and
without its last lines (an empty line and "Script done"), which no
timing entry covers. The `é` was split across two entries, as in E.8.
The player copies bytes and never decodes them, so the split does no
harm.

The second test uses recordings made by util-linux `script`:

```console
$ script -q -T ut -c 'echo one; sleep 0.3; echo two' us < /dev/null > /dev/null
$ head -2 ut
0.010139 5
0.292733 5
$ ptyreplay ut us | cat -v
one^M
two^M
ptyreplay: 2 entries, 10 bytes
$ printf 'typed\n' > keys
$ script -q -I bi -O bo -T bt -c 'head -n 1' < keys > /dev/null
$ grep -v '^H' bt
I 0.000034 6
O 0.260329 14
$ ptyreplay bt bo | cat -v
typed^M
typed^M
ptyreplay: 1 entries, 14 bytes
```

With only `-T`, `script` writes the classic format. With `-I` and
`-O` it logs two streams and switches to the advanced format, because
it must say which stream each entry belongs to. The output shows
`typed` twice: once as the echo of the line discipline, once as the
output of `head`. The input entry `I` is not copied, but its delay is
still slept, because each delay counts from the previous entry,
whatever its stream. A first version of the program skipped the `I`
lines entirely and lost their delays. That error does not show on
this short test, but it would shorten every pause after a typed key
in a long session.

#### E.11 in C: `keysplit`

```c
// file: c/keysplit.c
/*
 * keysplit: decode keys that may arrive split across reads, and tell
 * the Escape key from the start of a sequence by a timeout
 * (exercise E.11). Prints one key per line; q quits.
 */
#define _DEFAULT_SOURCE
#include <errno.h>
#include <poll.h>
#include <stdio.h>
#include <string.h>
#include <termios.h>
#include <unistd.h>

#define ESC_TIMEOUT_MS 50

static struct termios orig;
static void restore(void) { tcsetattr(STDIN_FILENO, TCSAFLUSH, &orig); }

/*
 * How many bytes form the first key of b[0..n)?
 *   > 0  a complete key of that length
 *   0    the key is not complete yet: wait for more bytes
 * Recognized: ESC [ params final, ESC O final, ESC x (Alt+x),
 * UTF-8 characters, single bytes.
 */
static size_t key_length(const unsigned char *b, size_t n)
{
    if (b[0] == 0x1b) {
        if (n < 2) return 0;                    /* lone ESC: so far */
        if (b[1] == 'O') return n < 3 ? 0 : 3;  /* SS3: one more byte */
        if (b[1] != '[') return 2;              /* Alt+key */
        for (size_t i = 2; i < n; i++)          /* CSI: up to a final */
            if (b[i] >= 0x40 && b[i] <= 0x7e) return i + 1;
        return 0;
    }
    size_t len = b[0] < 0x80 ? 1 : b[0] < 0xc0 ? 1   /* stray byte */
               : b[0] < 0xe0 ? 2 : b[0] < 0xf0 ? 3 : 4;
    return len <= n ? len : 0;
}

static void name_key(const unsigned char *b, size_t len)
{
    static const char finals[] = "ABCDHFPQRS";
    static const char *names[] = { "Up", "Down", "Right", "Left", "Home",
                                   "End", "F1", "F2", "F3", "F4" };
    static const char *mods[] = { "", "", "Shift+", "Alt+", "Shift+Alt+",
                                  "Ctrl+", "Ctrl+Shift+", "Ctrl+Alt+" };
    if (len == 1 && b[0] == 0x1b) { printf("Escape\r\n"); return; }
    if (len >= 3 && b[0] == 0x1b && (b[1] == '[' || b[1] == 'O')) {
        const char *p = strchr(finals, b[len - 1]);
        /* ESC [ 1 ; m X: m is 1 + a bit mask of the modifiers (B.8). */
        const char *semi = memchr(b, ';', len);
        int m = semi ? semi[1] - '0' : 1;
        if (p) {
            printf("%s%s\r\n", m >= 0 && m < 8 ? mods[m] : "?+",
                   names[p - finals]);
            return;
        }
        printf("sequence ESC %.*s\r\n", (int)(len - 1), (const char *)b + 1);
        return;
    }
    if (len == 2 && b[0] == 0x1b) { printf("Alt+%c\r\n", b[1]); return; }
    if (b[0] < 0x20 || b[0] == 0x7f) {
        printf("Ctrl+%c\r\n", b[0] ^ 0x40);
        return;
    }
    printf("char '%.*s'\r\n", (int)len, (const char *)b);
}

int main(void)
{
    if (tcgetattr(STDIN_FILENO, &orig) == -1) {
        perror("tcgetattr");
        return 1;
    }
    struct termios raw = orig;
    cfmakeraw(&raw);
    tcsetattr(STDIN_FILENO, TCSAFLUSH, &raw);
    setvbuf(stdout, NULL, _IONBF, 0);

    unsigned char buf[1024];
    size_t have = 0;
    for (;;) {
        /* An incomplete escape sequence: wait only a little for the
         * rest. An incomplete UTF-8 character: wait as long as needed
         * (no key starts with a continuation byte). */
        int timeout = have > 0 && buf[0] == 0x1b ? ESC_TIMEOUT_MS : -1;
        struct pollfd pf = { .fd = STDIN_FILENO, .events = POLLIN };
        int r = poll(&pf, 1, timeout);
        if (r == -1 && errno == EINTR) continue;
        if (r == -1) break;
        if (r == 0) {
            /* Timeout: the bytes will not become a sequence. An ESC
             * alone is the Escape key; then the rest, one key at a time
             * (ESC [ without a final byte gives Escape, '[', ...). */
            name_key(buf, 1);
            memmove(buf, buf + 1, --have);
        } else {
            ssize_t n = read(STDIN_FILENO, buf + have, sizeof buf - have);
            if (n <= 0) break;
            have += (size_t)n;
        }
        size_t len;
        while (have > 0 && (len = key_length(buf, have)) > 0) {
            if (len == 1 && buf[0] == 'q') { restore(); return 0; }
            name_key(buf, len);
            memmove(buf, buf + len, have -= len);
        }
        if (have == sizeof buf) have = 0;       /* garbage: give up */
    }
    restore();
    return 0;
}
```

To test it, a driver must send a key in two writes, with a pause it
controls. Python's `pty` module is enough for that. `pty.fork` is
`forkpty`: the child's standard descriptors are the slave, and the
parent gets the master.

```python
# file: c/drive_keys.py
# Drive keysplit on a PTY. Each test sends a key in two writes with a
# pause between them: ESC then "[A" (Up), and the two bytes of "é".
import os, pty, sys, time

def run(prog, gap):
    pid, fd = pty.fork()        # the child gets the slave as 0, 1, 2
    if pid == 0:
        os.execv(prog, [prog])
    time.sleep(0.2)             # let it switch to raw mode
    os.write(fd, b"\x1b")
    time.sleep(gap)
    os.write(fd, b"[A")
    time.sleep(0.2)
    e = "é".encode()
    os.write(fd, e[:1])
    time.sleep(gap)
    os.write(fd, e[1:])
    time.sleep(0.2)
    os.write(fd, b"\x1bOP\x1b[1;5Cq")   # F1, Ctrl+Right, q in one write
    out = b""
    while True:
        try:
            d = os.read(fd, 1024)
        except OSError:         # EIO: the slave side is closed
            break
        if not d:
            break
        out += d
    os.waitpid(pid, 0)
    keys = out.decode().replace("\r\n", " | ")
    print(f"gap {gap * 1000:.0f} ms: {keys}")

for gap in (0.010, 0.100):
    run(sys.argv[1], gap)
```

```console
$ gcc -Wall -Wextra -O2 -o keysplit keysplit.c
$ python3 drive_keys.py ./keysplit
gap 10 ms: Up | char 'é' | F1 | Ctrl+Right |
gap 100 ms: Escape | char '[' | char 'A' | char 'é' | F1 | Ctrl+Right |
```

With a 10 ms gap, the two halves of the Up key come together again.
With 100 ms, the program decides after 50 ms that the ESC was the
Escape key, so `[` and `A` arrive as ordinary characters. That is
what a user who presses Escape and then types `[A` quickly expects.
The split `é` is decoded correctly in both cases.

The design comes from two rules:

- **The decoder never consumes an incomplete key.** `key_length`
  returns 0 for "not enough bytes yet", which is different from a
  bad sequence. The bytes stay in the buffer, and the next `read`
  appends to them. In the original `rawkeys`, `decode` said
  "incomplete sequence" and dropped the bytes.
- **Only an escape sequence gets a timeout.** A UTF-8 character can
  also be split, but it is not ambiguous: its lead byte gives its
  length, so waiting as long as needed is correct. An ESC is
  ambiguous: it is a key on its own and also the start of a
  sequence. Only time tells them apart.

50 ms is a compromise. Vim's `defaults.vim` sets `ttimeoutlen` to
100 ms. tmux's `escape-time` is 10 ms in the version used here (3.8),
and older versions used 500 ms. Over a slow
`ssh` link, a sequence can be split by more than 50 ms, and an arrow
key becomes Escape, `[`, `A`. In vim, that means leaving insert mode
and inserting a line. This is the reason for the kitty keyboard
protocol (B.8), where the Escape key itself is sent as a sequence,
`ESC [ 27 u`, so that a lone ESC byte never has to be guessed.

#### E.12 in Raku: `rtee.raku`

```raku
# file: raku/rtee.raku
# rtee: run a command, copy its stdout to ours and to FILE, prefix its
# stderr with "[err] ", and exit with its exit code (exercise E.12).
#   raku rtee.raku out.txt sh -c 'echo a; echo b >&2; exit 3'

sub MAIN(Str $file, *@cmd where @cmd > 0) {
    my $log = $file.IO.open(:w, :bin);
    my $proc = Proc::Async.new(|@cmd);
    my $err-rest = '';                 # an incomplete stderr line
    my $exit;
    react {
        # Bytes, not text: copied as they are, even invalid UTF-8.
        whenever $proc.stdout(:bin) -> $blob {
            $*OUT.write($blob);
            $log.write($blob);
        }
        # Text, split by us: a chunk may end in the middle of a line,
        # and the prefix belongs at the start of each line only.
        whenever $proc.stderr -> $text {
            my @lines = ($err-rest ~ $text).split("\n");
            $err-rest = @lines.pop;
            $*ERR.print("[err] $_\n") for @lines;
        }
        whenever $proc.start -> $result {
            $*ERR.print("[err] $err-rest\n") if $err-rest;
            $exit = $result.signal ?? 128 + $result.signal !! $result.exitcode;
            done;
        }
        whenever signal(SIGINT) { $proc.kill(SIGINT) }   # pass ^C on
    }
    $log.close;
    exit $exit;
}
```

```console
$ raku rtee.raku out.txt sh -c 'echo a; echo b >&2; printf "no newline" >&2; exit 3'
a
[err] b
[err] no newline
$ echo $?
3
$ cat -A out.txt
a$
$ raku rtee.raku o2.txt sh -c 'kill -TERM $$'; echo $?
143
$ raku rtee.raku o3.txt seq 100000 | tail -1; wc -l < o3.txt
100000
100000
```

The two streams are handled differently on purpose. Standard output
is copied as bytes (`:bin`), because a `tee` must not change what it
copies: decoding and re-encoding would normalize the text (E.14
shows that Raku turns `e` + U+0301 into `é`) and would fail on
invalid UTF-8. Standard error is decoded text, because the program
adds a prefix to each line. A chunk from the supply ends wherever the
`read` of the pipe ended, not at the end of a line, so the last
incomplete piece is kept in `$err-rest` for the next chunk.

A process killed by a signal has no exit code. `Proc` reports it
with `.signal`, and the program converts it to the shell's 128 + N.
The `whenever signal(SIGINT)` block is there because both processes
are in the same foreground process group: a `^C` at the terminal
already reaches the child. The block matters when someone sends
SIGINT to `rtee` alone with `kill`.
#### E.13 in Raku: `rplay.raku`

```raku
# file: raku/rplay.raku
# Replay a terminal recording at its original pace (exercise E.13).
# Two formats, chosen from the first line:
#   asciicast v2 (ptyrec, asciinema):  rplay.raku [-s=2] [-i=1] demo.cast
#   script -T TIMING -B LOG:  rplay.raku --log=LOG TIMING
# -s: speed factor; -i: longest pause, in seconds.
use JSON::Fast;               # zef install JSON::Fast (in Rakudo Star)

# One event: when (seconds since the start) and what to write.
class Event { has Num $.t; has Str $.kind; has Blob $.data }

sub asciicast-events(IO::Path $file) {
    my @lines = $file.lines;
    my %header = from-json @lines.shift;
    die "not an asciicast v2 file" unless %header<version> == 2;
    note "recorded at %header<width>x%header<height>";
    gather for @lines.grep(*.trim) -> $line {
        my ($t, $kind, $data) = from-json($line).list;
        take Event.new(t => $t.Num, :$kind, data => $data.encode);
    }
}

# script -T --logging-format advanced: lines "O 0.000123 42" mean
# "after this delay, 42 bytes of output"; the bytes are in the log.
# Header lines start with H; S lines are signals (resize...).
sub script-events(IO::Path $timing, IO::Path $log) {
    my $fh = $log.open(:bin);
    # Skip the "Script started..." line: binary handles have no .get.
    Nil until $fh.read(1)[0] == 10;
    my Num $t = 0e0;
    gather for $timing.lines -> $line {
        my ($kind, $delay, $len) = $line.words;
        next unless $kind eq 'O' | 'I';
        $t += $delay.Num;
        my $data = $fh.read($len.Int);
        take Event.new(:$t, kind => $kind.lc, :$data);
    }
}

sub MAIN(Str $file, Num(Real) :s(:$speed) = 1e0,
         Num(Real) :i(:$max-idle) = Inf, Str :$log) {
    my $first = $file.IO.lines.head // die "empty file";
    my @events = $first.starts-with('{')
        ?? asciicast-events($file.IO)
        !! script-events($file.IO, ($log // die "--log=TYPESCRIPT needed").IO);
    my $out = $*OUT;
    $out.out-buffer = False;
    my $start = now;
    my ($last, $clock) = 0e0, 0e0;
    for @events -> $e {
        $clock += min($e.t - $last, $max-idle) / $speed;
        $last = $e.t;
        my $wait = $clock - (now - $start);
        sleep $wait if $wait > 0;
        given $e.kind {
            when 'o' { $out.write: $e.data }
            when 'r' { note "\n[resized to {$e.data.decode}]" }
            default  { }                       # input and markers
        }
    }
}
```

To check it, I played the recording of 29.7 with both players at
double speed and compared the bytes:

```console
$ raku rplay.raku -s=2 demo.cast > rplay.out
recorded at 80x24

[resized to 60x20]
$ ptyplay -s 2 demo.cast 2>/dev/null | cmp - rplay.out && echo SAME
SAME
$ script -q -B log -T timing -c 'printf hello; sleep 0.3; printf " world\n"'
$ raku rplay.raku --log=log timing | cat -v
hello world^M
```

Notes:

- `Num(Real) :s(:$speed) = 1e0` is a coercing parameter type with an
  alias. `-s=2` and `--speed=2` both work, and the integer `2`
  becomes the `Num` `2e0`.
- `gather`/`take` makes both readers lazy, so a long recording is not
  loaded into memory before the first event plays.
- The script log is read in binary mode, with `read($len)`, because
  the timing file counts bytes. Decoding it as UTF-8 would cut
  characters in two, as in the `caf\303` + `\251` example of the
  recording. Binary handles have no `get`, so the first line is
  skipped one byte at a time.
- The real `scriptreplay` handles more cases: `S` lines (signals) and
  the older two-column timing format. The `INPUT_LOG` header of the
  example says that input and output went to the same file. That
  works here only because `script -c` with output redirected records
  no input.

#### E.14 in Raku: `widths.raku`

```raku
# file: raku/widths.raku
# For each line read: bytes, code points, graphemes and terminal
# columns (exercise E.14). Columns come from the C library's wcwidth.
use NativeCall;

constant LC_ALL = 6;                            # glibc's value
sub setlocale(int32, Str --> Str) is native {*}
sub wcwidth(int32 --> int32) is native {*}

# wcwidth knows nothing until the program selects a locale, like a C
# program calling setlocale(LC_ALL, "") from the environment's LANG.
setlocale(LC_ALL, '') // note 'setlocale failed: widths will be wrong';

# Columns of a string: the sum of the code points' widths. That is
# what most terminals do, and why emoji sequences surprise them.
sub columns(Str $s) {
    [+] $s.NFC.list.map: -> $cp {
        my $w = wcwidth($cp);
        $w < 0 ?? 0 !! $w                       # controls: -1
    }
}

# The string comes last: its own width would misalign a column after it.
sub show(Str $s) {
    printf "%3d bytes %3d codes %3d chars %3d cols  %s\n",
        $s.encode.bytes, $s.codes, $s.chars, columns($s), $s.raku;
}

sub MAIN(Bool :$demo) {
    if $demo {
        show($_) for "é", "e\x[301]", "👍🏽", "漢字", "a\tb",
                     "👩‍👩‍👧", "\x[1F1EB]\x[1F1F7]";
        return;
    }
    show($_) for lines;                         # canonical mode: Enter
}
```

```console
$ raku widths.raku --demo
  2 bytes   1 codes   1 chars   1 cols  "é"
  2 bytes   1 codes   1 chars   1 cols  "é"
  8 bytes   2 codes   1 chars   4 cols  "👍🏽"
  6 bytes   2 codes   2 chars   4 cols  "漢字"
  3 bytes   3 codes   3 chars   2 cols  "a\tb"
 18 bytes   5 codes   1 chars   6 cols  "👩‍👩‍👧"
  8 bytes   2 codes   1 chars   2 cols  "🇫🇷"
```

Four surprises:

- **The second line is not `e` + U+0301.** Raku strings are in
  normal form NFG, and `.codes` and `.encode` work on its NFC form.
  The two code points became the single `é` when the literal was
  compiled. To keep them apart, use a `Uni` (`Uni.new(0x65, 0x301)`)
  or `$s.NFD`, which has 2 elements. Any program that reads the
  terminal through Raku's text layer sees composed characters.
- **The thumb with a skin tone takes 4 columns for wcwidth**, 2 + 2,
  because wcwidth looks at one code point at a time. Terminals that
  handle grapheme clusters draw it in 2 columns. An application that
  believes wcwidth then puts the cursor 2 columns too far, and the
  rest of the line is shifted. The family emoji (three people joined
  by two zero-width joiners) is worse: 6 columns for wcwidth, 2 for
  a modern terminal.
- **The tab counts as 0.** `wcwidth` returns -1 for control
  characters, and the program counts that as 0. A tab's real width
  depends on the column where it starts, so only the terminal (or a
  program that tracks the cursor) can know it.
- **The flag is right, by luck.** Each regional indicator letter is
  width 1, so the pair adds up to the 2 columns of the flag.

This is why full-screen programs and terminals sometimes disagree,
and why Unicode width is still being debated in the terminal working
group (G.2). The `printf` of `show` puts the string last for the
same reason: `%-14s` pads to 14 code points, not 14 columns, and
would misalign every line that contains a wide character.

#### E.15 in Raku: `rless.raku`

The pager loads the file and enters raw mode and the alternate
screen. It then waits for two kinds of events in a `react` block: keys
and signals.

```raku
# file: raku/rless.raku
# A minimal pager (exercise E.15):  raku rless.raku FILE
# Space/f/PgDn: next page   b/PgUp: previous page
# j/Down: one line down     k/Up: one line up   g/G: top/bottom   q: quit
use lib $*PROGRAM.parent.add('lib');
use Tty;
use Term::termios;

sub MAIN(Str $file) {
    die "rless: the keyboard (stdin) is not a terminal\n" unless $*IN.t;
    my @lines = $file.IO.lines;
    my $out   = $*OUT;
    my ($rows, $cols) = term-size(1);
    my $top   = 0;

    # Raw mode and the alternate screen; restore both, whatever happens.
    my $saved := Term::termios.new(fd => 0).getattr;
    my $raw   := Term::termios.new(fd => 0).getattr;
    $raw.makeraw;
    $raw.setattr(:FLUSH);
    my $restored = False;
    sub restore {
        return if $restored++;
        $out.print("\e[?25h\e[?1049l");         # cursor on, main screen
        $out.flush;
        $saved.setattr(:DRAIN);
    }
    LEAVE restore();                            # normal end, exceptions
    $out.print("\e[?1049h\e[?25l");             # alternate screen, no cursor

    my $page = { max(1, $rows - 1) };           # lines of text per screen
    my $last = { max(0, @lines.elems - $page()) };
    sub draw {
        $top = ($top min $last()) max 0;
        my $screen = "\e[H";                    # home, then each line
        for ^$page() -> $i {
            my $l = @lines[$top + $i] // '~';
            # Cut to the width (in characters: good enough for ASCII;
            # E.14 shows why wide characters need wcwidth). Tabs and
            # control characters would break the columns: show ^X.
            $l = $l.subst(/\t/, '    ', :g)
                   .subst(/<[\x00..\x1f\x7f]>/, { '^' ~ chr(.ord +^ 64) }, :g);
            $screen ~= $l.substr(0, $cols) ~ "\e[K\r\n";   # erase the rest
        }
        my $pct = @lines ?? (100 * min($top + $page(), +@lines) div +@lines) !! 100;
        $screen ~= "\e[7m {$file.IO.basename}  {$top + 1}-"
                 ~ "{min($top + $page(), +@lines)}/{+@lines}  $pct%  (q quits) "
                 ~ "\e[m\e[K";
        $out.print($screen);                    # one write: no flicker
        $out.flush;
    }

    # Keys come from a thread: a blocking read must not stop the signals.
    my $keys = Supplier.new;
    start {
        loop {
            my $buf = $*IN.read(64);
            last unless $buf;
            $keys.emit($buf.decode('latin-1'));
        }
        $keys.done;
    }
    draw();
    react {
        whenever $keys.Supply {
            given $_ {
                when 'q' | "\x[3]"        { done }   # q, or ^C (isig is off)
                when ' ' | 'f' | "\e[6~"  { $top += $page() }
                when 'b' | "\e[5~"        { $top -= $page() }
                when 'j' | "\e[B" | "\r"  { $top += 1 }
                when 'k' | "\e[A"         { $top -= 1 }
                when 'g' | "\e[H"         { $top = 0 }
                when 'G' | "\e[F"         { $top = $last() }
                default                   { $out.print("\a") }  # bell
            }
            draw();
        }
        whenever signal(SIGWINCH) {
            ($rows, $cols) = term-size(1);
            draw();
        }
        # isig is off, so these come only from kill(1) or the system.
        whenever signal(SIGINT, SIGTERM, SIGHUP) { done }
    }
}
```

The structure answers the questions of the exercise:

- **Keys come from a thread.** `$*IN.read` blocks. If the main thread
  waited there, a SIGWINCH would only be handled at the next key. The
  `start` block reads and emits each chunk into a `Supplier`. The
  `react` block then handles keys and signals, one event at a time, so
  `draw` never runs twice at once.
- **One `read` is one key.** In raw mode, an arrow key arrives as
  `ESC [ B` in a single `read`, which is enough for typed keys.
  Pasted text, or a slow link that splits a sequence, would need the
  decoder of E.11. Unknown input rings the bell.
- **Bytes are decoded as Latin-1**, which maps every byte to one
  character and never fails. The keys compared are ASCII, so the
  choice is safe. UTF-8 decoding would fail on a chunk that ends in
  the middle of a character.
- **The restore runs once, whatever the exit.** `LEAVE` runs when
  `MAIN` returns, normally or by an exception. `restore` is guarded by
  a flag, because a signal and the end of `MAIN` could otherwise both
  run it. `isig` is off in raw mode, so `^C` is just byte 3. The
  pager treats it as `q`, as `less` does. SIGINT, SIGTERM and SIGHUP
  can still come from `kill` or from a closed terminal, and each one
  ends the `react` block and goes through the same `LEAVE`.
  SIGKILL cannot be caught. After a `kill -9`, `stty sane` and `tput
  rmcup`, or simply `reset`, repair the terminal.
- **One `print` per screen.** The screen is built as one string and
  written at once. Every line ends with `ESC [ K` (erase to the end of
  the line) instead of clearing the screen first, so nothing flickers.
  This also avoids the `erase-to-end-of-line` bug of `Terminal::ANSI`
  (18.2), which is why the sequences are written by hand.

The check runs a shell on a 10×40 PTY. It starts the pager on a file
of 101 lines whose last line contains a tab and a `^A`. It presses
keys and reads the status line after each one. Then it shrinks the
PTY to 6 rows, quits, and compares `stty -g` with its value before the
pager. A second run is ended by SIGTERM, sent to the foreground
process group from outside:

```python
# file: raku/drive_rless.py
# Test rless (E.15) in a shell on a 10x40 PTY: page around, resize,
# quit; then again, ended by kill -TERM. Compare "stty -g" before and
# after each run: the terminal must be restored.
#   python3 drive_rless.py rless.raku FILE
import fcntl, os, pty, re, select, signal, struct, sys, termios, time

pager, text = (os.path.abspath(a) for a in sys.argv[1:3])
pid, fd = pty.fork()
if pid == 0:
    os.execvp("sh", ["sh"])
out = b""

def size(rows, cols):     # the kernel sends SIGWINCH to the foreground
    fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", rows, cols, 0, 0))

def pump(seconds):
    global out
    end = time.time() + seconds
    while time.time() < end:
        if select.select([fd], [], [], 0.05)[0]:
            try:
                out += os.read(fd, 65536)
            except OSError:                 # EIO: the shell has exited
                return

def status():
    """The last status line drawn (reverse video: ESC [ 7 m)."""
    return re.findall(rb"\x1b\[7m(.*?)\x1b\[m", out)[-1].decode().strip()

def last_text():
    """The last line of text of the last screen drawn."""
    frame = out[out.rfind(b"\x1b[H"):]
    return re.findall(rb"([^\r\n\x1b]*)\x1b\[K\r\n", frame)[-1].decode()

def stty():
    global out
    out = b""
    os.write(fd, b"stty -g\n")
    pump(0.5)
    return re.search(rb"[0-9a-f]+(:[0-9a-f]+){10,}", out).group(0)

size(10, 40)
os.write(fd, b"PS1='$ '\n")
pump(0.3)
before = stty()

os.write(fd, f"raku {pager} {text}\n".encode())
pump(3)                                     # Rakudo starts in ~1 s
print(f"{'start':12} {status()}")
for k, label in [(b" ", "space"), (b"j", "j"), (b"\x1b[B", "down arrow"),
                 (b"b", "b"), (b"G", "G"), (b"x", "x (unknown)")]:
    mark = len(out)
    os.write(fd, k)
    pump(0.4)
    bell = "   (bell)" if b"\a" in out[mark:] else ""
    print(f"{label:12} {status()}{bell}")
print("last line of text:", repr(last_text()))
size(6, 40)
pump(0.6)
print(f"{'resize 6x40':12} {status()}")
print("last line of text:", repr(last_text()))
os.write(fd, b"q")
pump(0.5)
print("main screen back:", b"\x1b[?1049l" in out, "| stty restored:", stty() == before)

os.write(fd, f"raku {pager} {text}\n".encode())
pump(3)
fg = os.tcgetpgrp(fd)                       # the pager's process group
os.killpg(fg, signal.SIGTERM)
pump(0.5)
print("after kill -TERM: main screen back:", b"\x1b[?1049l" in out,
      "| stty restored:", stty() == before)
os.write(fd, b"exit\n")
pump(0.3)
os.waitpid(pid, 0)
```

```console
$ seq -f 'line %g of the file' 1 100 > hundred.txt
$ printf 'tab\there\001ctl\n' >> hundred.txt
$ python3 drive_rless.py rless.raku hundred.txt
start        hundred.txt  1-9/101  8%  (q quits)
space        hundred.txt  10-18/101  17%  (q quits)
j            hundred.txt  11-19/101  18%  (q quits)
down arrow   hundred.txt  12-20/101  19%  (q quits)
b            hundred.txt  3-11/101  10%  (q quits)
G            hundred.txt  93-101/101  100%  (q quits)
x (unknown)  hundred.txt  93-101/101  100%  (q quits)   (bell)
last line of text: 'tab    here^Actl'
resize 6x40  hundred.txt  93-97/101  96%  (q quits)
last line of text: 'line 97 of the file'
main screen back: True | stty restored: True
after kill -TERM: main screen back: True | stty restored: True
```

With 10 rows, a page is 9 lines: the 10th row is the status line. The
resize keeps the first line shown (93) and draws fewer lines after
it, as `less` does. The test runs the pager in the foreground. An
earlier version ran `rless.raku FILE & sleep 3; kill -TERM $!` and
hung: started with `&` from an interactive shell with job control,
the pager was in a background group. Its `tcsetattr` for raw mode
earned it a SIGTTOU (chapter 5), and it stopped before drawing
anything, while the test waited for it. `jobs` in that shell (here
`sh` is bash) said `[1]+  Stopped(SIGTTOU)  raku rless.raku
hundred.txt`.

#### E.18 in Rust: `ptyscript_nb`

The first part of the exercise is mechanical: a non-blocking master,
a queue, and `POLLOUT` only while the queue is not empty. Testing it
showed that it is not enough, and the reason is worth a detour.

A script drives the test. It runs `ptyscript ... sleep 30` on a PTY,
pastes 100 KiB, types `^C`, and watches:

```python
# file: rust/paste_test.py
# Run "PROG... sleep 30" on a PTY, paste 100 KiB into it, type ^C, and
# report whether the ^C ended the session.
#   python3 paste_test.py target/release/ptyscript_nb -o /dev/null
import fcntl, os, pty, select, sys, time

prog = sys.argv[1:]
pid, fd = pty.fork()
if pid == 0:
    os.execv(prog[0], prog + ["sleep", "30"])
time.sleep(0.5)
fcntl.fcntl(fd, fcntl.F_SETFL, fcntl.fcntl(fd, fcntl.F_GETFL) | os.O_NONBLOCK)

def drain():
    """Read and drop the output (the echo of the paste)."""
    try:
        while os.read(fd, 65536):
            pass
    except OSError:             # BlockingIOError, or EIO at the end
        pass

def send(data, seconds):
    """Write as much of data as the PTY accepts within the delay."""
    sent, t0 = 0, time.time()
    while sent < len(data) and time.time() - t0 < seconds:
        try:
            sent += os.write(fd, data[sent:sent + 4096])
        except BlockingIOError:
            time.sleep(0.01)
        drain()
    return sent

paste = (b"x" * 63 + b"\r") * 1600     # 1600 lines, 100 KiB
t0 = time.time()
n = send(paste, 3)
print(f"pasted {n} of {len(paste)} bytes in {time.time() - t0:.1f} s")
t1 = time.time()
print("^C accepted:", send(b"\x03", 3) == 1)
while time.time() - t1 < 8:
    select.select([fd], [], [], 0.1)
    drain()
    done, status = os.waitpid(pid, os.WNOHANG)
    if done:
        print(f"ended {time.time() - t1:.1f} s after ^C, "
              f"exit status {os.waitstatus_to_exitcode(status)}")
        break
else:
    print("still running 8 s after ^C: killed")
    os.kill(pid, 9)
    os.waitpid(pid, 0)
```

With the original `ptyscript`:

```console
$ python3 paste_test.py target/release/ptyscript -o /dev/null
pasted 25600 of 102400 bytes in 3.0 s
^C accepted: False
still running 8 s after ^C: killed
```

`sleep` does not read its input, so the inner PTY fills up, and
`ptyscript` blocks in `write_all` on the master. It no longer reads
its own standard input, so the outer PTY fills up too, and even the
`^C` cannot be written.

A queue fixes the outer side: `ptyscript_nb` reads everything. But
the `^C` is then at the end of a 100 KiB queue that `sleep` will never
read. Can it be written to the inner PTY directly? A test on a bare
PTY says no. Once about 20 KiB are waiting (20,480 bytes in the
test), a `write` of the single byte `^C` fails with `EAGAIN`, so the
line discipline never sees it. So the relay must do the line
discipline's work itself. It checks the PTY's mode with `tcgetattr`
on the master. If `ISIG` is set and a key is `VINTR`, `VQUIT` or
`VSUSP`, the relay drops the queue and sends the signal with the
`TIOCSIG` ioctl. Linux provides that ioctl on the master side for
exactly this purpose: it sends a signal to the foreground process
group of the slave.

```rust
// file: rust/src/bin/ptyscript_nb.rs
//! ptyscript with a relay that never blocks (exercise E.18): the
//! master is non-blocking, keys wait in a queue, and POLLOUT is
//! requested only while the queue is not empty. Signal keys (^C, ^\,
//! ^Z) jump the queue, as the line discipline would handle them.
//!   ptyscript_nb [-o LOG] [CMD ARGS...]
use nix::errno::Errno;
use nix::fcntl::{FcntlArg, OFlag, fcntl};
use nix::poll::{PollFd, PollFlags, PollTimeout, poll};
use nix::pty::{Winsize, openpty};
use nix::sys::termios::{LocalFlags, SpecialCharacterIndices as Cc};
use signal_hook::consts::SIGWINCH;
use std::collections::VecDeque;
use std::fs::File;
use std::io::{self, ErrorKind, IsTerminal, Read, Write};
use std::os::fd::{AsFd, AsRawFd};
use std::os::unix::net::UnixStream;
use std::os::unix::process::ExitStatusExt;
use std::process::ExitCode;
use termtut::{
    RawMode, set_cloexec, set_window_size, spawn_on_pty, window_size,
};

/// If `keys` contains a signal character of the PTY (with ISIG on),
/// return the signal of the last one and its position.
fn signal_key(master: &File, keys: &[u8]) -> Option<(usize, i32)> {
    let t = nix::sys::termios::tcgetattr(master).ok()?;
    if !t.local_flags.contains(LocalFlags::ISIG) {
        return None; // raw mode: ^C is an ordinary byte (vim, ssh...)
    }
    let table = [
        (t.control_chars[Cc::VINTR as usize], libc::SIGINT),
        (t.control_chars[Cc::VQUIT as usize], libc::SIGQUIT),
        (t.control_chars[Cc::VSUSP as usize], libc::SIGTSTP),
    ];
    keys.iter().enumerate().rev().find_map(|(i, &b)| {
        table
            .iter()
            .find(|&&(c, _)| c == b && c != 0) // 0: disabled
            .map(|&(_, sig)| (i, sig))
    })
}

fn main() -> Result<ExitCode, Box<dyn std::error::Error>> {
    let mut args: Vec<String> = std::env::args().skip(1).collect();
    let mut log_path = String::from("typescript");
    if args.first().map(String::as_str) == Some("-o") {
        if args.len() < 2 {
            return Err("-o needs a file name".into());
        }
        log_path = args.remove(1);
        args.remove(0);
    }
    if args.is_empty() {
        args.push(std::env::var("SHELL").unwrap_or_else(|_| "/bin/sh".into()));
    }

    let stdin = io::stdin();
    let interactive = stdin.is_terminal();
    let (rows, cols) = if interactive {
        window_size(&stdin)?
    } else {
        (24, 80)
    };
    let ws = Winsize {
        ws_row: rows,
        ws_col: cols,
        ws_xpixel: 0,
        ws_ypixel: 0,
    };
    let pty = openpty(&ws, None)?;
    set_cloexec(&pty.master)?;
    set_cloexec(&pty.slave)?;
    let mut child = spawn_on_pty(&args, pty.slave)?;
    // Non-blocking from now on: a write that does not fit gives
    // WouldBlock instead of stopping the whole relay.
    let flags =
        OFlag::from_bits_truncate(fcntl(&pty.master, FcntlArg::F_GETFL)?);
    fcntl(&pty.master, FcntlArg::F_SETFL(flags | OFlag::O_NONBLOCK))?;
    let mut master = File::from(pty.master);

    let mut log = File::create(&log_path)?;
    let mut out = io::stdout().lock();
    writeln!(out, "Script started, output log file is '{log_path}'.")?;

    let (mut sig_r, sig_w) = UnixStream::pair()?;
    sig_r.set_nonblocking(true)?;
    signal_hook::low_level::pipe::register(SIGWINCH, sig_w)?;

    let raw = if interactive {
        Some(RawMode::enable(stdin.as_fd())?)
    } else {
        None
    };
    let mut pending: VecDeque<u8> = VecDeque::new();
    let mut stdin_open = true;
    let mut buf = [0u8; 4096];
    let ready = PollFlags::POLLIN | PollFlags::POLLHUP | PollFlags::POLLERR;
    loop {
        let mut want = PollFlags::POLLIN;
        if !pending.is_empty() {
            want |= PollFlags::POLLOUT; // only when there is something
        }
        let mut fds = vec![
            PollFd::new(master.as_fd(), want),
            PollFd::new(sig_r.as_fd(), PollFlags::POLLIN),
        ];
        // Stop reading the keyboard while the queue is large: memory
        // stays bounded, and the outer terminal holds the rest.
        let read_keys = stdin_open && pending.len() < 1 << 20;
        if read_keys {
            fds.push(PollFd::new(stdin.as_fd(), PollFlags::POLLIN));
        }
        match poll(&mut fds, PollTimeout::NONE) {
            Err(Errno::EINTR) => continue,
            r => r?,
        };
        let ev: Vec<PollFlags> = fds
            .iter()
            .map(|f| f.revents().unwrap_or(PollFlags::empty()))
            .collect();
        drop(fds);

        // 1. Output of the child.
        if ev[0].intersects(ready) {
            match master.read(&mut buf) {
                Ok(0) => break,
                Err(e) if e.raw_os_error() == Some(libc::EIO) => break,
                Err(e) if e.kind() == ErrorKind::WouldBlock => {}
                Err(e) => return Err(e.into()),
                Ok(n) => {
                    out.write_all(&buf[..n])?;
                    out.flush()?;
                    log.write_all(&buf[..n])?;
                }
            }
        }
        // 2. Room in the PTY: write as much of the queue as fits.
        if ev[0].contains(PollFlags::POLLOUT) {
            while !pending.is_empty() {
                let (front, _) = pending.as_slices();
                match master.write(front) {
                    Ok(n) => drop(pending.drain(..n)),
                    Err(e) if e.kind() == ErrorKind::WouldBlock => break,
                    Err(e) => return Err(e.into()),
                }
            }
        }
        // 3. Window size.
        if ev[1].contains(PollFlags::POLLIN) {
            while sig_r.read(&mut buf).is_ok() {}
            if interactive {
                let (rows, cols) = window_size(&stdin)?;
                set_window_size(&master, rows, cols)?;
            }
        }
        // 4. Keys: into the queue. A signal key cannot wait behind a
        //    paste that the program will never read, and a full PTY
        //    refuses even ^C (EAGAIN). So do what the line discipline
        //    does with its own buffer: drop the pending input and send
        //    the signal, with TIOCSIG (Linux), to the foreground group.
        if read_keys && ev.get(2).is_some_and(|e| e.intersects(ready)) {
            let n = nix::unistd::read(&stdin, &mut buf)?;
            if n == 0 {
                stdin_open = false;
                pending.push_back(0x04); // ^D: end of input
            } else if let Some((i, sig)) = signal_key(&master, &buf[..n]) {
                pending.clear();
                pending.extend(&buf[i + 1..n]);
                unsafe { libc::ioctl(master.as_raw_fd(), libc::TIOCSIG, sig) };
            } else {
                pending.extend(&buf[..n]);
            }
        }
    }

    drop(raw);
    let status = child.wait()?;
    let code = status
        .code()
        .unwrap_or_else(|| 128 + status.signal().unwrap_or(0));
    writeln!(out, "Script done, exit status {code}.")?;
    Ok(ExitCode::from(code as u8))
}
```

```console
$ python3 paste_test.py target/release/ptyscript_nb -o /dev/null
pasted 102400 of 102400 bytes in 0.1 s
^C accepted: True
ended 0.0 s after ^C, exit status 130
```

A real `^C` does one more thing that `TIOCSIG` does not: it flushes
the input already in the PTY (unless `NOFLSH` is set). This was
measured with a shell that ignores SIGINT, then reads a line. With
the `^C` byte, the shell read the line typed after it. With
`TIOCSIG`, it read the line typed before it. `tcflush` on the master
does not help: it flushes the master's own queues (in the test, the
echo disappeared), not the slave's input. So up to 20 KiB of the
paste can still reach the program after the `^C`. A shell at its
prompt would then run those lines. That is a good reason for bracketed
paste (B.11), which lets the program recognize a paste and handle it
as one block.

Other choices in the code:

- When `ISIG` is off, `^C` is an ordinary byte and goes through the
  queue. That is what vim, `ssh` or a nested `ptyscript` expect in
  raw mode.
- The keyboard is read only while the queue is below 1 MiB. Without
  that limit, `yes | ptyscript_nb cat > /dev/null` would grow the
  queue without bound. With it, the pressure goes back to the outer
  writer, as with a pipe.
- `pending.as_slices().0` writes the first contiguous part of the
  ring buffer. A `VecDeque` can wrap around, and the next loop writes
  the rest.
#### E.19 in Rust: `ttyinfo2`

```rust
// file: rust/src/bin/ttyinfo2.rs
//! For each of the descriptors 0, 1 and 2, tell whether it is a
//! terminal and, if not, what it is (exercise E.19).
//!   ttyinfo2 < /dev/null 2>&1 | cat
use nix::sys::stat::{SFlag, fstat, major, minor};
use std::io::IsTerminal;
use std::os::fd::{AsFd, BorrowedFd};

fn describe(fd: BorrowedFd) -> String {
    let st = match fstat(fd) {
        Ok(st) => st,
        Err(e) => return format!("closed ({e})"),
    };
    let kind = SFlag::from_bits_truncate(st.st_mode) & SFlag::S_IFMT;
    let link = std::fs::read_link(format!(
        "/proc/self/fd/{}",
        std::os::fd::AsRawFd::as_raw_fd(&fd)
    ))
    .map(|p| p.display().to_string())
    .unwrap_or_default();
    if fd.is_terminal() {
        let name = nix::unistd::ttyname(fd)
            .map(|p| p.display().to_string())
            .unwrap_or_else(|_| "?".into());
        let size = termtut::window_size(fd)
            .map(|(r, c)| format!("{c}x{r}"))
            .unwrap_or_else(|_| "?".into());
        let fg = nix::unistd::tcgetpgrp(fd)
            .map(|p| p.to_string())
            .unwrap_or_else(|e| format!("none ({e})"));
        return format!("terminal {name}, {size}, foreground group {fg}");
    }
    match kind {
        SFlag::S_IFIFO => format!("pipe or FIFO ({link})"),
        SFlag::S_IFSOCK => format!("socket ({link})"),
        SFlag::S_IFREG => format!("regular file {link}, {} bytes", st.st_size),
        SFlag::S_IFDIR => format!("directory {link}"),
        SFlag::S_IFCHR => format!(
            "character device {}:{} that is not a terminal ({link})",
            major(st.st_rdev),
            minor(st.st_rdev)
        ),
        _ => format!("other ({link})"),
    }
}

fn main() {
    let fds = [
        ("stdin", std::io::stdin().as_fd().try_clone_to_owned()),
        ("stdout", std::io::stdout().as_fd().try_clone_to_owned()),
        ("stderr", std::io::stderr().as_fd().try_clone_to_owned()),
    ];
    for (name, fd) in &fds {
        let line = match fd {
            Ok(fd) => describe(fd.as_fd()),
            Err(e) => format!("closed ({e})"),
        };
        println!("{name}: {line}");
    }
}
```

```console
$ ttyinfo2 < /dev/null 2>&1 | cat
stdin: character device 1:3 that is not a terminal (/dev/null)
stdout: pipe or FIFO (pipe:[20511520])
stderr: pipe or FIFO (pipe:[20511520])
$ ttyinfo2 < f.txt 2>/dev/null > out.txt; cat out.txt
stdin: regular file .../f.txt, 2 bytes
stdout: regular file .../out.txt, 114 bytes
stderr: character device 1:3 that is not a terminal (/dev/null)
$ script -q -c ttyinfo2 /dev/null < /dev/null
stdin: terminal /dev/pts/17, 0x0, foreground group 1154449
stdout: terminal /dev/pts/17, 0x0, foreground group 1154449
stderr: terminal /dev/pts/17, 0x0, foreground group 1154449
$ ttyinfo2 <&- 2>&1 | cat
stdin: character device 1:3 that is not a terminal (/dev/null)
stdout: pipe or FIFO (pipe:[20515962])
stderr: pipe or FIFO (pipe:[20515962])
```

(The paths of the second example are shortened.) Things to notice:

- `/dev/null` is a character device (major 1, minor 3), and it is
  not a terminal. A test like "is it a character device?" is not a
  substitute for `isatty`, which asks the driver with `TCGETS`.
- In the second example, `out.txt` already has 114 bytes when
  `fstat` runs on descriptor 1. `println!` on a `Stdout` flushes at
  each newline, so the line about stdin was written before the line
  about stdout was computed.
- Under `script` with its input redirected, the PTY has a size of
  0x0. `script` copies the size of its own standard input, which is
  not a terminal here (27.2 makes the same choice, but with a 24x80
  default).
- **The last example closes descriptor 0**, and yet `ttyinfo2` finds
  `/dev/null` there. Rust's runtime does that at start-up: if 0, 1 or
  2 is closed, it opens `/dev/null` in its place, so that the first
  `File::open` of the program cannot get descriptor 1 by accident and
  receive everything `println!` prints. A C program has no such
  protection. That is why daemons open `/dev/null` three times before
  doing anything else.
#### E.20 in Rust: `pipestatus`

```rust
// file: rust/src/bin/pipestatus.rs
//! Run a pipeline given as arguments separated by "|", like a shell,
//! and report every exit status, like bash's PIPESTATUS (exercise E.20).
//!   pipestatus false '|' true '|' sh -c 'exit 3'
use std::os::unix::process::ExitStatusExt;
use std::process::{Child, Command, ExitStatus, Stdio};

/// Start the commands of a pipeline, each reading the previous one's
/// output. The first reads our stdin, the last writes our stdout.
fn pipeline(cmds: &[Vec<String>]) -> std::io::Result<Vec<Child>> {
    let mut children: Vec<Child> = Vec::new();
    for (i, argv) in cmds.iter().enumerate() {
        let mut cmd = Command::new(&argv[0]);
        cmd.args(&argv[1..]);
        if let Some(prev) = children.last_mut() {
            // take() moves the read end into the new child; the parent
            // keeps no copy of it, so EOF and SIGPIPE work as in a shell.
            cmd.stdin(Stdio::from(prev.stdout.take().expect("piped")));
        }
        if i + 1 < cmds.len() {
            cmd.stdout(Stdio::piped());
        }
        match cmd.spawn() {
            Ok(child) => children.push(child),
            Err(e) => {
                // A shell would report it and go on, with status 127.
                eprintln!("pipestatus: {}: {e}", argv[0]);
                let mut dummy = Command::new("sh");
                dummy.args(["-c", "exit 127"]);
                if let Some(prev) = children.last_mut() {
                    drop(prev.stdout.take()); // the writer gets SIGPIPE
                }
                if i + 1 < cmds.len() {
                    dummy.stdout(Stdio::piped()).stdin(Stdio::null());
                }
                children.push(dummy.spawn()?);
            }
        }
    }
    Ok(children)
}

fn describe(st: ExitStatus) -> String {
    match (st.code(), st.signal()) {
        (Some(c), _) => c.to_string(),
        (None, Some(s)) => format!("{} (signal {s})", 128 + s),
        _ => "?".into(),
    }
}

fn main() -> std::io::Result<()> {
    let args: Vec<String> = std::env::args().skip(1).collect();
    let cmds: Vec<Vec<String>> =
        args.split(|a| a == "|").map(<[String]>::to_vec).collect();
    if cmds.iter().any(Vec::is_empty) {
        eprintln!("usage: pipestatus CMD [ARGS] ['|' CMD [ARGS]]...");
        std::process::exit(2);
    }
    let children = pipeline(&cmds)?;
    let mut statuses = Vec::new();
    for mut child in children {
        statuses.push(describe(child.wait()?));
    }
    eprintln!("PIPESTATUS: {}", statuses.join(" "));
    Ok(())
}
```

```console
$ cargo build --release --bin pipestatus
$ pipestatus false '|' true '|' sh -c 'exit 3'
PIPESTATUS: 1 0 3
$ pipestatus yes '|' head -2
y
y
PIPESTATUS: 141 (signal 13) 0
$ pipestatus printf 'b\na\n' '|' sort '|' nosuch '|' cat
pipestatus: nosuch: No such file or directory (os error 2)
PIPESTATUS: 0 141 (signal 13) 127 0
$ bash -c 'false | true | (exit 3); echo ${PIPESTATUS[*]}'
1 0 3
$ bash -c 'yes | head -2 >/dev/null; echo ${PIPESTATUS[*]}'
141 0
```

The `yes | head -2` line shows SIGPIPE at work (3.4). `yes` stops only
because `head` exited and nothing else holds the read end of the
pipe. This depends on `prev.stdout.take()`. It moves the
`ChildStdout` into the next `Command`, and the `Command` is dropped at
the end of the loop iteration, after `spawn`. If the parent kept a
clone of the read end, `yes` would run forever.

The missing command in the third example shows a design choice. A
shell does not abort the pipeline when one command cannot start: it
reports the error, and that element has status 127. Here a stand-in
`sh -c 'exit 127'` plays that role. The writer before it (`sort`) gets
SIGPIPE, as it would in bash.

#### E.23 in Go: `status`

```go
// file: go/cmd/status/main.go
// status: run a command and say exactly how it ended (exercise E.23).
package main

import (
	"errors"
	"fmt"
	"os"
	"os/exec"
	"syscall"
)

func main() {
	if len(os.Args) < 2 {
		fmt.Fprintln(os.Stderr, "usage: status CMD [ARGS...]")
		os.Exit(2)
	}
	cmd := exec.Command(os.Args[1], os.Args[2:]...)
	cmd.Stdin, cmd.Stdout, cmd.Stderr = os.Stdin, os.Stdout, os.Stderr
	err := cmd.Run()

	var exitErr *exec.ExitError
	switch {
	case err == nil:
		fmt.Println("exited with code 0")
	case errors.As(err, &exitErr):
		ws := exitErr.Sys().(syscall.WaitStatus)
		switch {
		case ws.Exited():
			fmt.Printf("exited with code %d\n", ws.ExitStatus())
		case ws.Signaled():
			core := ""
			if ws.CoreDump() {
				core = ", core dumped"
			}
			fmt.Printf("killed by signal %d (%v%s); a shell would say %d\n",
				int(ws.Signal()), ws.Signal(), core, 128+int(ws.Signal()))
		}
		fmt.Printf("ProcessState.String(): %q\n", exitErr.ProcessState.String())
	default:
		// The command did not start: not found, not executable...
		fmt.Printf("did not start: %v\n", err)
		os.Exit(127)
	}
}
```

```console
$ go build -o bin/status ./cmd/status
$ status sh -c 'exit 3'
exited with code 3
ProcessState.String(): "exit status 3"
$ status sh -c 'kill -SEGV $$'
killed by signal 11 (segmentation fault, core dumped); a shell would say 139
ProcessState.String(): "signal: segmentation fault (core dumped)"
$ status sh -c 'kill -TERM $$'
killed by signal 15 (terminated); a shell would say 143
ProcessState.String(): "signal: terminated"
$ status nosuch
did not start: exec: "nosuch": executable file not found in $PATH
```

On this machine, `ulimit -c` is `unlimited`, and systemd-coredump
collects the cores, so SIGSEGV reports "core dumped". With
`ulimit -c 0`, the same command prints no core.

The `errors.As` test separates the two kinds of failure. An
`*exec.ExitError` means the program ran and ended badly. Any other
error means it never ran. Testing `err != nil` alone would treat both
the same. A program that is not found is also the only case where
`cmd.ProcessState` is `nil`.

#### E.24 in Go: `cancelread`

```go
// file: go/cmd/cancelread/main.go
// cancelread: read the terminal, give up after 3 s of silence, and
// leave no goroutine blocked behind (exercise E.24).
//
//	cancelread a   SetReadDeadline on os.Stdin
//	cancelread b   a non-blocking duplicate, with deadlines
//	cancelread c   poll(2) before each read
package main

import (
	"errors"
	"fmt"
	"os"
	"time"

	"golang.org/x/sys/unix"
)

const quiet = 3 * time.Second

// (a) os.Stdin is a blocking descriptor: the runtime does not manage
// it with epoll, so it cannot honor deadlines.
func withStdinDeadline() error {
	return os.Stdin.SetReadDeadline(time.Now().Add(quiet))
}

// (b) A duplicate of descriptor 0 in non-blocking mode: os.NewFile
// sees O_NONBLOCK and registers it with the netpoller, so deadlines
// work. But dup shares the open file description, and O_NONBLOCK is
// a flag of the description: descriptor 0, and the shell that shares
// it, are now non-blocking too. Restore the flag before leaving.
func withDuplicate() error {
	fd, err := unix.Dup(0)
	if err != nil {
		return err
	}
	flags, err := unix.FcntlInt(uintptr(fd), unix.F_GETFL, 0)
	if err != nil {
		return err
	}
	if err := unix.SetNonblock(fd, true); err != nil {
		return err
	}
	f := os.NewFile(uintptr(fd), "stdin-nb")
	// Restore, then close: deferred calls run last-in first-out, so
	// two separate defers in the natural order would close first and
	// then fail to restore (EBADF), leaving the terminal non-blocking.
	defer func() {
		unix.FcntlInt(uintptr(fd), unix.F_SETFL, flags) // not f.Fd(): 27.1
		f.Close()
	}()
	report(0, "after SetNonblock on the duplicate")

	buf := make([]byte, 256)
	for {
		f.SetReadDeadline(time.Now().Add(quiet))
		n, err := f.Read(buf)
		if errors.Is(err, os.ErrDeadlineExceeded) {
			fmt.Println("(b) no input for 3 s:", err)
			return nil
		}
		if err != nil {
			return err
		}
		fmt.Printf("(b) read %q\n", buf[:n])
	}
}

// (c) Ask poll whether a read would block, with a timeout. The read
// itself is a plain blocking read that is known to return at once.
func withPoll() error {
	buf := make([]byte, 256)
	for {
		fds := []unix.PollFd{{Fd: 0, Events: unix.POLLIN}}
		n, err := unix.Poll(fds, int(quiet/time.Millisecond))
		if err == unix.EINTR {
			continue
		}
		if err != nil {
			return err
		}
		if n == 0 {
			fmt.Println("(c) no input for 3 s")
			return nil
		}
		m, err := unix.Read(0, buf)
		if err != nil || m == 0 {
			return err
		}
		fmt.Printf("(c) read %q\n", buf[:m])
	}
}

// report shows whether descriptor fd is in non-blocking mode.
func report(fd int, when string) {
	flags, _ := unix.FcntlInt(uintptr(fd), unix.F_GETFL, 0)
	fmt.Printf("fd %d O_NONBLOCK=%v %s\n", fd, flags&unix.O_NONBLOCK != 0, when)
}

func main() {
	if len(os.Args) != 2 {
		fmt.Fprintln(os.Stderr, "usage: cancelread a|b|c")
		os.Exit(2)
	}
	start := time.Now()
	var err error
	switch os.Args[1] {
	case "a":
		err = withStdinDeadline()
	case "b":
		err = withDuplicate()
	case "c":
		err = withPoll()
	}
	if err != nil {
		fmt.Println("error:", err)
	}
	report(0, "at exit")
	fmt.Printf("done after %v\n", time.Since(start).Round(100*time.Millisecond))
}
```

The driver types `hi` after one second, then nothing:

```python
# file: go/drive_cancel.py
# Run "cancelread MODE" on a PTY for each mode; type "hi" after 1 s.
import os, pty, sys, time

prog = sys.argv[1]
for mode in "abc":
    pid, fd = pty.fork()
    if pid == 0:
        os.execv(prog, [prog, mode])
    time.sleep(1)
    os.write(fd, b"hi\r")
    out = b""
    while True:
        try:
            d = os.read(fd, 1024)
        except OSError:
            break
        if not d:
            break
        out += d
    os.waitpid(pid, 0)
    print(f"--- {mode}\n" + out.decode().replace("\r\n", "\n"), end="")
```

```console
$ go build -o bin/cancelread ./cmd/cancelread
$ python3 drive_cancel.py bin/cancelread
--- a
error: file type does not support deadline
fd 0 O_NONBLOCK=false at exit
done after 0s
--- b
fd 0 O_NONBLOCK=true after SetNonblock on the duplicate
hi
(b) read "hi\n"
(b) no input for 3 s: read stdin-nb: i/o timeout
fd 0 O_NONBLOCK=false at exit
done after 4s
--- c
hi
(c) read "hi\n"
(c) no input for 3 s
fd 0 O_NONBLOCK=false at exit
done after 4s
```

(a) fails immediately with `os.ErrNoDeadline`. `os.Stdin` is created
by `os.NewFile` at start-up, and `NewFile` puts a descriptor under the
netpoller only if it is already in non-blocking mode. A terminal
normally is not.

(b) works, and the line "O_NONBLOCK=true after SetNonblock on the
duplicate" proves the warning of the exercise. The flag was set on
the duplicate, yet descriptor 0 has it too, because both share one
open file description (2.8). So do the shell and every other program
using the same terminal. The first version of this solution had two
separate `defer`s, one restoring the flags and one closing the file:

```go
defer unix.FcntlInt(uintptr(fd), unix.F_SETFL, flags) // restore
f := os.NewFile(uintptr(fd), "stdin-nb")
defer f.Close()
```

It printed `fd 0 O_NONBLOCK=true at exit`. Deferred calls run in
reverse order: `Close` ran first, and the restore then failed with
`EBADF`, an error nobody checked. The next program to read the
terminal then gets `EAGAIN` instead of waiting. A test on a PTY,
setting the flag with Python and then running `cat`, gave
`cat: -: Resource temporarily unavailable` and status 1. The restore also uses
the saved `fd`, not `f.Fd()`: as 27.1 showed, `Fd()` switches the
descriptor back to blocking mode, which would hide the bug instead of
fixing it.

(c) is the simplest, and changes nothing that others can see. It is
the solution of C programs, and of `muesli/cancelreader`, which waits
with `epoll` on the terminal and on a pipe, and writes to the pipe
when `Cancel` is called. A goroutine blocked in (c)'s `Poll` can be
woken in the same way, by adding a pipe to the `fds` list.
#### E.25 in Go: `procmon`

`procmon` reads `/proc/PID/stat` for every process and keeps those
whose `tty_nr` (field 7) is the one of `procmon` itself. Field 8,
`tpgid`, is the foreground process group of that terminal, so a
process is in the foreground when its `pgrp` equals `tpgid`. No
`ioctl` is needed, and no file descriptor on the terminal: the kernel
publishes the information for every process.

```go
// file: go/cmd/procmon/main.go
// procmon: the processes of this terminal, refreshed every second,
// with Bubble Tea (exercise E.25). Keys: s SIGSTOP, c SIGCONT,
// t SIGTERM, arrows or j/k to move, q to quit.
package main

import (
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strconv"
	"strings"
	"syscall"
	"time"

	"charm.land/bubbles/v2/table"
	tea "charm.land/bubbletea/v2"
	"charm.land/lipgloss/v2"
)

// proc holds the fields of /proc/PID/stat that matter here.
type proc struct {
	pid, ppid, pgrp, sid, ttyNr, tpgid int
	state                              string
	comm                               string
}

// readStat parses /proc/PID/stat. The command name is in parentheses
// and may contain spaces or ')' itself, so the fields are counted
// from the LAST ')'.
func readStat(pid string) (proc, error) {
	b, err := os.ReadFile(filepath.Join("/proc", pid, "stat"))
	if err != nil {
		return proc{}, err
	}
	s := string(b)
	open, close := strings.IndexByte(s, '('), strings.LastIndexByte(s, ')')
	if open < 0 || close < open {
		return proc{}, fmt.Errorf("bad stat for %s", pid)
	}
	f := strings.Fields(s[close+1:]) // f[0] is field 3, the state
	if len(f) < 6 {
		return proc{}, fmt.Errorf("short stat for %s", pid)
	}
	n := func(i int) int { v, _ := strconv.Atoi(f[i]); return v }
	p := proc{state: f[0], ppid: n(1), pgrp: n(2), sid: n(3),
		ttyNr: n(4), tpgid: n(5), comm: s[open+1 : close]}
	p.pid, _ = strconv.Atoi(pid)
	return p, nil
}

// cmdline is the full command, or [comm] for kernel-like processes.
func cmdline(p proc) string {
	b, err := os.ReadFile(fmt.Sprintf("/proc/%d/cmdline", p.pid))
	if err != nil || len(b) == 0 {
		return "[" + p.comm + "]"
	}
	return strings.TrimSpace(strings.ReplaceAll(string(b), "\x00", " "))
}

// scan returns the processes whose controlling terminal is ttyNr.
func scan(ttyNr int) []proc {
	dirs, _ := os.ReadDir("/proc")
	var ps []proc
	for _, d := range dirs {
		if d.Name()[0] < '0' || d.Name()[0] > '9' {
			continue
		}
		p, err := readStat(d.Name()) // may vanish meanwhile: skip it
		if err == nil && p.ttyNr == ttyNr {
			ps = append(ps, p)
		}
	}
	sort.Slice(ps, func(i, j int) bool { return ps[i].pid < ps[j].pid })
	return ps
}

var (
	fgStyle  = lipgloss.NewStyle().Bold(true)
	msgStyle = lipgloss.NewStyle().Faint(true)
	states   = map[string]string{"R": "running", "S": "sleeping",
		"D": "disk", "T": "stopped", "t": "traced", "Z": "zombie"}
)

type tickMsg time.Time

func tick() tea.Cmd {
	return tea.Tick(time.Second, func(t time.Time) tea.Msg {
		return tickMsg(t)
	})
}

type model struct {
	ttyNr  int
	self   int
	procs  []proc
	table  table.Model
	status string
}

func (m *model) refresh() {
	selected := 0
	if r := m.table.SelectedRow(); r != nil {
		selected, _ = strconv.Atoi(r[0])
	}
	m.procs = scan(m.ttyNr)
	rows := make([]table.Row, len(m.procs))
	cursor := 0
	for i, p := range m.procs {
		fg := ""
		if p.pgrp == p.tpgid {
			fg = "fg"
		}
		if p.pid == m.self {
			fg += " (me)"
		}
		st := p.state + " " + states[p.state]
		rows[i] = table.Row{strconv.Itoa(p.pid), strconv.Itoa(p.pgrp),
			st, fg, cmdline(p)}
		if p.pid == selected {
			cursor = i // keep the cursor on the same process
		}
	}
	m.table.SetRows(rows)
	m.table.SetCursor(cursor)
}

func (m model) Init() tea.Cmd { return tick() }

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tickMsg:
		m.refresh()
		return m, tick()
	case tea.WindowSizeMsg:
		m.table.SetWidth(msg.Width)
		m.table.SetHeight(max(3, msg.Height-4))
		return m, nil
	case tea.KeyPressMsg:
		sigs := map[string]syscall.Signal{"s": syscall.SIGSTOP,
			"c": syscall.SIGCONT, "t": syscall.SIGTERM}
		k := msg.String()
		if k == "q" || k == "ctrl+c" {
			return m, tea.Quit
		}
		if sig, ok := sigs[k]; ok {
			r := m.table.SelectedRow()
			if r == nil {
				return m, nil
			}
			pid, _ := strconv.Atoi(r[0])
			if pid == m.self && sig == syscall.SIGSTOP {
				m.status = "not stopping myself: nobody could continue me"
				return m, nil
			}
			if err := syscall.Kill(pid, sig); err != nil {
				m.status = fmt.Sprintf("kill %d: %v", pid, err)
			} else {
				m.status = fmt.Sprintf("sent %v to %d", sig, pid)
			}
			m.refresh() // show the new state now, not in a second
			return m, nil
		}
	}
	var cmd tea.Cmd
	m.table, cmd = m.table.Update(msg)
	return m, cmd
}

func (m model) View() tea.View {
	fg := 0
	if len(m.procs) > 0 {
		fg = m.procs[0].tpgid
	}
	head := fgStyle.Render(fmt.Sprintf(
		"tty_nr %d:%d   foreground group %d", m.ttyNr>>8&0xfff,
		m.ttyNr&0xff|m.ttyNr>>12&0xfff00, fg))
	help := msgStyle.Render("s stop · c continue · t term · q quit   " +
		m.status)
	v := tea.NewView(head + "\n" + m.table.View() + "\n" + help + "\n")
	v.AltScreen = true
	return v
}

func main() {
	self, err := readStat("self")
	if err != nil || self.ttyNr == 0 {
		fmt.Fprintln(os.Stderr, "procmon: no controlling terminal")
		os.Exit(1)
	}
	m := model{ttyNr: self.ttyNr, self: os.Getpid()}
	m.table = table.New(
		table.WithColumns([]table.Column{
			{Title: "PID", Width: 7}, {Title: "PGID", Width: 7},
			{Title: "STATE", Width: 11}, {Title: "", Width: 7},
			{Title: "COMMAND", Width: 40},
		}),
		table.WithFocused(true),
		table.WithHeight(10),
	)
	m.refresh()
	if _, err := tea.NewProgram(m).Run(); err != nil {
		fmt.Fprintln(os.Stderr, "procmon:", err)
		os.Exit(1)
	}
}
```

It builds like the other programs of the module:

```console
$ go vet ./cmd/procmon && go build -o bin/procmon ./cmd/procmon
```

The check of the exercise is a test script. It runs an interactive
`bash` on a PTY, starts `sleep 1000 &` and `procmon`, presses keys,
and looks at the state of `sleep` in `/proc` after each key. At the
end it quits `procmon` and asks `bash` for `jobs`:

```python
# file: go/drive_procmon.py
# Test procmon (E.25): in an interactive bash on a PTY, start
# "sleep 1000 &", run procmon, stop and continue the sleep from it,
# quit, and ask bash for "jobs".
#   python3 drive_procmon.py bin/procmon
import os, pty, re, select, struct, sys, time, fcntl, termios

os.chdir(os.path.dirname(os.path.abspath(sys.argv[1])))
procmon = "./" + os.path.basename(sys.argv[1])
pid, fd = pty.fork()
if pid == 0:
    os.execvp("bash", ["bash", "--norc", "--noprofile", "-i"])
fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", 24, 80, 0, 0))
out = b""

def pump(seconds):
    """Collect the output for a while; answer cursor queries."""
    global out
    end = time.time() + seconds
    while time.time() < end:
        if select.select([fd], [], [], 0.05)[0]:
            try:
                data = os.read(fd, 65536)
            except OSError:                    # EIO: bash has exited
                return
            out += data
            if b"\x1b[6n" in data:
                os.write(fd, b"\x1b[1;1R")

def state(p):
    with open(f"/proc/{p}/stat") as f:
        return f.read().rsplit(")", 1)[1].split()[0]

def key(k, label):
    os.write(fd, k)
    pump(0.6)
    print(f"{label:22} sleep is {state(sleep_pid)}")

os.write(fd, b"PS1='$ '; sleep 1000 & echo pid=$!\r")
pump(0.5)
sleep_pid = int(re.search(rb"pid=(\d+)", out).group(1))
os.write(fd, procmon.encode() + b"\r")
pump(1.5)
# The first frame, as text: expand REP (ESC [ N b repeats the
# previous character N times), then drop the other escape sequences.
frame = out[out.rfind(b"\x1b[?1049h"):].decode()
frame = re.sub(r"(.)\x1b\[(\d+)b", lambda m: m[1] * (int(m[2]) + 1), frame)
frame = re.sub(r"\x1b\[[0-9;?>=]*[A-Za-z]", "", frame)
for line in frame.split("\r\n")[:5]:
    print("  |", line.split("\r")[0])
key(b"j", "j (to the sleep row)")
key(b"s", "s (SIGSTOP)")
key(b"c", "c (SIGCONT)")
key(b"s", "s (SIGSTOP again)")
os.write(fd, b"q")
pump(0.5)
mark = len(out)
os.write(fd, b"jobs; kill -CONT %1; kill %1; exit\r")
pump(1.0)
for line in out[mark:].decode(errors="replace").splitlines():
    if "Stopped" in line or "Running" in line or "Terminated" in line:
        print("bash:", line.strip())
os.waitpid(pid, 0)
```

```console
$ python3 drive_procmon.py bin/procmon
  | tty_nr 136:16   foreground group 1195276
  |  PID      PGID     STATE                 COMMAND
  |  1195245  1195245  S sleeping            bash --norc --noprofile -i
  |  1195246  1195246  S sleeping            sleep 1000
  |  1195276  1195276  R running    fg (me)  ./procmon
j (to the sleep row)   sleep is S
s (SIGSTOP)            sleep is T
c (SIGCONT)            sleep is S
s (SIGSTOP again)      sleep is T
bash: [1]+  Stopped                    sleep 1000
```

`136:16` is `/dev/pts/16`: major 136 is the first major number of the
Unix 98 PTY slaves. Each job of the interactive `bash` has its own
process group, and only `procmon` is in the foreground. `bash` learns
about the stop by itself: as the parent of `sleep`, it gets a SIGCHLD
and a `waitpid` status saying "stopped". So `jobs` shows it, even
though another program sent the signal.

Points worth noting:

- **Parsing `stat`.** The second field is the command name in
  parentheses. That name is chosen by the program (`prctl`) and can
  contain spaces and `)`. The fields are therefore counted from the
  *last* `)`. Splitting the whole line on spaces works until a
  program is called `my prog`.
- **Processes vanish.** Between `ReadDir` and `ReadFile`, a process
  can exit. The error is not reported: the process is skipped.
- **The selection follows the process.** The table is rebuilt every
  second and processes come and go, so a row index would make the
  cursor jump to another process. `refresh` remembers the PID of the
  selected row and finds it again. Without that, `s` could stop the
  wrong process.
- **Stopping `procmon` itself is refused.** It would freeze the
  program in raw mode and on the alternate screen, and the shell
  would print its prompt into that screen. `fg` would continue it,
  but the user may not know that.
- **`REP` in the output.** The test first failed to match the rows.
  The raw output showed `S sleeping \e[11bbash`, where `\e[11b` is
  REP, an ECMA-48 control that repeats the previous character 11
  times. The renderer of Bubble Tea v2 uses it to send long runs of
  spaces in fewer bytes. A test that reads the screen must expand REP,
  or use a real terminal emulator such as `vt.go` of `muxi` (31).

## Appendix F. Troubleshooting

This appendix is organized by symptom. For each, the likely causes,
in order of probability, and how to check and fix them. Section 32.8
has the short version; chapter 32 has the tools.

### F.1 The terminal itself

**Typing shows nothing, but commands run.** Echo is off: a program
that turned it off (a password prompt, a crashed TUI) did not restore
it. Type `stty echo` (blind) and Enter, or `stty sane`; see 32.9.

**Enter does nothing, or shows `^M`.** ICRNL is off and the shell is
not readline-based (or the program waiting is not the shell). Press
`^J` instead of Enter: `stty sane^J`.

**Output goes down in a staircase.** OPOST (or ONLCR) is off: `\n`
moves down without returning to column 1. `stty sane`, or just `stty
opost onlcr`.

**The terminal is frozen; no output, keys do nothing.** In order:
`^Q` (XOFF from an accidental `^S`, A.1); a program in the
foreground that reads nothing (try `^C`, then `^\`, then `^Z` and
`kill %1`); output stuck in a full PTY buffer because the emulator is
blocked (rare); from another terminal, `ps -t pts/N -o
pid,stat,wchan,comm` tells which (32.2, 32.3).

**Letters print as line-drawing characters (`┌┐└┘` instead of
`lkmj`).** A binary file or a broken program switched to the DEC
graphics set (SO, or `ESC ( 0`, B.2). Type `printf '\e(B\017'`, or
`reset`.

**Garbage like `^[[<0;34;12M` on every click, or `^[[I` and `^[[O`
when switching windows.** Mouse reporting or focus events were left
on (B.10, B.11). `reset`, or turn them off with `printf
'\e[?1000l\e[?1002l\e[?1003l\e[?1006l\e[?1004l'`.

**Pasting adds `^[[200~` and `^[[201~` around the text.** Bracketed
paste was left on by a program, and the current program does not
understand it. `printf '\e[?2004l'`.

**The cursor has disappeared.** `tput cnorm`, or `printf '\e[?25h'`.

**The prompt overwrites itself, long lines wrap on the same line.**
The prompt contains escape sequences that readline thinks are
printable characters, so it miscalculates the cursor position. In
bash, surround them with `\[` and `\]` in `PS1`; in zsh, `%{` and
`%}`. Or the window size is wrong: see F.2.

**`^H` or `^?` appears when pressing Backspace.** The ERASE character
(`stty -a`) does not match what the key sends (`showkey -a`). Change
one: `stty erase '^?'`, or the emulator's "Backspace sends" setting.
Over `ssh` to old systems, `stty erase '^H'`.

**`^D` does not end `cat`.** It ends input only at the start of a
line; in the middle of a line, press it twice (A.5). Or the terminal
is in raw mode, where `^D` is a byte (4).

**`^C` does not interrupt.** ISIG is off (the program set raw mode);
the program catches or ignores SIGINT; or the program is not in the
foreground group (the signal goes to the foreground group only, 32.2).
Try `^\` (SIGQUIT), then `^Z` and `kill %1`, then `kill -9` from
another terminal.

### F.2 Size, `TERM` and display

**Full-screen programs use only part of the window, or wrap at 80
columns.** The PTY's size is wrong. `stty size` shows what the kernel
knows; if it is `0 0` or does not match, the PTY was created without
a size, or a resize was not propagated: a program that creates PTYs
must call `TIOCSWINSZ` at start and on every SIGWINCH (chapter 8,
29.3). Fix for the session: `stty rows 40 cols 120`, or `resize`
(from xterm).

**`tput: unknown terminal`, "terminal is not fully functional",
`vim` complains, `less` warns "WARNING: terminal is not fully
functional".** `TERM` names an entry that does not exist on this
machine. Usual over `ssh` from kitty, foot, Ghostty, Alacritty or
WezTerm. Install the entry (`infocmp -x | ssh host -- tic -x -`, or
the distribution package such as `kitty-terminfo`), or use
`TERM=xterm-256color` for that host.

**No colors.** The program decided the output is not a terminal (it
is a pipe: use `--color=always`, `-R` for `less`); `TERM` says the
terminal has no colors (`tput colors`); `NO_COLOR` is set in the
environment (a convention many programs honor); or the program checks
`COLORTERM` for true color.

**Colors are wrong inside tmux.** tmux's `default-terminal` should be
`tmux-256color`; for 24-bit colors, add the outer terminal's `RGB`
feature: `set -as terminal-features ',xterm-256color:RGB'` (or the
outer `TERM`).

**Characters misaligned after emoji or CJK text.** The program and
the terminal disagree on the width of some characters (`wcwidth`,
E.14): different Unicode versions, ambiguous-width characters (some
East Asian settings make `→` two columns wide), or emoji with
variation selectors. No universal fix; update both, or avoid those
characters in TUIs.

**Accented letters appear as `Ã©`.** UTF-8 bytes interpreted as
Latin-1 somewhere: the locale is not UTF-8 (`locale`; set `LANG=
C.UTF-8` or `en_US.UTF-8`), or a program decoded bytes with the wrong
encoding. Appears as `�` when the opposite happens (Latin-1 bytes
decoded as UTF-8).

**The screen is not restored after `vim` or `less` exits.** The
`TERM` entry has no `smcup` and `rmcup`, or they are disabled (`less
-X`). Conversely, if you want the output to stay, `less -X`.

### F.3 Pipes and processes

**A pipeline never ends.** A write end of a pipe is still open:
in the parent that created it, in a sibling, or leaked to a
grandchild (3.6, 32.3). Find the `pipe:[N]` with `ls -l
/proc/*/fd/ 2>/dev/null | grep 'pipe:\[N\]'` and see who holds it.
In your own code: close the ends you do not use right after `fork`,
and create pipes with `O_CLOEXEC`.

**A program hangs when its output is large, but works with small
output.** A deadlock on a full pipe: the parent writes to the child's
input while the child writes to its output, and nobody reads (3.6).
Read and write concurrently (`poll`, threads, or `communicate`-style
helpers), or use a temporary file.

**Output appears only at the end, or in bursts.** stdio buffering
when the output is a pipe (2.13): `stdbuf -oL cmd`, `unbuffer cmd`,
`script -qc cmd /dev/null`, `python3 -u`, or the program's own
flush option (`grep --line-buffered`, `sed -u`).

**"Broken pipe" errors, or `BrokenPipeError` tracebacks, when piping
to `head`.** The program ignores SIGPIPE (or its language does, as
Rust and Python do) and reports EPIPE as an error (3.4, 20.5). For your
own programs, treat EPIPE on standard output as a normal end. In
Python, `signal.signal(signal.SIGPIPE, signal.SIG_DFL)`.

**Exit status 141.** 128 + 13: killed by SIGPIPE, usually harmless
(`yes | head`). With `set -o pipefail`, it makes the pipeline fail;
check `PIPESTATUS`.

**A background job stops with "Stopped (tty input)".** It read from
the terminal (SIGTTIN, C.2). Give it input from a file or
`/dev/null`, or bring it to the foreground. "Stopped (tty output)":
it wrote with `tostop` set, or changed terminal modes (some programs
do it at start), SIGTTOU.

**`nohup cmd &` still dies when I log out**, or **dies when I close
the terminal**. With `nohup`, SIGHUP is ignored, but the program may
reset it, or die from `EIO` when writing to the vanished terminal
(`nohup` redirects only if the output is a terminal at start). Use
`setsid -f cmd > log 2>&1 < /dev/null`, `systemd-run --user`, or a
multiplexer.

**Zombies (`<defunct>`) accumulate.** The parent does not `wait`
for its children. Fix the parent (reap on SIGCHLD); killing the
zombie does nothing, killing the parent hands them to `init`, which
reaps them.

### F.4 Pseudo-terminals in your programs

**Reading the master returns `EIO` and the program thinks it is an
error.** It is the normal end: all slave descriptors are closed. Treat
`EIO` like end of file (chapter 6, 30.4).

**The child's output is lost at the end.** The program stopped reading
the master when the child exited (SIGCHLD), but output was still in
the buffer. Read the master until `EIO`, then reap the child.

**The program never ends when the child exits.** Another process
holds the slave open: a grandchild in the background, or your own
process (you kept the slave descriptor after `fork`). Close the slave
in the parent after starting the child; for grandchildren, decide
whether to wait (like `script`) or stop at the child's exit (E.10).

**Job control does not work in the child ("no job control in this
shell", `^Z` does nothing).** The child did not become a session
leader with the slave as controlling terminal: `setsid()` and
`ioctl(slave, TIOCSCTTY, 0)` in the child (chapter 12), or the
language's equivalent (`Setsid` and `Setctty` in Go's
`SysProcAttr`, `pre_exec` in Rust, the `setsid -c` helper in Raku).

**Input is echoed twice, or the expected text is not found.** The
slave echoes what you send (ECHO is on by default), so your input
comes back on the master before the program's answer. Match after the
echo, or turn echo off on the slave (30.5).

**Output has `\r\n` instead of `\n`.** ONLCR on the slave: normal for
a PTY. Strip `\r`, or turn off OPOST on the slave if you control it.

**The program on the PTY behaves as if not interactive (no prompt,
buffered output).** It may check its standard input or output with
`isatty`: make sure all three descriptors are the slave. Or it reads
`TERM`: set it (`TERM=dumb` for plain output, 30.4).

**Closing the master does not interrupt a goroutine reading it
(Go).** creack/pty's master was left in blocking mode, outside Go's
poller: set it non-blocking (27.1).

**The program hangs waiting for an answer to a query.** It asked the
terminal something (B.9) and your PTY program does not answer.
Answer DA and DSR yourself (31.2), or use `TERM=dumb`.

### F.5 Language-specific surprises

- **C**: `fork` in a multithreaded program: only async-signal-safe
  calls until `exec`. Forgetting to `fflush(stdout)` before `fork`
  duplicates the buffered output. Forgetting `_exit` (rather than
  `exit`) in a child that failed to `exec` flushes the parent's
  buffers twice.
- **Raku**: a `Proc` that failed throws only when **sunk** (its value
  discarded), or when used in boolean context returns `False` (15.2);
  `run(..., :out)` without reading `.out` can deadlock on large
  output; the `react` block ends when all `whenever` supplies are
  done, which may be earlier or later than you think; `.chars`
  counts graphemes, not code points or columns.
- **Rust**: SIGPIPE is ignored by the runtime, so `println!` to a
  closed pipe **panics** ("failed printing to stdout: Broken pipe")
  (20.5); `Command` uses `posix_spawn` or `fork`+`exec` depending on
  the options, and `pre_exec` is `unsafe` for good reasons; dropping
  a `Child` does not wait for it or kill it.
- **Go**: `exec.Cmd.Wait` waits for the copying goroutines too, so a
  grandchild holding the output pipe makes `Wait` hang (set
  `WaitDelay`); `os.Stdin` is not in the poller, so a read on it
  cannot be cancelled (E.24); `syscall.ForkExec` happens in the
  runtime, so code "between fork and exec" can only be expressed with
  `SysProcAttr`.

## Appendix G. Further reading

The links below were checked on 2026-11-22 (two gnu.org pages refused
automated requests that day; they are long-standing pages of the GNU
manuals).

### G.1 Books

- W. Richard Stevens and Stephen A. Rago, *Advanced Programming in
  the UNIX Environment*, 3rd edition (Addison-Wesley, 2013). Chapters
  9 (process relationships), 10 (signals), 15 (IPC, pipes), 18
  (terminal I/O) and 19 (pseudo terminals) cover the C side of this
  tutorial in depth, with the historical differences between systems.
  Its `pty` program is the ancestor of every `ptyscript`.
- Michael Kerrisk, *The Linux Programming Interface* (No Starch Press,
  2010), [man7.org/tlpi](https://man7.org/tlpi/). Chapters 34
  (process groups, sessions, job control), 44 (pipes and FIFOs), 62
  (terminals) and 64 (pseudoterminals) are the Linux reference, by the
  maintainer of the man pages.
- Don Libes, *Exploring Expect* (O'Reilly, 1995). The book of Expect,
  and still the best discussion of driving interactive programs: the
  echo, timing and buffering problems of chapter 30 are all in it.
- Marc J. Rochkind, *Advanced UNIX Programming*, 2nd edition
  (Addison-Wesley, 2004). A clear alternative to Stevens, with a good
  chapter on terminals.

### G.2 Articles

- Linus Åkesson, "The TTY demystified",
  [linusakesson.net/programming/tty](https://www.linusakesson.net/programming/tty/).
  The classic explanation of the line discipline, sessions and job
  control, with diagrams.
- Paul Flo Williams, "A parser for DEC's ANSI-compatible video
  terminals",
  [vt100.net/emu/dec_ansi_parser](https://vt100.net/emu/dec_ansi_parser).
  The state machine behind `muxi` and most emulators (31.2). The rest
  of vt100.net has the DEC terminal manuals.
- "Synchronized output" specification, by Christian Parpart
  ([gist](https://gist.github.com/christianparpart/d8a62cc1ab659194337d73e399004036)):
  mode 2026 (B.6).
- The terminal working group's specifications at freedesktop.org,
  [gitlab.freedesktop.org/terminal-wg/specifications](https://gitlab.freedesktop.org/terminal-wg/specifications):
  proposals and discussions for hyperlinks, colors, and other
  extensions.

### G.3 Standards and references

- POSIX, "General Terminal Interface" (the termios chapter of the
  Base Definitions),
  [pubs.opengroup.org/onlinepubs/9799919799/basedefs/V1_chap11.html](https://pubs.opengroup.org/onlinepubs/9799919799/basedefs/V1_chap11.html).
- ECMA-48, *Control Functions for Coded Character Sets*,
  [ecma-international.org](https://ecma-international.org/publications-and-standards/standards/ecma-48/).
- Thomas Dickey, "XTerm Control Sequences",
  [invisible-island.net/xterm/ctlseqs/ctlseqs.html](https://invisible-island.net/xterm/ctlseqs/ctlseqs.html).
  The de facto reference for what terminals understand (Appendix B).
- ncurses and terminfo:
  [invisible-island.net/ncurses](https://invisible-island.net/ncurses/),
  and the `terminfo(5)` manual,
  [invisible-island.net/ncurses/man/terminfo.5.html](https://invisible-island.net/ncurses/man/terminfo.5.html).
- The kitty keyboard protocol,
  [sw.kovidgoyal.net/kitty/keyboard-protocol](https://sw.kovidgoyal.net/kitty/keyboard-protocol/).
- The asciicast v2 format,
  [docs.asciinema.org/manual/asciicast/v2](https://docs.asciinema.org/manual/asciicast/v2/)
  (29.6).
- Unicode Standard Annex #11, "East Asian Width",
  [unicode.org/reports/tr11](https://www.unicode.org/reports/tr11/):
  where character widths come from (E.14, E.29).
- The `NO_COLOR` convention, [no-color.org](https://no-color.org).

### G.4 Manual pages

Available locally with `man` if your distribution installs the
`man-pages` package (it was not installed on the machine of this
tutorial; the names below were checked on man7.org), and online at
[man7.org](https://man7.org/linux/man-pages/). The most useful for
this tutorial:

- `termios(3)`, `ioctl_tty(2)` (formerly `tty_ioctl(4)`; recent
  man-pages releases also have one page per request, such as
  `TIOCSCTTY(2const)`), `pty(7)`,
  `posix_openpt(3)`, `ptsname(3)`, `openpty(3)`, `forkpty(3)`;
- `pipe(7)`, `pipe(2)`, `fifo(7)`, `splice(2)`;
- `signal(7)`, `signal-safety(7)`, `sigaction(2)`, `signalfd(2)`;
- `credentials(7)` (process groups and sessions), `setsid(2)`,
  `setpgid(2)`, `tcsetpgrp(3)`;
- `console_codes(4)`: the sequences of the Linux console, which is a
  terminal emulator in the kernel;
- `stty(1)`, `tput(1)`, `infocmp(1)`, `tic(1)`, `script(1)`,
  `scriptreplay(1)`, `setsid(1)`;
- `proc_pid_stat(5)`, `proc_pid_fd(5)` and the other `/proc` pages.

The GNU manuals: `info stty` (coreutils, with the exact list of what
`sane` sets), and the bash manual's "Job Control" chapter
([gnu.org](https://www.gnu.org/software/bash/manual/html_node/Job-Control.html)).

### G.5 Source code worth reading

- The Linux TTY layer: `drivers/tty/n_tty.c` (the line discipline),
  `drivers/tty/pty.c`, `drivers/tty/tty_jobctrl.c`, in the kernel
  tree ([n_tty.c on GitHub](https://github.com/torvalds/linux/blob/master/drivers/tty/n_tty.c)).
- util-linux's `script`, `scriptreplay` and `setsid`, in
  `term-utils/` and `sys-utils/` of the util-linux repository.
- tmux, [github.com/tmux/tmux](https://github.com/tmux/tmux): `input.c`
  (the parser), `screen-write.c`, `tty.c` (output to the real
  terminal), `client.c` and `server.c` (detaching, 31.5).
- Expect, [core.tcl-lang.org/expect](https://core.tcl-lang.org/expect/index):
  `exp_clib.c` and `pty_termios.c`.
- creack/pty, [github.com/creack/pty](https://github.com/creack/pty):
  small enough to read in an evening, and the source of 27.1's
  surprise.
- Zellij, [github.com/zellij-org/zellij](https://github.com/zellij-org/zellij):
  a multiplexer in Rust.

### G.6 Language documentation

- **C**: the man pages above; glibc's manual, chapter "Low-Level
  Terminal Interface" (`info libc`).
- **Raku**: [docs.raku.org](https://docs.raku.org), in particular
  [NativeCall](https://docs.raku.org/language/nativecall), `Proc`,
  `Proc::Async`, `Supply` and "Concurrency"; modules on
  [raku.land](https://raku.land); Rakudo Star at
  [rakudo.org/star](https://rakudo.org/star).
- **Rust**: [`std::process`](https://doc.rust-lang.org/std/process/index.html),
  [nix](https://docs.rs/nix), [signal-hook](https://docs.rs/signal-hook),
  [portable-pty](https://docs.rs/portable-pty),
  [crossterm](https://docs.rs/crossterm), [ratatui.rs](https://ratatui.rs).
- **Go**: [`os/exec`](https://pkg.go.dev/os/exec),
  [`golang.org/x/term`](https://pkg.go.dev/golang.org/x/term),
  [creack/pty](https://github.com/creack/pty),
  [go-runewidth](https://github.com/mattn/go-runewidth), and the Charm
  libraries at [charm.land](https://charm.land) (Bubble Tea's
  repository: [github.com/charmbracelet/bubbletea](https://github.com/charmbracelet/bubbletea)).

## Appendix H. Extracting the listings

Every listing that is a whole file starts with a comment naming its
path (`// file: c/ptyscript2.c`, `# file: raku/rless.raku`). This
script copies all of them out of the document:

```python
# file: tools/extract.py
# Write every listing of term.md that starts with a "file:" comment
# to that path under OUTDIR.   python3 extract.py OUTDIR term.md
import os, re, sys

outdir, doc = sys.argv[1], sys.argv[2]
lines = open(doc, encoding="utf-8").read().split("\n")
i = count = 0
while i < len(lines):
    fence = re.match(r"^(\s*)```\w+\s*$", lines[i])
    if not fence:
        i += 1
        continue
    indent = fence.group(1)                 # listings inside list items
    end = i + 1
    while end < len(lines) and not re.match(rf"^{indent}```\s*$", lines[end]):
        end += 1
    name = re.match(r"^\s*(?://|#|--)\s*file:\s*(\S+)", lines[i + 1])
    if name:
        body = [l[len(indent):] if l.startswith(indent) else l
                for l in lines[i + 1:end]]
        path = os.path.join(outdir, name.group(1))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(body) + "\n")
        count += 1
    i = end + 1
print(f"{count} files written under {outdir}")
```

```console
$ python3 extract.py src term.md
102 files written under src
$ cd src/c && make && cd ../..
$ cd src/go && go mod init termtut && go mod tidy && go build ./... && cd ../..
$ cd src/rust && cargo build --release && cd ../..
$ cd src/raku && for f in *.raku; do raku -Ilib -c $f; done
```

The C tree has its `Makefile`, and the Rust tree its `Cargo.toml`.
The Go tree has no `go.mod` listing: `go mod tidy` finds the modules
from the imports and writes `go.mod` and `go.sum`. Run that way, on an
empty directory, the four commands above built everything. The
programs that are solutions to exercises (`ptyscript2.c`,
`ptyreplay.c`, `keysplit.c`, `capture.c`) are not in the `Makefile`.
Build them with the `gcc` line given with each one.
