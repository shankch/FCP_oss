/-
The reference semantics of FCP-PL: what every expression, pattern and item
means on a trace, written as closed forms over the past of the trace (no
registers).  `FCP/Monitor.lean` proves that the register machines the
compiler emits compute these closed forms; the oracle (`Main.lean`)
evaluates them, and the test suite compares the result, cycle by cycle,
with a simulation of the compiled monitor.
-/
import FCP.Syntax

namespace FCP

/-! ## Values -/

/-- A value: an exact integer (a condition is 0 or 1, a bit-vector its
unsigned value), or a sequence (a string, a list) of integers. -/
inductive Val where
  | int (n : Int)
  | seq (l : List Int)
deriving Repr, BEq, Inhabited

namespace Val

/-- A value where a number is expected.  A one-character literal is its code. -/
def toInt : Val → Int
  | .int n => n
  | .seq [c] => c
  | .seq _ => 0

def toSeq : Val → List Int
  | .seq l => l
  | .int _ => []

def truth (v : Val) : Bool := v.toInt != 0

def ofBool (b : Bool) : Val := .int (if b then 1 else 0)

end Val

def inRange (lo hi c : Int) : Bool := decide (lo ≤ c) && decide (c ≤ hi)

/-- The number of one bits of a natural number. -/
def popcount (n : Nat) : Nat := (List.range (Nat.log2 n + 1)).countP fun i => n.testBit i

def evalUn (op : UnOp) (v : Val) : Val :=
  let a := v.toInt
  match op with
  | .not => .ofBool (a == 0)
  | .neg => .int (-a)
  | .bnot w => .int ((2 : Int) ^ w - 1 - a)
  | .slice hi lo => .int (((a.toNat >>> lo) % 2 ^ (hi - lo + 1) : Nat) : Int)
  | .anyBit => .ofBool (a != 0)
  | .allBits w => .ofBool (a == (2 : Int) ^ w - 1)
  | .countones => .int (popcount a.toNat : Nat)
  | .onehot => .ofBool (a != 0 && (a.toNat &&& (a.toNat - 1)) == 0)
  | .onehot0 => .ofBool ((a.toNat &&& (a.toNat - 1)) == 0)
  | .len => .int (v.toSeq.length : Nat)
  | .isdigit => .ofBool (inRange 48 57 a)
  | .isalpha => .ofBool (inRange 65 90 a || inRange 97 122 a)
  | .isalnum => .ofBool (inRange 48 57 a || inRange 65 90 a || inRange 97 122 a)
  | .islower => .ofBool (inRange 97 122 a)
  | .isupper => .ofBool (inRange 65 90 a)
  | .isspace => .ofBool (inRange 9 13 a || a == 32)
  | .lower => .int (if inRange 65 90 a then a + 32 else a)
  | .upper => .int (if inRange 97 122 a then a - 32 else a)

/-- Equality: of two sequences, or of two numbers. -/
def valEq : Val → Val → Bool
  | .seq a, .seq b => a == b
  | a, b => a.toInt == b.toInt

def evalBin (op : BinOp) (x y : Val) : Val :=
  let a := x.toInt
  let b := y.toInt
  match op with
  | .and => .ofBool (a != 0 && b != 0)
  | .or => .ofBool (a != 0 || b != 0)
  | .imp => .ofBool (a == 0 || b != 0)
  | .iff => .ofBool ((a != 0) == (b != 0))
  | .eq => .ofBool (valEq x y)
  | .ne => .ofBool (!valEq x y)
  | .lt => .ofBool (decide (a < b))
  | .le => .ofBool (decide (a ≤ b))
  | .gt => .ofBool (decide (a > b))
  | .ge => .ofBool (decide (a ≥ b))
  | .add => .int (a + b)
  | .sub => .int (a - b)
  | .mul => .int (a * b)
  | .mod => .int (a % b)
  | .shl => .int (a * (2 : Int) ^ b.toNat)
  | .shlw w => .int ((a * (2 : Int) ^ b.toNat) % (2 : Int) ^ w)
  | .shr => .int (a / (2 : Int) ^ b.toNat)
  | .band => .int ((a.toNat &&& b.toNat : Nat) : Int)
  | .bor => .int ((a.toNat ||| b.toNat : Nat) : Int)
  | .bxor => .int ((a.toNat ^^^ b.toNat : Nat) : Int)
  | .min => .int (if a ≤ b then a else b)
  | .max => .int (if a ≤ b then b else a)
  | .mem => .ofBool (y.toSeq.contains a)
  | .idx =>
    match x with
    | .seq l => .int (if b < 0 then 0 else l.getD b.toNat 0)
    | .int n => .ofBool (decide (0 ≤ b) && n.toNat.testBit b.toNat)

/-! ## Time: resets, and the operators over the past -/

/-- No cycle in `[a, b)` is a reset. -/
def quiet (rst : Nat → Bool) (a b : Nat) : Bool :=
  (List.range (b - a)).all fun i => !rst (a + i)

/-- At least `d` cycles have passed since the last reset ended: the `d`
cycles before `t` exist and none of them is a reset. -/
def segGe (rst : Nat → Bool) (d t : Nat) : Bool :=
  decide (d ≤ t) && quiet rst (t - d) t

/-- `once(a)`: `a` held at a cycle with no reset between it and now. -/
def onceS (rst : Nat → Bool) (a : Nat → Bool) (t : Nat) : Bool :=
  (List.range (t + 1)).any fun s => a s && quiet rst s t

/-- `hist(a)`: `a` held at every cycle with no reset between it and now. -/
def histS (rst : Nat → Bool) (a : Nat → Bool) (t : Nat) : Bool :=
  (List.range (t + 1)).all fun s => a s || !quiet rst s t

/-- `since(a, b)`: `b` held at a cycle with no reset between it and now,
and `a` at every cycle after it. -/
def sinceS (rst : Nat → Bool) (a b : Nat → Bool) (t : Nat) : Bool :=
  (List.range (t + 1)).any fun s =>
    b s && quiet rst s t && (List.range (t - s)).all fun i => a (s + 1 + i)

/-! ## Expressions -/

/-- What an expression is evaluated on: the trace (a value of every signal
at every cycle, and which cycles are resets), the values of the ghosts at
every cycle, and one value of every rigid variable. -/
structure Env where
  sig : String → Nat → Val
  rst : Nat → Bool
  ghost : String → Nat → Int
  rigid : String → Int

/-- The value of an expression at cycle `t`; `bv` holds the variables of the
enclosing quantifiers, the innermost first.

The operand of `once`, `hist` and `since` is skipped at the cycles where it
is not defined (fewer than its look-back after a reset): it counts as false
for `once` and for the second operand of `since`, as true for `hist` and
for the first operand of `since`. -/
def eval (env : Env) : List Int → Expr → Nat → Val
  | _, .num n, _ => .int n
  | _, .lst l, _ => .seq l
  | _, .sig x, t => env.sig x t
  | _, .ghost g, t => .int (env.ghost g t)
  | _, .rigid r, _ => .int (env.rigid r)
  | bv, .bvar i, _ => .int (bv.getD i 0)
  | bv, .un op a, t => evalUn op (eval env bv a t)
  | bv, .bin op a b, t => evalBin op (eval env bv a t) (eval env bv b t)
  | bv, .ite c a b, t => if (eval env bv c t).truth then eval env bv a t else eval env bv b t
  | bv, .quant q n b, t =>
    let ks := List.range (eval env bv n t).toInt.toNat
    match q with
    | .all => .ofBool (ks.all fun (k : Nat) => (eval env (Int.ofNat k :: bv) b t).truth)
    | .any => .ofBool (ks.any fun (k : Nat) => (eval env (Int.ofNat k :: bv) b t).truth)
    | .count => .int (Int.ofNat (ks.countP fun (k : Nat) => (eval env (Int.ofNat k :: bv) b t).truth))
    | .sum => .int (ks.foldl (fun (acc : Int) (k : Nat) => acc + (eval env (Int.ofNat k :: bv) b t).toInt) 0)
  | bv, .prev n a, t => if n ≤ t then eval env bv a (t - n) else .int 0
  | bv, .once a, t =>
    .ofBool (onceS env.rst (fun s => segGe env.rst a.lookback s && (eval env bv a s).truth) t)
  | bv, .hist a, t =>
    .ofBool (histS env.rst (fun s => !segGe env.rst a.lookback s || (eval env bv a s).truth) t)
  | bv, .since a b, t =>
    .ofBool (sinceS env.rst
      (fun s => !segGe env.rst a.lookback s || (eval env bv a s).truth)
      (fun s => segGe env.rst b.lookback s && (eval env bv b s).truth) t)

/-- An expression as a condition, at cycle `t`. -/
def holds (env : Env) (e : Expr) (t : Nat) : Bool := (eval env [] e t).truth

end FCP
