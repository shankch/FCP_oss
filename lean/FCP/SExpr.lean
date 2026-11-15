/-
Reading a reading and its traces from text: the format the Python side
writes (`fcp/leanref.py`).  S-expressions; an atom that is a number is that
number.
-/
import FCP.Items

namespace FCP

inductive SExpr where
  | atom (s : String)
  | list (l : List SExpr)
deriving Inhabited

def tokenize (s : String) : Array String := Id.run do
  let mut out : Array String := #[]
  let mut cur := ""
  for c in s.toList do
    if c == '(' || c == ')' then
      if cur != "" then
        out := out.push cur
        cur := ""
      out := out.push (String.singleton c)
    else if c.isWhitespace then
      if cur != "" then
        out := out.push cur
        cur := ""
    else
      cur := cur.push c
  if cur != "" then
    out := out.push cur
  return out

partial def parseSeq (toks : Array String) (i : Nat) (acc : Array SExpr) (top : Bool) :
    Except String (List SExpr × Nat) :=
  if h : i < toks.size then
    let t := toks[i]
    if t == "(" then do
      let (xs, j) ← parseSeq toks (i + 1) #[] false
      parseSeq toks j (acc.push (.list xs)) top
    else if t == ")" then
      if top then .error "unbalanced )" else .ok (acc.toList, i + 1)
    else parseSeq toks (i + 1) (acc.push (.atom t)) top
  else if top then .ok (acc.toList, i) else .error "missing )"

def parseSExprs (s : String) : Except String (List SExpr) := do
  let (xs, _) ← parseSeq (tokenize s) 0 #[] true
  return xs

namespace SExpr

def int : SExpr → Except String Int
  | .atom s => match s.toInt? with
    | some n => .ok n
    | none => .error s!"expected a number, got {s}"
  | .list _ => .error "expected a number, got a list"

def nat (x : SExpr) : Except String Nat := do
  let n ← x.int
  if n < 0 then .error s!"expected a natural number, got {n}" else return n.toNat

def name : SExpr → Except String String
  | .atom s => .ok s
  | .list _ => .error "expected a name, got a list"

def ints : SExpr → Except String (List Int)
  | .list xs => xs.mapM int
  | .atom s => .error s!"expected a list, got {s}"

end SExpr

def unOp? : String → Option UnOp
  | "not" => some .not | "neg" => some .neg | "anybit" => some .anyBit
  | "countones" => some .countones | "onehot" => some .onehot | "onehot0" => some .onehot0
  | "len" => some .len | "isdigit" => some .isdigit | "isalpha" => some .isalpha
  | "isalnum" => some .isalnum | "islower" => some .islower | "isupper" => some .isupper
  | "isspace" => some .isspace | "lower" => some .lower | "upper" => some .upper
  | _ => none

def binOp? : String → Option BinOp
  | "and" => some .and | "or" => some .or | "imp" => some .imp | "iff" => some .iff
  | "eq" => some .eq | "ne" => some .ne | "lt" => some .lt | "le" => some .le
  | "gt" => some .gt | "ge" => some .ge | "add" => some .add | "sub" => some .sub
  | "mul" => some .mul | "mod" => some .mod | "shl" => some .shl | "shr" => some .shr
  | "band" => some .band | "bor" => some .bor | "bxor" => some .bxor
  | "min" => some .min | "max" => some .max | "mem" => some .mem | "idx" => some .idx
  | _ => none

def quant? : String → Option Quant
  | "q-all" => some .all | "q-any" => some .any | "q-count" => some .count | "q-sum" => some .sum
  | _ => none

partial def toExpr : SExpr → Except String Expr
  | .atom s => match s.toInt? with
    | some n => .ok (.num n)
    | none => .error s!"expected an expression, got {s}"
  | .list [] => .error "empty expression"
  | .list (.list _ :: _) => .error "an expression starts with a name"
  | .list (.atom h :: args) => do
    match h, args with
    | "lst", xs => return .lst (← xs.mapM SExpr.int)
    | "sig", [x] => return .sig (← x.name)
    | "ghost", [x] => return .ghost (← x.name)
    | "rigid", [x] => return .rigid (← x.name)
    | "bvar", [i] => return .bvar (← i.nat)
    | "ite", [c, a, b] => return .ite (← toExpr c) (← toExpr a) (← toExpr b)
    | "prev", [n, a] => return .prev (← n.nat) (← toExpr a)
    | "once", [a] => return .once (← toExpr a)
    | "hist", [a] => return .hist (← toExpr a)
    | "since", [a, b] => return .since (← toExpr a) (← toExpr b)
    | "rose", [a] => return (← toExpr a).rose
    | "fell", [a] => return (← toExpr a).fell
    | "stable", [a] => return (← toExpr a).stable
    | "changed", [a] => return (← toExpr a).changed
    | "bnot", [w, a] => return .un (.bnot (← w.nat)) (← toExpr a)
    | "allbits", [w, a] => return .un (.allBits (← w.nat)) (← toExpr a)
    | "slice", [hi, lo, a] => return .un (.slice (← hi.nat) (← lo.nat)) (← toExpr a)
    | "shlw", [w, a, b] => return .bin (.shlw (← w.nat)) (← toExpr a) (← toExpr b)
    | _, [a] => match unOp? h with
      | some op => return .un op (← toExpr a)
      | none => .error s!"unknown operator {h} of one operand"
    | _, [a, b] => match binOp? h, quant? h with
      | some op, _ => return .bin op (← toExpr a) (← toExpr b)
      | none, some q => return .quant q (← toExpr a) (← toExpr b)
      | none, none => .error s!"unknown operator {h} of two operands"
    | _, _ => .error s!"unknown form {h}"

def toPattern : SExpr → Except String Pattern
  | .list (.atom h :: args) => do
    match h, args with
    | "invariant", [c] => return .invariant (← toExpr c)
    | "implies", [t, c] => return .implies (← toExpr t) (← toExpr c)
    | "next", [t, c] => return .next (← toExpr t) (← toExpr c)
    | "within", [t, c, lo, hi] => return .within (← toExpr t) (← toExpr c) (← lo.nat) (← hi.nat)
    | "hold_until", [t, hd, r] => return .holdUntil (← toExpr t) (← toExpr hd) (← toExpr r)
    | "bounded_wait", [c, n] => return .boundedWait (← toExpr c) (← n.nat)
    | "after_reset", [c] => return .afterReset (← toExpr c)
    | _, _ => .error s!"unknown pattern {h}"
  | _ => .error "expected a pattern"

def toRole : String → Except String Role
  | "property" => .ok .property | "assumption" => .ok .assumption
  | "scenario" => .ok .scenario | "dontcare" => .ok .dontcare
  | s => .error s!"unknown role {s}"

def toItem : SExpr → Except String Item
  | .list [id, role, mode, pat] => do
    return { id := ← id.name, role := ← toRole (← role.name), always := (← mode.name) == "always",
             pattern := ← toPattern pat }
  | _ => .error "expected (id role mode pattern)"

def toGhost : SExpr → Except String Ghost
  | .list [n, lo, hi, init, next] => do
    return { name := ← n.name, lo := ← lo.int, hi := ← hi.int, init := ← init.int, next := ← toExpr next }
  | _ => .error "expected (name lo hi init next)"

def toRigid : SExpr → Except String Rigid
  | .list [n, lo, hi] => do return { name := ← n.name, lo := ← lo.int, hi := ← hi.int }
  | _ => .error "expected (name lo hi)"

def section? (key : String) (xs : List SExpr) : List SExpr :=
  match xs.find? fun x => match x with
    | .list (.atom k :: _) => k == key
    | _ => false with
  | some (.list (_ :: rest)) => rest
  | _ => []

def toReading : SExpr → Except String Reading
  | .list (.atom "reading" :: xs) => do
    return { ghosts := ← (section? "ghosts" xs).mapM toGhost,
             rigids := ← (section? "rigids" xs).mapM toRigid,
             items := ← (section? "items" xs).mapM toItem }
  | _ => .error "expected (reading ...)"

/-- A recorded trace: one value of every signal at every cycle. -/
structure Trace where
  len : Nat
  rst : Array Bool
  sigs : List (String × Array Val)
deriving Inhabited

def toTrace : SExpr → Except String Trace
  | .list (.atom "trace" :: xs) => do
    let mut len := 0
    let mut rst : Array Bool := #[]
    let mut sigs : List (String × Array Val) := []
    for x in xs do
      match x with
      | .list [.atom "len", n] => len ← n.nat
      | .list (.atom "rst" :: vs) => rst := (← vs.mapM SExpr.int).toArray.map (· != 0)
      | .list (.atom "sig" :: n :: vs) =>
        sigs := (← n.name, (← vs.mapM SExpr.int).toArray.map Val.int) :: sigs
      | .list (.atom "seq" :: n :: vs) =>
        sigs := (← n.name, (← vs.mapM SExpr.ints).toArray.map Val.seq) :: sigs
      | _ => throw "unknown entry in a trace"
    return { len, rst, sigs }
  | _ => .error "expected (trace ...)"

def toVals : SExpr → Except String (List (List (String × Int)))
  | .list (.atom "vals" :: vs) => vs.mapM fun v =>
    match v with
    | .list ps => ps.mapM fun p =>
      match p with
      | .list [n, x] => do return (← n.name, ← x.int)
      | _ => .error "expected (name value)"
    | _ => .error "expected a list of (name value)"
  | _ => .error "expected (vals ...)"

end FCP
