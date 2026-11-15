"""A second solver on the proofs of a study: z3's answers decided again by cvc5 (fcp.confirm).

    python experiments/confirm_demo.py [corpus] [--tlimit MS] [--again MS] [--workers N] [--keep]

The proofs of experiments/prove_demo.py are run again with every formula
that z3 finds unsatisfiable recorded, and each formula is given to cvc5.
Every requirement proved (PROVED or PROVED-BOUNDED) is
*confirmed* when cvc5 finds each formula behind the verdict unsatisfiable,
*refuted* when it finds a model of one, *unconfirmed* when it answers
neither way in its time, and *none* when z3 was asked nothing (the goal
was settled by rewriting).  cvc5 has --tlimit milliseconds for each of
its attempts at a formula (10 seconds), and the formulas then left open
get one more go of --again milliseconds each when the study is over (45
minutes; 0 for none).  Failures need no second solver: their calls are
replayed on the code.  Formulas cvc5 did not confirm are kept in
corpus/<corpus>/.fcp/confirm/ (all of them with --keep).
Writes experiments/results/confirm_<corpus>.json.
"""
from __future__ import annotations

import collections
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

from fcp import confirm as C, effects as FX, prove as P, software as SW  # noqa: E402
from fcp.analyses import Session  # noqa: E402
import prove_demo as PD  # noqa: E402


def main():
    if not C.available():
        sys.exit('cvc5 is not installed: .venv/bin/pip install cvc5')
    args = sys.argv[1:]
    keep = '--keep' in args
    opt = {k: int(args[args.index(k) + 1]) for k in ('--tlimit', '--workers', '--again') if k in args}
    names = [a for i, a in enumerate(args) if not a.startswith('--') and (i == 0 or args[i - 1] not in opt)]
    corpus = names[0] if names else 'code_checkout'
    B = os.path.join(ROOT, 'corpus', corpus)
    sets = [s for s in PD.SETS if os.path.exists(os.path.join(B, 'formal', f'{s}.yaml'))]
    S = Session(B, sets=sets)
    fn = SW.function(S)
    ifc = FX.interface(S, fn)
    frame_reqs = {S.mon(s).items[i].req for s in sets for i in S.b.frame_ids if i in S.mon(s).items}
    calls = FX.scope(S, fn, ifc) if ifc else SW.calls_for(S, fn)
    store = os.path.join(B, '.fcp', 'confirm')
    os.makedirs(store, exist_ok=True)
    for f in os.listdir(store):                      # the store holds the last run's formulas only
        if f.endswith('.smt2'):
            os.remove(os.path.join(store, f))
    ck = C.Checker(workers=opt.get('--workers', 4), tlimit=opt.get('--tlimit', 10000))
    again = opt.get('--again', 2700000)
    out = {'solver': C.versions(), 'tlimit_ms': ck.tlimit, 'implementations': {}}
    tally = collections.Counter()
    seen: dict[str, int] = {}                        # digest -> bytes, over the whole study
    held = {}                                        # (implementation, set) -> its proof, where a formula is open
    t0 = time.time()
    for name, src in PD.implementations(B, fn.name, fn.module or '').items():
        res = FX.run(fn, ifc, src, calls) if ifc else SW.run(fn, src, calls)
        rec_i = {}
        for s in sets:
            t = time.time()
            with C.recording() as rec:
                pr = P.prove_effects(S, s, fn, ifc, src, calls, res) if ifc else \
                    P.prove_object(S, s, fn, src, calls, res) if fn.stateful else P.prove(S, s, fn, src, calls, res)
            t_proof = round(time.time() - t, 1)
            if pr['status'] != 'ok':
                rec_i[s] = {'status': pr['status']}
                continue
            t = time.time()
            answers = ck.check(rec.texts)
            confs = {r: c for r, c in C.confirmations(pr, rec, answers).items() if r not in frame_reqs}
            for d, text in rec.texts.items():
                seen[d] = len(text)
                if keep or answers[d]['result'] != 'unsat':
                    with open(os.path.join(store, d + '.smt2'), 'w') as f:
                        f.write(text)
            if any(answers[d]['result'] not in ('unsat', 'sat') for d in rec.texts):
                held[name, s] = ({'requirements': {r: {'status': v['status']} for r, v in pr['requirements'].items()}},
                                 rec)
            tally['pairs'] += 1
            for c in confs.values():
                tally['proved'] += 1
                tally[c['status']] += 1
            rec_i[s] = {'status': 'ok', 'seconds': {'proof': t_proof, 'cvc5': round(time.time() - t, 1)},
                        'z3_answers': rec.answers, 'formulas': len(rec.texts), 'requirements': confs}
            print(name, s, t_proof, 's proof,', rec_i[s]['seconds']['cvc5'], 's cvc5,', len(rec.texts), 'formulas',
                  {r: c['status'] for r, c in confs.items()}, flush=True)
        out['implementations'][name] = rec_i
    write(out, tally, seen, ck, corpus, t0)             # kept should the second go be cut short
    if again and held:
        t = time.time()
        texts = {d: x for _, rec in held.values() for d, x in rec.texts.items() if ck.known[d]['result'] != 'unsat'}
        settled = set(ck.again(texts, again))
        for (name, s), (pr, rec) in held.items():
            if not settled & set(rec.texts):
                continue
            was = out['implementations'][name][s]['requirements']
            now = {r: c for r, c in C.confirmations(pr, rec, {d: ck.known[d] for d in rec.texts}).items() if r in was}
            tally.subtract(c['status'] for c in was.values())
            tally.update(c['status'] for c in now.values())
            out['implementations'][name][s]['requirements'] = now
            print(name, s, 'again:', {r: c['status'] for r, c in now.items()}, flush=True)
        for d in settled:
            if ck.known[d]['result'] == 'unsat' and not keep:
                os.remove(os.path.join(store, d + '.smt2'))
        out['again'] = {'tlimit_ms': again, 'formulas': len(texts), 'settled': len(settled),
                        'seconds': round(time.time() - t)}
        print('again:', out['again'], flush=True)
    ck.close()
    write(out, tally, seen, ck, corpus, t0)
    print(json.dumps({k: v for k, v in out['summary'].items() if k != 'not_unsat'}, indent=1))


def write(out, tally, seen, ck, corpus, t0):
    got = collections.Counter(ck.known[d]['result'] for d in seen)
    slow = sorted((ck.known[d]['seconds'] for d in seen), reverse=True)
    out['summary'] = {
        'pairs': tally['pairs'], 'proved': tally['proved'],
        'confirmed': tally['confirmed'], 'unconfirmed': tally['unconfirmed'], 'refuted': tally['refuted'],
        'none': tally['none'],
        'formulas': {'distinct': len(seen), 'bytes': sum(seen.values()), **{k: got.get(k, 0) for k in
                                                                         ('unsat', 'sat', 'unknown', 'error')},
                     'abstracted': sum('abstraction' in ck.known[d] for d in seen),
                     'again': sum('again' in ck.known[d] for d in seen)},
        'cvc5_seconds': {'total': round(sum(slow), 1), 'max': slow[0] if slow else 0,
                         'over_1s': sum(x > 1 for x in slow)},
        'not_unsat': {d: {k: v for k, v in ck.known[d].items() if k != 'proof'} for d in seen
                      if ck.known[d]['result'] != 'unsat'}}
    out['seconds'] = round(time.time() - t0)
    with open(os.path.join(HERE, 'results', f'confirm_{corpus}.json'), 'w') as f:
        json.dump(out, f, indent=1)


if __name__ == '__main__':
    main()
