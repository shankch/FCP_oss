"""The FCP intermediate representation: loading, validation and provenance.

A design bundle is a directory with

  design.yaml          interface, parameters, environment, RTL variants, docs
  requirements.yaml    atomic requirements, each pinned to a verbatim source span
  formal/<set>.yaml    one or more independent formalization sets

All three are validated against the versioned JSON Schema in
``fcp/schema/fcp-ir.schema.json`` and cross-checked (every formal item must
cite an existing requirement, every quote must occur verbatim at the cited
lines of the cited document, ...).  Every artifact is content-addressed so
evidence can name exactly what it was computed from.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass, field
from typing import Optional

import jsonschema
import yaml

from .lang import FcpError, clog2, const_eval, seq_len_port

IR_VERSION = '0.1'
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), 'schema', 'fcp-ir.schema.json')


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(path: str) -> str:
    with open(path, 'rb') as f:
        return sha256_bytes(f.read())


def canon(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), default=str)


def digest(obj) -> str:
    return sha256_bytes(canon(obj).encode())[:16]


@dataclass
class Signal:
    name: str
    dir: str          # in | out
    width: int
    desc: str = ''


@dataclass
class Reset:
    name: str
    active_low: bool


@dataclass
class Interface:
    clock: str
    reset: Reset
    params: dict[str, int]
    signals: list[Signal]
    # sequence signals (strings, lists): name -> (slot width, max length); each
    # is carried by two of the signals above, name (packed slots) and name__len
    seqs: dict[str, tuple[int, int]] = field(default_factory=dict)
    # groups of sequence signals that always have the same length (the fields
    # of a list of records): group name -> its signals
    groups: dict[str, list[str]] = field(default_factory=dict)

    @property
    def inputs(self) -> list[Signal]:
        return [s for s in self.signals if s.dir == 'in' and s.name != self.clock]

    @property
    def outputs(self) -> list[Signal]:
        return [s for s in self.signals if s.dir == 'out']

    def sig(self, name: str) -> Signal:
        for s in self.signals:
            if s.name == name:
                return s
        raise KeyError(name)


@dataclass
class RtlVariant:
    name: str
    top: str
    files: list[str]
    params: dict[str, object]
    port_map: dict[str, str]
    desc: str = ''
    origin: str = ''


@dataclass
class Requirement:
    id: str
    doc: str
    lines: list[int]
    quote: str
    text: str
    kind: str
    depends: list[str] = field(default_factory=list)
    ambiguity: list[dict] = field(default_factory=list)
    confidence: str = 'high'
    note: str = ''


@dataclass
class Bundle:
    root: str
    design: str
    raw_design: dict
    iface: Interface
    env: dict
    docs: dict[str, dict]               # id -> {path, sha256, lines}
    rtl: dict[str, RtlVariant]
    requirements: dict[str, Requirement]
    req_origin: dict
    fsets: dict[str, dict]              # set name -> raw formalization set
    issues: list[dict] = field(default_factory=list)   # validation findings (non-fatal)
    frame: list[dict] = field(default_factory=list)    # design-level frame items (see _inject_frame)

    @property
    def frame_ids(self) -> set[str]:
        return {it['id'] for it in self.frame}

    def path(self, rel: str) -> str:
        return os.path.join(self.root, rel)

    def fingerprint(self) -> dict:
        """Content hashes of everything the analyses depend on."""
        fp = {'design.yaml': sha256_file(self.path('design.yaml')),
              'requirements.yaml': sha256_file(self.path('requirements.yaml'))}
        for d in self.docs.values():
            fp[d['path']] = d['sha256']
        for v in self.rtl.values():
            for f in v.files:
                fp[f] = sha256_file(self.path(f))
        for name in self.fsets:
            fp[f'formal/{name}.yaml'] = sha256_file(self.path(f'formal/{name}.yaml'))
        return fp


_schema_cache = None


def schema() -> dict:
    global _schema_cache
    if _schema_cache is None:
        with open(SCHEMA_PATH) as f:
            _schema_cache = json.load(f)
    return _schema_cache


def _validate(obj: dict, defname: str, where: str):
    s = schema()
    sub = {'$ref': f'#/$defs/{defname}', '$defs': s['$defs']}
    try:
        jsonschema.validate(obj, sub)
    except jsonschema.ValidationError as e:
        loc = '/'.join(str(p) for p in e.absolute_path)
        raise FcpError(f'{where}: schema violation at {loc or "<root>"}: {e.message}') from None


def load_yaml(path: str) -> dict:
    with open(path) as f:
        return yaml.safe_load(f) or {}


def _norm_ws(s: str) -> str:
    return re.sub(r'\s+', ' ', s).strip()


def _inject_frame(fs: dict, frame: list[dict], where: str):
    """Prepend the design's frame items to a formalization set's properties.

    The frame states how behaviours are encoded on the interface (for a text
    response: units, end of response, labels cleared after the end).  It is
    part of the semantics adapter, not of any reading, so every set carries
    the same items: spec-only analyses assume them (they range over
    well-formed behaviours only) and verification checks them on the RTL."""
    if not frame:
        return
    own = {it['id'] for sec in ('assumptions', 'properties', 'scenarios', 'dont_cares')
           for it in fs.get(sec, []) or []}
    clash = own & {it['id'] for it in frame}
    if clash:
        raise FcpError(f'{where}: ids {", ".join(sorted(clash))} are reserved by the design frame')
    fs['properties'] = [dict(it) for it in frame] + list(fs.get('properties') or [])


def load_bundle(root: str, sets: Optional[list[str]] = None) -> Bundle:
    root = os.path.abspath(root)
    dpath = os.path.join(root, 'design.yaml')
    d = load_yaml(dpath)
    _validate(d, 'design', dpath)
    issues: list[dict] = []

    ifc = d['interface']
    params = {}
    for k, v in (ifc.get('params') or {}).items():
        params[k] = const_eval(v, params)
    sigs, seqs, groups = [], {}, {}
    for s in ifc['signals']:
        w = const_eval(s.get('width', 1), params)
        if 'length' in s:
            n = const_eval(s['length'], params)
            if n < 1:
                raise FcpError(f'{dpath}: signal {s["name"]}: length must be at least 1')
            sigs.append(Signal(s['name'], s['dir'], n * w, s.get('desc', '')))
            sigs.append(Signal(seq_len_port(s['name']), s['dir'], max(1, clog2(n + 1)), f'length of {s["name"]}'))
            seqs[s['name']] = (w, n)
            if s.get('group'):
                groups.setdefault(s['group'], []).append(s['name'])
        else:
            if s.get('group'):
                raise FcpError(f'{dpath}: signal {s["name"]}: only a sequence signal (with length) can be in a group')
            sigs.append(Signal(s['name'], s['dir'], w, s.get('desc', '')))
    for g, members in groups.items():
        sd = {s['name']: s for s in ifc['signals']}
        if len({sd[m]['dir'] for m in members}) > 1 or len({seqs[m][1] for m in members}) > 1:
            raise FcpError(f'{dpath}: group {g}: its signals must have one direction and one length')
    names = [s.name for s in sigs]
    if len(set(names)) != len(names):
        raise FcpError(f'{dpath}: duplicate interface signal names')
    rst = ifc['reset']
    iface = Interface(ifc['clock'], Reset(rst['name'], bool(rst.get('active_low', False))), params, sigs, seqs,
                      groups)
    for needed in (iface.clock, iface.reset.name):
        if needed not in names:
            raise FcpError(f'{dpath}: clock/reset signal {needed!r} is not declared in interface.signals')

    docs = {}
    for doc in d.get('docs', []):
        p = os.path.join(root, doc['path'])
        with open(p, encoding='utf-8') as f:
            text = f.read()
        docs[doc['id']] = {'path': doc['path'], 'sha256': sha256_bytes(text.encode()),
                           'lines': text.split('\n')}

    rtl = {}
    for name, v in (d.get('rtl') or {}).items():
        rtl[name] = RtlVariant(name, v['top'], list(v['files']), dict(v.get('params') or {}),
                               dict(v.get('port_map') or {}), v.get('desc', ''), v.get('origin', ''))

    rpath = os.path.join(root, 'requirements.yaml')
    rq = load_yaml(rpath)
    _validate(rq, 'requirements', rpath)
    reqs = {}
    for r in rq['requirements']:
        if r['id'] in reqs:
            raise FcpError(f'{rpath}: duplicate requirement id {r["id"]}')
        req = Requirement(r['id'], r['doc'], list(r['lines']), r['quote'], r['text'], r['kind'],
                          list(r.get('depends') or []), list(r.get('ambiguity') or []),
                          r.get('confidence', 'high'), r.get('note', ''))
        reqs[req.id] = req
        # provenance integrity: the quote must occur verbatim at the cited lines
        if req.doc not in docs:
            issues.append({'kind': 'provenance', 'severity': 'error', 'req': req.id,
                           'msg': f'cites unknown document {req.doc!r}'})
            continue
        lines = docs[req.doc]['lines']
        lo, hi = req.lines[0], req.lines[-1]
        if not (1 <= lo <= hi <= len(lines)):
            issues.append({'kind': 'provenance', 'severity': 'error', 'req': req.id,
                           'msg': f'cites lines {lo}-{hi} outside document ({len(lines)} lines)'})
            continue
        span = _norm_ws(' '.join(lines[lo - 1:hi]))
        if _norm_ws(req.quote) not in span:
            issues.append({'kind': 'provenance', 'severity': 'error', 'req': req.id,
                           'msg': f'quote does not occur verbatim in {req.doc} lines {lo}-{hi}'})
    for req in reqs.values():
        for dep in req.depends:
            if dep not in reqs:
                issues.append({'kind': 'reference', 'severity': 'error', 'req': req.id,
                               'msg': f'depends on unknown requirement {dep}'})
    frame = list(d.get('frame') or [])
    for it in frame:
        if it.get('req') not in reqs:
            issues.append({'kind': 'reference', 'severity': 'error', 'item': it['id'],
                           'msg': f'frame item cites unknown requirement {it.get("req")}'})

    fsets = {}
    fdir = os.path.join(root, 'formal')
    avail = sorted(f[:-5] for f in os.listdir(fdir) if f.endswith('.yaml')) if os.path.isdir(fdir) else []
    for name in (sets if sets is not None else avail):
        fp = os.path.join(fdir, f'{name}.yaml')
        fs = load_yaml(fp)
        _validate(fs, 'formalization', fp)
        if fs.get('set') != name:
            raise FcpError(f'{fp}: set name {fs.get("set")!r} does not match file name')
        ids = set()
        for section in ('assumptions', 'properties', 'scenarios', 'dont_cares'):
            for it in fs.get(section, []) or []:
                if it['id'] in ids:
                    raise FcpError(f'{fp}: duplicate id {it["id"]}')
                ids.add(it['id'])
                rid = it.get('req')
                if rid is not None and rid not in reqs:
                    issues.append({'kind': 'reference', 'severity': 'error', 'set': name, 'item': it['id'],
                                   'msg': f'cites unknown requirement {rid}'})
                if rid is None and section == 'assumptions':
                    issues.append({'kind': 'unjustified-assumption', 'severity': 'warning', 'set': name,
                                   'item': it['id'],
                                   'msg': 'assumption is not traced to any requirement; it needs human sign-off'})
        for u in fs.get('unformalized', []) or []:
            if u['req'] not in reqs:
                issues.append({'kind': 'reference', 'severity': 'error', 'set': name,
                               'msg': f'unformalized entry cites unknown requirement {u["req"]}'})
        _inject_frame(fs, frame, fp)
        fsets[name] = fs

    return Bundle(root, d['design'], d, iface, dict(d.get('environment') or {}), docs, rtl, reqs,
                  dict(rq.get('origin') or {}), fsets, issues, frame)


def rtl_param_values(b: Bundle, v: RtlVariant) -> dict[str, int]:
    return {k: const_eval(x, b.iface.params) for k, x in v.params.items()}


def load_fset(b: 'Bundle', path: str, name: Optional[str] = None) -> str:
    """Validate a formalization set file and attach it to a loaded bundle."""
    fs = load_yaml(path)
    _validate(fs, 'formalization', path)
    name = name or fs['set']
    fs['set'] = name
    for section in ('assumptions', 'properties', 'scenarios', 'dont_cares'):
        for it in fs.get(section, []) or []:
            rid = it.get('req')
            if rid is not None and rid not in b.requirements:
                b.issues.append({'kind': 'reference', 'severity': 'error', 'set': name, 'item': it['id'],
                                 'msg': f'cites unknown requirement {rid}'})
    _inject_frame(fs, b.frame, path)
    b.fsets[name] = fs
    return name
