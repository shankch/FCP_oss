"""FCP agent protocol: roles, context isolation and recorded runs.

Agents are untrusted producers of IR.  The protocol fixes, for every role,
what the agent may see (its workspace), what it must produce (a schema-valid
artifact) and which mechanical checks it may run on its own output.  The
central rule is context isolation: formalizers never see the RTL (they cannot
"teach to the test"), RTL generators never see the formalizations, and two
formalizers of the same requirements never see each other.

Every run is recorded (role, model, prompt, prompt hash, outputs, hashes) so
the study can be replayed without the agents, or re-run with another model.
"""
from __future__ import annotations

import datetime
import json
import os
import shutil

from .ir import sha256_bytes, sha256_file

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FCP = os.path.join(ROOT, 'bin', 'fcp')
IVERILOG = os.path.join(ROOT, '.tools', 'oss-cad-suite', 'bin', 'iverilog')

STYLE = {
    'agent_a': 'Prefer direct relations between interface signals and the standard patterns; '
               'introduce ghost state only where a requirement cannot be stated otherwise.',
    'agent_b': 'Prefer an explicit specification model: ghost state driven by the inputs (e.g. an occupancy '
               'counter or protocol phase), with every output checked against the model.',
    'variant': 'Prefer direct relations between interface signals and the standard patterns; '
               'introduce ghost state only where a requirement cannot be stated otherwise.',
}

FORMALIZER = """You are an independent formal-verification engineer acting as an FCP formalization agent.

Workspace: {ws}
It contains spec.md (the specification), design.yaml (interface and parameters),
requirements.yaml (the atomic requirements to formalize, each with a verbatim
source quote) and docs/IR_spec.md (the FCP IR and the FCP-PL property language).{extra_docs}

Task: write {ws}/formal/{set}.yaml, a formalization set (FCP IR v0.1, `set: {set}`)
for every requirement in requirements.yaml, derived from the specification text.

Rules:
1. Read docs/IR_spec.md first. Use only the operators and patterns it defines.
2. Work only from the files in the workspace. There is no RTL and you must not
   look for one; do not read or list any file outside {ws}.
3. Every requirement must appear as one or more formal items carrying `req: <id>`
   (properties for guarantees, assumptions for environment obligations,
   dont_cares for intentionally unconstrained outputs, scenarios for behaviours
   that must be possible), or under `unformalized` with a reason (use
   `covered_by` if other items realize it).
4. Formalize what the text says. Where it is ambiguous or contradictory, choose
   the most literal reading and say so in the item's `note`. Do not silently
   repair the specification.
5. Every item id starts with "{prefix}-". Set `origin: {{kind: agent, role: formalizer, id: {set}}}`.
6. Validate with `{fcp} lint {ws}` until it reports no errors, and read back the
   English rendering with `{fcp} explain {ws} --set {set}` to check that every
   item means what you intend.
7. Style: {style}
8. For every phrase that requirements.yaml flags under `ambiguity`, record the
   reading you took under `decisions`: `{{req: <id>, phrase: <the phrase>,
   reading: <its number in the list, from 1>}}`.

When done, reply with a short summary: number of items, requirements left
unformalized and why, and any problems you noticed in the specification."""

DECOMPOSER = """You are an FCP specification agent.

Workspace: {ws}
It contains spec.md (a hardware specification), design.yaml (interface) and
docs/IR_spec.md (section 2 describes requirements.yaml).

Task: decompose spec.md into atomic requirements.
1. Write {ws}/requirements_draft.yaml:
     fcp: "0.1"
     design: {design}
     origin: {{kind: agent, role: decomposer, id: decomposer}}
     requirements:
       - id: R-<AREA>-<n>
         doc: SPEC
         quote: <verbatim sentence or clause copied from spec.md>
         text: <atomic, self-contained restatement>
         kind: guarantee | assumption | dont_care | scenario | definition | non_functional
         depends: [<ids>]                      # optional
         ambiguity: [{{phrase: ..., readings: [..., ...]}}]   # optional
         confidence: high | medium | low
   Do not write line numbers.
2. Run `{fcp} anchor {ws} {ws}/requirements_draft.yaml --out {ws}/requirements.yaml`.
   It computes line spans and rejects any quote that is not verbatim; fix rejected
   quotes and re-run until every requirement is anchored.

Guidance: one requirement per independently checkable obligation. Use kind
`assumption` for obligations on the environment (other blocks, requesters,
the bus). Flag every ambiguity, vague phrase, permission ("may"), and every
pair of statements that seem to contradict each other (record contradictions
as an ambiguity on both requirements, naming the other one). Do not read any
file outside {ws}.

When done, reply with a short summary, including every contradiction or gap
you found in the specification."""

RTLGEN = """You are an RTL design engineer.

Workspace: {ws}
It contains spec.md (the specification) and design.yaml (the interface).{extra_docs}

Task: implement the specified block as synthesizable Verilog-2005 in
{ws}/rtl/{top}.v, top module `{top}`, with exactly the ports listed in
design.yaml (same names, directions and widths{param_note}).

Constraints: single clock `clk`, synchronous active-low reset `rst_n` as the
spec describes, no initial blocks, no SystemVerilog-only syntax, no
simulation-only code. You may check syntax with
`{iverilog} -g2005 -o /dev/null {ws}/rtl/*.v` and may write your own
testbench under {ws}/tb/. Do not read any file outside {ws}.

When done, reply with a short summary of your design decisions and of any
ambiguities in the specification you had to resolve."""


LABELER = """You are an FCP labeling agent.

Workspace: {ws}
It contains frame.md (the text adapter: how responses are split into units, and
the definition of every label) and units/<response>.tsv, one file per response
with one unit per line: "<index><TAB><text>".

Task: for every unit of every response, decide which of these labels hold:
{labels}.
Use only the definitions in frame.md. Judge each unit by its own text; read the
neighbouring units only for context. The labels subject, price and signoff are
computed by a rule; do not decide them.

Write {ws}/labels.yaml:
  <response>:
    <index>: [<label>, ...]      # [] when no label holds

Do not read or list any file outside {ws}. Reply with a one-line summary."""


def _copy(src: str, dst: str):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy(src, dst)


def workspace(bundle: str, role: str, dest: str, set_name: str = '', extra_docs: dict = None) -> str:
    """Create a sanitized workspace exposing only what the role may see."""
    if os.path.exists(dest):
        shutil.rmtree(dest)
    os.makedirs(dest)
    _copy(os.path.join(bundle, 'spec.md'), os.path.join(dest, 'spec.md'))
    _copy(os.path.join(bundle, 'design.yaml'), os.path.join(dest, 'design.yaml'))
    if role != 'rtlgen':
        # every document the design cites must be where design.yaml says it is
        # (the frame, for instance), or the agent cannot run lint
        import yaml
        with open(os.path.join(bundle, 'design.yaml')) as f:
            for doc in yaml.safe_load(f).get('docs') or []:
                if doc['path'] != 'spec.md':
                    _copy(os.path.join(bundle, doc['path']), os.path.join(dest, doc['path']))
    _copy(os.path.join(ROOT, 'docs', 'IR_spec.md'), os.path.join(dest, 'docs', 'IR_spec.md'))
    for name, path in (extra_docs or {}).items():
        _copy(path, os.path.join(dest, 'docs', name))
    if role == 'formalizer':
        _copy(os.path.join(bundle, 'requirements.yaml'), os.path.join(dest, 'requirements.yaml'))
        os.makedirs(os.path.join(dest, 'formal'))
    if role == 'rtlgen':
        os.remove(os.path.join(dest, 'docs', 'IR_spec.md'))
        os.makedirs(os.path.join(dest, 'rtl'))
    return dest


def prompt(role: str, ws: str, design: str, set_name: str = '', prefix: str = '', top: str = '',
           extra_docs: dict = None, param_note: str = '') -> str:
    extra = ''
    if extra_docs:
        extra = '\nAlso available: ' + ', '.join(f'docs/{n}' for n in extra_docs) + '.'
    if role == 'formalizer':
        return FORMALIZER.format(ws=ws, set=set_name, prefix=prefix, fcp=FCP, style=STYLE[set_name],
                                 extra_docs=extra)
    if role == 'decomposer':
        return DECOMPOSER.format(ws=ws, design=design, fcp=FCP)
    if role == 'rtlgen':
        return RTLGEN.format(ws=ws, top=top, iverilog=IVERILOG, extra_docs=extra, param_note=param_note)
    if role == 'labeler':
        from .text import LABELS, RULE_LABELS
        return LABELER.format(ws=ws, labels=', '.join(l for l in LABELS if l not in RULE_LABELS))
    raise KeyError(role)


def label_workspace(bundle: str, responses: list[str], dest: str) -> str:
    """Workspace for a labeler: the label definitions and the segmented units.
    A labeler never sees the prompt or its requirements."""
    from .text import segment
    if os.path.exists(dest):
        shutil.rmtree(dest)
    os.makedirs(os.path.join(dest, 'units'))
    _copy(os.path.join(bundle, 'frame.md'), os.path.join(dest, 'frame.md'))
    for r in responses:
        with open(os.path.join(bundle, 'responses', f'{r}.md')) as f:
            units = segment(f.read())
        with open(os.path.join(dest, 'units', f'{r}.tsv'), 'w') as f:
            f.write(''.join(f'{i}\t{u}\n' for i, u in enumerate(units)))
    return dest


def record(bundle: str, role: str, name: str, model: str, prompt_text: str, outputs: dict, summary: str):
    """Store an agent run (prompt, outputs, hashes) inside the bundle."""
    d = os.path.join(bundle, 'agents', name)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, 'prompt.md'), 'w') as f:
        f.write(prompt_text)
    with open(os.path.join(d, 'summary.md'), 'w') as f:
        f.write(summary)
    files = {}
    for rel, src in outputs.items():
        dst = os.path.join(d, os.path.basename(rel))
        if os.path.exists(src):
            shutil.copy(src, dst)
            files[rel] = sha256_file(dst)
    rec = {'role': role, 'name': name, 'model': model,
           'date': datetime.datetime.now().isoformat(timespec='seconds'),
           'prompt_sha256': sha256_bytes(prompt_text.encode()), 'outputs': files}
    if getattr(summary, 'meta', None):         # what the run cost (fcp.review.run_agent)
        rec['run'] = summary.meta
    with open(os.path.join(d, 'run.json'), 'w') as f:
        json.dump(rec, f, indent=1)
    return rec
