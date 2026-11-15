"""FCP analyses.  Each one is a mechanical defence against a specific way in
which a verification run can produce false assurance.

  verify        M |= (A => P) for each property: PDR (unbounded) + BMC
                cross-check; every counterexample is replayed in an
                independent simulator.
  vacuity       the property's trigger is reachable on the RTL under A
                (witness), else proved unreachable => VACUOUS.
  tautology     P holds on *every* interface behaviour allowed by A (spec-only
                model, outputs free) => P constrains nothing => VACUOUS.
  env_sanity    A admits long traces on the RTL (A is not self-contradictory).
  consistency   for every situation a requirement talks about (its trigger),
                every pair of situations, and every scenario: some behaviour
                satisfies all requirements there => else CONFLICT + minimal
                conflicting set (deletion-based MUS).
  determinacy   two behaviours with identical inputs and identical output
                history that both satisfy the spec but differ in an output
                => UNDER-SPECIFIED (unless declared don't-care).
  compare       semantic implication between two independent formalizations
                of the same requirement (PDR on the product of monitors)
                => EQUIVALENT / STRONGER / WEAKER / INCOMPARABLE, with a
                distinguishing trace for a human to adjudicate.
"""
from __future__ import annotations

import itertools
import os
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from typing import Optional

import yaml

from .engine import Result, Runner, Task, tool, tool_env
from .harness import HarnessBuilder, replay_tb
from .ir import Bundle, RtlVariant, load_bundle
from .lang import FcpError
from .monitor import Monitor, build_monitor, vname
from . import smt as smtmod
from . import mutation as mutmod


def _rigid_focus(items, defs: Optional[dict] = None) -> dict:
    """Rigid variables that a trigger binds to a signal (a conjunct `sig == r`
    or `r == sig`, also inside a def the trigger names; defs: name -> body,
    text or parsed): rigid name -> signal name."""
    from .lang import parse
    out = {}
    defs = {k: (parse(v) if isinstance(v, str) else v) for k, v in (defs or {}).items()}

    def walk(n, seen=frozenset()):
        if n.op == 'bin' and n.val == '&&':
            for a in n.args:
                walk(a, seen)
        elif n.op == 'ref' and n.val in defs and n.val not in seen:
            walk(defs[n.val], seen | {n.val})
        elif n.op == 'bin' and n.val == '==':
            l, r = n.args
            for x, y in ((l, r), (r, l)):
                if x.op == 'ref' and y.op == 'ref' and x.val in rig and y.val not in rig and y.val not in defs:
                    out.setdefault(x.val, y.val)

    for it in items:
        rig = set(it.rigids)
        t = it.args.exprs.get('trigger')
        if t is not None:
            walk(t)
    return out


@dataclass
class Session:
    root: str
    sets: Optional[list] = None
    cache: Optional[str] = None
    jobs: int = 24
    timeout: int = 180
    cmp_engine: str = 'pdr'       # 'bmc': compare readings on runs of bmc_depth cycles (bounded evidence: see compare)

    def __post_init__(self):
        self.b: Bundle = load_bundle(self.root, self.sets)
        self.cache = self.cache or os.path.join(self.b.root, '.fcp', 'cache')
        self.runner = Runner(self.cache, self.jobs)
        self.bmc_depth = self.b.env.get('bmc_depth', 20)
        self.cover_depth = self.b.env.get('cover_depth', 20)
        self._mons: dict[str, Monitor] = {}
        self._points: dict[tuple, list] = {}      # the calls drawn for this session (fcp.software)
        self.mon_errors: dict[str, str] = {}

    # -- building blocks -------------------------------------------------------
    def mon(self, s: str) -> Monitor:
        if s not in self._mons:
            self._mons[s] = build_monitor(self.b.iface, self.b.fsets[s], f'fcp_mon_{vname(s)}')
        return self._mons[s]

    def try_mon(self, s: str) -> Optional[Monitor]:
        try:
            return self.mon(s)
        except FcpError as e:
            self.mon_errors[s] = str(e)
            return None

    def variant(self, name: str) -> RtlVariant:
        if name in self.b.rtl:
            return self.b.rtl[name]
        bugs = self.bugs()
        if name in bugs:
            ref = self.b.rtl['ref']
            return RtlVariant(name, ref.top, [bugs[name]['file']] + list(bugs[name].get('extra_files', [])),
                              ref.params, ref.port_map, bugs[name].get('desc', ''), 'injected-defect')
        raise KeyError(name)

    def bugs(self) -> dict:
        p = self.b.path('bugs/bugs.yaml')
        if not os.path.exists(p):
            return {}
        with open(p) as f:
            return {x['id']: x for x in yaml.safe_load(f)['bugs']}

    def gens(self, sets: list[str]) -> dict:
        return {f'mon_{vname(s)}.v': self.mon(s).text for s in sets}

    def props(self, s: str) -> list:
        return [it for it in self.mon(s).items.values() if it.role == 'property']

    def assumptions(self, s: str) -> list:
        return [it for it in self.mon(s).items.values() if it.role == 'assumption']

    def rtl_hb(self, s: str, v: RtlVariant, with_assumptions: bool = True) -> HarnessBuilder:
        hb = HarnessBuilder(self.b)
        hb.interface_free(False)
        hb.dut('dut', v)
        hb.monitor('mon', self.mon(s))
        hb.std_env()
        if with_assumptions:
            for a in self.assumptions(s):
                hb.assumes.append(f"mon_{a.out['aok']}")
        return hb

    def free_hb(self, sets: list[str], insts: Optional[list[str]] = None) -> HarnessBuilder:
        hb = HarnessBuilder(self.b)
        hb.interface_free(True)
        for s, inst in zip(sets, insts or ['mon'] * len(sets)):
            hb.monitor(inst, self.mon(s))
            # free outputs range over well-formed behaviours only
            for it in self.frame_items(s):
                hb.assumes.append(f"{inst}_{it.out['okd']}")
        hb.std_env()
        return hb

    def frame_items(self, s: str) -> list:
        return [it for it in self.props(s) if it.id in self.b.frame_ids]

    def reading_props(self, s: str) -> list:
        """Properties of the set itself, without the design frame."""
        return [it for it in self.props(s) if it.id not in self.b.frame_ids]

    def task(self, name: str, mode: str, hb: HarnessBuilder, sets: list[str], v: Optional[RtlVariant] = None,
             engine: str = 'pdr', depth: Optional[int] = None, timeout: Optional[int] = None) -> Task:
        gen = self.gens(sets)
        gen['harness.v'] = hb.text()
        srcs = [self.b.path(f) for f in v.files] if v else []
        d = depth or (self.cover_depth if mode == 'cover' else self.bmc_depth)
        return Task(name, mode, gen, srcs, hb.name, d, engine, timeout or self.timeout)

    def run(self, tasks: list[Task]) -> dict[str, Result]:
        return self.runner.run(tasks)

    def lookahead(self, s: str) -> int:
        """Cycles a witness must be extendable by so that every pending
        obligation of the set has expired (rules out doomed prefixes)."""
        win = []
        for it in self.mon(s).items.values():
            if it.role not in ('property', 'assumption'):
                continue
            if it.pattern == 'within':
                win.append(it.args.ints['max'])
            elif it.pattern == 'bounded_wait':
                win.append(it.args.ints['max'] + 1)
            elif it.pattern in ('next', 'after_reset'):
                win.append(1)
        return max([2] + [1 + w for w in win])

    def smt_free(self, s: str):
        if not hasattr(self, '_smt_free'):
            self._smt_free = {}
        if s not in self._smt_free:
            hb = self.free_hb([s])
            gen = self.gens([s])
            gen['harness.v'] = hb.text(formal=False)
            self._smt_free[s] = (smtmod.SmtModel(gen, [], hb.name), hb)
        return self._smt_free[s]

    # =========================================================================
    # verify: M |= (A => P)
    # =========================================================================
    def verify(self, s: str, vname_: str, replay: bool = True) -> dict:
        v = self.variant(vname_)
        tasks, hbs = [], {}
        for it in self.props(s):
            hb = self.rtl_hb(s, v)
            hb.asserts.append(f"mon_{it.out['ok']}")
            hbs[it.id] = hb
            tasks.append(self.task(f'pdr:{it.id}', 'prove', hb, [s], v, engine='pdr'))
            tasks.append(self.task(f'bmc:{it.id}', 'bmc', hb, [s], v, engine='bmc'))
        R = self.run(tasks)
        out = {}
        for it in self.props(s):
            p, bm = R[f'pdr:{it.id}'], R[f'bmc:{it.id}']
            rec = {'item': it.id, 'req': it.req, 'pdr': p.status, 'bmc': bm.status,
                   'seconds': round(p.seconds + bm.seconds, 3), 'keys': [p.key, bm.key],
                   'cached': p.cached and bm.cached}
            if p.status == 'FAIL' or bm.status == 'FAIL':
                trace = p.trace if (p.status == 'FAIL' and p.trace) else bm.trace
                wit = p.witness if (p.status == 'FAIL' and p.witness) else bm.witness
                rec['status'] = 'FAILED'
                rec['trace'] = trace
                rec['fail_step'] = len(trace) - 1 if trace else None
                if p.status == 'PASS' and bm.status == 'FAIL':
                    rec['status'] = 'ENGINE-DISAGREEMENT'
                if replay and wit:
                    rec['replay'] = self.replay(s, v, hbs[it.id], wit, trace, it)
            elif p.status == 'PASS' and bm.status in ('PASS', 'TIMEOUT', 'UNKNOWN'):
                rec['status'] = 'PROVED'
            elif bm.status == 'PASS':
                rec['status'] = 'BOUNDED'
                rec['depth'] = self.bmc_depth
            else:
                rec['status'] = 'UNKNOWN'
                rec['log'] = p.log_tail
            out[it.id] = rec
        return out

    # -- independent simulation replay of a counterexample -----------------------
    def replay(self, s: str, v: RtlVariant, hb: HarnessBuilder, wit: dict, trace: list, it) -> dict:
        probe = [x.name for x in self.b.iface.outputs] + [f"mon_{it.out['ok']}"]
        tb = replay_tb(hb, wit, probe)
        with tempfile.TemporaryDirectory(prefix='fcp_sim_') as d:
            files = []
            for k, txt in [('harness_sim.v', hb.text(formal=False)), ('tb.v', tb)] + list(self.gens([s]).items()):
                with open(os.path.join(d, k), 'w') as f:
                    f.write(txt)
                files.append(k)
            for src in v.files:
                shutil.copy(self.b.path(src), d)
                files.append(os.path.basename(src))
            try:
                c = subprocess.run([tool('iverilog'), '-g2012', '-o', 'sim', '-s', 'fcp_tb'] + files, cwd=d,
                                   capture_output=True, text=True, env=tool_env(), timeout=120)
                if c.returncode != 0:
                    return {'status': 'SIM-ERROR', 'detail': (c.stdout + c.stderr)[-1500:]}
                r = subprocess.run([tool('vvp'), '-n', 'sim'], cwd=d, capture_output=True, text=True,
                                   env=tool_env(), timeout=120)
            except subprocess.TimeoutExpired:
                return {'status': 'SIM-TIMEOUT'}
        steps = []
        for line in r.stdout.split('\n'):
            if line.startswith('STEP '):
                parts = line.split()
                vals = {}
                for kv in parts[2:]:
                    k, _, val = kv.partition('=')
                    vals[k] = int(val) if val.lstrip('-').isdigit() else None
                steps.append(vals)
        if not steps:
            return {'status': 'SIM-ERROR', 'detail': r.stdout[-800:] + r.stderr[-800:]}
        okn = f"mon_{it.out['ok']}"
        mismatches = []
        for k, (sv, fv) in enumerate(zip(steps, trace or [])):
            for sig in probe:
                if sig in fv and sv.get(sig) is not None and sv[sig] != fv[sig]:
                    mismatches.append({'step': k, 'signal': sig, 'formal': fv[sig], 'sim': sv[sig]})
        fails = [k for k, sv in enumerate(steps) if sv.get(okn) == 0]
        xsteps = [k for k, sv in enumerate(steps) if any(sv.get(p) is None for p in probe)]
        confirmed = bool(fails) and fails[-1] == len(steps) - 1 and not mismatches
        if confirmed:
            status = 'CONFIRMED'
        elif xsteps and not mismatches and (not fails or fails[-1] != len(steps) - 1) and \
                len(steps) - 1 in xsteps:
            # the simulator yields X where the solver picked a value: the failure
            # depends on undefined behaviour (uninitialised / out-of-range state)
            status = 'CONFIRMED-X'
        else:
            status = 'MISMATCH'
        return {'status': status, 'sim_fail_steps': fails, 'x_steps': xsteps,
                'mismatches': mismatches[:10], 'steps': len(steps)}

    # =========================================================================
    # vacuity / witnesses on the RTL, and environment sanity
    # =========================================================================
    def vacuity(self, s: str, vname_: str) -> dict:
        v = self.variant(vname_)
        tasks = []
        for it in self.props(s):
            hb = self.rtl_hb(s, v)
            hb.covers.append(f"mon_{it.out['tr']}")
            tasks.append(self.task(f'cov:{it.id}', 'cover', hb, [s], v, engine='cover'))
        for it in self.mon(s).items.values():
            if it.role == 'scenario':
                hb = self.rtl_hb(s, v)
                hb.covers.append(f"mon_{it.out['cov']}")
                tasks.append(self.task(f'scn:{it.id}', 'cover', hb, [s], v, engine='cover'))
        hb = self.rtl_hb(s, v)
        hb.covers.append(f"fcp_cnt == 8'd{self.cover_depth - 1}")
        tasks.append(self.task('env:long-trace', 'cover', hb, [s], v, engine='cover'))
        R = self.run(tasks)
        out = {'properties': {}, 'scenarios': {}, 'env': {}}
        unreached = []
        for it in self.props(s):
            r = R[f'cov:{it.id}']
            rec = {'item': it.id, 'reached': r.status == 'PASS', 'seconds': r.seconds, 'key': r.key}
            if r.status == 'PASS' and r.traces:
                rec['witness'] = r.traces[0]
            out['properties'][it.id] = rec
            if r.status != 'PASS':
                unreached.append(it)
        for it in self.mon(s).items.values():
            if it.role == 'scenario':
                r = R[f'scn:{it.id}']
                out['scenarios'][it.id] = {'item': it.id, 'reached': r.status == 'PASS',
                                           'witness': r.traces[0] if r.traces else None}
        r = R['env:long-trace']
        out['env'] = {'long_trace': r.status == 'PASS', 'depth': self.cover_depth}
        # unreached triggers: try to *prove* they are unreachable
        if unreached:
            pt = []
            for it in unreached:
                hb = self.rtl_hb(s, v)
                hb.asserts.append(f"!mon_{it.out['tr']}")
                pt.append(self.task(f'vac:{it.id}', 'prove', hb, [s], v, engine='pdr'))
            R2 = self.run(pt)
            for it in unreached:
                r = R2[f'vac:{it.id}']
                out['properties'][it.id]['vacuous'] = {'PASS': 'PROVEN', 'FAIL': 'NO'}.get(r.status, 'UNKNOWN')
                if r.status == 'FAIL':
                    out['properties'][it.id]['reached'] = True
                    out['properties'][it.id]['witness'] = r.trace
        return out

    # =========================================================================
    # tautology: does P constrain the design at all?
    # =========================================================================
    def tautology(self, s: str) -> dict:
        tasks = []
        for it in self.reading_props(s):
            hb = self.free_hb([s])
            for a in self.assumptions(s):
                hb.assumes.append(f"mon_{a.out['aok']}")
            hb.asserts.append(f"mon_{it.out['ok']}")
            tasks.append(self.task(f'taut:{it.id}', 'prove', hb, [s], engine='pdr'))
        R = self.run(tasks)
        out = {}
        for it in self.reading_props(s):
            r = R[f'taut:{it.id}']
            out[it.id] = {'item': it.id, 'tautology': r.status == 'PASS',
                          'status': r.status, 'violation_example': r.trace if r.status == 'FAIL' else None}
        return out

    # =========================================================================
    # consistency: conflicts among requirements, with minimal conflicting sets
    # =========================================================================
    def _spec_hb(self, s: str, assumed: list, cover: str, delay: int) -> HarnessBuilder:
        hb = self.free_hb([s])
        hb.no_later_reset()
        for a in self.assumptions(s):
            hb.assumes.append(f"mon_{a.out['aok']}")
        for it in assumed:
            hb.assumes.append(f"mon_{it.out['okd']}")
        hb.asserts.append('!' + hb.delayed(cover, delay))
        return hb

    def consistency(self, s: str, delay: Optional[int] = None, pairs: bool = True,
                    scenarios_only: bool = False) -> dict:
        """Search for stimuli on which the requirements cannot all be met.

        Every situation a requirement talks about (its trigger), every pair of
        situations and every scenario is checked for a spec-conforming
        continuation.  A blocked situation is only a *candidate*: the spec may
        legitimately steer outputs away from it.  It is a conflict only if, on
        the inputs of a trace reaching it, no output sequence at all satisfies
        the requirements (checked with z3, which also yields a minimal core).
        scenarios_only: the scenarios and no other situation; each scenario
        gets the verdict it has in the full search."""
        props = [it for it in self.props(s) if 'okd' in it.out]
        delay = delay or self.lookahead(s)
        situations = {}
        trig = [] if scenarios_only else \
            [it for it in props if it.pattern != 'invariant' and it.id not in self.b.frame_ids]
        for it in trig:
            situations[f'trig({it.id})'] = (f"mon_{it.out['tr']}", [it.id])
        if pairs:
            for p, q in itertools.combinations(trig, 2):
                situations[f'trig({p.id})&trig({q.id})'] = (f"mon_{p.out['tr']} && mon_{q.out['tr']}", [p.id, q.id])
        for it in self.mon(s).items.values():
            if it.role == 'scenario':
                situations[f'scenario({it.id})'] = (f"mon_{it.out['cov']}", [it.id])
        if not scenarios_only:
            situations['progress'] = ("1'b1", [])
        t1 = [self.task(f'cons:{k}', 'prove', self._spec_hb(s, props, e, delay), [s], engine='pdr')
              for k, (e, _) in situations.items()]
        R1 = self.run(t1)
        blocked = [k for k in situations if R1[f'cons:{k}'].status == 'PASS']
        undecided = [k for k in situations if R1[f'cons:{k}'].status not in ('PASS', 'FAIL')]
        t2 = [self.task(f'free:{k}', 'prove', self._spec_hb(s, [], situations[k][0], delay), [s], engine='pdr')
              for k in blocked]
        R2 = self.run(t2)
        impossible = [k for k in blocked if R2[f'free:{k}'].status == 'PASS']
        candidates = [k for k in blocked if R2[f'free:{k}'].status == 'FAIL' and R2[f'free:{k}'].trace]
        conflicts, excluded = {}, []
        scenario_blocked = []
        for k in candidates:
            tr = R2[f'free:{k}'].trace
            res = self.triage(s, tr, closest=False)
            if res['class'] == 'SPEC-CONFLICT':
                key = tuple(res['core'])
                c = conflicts.setdefault(key, {'mus': list(key), 'situations': [], 'stimulus': tr})
                c['situations'].append(k)
            else:
                excluded.append({'situation': k, 'class': res['class']})
                if k.startswith('scenario('):
                    scenario_blocked.append(k)
        out = []
        for key, c in conflicts.items():
            c['reqs'] = sorted({self.mon(s).items[i].req for i in c['mus'] if self.mon(s).items[i].req})
            out.append(c)
        # a scenario that can never happen: its cover is impossible by itself
        # (a formalization error), or the reading's own properties forbid it
        # (the example contradicts a rule, or a rule is misread)
        return {'situations': len(situations), 'lookahead': delay, 'blocked': blocked,
                'impossible_situations': impossible, 'excluded_situations': excluded,
                'unreachable_scenarios': scenario_blocked, 'undecided': undecided,
                'impossible_scenarios': [k[9:-1] for k in impossible if k.startswith('scenario(')],
                'forbidden_scenarios': [k[9:-1] for k in scenario_blocked],
                'conflicts': out, 'consistent': not out}

    def forcing(self, s: str, depth: Optional[int] = None, limit: int = 4, max_iter: int = 80) -> dict:
        """Conflicts that the environment can force: stimuli on which no output
        sequence at all meets the requirements (smt.forcing), each with a
        minimal conflicting set.  Unlike `consistency`, this does not need a
        whole trigger situation to be blocked: a requirement that is satisfiable
        in most situations can still be defeated by one stimulus (for example
        an input that arrives before the design could prepare for it).  Further
        conflicts are searched for with each element of a found core removed."""
        model, hb = self.smt_free(s)
        props = [it for it in self.props(s) if 'okd' in it.out]
        frame = set(self.b.frame_ids)
        okd = {it.id: f"mon_{it.out['okd']}" for it in props}
        aok = [f"mon_{a.out['aok']}" for a in self.assumptions(s)]
        ins = [(x.name, x.width) for x in self.b.iface.inputs]
        outs = [(x.name, x.width) for x in self.b.iface.outputs]
        r = self.b.iface.reset
        depth = depth or max(self.lookahead(s), 4)
        found, queue, seen, runs = [], [frozenset()], set(), []
        t0 = time.time()
        while queue and len(found) < limit:
            banned = queue.pop(0)
            if banned in seen:
                continue
            seen.add(banned)
            sub = {k: v for k, v in okd.items() if k not in banned}
            res = smtmod.forcing(model, ins, outs, aok, sub, r.name, r.active_low, depth, max_iter)
            runs.append({'banned': sorted(banned), 'forced': res['forced'], 'depth': res['depth'],
                         'iterations': res['iterations'], 'undecided': res.get('undecided', False)})
            if not res['forced']:
                continue
            tri = smtmod.triage(model, res['stimulus'], ins, outs, aok, sub, hb.rigid_regs, [], closest=False)
            core = tri.get('core') or sorted(sub)
            if not any(c['core'] == core for c in found):
                found.append({'core': core, 'stimulus': res['stimulus'], 'depth': res['depth'],
                              'reqs': sorted({self.mon(s).items[i].req for i in core if self.mon(s).items[i].req})})
            for e in core:
                if e not in frame:
                    queue.append(banned | {e})
        return {'conflicts': found, 'searches': runs, 'depth': depth, 'seconds': round(time.time() - t0, 2),
                'forced': bool(found)}

    def _blocked(self, s: str, props: list, cover: str, delay: int) -> bool:
        r = self.run([self.task('blk', 'prove', self._spec_hb(s, props, cover, delay), [s], engine='pdr')])['blk']
        return r.status == 'PASS'

    def _mus_enum(self, s: str, props: list, cover: str, delay: int, limit: int = 4) -> list[list[str]]:
        """Several minimal conflicting subsets: after finding one MUS M, look for
        MUSes that avoid each element of M (a simple hitting-set diversification),
        so that one conflict cannot mask another."""
        found: list[list[str]] = []
        queue = [frozenset()]
        seen = set()
        while queue and len(found) < limit:
            banned = queue.pop(0)
            if banned in seen:
                continue
            seen.add(banned)
            cand = [it for it in props if it.id not in banned]
            if not self._blocked(s, cand, cover, delay):
                continue
            m = self._mus(s, cand, cover, delay)
            if m not in found:
                found.append(m)
            for e in m:
                queue.append(banned | {e})
        return found

    def _mus(self, s: str, props: list, cover: str, delay: int) -> list[str]:
        keep = list(props)
        i = 0
        while i < len(keep):
            trial = keep[:i] + keep[i + 1:]
            r = self.run([self.task('mus', 'prove', self._spec_hb(s, trial, cover, delay), [s], engine='pdr')])['mus']
            if r.status == 'PASS':      # still blocked without keep[i]: not needed
                keep = trial
            else:
                i += 1
        return [it.id for it in keep]

    # =========================================================================
    # determinacy: is every output determined by the spec (or declared don't-care)?
    # =========================================================================
    def determinacy(self, s: str) -> dict:
        m = self.mon(s)
        props = [it for it in self.props(s) if 'okd' in it.out]
        outs = self.b.iface.outputs
        dcs = [it for it in m.items.values() if it.role == 'dontcare']
        results = {}
        tasks = []
        for o in outs:
            hb = HarnessBuilder(self.b)
            for sig in self.b.iface.signals:
                if sig.name == self.b.iface.clock:
                    continue
                hb.free(sig.name, sig.width)
                if sig.dir == 'out':
                    hb.free(sig.name + '__b', sig.width)
            hb.monitor('ma', m)
            hb.monitor('mb', m, rename={x.name: x.name + '__b' for x in outs})
            hb.std_env()
            hb.no_later_reset()
            for inst in ('ma', 'mb'):
                for a in self.assumptions(s):
                    hb.assumes.append(f"{inst}_{a.out['aok']}")
                for it in props:
                    hb.assumes.append(f"{inst}_{it.out['okd']}")
            eq = ' && '.join(f'({x.name} == {x.name}__b)' for x in outs)
            hb.regs.append("  reg fcp_same = 1'b1;")
            hb.body.append(f'  always @(posedge clk) if (!({hb.rst})) fcp_same <= fcp_same && ({eq});')
            dc = [f"ma_{d.out['dc']}" for d in dcs if d.note == o.name]
            cond = f'!({hb.rst}) && fcp_same && ({o.name} != {o.name}__b)'
            if dc:
                cond += ' && !(' + ' || '.join(dc) + ')'
            hb.asserts.append('!' + hb.delayed(cond, self.lookahead(s)))
            tasks.append(self.task(f'det:{o.name}', 'prove', hb, [s], engine='pdr', timeout=max(self.timeout, 600)))
        R = self.run(tasks)
        for o in outs:
            r = R[f'det:{o.name}']
            results[o.name] = {'signal': o.name,
                               'determined': {'PASS': True, 'FAIL': False}.get(r.status),
                               'witness': r.trace if r.status == 'FAIL' else None,
                               'status': r.status, 'seconds': r.seconds}
        return results

    # =========================================================================
    # compare two formalizations, requirement by requirement
    # =========================================================================
    @property
    def _cmp_mode(self) -> str:
        return 'bmc' if self.cmp_engine == 'bmc' else 'prove'

    def compare(self, sa: str, sb: str, env: Optional[str] = None, context: bool = False,
                only: Optional[set] = None, economy: Optional[list[str]] = None,
                ctx_reqs: Optional[dict] = None) -> dict:
        """Compare the *contracts* of two formalizations, requirement by requirement.

        With env=<set>, compare instead the *properties* of both sets under the
        assumptions of that one set only (used to measure property accuracy
        against a reference independently of assumption differences).

        With context=True, a distinguishing behaviour must also satisfy every
        *other* requirement under both readings.  Witnesses then look like real
        conforming behaviour, and a disagreement that no such behaviour exhibits
        is reported EQUIVALENT (in context): it cannot change the verdict on any
        behaviour that meets the rest of the specification under both readings.
        NO-CONTEXT means that no behaviour meets the rest of the specification.
        `only` restricts the comparison to some requirements, and `ctx_reqs`
        (req -> requirements) narrows a requirement's context.  With `economy`
        (1-bit outputs), each witness is replaced by one that sets as few of
        those outputs as possible: the simplest behaviour to show a person.
        A record's 'status' says what each direction found ('none', 'witness'
        or 'unknown'), so that an UNKNOWN record still tells which direction
        was closed.  With cmp_engine 'bmc' a 'none' is bounded: a disagreement
        is reported `lookahead` cycles after it happens, so no run of
        bmc_depth cycles has one in its first bmc_depth - lookahead cycles
        (the record's 'depth' and 'lookahead').  In context a 'none' is
        written only where a behaviour was shown to meet the rest of the
        specification (the search for one found it, or a direction found a
        call); otherwise the record is UNKNOWN with nothing closed.  With
        env no '<assumptions>' record is written: both sets run under the
        assumptions of that one set.

        Set x's contract for requirement r is  A_x => P_x,r : its guarantees are
        required only while all of its own assumptions have held.  Comparing
        properties under the pooled assumptions of both sets would let one
        set's over-constraining assumption hide every disagreement in the
        behaviours it excludes; comparing contracts exposes it."""
        by_req = {}
        for it in self.props(sa):
            by_req.setdefault(it.req, [[], []])[0].append(it)
        for it in self.props(sb):
            by_req.setdefault(it.req, [[], []])[1].append(it)
        la = max(self.lookahead(sa), self.lookahead(sb))
        if self.cmp_engine == 'bmc' and self.bmc_depth < la + 2:
            # cycle 0 is the reset, and a disagreement in cycle t is reported in cycle t + la
            raise ValueError(f'a bounded comparison of {self.bmc_depth} cycles examines no call: a disagreement is '
                             f'reported {la} cycles after it happens, so it needs at least {la + 2}')

        def hb_for():
            hb = self.free_hb([sa, sb], ['ma', 'mb'])
            if env is not None:
                inst = 'ma' if env == sa else 'mb'
                for a in self.assumptions(env):
                    hb.assumes.append(f"{inst}_{a.out['aok']}")
                for i in ('ma', 'mb'):
                    hb.wire(f'fcp_e_{i}', 1)
                    hb.body.append(f"  assign fcp_e_{i} = 1'b1;")
                return hb
            for inst, st in (('ma', sa), ('mb', sb)):
                aok = ' && '.join(f"{inst}_{a.out['aok']}" for a in self.assumptions(st)) or "1'b1"
                hb.regs.append(f"  reg fcp_h_{inst} = 1'b1;")
                hb.body.append(f'  always @(posedge clk) fcp_h_{inst} <= fcp_h_{inst} && ({aok});')
                hb.wire(f'fcp_e_{inst}', 1)
                hb.body.append(f'  assign fcp_e_{inst} = fcp_h_{inst} && ({aok});  // own assumptions held so far')
            return hb

        def ctx(hb, req):
            keep = (ctx_reqs or {}).get(req)
            for inst, st in (('ma', sa), ('mb', sb)):
                for it in self.reading_props(st):
                    if it.req != req and 'okd' in it.out and (keep is None or it.req in keep):
                        hb.assumes.append(f"!fcp_e_{inst} || {inst}_{it.out['okd']}")

        def dir_hb(req, src, dst, si, di, budget=None, pins=()):
            hb = hb_for()
            if context:
                ctx(hb, req)
            for it in src:
                if 'okd' in it.out:
                    hb.assumes.append(f"!fcp_e_{si} || {si}_{it.out['okd']}")
            ok_dst = f'!fcp_e_{di} || (' + ' && '.join(f"{di}_{it.out['ok']}" for it in dst) + ')'
            # A source property over a rigid range too large to expand is assumed
            # only at some valuations, one monitor instance each: the focus (rigid
            # values equal to the signals the trigger binds them to, sampled at
            # the first violation of the destination) and pinned constants.  Each
            # valuation is a function of the trace, so the premise is implied by
            # the property for all values: a proof is sound.
            free_src = [it for it in src if 'okd' not in it.out]
            if free_src:
                for k, val in enumerate([None] + list(pins)):
                    inst = f'{si}p{k}'
                    hb.monitor(inst, self.mon(sa if si == 'ma' else sb))
                    if val is None:
                        for name, sig in _rigid_focus(free_src, self.b.fsets[sa if si == 'ma' else sb].get('defs')).items():
                            hb.assumes.append(f'fcp_bad || ({ok_dst}) || ({inst}_rg_{name} == {sig})')
                    else:
                        for name, v in val.items():
                            hb.assumes.append(f'{inst}_rg_{name} == {v}')
                    for it in free_src:
                        hb.assumes.append(f"!fcp_e_{si} || {inst}_{it.out['ok']}")
            hb.regs.append("  reg fcp_bad = 1'b0;")
            hb.body.append(f'  always @(posedge clk) if (!({ok_dst})) fcp_bad <= 1\'b1;')
            hb.asserts.append('!' + hb.delayed(f'fcp_bad || !({ok_dst})', la))
            if budget is not None:
                hb.regs.append("  reg [7:0] fcp_cost = 8'd0;  // outputs set so far (witness economy)")
                hb.body.append(f'  always @(posedge clk) if (!({hb.rst})) fcp_cost <= fcp_cost + ' +
                               ' + '.join(f"{{7'b0, {o}}}" for o in economy) + ';')
                hb.assumes.append(f"fcp_cost <= 8'd{budget}")
            return hb

        def cost(trace):
            return sum(int(st.get(o) or 0) for st in trace if str(st.get(self.b.iface.reset.name)) ==
                       ('1' if self.b.iface.reset.active_low else '0') for o in economy)

        tag = 'cmpx' if context else 'cmp'
        dirs, pinned = {}, {}
        if only is not None:
            by_req = {r: x for r, x in by_req.items() if r in only}
        tasks = []
        for req, (pa, pb) in by_req.items():
            if not pa or not pb:
                continue
            if context:
                hb = hb_for()
                ctx(hb, req)
                hb.asserts.append('!' + hb.delayed("1'b1", la))
                tasks.append(self.task(f'{tag}:{req}:sat', self._cmp_mode, hb, [sa, sb], engine=self.cmp_engine))
            for direction, (src, dst, si, di) in {'a=>b': (pa, pb, 'ma', 'mb'), 'b=>a': (pb, pa, 'mb', 'ma')}.items():
                spec = (req, src, dst, si, di)
                dirs[f'{tag}:{req}:{direction}'] = spec
                if any('okd' not in it.out for it in src):
                    pinned[f'{tag}:{req}:{direction}'] = []
                    continue
                tasks.append(self.task(f'{tag}:{req}:{direction}', self._cmp_mode, dir_hb(*spec), [sa, sb], engine=self.cmp_engine))
        # the environments themselves (informational)
        if env is None and not context and (self.assumptions(sa) or self.assumptions(sb)):
            for direction, (src, dst, si, di) in {'a=>b': (sa, sb, 'ma', 'mb'), 'b=>a': (sb, sa, 'mb', 'ma')}.items():
                hb = self.free_hb([sa, sb], ['ma', 'mb'])
                for a in self.assumptions(src):
                    hb.assumes.append(f"{si}_{a.out['aok']}")
                if self.assumptions(dst):
                    hb.asserts.append(' && '.join(f"{di}_{a.out['aok']}" for a in self.assumptions(dst)))
                    tasks.append(self.task(f'cmp:<assumptions>:{direction}', self._cmp_mode, hb, [sa, sb], engine=self.cmp_engine))
        R = self.run(tasks)
        for name in pinned:
            R[name], pinned[name] = self._pinned_direction(name, dirs[name], dir_hb, sa, sb)
        for name, spec in dirs.items() if economy else ():
            best = R[name]
            if best.status != 'FAIL' or not best.trace:
                continue
            lo, hi = 0, cost(best.trace) - 1          # search for a witness of cost <= hi
            while lo <= hi:
                mid = (lo + hi) // 2
                r = self.run([self.task(f'{name}:k{mid}', self._cmp_mode, dir_hb(*spec, budget=mid, pins=pinned.get(name, ())),
                                        [sa, sb], engine=self.cmp_engine)])[f'{name}:k{mid}']
                if r.status == 'FAIL' and r.trace and name in pinned and self._pin_needed(dirs[name], sa, sb, r.trace):
                    r = None        # cheaper, but breaks the source reading at a value that is not pinned
                if r is not None and r.status == 'FAIL' and r.trace:
                    best, hi = r, min(mid, cost(r.trace)) - 1
                else:
                    lo = mid + 1
            R[name] = best
        out = {}
        for req in list(by_req) + ([] if context or env is not None else ['<assumptions>']):
            pa, pb = by_req.get(req, [[], []]) if req != '<assumptions>' else (self.assumptions(sa), self.assumptions(sb))
            ab, ba = R.get(f'{tag}:{req}:a=>b'), R.get(f'{tag}:{req}:b=>a')
            if req == '<assumptions>' and not (pa or pb):
                continue
            rec = {'req': req, 'a': [it.id for it in pa], 'b': [it.id for it in pb]}
            if req != '<assumptions>' and (not pa or not pb):
                rec['relation'] = 'ONLY-A' if pa else 'ONLY-B'
            else:
                if req == '<assumptions>':
                    ab = ab if pb else None
                    ba = ba if pa else None
                    a_imp_b = (ab.status == 'PASS') if ab else True
                    b_imp_a = (ba.status == 'PASS') if ba else True
                else:
                    a_imp_b = ab is not None and ab.status == 'PASS'
                    b_imp_a = ba is not None and ba.status == 'PASS'
                unknown = any(r is not None and r.status not in ('PASS', 'FAIL') for r in (ab, ba)) or \
                    (req != '<assumptions>' and (ab is None or ba is None))
                if a_imp_b and b_imp_a:
                    rec['relation'] = 'EQUIVALENT'
                elif unknown:
                    rec['relation'] = 'UNKNOWN'
                elif a_imp_b:
                    rec['relation'] = 'A-STRONGER'
                elif b_imp_a:
                    rec['relation'] = 'A-WEAKER'
                else:
                    rec['relation'] = 'INCOMPARABLE'
                if ab is not None and ab.status == 'FAIL':
                    rec['witness_a_not_b'] = ab.trace
                if ba is not None and ba.status == 'FAIL':
                    rec['witness_b_not_a'] = ba.trace
                rec['status'] = {key: 'none' if imp else 'witness' if x is not None and x.status == 'FAIL' else 'unknown'
                                 for key, imp, x in (('witness_a_not_b', a_imp_b, ab), ('witness_b_not_a', b_imp_a, ba))}
                sat = R.get(f'{tag}:{req}:sat')
                if context and sat is not None and sat.status == 'PASS':
                    rec['relation'] = 'NO-CONTEXT'
                elif context and not any(x is not None and x.status == 'FAIL' for x in (sat, ab, ba)):
                    # no behaviour was shown to meet the rest of the specification (the search for one did not
                    # end, and no direction found a call): a direction that passed may have passed on nothing
                    rec['relation'] = 'UNKNOWN'
                    rec['status'] = {key: 'unknown' for key in rec['status']}
            if self.cmp_engine != 'pdr':
                # a bounded direction searched runs of `depth` cycles for a disagreement in their first depth - la
                rec['engine'], rec['depth'], rec['lookahead'] = self.cmp_engine, self.bmc_depth, la
            out[req] = rec
        return out

    def _pin_needed(self, spec, sa: str, sb: str, trace: list) -> Optional[dict]:
        """A rigid valuation at which the trace breaks a source property that is
        assumed only at pinned values, or None if it meets them all."""
        from . import rv
        req, src, dst, si, di = spec
        res = rv.check(self, sa if si == 'ma' else sb, trace, valuations=True)
        bad = [res[it.id] for it in src if 'okd' not in it.out and res.get(it.id)]
        return min(bad, key=lambda x: x[0])[1] if bad else None

    def _pinned_direction(self, name: str, spec, dir_hb, sa: str, sb: str, max_iter: int = 16):
        """Implication check for a source reading over a rigid range too large to
        expand (no deterministic form): assume it at pinned valuations; when the
        solver's counterexample breaks it at another valuation (checked exactly by
        replaying the trace over every valuation), pin that one and repeat.
        A proof at the pinned valuations is a proof for all of them.  Where the
        valuations are more than a replay runs (rv.MAX_CASES), a counterexample
        cannot be checked that way, and the direction is left open (UNKNOWN)."""
        from . import rv
        pins: list[dict] = []
        for _ in range(max_iter):
            r = self.run([self.task(f'{name}:p{len(pins)}', self._cmp_mode, dir_hb(*spec, pins=pins), [sa, sb],
                                    engine=self.cmp_engine)])[f'{name}:p{len(pins)}']
            if r.status != 'FAIL':
                return r, pins
            if not r.trace:                    # a counterexample without a trace cannot be replayed: not confirmed
                return Result(name, '', 'UNKNOWN', 'prove', self.cmp_engine, 0.0, '',
                              log_tail='not confirmed: the counterexample has no trace'), pins
            try:
                v = self._pin_needed(spec, sa, sb, r.trace)
            except rv.NotReplayed as e:
                return Result(name, '', 'UNKNOWN', 'prove', self.cmp_engine, 0.0, '', log_tail=f'not confirmed: {e}'), pins
            if v is None:
                return r, pins
            pins.append(v)
        return Result(name, '', 'UNKNOWN', 'prove', 'pdr', 0.0, ''), pins

    def minimal_context(self, sa: str, sb: str, req: str) -> Optional[list[str]]:
        """A minimal set of other requirements under which the two readings of
        `req` are equivalent (deletion-based, like a MUS), or None if they
        differ even in the full context."""
        reqs = sorted({it.req for st in (sa, sb) for it in self.reading_props(st) if it.req and it.req != req})

        def equiv(keep):
            c = self.compare(sa, sb, context=True, only={req}, ctx_reqs={req: set(keep)})
            return c.get(req, {}).get('relation') in ('EQUIVALENT', 'NO-CONTEXT')

        if not equiv(reqs):
            return None
        keep = list(reqs)
        for r in reqs:
            trial = [x for x in keep if x != r]
            if equiv(trial):
                keep = trial
        return keep

    # =========================================================================
    # z3-based: receptiveness of assumptions, counterexample triage
    # =========================================================================
    def receptive(self, s: str, vname_: str, depth: int = 12) -> dict:
        v = self.variant(vname_)
        hb = HarnessBuilder(self.b)
        hb.interface_free(False)
        hb.dut('dut', v)
        hb.monitor('mon', self.mon(s))
        aok = [f"mon_{a.out['aok']}" for a in self.assumptions(s)]
        if not aok:
            return {'receptive': True, 'note': 'no environment assumptions'}
        gen = self.gens([s])
        gen['harness.v'] = hb.text(formal=False)
        model = smtmod.SmtModel(gen, [self.b.path(f) for f in v.files], hb.name)
        r = self.b.iface.reset
        t0 = time.time()
        res = smtmod.receptiveness(model, aok, r.name, r.active_low, hb.rigid_regs, depth)
        res['seconds'] = round(time.time() - t0, 2)
        return res

    def triage(self, s: str, trace: list, closest: bool = True) -> dict:
        model, hb = self.smt_free(s)
        props = [it for it in self.props(s) if 'okd' in it.out]
        okd = {it.id: f"mon_{it.out['okd']}" for it in props}
        aok = [f"mon_{a.out['aok']}" for a in self.assumptions(s)]
        ins = [(x.name, x.width) for x in self.b.iface.inputs]
        outs = [(x.name, x.width) for x in self.b.iface.outputs]
        t0 = time.time()
        res = smtmod.triage(model, trace, ins, outs, aok, okd, hb.rigid_regs, [], closest=closest)
        res['seconds'] = round(time.time() - t0, 2)
        return res

    # =========================================================================
    # mutation-based assurance coverage
    # =========================================================================
    def mutation(self, s: str, vname_: str = 'ref', n: int = 60, seed: int = 1,
                 obs_set: Optional[str] = None) -> dict:
        v = self.variant(vname_)
        muts = mutmod.gen_mutants(self.b, v, n, seed, os.path.join(self.cache, 'mutants'))
        obs_set = obs_set or s
        mo = self.mon(obs_set)
        dcs = [it for it in mo.items.values() if it.role == 'dontcare']
        tasks = []
        mvs = {}
        for mu in muts:
            mv = RtlVariant(mu['id'], mu['module'], [mu['file']], {}, v.port_map)
            mvs[mu['id']] = mv
            hb = HarnessBuilder(self.b)
            hb.interface_free(False)
            hb.dut('dut', v)
            hb.dut('mut', mv, out_suffix='__m')
            hb.monitor('mon', mo)
            hb.std_env()
            for a in self.assumptions(obs_set):
                hb.assumes.append(f"mon_{a.out['aok']}")
            conds = []
            for o in self.b.iface.outputs:
                dc = [f"mon_{d.out['dc']}" for d in dcs if d.note == o.name]
                c = f'({o.name} == {o.name}__m)'
                if dc:
                    c = f'({c} || ' + ' || '.join(dc) + ')'
                conds.append(c)
            hb.asserts.append(f'({hb.rst}) || (' + ' && '.join(conds) + ')')
            gen = self.gens([obs_set])
            gen['harness.v'] = hb.text()
            tasks.append(Task(f'obs:{mu["id"]}', 'prove', gen, [self.b.path(f) for f in v.files] + [mu['file']],
                              hb.name, self.bmc_depth, 'pdr', self.timeout))
        R = self.run(tasks)
        obs = {m['id']: {'PASS': False, 'FAIL': True}.get(R[f'obs:{m["id"]}'].status) for m in muts}
        ktasks = []
        for mu in muts:
            if obs[mu['id']] is False:
                continue
            for it in self.props(s):
                hb = self.rtl_hb(s, mvs[mu['id']])
                hb.asserts.append(f"mon_{it.out['ok']}")
                gen = self.gens([s])
                gen['harness.v'] = hb.text()
                ktasks.append(Task(f'kill:{mu["id"]}:{it.id}', 'prove', gen, [mu['file']], hb.name,
                                   self.bmc_depth, 'pdr', self.timeout))
        K = self.run(ktasks)
        rows = []
        for mu in muts:
            o = obs[mu['id']]
            killed_by = [it.id for it in self.props(s)
                         if K.get(f'kill:{mu["id"]}:{it.id}') and K[f'kill:{mu["id"]}:{it.id}'].status == 'FAIL']
            if o is False:
                st = 'EQUIVALENT'
            elif killed_by:
                st = 'KILLED'
            elif o is True:
                st = 'SURVIVED'
            else:
                st = 'UNKNOWN'
            row = {'id': mu['id'], 'mode': mu['mode'], 'src_lines': mu['src_lines'], 'wire': mu['wire'],
                   'observable': o, 'killed_by': killed_by, 'status': st, 'cmd': mu['cmd']}
            if st == 'SURVIVED':
                row['witness'] = R[f'obs:{mu["id"]}'].trace
            rows.append(row)
        n_obs = sum(1 for r in rows if r['status'] in ('KILLED', 'SURVIVED'))
        n_kill = sum(1 for r in rows if r['status'] == 'KILLED')
        by_line: dict[int, dict] = {}
        for r in rows:
            for ln in r['src_lines']:
                d = by_line.setdefault(ln, {'killed': 0, 'survived': 0, 'equivalent': 0, 'reqs': set()})
                if r['status'] == 'KILLED':
                    d['killed'] += 1
                    d['reqs'] |= {self.mon(s).items[p].req for p in r['killed_by']}
                elif r['status'] == 'SURVIVED':
                    d['survived'] += 1
                elif r['status'] == 'EQUIVALENT':
                    d['equivalent'] += 1
        for d in by_line.values():
            d['reqs'] = sorted(x for x in d['reqs'] if x)
        return {'set': s, 'obs_set': obs_set, 'variant': vname_, 'n': len(rows), 'observable': n_obs,
                'killed': n_kill, 'coverage': round(n_kill / n_obs, 4) if n_obs else None,
                'mutants': rows, 'by_line': by_line}
