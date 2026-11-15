"""Aggregate experiments/results/<design>.json into summary tables (Markdown + JSON)."""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'results')


def load(designs):
    out = {}
    for d in designs:
        p = os.path.join(OUT, f'{d}.json')
        if os.path.exists(p):
            with open(p) as f:
                out[d] = json.load(f)
    return out


def pct(a, b):
    return f'{100 * a / b:.0f}%' if b else 'n/a'


def main(designs):
    R = load(designs)
    lines = ['# FCP study: results', '']
    agg = {'violations': 0, 'fa_naive': 0, 'fa_fcp': 0, 'faults': 0, 'flagged': 0, 'hide_naive': 0,
           'hide_fcp': 0, 'equiv': 0, 'graded': 0}

    lines += ['## Formalization sets', '',
              '| Design | Set | Props | Assumptions | Proved on ref | Failed on ref | Injected bugs detected (other variants) | Mutation coverage | Receptive | Conflicts | Lint |',
              '|---|---|---|---|---|---|---|---|---|---|---|']
    for d, r in R.items():
        for s, x in r['sets'].items():
            if 'ill_formed' in x:
                lines.append(f'| {d} | {s} | ill-formed: {x["ill_formed"][:60]} |||||||||')
                continue
            oth = ', '.join(f'{v}: {"FAIL" if o["detected"] else "pass"}' for v, o in x.get('other_variants', {}).items())
            lines.append(f'| {d} | {s} | {x["n_properties"]} | {x["n_assumptions"]} | {x["proved_on_ref"]} | '
                         f'{len(x["failed_on_ref"])} | {x["injected_detected"]}/{x["injected_total"]} ({oth}) | '
                         f'{x["mutants_killed"]}/{x["mutants_observable"]} ({pct(x["mutants_killed"], x["mutants_observable"])}) | '
                         f'{x["receptive"]} | {len(x["conflicts"])} | {len(x["lint"])} |')
    lines += ['', '## Formalization accuracy of the agents (semantic relation to gold, per requirement)', '',
              'Properties are compared under the gold environment; the agent\'s assumption set is compared with gold\'s separately.', '',
              '| Design | Set | Equivalent | Stronger | Weaker | Incomparable | Missing | Unknown | Equivalent rate | Assumptions vs gold |',
              '|---|---|---|---|---|---|---|---|---|---|']
    for d, r in R.items():
        for s, x in r['sets'].items():
            a = x.get('accuracy')
            if not a:
                continue
            c = a['counts']
            graded = sum(v for k, v in c.items() if k != 'EXTRA')
            agg['equiv'] += c.get('EQUIVALENT', 0)
            agg['graded'] += graded
            lines.append(f'| {d} | {s} | {c.get("EQUIVALENT", 0)} | {c.get("STRONGER", 0)} | {c.get("WEAKER", 0)} | '
                         f'{c.get("INCOMPARABLE", 0)} | {c.get("MISSING", 0)} | {c.get("UNKNOWN", 0)} | '
                         f'{pct(c.get("EQUIVALENT", 0), graded)} | {a.get("assumptions_vs_gold", "?")} |')
    lines += ['', '## False assurance on real agent formalizations', '',
              'A *violation* is a (buggy RTL variant, requirement) pair whose gold property fails. '
              'False assurance = the flow claims the requirement is assured although it is violated. '
              'Naive: all of the set\'s properties for the requirement proved. FCP: level ASSURED '
              '(proved, non-vacuous, receptive environment, equivalent to the independent peer agent set).', '',
              '| Design | Set | Violations | Naive false assurance | FCP false assurance | Buggy designs declared verified (naive / FCP) |',
              '|---|---|---|---|---|---|']
    for d, r in R.items():
        for s, x in r['sets'].items():
            if s == 'gold' or 'ill_formed' in x:
                continue
            v = x['violations']
            if s in r.get('agent_sets', []):
                agg['violations'] += v
                agg['fa_naive'] += x['false_assurance_naive']
                agg['fa_fcp'] += x['false_assurance_fcp']
            lines.append(f'| {d} | {s} | {v} | {x["false_assurance_naive"]} ({pct(x["false_assurance_naive"], v)}) | '
                         f'{x["false_assurance_fcp"]} ({pct(x["false_assurance_fcp"], v)}) | '
                         f'{x["design_false_assurance_naive"]} / {x["design_false_assurance_fcp"]} |')
    lines += ['', '## Injected formalization faults (one fault per run, into gold)', '',
              '| Design | Injected | Semantic faults | Flagged by FCP | Hide a real bug (naive) | Hide a real bug (FCP) |',
              '|---|---|---|---|---|---|']
    ops = {}
    for d, r in R.items():
        f = r['faults']
        agg['faults'] += f['semantic']
        agg['flagged'] += f['flagged']
        agg['hide_naive'] += f['hides_bug_naive']
        agg['hide_fcp'] += f['hides_bug_fcp']
        lines.append(f'| {d} | {f["injected"]} | {f["semantic"]} | {f["flagged"]} ({pct(f["flagged"], f["semantic"])}) | '
                     f'{f["hides_bug_naive"]} | {f["hides_bug_fcp"]} |')
        for o, x in f['by_operator'].items():
            y = ops.setdefault(o, {'n': 0, 'flagged': 0, 'hn': 0, 'hf': 0, 'by': {}})
            y['n'] += x['n']
            y['flagged'] += x['flagged']
            y['hn'] += x['hides_bug_naive']
            y['hf'] += x['hides_bug_fcp']
            for k, c in x['flagged_by'].items():
                y['by'][k] = y['by'].get(k, 0) + c
    lines += ['', '| Fault operator | Semantic faults | Flagged | Hide bug (naive) | Hide bug (FCP) | Flagged by |', '|---|---|---|---|---|---|']
    for o, y in sorted(ops.items()):
        lines.append(f'| {o} | {y["n"]} | {y["flagged"]} | {y["hn"]} | {y["hf"]} | '
                     + ', '.join(f'{k} {v}' for k, v in sorted(y['by'].items())) + ' |')
    lines += ['', '## Disagreement between independent agents as an error detector', '',
              '| Design | Disagree & wrong | Disagree & both right | Agree & wrong | Agree & right |', '|---|---|---|---|---|']
    for d, r in R.items():
        x = r.get('disagreement_as_error_detector')
        if x:
            lines.append(f'| {d} | {x["tp"]} | {x["fp"]} | {x["fn"]} | {x["tn"]} |')
    lines += ['', '## Assurance yield on the reference design and simulated adjudication', '',
              'ASSURED: requirements FCP discharges without human input. Adjudication simulates a human who resolves '
              'every PROVED-DISPUTED requirement against the intended meaning (gold): the set\'s formalization is '
              'confirmed if it is equivalent to gold, otherwise it must be repaired.', '',
              '| Design | Set | Formalized reqs | ASSURED | Disputed | Disputed, confirmed by adjudication | Disputed, needs repair | Failed on ref |',
              '|---|---|---|---|---|---|---|---|']
    for d, r in R.items():
        for s, x in r['sets'].items():
            if 'ill_formed' in x or s == 'gold' or 'ref_levels' not in x:
                continue
            lv = x['ref_levels']
            acc = (x.get('accuracy') or {}).get('per_req', {})
            disp = [q for q, l in lv.items() if l == 'PROVED-DISPUTED']
            conf = [q for q in disp if acc.get(q) == 'EQUIVALENT']
            lines.append(f'| {d} | {s} | {len(lv)} | {sum(1 for l in lv.values() if l == "ASSURED")} | {len(disp)} | '
                         f'{len(conf)} | {len(disp) - len(conf)} | {sum(1 for l in lv.values() if l == "FAILED")} |')
    lines += ['', '## Review queue and runtime', '', '| Design | Set | Queue on ref | Wall time (s) |', '|---|---|---|---|']
    for d, r in R.items():
        for s, x in r['sets'].items():
            if 'ill_formed' in x:
                continue
            lines.append(f'| {d} | {s} | {x["per_variant"]["ref"]["queue"]} | {r["wall_seconds"] if s == "gold" else ""} |')
    lines += ['', '## Totals', '',
              f'- Agent formalizations equivalent to gold: {agg["equiv"]}/{agg["graded"]} ({pct(agg["equiv"], agg["graded"])})',
              f'- False assurance on agent sets: naive {agg["fa_naive"]}/{agg["violations"]} ({pct(agg["fa_naive"], agg["violations"])}), '
              f'FCP {agg["fa_fcp"]}/{agg["violations"]} ({pct(agg["fa_fcp"], agg["violations"])})',
              f'- Injected semantic formalization faults flagged by FCP: {agg["flagged"]}/{agg["faults"]} ({pct(agg["flagged"], agg["faults"])})',
              f'- Injected faults that hide a real RTL bug: naive {agg["hide_naive"]}, FCP {agg["hide_fcp"]}']
    txt = '\n'.join(lines) + '\n'
    with open(os.path.join(OUT, 'summary.md'), 'w') as f:
        f.write(txt)
    with open(os.path.join(OUT, 'summary.json'), 'w') as f:
        json.dump({'totals': agg, 'by_operator': ops}, f, indent=1)
    print(txt)


if __name__ == '__main__':
    main(sys.argv[1:] or ['fifo', 'arbiter', 'bridge', 'hub'])
