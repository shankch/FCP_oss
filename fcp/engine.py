"""Proof-engine back end: SymbiYosys tasks, parallel execution, caching, traces.

Every task is content-addressed: its identity is the hash of the exact sby
configuration and of every file it reads.  Results are cached under that
hash, so re-running an unchanged obligation is free, and each cached task
directory is a self-contained, re-runnable proof artifact.
"""
from __future__ import annotations

import concurrent.futures as cf
import json
import os
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from typing import Optional

from .ir import sha256_bytes

TOOLS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.tools', 'oss-cad-suite', 'bin')


def tool_env() -> dict:
    env = dict(os.environ)
    if os.path.isdir(TOOLS):
        env['PATH'] = TOOLS + os.pathsep + env.get('PATH', '')
    return env


def tool(name: str) -> str:
    p = os.path.join(TOOLS, name)
    return p if os.path.exists(p) else name


_versions = None


def tool_versions() -> dict:
    global _versions
    if _versions is None:
        def first(cmd):
            try:
                out = subprocess.run(cmd, capture_output=True, text=True, env=tool_env(), timeout=30)
                return (out.stdout or out.stderr).strip().split('\n')[0]
            except Exception as e:  # pragma: no cover
                return f'unavailable ({e})'
        import z3
        _versions = {'yosys': first([tool('yosys'), '-V']),
                     'iverilog': first([tool('iverilog'), '-V']),
                     'yices': first([tool('yices-smt2'), '--version']),
                     'z3py': z3.get_version_string()}
    return _versions


ENGINES = {
    'pdr': 'abc pdr',               # unbounded proof (IC3/PDR on the AIGER model)
    'bmc': 'smtbmc boolector',      # bounded cross-check through the independent SMT2 path
    'kind': 'smtbmc boolector',     # k-induction
    'cover': 'smtbmc boolector',
}


@dataclass
class Task:
    name: str
    mode: str                     # prove | bmc | cover
    gen: dict                     # generated file name -> content
    srcs: list                    # absolute paths of source files to include
    top: str
    depth: int = 20
    engine: str = 'pdr'
    timeout: int = 120
    pre: list = field(default_factory=list)    # extra yosys commands after prep

    def config(self) -> str:
        files = sorted(self.gen) + [os.path.basename(s) for s in self.srcs]
        reads = []
        for f in files:
            if f.endswith('.il'):
                reads.append(f'read_rtlil {f}')
        vfiles = [f for f in files if not f.endswith('.il')]
        reads.append('read -formal ' + ' '.join(vfiles))
        mode = self.mode
        eng = ENGINES[self.engine]
        opts = [f'mode {mode}', f'depth {self.depth}', f'timeout {self.timeout}']
        if self.engine == 'kind':
            mode = 'prove'
            opts[0] = 'mode prove'
        # memories are mapped to registers up front: witnesses then name plain
        # registers (needed for simulation replay) and trace conversion is robust
        script = '\n'.join(reads + [f'prep -top {self.top}', 'memory_map'] + list(self.pre))
        return (f'[options]\n' + '\n'.join(opts) + '\n\n[engines]\n' + eng + '\n\n[script]\n' + script +
                '\n\n[files]\n' + '\n'.join(files) + '\n')

    def key(self) -> str:
        h = [self.config()]
        for k in sorted(self.gen):
            h.append(k + '\0' + self.gen[k])
        for s in self.srcs:
            with open(s, 'rb') as f:
                h.append(os.path.basename(s) + '\0' + sha256_bytes(f.read()))
        return sha256_bytes('\n'.join(h).encode())[:20]


@dataclass
class Result:
    name: str
    key: str
    status: str                   # PASS | FAIL | UNKNOWN | ERROR | TIMEOUT
    mode: str
    engine: str
    seconds: float
    workdir: str
    trace: Optional[list] = None          # list of {signal: int} per step (VCD)
    traces: list = field(default_factory=list)   # cover mode: one per reached cover
    witness: Optional[dict] = None
    cached: bool = False
    log_tail: str = ''

    def to_json(self) -> dict:
        return {k: getattr(self, k) for k in ('name', 'key', 'status', 'mode', 'engine', 'seconds', 'workdir',
                                              'trace', 'traces', 'witness', 'cached', 'log_tail')}


# ----------------------------------------------------------------------------
# Trace parsing
# ----------------------------------------------------------------------------

def parse_vcd(path: str, top_only: bool = True) -> list[dict]:
    """Parse a sby VCD into per-step signal values (step k sampled at time 10k)."""
    ids: dict[str, list[str]] = {}
    scope: list[str] = []
    changes: list[tuple[int, str, int]] = []
    t = 0
    with open(path) as f:
        in_defs = True
        for line in f:
            line = line.strip()
            if not line:
                continue
            if in_defs:
                if line.startswith('$scope'):
                    scope.append(line.split()[2])
                elif line.startswith('$upscope'):
                    scope.pop()
                elif line.startswith('$var'):
                    parts = line.split()
                    code, name = parts[3], parts[4]
                    full = '.'.join(scope[1:] + [name])
                    ids.setdefault(code, []).append(full)
                elif line.startswith('$enddefinitions'):
                    in_defs = False
                continue
            if line[0] == '#':
                t = int(line[1:])
            elif line[0] in 'bB':
                val, code = line[1:].split()
                v = int(val.replace('x', '0').replace('z', '0'), 2) if val else 0
                changes.append((t, code, v))
            elif line[0] in '01xz':
                changes.append((t, line[1:], 1 if line[0] == '1' else 0))
    if not changes:
        return []
    last = max(c[0] for c in changes)
    nsteps = last // 10 + 1
    cur: dict[str, int] = {}
    steps = []
    ci = 0
    changes.sort(key=lambda c: c[0])
    for k in range(nsteps):
        while ci < len(changes) and changes[ci][0] <= 10 * k:
            _, code, v = changes[ci]
            for name in ids.get(code, []):
                cur[name] = v
            ci += 1
        snap = {n: v for n, v in cur.items() if (not top_only or '.' not in n)}
        steps.append(snap)
    return steps


def parse_yw(path: str) -> dict:
    """Parse a Yosys witness file into {'signals': [...], 'steps': [{path: value}]}."""
    with open(path) as f:
        d = json.load(f)
    sigs = d['signals']
    out_steps = []
    for st in d['steps']:
        bits = st['bits'][::-1]
        pos = 0
        vals = {}
        for s in sigs:
            w = s['width']
            chunk = bits[pos:pos + w]
            pos += w
            key = '.'.join(p.lstrip('\\') for p in s['path'])
            if 'x' in chunk or '?' in chunk:
                v = None
            else:
                v = int(chunk[::-1], 2) if chunk else 0
            if v is not None and s.get('offset', 0):
                v <<= s['offset']
                vals[key] = vals.get(key, 0) | v
            else:
                vals[key] = v if not s.get('offset', 0) else vals.get(key, 0)
        out_steps.append(vals)
    return {'signals': sigs, 'steps': out_steps}


# ----------------------------------------------------------------------------
# Running
# ----------------------------------------------------------------------------

class Runner:
    def __init__(self, cache_dir: str, jobs: int = 24):
        self.cache_dir = os.path.abspath(cache_dir)
        os.makedirs(self.cache_dir, exist_ok=True)
        self.jobs = jobs
        self.stats = {'run': 0, 'cached': 0, 'seconds': 0.0}

    def _one(self, task: Task) -> Result:
        """Run a task, or read its cached result.  A lock file per task keeps
        two processes sharing a cache from running the same task in the same
        directory at once; the second one then finds the first one's result."""
        import fcntl
        key = task.key()
        with open(os.path.join(self.cache_dir, key + '.lock'), 'w') as lk:
            fcntl.flock(lk, fcntl.LOCK_EX)
            return self._locked(task, key)

    def _locked(self, task: Task, key: str) -> Result:
        wd = os.path.join(self.cache_dir, key)
        rpath = os.path.join(wd, 'result.json')
        if os.path.exists(rpath):
            with open(rpath) as f:
                d = json.load(f)
            d['cached'] = True
            d['name'] = task.name
            return Result(**d)
        if os.path.exists(wd):
            shutil.rmtree(wd)
        os.makedirs(wd)
        for k, v in task.gen.items():
            with open(os.path.join(wd, k), 'w') as f:
                f.write(v)
        for s in task.srcs:
            shutil.copy(s, os.path.join(wd, os.path.basename(s)))
        with open(os.path.join(wd, 'task.sby'), 'w') as f:
            f.write(task.config())
        t0 = time.time()
        try:
            p = subprocess.run([tool('sby'), '-f', 'task.sby'], cwd=wd, capture_output=True, text=True,
                               env=tool_env(), timeout=task.timeout + 60)
            out = p.stdout + p.stderr
        except subprocess.TimeoutExpired:
            out = 'TIMEOUT (wall clock)'
        dt = time.time() - t0
        status = 'ERROR'
        sdir = os.path.join(wd, 'task')
        st = os.path.join(sdir, 'status')
        if os.path.exists(st):
            with open(st) as f:
                txt = f.read().split()
            if txt:
                status = txt[0]
        if 'TIMEOUT' in out and status not in ('PASS', 'FAIL'):
            status = 'TIMEOUT'
        if status == 'ERROR' and 'returned FAIL' in out:
            status = 'FAIL'          # engine verdict stands; only trace conversion failed
        trace, traces, wit = None, [], None
        edir = os.path.join(sdir, 'engine_0')
        if os.path.isdir(edir):
            if os.path.exists(os.path.join(edir, 'trace.vcd')):
                trace = parse_vcd(os.path.join(edir, 'trace.vcd'))
            if os.path.exists(os.path.join(edir, 'trace.yw')):
                wit = parse_yw(os.path.join(edir, 'trace.yw'))
                if trace is not None:
                    trace = trace[:len(wit['steps'])]     # VCD carries one extra post-state
            i = 0
            while os.path.exists(os.path.join(edir, f'trace{i}.vcd')):
                tr = parse_vcd(os.path.join(edir, f'trace{i}.vcd'))
                yw = os.path.join(edir, f'trace{i}.yw')
                if os.path.exists(yw):
                    tr = tr[:len(parse_yw(yw)['steps'])]
                traces.append(tr)
                i += 1
        tail = '\n'.join(out.strip().split('\n')[-12:])
        r = Result(task.name, key, status, task.mode, task.engine, round(dt, 3),
                   os.path.relpath(wd, self.cache_dir), trace, traces, wit, False, tail)
        if status in ('PASS', 'FAIL'):
            with open(rpath, 'w') as f:
                json.dump(r.to_json(), f)
        return r

    def run(self, tasks: list[Task]) -> dict[str, Result]:
        """Run tasks in parallel.  Tasks with the same content (the same key)
        run once; every name gets the result."""
        import dataclasses
        out: dict[str, Result] = {}
        if not tasks:
            return out
        by_key: dict[str, list[Task]] = {}
        for t in tasks:
            by_key.setdefault(t.key(), []).append(t)
        with cf.ThreadPoolExecutor(max_workers=self.jobs) as ex:
            futs = {ex.submit(self._one, ts[0]): ts for ts in by_key.values()}
            for fu in cf.as_completed(futs):
                ts = futs[fu]
                r = fu.result()
                for t in ts:
                    out[t.name] = r if t is ts[0] else dataclasses.replace(r, name=t.name)
                if r.cached:
                    self.stats['cached'] += 1
                else:
                    self.stats['run'] += 1
                    self.stats['seconds'] += r.seconds
        return out


def run_yosys(script: str, cwd: str, timeout: int = 300) -> str:
    p = subprocess.run([tool('yosys'), '-q', '-p', script], cwd=cwd, capture_output=True, text=True,
                       env=tool_env(), timeout=timeout)
    if p.returncode != 0:
        raise RuntimeError(f'yosys failed:\n{p.stdout}\n{p.stderr}')
    return p.stdout
