/-
Items: what a pattern, a ghost and an item of a reading mean on a trace.

Every definition is a closed form over the past of the trace.  The verdict
of an item at a cycle is `Item.ok`; an item is kept by a trace when its
verdict is true at every cycle (`Item.sat`).
-/
import FCP.Semantics

namespace FCP

/-! ## Patterns -/

/-- An expression that starts an obligation does so only where it is
defined: at least its look-back after the last reset.  (An item checked in
reset cycles too starts obligations everywhere.) -/
def armed (env : Env) (always : Bool) (e : Expr) (t : Nat) : Bool :=
  (always || segGe env.rst e.lookback t) && holds env e t

namespace Pattern

def exprs : Pattern → List Expr
  | .invariant c => [c]
  | .implies tr c => [tr, c]
  | .next tr c => [tr, c]
  | .within tr c _ _ => [tr, c]
  | .holdUntil tr h r => [tr, h, r]
  | .boundedWait c _ => [c]
  | .afterReset c => [c]

/-- The look-back of a pattern: the deepest of its expressions. -/
def depth (p : Pattern) : Nat := (p.exprs.map Expr.lookback).foldl Nat.max 0

/-- The look-back of the expression that starts the pattern's obligation. -/
def tdepth : Pattern → Nat
  | .invariant _ => 0
  | .implies tr _ => tr.lookback
  | .next tr _ => tr.lookback
  | .within tr _ _ _ => tr.lookback
  | .holdUntil tr _ _ => tr.lookback
  | .boundedWait c _ => c.lookback
  | .afterReset _ => 0

/-- The obligation of `next` is open at `t`: the trigger held one cycle ago,
which was not a reset. -/
def nextOpen (env : Env) (alw : Bool) (tr : Expr) (t : Nat) : Bool :=
  decide (1 ≤ t) && !env.rst (t - 1) && armed env alw tr (t - 1)

/-- The obligation of `within` expires at `t`: the trigger held `hi` cycles
ago, no cycle since was a reset, and the condition held at no age from `lo`
up to `hi - 1`. -/
def withinDue (env : Env) (alw : Bool) (tr c : Expr) (lo hi t : Nat) : Bool :=
  decide (hi ≤ t) && armed env alw tr (t - hi) &&
    (List.range hi).all fun i =>
      !env.rst (t - hi + i) && !(decide (lo ≤ i) && holds env c (t - hi + i))

/-- The obligation of `hold_until` is open at `t`: the trigger held at an
earlier cycle, no cycle since was a reset, and the release has not held
after the trigger. -/
def holdOpen (env : Env) (alw : Bool) (tr r : Expr) (t : Nat) : Bool :=
  (List.range t).any fun s =>
    armed env alw tr s && quiet env.rst s t &&
      (List.range (t - s - 1)).all fun i => !holds env r (s + 1 + i)

/-- The condition of `bounded_wait` has held for the last `n` cycles, none
of them a reset. -/
def waited (env : Env) (alw : Bool) (c : Expr) (n t : Nat) : Bool :=
  decide (n ≤ t) &&
    (List.range n).all fun i => armed env alw c (t - n + i) && !env.rst (t - n + i)

/-- The verdict of a pattern at cycle `t`, before the gates. -/
def raw (env : Env) (alw : Bool) : Pattern → Nat → Bool
  | .invariant c, t => holds env c t
  | .implies tr c, t => !holds env tr t || holds env c t
  | .next tr c, t => !nextOpen env alw tr t || holds env c t
  | .within tr c lo hi, t => !(withinDue env alw tr c lo hi t && !holds env c t)
  | .holdUntil tr h r, t => !holdOpen env alw tr r t || holds env h t
  | .boundedWait c n, t => !(armed env alw c t && waited env alw c n t)
  | .afterReset c, t => !(decide (1 ≤ t) && env.rst (t - 1)) || holds env c t

/-- The cycles at which a pattern is exercised (its trigger). -/
def trig (env : Env) (alw : Bool) : Pattern → Nat → Bool
  | .invariant _, _ => true
  | .implies tr _, t => holds env tr t
  | .next tr _, t => armed env alw tr t
  | .within tr _ _ _, t => armed env alw tr t
  | .holdUntil tr _ _, t => armed env alw tr t
  | .boundedWait c _, t => armed env alw c t
  | .afterReset _, t => decide (1 ≤ t) && env.rst (t - 1)

end Pattern

/-! ## Gates -/

/-- A verdict counts outside reset, once the expressions are defined.  An
item checked in reset cycles too waits only for the start of the trace. -/
def gate (env : Env) (alw : Bool) (d : Nat) (raw : Bool) (t : Nat) : Bool :=
  if alw then decide (t < d) || raw else env.rst t || !segGe env.rst d t || raw

def gateTrig (env : Env) (alw : Bool) (d : Nat) (trig : Bool) (t : Nat) : Bool :=
  if alw then decide (d ≤ t) && trig else !env.rst t && segGe env.rst d t && trig

/-! ## Ghosts -/

def Expr.ghosts : Expr → List String
  | .ghost g => [g]
  | .un _ a => a.ghosts
  | .bin _ a b => a.ghosts ++ b.ghosts
  | .ite c a b => c.ghosts ++ a.ghosts ++ b.ghosts
  | .quant _ n b => n.ghosts ++ b.ghosts
  | .prev _ a => a.ghosts
  | .once a => a.ghosts
  | .hist a => a.ghosts
  | .since a b => a.ghosts ++ b.ghosts
  | _ => []

def Expr.rigids : Expr → List String
  | .rigid r => [r]
  | .un _ a => a.rigids
  | .bin _ a b => a.rigids ++ b.rigids
  | .ite c a b => c.rigids ++ a.rigids ++ b.rigids
  | .quant _ n b => n.rigids ++ b.rigids
  | .prev _ a => a.rigids
  | .once a => a.rigids
  | .hist a => a.rigids
  | .since a b => a.rigids ++ b.rigids
  | _ => []

namespace Reading

def ghost? (R : Reading) (g : String) : Option Ghost := R.ghosts.find? fun d => d.name == g

/-- The ghosts a set of ghosts depends on, through their next values. -/
def closure (R : Reading) : Nat → List String → List String
  | 0, gs => gs
  | n + 1, gs =>
    closure R n (gs ++ gs.flatMap fun g =>
      match R.ghost? g with
      | some d => d.next.ghosts
      | none => []).eraseDups

end Reading

def lookupG (st : List (String × Int)) (x : String) : Int := (st.lookup x).getD 0

/-- The next value of a ghost, from the values `st` of the ghosts at `t`. -/
def Ghost.step (base : Env) (st : List (String × Int)) (t : Nat) (g : Ghost) : Int :=
  if base.rst t then g.init
  else (eval { base with ghost := fun x _ => lookupG st x } [] g.next t).toInt

/-- The values of the ghosts at cycle `t`: the initial values at the start
of the trace and after a reset cycle, the next values otherwise.  The
values are exact integers; a next value outside the range of its ghost is
reported by `Ghost.wf`, in the cycle that computes it. -/
def ghostRun (R : Reading) (base : Env) : Nat → List (String × Int)
  | 0 => R.ghosts.map fun g => (g.name, g.init)
  | t + 1 => R.ghosts.map fun g => (g.name, g.step base (ghostRun R base t) t)

/-- The same values for the cycles `T, T - 1, .., 0`, computed in one pass
(`ghostRuns_eq` in `FCP/Monitor.lean`). -/
def ghostRuns (R : Reading) (base : Env) : Nat → List (List (String × Int))
  | 0 => [R.ghosts.map fun g => (g.name, g.init)]
  | T + 1 =>
    match ghostRuns R base T with
    | [] => []
    | st :: rest => (R.ghosts.map fun g => (g.name, g.step base st T)) :: st :: rest

/-- The environment of a trace: its ghosts take the values the reading gives them. -/
def Env.withGhosts (R : Reading) (base : Env) : Env :=
  { base with ghost := fun x t => lookupG (ghostRun R base t) x }

/-- The next value of a ghost stays in its range (checked outside reset). -/
def Ghost.wf (env : Env) (g : Ghost) (t : Nat) : Bool :=
  env.rst t || inRange g.lo g.hi (eval env [] g.next t).toInt

/-! ## Items -/

namespace Item

/-- The ghosts an item depends on, directly or through other ghosts. -/
def ghostsOf (R : Reading) (it : Item) : List Ghost :=
  (R.closure R.ghosts.length (it.pattern.exprs.flatMap Expr.ghosts).eraseDups).filterMap R.ghost?

/-- The rigid variables an item depends on, directly or through its ghosts. -/
def rigidsOf (R : Reading) (it : Item) : List String :=
  (it.pattern.exprs.flatMap Expr.rigids ++ (it.ghostsOf R).flatMap fun g => g.next.rigids).eraseDups

/-- The verdict of a property or an assumption at cycle `t`, for the values
of the rigid variables in `env`: the gated verdict of its pattern, and
every ghost it depends on stays in its range. -/
def ok (R : Reading) (env : Env) (it : Item) (t : Nat) : Bool :=
  gate env it.always it.pattern.depth (it.pattern.raw env it.always t) t &&
    (it.ghostsOf R).all fun g => g.wf env t

/-- The cycles that exercise a property (used to report vacuity). -/
def tr (env : Env) (it : Item) (t : Nat) : Bool :=
  gateTrig env it.always it.pattern.tdepth (it.pattern.trig env it.always t) t

/-- A scenario is covered at cycle `t`. -/
def cov (env : Env) (it : Item) (t : Nat) : Bool :=
  gateTrig env it.always it.pattern.depth (it.pattern.raw env it.always t) t

/-- A don't-care applies at cycle `t`. -/
def dc (env : Env) (it : Item) (t : Nat) : Bool :=
  env.rst t || it.pattern.raw env it.always t

/-- A trace keeps an item, for the values of the rigid variables in `env`. -/
def sat (R : Reading) (env : Env) (it : Item) : Prop := ∀ t, it.ok R env t = true

end Item

end FCP

/-! ### Every value of the rigid names at once

A requirement that names a rigid value is checked for one value per run of
the monitor.  Where it stands as an assumption it has to hold for every
value, and the monitor carries one copy per value (at most 64).  -/

namespace FCP

def Rigid.values (r : Rigid) : List Int :=
  (List.range (r.hi - r.lo + 1).toNat).map fun i => r.lo + Int.ofNat i

/-- Every assignment of a value to each of the rigid names. -/
def combos : List Rigid → List (List (String × Int))
  | [] => [[]]
  | r :: rest => r.values.flatMap fun v => (combos rest).map fun c => (r.name, v) :: c

def comboCount (rs : List Rigid) : Nat :=
  rs.foldl (fun n r => n * (r.hi - r.lo + 1).toNat) 1

/-- The environment with some rigid names set to given values. -/
def Env.bind (env : Env) (c : List (String × Int)) : Env :=
  { env with rigid := fun r => (c.lookup r).getD (env.rigid r) }

namespace Item

/-- The rigid names of an item, with their ranges. -/
def rigidDecls (R : Reading) (it : Item) : List Rigid :=
  R.rigids.filter fun r => (it.rigidsOf R).contains r.name

/-- The verdict of an item for every value of its rigid names: `base` gives
the signals and the reset, the ghosts are run again for each value. -/
def okAll (R : Reading) (base : Env) (it : Item) (t : Nat) : Bool :=
  (combos (it.rigidDecls R)).all fun c => it.ok R (Env.withGhosts R (base.bind c)) t

end Item

end FCP
