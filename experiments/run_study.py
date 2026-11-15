"""FCP experimental study.

For every corpus design it measures
  * formalization accuracy of the agent sets (semantic relation to gold, per requirement)
  * defect detection on injected RTL defects and on AI-generated RTL
  * false assurance of the naive flow (proved => assured) versus FCP (ASSURED level)
    on real agent formalizations
  * a controlled fault-injection study on the gold formalizations
  * proof coverage, mutation assurance coverage, runtime and review-queue size

Usage: python experiments/run_study.py [design ...]
Results: experiments/results/<design>.json and experiments/results/summary.md
"""
from __future__ import annotations

import copy
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

import yaml  # noqa: E402

from fcp import pipeline  # noqa: E402
from fcp.analyses import Session  # noqa: E402
from fcp.ir import load_fset  # noqa: E402
from fcp.lang import FcpError  # noqa: E402
import faults  # noqa: E402

DESIGNS = ['fifo', 'arbiter', 'bridge', 'hub']
CACHE = os.path.join(ROOT, '.fcp-cache')
OUT = os.path.join(HERE, 'results')
TMP = os.path.join(OUT, 'tmp')


def log(*a):
    print(time.strftime('%H:%M:%S'), *a, flush=True)


def build_ev(S: Session, sets: list[str], variants: list[str], mutation_n: int) -> dict:
    """Run the FCP analyses needed for verdicts on every (set, variant)."""
    b = S.b
    ev = {'design': b.design, 'requirements': {r.id: r.__dict__ for r in b.requirements.values()},
          'interface': {'params': b.iface.params, 'signals': [s.__dict__ for s in b.iface.signals]},
          'sets': {}, 'compare': {}, 'runtime': {}}
    rt = ev['runtime']
    for s in sets:
        fs = b.fsets[s]
        rec = {'origin': fs.get('origin', {}), 'unformalized': fs.get('unformalized', []) or [], 'rtl': {}}
        ev['sets'][s] = rec
        try:
            m = S.mon(s)
        except FcpError as e:
            rec['error'] = str(e)
            log(f'  [{s}] ill-formed: {e}')
            continue
        rec['items'] = {it.id: {'role': it.role, 'req': it.req, 'pattern': it.pattern, 'english': it.english,
                                'formula': it.formula, 'signals': it.signals, 'raw': it.args.raw, 'note': it.note}
                        for it in m.items.values()}
        rec['lint'] = pipeline.lint(S, s)
        t = time.time()
        rec['tautology'] = S.tautology(s)
        rec['consistency'] = S.consistency(s)
        rt[f'{s}:spec'] = round(time.time() - t, 1)
        t = time.time()
        try:
            recv = S.receptive(s, 'ref')
        except Exception as e:  # analysis errors are recorded, never fatal
            recv = {'receptive': None, 'error': str(e)[:300]}
        rt[f'{s}:receptive'] = round(time.time() - t, 1)
        for v in variants:
            t = time.time()
            vr = {'verify': S.verify(s, v, replay=(v != 'ref')), 'vacuity': S.vacuity(s, v), 'receptive': recv}
            tri = {}
            for pid, r in vr['verify'].items():
                if r['status'] == 'FAILED' and r.get('trace'):
                    try:
                        tri[pid] = S.triage(s, r['trace'])
                    except Exception as e:
                        tri[pid] = {'class': 'ERROR', 'error': str(e)[:200]}
            vr['triage'] = tri
            rec['rtl'][v] = vr
            rt[f'{s}:{v}:rtl'] = round(time.time() - t, 1)
        t = time.time()
        rec['mutation'] = S.mutation(s, 'ref', n=mutation_n, obs_set='gold')
        rt[f'{s}:mutation'] = round(time.time() - t, 1)
        log(f'  [{s}] done; mutation coverage {rec["mutation"]["coverage"]}')
    ok = [s for s in sets if 'error' not in ev['sets'][s]]
    for i, sa in enumerate(ok):
        for sb in ok[i + 1:]:
            t = time.time()
            ev['compare'][f'{sa}|{sb}'] = S.compare(sa, sb)          # contracts (FCP's decision)
            rt[f'compare:{sa}|{sb}'] = round(time.time() - t, 1)
    ev['compare_env'] = {}
    for s in ok:
        if s != 'gold':
            t = time.time()
            ev['compare_env'][f'gold|{s}'] = S.compare('gold', s, env='gold')   # properties (measurement)
            rt[f'compare_env:gold|{s}'] = round(time.time() - t, 1)
    return ev


def peer_view(ev: dict, peers: list[str]) -> dict:
    """Restrict the comparison table to a set's admissible peers (never gold)."""
    e2 = dict(ev)
    e2['compare'] = {k: v for k, v in ev['compare'].items() if set(k.split('|')) <= set(peers)}
    return e2


def ground_truth(ev: dict, variants: list[str]) -> dict:
    """violated[v][req] = some gold property (or covering property) of req fails on v."""
    g = ev['sets']['gold']
    items = g['items']
    gt = {}
    for v in variants:
        ver = g['rtl'][v]['verify']
        d = {}
        for rid in ev['requirements']:
            props = [p for p, it in items.items() if it['req'] == rid and it['role'] == 'property']
            for u in g['unformalized']:
                if u['req'] == rid and u.get('covered_by'):
                    props += [p for p in u['covered_by'] if p in ver]
            if props:
                d[rid] = any(ver[p]['status'] == 'FAILED' for p in props)
        gt[v] = d
    return gt


def verdicts(ev: dict, s: str, v: str, peers: list[str]) -> dict:
    A = pipeline.assess(peer_view(ev, [s] + peers), s, v)
    ver = ev['sets'][s]['rtl'][v]['verify']
    out = {}
    for rid, r in A['requirements'].items():
        if not r['properties']:
            continue
        naive = all(ver[p]['status'] == 'PROVED' for p in r['properties'])
        out[rid] = {'naive': naive, 'fcp': r['level'] == 'ASSURED', 'level': r['level'], 'flags': r['flags']}
    return {'reqs': out, 'queue': A['queue'], 'summary': A['summary']}


def accuracy(ev: dict, s: str) -> dict:
    """Property accuracy (under the gold environment) and assumption accuracy."""
    cmp_ = ev.get('compare_env', {}).get(f'gold|{s}', {})
    asm = ev['compare'].get(f'gold|{s}', {}).get('<assumptions>', {}).get('relation', 'EQUIVALENT')
    rel = {}
    for rid, c in cmp_.items():
        if rid == '<assumptions>':
            continue
        r = c['relation']
        # relation is gold vs agent: invert to agent vs gold
        r = {'A-STRONGER': 'WEAKER', 'A-WEAKER': 'STRONGER', 'ONLY-A': 'MISSING', 'ONLY-B': 'EXTRA'}.get(r, r)
        rel[rid] = r
    counts = {}
    for r in rel.values():
        counts[r] = counts.get(r, 0) + 1
    graded = [r for r in rel.values() if r not in ('EXTRA',)]
    asm = {'A-STRONGER': 'WEAKER', 'A-WEAKER': 'STRONGER'}.get(asm, asm)   # agent's environment vs gold's
    return {'per_req': rel, 'counts': counts, 'assumptions_vs_gold': asm,
            'equivalent_rate': round(sum(1 for r in graded if r == 'EQUIVALENT') / len(graded), 3) if graded else None}


def fault_study(S: Session, ev: dict, variants: list[str], agent_sets: list[str]) -> list[dict]:
    """Inject one formalization fault at a time into gold and see who notices."""
    g = S.b.fsets['gold']
    gitems = ev['sets']['gold']['items']
    rows = []
    os.makedirs(TMP, exist_ok=True)
    k = 0
    for p in g.get('properties', []):
        req = p.get('req')
        same_req = [q for q in g['properties'] if q.get('req') == req]
        variants_of_p = [(name, op(p)) for name, op in faults.OPERATORS.items()]
        mask = faults.masking_assumption(g, p)
        if mask:
            variants_of_p.append(('masking-assumption', ('MASK', mask)))
        for fname, fp in variants_of_p:
            if fp is None:
                continue
            k += 1
            base = copy.deepcopy(g)
            base.pop('scenarios', None)
            base.pop('dont_cares', None)
            base.pop('unformalized', None)
            ref_set = copy.deepcopy(base)
            ref_set['set'] = f'gref{k}'
            ref_set['properties'] = copy.deepcopy(same_req)
            fs = copy.deepcopy(base)
            fs['set'] = f'gflt{k}'
            if isinstance(fp, tuple):         # masking assumption
                fs['properties'] = copy.deepcopy(same_req)
                fs['assumptions'] = list(fs.get('assumptions') or []) + [fp[1]]
            else:
                fs['properties'] = [fp if q['id'] == p['id'] else copy.deepcopy(q) for q in same_req]
            for st in (ref_set, fs):
                path = os.path.join(TMP, f'{S.b.design}_{st["set"]}.yaml')
                with open(path, 'w') as f:
                    yaml.safe_dump(st, f, sort_keys=False)
                load_fset(S.b, path)
            try:
                S.mon(fs['set'])
                S.mon(ref_set['set'])
            except FcpError as e:
                rows.append({'prop': p['id'], 'req': req, 'fault': fname, 'error': str(e)[:200]})
                continue
            rel = S.compare(ref_set['set'], fs['set']).get(req, {}).get('relation')
            if rel == 'EQUIVALENT':
                rows.append({'prop': p['id'], 'req': req, 'fault': fname, 'semantic_fault': False})
                continue
            peer_rel = {}
            for a in agent_sets:
                c = S.compare(fs['set'], a).get(req)
                peer_rel[a] = c['relation'] if c else None
            taut = S.tautology(fs['set'])
            rec_ = S.receptive(fs['set'], 'ref') if isinstance(fp, tuple) else {'receptive': True}
            per_v = {}
            for v in variants:
                ver = S.verify(fs['set'], v, replay=False)
                vac = S.vacuity(fs['set'], v)['properties']
                gold_fail = any(ev['sets']['gold']['rtl'][v]['verify'][q['id']]['status'] == 'FAILED' for q in same_req)
                proved = all(x['status'] == 'PROVED' for x in ver.values())
                vacuous = any(taut[q]['tautology'] or vac[q].get('vacuous') == 'PROVEN' for q in ver)
                agreed = bool(peer_rel) and all(x == 'EQUIVALENT' for x in peer_rel.values())
                fcp_assured = proved and not vacuous and rec_.get('receptive', True) and agreed
                per_v[v] = {'gold_fail': gold_fail, 'naive_assured': proved, 'fcp_assured': fcp_assured,
                            'vacuous': vacuous}
            flagged_by = []
            if any(x['vacuous'] for x in per_v.values()):
                flagged_by.append('vacuity')
            if rec_.get('receptive') is False:
                flagged_by.append('receptiveness')
            if any(x not in ('EQUIVALENT', None) for x in peer_rel.values()):
                flagged_by.append('peer-disagreement')
            if not per_v['ref']['naive_assured']:
                flagged_by.append('fails-on-reference')
            rows.append({'prop': p['id'], 'req': req, 'fault': fname, 'semantic_fault': True,
                         'relation_to_gold': rel, 'peers': peer_rel, 'flagged_by': flagged_by,
                         'variants': per_v})
    return rows


def summarize_design(d: str, ev: dict, variants: list[str], agent_sets: list[str], fault_rows: list[dict]) -> dict:
    gt = ground_truth(ev, variants)
    bugs = [v for v in variants if v != 'ref']
    res = {'design': d, 'variants': variants, 'agent_sets': agent_sets, 'sets': {}}
    for s in ['gold'] + agent_sets + (['literal'] if 'literal' in ev['sets'] else []):
        if s not in ev['sets'] or 'error' in ev['sets'][s]:
            res['sets'][s] = {'ill_formed': ev['sets'].get(s, {}).get('error', 'missing')}
            continue
        peers = [a for a in agent_sets if a != s] if s in agent_sets else agent_sets
        sr = ev['sets'][s]
        det = {}
        fa_naive = fa_fcp = viol = 0
        design_fa_naive = design_fa_fcp = 0
        per_v = {}
        for v in variants:
            vd = verdicts(ev, s, v, peers)
            ver = sr['rtl'][v]['verify']
            failed = [p for p, x in ver.items() if x['status'] == 'FAILED']
            if v != 'ref':
                det[v] = bool(failed)
            for rid, x in vd['reqs'].items():
                if gt[v].get(rid):
                    viol += 1
                    fa_naive += x['naive']
                    fa_fcp += x['fcp']
            buggy = any(gt[v].values())
            if v != 'ref' and buggy:
                design_fa_naive += all(x['naive'] for x in vd['reqs'].values())
                design_fa_fcp += all(x['fcp'] for x in vd['reqs'].values())
            per_v[v] = {'summary': vd['summary'], 'queue': len(vd['queue']), 'failed': failed,
                        'triage': {p: t['class'] for p, t in sr['rtl'][v].get('triage', {}).items()}}
        props = [p for p, it in sr['items'].items() if it['role'] == 'property']
        refver = sr['rtl']['ref']['verify']
        ref_levels = {rid: x['level'] for rid, x in verdicts(ev, s, 'ref', peers)['reqs'].items()}
        injected = [v for v in variants if v.startswith('B')]
        others = {v: {'gold_says_buggy': any(gt[v].values()), 'detected': det.get(v)} for v in variants
                  if v != 'ref' and v not in injected}
        res['sets'][s] = {
            'n_properties': len(props),
            'n_assumptions': sum(1 for it in sr['items'].values() if it['role'] == 'assumption'),
            'proved_on_ref': sum(1 for p in props if refver[p]['status'] == 'PROVED'),
            'failed_on_ref': [p for p in props if refver[p]['status'] == 'FAILED'],
            'detected': det, 'detection_rate': round(sum(det.values()) / len(det), 3) if det else None,
            'injected_detected': sum(1 for v in injected if det.get(v)), 'injected_total': len(injected),
            'other_variants': others, 'ref_levels': ref_levels,
            'violations': viol, 'false_assurance_naive': fa_naive, 'false_assurance_fcp': fa_fcp,
            'design_false_assurance_naive': design_fa_naive, 'design_false_assurance_fcp': design_fa_fcp,
            'mutation_coverage': sr['mutation']['coverage'], 'mutants_observable': sr['mutation']['observable'],
            'mutants_killed': sr['mutation']['killed'],
            'receptive': sr['rtl']['ref']['receptive'].get('receptive'),
            'conflicts': [c['reqs'] for c in sr['consistency']['conflicts']],
            'unreachable_scenarios': sr['consistency'].get('unreachable_scenarios', []),
            'tautologies': [p for p, x in sr['tautology'].items() if x['tautology']],
            'vacuous_on_ref': [p for p, x in sr['rtl']['ref']['vacuity']['properties'].items()
                               if x.get('vacuous') == 'PROVEN'],
            'lint': [l for l in sr['lint'] if l['severity'] in ('error', 'warning')],
            'per_variant': per_v,
        }
        if s in agent_sets:
            res['sets'][s]['accuracy'] = accuracy(ev, s)
    if len(agent_sets) == 2 and f'{agent_sets[0]}|{agent_sets[1]}' in ev['compare']:
        ab = ev['compare'][f'{agent_sets[0]}|{agent_sets[1]}']
        acc_a = res['sets'][agent_sets[0]].get('accuracy', {}).get('per_req', {})
        acc_b = res['sets'][agent_sets[1]].get('accuracy', {}).get('per_req', {})
        # does agent-agent disagreement predict an error w.r.t. gold?
        tp = fp = fn = tn = 0
        for rid, c in ab.items():
            if rid == '<assumptions>' or rid not in acc_a or rid not in acc_b:
                continue
            disagree = c['relation'] not in ('EQUIVALENT',)
            env_ok = lambda a: res['sets'][a]['accuracy']['assumptions_vs_gold'] == 'EQUIVALENT'
            # a contract is right if its property matches gold and its environment does too
            wrong = (acc_a[rid] != 'EQUIVALENT' or not env_ok(agent_sets[0]) or
                     acc_b[rid] != 'EQUIVALENT' or not env_ok(agent_sets[1]))
            tp += disagree and wrong
            fp += disagree and not wrong
            fn += (not disagree) and wrong
            tn += (not disagree) and not wrong
        res['disagreement_as_error_detector'] = {'tp': tp, 'fp': fp, 'fn': fn, 'tn': tn}
    sem = [r for r in fault_rows if r.get('semantic_fault')]
    hidden = [r for r in sem if any(x['gold_fail'] and x['naive_assured'] for x in r['variants'].values())]
    hidden_fcp = [r for r in sem if any(x['gold_fail'] and x['fcp_assured'] for x in r['variants'].values())]
    res['faults'] = {'injected': len(fault_rows), 'semantic': len(sem),
                     'equivalent_mutations': sum(1 for r in fault_rows if r.get('semantic_fault') is False),
                     'flagged': sum(1 for r in sem if r['flagged_by']),
                     'hides_bug_naive': len(hidden), 'hides_bug_fcp': len(hidden_fcp),
                     'by_operator': {}}
    for r in sem:
        o = res['faults']['by_operator'].setdefault(r['fault'], {'n': 0, 'flagged': 0, 'hides_bug_naive': 0,
                                                                 'hides_bug_fcp': 0, 'flagged_by': {}})
        o['n'] += 1
        o['flagged'] += bool(r['flagged_by'])
        o['hides_bug_naive'] += r in hidden
        o['hides_bug_fcp'] += r in hidden_fcp
        for f in r['flagged_by']:
            o['flagged_by'][f] = o['flagged_by'].get(f, 0) + 1
    res['runtime'] = ev['runtime']
    return res


def run_design(d: str, mutation_n: int = 60) -> dict:
    t0 = time.time()
    log(f'== {d}')
    S = Session(os.path.join(ROOT, 'corpus', d), cache=CACHE, jobs=28)
    sets = [s for s in ['gold', 'agent_a', 'agent_b', 'literal'] if s in S.b.fsets]
    agent_sets = [s for s in ['agent_a', 'agent_b'] if s in S.b.fsets]
    variants = ['ref'] + sorted(S.bugs()) + [k for k in S.b.rtl if k != 'ref']
    ev = build_ev(S, sets, variants, mutation_n)
    good_agents = [a for a in agent_sets if 'error' not in ev['sets'][a]]
    log(f'  fault study')
    t = time.time()
    rows = fault_study(S, ev, variants, good_agents)
    ev['runtime']['fault_study'] = round(time.time() - t, 1)
    res = summarize_design(d, ev, variants, good_agents, rows)
    res['fault_rows'] = rows
    res['wall_seconds'] = round(time.time() - t0, 1)
    os.makedirs(OUT, exist_ok=True)
    pipeline.save(ev, os.path.join(OUT, f'{d}_evidence.json'))
    with open(os.path.join(OUT, f'{d}.json'), 'w') as f:
        json.dump(res, f, indent=1, default=str)
    log(f'== {d} done in {res["wall_seconds"]}s')
    return res


if __name__ == '__main__':
    ds = sys.argv[1:] or DESIGNS
    for d in ds:
        run_design(d)
