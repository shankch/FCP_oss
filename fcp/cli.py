"""fcp command-line interface.

  fcp check   <bundle> --set gold [--set agent_a ...] --rtl ref [--rtl B1 ...]
  fcp lint    <bundle>                       schema, provenance, compile and static checks only
  fcp explain <bundle> --set gold            English rendering of every formal item
  fcp monitor <bundle> --set gold            print the generated Verilog monitor
  fcp anchor  <bundle> draft.yaml            compute source spans for agent-provided quotes
  fcp code    <bundle> impl.py --set gold    run an AI-written function on the scope and check it
  fcp review  --request r.md --code a.py --out dir   the whole protocol on one AI answer (agents via claude -p);
                                                   --code dir --entry pkg.mod for a package;
                                                   --signature stub.py instead of --code: the request alone
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import yaml

from . import pipeline, report
from .analyses import Session
from .anchor import anchor
from .ir import load_bundle, load_fset
from .lang import FcpError


def cmd_check(a):
    extra = dict(x.split('=', 1) for x in a.extra_set) if a.extra_set else None
    sets = a.set + (list(extra) if extra else [])
    an = pipeline.ALL if not a.only else tuple(a.only.split(','))
    if a.no_mutation:
        an = tuple(x for x in an if x != 'mutation')
    b = load_bundle(a.bundle)
    if not b.rtl:
        # a function or object design: the analyses of the request alone; the
        # code is checked by `fcp code`
        if a.rtl != ['ref']:
            print(f'{a.bundle} has no RTL variants; `fcp code {a.bundle} impl.py` checks an implementation')
        if not a.only:
            an = ('lint', 'tautology', 'consistency', 'determinacy')
        ev = pipeline.run(a.bundle, sets, [], cache=a.cache, jobs=a.jobs, analyses=an, extra_sets=extra)
        out = a.out or os.path.join(a.bundle, '.fcp', 'report')
        pipeline.save(ev, os.path.join(out, 'evidence.json'))
        for s in sets:
            rec = ev['sets'].get(s, {})
            if s not in ev['assessment']:
                print(f'[{s}] ILL-FORMED: {rec.get("error")}')
                continue
            cons = rec.get('consistency', {})
            det = rec.get('determinacy', {})
            taut = [k for k, v in rec.get('tautology', {}).items() if v.get('tautology')]
            print(f'[{s}] consistency: {"consistent" if cons.get("consistent") else "CONFLICT"}' +
                  ''.join(f'\n    conflict: {" + ".join(c.get("reqs", []))}' for c in cons.get('conflicts', [])))
            never = [f'{x} (its cover is impossible)' for x in cons.get('impossible_scenarios', [])] + \
                [f'{x} (the reading forbids it)' for x in cons.get('forbidden_scenarios', [])]
            print(f'    scenarios that can never happen: {", ".join(never) or "none"}')
            opened = [k for k, x in det.items() if x.get('determined') is False]
            print(f'    open outputs (determinacy): {", ".join(opened) or "none"}')
            print(f'    tautologies: {", ".join(taut) or "none"}')
            if 'function' in b.raw_design:
                from . import software as SW
                S = Session(a.bundle, sets=[s])
                from . import effects as FX
                fn_ = SW.function(S)
                ifc = FX.interface(S, fn_)
                c = FX.conflicts(S, s, fn_, ifc) if ifc else SW.conflicts(S, s, fn_)
                what = ('scripts of answers' if ifc else
                        'call sequences' if b.raw_design['function'].get('class') else 'boundary calls')
                print(f'    conflicts on {what} ({c["checked"]} checked): ' +
                      (', '.join(' + '.join(x['reqs']) for x in c['conflicts']) or 'none'))
                for x in c['conflicts']:
                    print(f'      {" ; ".join(x["stimulus"])}')
        print(f'total {ev["runtime"]["total"]}s; spec-only analyses; `fcp code` runs an implementation')
        return 0
    ev = pipeline.run(a.bundle, sets, a.rtl, cache=a.cache, jobs=a.jobs, analyses=an, mutation_n=a.mutants,
                      extra_sets=extra)
    out = a.out or os.path.join(a.bundle, '.fcp', 'report')
    pipeline.save(ev, os.path.join(out, 'evidence.json'))
    for s in sets:
        if s not in ev['assessment']:
            print(f'[{s}] ILL-FORMED: {ev["sets"][s].get("error")}')
            continue
        for v in a.rtl:
            md, ht = report.write(ev, s, v, out)
            A = ev['assessment'][s][v]
            print(f'[{s} / {v}] {A["summary"]}  review queue: {len(A["queue"])}  -> {ht}')
    print(f'total {ev["runtime"]["total"]}s; engine tasks run {ev["engine_stats"]["run"]}, '
          f'cached {ev["engine_stats"]["cached"]}')


def cmd_lint(a):
    b = load_bundle(a.bundle)
    bad = False
    for i in b.issues:
        print(f'{i["severity"]:8s} {i["kind"]:22s} {i.get("req") or i.get("item", "")}: {i["msg"]}')
        bad |= i['severity'] == 'error'
    S = Session(a.bundle)
    for s in b.fsets:
        try:
            S.mon(s)
        except FcpError as e:
            print(f'error    ill-formed             set {s}: {e}')
            bad = True
            continue
        for l in pipeline.lint(S, s):
            print(f'{l["severity"]:8s} {l["kind"]:22s} {s}:{l.get("item") or l.get("req")}: {l["msg"]}')
            bad |= l['severity'] == 'error'
    print('lint:', 'errors found' if bad else 'clean')
    return 1 if bad else 0


def cmd_explain(a):
    S = Session(a.bundle)
    for s in a.set:
        try:
            m = S.mon(s)
        except FcpError as e:
            print(f'== {s}: ill-formed: {e}')
            return 1
        print(f'== {s}')
        defs = S.b.fsets[s].get('defs') or {}
        if defs:
            print('defs:')
            for name, body in defs.items():
                print(f'  {name} = {body}')
        for it in m.items.values():
            print(f'{it.id:14s} [{it.role}] {it.req or "-"}\n    {it.english}\n    {it.formula}')


def cmd_monitor(a):
    S = Session(a.bundle)
    try:
        print(S.mon(a.set[0]).text)
    except FcpError as e:
        print(f'ill-formed: {e}')
        return 1


def cmd_code(a):
    """One implementation of a function design against every given reading:
    a verdict per requirement, with the simplest failing call, replayed."""
    from . import effects as FX
    from . import software as SW
    S = Session(a.bundle, sets=a.set)
    fn = SW.function(S)
    ifc = FX.interface(S, fn)
    if ifc:
        return _code_effects(a, S, fn, ifc)
    calls = SW.calls_for(S, fn, [a.impl], small=a.small)
    res = SW.run(fn, a.impl, calls)
    cols = SW.trace(fn, calls, res)
    counts = SW.outcome_summary(fn, res)['counts']
    print(f'{fn.name}: {len(calls)} calls; ' + ', '.join(f'{k} {v}' for k, v in counts.items()))
    if res.get('load_error'):
        print(f'the module does not load: {res["load_error"]}')
    bad = False
    for s in a.set:
        print(f'== {s}')
        out = SW.verify(S, s, fn, a.impl, calls, res, cols)
        by_req: dict[str, list] = {}
        for iid, x in out.items():
            if not iid.startswith('F-'):
                by_req.setdefault(x['req'] or '-', []).append((iid, x))
        for r, items in sorted(by_req.items()):
            worst = next((x for _, x in items if x['status'] in ('FAIL', 'NOT-COVERED')), None) or \
                next((x for _, x in items if x['status'] == 'VACUOUS'), None) or items[0][1]
            st = worst['status']
            bad |= st in ('FAIL', 'NOT-COVERED')
            line = f'  {r:14s} {st:11s}'
            if st == 'FAIL':
                line += ' ' + ' | '.join(f'{c["call"]} -> {c["got"]}' for c in worst['calls_shown'])
                line += f'  ({worst["count"]} failing calls, replay {worst["replay"]})'
            elif st == 'PASS' and worst.get('triggered') is not None:
                line += f' ({worst["triggered"]} calls where it applies)'
            print(line)
    return 1 if bad else 0


def _code_effects(a, S, fn, ifc):
    """fcp code for a function that acts through an interface (fcp.effects)."""
    from . import effects as FX
    runs = FX.scope(S, fn, ifc, small=a.small)
    res = FX.run(fn, ifc, a.impl, runs)
    print(f'{fn.name}: {len(runs)} runs, {sum(len(r["events"]) for r in res)} calls on the interface')
    bad = False
    for s in a.set:
        print(f'== {s}')
        out = FX.verify(S, s, fn, ifc, a.impl, runs, res)
        by_req: dict[str, list] = {}
        for iid, x in out.items():
            if not iid.startswith('F-'):
                by_req.setdefault(x['req'] or '-', []).append(x)
        for r, items in sorted(by_req.items()):
            worst = next((x for x in items if x['status'] in ('FAIL', 'NOT-COVERED')), None) or \
                next((x for x in items if x['status'] == 'VACUOUS'), None) or items[0]
            bad |= worst['status'] in ('FAIL', 'NOT-COVERED')
            line = f'  {r:14s} {worst["status"]:11s}'
            if worst['status'] == 'FAIL':
                line += f' {worst["call"]}: ' + ' ; '.join(worst['conversation']) + f'  (replay {worst["replay"]})'
            print(line)
    return 1 if bad else 0


def cmd_review(a):
    from . import review as RV
    if not a.code and not a.signature:
        sys.exit('fcp review: give --code, or --signature for a review of the request alone')
    res = RV.review(a.request, a.code, a.out, model=a.model, resume=a.resume, scope_budget=a.budget,
                    conflict_budget=a.conflict_budget, entry=a.entry, signature=a.signature,
                    compare_budget=a.compare_budget, jobs=a.jobs or RV.JOBS, memory=a.memory,
                    step_seconds=a.step_seconds, check_seconds=a.check_seconds)
    partial = 'the check gave no verdicts; ' if res.get('unchecked') else \
        f'partial: {len(res["failed"])} of {len(res["steps"])} steps of the check did not end; ' \
        if res.get('failed') else ''
    print(f'{partial}{"certified" if a.code else "settled"} {len(res["certified"])} requirements; '
          f'{len(res["queue"])} questions -> {os.path.join(a.out, "review.md")}')
    return 0


def cmd_anchor(a):
    with open(os.path.join(a.bundle, 'design.yaml')) as f:
        docs = {x['id']: x['path'] for x in yaml.safe_load(f)['docs']}
    with open(a.draft) as f:
        d = yaml.safe_load(f)
    bad = []
    for r in d['requirements']:
        if r.get('doc') not in docs:
            bad.append(r['id'])
            continue
        with open(os.path.join(a.bundle, docs[r['doc']])) as f:
            lines = f.read().split('\n')
        sp = anchor(lines, r['quote'])
        if sp is None:
            bad.append(r['id'])
            continue
        r['lines'] = [sp[0]] if sp[0] == sp[1] else [sp[0], sp[1]]
    if bad:
        print('quotes not found verbatim (rejected):', ', '.join(bad))
        d['requirements'] = [r for r in d['requirements'] if r['id'] not in bad]
    with open(a.out or a.draft, 'w') as f:
        yaml.safe_dump(d, f, sort_keys=False, width=200)
    print(f'anchored {len(d["requirements"])} requirements')


AGENT_COMMANDS = ('lint', 'explain', 'anchor')


def agent_refusal(a):
    """An agent of fcp review runs with FCP_AGENT_WS naming its workspace
    (fcp.review.run_agent).  Its launcher lints, explains and anchors that
    workspace and nothing else, so a reader cannot be pointed at another
    reader's files, at another bundle or at a new review.  The reason these
    arguments are refused, or None."""
    ws = os.environ.get('FCP_AGENT_WS')
    if not ws:
        return None
    if a.cmd not in AGENT_COMMANDS:
        return f'`fcp {a.cmd}` is not available to an agent (it has {", ".join(AGENT_COMMANDS)})'
    root = os.path.realpath(ws)
    for v in (a.bundle, getattr(a, 'draft', None), getattr(a, 'out', None)):
        if v and os.path.commonpath([root, os.path.realpath(v)]) != root:
            return f'{v} is outside the workspace {ws}: an agent works on the files of its own workspace'
    return None


AGENT_MEM_GB, AGENT_CPU_S = 1.0, 120
TOO_LARGE = ('A reading this large cannot be checked either. What grows is usually a quantifier (each is '
             'expanded value by value, and nested ones multiply) or a definition used under many bindings.')


def limited(fn, a) -> int:
    """An agent's command, run inside a bounded share of the machine: 1 GB of
    address space and 120 s of processor time (FCP_AGENT_MEM_GB and
    FCP_AGENT_CPU_S; 0 lifts one).  Linting a bundle of the studies, all its
    readings together, takes at most three seconds and 260 MB.  Without the
    bound, one reading that expands without end takes the memory of the
    whole run with it, every other agent included (docs/FCP_code.md,
    section 10).  The exit code of the command, or 3 when a limit stopped it.

    The limits hold whatever the command is in; the line that explains the
    stop is written by the stopped process itself, which a process with no
    memory left cannot always do.  Measured on `fcp lint` with the limit
    below what the interpreter already holds, so that every allocation
    fails: 823 of 830 runs end with the line and exit code 3; in the other
    seven CPython 3.12 spins in its own exception unwinding, and the kernel
    ends the command at the processor limit, without the line."""
    import resource
    import signal

    def soft(kind, n, grace=0):
        hard = resource.getrlimit(kind)[1]
        top = (lambda x: x) if hard == resource.RLIM_INFINITY else (lambda x: min(x, hard))
        resource.setrlimit(kind, (top(n), top(n + grace) if grace else hard))

    gb = float(os.environ.get('FCP_AGENT_MEM_GB', AGENT_MEM_GB))
    cpu = int(float(os.environ.get('FCP_AGENT_CPU_S', AGENT_CPU_S)))
    late = f'fcp: {a.cmd} was stopped after {cpu} s of processor time. {TOO_LARGE}\n'.encode()
    full = f'fcp: {a.cmd} was stopped: it needs more than {gb:g} GB of memory. {TOO_LARGE}\n'.encode()

    def stop(msg: bytes):
        """One line, and the process ends here.  Out of memory it cannot be
        left to unwind: the next allocation fails too, in main or in the
        interpreter's own exit, and the exit code is then no longer 3."""
        try:
            sys.stdout.flush()
        except BaseException:
            pass
        os.write(2, msg)
        os._exit(3)

    def over(sig, frame):
        stop(late)

    def starved() -> bool:
        try:
            bytearray(1 << 24)
        except MemoryError:
            return True
        return False

    try:
        if gb > 0:
            soft(resource.RLIMIT_AS, int(gb * 2 ** 30))
        if cpu > 0:
            signal.signal(signal.SIGXCPU, over)
            soft(resource.RLIMIT_CPU, cpu, grace=10)     # ten seconds later the kernel stops it, whatever it is in
        return fn(a) or 0
    except MemoryError:
        stop(full)
    except SystemError:                 # how CPython reports some failed allocations ("error return without exception set")
        if gb > 0 and starved():
            stop(full)
        raise


def main(argv=None):
    p = argparse.ArgumentParser(prog='fcp', description='Formal Context Protocol')
    sp = p.add_subparsers(dest='cmd', required=True)
    c = sp.add_parser('check')
    c.add_argument('bundle')
    c.add_argument('--set', action='append', default=[])
    c.add_argument('--extra-set', action='append', default=[], help='name=path of an extra formalization set')
    c.add_argument('--rtl', action='append', default=[])
    c.add_argument('--cache')
    c.add_argument('--out')
    c.add_argument('--jobs', type=int, default=24)
    c.add_argument('--mutants', type=int, default=60)
    c.add_argument('--no-mutation', action='store_true')
    c.add_argument('--only', help='comma-separated subset of analyses')
    c.set_defaults(fn=cmd_check)
    for name, fn in (('lint', cmd_lint), ('explain', cmd_explain), ('monitor', cmd_monitor)):
        x = sp.add_parser(name)
        x.add_argument('bundle')
        x.add_argument('--set', action='append', default=['gold'])
        x.set_defaults(fn=fn)
    x = sp.add_parser('code')
    x.add_argument('bundle')
    x.add_argument('impl')
    x.add_argument('--set', action='append', default=[])
    x.add_argument('--small', action='store_true', help='the small scope only')
    x.set_defaults(fn=cmd_code)
    x = sp.add_parser('review')
    x.add_argument('--request', required=True)
    x.add_argument('--code', help='a file, or a package directory (with --entry)')
    x.add_argument('--signature', help='instead of --code: a file with the def line of the function asked for '
                                       '(the request alone, before any code)')
    x.add_argument('--entry', help='for a package: the dotted module the entry point is in')
    x.add_argument('--out', required=True)
    x.add_argument('--model', default='opus')
    x.add_argument('--resume', action='store_true', help='reuse the bundle and readings already in --out')
    x.add_argument('--budget', type=float, default=120, help='seconds for drawing the scope, per reading set')
    x.add_argument('--conflict-budget', type=float, default=300, help='seconds for the conflict search, per reading')
    x.add_argument('--compare-budget', type=float, default=300, help='seconds for one comparison of two readings')
    x.add_argument('--jobs', type=int, help='engine tasks that run at a time (default 8; a large reading takes '
                                            '1 GB for each)')
    x.add_argument('--memory', type=float, help='GB that the check may hold; the step that passes it is stopped, '
                                                'named in the report, and the check goes on (default: 8, or less '
                                                'on a small machine or under a memory limit; 0: no limit)')
    x.add_argument('--step-seconds', type=float, default=900, help='a step of the check that runs longer is stopped')
    x.add_argument('--check-seconds', type=float, default=3600, help='after this long, the steps left are not run')
    x.set_defaults(fn=cmd_review)
    x = sp.add_parser('anchor')
    x.add_argument('bundle')
    x.add_argument('draft')
    x.add_argument('--out')
    x.set_defaults(fn=cmd_anchor)
    a = p.parse_args(argv)
    why = agent_refusal(a)
    if why:
        print(f'fcp: {why}', file=sys.stderr)
        return 2
    if a.cmd == 'check' and not a.rtl:
        a.rtl = ['ref']
    if a.cmd == 'check' and not a.set and not a.extra_set:
        a.set = ['gold']
    if a.cmd == 'code' and not a.set:
        a.set = ['gold']
    if a.cmd in ('explain', 'monitor') and len(a.set) > 1:
        a.set = a.set[1:]
    if os.environ.get('FCP_AGENT_WS'):
        return limited(a.fn, a)
    return a.fn(a) or 0


if __name__ == '__main__':
    sys.exit(main())
