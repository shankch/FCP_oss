"""Fast replay of a compiled monitor on a long recorded trace, with Verilator.

The monitor of a reading is the same Verilog module that every engine uses.
Icarus interprets it, which costs about a millisecond per cycle once
quantifiers over strings unroll into tens of thousands of wires.  Here the
module is compiled to C++ once per monitor text (cached under .fcp-cache/vl)
and replayed on a binary trace file: per cycle, every input port as 32-bit
little-endian words.  The probes and their reading are those of
fcp.software.check; every rigid valuation replays the trace on a fresh
instance.  Up to `keep` failing cycles are reported per probe, so a caller
can show the simplest failing call rather than the first.
"""
from __future__ import annotations

import array
import hashlib
import os
import shutil
import subprocess
import tempfile
import threading

from .agents import IVERILOG, ROOT

VERILATOR = os.path.join(os.path.dirname(IVERILOG), 'verilator')
CACHE = os.path.join(ROOT, '.fcp-cache', 'vl')
VERSION = '2'
_LOCK = threading.Lock()


def available() -> bool:
    return os.path.exists(VERILATOR)


def _words(w: int) -> int:
    return (w + 31) // 32


def vlname(name: str) -> str:
    """The C++ member Verilator generates for a port: every '__' is escaped."""
    out, i = [], 0
    while i < len(name):
        if name.startswith('__', i):
            out.append('___05F')
            i += 2
        else:
            out.append(name[i])
            i += 1
    return ''.join(out)


def _harness(mon, probes) -> str:
    mod = f'V{mon.module}'
    ports = list(mon.ports_in)
    total = sum(_words(w) for _, w in ports)
    out = [f'#include "{mod}.h"', '#include "verilated.h"', '#include <cstdio>', '#include <cstdint>',
           '#include <cstdlib>', '#include <vector>', '',
           'int main(int argc, char** argv) {',
           '  const char* path = argv[1];',
           '  long n = atol(argv[2]);',
           '  long keep = atol(argv[3]);',
           f'  const long W = {total};',
           '  std::vector<uint32_t> buf((size_t)n * W);',
           '  FILE* f = fopen(path, "rb");',
           '  if (!f || fread(buf.data(), 4, buf.size(), f) != buf.size()) { fprintf(stderr, "bad trace\\n"); return 2; }',
           '  fclose(f);',
           f'  const int NP = {len(probes)};',
           '  std::vector<long> first(NP, -1), count(NP, 0);',
           '  std::vector<std::vector<long>> fails(NP);',
           '  // a cycle counts once, whichever rigid valuations it held or failed for',
           '  std::vector<std::vector<char>> hit(NP, std::vector<char>((size_t)n, 0));',
           '  VerilatedContext ctx;']
    ind = '  '
    for port, w, lo, hi in mon.rigid_ports:
        out.append(f'{ind}for (long r_{port} = {lo}; r_{port} <= {hi}; r_{port}++) {{')
        ind += '  '
    out.append(f'{ind}{mod}* top = new {mod}(&ctx);')
    for port, w, lo, hi in mon.rigid_ports:
        out.append(f'{ind}top->{vlname(port)} = (uint64_t)r_{port} & ((1ULL << {w}) - 1);')
    for port, w in mon.nondet_ports:
        if w > 64:
            out.append(f'{ind}for (int q = 0; q < {_words(w)}; q++) top->{vlname(port)}[q] = 0;')
        else:
            out.append(f'{ind}top->{vlname(port)} = 0;')
    out += [f'{ind}top->clk = 0;', f'{ind}top->eval();', f'{ind}for (long k = 0; k < n; k++) {{',
            f'{ind}  const uint32_t* x = &buf[k * W];']
    off = 0
    for name, w in ports:
        nw, m = _words(w), vlname(name)
        if w > 64:
            out.append(f'{ind}  for (int q = 0; q < {nw}; q++) top->{m}[q] = x[{off} + q];')
        elif w > 32:
            out.append(f'{ind}  top->{m} = ((uint64_t)x[{off + 1}] << 32) | x[{off}];')
        else:
            out.append(f'{ind}  top->{m} = x[{off}];')
        off += nw
    out.append(f'{ind}  top->eval();')
    for j, (_, kind, wire) in enumerate(probes):
        if kind in ('ok', 'aok'):
            out.append(f'{ind}  if (top->{vlname(wire)} != 1 && !hit[{j}][k]) {{ hit[{j}][k] = 1; '
                       f'if (first[{j}] < 0 || k < first[{j}]) first[{j}] = k; '
                       f'count[{j}]++; if ((long)fails[{j}].size() < keep) fails[{j}].push_back(k); }}')
        else:
            out.append(f'{ind}  if (top->{vlname(wire)} == 1 && !hit[{j}][k]) {{ hit[{j}][k] = 1; count[{j}]++; }}')
    out += [f'{ind}  top->clk = 1; top->eval(); top->clk = 0; top->eval();', f'{ind}}}', f'{ind}delete top;']
    for _ in mon.rigid_ports:
        ind = ind[:-2]
        out.append(f'{ind}}}')
    out += ['  for (int j = 0; j < NP; j++) {',
            '    printf("P %d %ld %ld", j, first[j], count[j]);',
            '    for (long c : fails[j]) printf(" %ld", c);',
            '    printf("\\n");',
            '  }',
            '  return 0;',
            '}']
    return '\n'.join(out) + '\n'


def build(mon, probes) -> str:
    """The path of the compiled replay binary for this monitor (built once)."""
    h = hashlib.sha256((VERSION + mon.text + repr(probes) + repr(mon.ports_in) + repr(mon.rigid_ports) +
                        repr(mon.nondet_ports)).encode()).hexdigest()[:20]
    d = os.path.join(CACHE, h)
    exe = os.path.join(d, 'obj', 'replay')
    with _LOCK:
        if os.path.exists(exe):
            return exe
        os.makedirs(CACHE, exist_ok=True)
        tmp = tempfile.mkdtemp(prefix=f'{h}.', dir=CACHE)
        with open(os.path.join(tmp, 'mon.v'), 'w') as f:
            f.write(mon.text)
        with open(os.path.join(tmp, 'replay.cpp'), 'w') as f:
            f.write(_harness(mon, probes))
        p = subprocess.run([VERILATOR, '--cc', '--exe', '--build', '-j', '8', '-Wno-fatal', '-Wno-lint',
                            '-Wno-style', '--x-initial', 'fast', '--top-module', mon.module, '-CFLAGS', '-O1',
                            '-o', 'replay', '--Mdir', os.path.join(tmp, 'obj'), os.path.join(tmp, 'mon.v'),
                            os.path.join(tmp, 'replay.cpp')], capture_output=True, text=True)
        if p.returncode != 0 or not os.path.exists(os.path.join(tmp, 'obj', 'replay')):
            shutil.rmtree(tmp, ignore_errors=True)
            raise RuntimeError(f'verilator failed for {mon.module}: {p.stderr[-2000:]}')
        try:
            os.rename(tmp, d)                      # atomic; another process may have won the race
        except OSError:
            shutil.rmtree(tmp, ignore_errors=True)
        return exe


def replay(mon, probes, cols: dict[str, list[int]], keep: int = 0) -> list[tuple[int, int, list[int]]]:
    """(first failing cycle or -1, count, up to keep failing cycles) per probe;
    for a trigger or cover probe, count is the number of cycles in which it held."""
    exe = build(mon, probes)
    n = len(cols['rst_n'])
    a = array.array('I')
    names = list(mon.ports_in)
    columns = [cols.get(name) for name, _ in names]
    for k in range(n):
        for (name, w), col in zip(names, columns):
            v = col[k] if col is not None else 0
            for _ in range(_words(w)):
                a.append(v & 0xFFFFFFFF)
                v >>= 32
    with tempfile.TemporaryDirectory(prefix='fcp_vl_') as d:
        p = os.path.join(d, 'trace.bin')
        with open(p, 'wb') as f:
            a.tofile(f)
        r = subprocess.run([exe, p, str(n), str(keep)], capture_output=True, text=True, check=True)
    out = []
    for line in r.stdout.splitlines():
        if line.startswith('P '):
            x = line.split()
            out.append((int(x[2]), int(x[3]), [int(c) for c in x[4:]]))
    return out
