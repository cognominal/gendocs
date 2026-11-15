# Native and C-like arrays in Raku

Tested on **Rakudo Star v2026.08 / MoarVM 2026.08**, Linux x86-64.

Raku has no stack-allocated arrays. Typed pointer access is expressed by
indexing a `Pointer[T]` (there is no C-style `p + n` that stays typed).
The C analogue for ordinary values is a **shaped native array**:

```raku
my int32 @a[10];      # roughly: int32_t a[10];
```

It is a fixed-size, zero-initialized, flat native buffer (MoarVM
`MultiDimArray` representation) with bounds checks. Everything else below
is about how that object behaves, and how the other array-ish types
compare when an index falls outside the valid range.

---

## 1. Which container should I use?

| Declaration | Type | Size | Element storage | C-like? |
|---|---|---|---|---|
| `my int32 @a[10]` | `array[int32]` | fixed at declaration | native, contiguous | **yes** |
| `my int32 @a[$n]` | `array[int32]` | fixed at runtime | native, contiguous | **yes** |
| `my int32 @a` | `array[int32]` | unbounded, grows on write | native | no, but fast |
| `my int32 @a[*]` | `array[int32]` | same as above | native | explicit "unbounded" |
| `my @a` | `Array` | dynamic | boxed `Scalar` containers | no |
| `my int32 @a = ...` | `array[int32]` | dynamic | native | no |
| `$x = array[int32].new(:shape(10,))` | `array[int32]` | fixed | native | **yes** |
| `CArray[int32]` | `CArray[int32]` | growable, malloc-backed | native | for NativeCall |
| `buf8` / `blob8` | `Buf[uint8]` / `Blob[uint8]` | growable / immutable | bytes | for binary data |

Element types usable in shaped native arrays include
`int8 int16 int32 int64`, `uint8 uint16 uint32 uint64`, `int uint`,
`num32 num64 num`, `str`, and `atomicint`. `bool` is **not** a Raku type;
use `uint8` or an object shaped array of `Bool`.

---

## 2. Shaped native arrays

### 2.1 Declaration

```raku
my int32 @a[10];                 # 10 elements, all zero
my int32 @b[4] = 1, 2, 3, 4;     # initializer
my int32 @m[3;4];                # 3 x 4 matrix, row-major
my num32 @f[3];
my str   @s[3];
my atomicint @c[3];

my $n = 8;
my int32 @c[$n];                 # runtime dimension is allowed
my $rows = 2; my $cols = 3;
my int32 @d[$rows;$cols];
```

`@a.WHAT` is `(array[int32])`; `@a.of` is `(int32)`; `@a.shape` is a
`List` such as `(10,)` or `(3,4)`.

Numeric elements start at `0` / `0e0`; `atomicint` starts at `0`.
`str` elements start as a **null string**, not a concrete empty string:
`.defined` is `True`, but `.chars`, `~`, `eq`, and even `.raku` die with
`... requires a concrete string, but got null`. Assign a value before
using a `str` slot.

### 2.2 Indexing

```raku
@a[0]     = 42;
@a[*-1]   = 7;        # last element, "Whatever" arithmetic
say @a[0];            # 42
say @a[*-1];          # 7
say @a[1..2];         # slice -> an array[int32] object
say @a[1,2];          # index list -> a List
```

Negative **literals** are rejected at compile time:

```text
Unsupported use of a negative -1 subscript to index from the end.
In Raku please use: a function such as *-1.
```

`@a[*-k]` resolves to a concrete negative index and then goes through the
normal bounds check (see below).

Index expressions are coerced to `Int`:

| Expression | Effect |
|---|---|
| `@a[3]` | normal |
| `@a[3.0]` | index 3 |
| `@a[1.9]` | index 1 (truncation) |
| `@a["3"]` | index 3 |
| `@a["3x"]` | dies: `This type cannot unbox to a native integer: P6opaque, Failure` |
| `@a[Int]`, `@a[Any]` | dies: `Unable to call postcircumfix [ (Int) ] with a type object` |

### 2.3 Multi-dimensional layout

`my int32 @m[3;4]` is row-major, flat:

```raku
@m[1;2]                 # row 1, column 2
# flat index = 1*4 + 2
@m.flat                 # Seq in row-major order
```

Measured ordering for `my int32 @m[2;3]` with some values:

```raku
@m[0;0]=1; @m[0;1]=2; @m[1;0]=3; @m[1;2]=6;
say @m.flat.list.raku;   # (1, 2, 0, 3, 0, 6)
```

For `my int32 @t[2;2;2]`:

```raku
@t[0;0;0]=1; @t[0;1;0]=2; @t[1;0;0]=3; @t[1;1;1]=8;
say @t.flat.list.raku;   # (1, 0, 2, 0, 3, 0, 0, 8)
```

So the flat index is the row-major linearization
`((i0 * d1) + i1) * d2 + i2 ...`. Four and more dimensions work too.

### 2.4 `.elems` and `.shape` — important gotcha

For a shaped array, `.elems` is the size of the **first dimension**, not
the total number of cells:

```raku
my int32 @m[2;3];
say @m.elems;          # 2   (!)
say @m.shape;          # (2 3)
say @m.flat.elems;     # 6
say [*] @m.shape;      # 6
```

For `my int32 @t[2;2;2;2]`: `.elems == 2`, `.shape == (2 2 2 2)`,
total `16`. Use `[*] @a.shape` or `@a.flat.elems` for the cell count.

### 2.5 Initialization and whole-array assignment (1-D)

```raku
my int32 @a[4] = 1, 2, 3, 4;   # ok
my int32 @b[4] = 1..4;         # ok
my int32 @c[4] = 1, 2, 3;      # ok: (1,2,3,0) -- missing cells become 0
my int32 @d[4] = [1,2,3,4];    # ok (Array is iterable)
my int32 @e[4] = 5;            # ok: (5,0,0,0) -- single Int goes to [0]
my int32 @f[4] = "x";          # dies X::Assignment::ToShaped
my int32 @g[4] = 1,2,3,4,5;    # dies: X::AdHoc
                               # "This type (List) does not support positional operations"
```

The same applies to later whole-array assignment:

```raku
my int32 @a[4];
@a = 1, 2, 3, 4;   # ok
@a = 1, 2, 3;      # ok -> (1,2,3,0)
@a = 1..4;         # ok
@a = 1..5;         # dies (same List/positional message)
@a = (1..Inf).lazy;# dies
```

For a single scalar (`@a = 5`) only slot 0 changes; the other cells keep
their current values. (A freshly declared array is already zero-filled,
so it looks like the rest were zeroed.) Measured:

```raku
my int32 @a[4] = 1,2,3,4;
@a = 5;
say @a.list;        # (5, 2, 3, 4)
```

### 2.6 Initialization and assignment (2-D and higher)

Multi-dimensional shaped arrays require **structured** data: a list of
row arrays/lists.

```raku
my int32 @m[2;3] = [1,2,3], [4,5,6];   # ok
my int32 @n[2;3];
@n = [1,2,3], [4,5,6];                 # ok
```

Flat data fails:

```raku
my int32 @m[2;3] = 1,2,3,4,5,6;        # internal error (observed):
                                       # Method BOOTIntArray.item not found

my int32 @m[2;3];
@m = 1,2,3,4,5,6;                      # same internal error
```

Wrong number of rows/cells produces a hard bounds error while copying,
for example a 3-row source into a 2-row destination:

```raku
my int32 @q[2;3];
@q = [1,2],[3,4],[5,6];
# dies: Index 2 for dimension 1 out of range (must be 0..1)
```

Calling `.STORE` directly on a multi-dimensional shaped array is even
pickier:

```raku
my $m = array[int32].new(:shape((2,3)));
$m.STORE([[1,2,3],[4,5,6]]);
# dies X::Assignment::ArrayShapeMismatch:
# "Cannot assign an array of shape * to an array of shape 2 3"

$m.STORE($m.clone);      # ok -- same shaped type and dimensions
```

Guidance: use `@m = [...] , [...]` for shaped arrays declared with an
`@` sigil; use element assignment for runtime-created arrays.

### 2.7 Copying, binding, and aliasing

```raku
my int32 @a[4] = 1,2,3,4;

my $clone = @a.clone;      # independent copy, still array[int32] shape (4)
$clone[0] = 99;            # @a[0] is still 1

my $alias = @a;            # scalar assignment: same object
$alias[1] = 77;            # @a[1] is now 77

my @plain = @a;            # copies into a *plain* Array
say @plain.WHAT;           # (Array) -- shape/native type lost
```

Binding also keeps the shaped object:

```raku
my @b := @a;               # alias, shape retained
my int32 @c := @a;         # alias, shape retained
```

**Do not** assign a runtime-created shaped array to a native `@`-sigil
variable:

```raku
my int32 @x = array[int32].new(:shape(4,));
# Rakudo 2026.08: segfault (exit 139)

my @x = array[int32].new(:shape(4,));
# works, but @x is now a plain Array (shape lost)

my $x = array[int32].new(:shape(4,));    # safe, keeps shape
my int32 @x := array[int32].new(:shape(4,));   # safe, binds
```

Assigning an *unbounded* native array to `my int32 @x = ...` does work
(it copies); the crash is specific to the shaped source in this build.

### 2.8 Slices

Slicing a shaped native array produces a **new unbounded native array**,
not another shaped array:

```raku
my int32 @a[4] = 1,2,3,4;
my $s = @a[1..2];
say $s.WHAT;    # (array[int32])
say $s.shape;   # (*,)
say $s.list;    # (2, 3)
```

Consequences:

- Out-of-bounds reads on the slice return `0` instead of throwing.
- Out-of-bounds writes on the slice grow it.
- Slice assignment into the original still writes back:
  `@a[1..2] = (9,8)` works and bounds-checks against `@a`.
- A full-range slice `@a[0..10]` on a 4-element array throws at the
  original array (index 4), before any slice object is built.
- `@a[0,2]` (index list) returns a plain `List`; `@a[*]` returns the
  whole array object (rendered with `.item` attached).

For an **object** shaped array (`my @a[3]`, `my Str @a[3]`), a slice
returns a `List` instead.

### 2.9 Runtime shapes

Literal-shape declarations accept runtime dimension expressions:

```raku
my $n = 8;
my int32 @a[$n];               # shape (8)
my $r = 2; my $c = 3;
my int32 @m[$r;$c];            # shape (2 3)
```

Or construct the object explicitly:

```raku
my $a = array[int32].new(:shape(8,));          # 1-D, shape (8)
my $m = array[int32].new(:shape((3,4)));       # 2-D, shape (3 4)
my $t = array[int32].new(:shape((2,2,2)));     # 3-D
my $big = array[int32].new(:shape(1_000_000,));
```

Note the extra parentheses for multi-dimensional shapes:
`:shape((3,4))`, not `:shape(3,4)`.

Initialize at construction:

```raku
my $a = array[int32].new(:shape(4,), 1, 2, 3, 4);   # ok
my $b = array[int32].new(:shape(4,), 1, 2, 3);      # ok, pads zero
my $c = array[int32].new(:shape(4,), 1, 2, 3, 4, 5);# dies (too many)
my $d = array[int32].new(:shape(4,), 1..4);         # ok
```

`set-shape` is **functional**, not mutating:

```raku
my $u = array[int32].new;          # shape (*)
my $v = $u.set-shape(4);           # $v has shape (4)
say $u.shape;                      # still (*)
$u = $u.set-shape(3);              # reassign to keep the new shape
```

### 2.10 Restrictions

```raku
my int32 @a[0];        # dies X::IllegalDimensionInShape:
                       # "Illegal dimension in shape: 0. All dimensions
                       #  must be integers bigger than 0"
my int32 @a[-1];       # same, for -1
my int32 @a[2;0];      # same, for 0
my int32 @a[*;3];      # dies X::NYI: "Jagged array shapes not yet implemented. Sorry."
```

Zero-sized shaped arrays do not exist. If you need an empty container,
use an unbounded native array (`my int32 @a`) or a plain `Array`.

---

## 3. Out-of-bounds access — what actually happens

This is where the container types differ sharply. The short version:

| Container | Read `@x[N]` (N >= elems) | Write `@x[N] = v` | `@x[N]:exists` |
|---|---|---|---|
| shaped native (`my int32 @a[N]`) | **throws** `X::AdHoc` | **throws** `X::AdHoc` | `False` |
| shaped object (`my @a[N]`, `my Str @a[N]`) | **throws** `X::AdHoc` | **throws** `X::AdHoc` | `False` |
| unbounded native (`my int32 @a`, `@a[*]`) | returns `0` | grows, zero-fills | `False` |
| `Array` / `List` | returns `Any` (undefined) | `Array` grows; `List` cannot be assigned to | `False` |
| `Buf[uint8]` | returns `0` | grows, zero-fills | `False` |
| `Blob[uint8]` | returns `Failure(X::OutOfRange)` | dies `X::Assignment::RO` | `False` |
| `CArray[T]` | returns `0` (observed) | grows/reallocates | `False` |
| `Pointer[T]` | raw memory, unchecked | raw memory, unchecked | n/a |

Negative/Whatever indices are a separate path (see 3.7).

### 3.1 Shaped native arrays: hard throw on read and write

Both reading and writing outside `0 ..^ elems` die immediately. This is
not a soft `Failure`.

```raku
my int32 @a[4] = 1,2,3,4;

@a[4];          # dies
@a[4] = 5;      # dies
@a[1000];       # dies
@a[*-5];        # dies (resolves to -1)
```

The message is:

```text
Index 4 for dimension 1 out of range (must be 0..3)
Index 1000 for dimension 1 out of range (must be 0..3)
Index -1 for dimension 1 out of range (must be 0..3)
```

The exception class is **`X::AdHoc`**, not `X::OutOfRange`. The dimension
number is 1-based. The valid range in the message is inclusive.

This happens even in void/sink context:

```raku
@a[4];          # still dies
```

An uncaught throw terminates the process with exit status `1` and a
backtrace pointing at the indexing expression.

Catching it:

```raku
{
    my $v = @a[4];
    say "got $v";
    CATCH {
        when X::AdHoc { say "out of range: ", .message }
    }
}
```

Or with `try` (note `$!` is set in the caller's scope):

```raku
my $v;
try { $v = @a[4] };
say $v.defined;    # False
say $! // "no error";   # X::AdHoc ... Index 4 ...
```

Writing out of bounds does not modify the array. `push`, `pop`, `shift`,
`unshift`, `splice` are all forbidden on a fixed-shape array:

```text
X::IllegalOnFixedDimensionArray:
Cannot push a fixed-dimension array
Cannot pop a fixed-dimension array
Cannot shift a fixed-dimension array
Cannot unshift a fixed-dimension array
Cannot splice a fixed-dimension array
```

### 3.2 Shaped native arrays: existence, deletion, binding

`EXISTS-POS` is safe and does not throw:

```raku
say @a[3]:exists;    # True
say @a[4]:exists;    # False
say @a[*-1]:exists;  # True
say @a[*-5]:exists;  # False (still safe, no throw)
```

`DELETE-POS` and `BIND-POS` are not supported on native shaped storage:

```raku
@a[4]:delete;        # X::Delete: Cannot delete from a native int array
@a[0]:delete;        # same, even in bounds
@a.BIND-POS(0, 5);   # X::Bind: Cannot bind to a natively typed shaped array
```

For `str` arrays the message is `Cannot delete from a native str array`.

Object shaped arrays are different: `:delete` and `BIND-POS` do work.

```raku
my Str @s[3] = <a b c>;
say @s[0]:delete;          # "a" (slot removed)
@s.BIND-POS(0, "x");       # ok
```

### 3.3 Shaped arrays: slices and out-of-range slices

A slice is bounds-checked against the source at the time the elements are
fetched:

```raku
@a[0..3];      # ok
@a[0..10];     # dies: Index 4 for dimension 1 out of range (must be 0..3)
@a[10..12];    # dies: Index 10 ...
@a[0,4];       # dies: Index 4 ...
@a[4,5];       # dies: Index 4 ...
```

As noted in 2.8, the *result* of an in-range slice is an unbounded native
array, so OOB on that result does not throw:

```raku
my $s = @a[1..2];
say $s[5];          # 0
$s[5] = 9;          # grows $s
```

### 3.4 Shaped arrays: multi-dimensional out-of-bounds

The message names the offending dimension and its valid range:

```raku
my int32 @m[3;4];

@m[3;0];    # Index 3 for dimension 1 out of range (must be 0..2)
@m[0;4];    # Index 4 for dimension 2 out of range (must be 0..3)
@m[3;0]=1;  # same throw on write
@m[0;4]=1;  # same throw on write
```

Wrong number of indices is a different error, and reads and writes do
not always produce the same message.

Too many indices:

```raku
my int32 @m[3;4];
@m[0;0;0];          # X::TooManyDimensions:
                    # Cannot access a 2 dimension array with 3 dimensions
@m[0;0;0] = 5;      # X::TooManyDimensions:
                    # Cannot assign to a 2 dimension array with 3 dimensions

my int32 @one[4];
@one[0;0];          # X::TooManyDimensions:
                    # Cannot access a 1 dimension array with 2 dimensions
```

Too few indices — 2-D and 3-D behave differently:

```raku
my int32 @m[3;4];
@m[0];              # X::AdHoc:
                    # Cannot access 2 dimension array with 1 indices
@m[0] = 5;          # same X::AdHoc message

my int32 @t[2;2;2];
@t[0];              # X::AdHoc:
                    # Cannot access 3 dimension array with 1 indices
@t[0;0];            # X::NYI: Partially dimensioned views of shaped
                    # arrays not yet implemented. Sorry.
@t[0;0] = 5;        # X::NotEnoughDimensions:
                    # Cannot assign to a 3 dimension array with only 2 dimensions
@t[0;0;0;0];        # X::TooManyDimensions:
                    # Cannot access a 3 dimension array with 4 dimensions
```

Summary of the wrong-arity cases:

| Indices | Read | Write |
|---|---|---|
| too many | `X::TooManyDimensions` "Cannot access ..." | `X::TooManyDimensions` "Cannot assign ..." |
| 2-D, one index | `X::AdHoc` "Cannot access 2 dimension array with 1 indices" | same |
| 3-D, two indices | `X::NYI` partial views | `X::NotEnoughDimensions` "Cannot assign to a 3 dimension array with only 2 dimensions" |

Partial views are not implemented at all:

```raku
@m[0;0..2];     # X::NYI: Partially dimensioned views ...
@m[0..2;0];     # X::NYI
@m[0..2;0..3];  # X::NYI
@m[*;0];        # X::NYI
@m[*-1;*-1];    # X::NYI
```

`:exists` works with a full index tuple:

```raku
@m[3;0]:exists;   # False
@m[0;4]:exists;   # False
@m[2;3]:exists;   # True
```

For 1-D shaped arrays, use `.elems` (which is the length). For 2-D and
higher, remember `.elems` is only the first dimension and write bounds
checks explicitly:

```raku
if $i >= 0 && $i < @m.shape[0]
   && $j >= 0 && $j < @m.shape[1] {
    @m[$i;$j] = $v;
}
```

or use `@m[$i;$j]:exists` before touching the cell.

### 3.5 Unbounded native arrays (`my int32 @a`, `@a[*]`)

These are dynamic native arrays, not shaped. Reading past `.elems` does
**not** throw; observed in 2026.08:

```raku
my int32 @d;
say @d.elems;     # 0
say @d[0];        # 0
say @d[5];        # 0
say @d.elems;     # still 0 -- read does not grow
```

Writing past the end grows the array and zero-fills the gap:

```raku
@d[5] = 1;
say @d.elems;             # 6
say @d.list;              # (0, 0, 0, 0, 0, 1)
@d[100] = 7;
say @d.elems;             # 101
```

Negative indices are checked, and throw:

```raku
my int32 @d;
@d[*-1];       # X::OutOfRange:
               # Index out of range. Is: -1, should be in 0..^Inf
               # (a real thrown exception, not a Failure)
```

`@d[5]:exists` is `False` and does not grow the array.

### 3.6 Plain `Array` and `List`

Boxed `Array` (`my @a`):

```raku
my @p = 1,2,3;

say @p[5];              # Any (undefined)
say @p[5].defined;      # False
say @p[5]:exists;       # False
@p[5] = 9;              # grows: [1,2,3,Any,Any,9]
say @p.elems;           # 6
```

`@p[*-5]` with only 3 elements is a **soft** `Failure`:

```raku
@p[*-5];
# Failure(X::OutOfRange.new(what => "Effective index", got => -2, ...))
```

`List` reads behave the same (`Any` for a positive OOB index, a
`Failure` for a Whatever index), but a `List` cannot grow, and an
out-of-range slice pads with `Nil`:

```raku
my $l = (1,2,3);
say $l[5];          # Any
say $l[0..5];       # (1, 2, 3, Nil, Nil, Nil)
```

### 3.7 Negative / Whatever indices

- `@a[-1]` is a **compile-time** error for all arrays:
  `Unsupported use of a negative -1 subscript ...`.
- `@a[*-1]` is the last element.
- `@a[*-k]` for `k > elems` resolves to a negative index:
  - shaped native: thrown `X::AdHoc` with `Index -n for dimension 1 ...`
  - unbounded native: thrown `X::OutOfRange` (`0..^Inf`)
  - plain `Array`/`List`: soft `Failure(X::OutOfRange)`
  - `Buf`: soft `Failure(X::OutOfRange)`
  - `Blob`: soft `Failure(X::OutOfRange)`
  - `CArray`: no negative check; reads return `0` (observed), and writes
    through a negative/out-of-range position are undefined behavior

### 3.8 `Buf` and `Blob`

`buf8` is mutable and growable; `blob8` is immutable.

```raku
my $b = buf8.new(1,2,3);
say $b[5];          # 0 (read does not grow)
say $b.elems;       # 3
$b[5] = 9;          # write grows
say $b.elems;       # 6
say $b.raku;        # Buf[uint8].new(1,2,3,0,0,9)
say $b[0..5];       # (1,2,3,0,0,9)
```

`Blob` returns a soft Failure on an out-of-range read, and is immutable:

```raku
my $bl = blob8.new(1,2,3);
my $x = $bl[5];     # Failure(X::OutOfRange "Index ... 0..2")
say $x.defined;     # False
$bl[5];             # if the Failure is sunk, the program dies (exit 1)
$bl[0] = 9;         # X::Assignment::RO: Cannot modify an immutable Int
$bl[0..5];          # dies X::OutOfRange (slice uses the checked path)
```

With `use fatal`, the Failure is thrown at creation even when assigned:

```raku
use fatal;
my $x = blob8.new(1,2,3)[5];   # throws here
```

Both `Buf` and `Blob` support `:exists` safely.

### 3.9 `CArray` (NativeCall)

`CArray` is a growable malloc-backed array, not a fixed-size C array.

```raku
use NativeCall;

my $c = CArray[int32].allocate(4);   # 4 zeroed int32 slots
say $c.elems;                        # 4
$c[0] = 1; $c[3] = 4;

say $c[4];                           # 0 (observed; no throw)
say $c[4]:exists;                    # False -- index 4 is out of range
$c[4] = 9;                           # grows the array
say $c.elems;                        # 5
say $c[4]:exists;                    # True now
$c[100] = 7;                         # grows to 101
```

Important construction facts:

- `CArray[int32].allocate(N)` allocates N zeroed elements.
- `CArray[int32].new(...)` treats its arguments as **values**:
  `new(4)` is a 1-element array containing `4`;
  `new(1,2,3)` is a 3-element array;
  `new(@shaped)` copies the values.
- There is no `(pointer, length)` constructor. `CArray.new($ptr, 4)` is
  read as the two values `$ptr` and `4`.

Reads past the known length return `0` in this build; writes past the
known length reallocate and grow the array. Do not rely on the `0`:
for a pointer-backed CArray, an out-of-range read is raw memory, and a
write beyond the allocation is undefined behavior.

`:exists` is bounds-aware. Index type objects (`$c[Any]`) die with
`Cannot use 'Any' as an index`.

### 3.10 Object shaped arrays

Object shaped arrays (`my @a[3]`, `my Str @a[3]`) have the same
out-of-range throw as native shaped arrays:

```raku
my @a[3] = <x y z>;
@a[3];             # Index 3 for dimension 1 out of range (must be 0..2)
@a[3] = 'w';       # same
@a[3]:exists;      # False
```

Differences from native shaped arrays:

- `:delete` works (returns the removed value).
- `BIND-POS` works.
- `push` / `pop` / `splice` still die with
  `X::IllegalOnFixedDimensionArray`.
- Slicing yields a `List`, not an unbounded native array.
- `.elems` on a 2-D object shaped array is still only the first
  dimension (`my @o[2;3]` -> `.elems == 2`, `.flat.elems == 6`).

---

## 4. C interoperability

### 4.1 Shaped arrays cannot be cast to pointers

The shaped native array has MoarVM representation `MultiDimArray`, not
`VMArray`/`CArray`, so this fails:

```raku
my int32 @a[4] = 1,2,3,4;
nativecast(Pointer[int32], @a);
# X::AdHoc: Native call cast expected return type with CPointer,
# CStruct, CArray, or VMArray representation,
# but got a MultiDimArray (array[int32])
```

If C must touch the memory, use `CArray` (or a `Buf`) from the start, or
copy:

```raku
use NativeCall;
my CArray[int32] $c = CArray[int32].new(@a);   # copies values
$c[0] = 99;                                     # @a[0] unchanged
```

### 4.2 Passing a CArray to C

```raku
use NativeCall;

sub memset(Pointer $p, int32 $c, size_t $n)
    is native('libc.so.6') { * }

my CArray[int32] $c = CArray[int32].allocate(10);
memset(nativecast(Pointer, $c), 0, 4 * 10);     # works

# illustrative: bind to a real library that exports fill(int32_t*, size_t)
sub fill(CArray[int32] $p, size_t $n)
    is native('./libfoo.so') { * }

fill($c, $c.elems);
```

`nativecast(Pointer, $c)` (or `Pointer[int32]`) gives the raw address;
`Pointer[T]` indexing is unchecked raw memory access.

### 4.3 Pointer-backed CArrays have unknown length

```raku
my $p = nativecast(Pointer[int32], $c);
my $w = nativecast(CArray[int32], $p);   # no length information
$w[0];                                   # reads memory through the pointer
$w.elems;
# X::AdHoc: Don't know how many elements a C array returned from a library
```

For pointer-backed CArrays:

- reads go through the pointer (no bounds check),
- writes go through the pointer,
- `.elems` throws because the length is unknown,
- do not write beyond the actual allocation.

### 4.4 Growth can detach aliases

A CArray created by `.allocate`/`.new` owns its buffer. Writing beyond
its current `elems` reallocates:

```raku
my CArray[int32] $a = CArray[int32].allocate(4);
my $w = nativecast(CArray[int32], nativecast(Pointer[int32], $a));
$w[4] = 55;     # writes through the old pointer
say $a[4];      # 0 -- $a still has elems 4 and does not see it
$a[10] = 101;   # reallocates $a; $w now points at the old buffer
```

Moral: keep the `CArray` as the owner; do not mix pointer views and
growth.

### 4.5 Buf/Blob are VMArrays

`buf8` and `blob8` can be cast to pointers, unlike shaped arrays:

```raku
my $b = buf8.new(1,2,3);
my $p = nativecast(Pointer[uint8], $b);
say $p[0];      # 1

my $p32 = nativecast(Pointer[int32], $b);
say $p32[0];    # 0x04030201 on little-endian (reinterpreted bytes)
```

Reading past the buffer's length through the pointer is undefined
behavior; Raku's bounds guarantees apply to `$b[...]`, not `$p[...]`.

### 4.6 Copying between representations

```raku
my int32 @a[3] = 1,2,3;

my $c = CArray[int32].new(@a);     # shaped -> CArray, copy
my $l = @a.list;                   # shaped -> List, copy
my $p = @a.flat;                   # shaped -> Seq, copy

my $b = buf8.new(@a);              # shaped -> Buf, copy (values must fit uint8)
```

`CArray.new(@a)` and `buf8.new(@a)` both copy; changing the source does
not modify the destination.

---

## 5. Gotchas checklist

1. `my @a = array[int32].new(:shape(N))` silently gives a plain `Array`,
   not a shaped native array. Use `my $a = ...` or bind with `:=`.
2. `my int32 @a = array[int32].new(:shape(N))` segfaults in Rakudo
   2026.08 (exit 139). Use `$` or binding.
3. `.elems` of a multi-dimensional shaped array is only the first
   dimension. Total is `[*] @a.shape` or `@a.flat.elems`.
4. Slicing a shaped native array produces an *unbounded* native array;
   OOB on that slice returns `0` instead of throwing.
5. `@a[-1]` is a compile error; use `@a[*-1]`.
6. Shaped arrays cannot `push`, `pop`, `shift`, `unshift`, or `splice`.
7. Native shaped arrays cannot `:delete` or `BIND-POS`; object shaped
   arrays can.
8. `my int32 @a[0]` is illegal; zero dimensions are rejected.
9. Jagged shapes such as `my int32 @a[*;3]` are not implemented.
10. Partial views (`@m[0;0..2]`, `@m[*-1;*-1]`, and `@t[0;0]` on a 3-D
    array) are `X::NYI`; a 2-D array with a single index gives
    `X::AdHoc` "Cannot access 2 dimension array with 1 indices".
11. `CArray[int32].new(4)` is one element with value 4, not four
    elements. Use `.allocate(4)`.
12. Reading past the end of an unbounded native array, a `Buf`, or an
    owned `CArray` returns `0` in this build; that is not a bounds check.
13. OOB on a shaped array is a thrown `X::AdHoc`, not a `Failure` and
    not `X::OutOfRange`; catch `X::AdHoc` or use `default`.
14. `Blob` OOB is a soft `Failure`; sinking it or using `use fatal`
    makes it fatal.
15. `@a[4.0]` is index 4; `@a[1.9]` truncates to 1. Indices are
    converted to `Int`.
16. Multi-dimensional shaped arrays require structured (nested)
    initializers; a flat list gives a hard error or an internal
    `Method BOOTIntArray.item not found`.
17. Passing a shaped array to `nativecast(Pointer, ...)` fails; use
    `CArray`/`Buf`.
18. `set-shape` returns a new array; calling it for side effects does
    nothing.
19. `array[int32].new(:shape((3,4)))` needs the extra parentheses; a
    scalar shape builds a 1-D array.
20. Do not assume `.shape` is a fixed-size array; it is a `List`.

---

## 6. Cheat sheet

### Declare

```raku
my int32 @a[10];                 # fixed, zeroed
my int32 @m[3;4];                # row-major matrix
my int32 @dyn;                   # growable native
my int32 @unbounded[*];          # same, explicit
my $r = array[int32].new(:shape((3,4)));   # runtime shape
```

### Bounds-safe access

```raku
# 1-D
if 0 <= $i < @a.elems {
    $v = @a[$i];
}

# any dimensionality, correct arity
if @m[$i;$j]:exists {
    $v = @m[$i;$j];
}

# or catch the throw
my $v;
try { $v = @m[$i;$j] };
if $! { ... }
```

### Cell count

```raku
my $cells = [*] @m.shape;        # multi-dim
my $n     = @a.elems;            # 1-D
```

### Convert

```raku
my $carray = CArray[int32].new(@a);     # copy to C memory
my $buf    = buf8.new(@a);              # copy to bytes
my $list   = @a.list;                   # copy to List
my $ptr    = nativecast(Pointer[uint8], $buf);   # Buf only
```

### Exact multi-dim messages

```text
Index I for dimension D out of range (must be 0..MAX)   # X::AdHoc
Cannot access N dimension array with M indices          # X::AdHoc (too few)
Cannot access a N dimension array with M dimensions     # X::TooManyDimensions (read)
Cannot assign to a N dimension array with M dimensions  # X::TooManyDimensions (write)
Cannot assign to a N dimension array with only M dimensions  # X::NotEnoughDimensions (write)
Partially dimensioned views of shaped arrays not yet implemented. Sorry.  # X::NYI
```

---

## 7. Minimal reproduction scripts

Shaped OOB read/write:

```raku
my int32 @a[4] = 1,2,3,4;
@a[4];
# Index 4 for dimension 1 out of range (must be 0..3)
# exit status 1
```

Safe probe:

```raku
my int32 @a[4] = 1,2,3,4;
say @a[3]:exists;   # True
say @a[4]:exists;   # False
```

Unbounded native read vs write:

```raku
my int32 @d;
say @d[5];          # 0
say @d.elems;       # 0
@d[5] = 1;
say @d.elems;       # 6
```

Blob failure:

```raku
my $bl = blob8.new(1,2,3);
my $x = $bl[5];     # soft Failure
say $x.defined;     # False
```

CArray allocation trap:

```raku
use NativeCall;
say CArray[int32].new(4).elems;        # 1
say CArray[int32].allocate(4).elems;   # 4
```
