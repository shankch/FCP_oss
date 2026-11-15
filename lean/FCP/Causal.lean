/-
Causality: the verdict of an item at a cycle reads the trace up to that
cycle and nothing after it.  This is the property of a monitor that the
propositions of `FCP/Contracts.lean` ask of a verdict (`Contracts.Causal`);
here it is proved for every expression, pattern and item of FCP-PL, the
ghosts included.
-/
import FCP.Monitor
import FCP.Contracts

namespace FCP

/-- Two traces carry the same signals, resets and rigid values up to cycle `t`. -/
def Env.same (e e' : Env) (t : Nat) : Prop :=
  (∀ x s, s ≤ t → e.sig x s = e'.sig x s) ∧ (∀ s, s ≤ t → e.rst s = e'.rst s) ∧
    (∀ r, e.rigid r = e'.rigid r)

/-- The same, and the ghosts have the same values up to cycle `t`. -/
def Env.agree (e e' : Env) (t : Nat) : Prop :=
  e.same e' t ∧ ∀ g s, s ≤ t → e.ghost g s = e'.ghost g s

theorem Env.same.mono {e e' : Env} {t s : Nat} (h : e.same e' t) (hs : s ≤ t) : e.same e' s :=
  ⟨fun x u hu => h.1 x u (Nat.le_trans hu hs), fun u hu => h.2.1 u (Nat.le_trans hu hs), h.2.2⟩

theorem Env.agree.mono {e e' : Env} {t s : Nat} (h : e.agree e' t) (hs : s ≤ t) : e.agree e' s :=
  ⟨h.1.mono hs, fun g u hu => h.2 g u (Nat.le_trans hu hs)⟩

theorem Env.agree.rst {e e' : Env} {t s : Nat} (h : e.agree e' t) (hs : s ≤ t) : e.rst s = e'.rst s :=
  h.1.2.1 s hs

/-! ## The operators over the past read the past -/

theorem all_range_congr {n : Nat} {f g : Nat → Bool} (h : ∀ i, i < n → f i = g i) :
    (List.range n).all f = (List.range n).all g := by
  apply bool_eq_of_iff
  rw [all_range_iff, all_range_iff]
  constructor
  · intro H i hi; rw [← h i hi]; exact H i hi
  · intro H i hi; rw [h i hi]; exact H i hi

theorem any_range_congr {n : Nat} {f g : Nat → Bool} (h : ∀ i, i < n → f i = g i) :
    (List.range n).any f = (List.range n).any g := by
  apply bool_eq_of_iff
  rw [any_range_iff, any_range_iff]
  constructor
  · rintro ⟨i, hi, H⟩; exact ⟨i, hi, by rw [← h i hi]; exact H⟩
  · rintro ⟨i, hi, H⟩; exact ⟨i, hi, by rw [h i hi]; exact H⟩

theorem quiet_congr {rst rst' : Nat → Bool} {a b : Nat} (h : ∀ i, i < b → rst i = rst' i) :
    quiet rst a b = quiet rst' a b := by
  unfold quiet
  exact all_range_congr fun i hi => by rw [h (a + i) (by omega)]

theorem segGe_congr {rst rst' : Nat → Bool} (d : Nat) {t : Nat} (h : ∀ i, i < t → rst i = rst' i) :
    segGe rst d t = segGe rst' d t := by
  unfold segGe
  rw [quiet_congr h]

theorem onceS_congr {rst rst' f f' : Nat → Bool} {t : Nat} (hr : ∀ i, i < t → rst i = rst' i)
    (hf : ∀ s, s ≤ t → f s = f' s) : onceS rst f t = onceS rst' f' t := by
  unfold onceS
  exact any_range_congr fun s hs => by rw [hf s (by omega), quiet_congr hr]

theorem histS_congr {rst rst' f f' : Nat → Bool} {t : Nat} (hr : ∀ i, i < t → rst i = rst' i)
    (hf : ∀ s, s ≤ t → f s = f' s) : histS rst f t = histS rst' f' t := by
  unfold histS
  exact all_range_congr fun s hs => by rw [hf s (by omega), quiet_congr hr]

theorem sinceS_congr {rst rst' a a' b b' : Nat → Bool} {t : Nat} (hr : ∀ i, i < t → rst i = rst' i)
    (ha : ∀ s, s ≤ t → a s = a' s) (hb : ∀ s, s ≤ t → b s = b' s) :
    sinceS rst a b t = sinceS rst' a' b' t := by
  unfold sinceS
  refine any_range_congr fun s hs => ?_
  rw [hb s (by omega), quiet_congr hr,
    all_range_congr (f := fun i => a (s + 1 + i)) (g := fun i => a' (s + 1 + i))
      fun i hi => ha (s + 1 + i) (by omega)]

/-! ## Expressions -/

/-- The value of an expression at cycle `t` reads the trace up to `t`. -/
theorem eval_causal {env env' : Env} (e : Expr) :
    ∀ (bv : List Int) (t : Nat), env.agree env' t → eval env bv e t = eval env' bv e t := by
  induction e with
  | num n => intro bv t _; simp only [eval]
  | lst l => intro bv t _; simp only [eval]
  | sig x => intro bv t h; simp only [eval]; exact h.1.1 x t (Nat.le_refl t)
  | ghost g => intro bv t h; simp only [eval]; rw [h.2 g t (Nat.le_refl t)]
  | rigid r => intro bv t h; simp only [eval]; rw [h.1.2.2 r]
  | bvar i => intro bv t _; simp only [eval]
  | un op a ih => intro bv t h; simp only [eval]; rw [ih bv t h]
  | bin op a b iha ihb => intro bv t h; simp only [eval]; rw [iha bv t h, ihb bv t h]
  | ite c a b ihc iha ihb =>
    intro bv t h; simp only [eval]; rw [ihc bv t h, iha bv t h, ihb bv t h]
  | quant q n b ihn ihb =>
    intro bv t h
    have hb : ∀ k : Nat, eval env (Int.ofNat k :: bv) b t = eval env' (Int.ofNat k :: bv) b t :=
      fun k => ihb _ t h
    simp only [eval, ihn bv t h, hb]
  | prev n a ih =>
    intro bv t h
    simp only [eval]
    split
    · exact ih bv (t - n) (h.mono (by omega))
    · rfl
  | once a ih =>
    intro bv t h
    simp only [eval]
    congr 1
    refine onceS_congr (fun i hi => h.rst (by omega)) fun s hs => ?_
    rw [ih bv s (h.mono hs), segGe_congr _ fun i hi => h.rst (by omega)]
  | hist a ih =>
    intro bv t h
    simp only [eval]
    congr 1
    refine histS_congr (fun i hi => h.rst (by omega)) fun s hs => ?_
    rw [ih bv s (h.mono hs), segGe_congr _ fun i hi => h.rst (by omega)]
  | since a b iha ihb =>
    intro bv t h
    simp only [eval]
    congr 1
    refine sinceS_congr (fun i hi => h.rst (by omega)) (fun s hs => ?_) fun s hs => ?_
    · rw [iha bv s (h.mono hs), segGe_congr _ fun i hi => h.rst (by omega)]
    · rw [ihb bv s (h.mono hs), segGe_congr _ fun i hi => h.rst (by omega)]

theorem holds_causal {env env' : Env} (e : Expr) {t : Nat} (h : env.agree env' t) :
    holds env e t = holds env' e t := by
  unfold holds
  rw [eval_causal e [] t h]

theorem armed_causal {env env' : Env} (alw : Bool) (e : Expr) {t : Nat} (h : env.agree env' t) :
    armed env alw e t = armed env' alw e t := by
  unfold armed
  rw [holds_causal e h, segGe_congr _ fun i hi => h.rst (by omega)]

/-! ## Patterns and gates -/

theorem nextOpen_causal {env env' : Env} (alw : Bool) (tr : Expr) {t : Nat} (h : env.agree env' t) :
    Pattern.nextOpen env alw tr t = Pattern.nextOpen env' alw tr t := by
  unfold Pattern.nextOpen
  rw [h.rst (Nat.sub_le t 1), armed_causal alw tr (h.mono (Nat.sub_le t 1))]

theorem withinDue_causal {env env' : Env} (alw : Bool) (tr c : Expr) (lo hi : Nat) {t : Nat}
    (h : env.agree env' t) :
    Pattern.withinDue env alw tr c lo hi t = Pattern.withinDue env' alw tr c lo hi t := by
  unfold Pattern.withinDue
  by_cases hh : hi ≤ t
  · rw [armed_causal alw tr (h.mono (Nat.sub_le t hi))]
    congr 1
    exact all_range_congr fun i hlt => by
      rw [h.rst (s := t - hi + i) (by omega), holds_causal c (h.mono (s := t - hi + i) (by omega))]
  · simp [hh]

theorem holdOpen_causal {env env' : Env} (alw : Bool) (tr r : Expr) {t : Nat} (h : env.agree env' t) :
    Pattern.holdOpen env alw tr r t = Pattern.holdOpen env' alw tr r t := by
  unfold Pattern.holdOpen
  refine any_range_congr fun s hs => ?_
  rw [armed_causal alw tr (h.mono (s := s) (by omega)), quiet_congr fun i hi => h.rst (by omega)]
  congr 1
  exact all_range_congr fun i hi => by rw [holds_causal r (h.mono (s := s + 1 + i) (by omega))]

theorem waited_causal {env env' : Env} (alw : Bool) (c : Expr) (n : Nat) {t : Nat} (h : env.agree env' t) :
    Pattern.waited env alw c n t = Pattern.waited env' alw c n t := by
  unfold Pattern.waited
  by_cases hh : n ≤ t
  · congr 1
    exact all_range_congr fun i hi => by
      rw [armed_causal alw c (h.mono (s := t - n + i) (by omega)), h.rst (s := t - n + i) (by omega)]
  · simp [hh]

theorem Pattern.raw_causal {env env' : Env} (alw : Bool) (p : Pattern) {t : Nat} (h : env.agree env' t) :
    p.raw env alw t = p.raw env' alw t := by
  cases p with
  | invariant c => simp only [Pattern.raw, holds_causal c h]
  | implies tr c => simp only [Pattern.raw, holds_causal tr h, holds_causal c h]
  | next tr c => simp only [Pattern.raw, nextOpen_causal alw tr h, holds_causal c h]
  | within tr c lo hi => simp only [Pattern.raw, withinDue_causal alw tr c lo hi h, holds_causal c h]
  | holdUntil tr hd r => simp only [Pattern.raw, holdOpen_causal alw tr r h, holds_causal hd h]
  | boundedWait c n => simp only [Pattern.raw, armed_causal alw c h, waited_causal alw c n h]
  | afterReset c => simp only [Pattern.raw, holds_causal c h, h.rst (Nat.sub_le t 1)]

theorem gate_causal {env env' : Env} (alw : Bool) (d : Nat) (raw : Bool) {t : Nat} (h : env.agree env' t) :
    gate env alw d raw t = gate env' alw d raw t := by
  unfold gate
  rw [h.rst (Nat.le_refl t), segGe_congr d fun i hi => h.rst (by omega)]

theorem Ghost.wf_causal {env env' : Env} (g : Ghost) {t : Nat} (h : env.agree env' t) :
    g.wf env t = g.wf env' t := by
  unfold Ghost.wf
  rw [h.rst (Nat.le_refl t), eval_causal g.next [] t h]

/-- The verdict of an item at cycle `t` reads the trace, and the ghosts, up to `t`. -/
theorem Item.ok_causal (R : Reading) (it : Item) {env env' : Env} {t : Nat} (h : env.agree env' t) :
    it.ok R env t = it.ok R env' t := by
  unfold Item.ok
  have hw : (fun g : Ghost => g.wf env t) = fun g => g.wf env' t :=
    funext fun g => Ghost.wf_causal g h
  rw [Pattern.raw_causal it.always it.pattern h, gate_causal it.always it.pattern.depth _ h, hw]

/-! ## Ghosts: their values at a cycle come from the trace before it -/

theorem Ghost.step_causal {base base' : Env} (st : List (String × Int)) (g : Ghost) {t : Nat}
    (h : base.same base' t) : g.step base st t = g.step base' st t := by
  unfold Ghost.step
  have ha : Env.agree { base with ghost := fun x _ => lookupG st x }
      { base' with ghost := fun x _ => lookupG st x } t := ⟨h, fun _ _ _ => rfl⟩
  rw [h.2.1 t (Nat.le_refl t), eval_causal g.next [] t ha]

theorem ghostRun_causal (R : Reading) {base base' : Env} :
    ∀ {t : Nat}, base.same base' t → ghostRun R base t = ghostRun R base' t := by
  intro t
  induction t with
  | zero => intro _; simp only [ghostRun]
  | succ t ih =>
    intro h
    have h' := h.mono (Nat.le_succ t)
    simp only [ghostRun, ih h']
    apply List.map_congr_left
    intro g _
    rw [Ghost.step_causal _ g h']

theorem withGhosts_agree (R : Reading) {base base' : Env} {t : Nat} (h : base.same base' t) :
    (Env.withGhosts R base).agree (Env.withGhosts R base') t :=
  ⟨h, fun g s hs => by
    show lookupG (ghostRun R base s) g = lookupG (ghostRun R base' s) g
    rw [ghostRun_causal R (h.mono hs)]⟩

theorem bind_same {base base' : Env} (c : List (String × Int)) {t : Nat} (h : base.same base' t) :
    (base.bind c).same (base'.bind c) t :=
  ⟨h.1, h.2.1, fun r => by
    show (c.lookup r).getD (base.rigid r) = (c.lookup r).getD (base'.rigid r)
    rw [h.2.2 r]⟩

/-- The verdict of an item on a trace, for every value of its rigid names,
reads the trace up to the cycle of the verdict. -/
theorem Item.okAll_causal (R : Reading) (it : Item) {base base' : Env} {t : Nat}
    (h : base.same base' t) : it.okAll R base t = it.okAll R base' t := by
  unfold Item.okAll
  have hc : (fun c => it.ok R (Env.withGhosts R (base.bind c)) t) =
      fun c => it.ok R (Env.withGhosts R (base'.bind c)) t :=
    funext fun c => Item.ok_causal R it (withGhosts_agree R (bind_same c h))
  rw [hc]

/-! ## The verdicts of FCP-PL are verdicts in the sense of the contracts -/

/-- A trace of an interface as an environment: the inputs carry the reset
and the input signals, the outputs carry the other signals. -/
def Env.ofTrace (isIn : String → Bool) (rigid : String → Int)
    (π : Contracts.Trace (Bool × (String → Val)) (String → Val)) : Env where
  sig x t := if isIn x then (π.inp t).2 x else π.out t x
  rst t := (π.inp t).1
  ghost _ _ := 0
  rigid := rigid

theorem Env.ofTrace_same (isIn : String → Bool) (rigid : String → Int)
    {π ρ : Contracts.Trace (Bool × (String → Val)) (String → Val)} {t : Nat} (h : π.agree ρ t) :
    (Env.ofTrace isIn rigid π).same (Env.ofTrace isIn rigid ρ) t := by
  refine ⟨fun x s hs => ?_, fun s hs => ?_, fun _ => rfl⟩
  · show (if isIn x then (π.inp s).2 x else π.out s x) = (if isIn x then (ρ.inp s).2 x else ρ.out s x)
    rw [(h s hs).1, (h s hs).2]
  · show (π.inp s).1 = (ρ.inp s).1
    rw [(h s hs).1]

/-- Every item of FCP-PL is causal: Propositions 1 and 2 apply to it. -/
theorem Item.causal (R : Reading) (it : Item) (isIn : String → Bool) (rigid : String → Int) :
    Contracts.Causal fun π t => it.okAll R (Env.ofTrace isIn rigid π) t :=
  fun _ _ _ h => Item.okAll_causal R it (Env.ofTrace_same isIn rigid h)

end FCP
