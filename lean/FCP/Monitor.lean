/-
The registers of the compiled monitor compute the closed forms.

`FCP/Semantics.lean` and `FCP/Items.lean` say what an operator or a pattern
means by looking at the whole past of the trace.  The compiler
(`fcp/lang.py`, `fcp/monitor.py`) emits one small register machine for each;
this file writes those machines down, as recurrences on the cycle, and
proves that each one computes the closed form at every cycle.  The value of
a register at cycle `t` is what it holds during cycle `t`: its initial
value at cycle 0, and after that the value it was given at the end of the
cycle before.
-/
import FCP.Items

namespace FCP

/-! ## The past, as statements about cycles -/

theorem quiet_iff (rst : Nat → Bool) (a b : Nat) :
    quiet rst a b = true ↔ ∀ i, a ≤ i → i < b → rst i = false := by
  unfold quiet
  rw [List.all_eq_true]
  constructor
  · intro h i hai hib
    have := h (i - a) (List.mem_range.mpr (by omega))
    have e : a + (i - a) = i := by omega
    rw [e] at this
    simpa using this
  · intro h i hi
    have hi := List.mem_range.mp hi
    simpa using h (a + i) (by omega) (by omega)

theorem bool_eq_of_iff {a b : Bool} (h : a = true ↔ b = true) : a = b := by
  cases a <;> cases b <;> simp_all

/-! ## The cycles since the last reset -/

/-- The counter `_seg`: 0 at the start of the trace and after a reset cycle,
one more after every other cycle. -/
def segReg (rst : Nat → Bool) : Nat → Nat
  | 0 => 0
  | t + 1 => if rst t then 0 else segReg rst t + 1

theorem segReg_le (rst : Nat → Bool) (t : Nat) : segReg rst t ≤ t := by
  induction t with
  | zero => simp [segReg]
  | succ t ih => simp only [segReg]; split <;> omega

theorem segReg_iff (rst : Nat → Bool) (d t : Nat) :
    d ≤ segReg rst t ↔ d ≤ t ∧ ∀ i, t - d ≤ i → i < t → rst i = false := by
  induction t generalizing d with
  | zero =>
    simp only [segReg]
    constructor
    · intro h; exact ⟨h, fun i _ hi => absurd hi (by omega)⟩
    · intro h; exact h.1
  | succ t ih =>
    simp only [segReg]
    cases d with
    | zero => simp; intro i h1 h2; omega
    | succ d =>
      cases hr : rst t with
      | true =>
        simp only [ite_true]
        constructor
        · intro h; omega
        · intro ⟨_, h⟩
          have := h t (by omega) (by omega)
          simp [hr] at this
      | false =>
        simp only [Bool.false_eq_true, ite_false]
        rw [Nat.add_le_add_iff_right, ih d]
        constructor
        · intro ⟨h1, h2⟩
          refine ⟨by omega, fun i hi1 hi2 => ?_⟩
          by_cases e : i = t
          · rw [e]; exact hr
          · exact h2 i (by omega) (by omega)
        · intro ⟨h1, h2⟩
          exact ⟨by omega, fun i hi1 hi2 => h2 i (by omega) (by omega)⟩

/-- The gate of the monitor (`_seg >= d`) is the look-back of the semantics. -/
theorem segGe_eq (rst : Nat → Bool) (d t : Nat) : segGe rst d t = decide (d ≤ segReg rst t) := by
  apply bool_eq_of_iff
  unfold segGe
  rw [Bool.and_eq_true, decide_eq_true_iff, decide_eq_true_iff, quiet_iff, segReg_iff]

/-- The counter the monitor carries stops at a bound `m`; it gives the same
answer for every look-back up to `m`. -/
def segSat (m : Nat) (rst : Nat → Bool) : Nat → Nat
  | 0 => 0
  | t + 1 => if rst t then 0 else if segSat m rst t = m then segSat m rst t else segSat m rst t + 1

theorem segSat_eq (m : Nat) (rst : Nat → Bool) (t : Nat) : segSat m rst t = min (segReg rst t) m := by
  induction t with
  | zero => simp [segSat, segReg]
  | succ t ih =>
    simp only [segSat, segReg]
    cases rst t with
    | true => simp
    | false => simp only [Bool.false_eq_true, ite_false]; rw [ih]; split <;> omega

theorem segGe_sat (m : Nat) (rst : Nat → Bool) (d t : Nat) (h : d ≤ m) :
    segGe rst d t = decide (d ≤ segSat m rst t) := by
  rw [segGe_eq, segSat_eq]
  apply bool_eq_of_iff
  rw [decide_eq_true_iff, decide_eq_true_iff]
  omega

/-! ## once, hist, since -/

theorem all_range_iff (n : Nat) (f : Nat → Bool) :
    (List.range n).all f = true ↔ ∀ i, i < n → f i = true := by
  rw [List.all_eq_true]
  exact ⟨fun h i hi => h i (List.mem_range.mpr hi), fun h i hi => h i (List.mem_range.mp hi)⟩

theorem any_range_iff (n : Nat) (f : Nat → Bool) :
    (List.range n).any f = true ↔ ∃ i, i < n ∧ f i = true := by
  rw [List.any_eq_true]
  exact ⟨fun ⟨i, hi, h⟩ => ⟨i, List.mem_range.mp hi, h⟩, fun ⟨i, hi, h⟩ => ⟨i, List.mem_range.mpr hi, h⟩⟩

/-- The register of `once(a)`: `a` held at an earlier cycle, and no cycle
since was a reset. -/
def onceReg (rst a : Nat → Bool) : Nat → Bool
  | 0 => false
  | t + 1 => !rst t && (onceReg rst a t || a t)

theorem onceReg_iff (rst a : Nat → Bool) (t : Nat) :
    onceReg rst a t = true ↔ ∃ s, s < t ∧ a s = true ∧ ∀ i, s ≤ i → i < t → rst i = false := by
  induction t with
  | zero => simp [onceReg]
  | succ t ih =>
    simp only [onceReg, Bool.and_eq_true, Bool.not_eq_true', Bool.or_eq_true, ih]
    constructor
    · rintro ⟨hr, h | h⟩
      · obtain ⟨s, hs, has, hq⟩ := h
        refine ⟨s, by omega, has, fun i h1 h2 => ?_⟩
        by_cases e : i = t
        · rw [e]; exact hr
        · exact hq i h1 (by omega)
      · refine ⟨t, by omega, h, fun i h1 h2 => ?_⟩
        have e : i = t := by omega
        rw [e]; exact hr
    · rintro ⟨s, hs, has, hq⟩
      refine ⟨hq t (by omega) (by omega), ?_⟩
      by_cases e : s = t
      · right; rw [← e]; exact has
      · left; exact ⟨s, by omega, has, fun i h1 h2 => hq i h1 (by omega)⟩

theorem onceS_iff (rst a : Nat → Bool) (t : Nat) :
    onceS rst a t = true ↔ ∃ s, s ≤ t ∧ a s = true ∧ ∀ i, s ≤ i → i < t → rst i = false := by
  unfold onceS
  rw [any_range_iff]
  constructor
  · rintro ⟨s, hs, h⟩
    rw [Bool.and_eq_true, quiet_iff] at h
    exact ⟨s, by omega, h.1, h.2⟩
  · rintro ⟨s, hs, has, hq⟩
    refine ⟨s, by omega, ?_⟩
    rw [Bool.and_eq_true, quiet_iff]
    exact ⟨has, hq⟩

/-- The wire of `once(a)` is the register, or `a` now. -/
theorem onceS_eq (rst a : Nat → Bool) (t : Nat) : onceS rst a t = (onceReg rst a t || a t) := by
  apply bool_eq_of_iff
  rw [onceS_iff, Bool.or_eq_true, onceReg_iff]
  constructor
  · rintro ⟨s, hs, has, hq⟩
    by_cases e : s = t
    · right; rw [← e]; exact has
    · left; exact ⟨s, by omega, has, hq⟩
  · rintro (⟨s, hs, has, hq⟩ | h)
    · exact ⟨s, by omega, has, hq⟩
    · exact ⟨t, by omega, h, fun i h1 h2 => by omega⟩

/-- The register of `hist(a)`: `a` held at every earlier cycle since the
last reset.  It starts at 1 and a reset sets it to 1. -/
def histReg (rst a : Nat → Bool) : Nat → Bool
  | 0 => true
  | t + 1 => rst t || (histReg rst a t && a t)

theorem histS_not_once (rst a : Nat → Bool) (t : Nat) : histS rst a t = !onceS rst (fun s => !a s) t := by
  unfold histS onceS
  rw [List.all_eq_not_any_not]
  congr 2
  funext s
  show (!(a s || !quiet rst s t)) = (!a s && quiet rst s t)
  cases a s <;> cases quiet rst s t <;> rfl

theorem histReg_not_once (rst a : Nat → Bool) (t : Nat) :
    histReg rst a t = !onceReg rst (fun s => !a s) t := by
  induction t with
  | zero => rfl
  | succ t ih =>
    simp only [histReg, onceReg, ih]
    cases rst t <;> cases onceReg rst (fun s => !a s) t <;> cases a t <;> rfl

/-- The wire of `hist(a)` is the register, and `a` now. -/
theorem histS_eq (rst a : Nat → Bool) (t : Nat) : histS rst a t = (histReg rst a t && a t) := by
  rw [histS_not_once, onceS_eq, histReg_not_once]
  cases onceReg rst (fun s => !a s) t <;> cases a t <;> rfl

/-- The register of `since(a, b)`: the wire of the cycle before, unless it
was a reset. -/
def sinceReg (rst a b : Nat → Bool) : Nat → Bool
  | 0 => false
  | t + 1 => !rst t && (b t || (a t && sinceReg rst a b t))

theorem sinceS_iff (rst a b : Nat → Bool) (t : Nat) :
    sinceS rst a b t = true ↔
      ∃ s, s ≤ t ∧ b s = true ∧ (∀ i, s ≤ i → i < t → rst i = false) ∧ ∀ i, s < i → i ≤ t → a i = true := by
  unfold sinceS
  rw [any_range_iff]
  constructor
  · rintro ⟨s, hs, h⟩
    rw [Bool.and_eq_true, Bool.and_eq_true, quiet_iff, all_range_iff] at h
    refine ⟨s, by omega, h.1.1, h.1.2, fun i h1 h2 => ?_⟩
    have := h.2 (i - s - 1) (by omega)
    have e : s + 1 + (i - s - 1) = i := by omega
    rwa [e] at this
  · rintro ⟨s, hs, hb, hq, ha⟩
    refine ⟨s, by omega, ?_⟩
    rw [Bool.and_eq_true, Bool.and_eq_true, quiet_iff, all_range_iff]
    exact ⟨⟨hb, hq⟩, fun i hi => ha (s + 1 + i) (by omega) (by omega)⟩

theorem sinceReg_iff (rst a b : Nat → Bool) (t : Nat) :
    sinceReg rst a b t = true ↔
      ∃ s, s < t ∧ b s = true ∧ (∀ i, s ≤ i → i < t → rst i = false) ∧ ∀ i, s < i → i < t → a i = true := by
  induction t with
  | zero => simp [sinceReg]
  | succ t ih =>
    simp only [sinceReg, Bool.and_eq_true, Bool.not_eq_true', Bool.or_eq_true, ih]
    constructor
    · rintro ⟨hr, h | ⟨hat, s, hs, hb, hq, ha⟩⟩
      · refine ⟨t, by omega, h, fun i h1 h2 => ?_, fun i h1 h2 => by omega⟩
        have e : i = t := by omega
        rw [e]; exact hr
      · refine ⟨s, by omega, hb, fun i h1 h2 => ?_, fun i h1 h2 => ?_⟩
        · by_cases e : i = t
          · rw [e]; exact hr
          · exact hq i h1 (by omega)
        · by_cases e : i = t
          · rw [e]; exact hat
          · exact ha i h1 (by omega)
    · rintro ⟨s, hs, hb, hq, ha⟩
      refine ⟨hq t (by omega) (by omega), ?_⟩
      by_cases e : s = t
      · left; rw [← e]; exact hb
      · right
        exact ⟨ha t (by omega) (by omega), s, by omega, hb, fun i h1 h2 => hq i h1 (by omega),
          fun i h1 h2 => ha i h1 (by omega)⟩

/-- The wire of `since(a, b)` is `b` now, or `a` now and the register. -/
theorem sinceS_eq (rst a b : Nat → Bool) (t : Nat) :
    sinceS rst a b t = (b t || (a t && sinceReg rst a b t)) := by
  apply bool_eq_of_iff
  rw [sinceS_iff, Bool.or_eq_true, Bool.and_eq_true, sinceReg_iff]
  constructor
  · rintro ⟨s, hs, hb, hq, ha⟩
    by_cases e : s = t
    · left; rw [← e]; exact hb
    · right
      exact ⟨ha t (by omega) (by omega), s, by omega, hb, hq, fun i h1 h2 => ha i h1 (by omega)⟩
  · rintro (h | ⟨hat, s, hs, hb, hq, ha⟩)
    · exact ⟨t, by omega, h, fun i h1 h2 => by omega, fun i h1 h2 => by omega⟩
    · refine ⟨s, by omega, hb, hq, fun i h1 h2 => ?_⟩
      by_cases e : i = t
      · rw [e]; exact hat
      · exact ha i h1 (by omega)

/-- In an expression, the operand of `once`, `hist` and `since` is first
masked where it is not defined; the rest is the register. -/
theorem eval_once (env : Env) (bv : List Int) (a : Expr) (t : Nat) :
    eval env bv (.once a) t =
      .ofBool (onceReg env.rst (fun s => segGe env.rst a.lookback s && (eval env bv a s).truth) t ||
        (segGe env.rst a.lookback t && (eval env bv a t).truth)) := by
  simp only [eval, onceS_eq]

theorem eval_hist (env : Env) (bv : List Int) (a : Expr) (t : Nat) :
    eval env bv (.hist a) t =
      .ofBool (histReg env.rst (fun s => !segGe env.rst a.lookback s || (eval env bv a s).truth) t &&
        (!segGe env.rst a.lookback t || (eval env bv a t).truth)) := by
  simp only [eval, histS_eq]

theorem eval_since (env : Env) (bv : List Int) (a b : Expr) (t : Nat) :
    eval env bv (.since a b) t =
      .ofBool ((segGe env.rst b.lookback t && (eval env bv b t).truth) ||
        ((!segGe env.rst a.lookback t || (eval env bv a t).truth) &&
          sinceReg env.rst (fun s => !segGe env.rst a.lookback s || (eval env bv a s).truth)
            (fun s => segGe env.rst b.lookback s && (eval env bv b s).truth) t)) := by
  simp only [eval, sinceS_eq]

/-! ## Patterns -/

/-- The register of `next`: the trigger of the cycle before, unless that
cycle was a reset. -/
def nextReg (rst x : Nat → Bool) : Nat → Bool
  | 0 => false
  | t + 1 => !rst t && x t

theorem nextOpen_eq (env : Env) (alw : Bool) (tr : Expr) (t : Nat) :
    Pattern.nextOpen env alw tr t = nextReg env.rst (armed env alw tr) t := by
  cases t with
  | zero => simp [Pattern.nextOpen, nextReg]
  | succ t => simp [Pattern.nextOpen, nextReg]

/-- The registers of `within`: register `k` holds an obligation of age `k`
(register 0 is the trigger itself).  An obligation moves on by one age per
cycle, unless the cycle is a reset or meets it (from age `lo` on). -/
def obReg (rst x c : Nat → Bool) (lo : Nat) : Nat → Nat → Bool
  | 0, t => x t
  | _ + 1, 0 => false
  | k + 1, t + 1 => obReg rst x c lo k t && !rst t && !(decide (lo ≤ k) && c t)

theorem obReg_iff (rst x c : Nat → Bool) (lo k t : Nat) :
    obReg rst x c lo k t = true ↔
      k ≤ t ∧ x (t - k) = true ∧ ∀ i, i < k → rst (t - k + i) = false ∧ ¬(lo ≤ i ∧ c (t - k + i) = true) := by
  induction k generalizing t with
  | zero => simp [obReg]
  | succ k ih =>
    cases t with
    | zero => simp [obReg]
    | succ t =>
      simp only [obReg, Bool.and_eq_true, Bool.not_eq_true', Bool.and_eq_false_iff, decide_eq_false_iff_not, ih]
      have e : t + 1 - (k + 1) = t - k := by omega
      rw [e]
      constructor
      · rintro ⟨⟨⟨hk, hx, hall⟩, hr⟩, hc⟩
        refine ⟨by omega, hx, fun i hi => ?_⟩
        by_cases ei : i = k
        · have e2 : t - k + i = t := by omega
          rw [e2]
          refine ⟨hr, fun ⟨h1, h2⟩ => ?_⟩
          rcases hc with hc | hc
          · exact hc (by omega)
          · rw [hc] at h2; exact Bool.noConfusion h2
        · exact hall i (by omega)
      · rintro ⟨hk, hx, hall⟩
        have hk' : k ≤ t := by omega
        have e2 : t - k + k = t := by omega
        have hlast := hall k (by omega)
        rw [e2] at hlast
        refine ⟨⟨⟨hk', hx, fun i hi => hall i (by omega)⟩, hlast.1⟩, ?_⟩
        by_cases hl : lo ≤ k
        · right
          cases hct : c t with
          | false => rfl
          | true => exact absurd ⟨hl, hct⟩ hlast.2
        · left; exact hl

theorem withinDue_eq (env : Env) (alw : Bool) (tr c : Expr) (lo hi t : Nat) :
    Pattern.withinDue env alw tr c lo hi t = obReg env.rst (armed env alw tr) (holds env c) lo hi t := by
  apply bool_eq_of_iff
  unfold Pattern.withinDue
  rw [Bool.and_eq_true, Bool.and_eq_true, decide_eq_true_iff, all_range_iff, obReg_iff]
  constructor
  · rintro ⟨⟨h1, h2⟩, h3⟩
    refine ⟨h1, h2, fun i hi => ?_⟩
    have := h3 i hi
    simp only [Bool.and_eq_true, Bool.not_eq_true', Bool.and_eq_false_iff, decide_eq_false_iff_not] at this
    refine ⟨this.1, fun ⟨a, b⟩ => ?_⟩
    rcases this.2 with h | h
    · exact h a
    · rw [h] at b; exact Bool.noConfusion b
  · rintro ⟨h1, h2, h3⟩
    refine ⟨⟨h1, h2⟩, fun i hlt => ?_⟩
    have := h3 i hlt
    simp only [Bool.and_eq_true, Bool.not_eq_true', Bool.and_eq_false_iff, decide_eq_false_iff_not]
    refine ⟨this.1, ?_⟩
    by_cases hl : lo ≤ i
    · right
      cases hc : holds env c (t - hi + i) with
      | false => rfl
      | true => exact absurd ⟨hl, hc⟩ this.2
    · left; exact hl

/-- The register of `hold_until`: an obligation is open from the cycle
after the trigger, and stays open until a reset or the cycle after the
release. -/
def holdReg (rst x r : Nat → Bool) : Nat → Bool
  | 0 => false
  | t + 1 => !rst t && (x t || (holdReg rst x r t && !r t))

theorem holdReg_since (rst x r : Nat → Bool) (t : Nat) :
    holdReg rst x r t = sinceReg rst (fun s => !r s) x t := by
  induction t with
  | zero => rfl
  | succ t ih => simp only [holdReg, sinceReg, ih, Bool.and_comm]

theorem holdOpen_eq (env : Env) (alw : Bool) (tr r : Expr) (t : Nat) :
    Pattern.holdOpen env alw tr r t = holdReg env.rst (armed env alw tr) (holds env r) t := by
  apply bool_eq_of_iff
  unfold Pattern.holdOpen
  rw [holdReg_since, sinceReg_iff, any_range_iff]
  constructor
  · rintro ⟨s, hs, h⟩
    rw [Bool.and_eq_true, Bool.and_eq_true, quiet_iff, all_range_iff] at h
    refine ⟨s, hs, h.1.1, h.1.2, fun i h1 h2 => ?_⟩
    have := h.2 (i - s - 1) (by omega)
    have e : s + 1 + (i - s - 1) = i := by omega
    rw [e] at this
    exact this
  · rintro ⟨s, hs, hx, hq, hr⟩
    refine ⟨s, hs, ?_⟩
    rw [Bool.and_eq_true, Bool.and_eq_true, quiet_iff, all_range_iff]
    exact ⟨⟨hx, hq⟩, fun i hi => hr (s + 1 + i) (by omega) (by omega)⟩

/-- The counter of `bounded_wait`: the cycles in a row, up to now, in which
the condition held; it stops at `n`. -/
def waitReg (n : Nat) (rst x : Nat → Bool) : Nat → Nat
  | 0 => 0
  | t + 1 =>
    if rst t then 0
    else if x t then (if waitReg n rst x t = n then waitReg n rst x t else waitReg n rst x t + 1)
    else 0

theorem waitReg_seg (n : Nat) (rst x : Nat → Bool) (t : Nat) :
    waitReg n rst x t = segSat n (fun i => rst i || !x i) t := by
  induction t with
  | zero => rfl
  | succ t ih =>
    simp only [waitReg, segSat, ih]
    by_cases hr : rst t = true
    · simp [hr]
    · by_cases hx : x t = true
      · simp [hr, hx]
      · simp [hr, hx]

theorem waited_eq (env : Env) (alw : Bool) (c : Expr) (n t : Nat) :
    Pattern.waited env alw c n t = decide (waitReg n env.rst (armed env alw c) t = n) := by
  have hsat := segSat_eq n (fun i => env.rst i || !armed env alw c i) t
  have hge := segGe_sat n (fun i => env.rst i || !armed env alw c i) n t (Nat.le_refl n)
  have : Pattern.waited env alw c n t = segGe (fun i => env.rst i || !armed env alw c i) n t := by
    apply bool_eq_of_iff
    unfold Pattern.waited segGe
    rw [Bool.and_eq_true, Bool.and_eq_true, decide_eq_true_iff, all_range_iff, quiet_iff]
    constructor
    · rintro ⟨h1, h2⟩
      refine ⟨h1, fun i hi1 hi2 => ?_⟩
      have := h2 (i - (t - n)) (by omega)
      have e : t - n + (i - (t - n)) = i := by omega
      rw [e] at this
      simp only [Bool.and_eq_true, Bool.not_eq_true'] at this
      simp [this.1, this.2]
    · rintro ⟨h1, h2⟩
      refine ⟨h1, fun i hi => ?_⟩
      have := h2 (t - n + i) (by omega) (by omega)
      simp only [Bool.or_eq_false_iff, Bool.not_eq_false'] at this
      simp [this.1, this.2]
  rw [this, hge, waitReg_seg]
  apply bool_eq_of_iff
  rw [decide_eq_true_iff, decide_eq_true_iff, hsat]
  omega

/-- The register of `after_reset`: the cycle before was a reset. -/
def resetReg (rst : Nat → Bool) : Nat → Bool
  | 0 => false
  | t + 1 => rst t

theorem afterReset_eq (rst : Nat → Bool) (t : Nat) : (decide (1 ≤ t) && rst (t - 1)) = resetReg rst t := by
  cases t <;> simp [resetReg]

/-- The verdict of a pattern as the monitor computes it: from its registers
and the values of the current cycle. -/
def Pattern.rawReg (env : Env) (alw : Bool) : Pattern → Nat → Bool
  | .invariant c, t => holds env c t
  | .implies tr c, t => !holds env tr t || holds env c t
  | .next tr c, t => !nextReg env.rst (armed env alw tr) t || holds env c t
  | .within tr c lo hi, t =>
    !(obReg env.rst (armed env alw tr) (holds env c) lo hi t && !holds env c t)
  | .holdUntil tr h r, t => !holdReg env.rst (armed env alw tr) (holds env r) t || holds env h t
  | .boundedWait c n, t => !(armed env alw c t && decide (waitReg n env.rst (armed env alw c) t = n))
  | .afterReset c, t => !resetReg env.rst t || holds env c t

/-- Every pattern: the registers compute the closed form, at every cycle of
every trace. -/
theorem Pattern.raw_eq_rawReg (env : Env) (alw : Bool) (p : Pattern) (t : Nat) :
    p.raw env alw t = p.rawReg env alw t := by
  cases p <;>
    simp only [Pattern.raw, Pattern.rawReg, nextOpen_eq, withinDue_eq, holdOpen_eq, waited_eq, afterReset_eq]

/-! ## prev

`prev(a, n)` is a chain of `n` registers with no reset and no initial
value.  Whatever the registers hold at the start, the chain gives the value
of `a` from `n` cycles ago at every cycle from `n` on; before that it is
not defined, and the gates below keep those cycles out of every verdict. -/

def prevReg {α : Type} (init : Nat → α) (a : Nat → α) : Nat → Nat → α
  | 0, t => a t
  | n + 1, 0 => init n
  | n + 1, t + 1 => prevReg init a n t

theorem prevReg_eq {α : Type} (init : Nat → α) (a : Nat → α) (n t : Nat) (h : n ≤ t) :
    prevReg init a n t = a (t - n) := by
  induction n generalizing t with
  | zero => rfl
  | succ n ih =>
    cases t with
    | zero => omega
    | succ t =>
      simp only [prevReg]
      rw [ih t (by omega)]
      congr 1
      omega

theorem eval_prev (env : Env) (bv : List Int) (init : Nat → Val) (a : Expr) (n t : Nat) (h : n ≤ t) :
    eval env bv (.prev n a) t = prevReg init (eval env bv a) n t := by
  rw [prevReg_eq init _ n t h]
  simp [eval, h]

/-! ## Gates and items -/

/-- The counter of an item checked in reset cycles too: the cycles since
the start of the trace, stopping at `m`. -/
def cycSat (m : Nat) : Nat → Nat
  | 0 => 0
  | t + 1 => if cycSat m t = m then cycSat m t else cycSat m t + 1

theorem cycSat_eq (m t : Nat) : cycSat m t = min t m := by
  induction t with
  | zero => simp [cycSat]
  | succ t ih => simp only [cycSat]; rw [ih]; split <;> omega

/-- The gates as the monitor computes them, from its two counters. -/
def gateReg (m : Nat) (env : Env) (alw : Bool) (d : Nat) (raw : Bool) (t : Nat) : Bool :=
  if alw then decide (cycSat m t < d) || raw
  else env.rst t || decide (segSat m env.rst t < d) || raw

def gateTrigReg (m : Nat) (env : Env) (alw : Bool) (d : Nat) (trig : Bool) (t : Nat) : Bool :=
  if alw then decide (d ≤ cycSat m t) && trig
  else !env.rst t && decide (d ≤ segSat m env.rst t) && trig

theorem gate_eq (m : Nat) (env : Env) (alw : Bool) (d : Nat) (raw : Bool) (t : Nat) (h : d ≤ m) :
    gate env alw d raw t = gateReg m env alw d raw t := by
  have e1 : decide (t < d) = decide (cycSat m t < d) := by
    apply bool_eq_of_iff
    rw [decide_eq_true_iff, decide_eq_true_iff, cycSat_eq]
    omega
  have e2 : (!segGe env.rst d t) = decide (segSat m env.rst t < d) := by
    rw [segGe_sat m env.rst d t h]
    by_cases hh : d ≤ segSat m env.rst t
    · have : ¬ segSat m env.rst t < d := by omega
      simp [hh, this]
    · have : segSat m env.rst t < d := by omega
      simp [hh, this]
  unfold gate gateReg
  rw [e1, e2]

theorem gateTrig_eq (m : Nat) (env : Env) (alw : Bool) (d : Nat) (trig : Bool) (t : Nat) (h : d ≤ m) :
    gateTrig env alw d trig t = gateTrigReg m env alw d trig t := by
  have e1 : decide (d ≤ t) = decide (d ≤ cycSat m t) := by
    apply bool_eq_of_iff
    rw [decide_eq_true_iff, decide_eq_true_iff, cycSat_eq]
    omega
  unfold gateTrig gateTrigReg
  rw [e1, segGe_sat m env.rst d t h]

namespace Item

/-- The verdict of an item as the monitor computes it. -/
def okReg (m : Nat) (R : Reading) (env : Env) (it : Item) (t : Nat) : Bool :=
  gateReg m env it.always it.pattern.depth (it.pattern.rawReg env it.always t) t &&
    (it.ghostsOf R).all fun g => g.wf env t

def covReg (m : Nat) (env : Env) (it : Item) (t : Nat) : Bool :=
  gateTrigReg m env it.always it.pattern.depth (it.pattern.rawReg env it.always t) t

/-- The monitor of an item computes its verdict: at every cycle of every
trace, for every value of the rigid names, whatever the counters stop at
(from the look-back of the item up). -/
theorem ok_eq_okReg (m : Nat) (R : Reading) (env : Env) (it : Item) (t : Nat)
    (h : it.pattern.depth ≤ m) : it.ok R env t = it.okReg m R env t := by
  unfold ok okReg
  rw [Pattern.raw_eq_rawReg, gate_eq m env it.always it.pattern.depth _ t h]

theorem cov_eq_covReg (m : Nat) (env : Env) (it : Item) (t : Nat)
    (h : it.pattern.depth ≤ m) : it.cov env t = it.covReg m env t := by
  unfold cov covReg
  rw [Pattern.raw_eq_rawReg, gateTrig_eq m env it.always it.pattern.depth _ t h]

end Item

/-! ## Ghosts -/

/-- The one-pass run of the ghosts (what the oracle evaluates) gives the
values of `ghostRun` for the cycles `T, T - 1, .., 0`. -/
theorem ghostRuns_eq (R : Reading) (base : Env) (T : Nat) :
    ghostRuns R base T = (List.range (T + 1)).reverse.map (ghostRun R base) := by
  induction T with
  | zero => simp [ghostRuns, ghostRun, List.range_succ]
  | succ T ih =>
    rw [ghostRuns, ih]
    simp [List.range_succ, ghostRun]

end FCP
