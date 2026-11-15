"""End-to-end FCP run: analyses -> evidence ledger -> requirement verdicts.

The evidence ledger is a JSON document that records, for every requirement,
the chain   source quote -> formal items -> engine runs -> verdict,   with the
content hashes of every input and the cache keys of every proof task, so the
whole chain can be audited and re-run.
"""
from __future__ import annotations

import datetime
import json
import math
import os
import time
from typing import Optional

from .analyses import Session
from .engine import tool_versions
from .ir import IR_VERSION
from .lang import FcpError

ALL = ('lint', 'tautology', 'consistency', 'determinacy', 'verify', 'vacuity', 'receptive', 'triage',
       'mutation', 'compare')


def lint(S: Session, s: str) -> list[dict]:
    out = []
    b = S.b
    ins = {x.name for x in b.iface.inputs}
    outs = {x.name for x in b.iface.outputs}
    m = S.mon(s)
    for it in m.items.values():
        sig = set(it.signals)
        if it.role == 'assumption':
            if not sig & ins:
                out.append({'item': it.id, 'severity': 'error', 'kind': 'not-environment',
                            'msg': 'assumption mentions no design input: it can only be satisfied by the design '
                                   'itself, so it constrains the implementation rather than its environment'})
            elif sig & outs:
                out.append({'item': it.id, 'severity': 'info', 'kind': 'output-dependent',
                            'msg': f'assumption depends on design outputs ({", ".join(sorted(sig & outs))}); '
                                   'its receptiveness must be checked'})
            if not it.req:
                out.append({'item': it.id, 'severity': 'warning', 'kind': 'unjustified',
                            'msg': 'assumption is not traced to a requirement'})
        if it.role == 'property' and not sig & outs and it.id not in b.frame_ids:
            out.append({'item': it.id, 'severity': 'warning', 'kind': 'no-observable',
                        'msg': 'property mentions no design output, so it cannot constrain the design'})
    # a replay runs every combination of rigid values; a set with more than it runs is not replayed (found on
    # a reader of the rate limiter: three rigid variables, 4.3e12 combinations, and a lint that said nothing)
    from .rv import MAX_CASES
    cases = math.prod(hi - lo + 1 for _, _, lo, hi in m.rigid_ports)
    if cases > MAX_CASES:
        out.append({'item': 'rigids', 'severity': 'warning', 'kind': 'rigid-cases',
                    'msg': f'the rigid variables of this set have {cases:,} combinations of values. A replay runs '
                           f'every combination, up to {MAX_CASES:,}: code is not checked against this set, and a '
                           'comparison with it cannot confirm a difference it finds. Ghost state can often state '
                           'a rule for every value of a quantity without a rigid variable over that quantity'})
    fs = b.fsets[s]
    covered = {it.req for it in m.items.values() if it.req}
    covered |= {u['req'] for u in fs.get('unformalized', []) or []}
    for r in b.requirements.values():
        if r.id not in covered and r.kind in ('guarantee', 'assumption', 'dont_care'):
            out.append({'req': r.id, 'severity': 'error', 'kind': 'missing',
                        'msg': f'{r.kind} requirement has no formal item and no recorded reason for leaving it unformalized'})
    for u in fs.get('unformalized', []) or []:
        unknown = [i for i in u.get('covered_by') or [] if i not in m.items]
        if unknown:
            out.append({'req': u['req'], 'severity': 'error', 'kind': 'dangling-cover',
                        'msg': f'covered_by names items that do not exist: {", ".join(unknown)}'})
    # every requirement that can be formalized is, or says why not (found by a formalizer agent)
    covered = {it.req for it in m.items.values() if it.req} | \
        {u['req'] for u in fs.get('unformalized', []) or []}
    for r in b.requirements.values():
        if r.id not in covered and r.doc != 'FRAME' and r.kind in ('guarantee', 'assumption', 'scenario', 'dont_care'):
            out.append({'req': r.id, 'severity': 'warning', 'kind': 'uncovered',
                        'msg': f'{r.kind} {r.id} has no item and no `unformalized` entry: it would be reported MISSING'})
    # decisions: the reading taken for a flagged phrase, by its number in the requirement's list
    for dc in fs.get('decisions') or []:
        r = b.requirements.get(dc['req'])
        amb = {a.get('phrase'): a.get('readings') or [] for a in (r.ambiguity if r else [])}
        if r is None or dc['phrase'] not in amb:
            out.append({'req': dc['req'], 'severity': 'error', 'kind': 'bad-decision',
                        'msg': f'decision names no flagged phrase of {dc["req"]}: {dc["phrase"]!r}'})
        elif not 1 <= dc['reading'] <= len(amb[dc['phrase']]):
            out.append({'req': dc['req'], 'severity': 'error', 'kind': 'bad-decision',
                        'msg': f'reading {dc["reading"]} of {dc["phrase"]!r}: it has {len(amb[dc["phrase"]])} readings'})
    return out


def run(root: str, sets: list[str], rtl: list[str], cache: Optional[str] = None, jobs: int = 24,
        analyses=ALL, mutation_n: int = 60, mutation_variant: str = 'ref', extra_sets: Optional[dict] = None,
        log=print) -> dict:
    t_all = time.time()
    S = Session(root, sets=None, cache=cache, jobs=jobs)
    if extra_sets:
        from .ir import load_fset
        for name, path in extra_sets.items():
            load_fset(S.b, path, name)
    b = S.b
    ev = {'fcp': IR_VERSION, 'design': b.design, 'created': datetime.datetime.now().isoformat(timespec='seconds'),
          'tools': tool_versions(), 'fingerprint': b.fingerprint(), 'issues': b.issues,
          'requirements': {r.id: r.__dict__ for r in b.requirements.values()},
          'req_origin': b.req_origin, 'interface': {'params': b.iface.params,
                                                    'signals': [s.__dict__ for s in b.iface.signals]},
          'rtl_variants': {k: v.__dict__ for k, v in b.rtl.items()},
          'sets': {}, 'compare': {}, 'runtime': {}}
    rt = ev['runtime']

    def timed(key, fn):
        t = time.time()
        try:
            return fn()
        finally:
            rt[key] = round(time.time() - t, 2)
            log(f'  {key}: {rt[key]}s')

    for s in sets:
        fs = b.fsets[s]
        rec = {'origin': fs.get('origin', {}), 'unformalized': fs.get('unformalized', []) or [], 'rtl': {}}
        ev['sets'][s] = rec
        try:
            m = S.mon(s)
        except FcpError as e:
            rec['error'] = str(e)
            log(f'[{s}] ill-formed: {e}')
            continue
        rec['items'] = {it.id: {'role': it.role, 'req': it.req, 'pattern': it.pattern, 'english': it.english,
                                'formula': it.formula, 'signals': it.signals, 'mode': it.mode,
                                'raw': it.args.raw, 'det': 'okd' in it.out or it.role != 'property',
                                'note': it.note}
                        for it in m.items.values()}
        rec['monitor_lines'] = m.text.count('\n')
        log(f'[{s}] {len(S.props(s))} properties, {len(S.assumptions(s))} assumptions')
        if 'lint' in analyses:
            rec['lint'] = lint(S, s)
        if 'tautology' in analyses:
            rec['tautology'] = timed(f'{s}:tautology', lambda: S.tautology(s))
        if 'consistency' in analyses:
            rec['consistency'] = timed(f'{s}:consistency', lambda: S.consistency(s))
        if 'determinacy' in analyses:
            rec['determinacy'] = timed(f'{s}:determinacy', lambda: S.determinacy(s))
        for v in rtl:
            vr = {}
            rec['rtl'][v] = vr
            if 'verify' in analyses:
                vr['verify'] = timed(f'{s}:{v}:verify', lambda: S.verify(s, v))
                if 'triage' in analyses:
                    tri = {}
                    for pid, r in vr['verify'].items():
                        if r['status'] == 'FAILED' and r.get('trace'):
                            try:
                                tri[pid] = S.triage(s, r['trace'])
                            except Exception as e:  # triage is advisory
                                tri[pid] = {'class': 'ERROR', 'error': str(e)[:300]}
                    vr['triage'] = tri
            if 'vacuity' in analyses:
                vr['vacuity'] = timed(f'{s}:{v}:vacuity', lambda: S.vacuity(s, v))
            if 'receptive' in analyses:
                vr['receptive'] = timed(f'{s}:{v}:receptive', lambda: S.receptive(s, v))
        if 'mutation' in analyses and mutation_variant in rtl:
            rec['mutation'] = timed(f'{s}:mutation', lambda: S.mutation(s, mutation_variant, n=mutation_n))
    if 'compare' in analyses:
        ok = [s for s in sets if 'error' not in ev['sets'][s]]
        for i, sa in enumerate(ok):
            for sb in ok[i + 1:]:
                ev['compare'][f'{sa}|{sb}'] = timed(f'compare:{sa}|{sb}', lambda: S.compare(sa, sb))
    ev['engine_stats'] = dict(S.runner.stats)
    ev['assessment'] = {s: {v: assess(ev, s, v) for v in rtl} for s in sets if 'error' not in ev['sets'][s]}
    rt['total'] = round(time.time() - t_all, 2)
    return ev


# ----------------------------------------------------------------------------
# Requirement verdicts and the human review queue
# ----------------------------------------------------------------------------

def assess(ev: dict, s: str, v: str) -> dict:
    sr = ev['sets'][s]
    items = sr.get('items', {})
    vr = sr['rtl'].get(v, {})
    ver = vr.get('verify', {})
    vac = vr.get('vacuity', {}).get('properties', {})
    taut = sr.get('tautology', {})
    cons = sr.get('consistency', {})
    rec_ = vr.get('receptive', {})
    mut = sr.get('mutation', {})
    unf = {u['req']: u for u in sr.get('unformalized', [])}
    conflict_reqs = {}
    for c in cons.get('conflicts', []):
        for r in c['reqs']:
            conflict_reqs.setdefault(r, []).append(c['mus'])
    kills = {}
    for row in mut.get('mutants', []):
        for p in row.get('killed_by', []):
            kills[p] = kills.get(p, 0) + 1
    # independent peers that formalized the same requirement
    peer = {}
    for key, cmp_ in ev.get('compare', {}).items():
        a, b = key.split('|')
        if s not in (a, b):
            continue
        other = b if a == s else a
        for req, c in cmp_.items():
            rel = c['relation']
            if a != s:
                rel = {'A-STRONGER': 'A-WEAKER', 'A-WEAKER': 'A-STRONGER', 'ONLY-A': 'ONLY-B',
                       'ONLY-B': 'ONLY-A'}.get(rel, rel)
            peer.setdefault(req, {})[other] = {'relation': rel,
                                               'witness': c.get('witness_a_not_b') if a == s else c.get('witness_b_not_a'),
                                               'witness_rev': c.get('witness_b_not_a') if a == s else c.get('witness_a_not_b')}
    env_ok = rec_.get('receptive', True) is not False
    unjust = [l for l in sr.get('lint', []) if l['kind'] in ('unjustified', 'not-environment')]
    lint_by_item = {}
    for l in sr.get('lint', []):
        if 'item' in l:
            lint_by_item.setdefault(l['item'], []).append(l)
    out = {}
    for rid, r in ev['requirements'].items():
        props = [pid for pid, it in items.items() if it['req'] == rid and it['role'] == 'property']
        asm = [pid for pid, it in items.items() if it['req'] == rid and it['role'] == 'assumption']
        dcs = [pid for pid, it in items.items() if it['req'] == rid and it['role'] == 'dontcare']
        rec = {'req': rid, 'kind': r['kind'], 'properties': props, 'assumptions': asm, 'dont_cares': dcs,
               'flags': [], 'peers': peer.get(rid, {})}
        if props:
            st = [ver.get(p, {}).get('status', 'NOT-RUN') for p in props]
            if 'FAILED' in st or 'ENGINE-DISAGREEMENT' in st:
                status = 'FAILED'
            elif 'UNKNOWN' in st or 'NOT-RUN' in st:
                status = 'UNKNOWN'
            elif 'BOUNDED' in st:
                status = 'BOUNDED'
            else:
                status = 'PROVED'
            rec['property_status'] = dict(zip(props, st))
            if 'ENGINE-DISAGREEMENT' in st:
                rec['flags'].append('engine-disagreement')
            tri = vr.get('triage', {})
            rec['triage'] = {p: tri[p]['class'] for p in props if p in tri}
            vac_p = [p for p in props if taut.get(p, {}).get('tautology') or vac.get(p, {}).get('vacuous') == 'PROVEN']
            unw = [p for p in props if p in vac and not vac[p].get('reached') and p not in vac_p]
            if vac_p:
                rec['flags'].append('vacuous')
                rec['vacuous'] = vac_p
            if unw:
                rec['flags'].append('unwitnessed')
            if rid in conflict_reqs:
                rec['flags'].append('conflict')
                rec['conflicts'] = conflict_reqs[rid]
            if mut.get('mutants') is not None:
                k = sum(kills.get(p, 0) for p in props)
                rec['mutants_killed'] = k
                if k == 0:
                    rec['flags'].append('non-discriminating')
            if any(lint_by_item.get(p) for p in props):
                rec['flags'].append('lint')
            prel = [x['relation'] for x in rec['peers'].values()]
            if prel:
                if all(x == 'EQUIVALENT' for x in prel):
                    rec['validation'] = 'AGREED'
                elif any(x in ('A-STRONGER', 'A-WEAKER', 'INCOMPARABLE') for x in prel):
                    rec['validation'] = 'DISPUTED'
                    rec['flags'].append('disputed')
                elif any(x == 'ONLY-A' for x in prel):
                    rec['validation'] = 'UNCORROBORATED'
                else:
                    rec['validation'] = 'UNKNOWN'
            else:
                rec['validation'] = 'NO-PEER'
            if not env_ok:
                rec['flags'].append('env-unsound')
            if status == 'PROVED':
                if 'vacuous' in rec['flags']:
                    level = 'PROVED-VACUOUS'
                elif 'env-unsound' in rec['flags']:
                    level = 'PROVED-ENV-UNSOUND'
                elif 'conflict' in rec['flags']:
                    level = 'PROVED-CONFLICTED'
                elif rec['validation'] == 'DISPUTED':
                    level = 'PROVED-DISPUTED'
                elif rec['validation'] == 'AGREED':
                    level = 'ASSURED'
                else:
                    level = 'PROVED-UNVALIDATED'
            else:
                level = status
            rec['status'] = status
            rec['level'] = level
        elif asm:
            rec['status'] = rec['level'] = 'ASSUMED'
            if not env_ok:
                rec['flags'].append('env-unsound')
        elif dcs:
            rec['status'] = rec['level'] = 'DONT-CARE'
        elif rid in unf:
            u = unf[rid]
            rec['status'] = rec['level'] = 'COVERED-INDIRECTLY' if u.get('covered_by') else 'UNFORMALIZED'
            rec['reason'] = u['reason']
            if u.get('covered_by'):
                rec['covered_by'] = u['covered_by']
                cst = [ver.get(p, {}).get('status') for p in u['covered_by']]
                if cst and all(x == 'PROVED' for x in cst):
                    rec['level'] = 'COVERED-PROVED'
                elif 'FAILED' in cst:
                    rec['level'] = 'COVERED-FAILED'
        else:
            rec['status'] = rec['level'] = 'MISSING'
        if r.get('ambiguity'):
            rec['flags'].append('ambiguous-text')
        out[rid] = rec
    return {'requirements': out, 'queue': review_queue(ev, s, v, out),
            'summary': summarize(out), 'env_ok': env_ok, 'unjustified_assumptions': unjust}


def summarize(reqs: dict) -> dict:
    out: dict[str, int] = {}
    for r in reqs.values():
        out[r['level']] = out.get(r['level'], 0) + 1
    return dict(sorted(out.items()))


SEV = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}


def review_queue(ev: dict, s: str, v: str, reqs: dict) -> list[dict]:
    """The prioritized list of decisions a human must make.  Everything not in
    the queue is mechanically discharged."""
    sr = ev['sets'][s]
    vr = sr['rtl'].get(v, {})
    q = []
    for rid, r in reqs.items():
        if r['status'] == 'FAILED':
            cls = sorted(set(r.get('triage', {}).values())) or ['UNTRIAGED']
            q.append({'severity': 'critical', 'kind': 'failure', 'req': rid, 'classes': cls,
                      'decision': 'RTL deviates from a spec-conforming behaviour: fix the RTL or confirm the requirement'
                      if cls == ['RTL-DEVIATION'] else 'Counterexample needs triage: RTL bug, wrong formalization or spec conflict?'})
        if 'engine-disagreement' in r['flags']:
            q.append({'severity': 'critical', 'kind': 'engine-disagreement', 'req': rid,
                      'decision': 'Proof engines disagree: tool soundness issue, do not trust either result'})
        if 'vacuous' in r['flags']:
            q.append({'severity': 'high', 'kind': 'vacuity', 'req': rid, 'items': r.get('vacuous'),
                      'decision': 'The proof is vacuous (the property can never be triggered or constrains nothing): fix the formalization or the assumptions'})
        if r.get('validation') == 'DISPUTED':
            q.append({'severity': 'high', 'kind': 'dispute', 'req': rid,
                      'peers': {k: x['relation'] for k, x in r['peers'].items()},
                      'decision': 'Independent formalizations disagree; adjudicate using the distinguishing trace'})
        if r['status'] in ('MISSING',):
            q.append({'severity': 'high', 'kind': 'missing', 'req': rid,
                      'decision': 'Requirement was dropped by the formalizer without a reason'})
        if r['status'] == 'UNFORMALIZED':
            q.append({'severity': 'low', 'kind': 'unformalized', 'req': rid, 'reason': r.get('reason'),
                      'decision': 'Confirm that leaving this requirement unformalized is acceptable'})
        if 'ambiguous-text' in r['flags']:
            q.append({'severity': 'medium', 'kind': 'ambiguity', 'req': rid,
                      'readings': ev['requirements'][rid]['ambiguity'],
                      'decision': 'The text admits several readings; confirm the chosen one'})
    for c in sr.get('consistency', {}).get('conflicts', []):
        q.append({'severity': 'critical', 'kind': 'conflict', 'reqs': c['reqs'], 'mus': c['mus'],
                  'situations': c['situations'][:6],
                  'decision': 'These requirements cannot all hold in the listed situations: amend the spec'})
    rc = vr.get('receptive', {})
    if rc.get('receptive') is False:
        q.append({'severity': 'critical', 'kind': 'non-receptive', 'step': rc.get('blocking_step'),
                  'decision': 'An environment assumption constrains the design itself (no legal input exists in a '
                              'reachable state): proofs that rely on it may hide bugs'})
    for o, d in sr.get('determinacy', {}).items():
        if d.get('determined') is False:
            q.append({'severity': 'medium', 'kind': 'underspecified', 'signal': o,
                      'decision': f'The spec allows two different values of {o} after identical histories: '
                                  'declare a don\'t-care or add a requirement'})
    mut = sr.get('mutation', {})
    surv = [m for m in mut.get('mutants', []) if m['status'] == 'SURVIVED']
    if surv:
        lines = sorted({ln for m in surv for ln in m['src_lines']})
        q.append({'severity': 'medium', 'kind': 'unconstrained-logic', 'mutants': [m['id'] for m in surv],
                  'rtl_lines': lines,
                  'decision': 'Observable RTL changes that no formalized requirement detects: missing requirement, '
                              'weak formalization or intentionally free behaviour?'})
    for l in sr.get('lint', []):
        if l['severity'] in ('error', 'warning') and l['kind'] != 'missing':
            q.append({'severity': 'high' if l['severity'] == 'error' else 'medium', 'kind': f'lint:{l["kind"]}',
                      'item': l.get('item'), 'decision': l['msg']})
    q.sort(key=lambda x: SEV[x['severity']])
    return q


def save(ev: dict, path: str):
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    with open(path, 'w') as f:
        json.dump(ev, f, indent=1, default=lambda o: sorted(o) if isinstance(o, set) else str(o))
