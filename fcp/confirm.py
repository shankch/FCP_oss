"""A second solver on every proof: what z3 found unsatisfiable, decided again by cvc5.

A PROVED verdict of fcp.prove rests on answers of one solver: each time z3
says that a formula has no model.  This module records every such formula
while a proof runs, in SMT-LIB text, and gives each to cvc5, a solver that
shares no code with z3.  A verdict is *confirmed* when cvc5 finds every
formula behind it unsatisfiable too; it is *refuted* when cvc5 finds a model
of one of them (the two solvers disagree, and neither is believed); it is
*unconfirmed* when cvc5 gives no answer in its time.

    with recording() as rec:
        pr = prove.prove(S, s, fn, src, calls, res)
    answers = Checker().check(rec.texts)
    confirmations(pr, rec, answers)       # per requirement: confirmed, refuted, unconfirmed

What is confirmed is the solver's part and nothing more.  The translation
of the code and of the reading into formulas, the rewriting done before a
formula reaches the solver (z3.simplify, the substitutions of fcp.sweep),
z3's printer and the way the engine puts the answers together (induction,
Houdini) are trusted as before; fcp.prove checks the first of these on the
scope's calls.  A failure needs no second solver: its calls are run on the
real code and on the compiled monitors.  (This is not FCP's certification
rule, which is about readings; here two solvers are compared on one
reading.)

The formulas behind one requirement are those z3 answered while the
requirement was being settled (prove.py calls tag(req) there) and those
answered before any requirement was (the agreements of a sweep, the
invariant of an induction), which every requirement of the proof leans on.
"""
from __future__ import annotations

import contextlib
import hashlib
import multiprocessing
import os
import re
import time
from typing import Optional

_ACTIVE: Optional['Recorder'] = None
_QUOTED = r'\|[^|]*\||"(?:[^"]|"")*"'      # a quoted symbol or a string: never rewritten
# z3 prints a disjunction of nothing as the bare word `or` (a conjunction: `and`), which is not SMT-LIB
_BARE = re.compile(_QUOTED + r'|(?<=[ \n])(or|and)(?=[ )\n])')
_MOD = re.compile(_QUOTED + r'|\((mod) ')
SHARED = ''                              # the tag of what is answered before any requirement is


class Recorder:
    """The formulas z3 found unsatisfiable during one proof, by the requirement being settled."""

    def __init__(self):
        self.texts: dict[str, str] = {}              # digest -> SMT-LIB text
        self.by: dict[str, list[str]] = {}           # requirement (SHARED for none) -> digests
        self.answers = {'unsat': 0, 'sat': 0, 'unknown': 0}
        self.tag = SHARED

    def add(self, z3, solver, assumptions) -> None:
        s2 = z3.Solver()
        s2.add(solver.assertions())
        for a in assumptions:
            s2.add(*a) if isinstance(a, (list, tuple)) else s2.add(a)
        text = _BARE.sub(lambda m: {'or': 'false', 'and': 'true'}.get(m.group(1), m.group(0)), s2.to_smt2())
        d = hashlib.sha256(text.encode()).hexdigest()[:20]
        self.texts.setdefault(d, text)
        own = self.by.setdefault(self.tag, [])
        if d not in own:
            own.append(d)

    def behind(self, req: str) -> list[str]:
        """The digests of the formulas a verdict on `req` rests on: its own and the shared ones."""
        return list(dict.fromkeys(self.by.get(SHARED, []) + self.by.get(req, [])))


def tag(req: Optional[str]) -> None:
    """Called by the prover when it starts on a requirement; a no-op unless a proof is being recorded."""
    if _ACTIVE is not None:
        _ACTIVE.tag = req or SHARED


@contextlib.contextmanager
def recording():
    """Record every `unsat` answer of z3 inside the block.  Not reentrant."""
    global _ACTIVE
    import z3
    if _ACTIVE is not None:
        raise RuntimeError('a proof is already being recorded')
    rec = Recorder()
    orig = z3.Solver.check

    def check(self, *assumptions):
        r = orig(self, *assumptions)
        rec.answers[str(r)] = rec.answers.get(str(r), 0) + 1
        if r == z3.unsat:
            rec.add(z3, self, assumptions)
        return r

    z3.Solver.check = check
    _ACTIVE = rec
    try:
        yield rec
    finally:
        z3.Solver.check = orig
        _ACTIVE = None


# ----------------------------------------------------------------------------
# The second solver


def available() -> bool:
    try:
        import cvc5  # noqa: F401
        return True
    except ImportError:
        return False


def versions() -> dict:
    import cvc5
    import z3
    return {'z3': z3.get_version_string(), 'cvc5': _text(cvc5.Solver().getVersion())}


def _text(x) -> str:
    return x.decode() if isinstance(x, bytes) else str(x)


def logic_of(text: str) -> str:
    """The SMT-LIB logic of a formula as z3 printed it, read off its text; cvc5 picks its strategy by it."""
    if 'String' in text or '(Seq ' in text or 'declare-datatypes' in text:
        return 'ALL'
    return ('' if '(forall ' in text or '(exists ' in text else 'QF_') + ('A' if '(Array ' in text else '') + \
        ('UF' if re.search(r'\(declare-fun \S+ \((?!\))', text) else '') + ('BV' if '(_ BitVec' in text else '') + 'LIA'


def abstracted(text: str) -> Optional[str]:
    """The formula with `mod` read as a function of which nothing is known; None where it has no `mod`.

    A formula with no model under every reading of that function has none under `mod`, which is
    one of them: unsat on this text is unsat on the formula.  Any other answer on it says nothing.
    """
    if 'fcp_mod' in text:
        return None
    new = _MOD.sub(lambda m: '(fcp_mod ' if m.group(1) else m.group(0), text)
    return '(declare-fun fcp_mod (Int Int) Int)\n' + new if new != text else None


def _once(text: str, logic: str, opts: dict, tlimit: int, proof: bool) -> dict:
    import cvc5
    slv = cvc5.Solver()
    slv.setOption('tlimit-per', str(tlimit))
    for k, v in opts.items():
        slv.setOption(k, v)
    if proof:
        slv.setOption('produce-proofs', 'true')
    sm = cvc5.SymbolManager(slv)
    par = cvc5.InputParser(slv, sm)
    par.setStringInput(cvc5.InputLanguage.SMT_LIB_2_6, f'(set-logic {logic})\n' + text, 'obligation')
    res = ''
    while True:
        cmd = par.nextCommand()
        if cmd.isNull():
            break
        said = _text(cmd.invoke(slv, sm)).strip()
        if cmd.getCommandName() == 'check-sat' or said.startswith('(error'):
            res = said
            if said.startswith('(error'):
                break
    word = res.split()[0] if res.split() else ''
    out = {'result': word if word in ('unsat', 'sat', 'unknown') else 'error', 'logic': logic}
    if res != out['result']:                         # 'unknown (TIMEOUT)', or what cvc5 said instead of an answer
        out['why'] = res[:200]
    if opts:
        out['options'] = opts
    if proof and out['result'] == 'unsat':
        out['proof'] = _text(slv.proofToString(slv.getProof()[0], cvc5.ProofFormat.CPC))
    return out


# cvc5's ways with products; each of the last three has decided in a second what the others left open in 150
NONLINEAR = [{}, {'arith-brab': 'false'}, {'nl-icp': 'true'}, {'nl-cov': 'true', 'nl-ext': 'none'}]
QUICK = 3000                             # milliseconds for each attempt of the first round


def _long_order(plan: tuple) -> tuple:
    return not plan[3], plan[1] == 'ALL'             # the looser text, the named logic, no logic named


def decide(text: str, tlimit: int = 30000, proof: bool = False, total: Optional[int] = None) -> dict:
    """cvc5's answer on one formula: {'result': unsat | sat | unknown | error, 'seconds', ...}.

    cvc5 picks its procedures by the logic it is told, and none of its choices is best on every
    formula here, so the formula is given first with no logic named, then in the smallest logic
    that holds it, and a nonlinear one with each of cvc5's procedures for products as well: all
    of them for a few seconds each, then all again for `tlimit` milliseconds each.  The first
    answer of unsat or sat stands.  A formula with `mod` is also given with `mod` left open (see
    abstracted), where only unsat is an answer ('abstraction' then names what was left open); in
    the long round that text goes first, being the quicker one where it answers at all, and the
    named logic before none (it has decided in 15 minutes what no logic named left open).  With
    `proof`, an unsat answer comes with cvc5's proof in its CPC format ('proof'), which the
    checker Ethos reads; nothing here checks it.

    With `total`, the formula has had its two rounds and is given one more go: the long round
    alone, `total` milliseconds for all of its attempts together.
    """
    t = time.time()
    logic = logic_of(text)
    plans = [(text, 'ALL', {}, '')] + ([(text, logic, {}, '')] if logic != 'ALL' else [])
    loose = abstracted(text)
    if loose is not None:
        plans.append((loose, logic_of(loose), {}, 'mod'))
    out, tried = {'result': 'error', 'why': 'not tried'}, 0
    if total is not None:
        plans.sort(key=_long_order)
    for budget in sorted({min(QUICK, tlimit), tlimit}) if total is None else [tlimit]:
        k = 0
        while k < len(plans):
            body, lg, opts, left_open = plans[k]
            left = budget if total is None else min(budget, int(total - (time.time() - t) * 1000))
            if left < 1000 and tried:
                break                                # the go is spent
            try:
                got = _once(body, lg, opts, max(left, 1000), proof)
            except Exception as e:                   # a symbol cvc5 does not read, a resource limit
                got = {'result': 'error', 'why': f'{type(e).__name__}: {e}'[:200]}
            tried += 1
            if got['result'] == 'error' and 'linear' in got.get('why', '') and 'LIA' in lg:
                plans[k:k + 1] = [(body, lg.replace('LIA', 'NIA'), o, left_open) for o in NONLINEAR]
                continue                             # products: the same place again, in the nonlinear logic
            k += 1
            if left_open:
                if got['result'] != 'unsat':
                    if out.get('why') == 'not tried':
                        out = {'result': 'unknown', 'why': f'with {left_open} left open: ' + got.get('why', got['result'])}
                    continue                         # a model of the looser formula is none of this one
                got['abstraction'] = left_open
            if got['result'] in ('unsat', 'sat') or out['result'] == 'error':
                out = got
            if out['result'] in ('unsat', 'sat'):
                break
        if out['result'] in ('unsat', 'sat'):
            break
        plans.sort(key=_long_order)
    out['attempts'] = tried
    out['seconds'] = round(time.time() - t, 3)
    return out


def _work(job: tuple) -> tuple:
    d, text, tlimit, total = job
    return d, decide(text, tlimit, total=total)


class Checker:
    """cvc5 on many formulas, in worker processes; an answer is kept by digest and given once."""

    def __init__(self, workers: int = 4, tlimit: int = 30000):
        self.workers, self.tlimit = workers, tlimit
        self.known: dict[str, dict] = {}
        self._pool = None

    def _open(self):
        if self._pool is None:
            self._pool = multiprocessing.get_context('spawn').Pool(self.workers, maxtasksperchild=4000)
        return self._pool

    def close(self) -> None:
        if self._pool is not None:
            self._pool.terminate()
            self._pool = None

    def _run(self, todo: list, wait: float) -> dict[str, dict]:
        got = {}
        if todo:
            it = self._open().imap_unordered(_work, todo)
            try:
                for _ in todo:
                    d, ans = it.next(timeout=wait)
                    got[d] = ans
            except multiprocessing.TimeoutError:     # a worker that does not come back: start afresh
                self.close()
        return got

    def check(self, texts: dict[str, str]) -> dict[str, dict]:
        todo = [(d, t, self.tlimit, None) for d, t in texts.items() if d not in self.known]
        got = self._run(todo, 6 * self.tlimit / 1000 + 120)
        for d, *_ in todo:
            self.known[d] = got.get(d, {'result': 'unknown', 'why': 'no answer from the worker', 'seconds': 0})
        return {d: self.known[d] for d in texts}

    def again(self, texts: dict[str, str], tlimit: int) -> list[str]:
        """One more go, `tlimit` milliseconds each, at the formulas left open; the digests it settled.

        'seconds' of a formula is then all the time cvc5 had on it, and 'again' the limit of this go.
        """
        todo = [(d, t, tlimit, tlimit) for d, t in texts.items() if self.known[d]['result'] not in ('unsat', 'sat')]
        got, settled = self._run(todo, tlimit / 1000 + 120), []
        for d, *_ in todo:
            first, ans = self.known[d], got.get(d, {'result': 'unknown', 'why': 'no answer from the worker', 'seconds': 0})
            if ans['result'] in ('unsat', 'sat'):
                settled.append(d)
            else:
                ans = {**first, **{k: ans[k] for k in ('why',) if k in ans}}
                ans['seconds'] = got.get(d, {}).get('seconds', tlimit / 1000)
            ans['seconds'] = round(ans['seconds'] + first.get('seconds', 0), 3)
            ans['again'] = tlimit
            self.known[d] = ans
        return settled


def confirmations(pr: dict, rec: Recorder, answers: dict[str, dict]) -> dict[str, dict]:
    """Per requirement the proof settled as proved: the formulas behind it and what cvc5 says of them."""
    out = {}
    for req, v in (pr.get('requirements') or {}).items():
        if v['status'] not in ('PROVED', 'PROVED-BOUNDED'):
            continue
        ds = rec.behind(req)
        got = [answers[d]['result'] for d in ds]
        conf = {'formulas': len(ds), 'own': len(rec.by.get(req, [])),
                'status': 'none' if not ds else 'refuted' if 'sat' in got else
                          'confirmed' if all(g == 'unsat' for g in got) else 'unconfirmed'}
        if conf['status'] in ('refuted', 'unconfirmed'):
            conf['open'] = {d: answers[d]['result'] for d in ds if answers[d]['result'] != 'unsat'}
        out[req] = conf
    return out


def main(argv: list[str]) -> int:
    """python -m fcp.confirm [--tlimit MS] FILE.smt2 ... : cvc5's answer on formulas kept on disk."""
    bad, tlimit = 0, 30000
    if argv[:1] == ['--tlimit']:
        tlimit, argv = int(argv[1]), argv[2:]
    for p in argv:
        with open(p) as f:
            ans = decide(f.read(), tlimit)
        bad += ans['result'] != 'unsat'
        print(os.path.basename(p), ans['result'], ans['seconds'], ans.get('why', ''))
    return 1 if bad else 0


if __name__ == '__main__':
    import sys
    raise SystemExit(main(sys.argv[1:]))
