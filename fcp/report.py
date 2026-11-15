"""Requirement-level evidence report (Markdown and self-contained HTML)."""
from __future__ import annotations

import html
import os

from .wave import wave

LEVEL_ORDER = ['FAILED', 'PROVED-VACUOUS', 'PROVED-ENV-UNSOUND', 'PROVED-CONFLICTED', 'PROVED-DISPUTED',
               'MISSING', 'UNKNOWN', 'BOUNDED', 'PROVED-UNVALIDATED', 'ASSURED', 'COVERED-FAILED',
               'COVERED-PROVED', 'COVERED-INDIRECTLY', 'ASSUMED', 'DONT-CARE', 'UNFORMALIZED']
LEVEL_DESC = {
    'ASSURED': 'proved (unbounded), non-vacuous, sound environment, independently cross-validated formalization',
    'PROVED-UNVALIDATED': 'proved, but no independent formalization corroborates the interpretation',
    'PROVED-DISPUTED': 'proved, but an independent formalization means something different',
    'PROVED-CONFLICTED': 'proved, but the requirement conflicts with others',
    'PROVED-VACUOUS': 'proof is vacuous: the property can never trigger or constrains nothing',
    'PROVED-ENV-UNSOUND': 'proved under an environment assumption that constrains the design itself',
    'FAILED': 'counterexample found (replayed in simulation, triaged)',
    'BOUNDED': 'no counterexample up to the BMC depth; unbounded proof inconclusive',
    'UNKNOWN': 'engines inconclusive',
    'UNFORMALIZED': 'not formalized (reason recorded)',
    'COVERED-PROVED': 'realized indirectly by other proved properties',
    'COVERED-FAILED': 'realized indirectly by properties that fail',
    'COVERED-INDIRECTLY': 'realized indirectly by other properties',
    'ASSUMED': 'environment obligation, used as an assumption',
    'DONT-CARE': 'declared intentional under-specification',
    'MISSING': 'dropped without a recorded reason',
}


class Doc:
    def __init__(self):
        self.blocks = []

    def h(self, level, text, anchor=None):
        self.blocks.append(('h', level, text, anchor))

    def p(self, text):
        self.blocks.append(('p', text))

    def table(self, head, rows):
        self.blocks.append(('table', head, rows))

    def pre(self, text, title=None):
        self.blocks.append(('pre', text, title))

    def ul(self, items):
        self.blocks.append(('ul', items))

    def md(self) -> str:
        out = []
        for b in self.blocks:
            if b[0] == 'h':
                out.append('#' * b[1] + ' ' + b[2])
            elif b[0] == 'p':
                out.append(b[1])
            elif b[0] == 'table':
                out.append('| ' + ' | '.join(b[1]) + ' |')
                out.append('|' + '---|' * len(b[1]))
                for r in b[2]:
                    out.append('| ' + ' | '.join(str(c).replace('|', '\\|').replace('\n', ' ') for c in r) + ' |')
            elif b[0] == 'pre':
                if b[2]:
                    out.append(f'*{b[2]}*')
                out.append('```\n' + b[1] + '\n```')
            elif b[0] == 'ul':
                out += [f'- {x}' for x in b[1]]
            out.append('')
        return '\n'.join(out)

    def html(self, title: str) -> str:
        def inl(t):
            t = html.escape(str(t))
            # `code` spans
            parts = t.split('`')
            return ''.join(f'<code>{p}</code>' if i % 2 else p for i, p in enumerate(parts))
        out = [f'<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
               f'<title>{html.escape(title)}</title><style>{CSS}</style></head><body><main>']
        for b in self.blocks:
            if b[0] == 'h':
                aid = f' id="{html.escape(b[3])}"' if b[3] else ''
                out.append(f'<h{b[1]}{aid}>{inl(b[2])}</h{b[1]}>')
            elif b[0] == 'p':
                out.append(f'<p>{inl(b[1])}</p>')
            elif b[0] == 'table':
                out.append('<div class="tw"><table><thead><tr>' + ''.join(f'<th>{inl(c)}</th>' for c in b[1]) +
                           '</tr></thead><tbody>')
                for r in b[2]:
                    out.append('<tr>' + ''.join(f'<td>{_cell(c)}</td>' for c in r) + '</tr>')
                out.append('</tbody></table></div>')
            elif b[0] == 'pre':
                if b[2]:
                    out.append(f'<div class="cap">{inl(b[2])}</div>')
                out.append(f'<pre>{html.escape(b[1])}</pre>')
            elif b[0] == 'ul':
                out.append('<ul>' + ''.join(f'<li>{inl(x)}</li>' for x in b[1]) + '</ul>')
        out.append('</main></body></html>')
        return '\n'.join(out)


def _cell(c):
    s = str(c)
    for lvl in LEVEL_ORDER:
        if s == lvl:
            return f'<span class="lv lv-{lvl.lower()}">{html.escape(s)}</span>'
    t = html.escape(s)
    parts = t.split('`')
    return ''.join(f'<code>{p}</code>' if i % 2 else p for i, p in enumerate(parts))


CSS = """
:root{--bg:#fbfbf9;--fg:#1d1f21;--mut:#5f6368;--line:#dadce0;--code:#f1f3f4;--ok:#137333;--warn:#b06000;--bad:#c5221f;--info:#1a73e8}
@media (prefers-color-scheme: dark){:root{--bg:#17181a;--fg:#e8eaed;--mut:#9aa0a6;--line:#3c4043;--code:#25272a;--ok:#81c995;--warn:#fdd663;--bad:#f28b82;--info:#8ab4f8}}
body{background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,-apple-system,Segoe UI,sans-serif;margin:0}
main{max-width:1100px;margin:0 auto;padding:24px 16px 80px}
h1{font-size:26px;margin:.2em 0}h2{font-size:20px;margin-top:2em;border-bottom:1px solid var(--line);padding-bottom:4px}h3{font-size:16px;margin-top:1.6em}
code{background:var(--code);padding:1px 4px;border-radius:3px;font-size:13px}
pre{background:var(--code);padding:10px;border-radius:6px;overflow-x:auto;font-size:12.5px;line-height:1.35}
.cap{color:var(--mut);font-size:13px;margin-top:10px}
.tw{overflow-x:auto}table{border-collapse:collapse;width:100%;font-size:13.5px}
th,td{border-bottom:1px solid var(--line);padding:5px 8px;text-align:left;vertical-align:top}th{color:var(--mut);font-weight:600}
.lv{font-weight:600;font-size:12px;padding:1px 6px;border-radius:10px;border:1px solid currentColor;white-space:nowrap}
.lv-assured,.lv-covered-proved,.lv-dont-care,.lv-assumed{color:var(--ok)}
.lv-proved-unvalidated,.lv-bounded,.lv-unformalized,.lv-covered-indirectly{color:var(--info)}
.lv-proved-disputed,.lv-proved-conflicted,.lv-unknown,.lv-missing{color:var(--warn)}
.lv-failed,.lv-proved-vacuous,.lv-proved-env-unsound,.lv-covered-failed{color:var(--bad)}
"""


def _sigs(ev):
    return [s['name'] for s in ev['interface']['signals'] if s['name'] != 'clk']


def render(ev: dict, s: str, v: str) -> Doc:
    d = Doc()
    A = ev['assessment'][s][v]
    sr = ev['sets'][s]
    vr = sr['rtl'].get(v, {})
    reqs = ev['requirements']
    d.h(1, f'FCP evidence report: {ev["design"]}')
    d.p(f'Formalization set `{s}` ({sr["origin"].get("kind", "?")}: {sr["origin"].get("id", "?")}), '
        f'RTL variant `{v}`, generated {ev["created"]}.')
    total = len(A['requirements'])
    summ = A['summary']
    d.h(2, 'Summary')
    d.table(['Level', 'Requirements', 'Meaning'],
            [[k, summ[k], LEVEL_DESC.get(k, '')] for k in LEVEL_ORDER if k in summ])
    mut = sr.get('mutation', {})
    props = [i for i, it in sr.get('items', {}).items() if it['role'] == 'property']
    proved = sum(1 for p in props if vr.get('verify', {}).get(p, {}).get('status') == 'PROVED')
    facts = [f'{total} requirements; {len(props)} properties, {proved} proved unboundedly.',
             f'Review queue: {len(A["queue"])} decisions for a human (everything else is mechanically discharged).']
    if mut:
        facts.append(f'Mutation assurance coverage: {mut["killed"]}/{mut["observable"]} observable mutants killed '
                     f'({100 * (mut["coverage"] or 0):.0f}%), {mut["n"] - mut["observable"]} equivalent mutants excluded.')
    rc = vr.get('receptive')
    if rc:
        facts.append('Environment assumptions: ' + ('receptive (no reachable state blocks the environment)'
                                                    if rc.get('receptive') else
                                                    f'NOT receptive: blocked at step {rc.get("blocking_step")}'))
    cons = sr.get('consistency', {})
    if cons:
        facts.append(f'Spec consistency: {cons["situations"]} situations checked, '
                     f'{len(cons.get("conflicts", []))} minimal conflicting sets.')
    d.ul(facts)

    d.h(2, 'Review queue')
    if not A['queue']:
        d.p('Nothing requires human attention.')
    else:
        rows = []
        for q in A['queue']:
            what = q.get('req') or ', '.join(q.get('reqs', [])) or q.get('signal') or q.get('item') or \
                (f'lines {q["rtl_lines"]}' if 'rtl_lines' in q else '')
            rows.append([q['severity'], q['kind'], what, q['decision']])
        d.table(['Severity', 'Kind', 'Subject', 'Decision needed'], rows)

    d.h(2, 'Requirements')
    rows = []
    for rid, r in A['requirements'].items():
        rq = reqs[rid]
        rows.append([f'[{rid}](#{rid})', rq['kind'], _short(rq['quote'], 70), r['level'],
                     ', '.join(r['flags']), ', '.join(r['properties'] + r['assumptions'] + r['dont_cares'])])
    d.table(['Req', 'Kind', 'Source', 'Level', 'Flags', 'Formal items'], rows)

    d.h(2, 'Requirement details')
    items = sr.get('items', {})
    for rid, r in A['requirements'].items():
        rq = reqs[rid]
        d.h(3, f'{rid}: {r["level"]}', anchor=rid)
        ln = rq['lines']
        d.p(f'Source `{rq["doc"]}` line{"s" if len(ln) > 1 else ""} {"-".join(map(str, ln))}: "{rq["quote"]}"')
        d.p(f'Atomic requirement: {rq["text"]}')
        for a in rq.get('ambiguity') or []:
            d.p(f'Ambiguity in "{a["phrase"]}": ' + ' / '.join(f'({i + 1}) {x}' for i, x in enumerate(a['readings'])))
        if r.get('reason'):
            d.p(f'Not formalized: {r["reason"]}')
        for pid in r['properties'] + r['assumptions'] + r['dont_cares']:
            it = items[pid]
            vv = vr.get('verify', {}).get(pid, {})
            d.p(f'`{pid}` ({it["role"]}, pattern `{it["pattern"]}`): {it["english"]}')
            d.pre(it['formula'], 'formula')
            if it['role'] == 'property' and vv:
                d.p(f'Proof: PDR {vv.get("pdr")}, BMC {vv.get("bmc")} -> **{vv.get("status")}** '
                    f'({vv.get("seconds")}s; tasks {", ".join(k[:10] for k in vv.get("keys", []))})')
                if vv.get('status') == 'FAILED' and vv.get('trace'):
                    tri = vr.get('triage', {}).get(pid, {})
                    exp = {(x['step'], x['signal']): x['spec'] for x in tri.get('diff', [])}
                    sigs = _sigs(ev) + [f'mon_ok_{pid.replace("-", "_")}']
                    d.pre(wave(vv['trace'], [x for x in sigs if x in vv['trace'][-1]], mark=vv.get('fail_step'),
                               expect=exp), 'counterexample (actual>spec-required where the triage found a deviation)')
                    rp = vv.get('replay', {})
                    d.p(f'Independent simulation replay: {rp.get("status")}. Triage: {tri.get("class", "n/a")}'
                        + (f'; conflicting requirements {tri.get("core")}' if tri.get('core') else '')
                        + (f'; first divergence at cycle {tri.get("first_divergence")}' if tri.get('first_divergence') is not None else ''))
            vq = vr.get('vacuity', {}).get('properties', {}).get(pid)
            if vq and vq.get('witness') and it['role'] == 'property':
                sigs = [x for x in _sigs(ev) if x in vq['witness'][-1]]
                d.pre(wave(vq['witness'], sigs), 'witness: the trigger fires on the RTL (non-vacuity)')
            elif vq and not vq.get('reached'):
                d.p(f'Trigger never reached on the RTL (vacuity proof: {vq.get("vacuous")}).')
        for peer, x in r.get('peers', {}).items():
            d.p(f'Independent formalization `{peer}`: **{x["relation"]}**')
            for key, cap in (('witness', f'behaviour allowed by `{s}` but rejected by `{peer}`'),
                             ('witness_rev', f'behaviour allowed by `{peer}` but rejected by `{s}`')):
                if x.get(key):
                    sigs = [y for y in _sigs(ev) if y in x[key][-1]]
                    d.pre(wave(x[key], sigs, mark=len(x[key]) - 1), cap)

    if cons.get('conflicts'):
        d.h(2, 'Specification conflicts')
        for c in cons['conflicts']:
            d.p(f'Minimal conflicting set {c["mus"]} (requirements {c["reqs"]}) in situations: ' +
                ', '.join(f'`{x}`' for x in c['situations'][:8]))
    det = sr.get('determinacy', {})
    if det:
        d.h(2, 'Determinacy (is every output pinned down by the spec?)')
        d.table(['Output', 'Determined', 'Status'], [[o, x['determined'], x['status']] for o, x in det.items()])
        for o, x in det.items():
            if x.get('witness'):
                sigs = [y for y in _sigs(ev) + [o + '__b'] if y in x['witness'][-1]]
                d.pre(wave(x['witness'], sigs, mark=len(x['witness']) - 1),
                      f'{o} and {o}__b: two spec-conforming behaviours with identical history that differ')
    if rc and rc.get('trace'):
        d.h(2, 'Environment receptiveness')
        d.pre(wave(rc['trace'], [y for y in _sigs(ev) if y in rc['trace'][-1]], mark=len(rc['trace']) - 1),
              f'after this input history no (non-reset) input satisfies the assumptions at cycle {rc["blocking_step"]}')
    if mut:
        d.h(2, 'Mutation assurance')
        d.p(f'{mut["n"]} mutants: {mut["observable"]} observable, {mut["killed"]} killed, '
            f'{sum(1 for m in mut["mutants"] if m["status"] == "SURVIVED")} survived, '
            f'{sum(1 for m in mut["mutants"] if m["status"] == "EQUIVALENT")} equivalent.')
        rows = [[ln, x['killed'], x['survived'], x['equivalent'], ', '.join(x['reqs'])]
                for ln, x in sorted(mut['by_line'].items(), key=lambda kv: int(kv[0]))]
        d.table(['RTL line', 'killed', 'survived', 'equivalent', 'requirements that constrain it'], rows)
        for m in mut['mutants']:
            if m['status'] == 'SURVIVED' and m.get('witness'):
                sigs = [y for y in _sigs(ev) + [o + '__m' for o in [x['name'] for x in ev['interface']['signals']]]
                        if y in m['witness'][-1]]
                d.pre(wave(m['witness'], sigs, mark=len(m['witness']) - 1),
                      f'surviving mutant {m["id"]} ({m["mode"]} at lines {m["src_lines"]}): x__m is the mutant')
    d.h(2, 'Reproducibility')
    d.p('Every proof task is content-addressed; its directory in the cache contains the exact sby configuration, '
        'the generated monitor and harness, and copies of the RTL. Re-run any task with `sby -f task.sby`.')
    d.table(['Artifact', 'sha256'], [[k, v_[:16]] for k, v_ in ev['fingerprint'].items()])
    d.table(['Tool', 'Version'], [[k, v_] for k, v_ in ev['tools'].items()])
    return d


def _short(s, n):
    s = ' '.join(s.split())
    return s if len(s) <= n else s[:n - 1] + '...'


def write(ev: dict, s: str, v: str, outdir: str) -> tuple[str, str]:
    os.makedirs(outdir, exist_ok=True)
    d = render(ev, s, v)
    md = os.path.join(outdir, f'report_{s}_{v}.md')
    ht = os.path.join(outdir, f'report_{s}_{v}.html')
    with open(md, 'w') as f:
        f.write(d.md())
    with open(ht, 'w') as f:
        f.write(d.html(f'FCP report {ev["design"]} {s}/{v}'))
    return md, ht
