/-
FCP-PL, elaborated: the abstract syntax the reference semantics is defined on.

A reading written in the surface language is elaborated before it reaches
this file: names are resolved (signal, ghost, rigid variable, variable of a
quantifier), definitions are inlined, parameters are replaced by their
values, and the three operators whose value depends on the width of a
bit-vector operand (`~`, `<<` on a bit-vector, `all`) carry that width.
-/
namespace FCP

/-- Operators of one operand. -/
inductive UnOp where
  | not                         -- `!a`
  | neg                         -- `-a`
  | bnot (w : Nat)              -- `~a` on a bit-vector of width `w`
  | slice (hi lo : Nat)         -- `a[hi:lo]`
  | anyBit                      -- `any(a)`
  | allBits (w : Nat)           -- `all(a)` on a bit-vector of width `w`
  | countones
  | onehot
  | onehot0
  | len                         -- `len(s)`
  | isdigit | isalpha | isalnum | islower | isupper | isspace
  | lower | upper
deriving Repr, BEq, Inhabited

/-- Operators of two operands. -/
inductive BinOp where
  | and | or | imp | iff
  | eq | ne | lt | le | gt | ge
  | add | sub | mul
  | mod                         -- floor modulo; the divisor is a positive constant
  | shl                         -- `a << b` on an integer
  | shlw (w : Nat)              -- `a << b` on a bit-vector of width `w`
  | shr
  | band | bor | bxor
  | min | max
  | mem                         -- `a in s`
  | idx                         -- `s[i]` on a sequence, bit `i` of a bit-vector
deriving Repr, BEq, Inhabited

inductive Quant where
  | all | any | count | sum
deriving Repr, BEq, Inhabited

/-- Expressions.  The four temporal operators are the primitives; `rose`,
`fell`, `stable` and `changed` are defined from `prev` below. -/
inductive Expr where
  | num (n : Int)
  | lst (l : List Int)                          -- a string or list literal
  | sig (name : String)                         -- an interface signal, this cycle
  | ghost (name : String)
  | rigid (name : String)
  | bvar (i : Nat)                              -- variable of the i-th enclosing quantifier
  | un (op : UnOp) (a : Expr)
  | bin (op : BinOp) (a b : Expr)
  | ite (c a b : Expr)
  | quant (q : Quant) (bound body : Expr)       -- `q(i < bound: body)`
  | prev (n : Nat) (a : Expr)                   -- the value of `a`, `n` cycles ago
  | once (a : Expr)                             -- `a` held at some cycle since the last reset
  | hist (a : Expr)                             -- `a` held at every cycle since the last reset
  | since (a b : Expr)                          -- `b` held, and `a` at every cycle after it
deriving Repr, Inhabited

namespace Expr

def rose (a : Expr) : Expr := .bin .and a (.un .not (.prev 1 a))
def fell (a : Expr) : Expr := .bin .and (.un .not a) (.prev 1 a)
def stable (a : Expr) : Expr := .bin .eq a (.prev 1 a)
def changed (a : Expr) : Expr := .bin .ne a (.prev 1 a)

/-- The number of cycles an expression looks back with `prev`.  Its value
in the first `lookback` cycles after a reset is not defined: it would read
the reset. -/
def lookback : Expr → Nat
  | .prev n a => n + a.lookback
  | .un _ a => a.lookback
  | .bin _ a b => Nat.max a.lookback b.lookback
  | .ite c a b => Nat.max c.lookback (Nat.max a.lookback b.lookback)
  | .quant _ n b => Nat.max n.lookback b.lookback
  | .once a => a.lookback
  | .hist a => a.lookback
  | .since a b => Nat.max a.lookback b.lookback
  | _ => 0

end Expr

/-- The patterns: how a condition is tied to time.  (`inorder`, the
transport pattern that tracks one item chosen without determinism, is not
part of this formalization.) -/
inductive Pattern where
  | invariant (cond : Expr)
  | implies (trigger cond : Expr)
  | next (trigger cond : Expr)
  | within (trigger cond : Expr) (lo hi : Nat)
  | holdUntil (trigger hold release : Expr)
  | boundedWait (cond : Expr) (max : Nat)
  | afterReset (cond : Expr)
deriving Repr, Inhabited

inductive Role where
  | property | assumption | scenario | dontcare
deriving Repr, BEq, Inhabited

/-- A ghost: a register of the reading, with a range, an initial value and
a next value (an expression without temporal operators). -/
structure Ghost where
  name : String
  lo : Int
  hi : Int
  init : Int
  next : Expr
deriving Repr, Inhabited

structure Rigid where
  name : String
  lo : Int
  hi : Int
deriving Repr, Inhabited

structure Item where
  id : String
  role : Role
  always : Bool                 -- checked in reset cycles too
  pattern : Pattern
deriving Repr, Inhabited

structure Reading where
  ghosts : List Ghost
  rigids : List Rigid
  items : List Item
deriving Repr, Inhabited

end FCP
