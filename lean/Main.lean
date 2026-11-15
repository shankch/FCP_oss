/-
fcp-oracle: the verdicts of a reading on recorded traces, computed from the
reference semantics (FCP.Semantics, FCP.Items).  The Python side compares
them, cycle by cycle, with what the monitor compiled to Verilog reports on
the same traces (fcp/leanref.py).

    fcp-oracle FILE

FILE holds `(reading ..)`, `(vals ..)` (values for the rigid names, one list
per run) and any number of `(trace ..)`.  For every trace and every run the
oracle prints one line per stream: the item's id, the stream's name and one
character per cycle.
-/
import FCP.Items
import FCP.SExpr
open FCP

def bits (T : Nat) (f : Nat → Bool) : String :=
  (List.range T).foldl (fun s t => s.push (if f t then '1' else '0')) ""

def baseEnv (tr : Trace) (val : List (String × Int)) : Env :=
  { sig := fun x t => match tr.sigs.lookup x with
      | some a => a.getD t (.int 0)
      | none => .int 0
    rst := fun t => tr.rst.getD t false
    ghost := fun _ _ => 0
    rigid := fun r => (val.lookup r).getD 0 }

/-- The environment with the ghosts run once over the trace and kept in a
table (`ghostRuns`), in place of `Env.withGhosts`, which runs them again at
every look. -/
def tabled (R : Reading) (base : Env) (T : Nat) : Env :=
  let tbl := (ghostRuns R base (T - 1)).reverse.toArray
  { base with ghost := fun x t => lookupG (tbl.getD t []) x }

def inRangeAll (R : Reading) (env : Env) (t : Nat) : Bool :=
  R.ghosts.all fun g => g.wf env t

def itemLines (R : Reading) (base env : Env) (T : Nat) (it : Item) : List String :=
  let line (what : String) (f : Nat → Bool) : String := s!"{it.id} {what} {bits T f}"
  let rs := it.rigidDecls R
  let envs := if comboCount rs ≤ 64 then (combos rs).map fun c => tabled R (base.bind c) T else []
  let all (f : Env → Nat → Bool) (t : Nat) : Bool := envs.all fun e => f e t
  match it.role with
  | .property =>
    [line "ok" (it.ok R env), line "tr" (it.tr env)] ++
      (if rs.isEmpty || envs.isEmpty then []
       else [line "okd" (all fun e => it.ok R e), line "wfx" (all fun e => inRangeAll R e)])
  | .assumption =>
    if envs.isEmpty then []
    else [line "aok" (all fun e => it.ok R e), line "wfx" (all fun e => inRangeAll R e)]
  | .scenario => [line "cov" (it.cov env)]
  | .dontcare => [line "dc" (it.dc env)]

def run (xs : List SExpr) : Except String (Array String) := do
  let mut reading : Reading := { ghosts := [], rigids := [], items := [] }
  let mut vals : List (List (String × Int)) := [[]]
  let mut traces : Array Trace := #[]
  for x in xs do
    match x with
    | .list (.atom "reading" :: _) => reading ← toReading x
    | .list (.atom "vals" :: _) => vals ← toVals x
    | .list (.atom "trace" :: _) => traces := traces.push (← toTrace x)
    | _ => throw "expected (reading ..), (vals ..) or (trace ..)"
  let mut out : Array String := #[]
  let mut k := 0
  for tr in traces do
    out := out.push s!"trace {k}"
    k := k + 1
    let mut j := 0
    for val in vals do
      out := out.push s!"val {j}"
      j := j + 1
      let base := baseEnv tr val
      let env := tabled reading base tr.len
      out := out.push s!"- wf {bits tr.len (inRangeAll reading env)}"
      for it in reading.items do
        out := out ++ (itemLines reading base env tr.len it).toArray
  return out

def main (args : List String) : IO UInt32 := do
  match args with
  | [path] =>
    let text ← IO.FS.readFile path
    match parseSExprs text >>= run with
    | .error e =>
      IO.eprintln s!"fcp-oracle: {e}"
      return 1
    | .ok lines =>
      let h ← IO.getStdout
      for l in lines do
        h.putStrLn l
      return 0
  | _ =>
    IO.eprintln "usage: fcp-oracle FILE"
    return 2
