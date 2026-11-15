/-
Contracts: the definitions of the paper and its propositions, stated over
abstract traces and verdicts.  Nothing here depends on FCP-PL: a property
is any verdict that is causal (at a cycle it reads the trace up to that
cycle), which is what a monitor computes.

  Definition 1   `Sat`               assume-guarantee satisfaction
  Definition 3   `Conflict`          a conflict of a set of readings
  Proposition 1  `conflict_sound`    reported conflicts are sound
  Corollary      `conflict_pinned`   pinned instances of a rigid variable
  Proposition 2  `enforced_meaning`, `delegated_meaning`
  Proposition 3  `horizon`           a disagreement fits in d + 1 calls
  Proposition 4  `proved_sound`, `proved_bounded_sound`, `invariant_sound`
-/

namespace FCP.Contracts

/-! ## Traces, verdicts, satisfaction -/

/-- A trace: a value of the inputs and of the outputs at every cycle. -/
structure Trace (I O : Type) where
  inp : Nat → I
  out : Nat → O

/-- A property, as its monitor sees it: a verdict at every cycle. -/
abbrev Verdict (I O : Type) := Trace I O → Nat → Bool

variable {I O : Type}

/-- Two traces are the same up to cycle `k`. -/
def Trace.agree (π ρ : Trace I O) (k : Nat) : Prop :=
  ∀ t, t ≤ k → π.inp t = ρ.inp t ∧ π.out t = ρ.out t

/-- A verdict is causal: at a cycle it reads the trace up to that cycle. -/
def Causal (φ : Verdict I O) : Prop :=
  ∀ π ρ t, π.agree ρ t → φ π t = φ ρ t

/-- Every assumption has held up to cycle `t`. -/
def heldUpTo (A : List (Verdict I O)) (π : Trace I O) (t : Nat) : Prop :=
  ∀ a, a ∈ A → ∀ s, s ≤ t → a π s = true

/-- Definition 1.  An artifact (a set of traces) satisfies `A ⇒ φ`. -/
def Sat (M : Trace I O → Prop) (A : List (Verdict I O)) (φ : Verdict I O) : Prop :=
  ∀ π, M π → ∀ t, heldUpTo A π t → φ π t = true

theorem heldUpTo_agree {A : List (Verdict I O)} (hA : ∀ a, a ∈ A → Causal a)
    {π ρ : Trace I O} {t : Nat} (h : π.agree ρ t) (hπ : heldUpTo A π t) : heldUpTo A ρ t := by
  intro a ha s hs
  have : π.agree ρ s := fun u hu => h u (Nat.le_trans hu hs)
  rw [← hA a ha π ρ s this]
  exact hπ a ha s hs

/-! ## Conflicts (Proposition 1) -/

/-- Definition 3.  The inputs `σ` of the cycles `0..k` are a conflict of
the assumptions `A` and the guarantees `G`: whatever the outputs, some
guarantee fails at a cycle up to which every assumption has held. -/
def Conflict (A G : List (Verdict I O)) (σ : Nat → I) (k : Nat) : Prop :=
  ∀ τ : Nat → O, ∃ t, t ≤ k ∧ (∃ g, g ∈ G ∧ g ⟨σ, τ⟩ t = false) ∧ heldUpTo A ⟨σ, τ⟩ t

/-- Proposition 1.  A trace that carries a conflict in its cycles `0..k`
breaks a guarantee at a cycle up to which every assumption has held. -/
theorem conflict_sound {A G : List (Verdict I O)} (hA : ∀ a, a ∈ A → Causal a)
    (hG : ∀ g, g ∈ G → Causal g) {σ : Nat → I} {k : Nat} (hc : Conflict A G σ k)
    (π : Trace I O) (hσ : ∀ t, t ≤ k → π.inp t = σ t) :
    ∃ t, t ≤ k ∧ (∃ g, g ∈ G ∧ g π t = false) ∧ heldUpTo A π t := by
  obtain ⟨t, ht, ⟨g, hg, hf⟩, hheld⟩ := hc π.out
  have hag : (⟨σ, π.out⟩ : Trace I O).agree π t :=
    fun s hs => ⟨(hσ s (Nat.le_trans hs ht)).symm, rfl⟩
  refine ⟨t, ht, ⟨g, hg, ?_⟩, heldUpTo_agree hA hag hheld⟩
  rw [← hG g hg _ π t hag]
  exact hf

/-- So every artifact that accepts the conflict violates a guarantee. -/
theorem conflict_violates {A G : List (Verdict I O)} (hA : ∀ a, a ∈ A → Causal a)
    (hG : ∀ g, g ∈ G → Causal g) {σ : Nat → I} {k : Nat} (hc : Conflict A G σ k)
    (M : Trace I O → Prop) (hacc : ∃ π, M π ∧ ∀ t, t ≤ k → π.inp t = σ t) :
    ∃ g, g ∈ G ∧ ¬ Sat M A g := by
  obtain ⟨π, hM, hσ⟩ := hacc
  obtain ⟨t, _, ⟨g, hg, hf⟩, hheld⟩ := conflict_sound hA hG hc π hσ
  refine ⟨g, hg, fun hs => ?_⟩
  have := hs π hM t hheld
  rw [hf] at this
  exact Bool.noConfusion this

/-- A conflict stays one when the guarantees get stronger: if a failure of
a guarantee of `G'` is always a failure of one of `G`. -/
theorem conflict_mono {A G G' : List (Verdict I O)} {σ : Nat → I} {k : Nat}
    (h : ∀ g', g' ∈ G' → ∀ π t, g' π t = false → ∃ g, g ∈ G ∧ g π t = false)
    (hc : Conflict A G' σ k) : Conflict A G σ k := by
  intro τ
  obtain ⟨t, ht, ⟨g', hg', hf⟩, hheld⟩ := hc τ
  exact ⟨t, ht, h g' hg' _ t hf, hheld⟩

/-- Corollary (pinned instances).  Let the guarantee `all` say `φ u` for
every value `u` of a rigid variable.  A conflict found with `all` replaced
by the instances `φ u₁, .., φ uₘ` is a conflict of the original readings. -/
theorem conflict_pinned {U : Type} {A G : List (Verdict I O)} (φ : U → Verdict I O)
    (all : Verdict I O) (hall : ∀ π t, all π t = true → ∀ u, φ u π t = true)
    (pins : List U) {σ : Nat → I} {k : Nat}
    (hc : Conflict A (pins.map φ ++ G) σ k) : Conflict A (all :: G) σ k := by
  apply conflict_mono _ hc
  intro g' hg' π t hf
  rcases List.mem_append.mp hg' with hp | hg
  · obtain ⟨u, _, rfl⟩ := List.mem_map.mp hp
    refine ⟨all, List.mem_cons_self, ?_⟩
    cases hv : all π t with
    | false => rfl
    | true =>
      have := hall π t hv u
      rw [hf] at this
      exact Bool.noConfusion this
  · exact ⟨g', List.mem_cons_of_mem _ hg, hf⟩

/-! ## Trust classes (Proposition 2)

The proposal of the model is an input of the scaffold `M`, so every run of
the agent is a trace of `M`: that is the hypothesis `M π` below. -/

/-- Enforced: every run keeps `φ` under `A`, whatever the model proposes. -/
theorem enforced_meaning {M : Trace I O → Prop} {A : List (Verdict I O)} {φ : Verdict I O}
    (h : Sat M A φ) (π : Trace I O) (hM : M π) (hA : ∀ t, heldUpTo A π t) :
    ∀ t, φ π t = true :=
  fun t => h π hM t (hA t)

/-- Delegated: every run keeps `φ` under `A` at every turn before the
first one in which the proposal breaks the model contract `c`. -/
theorem delegated_meaning {M : Trace I O → Prop} {A : List (Verdict I O)} {c φ : Verdict I O}
    (h : Sat M (c :: A) φ) (π : Trace I O) (hM : M π) (hA : ∀ t, heldUpTo A π t)
    (v : Nat) (hv : ∀ s, s < v → c π s = true) : ∀ t, t < v → φ π t = true := by
  intro t ht
  apply h π hM t
  intro a ha s hs
  rcases List.mem_cons.mp ha with rfl | ha'
  · exact hv s (Nat.lt_of_le_of_lt hs ht)
  · exact hA t a ha' s hs

/-! ## Bounded horizon (Proposition 3)

A function has no state, so a trace is a list of calls (arguments with
their answer), and any list of calls of the function is again a trace of
it.  An item without ghosts or unbounded history reads a window: the call
it is checked at and the `back` calls before it.  Where the window reaches
before the first call the item is disabled, and holds. -/

/-- An item that reads a window of `back + 1` calls. -/
structure WItem (C : Type) where
  back : Nat
  p : (Nat → Option C) → Bool
  reads : ∀ w w' : Nat → Option C, (∀ i, i ≤ back → w i = w' i) → p w = p w'

variable {C : Type}

/-- The verdict of an item at call `j` of a trace. -/
def WItem.ok (it : WItem C) (π : List C) (j : Nat) : Bool :=
  decide (j < it.back) || it.p (fun m => π[j - it.back + m]?)

/-- A trace keeps a set of items: each holds at every call. -/
def keeps (items : List (WItem C)) (π : List C) : Prop :=
  ∀ it, it ∈ items → ∀ j, j < π.length → it.ok π j = true

/-- The calls `s..j` of a trace, as a trace. -/
def cut (π : List C) (s j : Nat) : List C := (π.drop s).take (j - s + 1)

theorem cut_get (π : List C) (s j n : Nat) (h : n ≤ j - s) : (cut π s j)[n]? = π[s + n]? := by
  unfold cut
  rw [List.getElem?_take]
  split
  · rw [List.getElem?_drop]
  · omega

theorem cut_length (π : List C) (s j : Nat) (hs : s ≤ j) (h : j < π.length) :
    (cut π s j).length = j - s + 1 := by
  unfold cut
  rw [List.length_take, List.length_drop]
  omega

/-- Where the window of an item fits in the cut, the item sees the same
window as in the whole trace, so its verdict is the same. -/
theorem ok_cut (it : WItem C) (π : List C) (s j i : Nat) (hi : i ≤ j - s) (hb : it.back ≤ i) :
    it.ok (cut π s j) i = it.ok π (s + i) := by
  unfold WItem.ok
  have e1 : decide (i < it.back) = false := by simp; omega
  have e2 : decide (s + i < it.back) = false := by simp; omega
  rw [e1, e2]
  congr 1
  apply it.reads
  intro m hm
  rw [cut_get π s j (i - it.back + m) (by omega)]
  congr 1
  omega

theorem ok_early (it : WItem C) (π : List C) (i : Nat) (h : i < it.back) : it.ok π i = true := by
  unfold WItem.ok
  simp [h]

/-- Proposition 3.  Let the items of `brk` look back at most `d` calls.  If
a trace keeps the items `keep` and breaks one of `brk`, so does a trace of
at most `d + 1` of its calls.  (For two readings `a` and `b` of a
requirement `r`: `brk` holds the items of `r` under `b`; `keep` holds the
items of `r` under `a` and, for comparison in context, the items of the
other requirements.  The bound is needed only for the items that fail.) -/
theorem horizon (d : Nat) (keep brk : List (WItem C)) (π : List C)
    (hd' : ∀ it, it ∈ brk → it.back ≤ d)
    (hk : keeps keep π) (hb : ¬ keeps brk π) :
    ∃ π' : List C, π'.length ≤ d + 1 ∧ (∀ c, c ∈ π' → c ∈ π) ∧ keeps keep π' ∧ ¬ keeps brk π' := by
  have ⟨it, hit, j, hj, hf⟩ : ∃ it, it ∈ brk ∧ ∃ j, j < π.length ∧ ¬ it.ok π j = true := by
    apply Classical.byContradiction
    intro hne
    apply hb
    intro it hit j hj
    apply Classical.byContradiction
    intro hf
    exact hne ⟨it, hit, j, hj, hf⟩
  have hbj : it.back ≤ j := by
    apply Classical.byContradiction
    intro hlt
    exact hf (ok_early it π j (by omega))
  have hlen := cut_length π (j - d) j (by omega) hj
  refine ⟨cut π (j - d) j, by omega, ?_, ?_, ?_⟩
  · intro c hc
    exact List.mem_of_mem_drop (List.mem_of_mem_take hc)
  · intro it' hit' i hi
    by_cases hbi : it'.back ≤ i
    · rw [ok_cut it' π (j - d) j i (by omega) hbi]
      exact hk it' hit' (j - d + i) (by omega)
    · exact ok_early it' _ i (by omega)
  · intro hk'
    have h1 := hk' it hit (j - (j - d)) (by omega)
    have hdb := hd' it hit
    rw [ok_cut it π (j - d) j (j - (j - d)) (Nat.le_refl _) (by omega)] at h1
    have e : j - d + (j - (j - d)) = j := by omega
    rw [e] at h1
    exact hf h1

/-- The same for one set of items: a violation fits in `d + 1` calls. -/
theorem horizon_single (d : Nat) (brk : List (WItem C)) (π : List C)
    (hd : ∀ it, it ∈ brk → it.back ≤ d) (hb : ¬ keeps brk π) :
    ∃ π' : List C, π'.length ≤ d + 1 ∧ (∀ c, c ∈ π' → c ∈ π) ∧ ¬ keeps brk π' := by
  obtain ⟨π', h1, h2, _, h3⟩ :=
    horizon d [] brk π hd (fun _ h => nomatch h) hb
  exact ⟨π', h1, h2, h3⟩

/-! ## Proofs beyond the scope (Proposition 4)

`f` is the code, `T` its translation; a trace of the code is the list of
its answers to a list of calls within the ranges of the interface.  `mon`
is true on the traces the compiled monitors reject for the requirement,
`enc` on the traces the integer encoding rejects. -/

section Prove

variable {X Y : Type}

/-- The trace of a function on a list of calls. -/
def run (f : X → Y) (xs : List X) : List (X × Y) := xs.map fun x => (x, f x)

/-- The query has no answer: no `k` calls within the ranges make the
encoding reject the trace of the translation. -/
def Unsat (inR : X → Prop) (T : X → Y) (enc : List (X × Y) → Bool) (k : Nat) : Prop :=
  ∀ xs : List X, xs.length ≤ k → (∀ x, x ∈ xs → inR x) → enc (run T xs) = false

/-- The horizon is exact: a rejected trace of the code has a rejected
trace of at most `k` calls. -/
def Exact (inR : X → Prop) (f : X → Y) (mon : List (X × Y) → Bool) (k : Nat) : Prop :=
  ∀ xs : List X, (∀ x, x ∈ xs → inR x) → mon (run f xs) = true →
    ∃ ys : List X, ys.length ≤ k ∧ (∀ y, y ∈ ys → inR y) ∧ mon (run f ys) = true

theorem run_congr {f T : X → Y} {inR : X → Prop} (hT : ∀ x, inR x → T x = f x)
    (xs : List X) (h : ∀ x, x ∈ xs → inR x) : run T xs = run f xs := by
  unfold run
  apply List.map_congr_left
  intro x hx
  rw [hT x (h x hx)]

/-- Proposition 4 (ii), PROVED-BOUNDED: no sequence of at most `k` calls
violates the requirement. -/
theorem proved_bounded_sound {f T : X → Y} {inR : X → Prop} {mon enc : List (X × Y) → Bool}
    {k : Nat} (hT : ∀ x, inR x → T x = f x) (hE : ∀ tr, enc tr = mon tr)
    (hq : Unsat inR T enc k) (xs : List X) (hlen : xs.length ≤ k) (hr : ∀ x, x ∈ xs → inR x) :
    mon (run f xs) = false := by
  rw [← run_congr hT xs hr, ← hE]
  exact hq xs hlen hr

/-- Proposition 4 (ii), PROVED: with an exact horizon, no trace of the
code violates the requirement. -/
theorem proved_sound {f T : X → Y} {inR : X → Prop} {mon enc : List (X × Y) → Bool}
    {k : Nat} (hT : ∀ x, inR x → T x = f x) (hE : ∀ tr, enc tr = mon tr)
    (hq : Unsat inR T enc k) (hx : Exact inR f mon k) (xs : List X) (hr : ∀ x, x ∈ xs → inR x) :
    mon (run f xs) = false := by
  cases hm : mon (run f xs) with
  | false => rfl
  | true =>
    obtain ⟨ys, hlen, hry, hbad⟩ := hx xs hr hm
    rw [proved_bounded_sound hT hE hq ys hlen hry] at hbad
    exact Bool.noConfusion hbad

end Prove

/-- Objects.  `Inv t` says the invariant holds in the state after `t`
calls of a trace.  If it holds in the first `w` states and, whenever in
`w` states in a row, in the next, it holds in every state. -/
theorem invariant_all (Inv : Nat → Prop) (w : Nat) (base : ∀ t, t < w → Inv t)
    (step : ∀ t, (∀ i, i < w → Inv (t + i)) → Inv (t + w)) : ∀ t, Inv t := by
  intro t
  induction t using Nat.strongRecOn with
  | _ t ih =>
    by_cases h : t < w
    · exact base t h
    · have e : t - w + w = t := by omega
      rw [← e]
      exact step (t - w) fun i hi => ih (t - w + i) (by omega)

/-- So a requirement with such an invariant is kept at every call: `Bad t`
says the requirement fails at call `t`; the queries exclude a failure in
the first `w` calls, and one at the end of a window of states in which the
invariant holds. -/
theorem invariant_sound (Inv Bad : Nat → Prop) (w : Nat) (base : ∀ t, t < w → Inv t)
    (step : ∀ t, (∀ i, i < w → Inv (t + i)) → Inv (t + w))
    (pre : ∀ t, t < w → ¬ Bad t)
    (win : ∀ t, (∀ i, i < w → Inv (t + i)) → ¬ Bad (t + w)) : ∀ t, ¬ Bad t := by
  intro t
  by_cases h : t < w
  · exact pre t h
  · have e : t - w + w = t := by omega
    rw [← e]
    exact win (t - w) fun i _ => invariant_all Inv w base step (t - w + i)

end FCP.Contracts
