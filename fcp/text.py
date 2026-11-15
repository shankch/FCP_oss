"""FCP text adapter: a text response as a trace, and the trace as a chip.

  segment(text)        deterministic split into units (frame.md, "Units")
  rule_labels(units)   the labels a deterministic rule decides: subject, price, signoff
  merge(a, b)          per-unit agreement of two independent labelers, and the
                       disputed (unit, label) pairs
  replay_rtl(...)      a Verilog module that replays the labelled units, one per
                       cycle after reset, and then raises eos: the response "as a chip"

The labels are the only interpretive step.  Everything downstream of them
(monitors, proofs, comparisons) is exact, so each label records who decided it:
a rule, or two labelers that never see the prompt's requirements.

  python -m fcp.text segment <response.md>          numbered units
  python -m fcp.text build <bundle> <labels.yaml>   rtl/<name>_la.v, _lb.v (and _lh.v: adjudicator)
"""
from __future__ import annotations

import os
import re
import sys

import yaml

LABELS = ['subject', 'greet', 'feature', 'benefit', 'price', 'offer', 'ends', 'rival', 'cta', 'signoff']
RULE_LABELS = {'subject', 'price', 'signoff'}
MAX_UNITS = 14
SIGNOFF_NAME = 'The Aurora Team'

_SENT = re.compile(r'(?<=[.!?])\s+(?=\S)')


def segment(text: str) -> list[str]:
    units = []
    for line in text.split('\n'):
        line = line.strip()
        if line:
            units += [u.strip() for u in _SENT.split(line) if u.strip()]
    return units


def _bare(u: str) -> str:
    return re.sub(r'^[\s\-–—*_]+|[\s.,!*_]+$', '', u)


def rule_labels(units: list[str]) -> list[set]:
    out = [set() for _ in units]
    for i, u in enumerate(units):
        if re.match(r'\s*\**subject\s*:', u, re.I):
            out[i].add('subject')
        if re.search(r'\$\s?249(?:\.00)?(?!\d)', u):
            out[i].add('price')
        if _bare(u) == SIGNOFF_NAME:
            out[i].add('signoff')
            # a short closing word on the line before the name ("Warmly,")
            if i > 0 and units[i - 1].rstrip().endswith(',') and len(units[i - 1].split()) <= 4:
                out[i - 1].add('signoff')
    return out


def merge(a: list[set], b: list[set]) -> list[dict]:
    """Disputed (unit, label) pairs between two labelers."""
    return [{'unit': i, 'label': l, 'a': l in x, 'b': l in y}
            for i, (x, y) in enumerate(zip(a, b)) for l in LABELS if (l in x) != (l in y)]


def render_trace(trace: list, units: list[str] | None = None) -> list[str]:
    """A solver trace as the response skeleton it encodes: one line per unit
    with its labels (the text analogue of a waveform)."""
    out = []
    for st in trace:
        if str(st.get('rst_n')) == '0':
            continue
        if str(st.get('eos')) == '1':
            out.append('(end of response)')
            break
        i = len(out)
        labs = [l for l in LABELS if str(st.get(l)) == '1']
        txt = f'  "{units[i]}"' if units and i < len(units) else ''
        out.append(f'unit {i}: {" ".join(labs) or "-"}{txt}')
    return out


def _vstr(s: str) -> str:
    return re.sub(r'[^\x20-\x7e]', '?', s).replace('*/', '* /')


def replay_rtl(name: str, units: list[str], labels: list[set], who: str) -> str:
    n = len(units)
    if n > MAX_UNITS:
        raise ValueError(f'{name}: {n} units exceed the frame limit of {MAX_UNITS}')
    L = len(LABELS)
    lines = [f'// Response "{name}" replayed as a chip by the FCP text adapter (frame.md).',
             f'// Labels: {who}. {n} units; unit i drives the outputs in cycle i+1 (cycle 0 is reset),',
             '// then eos rises and stays high with every label false. Generated; do not edit.',
             'module response (input clk, input rst_n, ' + ', '.join(f'output {l}' for l in LABELS) + ', output eos);',
             '  reg [3:0] k;  // index of the current unit',
             '  always @(posedge clk)',
             "    if (!rst_n) k <= 4'd0;",
             f"    else if (k != 4'd{n}) k <= k + 4'd1;",
             f'  reg [{L - 1}:0] lab;  // {{{", ".join(LABELS)}}}',
             '  always @* begin',
             '    case (k)']
    for i, (u, ls) in enumerate(zip(units, labels)):
        bits = ''.join('1' if l in ls else '0' for l in LABELS)
        lines.append(f"      4'd{i}: lab = {L}'b{bits};  /* {_vstr(u[:70])} */")
    lines += [f"      default: lab = {L}'b0;",
              '    endcase',
              '  end',
              f"  assign eos = (k == 4'd{n});",
              f'  assign {{{", ".join(LABELS)}}} = lab;',
              'endmodule']
    return '\n'.join(lines) + '\n'


def build(bundle: str, labels_path: str) -> list[str]:
    """Write one replay chip per labeler, and one for the adjudicator's labels
    when present (rule labels are shared)."""
    with open(labels_path) as f:
        d = yaml.safe_load(f)
    name = d['response']
    units = [u['text'] for u in d['units']]
    rules = rule_labels(units)
    out = []
    for who in [w for w in ('a', 'b', 'h') if any(w in u for u in d['units'])]:
        labs = [set(r) | (set(u.get(who) or []) - RULE_LABELS) for r, u in zip(rules, d['units'])]
        rel = f'rtl/{name}_l{who}.v'
        with open(os.path.join(bundle, rel), 'w') as f:
            f.write(replay_rtl(name, units, labs, f'rules + {"adjudicator" if who == "h" else "labeler " + who.upper()} '
                                                  f'({d.get(f"labeler_{who}", "?")})'))
        out.append(rel)
    return out


if __name__ == '__main__':
    if sys.argv[1] == 'segment':
        with open(sys.argv[2]) as f:
            for i, u in enumerate(segment(f.read())):
                print(f'{i}\t{u}')
    elif sys.argv[1] == 'build':
        print('\n'.join(build(sys.argv[2], sys.argv[3])))
