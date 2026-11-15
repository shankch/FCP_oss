#!/usr/bin/env python3
"""One more reader per answer, on the ten code tasks.

On the gift card two readers and three models took the same side of a phrase
that the decomposer had flagged, and FCP certified three violations
(docs/FCP_code.md, section 8.2).  One more reader, told to take the other
side, differed from the two on the requirements that the answer decides;
held as depending on the question, none of the three was certified.  That
was measured on one task.  This script measures it on all ten.

The stored readings of seven tasks do not say which listed reading of a
flagged phrase their reader took, so no reader here is told "the other
side".  A task gets one more reader per position in the lists: reader k
takes the k-th listed reading of every flagged phrase (a phrase with fewer
readings is left to it).  Where the two readers took reading k of a phrase,
reader k is on their side and shows what a third reader holds back by being
a third reader; the others show what the answer decides.  A requirement on
which a new reader differs from one of the two, in context, is held; the
rule for what FCP certifies is otherwise that of the code studies
(code_demo.assurance), and the cells and violations are theirs.

A certificate says that the code meets a requirement as the two readers
state it, and it stands under a new reading that accepts every run they
accept.  The summary therefore counts a second rule beside the first, one
written after the results of the first were seen: a requirement is held
only where a new reader may reject a run that one of the two accepts.

The comparison behind the second rule is the one in context.  It assumes
the other rules of both readings, so it says nothing of a run on which
another rule of the new reading fails.  A comparison without context covers
every run, and fcp review lets a requirement go only where neither of the
two found a run that a reader accepts and the new reader rejects
(fcp.review.waiting).  The summary counts that rule as well (waits).

  variant_demo.py plan                           the tasks, their flagged phrases, the readers to run
  variant_demo.py agents [--jobs N] [TASK...]    the readers that are missing (Opus, each in the sandbox of
                                                 fcp.review.run_agent); this spends agent usage
  variant_demo.py compare TASK                   every new reader of TASK against both readers, in this
                                                 process (run alone, inside a memory cap)
  variant_demo.py under TASK                     the pairs of TASK in which the new reader assumes more
                                                 than the stored one, compared again on the runs that meet
                                                 the new reader's assumptions (a task whose code calls a service)
  variant_demo.py summary                        results/code_variants.json, and the table

A new reading is stored in corpus/code_<task>/variants/ (not in formal/, so
nothing that loads every reading of a task finds it), its prompt, reply and
run record in corpus/code_<task>/agents/<name>/, the comparisons in
results/variants/<task>.json.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

TASKS = ['card', 'change', 'checkout', 'invoice', 'limit', 'loyal', 'mask', 'order', 'pay', 'save']
PEERS = ['agent_a', 'agent_b']
AGREE = {'EQUIVALENT', 'ONLY-A', 'ONLY-B'}              # code_demo.PLAIN_AGREE
STORED = {'card': {1: 'variant'}}                       # the reader of section 8.2: formal/variant.yaml, reading 1
MODEL = 'opus'
AGENT_SECONDS = 3600
JOBS = int(os.environ.get('FCP_JOBS', 8))               # engine tasks of a comparison that run at a time
WORK = os.environ.get('FCP_VARIANT_WORK') or os.path.expanduser('~/.cache/fcp/variant-work')
OUT = os.path.join(HERE, 'results', 'variants')
RESULT = os.path.join(HERE, 'results', 'code_variants.json')
LIMIT = re.compile(r'limit reached|usage limit|rate limit|hit your limit|\b429\b|overloaded|credit balance|quota',
                   re.I)
STOP = threading.Event()                                # an agent's reply was an error about usage: no further run

READ_AS = """
The phrases below are flagged as ambiguous in requirements.yaml, each with a
list of readings. Read each of them as given here, even where another reading
seems more natural, and say so in the note of every item it affects:
{lines}
"""


def bundle(task: str) -> str:
    return os.path.join(ROOT, 'corpus', f'code_{task}')


def read(path: str):
    with open(path) as f:
        return json.load(f)


def write(path: str, doc):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path + '.tmp', 'w') as f:
        json.dump(doc, f, indent=1, default=str)
        f.write('\n')
    os.replace(path + '.tmp', path)


def engine() -> str:
    git = lambda *a: subprocess.run(('git', '-C', ROOT) + a, capture_output=True, text=True).stdout.strip()
    return git('rev-parse', '--short', 'HEAD') + (' with uncommitted changes in fcp/'
                                                  if git('status', '--porcelain', '--', 'fcp') else '')


def phrases(task: str) -> list[dict]:
    """The phrases the decomposer flagged, each with its listed readings."""
    import yaml
    with open(os.path.join(bundle(task), 'requirements.yaml')) as f:
        reqs = yaml.safe_load(f)['requirements']
    return [{'req': r['id'], 'phrase': a['phrase'], 'readings': list(a['readings'])}
            for r in reqs for a in r.get('ambiguity') or []]


def variants(task: str) -> list[dict]:
    """Reader k of a task: the k-th listed reading of every flagged phrase that has one."""
    ps, out = phrases(task), []
    for k in range(1, max(len(p['readings']) for p in ps) + 1):
        name = STORED.get(task, {}).get(k) or f'variant{k}'
        stored = name in STORED.get(task, {}).values()
        out.append({'k': k, 'name': name, 'stored': stored,
                    'path': os.path.join(bundle(task), 'formal' if stored else 'variants', f'{name}.yaml'),
                    'answers': [{'req': p['req'], 'phrase': p['phrase'], 'reading': k, 'text': p['readings'][k - 1]}
                                for p in ps if len(p['readings']) >= k]})
    return out


def decisions(path: str) -> list[dict]:
    """What a reading says it took of each flagged phrase."""
    import yaml
    with open(path) as f:
        fs = yaml.safe_load(f) or {}
    return [{'req': d.get('req'), 'phrase': d.get('phrase'), 'reading': d.get('reading')}
            for d in fs.get('decisions') or []]


TOOK = {'card': {('R-CAP-1', 'a load that would take it over'): [2, 2]}}     # docs/FCP_code.md, section 8.2


def sides(task: str) -> dict:
    """The listed reading that each of the two readers took of a flagged phrase, where that is recorded."""
    took = [{(d['req'], d['phrase']): d['reading']
             for d in decisions(os.path.join(bundle(task), 'formal', f'{s}.yaml'))} for s in PEERS]
    return {**TOOK.get(task, {}), **{k: [took[0][k], took[1][k]] for k in took[0] if k in took[1]}}


def plan():
    runs = 0
    for task in TASKS:
        took = sides(task)
        print(f'{task}:')
        for p in phrases(task):
            print(f'  {p["req"]} "{p["phrase"]}"   the two readers took:',
                  took.get((p['req'], p['phrase'])) or 'not recorded')
            for i, text in enumerate(p['readings'], 1):
                print(f'      {i}. {text}')
        for v in variants(task):
            have = os.path.exists(v['path'])
            runs += not have
            print(f'  reader {v["k"]} ({v["name"]}): {len(v["answers"])} phrases fixed;',
                  ('stored' if v['stored'] else 'written') if have else 'to run')
    print(f'{runs} readers to run')


# ---------------------------------------------------------------- the readers

def prompt_for(task: str, v: dict, ws: str) -> str:
    """The prompt of the task's first reader, for this reader: its workspace,
    its set and its prefix, the readings it is to take, and the rule that it
    records them."""
    from fcp import agents as AG
    with open(os.path.join(bundle(task), 'agents', 'agent_a', 'prompt.md')) as f:
        text = f.read()
    name = v['name']

    def sub(old: str, new: str):
        nonlocal text
        if text.count(old) != 1:
            raise ValueError(f'{task}: {old!r} is in the first reader\'s prompt {text.count(old)} times')
        text = text.replace(old, new)
    text = text.replace(re.search(r'^Workspace: (\S+)$', text, re.M).group(1), ws)
    sub('formal/agent_a.yaml', f'formal/{name}.yaml')
    sub('`set: agent_a`', f'`set: {name}`')
    sub('--set agent_a', f'--set {name}')
    sub('id: agent_a}', f'id: {name}}}')
    sub(re.search(r'Every item id starts with "[A-Z]+-"', text).group(0), f'Every item id starts with "V{v["k"]}-"')
    lines = '\n'.join(f'- {a["req"]}, "{a["phrase"]}": {a["text"]}' for a in v['answers'])
    sub('\nRules:', READ_AS.format(lines=lines) + '\nRules:')
    rule = re.search(r'\n8\. .*?(?=\n\nWhen done)', AG.FORMALIZER, re.S).group(0)
    sub('\n\nWhen done, reply', rule.replace('{{', '{').replace('}}', '}') + '\n\nWhen done, reply')
    if 'agent_a' in text or AG.FCP not in text:
        raise ValueError(f'{task}: the first reader\'s prompt is not the one this script knows')
    return text


_RUNS = threading.Lock()


def reader(task: str, v: dict) -> dict:
    """One reader, in a new workspace: how its run went.  A reading that
    passes lint is stored with the task, with the record of its run."""
    from fcp import agents as AG, review as R
    name = v['name']
    d = os.path.join(WORK, f'{task}-{name}-{time.strftime("%Y%m%d-%H%M%S")}')
    os.makedirs(d)
    ws = AG.workspace(bundle(task), 'formalizer', os.path.join(d, 'ws'), name)
    prompt = prompt_for(task, v, ws)
    with open(os.path.join(d, 'prompt.md'), 'w') as f:
        f.write(prompt)
    reply = R.run_agent(prompt, ws, MODEL, timeout=AGENT_SECONDS)
    with open(os.path.join(d, 'reply.md'), 'w') as f:
        f.write(str(reply))
    src = os.path.join(ws, 'formal', f'{name}.yaml')
    run = {'task': task, 'reader': name, 'k': v['k'], 'model': MODEL, 'date': time.strftime('%Y-%m-%d %H:%M:%S'),
           **reply.meta, 'written': os.path.exists(src)}
    if reply.meta.get('error') and LIMIT.search(str(reply)):
        STOP.set()
        run['limit'] = str(reply).strip()[:200]
    if run['written']:
        p = subprocess.run([AG.FCP, 'lint', ws], capture_output=True, text=True, timeout=900)
        run['lint'] = 'clean' if p.returncode == 0 else (p.stdout + p.stderr).strip()[-600:]
        took = {(x['req'], x['phrase']): x['reading'] for x in decisions(src)}
        run['recorded'] = len(took)
        run['as_told'] = all(took.get((a['req'], a['phrase'])) == a['reading'] for a in v['answers'])
    if run.get('lint') == 'clean':
        AG.record(bundle(task), 'formalizer', name, MODEL, prompt, {f'formal/{name}.yaml': src}, reply)
        os.makedirs(os.path.dirname(v['path']), exist_ok=True)
        shutil.copy(src, v['path'])
        run['stored'] = True
    with _RUNS:                                             # every run counts in the cost, also one that left nothing
        os.makedirs(OUT, exist_ok=True)
        with open(os.path.join(OUT, 'runs.jsonl'), 'a') as f:
            f.write(json.dumps(dict(run, work=os.path.basename(d))) + '\n')
    return run


def agents(tasks: list, jobs: int):
    from fcp import review as R
    os.environ['FCP_AGENT_SANDBOX'] = '1'                   # in a sandbox, or not at all
    why = R.sandbox_fault()
    if why:
        sys.exit(f'no sandbox starts here, so no reader is run: {why}')
    todo = [(t, v) for t in tasks or TASKS for v in variants(t) if not os.path.exists(v['path'])]
    print(time.strftime('%H:%M:%S'), len(todo), 'readers to run,', jobs, 'at a time', flush=True)

    def go(tv):
        task, v = tv
        if STOP.is_set():
            return
        try:
            run = reader(task, v)
            print(time.strftime('%H:%M:%S'), task, v['name'],
                  ' '.join(f'{k}={run[k]}' for k in ('seconds', 'turns', 'cost_usd', 'error', 'written', 'lint',
                                                     'as_told', 'limit') if k in run)[:400], flush=True)
        except Exception as e:                              # this reader has no reading; the others go on
            print(time.strftime('%H:%M:%S'), task, v['name'], 'NOT RUN', f'{type(e).__name__}: {e}'[:300],
                  flush=True)
    with ThreadPoolExecutor(max_workers=jobs) as ex:
        list(ex.map(go, todo))
    left = [(t, v['name']) for t in tasks or TASKS for v in variants(t) if not os.path.exists(v['path'])]
    print('STOPPED on a reply about usage' if STOP.is_set() else 'DONE', len(todo) - len(left), 'stored,',
          len(left), 'missing', left, flush=True)


# ---------------------------------------------------------------- a new reader against the two

def compare(task: str, force: bool = False):
    """Every new reader of a task compared with each of the two readers,
    requirement by requirement, by the function that compared the two with
    each other in the task's study (code_demo.readings, effects_demo.readings
    where the code calls a service).  The comparisons run on a copy of the
    task with the new readings in formal/; each pair is written when it is
    done, and a pair that is there is not run again (unless force)."""
    vs = variants(task)
    tmp = os.path.join(WORK, 'compare', f'{task}-{time.strftime("%Y%m%d-%H%M%S")}')
    shutil.copytree(bundle(task), tmp, ignore=shutil.ignore_patterns('.fcp', '__pycache__', 'agents', 'variants'))
    for v in vs:
        if not v['stored'] and os.path.exists(v['path']):
            shutil.copy(v['path'], os.path.join(tmp, 'formal', f'{v["name"]}.yaml'))
    sys.argv = [sys.argv[0], f'code_{task}']               # the task of the two study scripts
    sys.path.insert(0, HERE)
    import effects_demo as ED
    from fcp import effects as FX, software as SW
    from fcp.analyses import Session
    CD = ED.CD
    path = os.path.join(OUT, f'{task}.json')
    doc = read(path) if os.path.exists(path) else {'task': task, 'readers': {}}
    doc['settings'] = {'jobs': JOBS, 'bit_jobs': SW.BIT_JOBS}
    for v in vs:
        name = v['name']
        rec = doc['readers'].setdefault(name, {})
        rec.update(k=v['k'], stored=v['stored'], answers=v['answers'])
        rec.pop('error', None)
        if not os.path.exists(v['path']):
            rec['error'] = 'no reading'
            write(path, doc)
            continue
        rec['recorded'] = decisions(v['path'])
        try:
            S = Session(tmp, sets=PEERS + [name], cache=os.path.join(WORK, 'cache', task), jobs=JOBS)
            fn = SW.function(S)
            ifc = FX.interface(S, fn)
        except Exception as e:                              # a reading that does not load is not compared
            rec['error'] = f'{type(e).__name__}: {e}'[:600]
            write(path, doc)
            continue
        pairs = rec.setdefault('pairs', {})
        for peer in PEERS:
            key = f'{peer}|{name}'
            if 'relations' in pairs.get(key, {}) and not force:
                continue
            CD.SETS = ED.SETS = [peer, name]
            t = time.time()
            try:
                out = ED.readings(S, fn, ifc) if ifc else CD.readings(S, fn)
                pairs[key] = {'seconds': round(time.time() - t), 'engine': engine(),
                              'by': 'effects_demo.readings' if ifc else 'code_demo.readings', 'relations': out[key]}
            except Exception as e:
                pairs[key] = {'seconds': round(time.time() - t), 'engine': engine(),
                              'error': f'{type(e).__name__}: {e}'[:600]}
            write(path, doc)
            x = pairs[key]
            print(time.strftime('%H:%M:%S'), task, key, x['seconds'], 's',
                  x.get('error') or sorted(r for r in x['relations'] if differs(x['relations'][r])), flush=True)
    write(path, doc)


def under(task: str, force: bool = False):
    """The pairs of a task in which the new reader assumes more than the stored
    reader, compared again on the runs that meet the new reader's assumptions.

    A comparison compares contracts: the rules of a reading bind for as long
    as its assumptions hold.  A new reader that assumes more about the service
    than a stored reader accepts every run that breaks what it assumes, and
    so differs from the stored reader on every requirement, whatever answer
    it was told.  Such a run cannot show that a requirement depends on the
    answer, because the new reader's rules say nothing about it.  Where the
    new reader's assumptions imply the stored reader's and not the other way
    round (A-WEAKER on <assumptions>), both readings bind on every run that
    meets the new reader's assumptions, and the pair is compared again on
    those runs only (Session.compare with env).  In every other pair the
    comparison of contracts stands: with equivalent assumptions it is the
    same comparison, and a stored reader that assumes what the new reader
    does not may be silent exactly where the answer matters.  Only for a
    task whose code calls a service: readings of a function are compared by
    fcp.software.compare, which has no such mode."""
    vs = variants(task)
    path = os.path.join(OUT, f'{task}.json')
    if not os.path.exists(path):
        sys.exit(f'{task}: not compared yet')
    doc = read(path)
    tmp = os.path.join(WORK, 'compare', f'{task}-under-{time.strftime("%Y%m%d-%H%M%S")}')
    shutil.copytree(bundle(task), tmp, ignore=shutil.ignore_patterns('.fcp', '__pycache__', 'agents', 'variants'))
    for v in vs:
        if not v['stored'] and os.path.exists(v['path']):
            shutil.copy(v['path'], os.path.join(tmp, 'formal', f'{v["name"]}.yaml'))
    sys.argv = [sys.argv[0], f'code_{task}']               # the task of the two study scripts
    sys.path.insert(0, HERE)
    import effects_demo as ED
    from fcp import effects as FX, software as SW
    from fcp.analyses import Session
    for v in vs:
        name = v['name']
        pairs = (doc['readers'].get(name) or {}).get('pairs') or {}
        todo = [p for p in PEERS if 'relations' in pairs.get(f'{p}|{name}', {})
                and (force or 'under' not in pairs[f'{p}|{name}'])]
        if not todo:
            continue
        S = Session(tmp, sets=PEERS + [name], cache=os.path.join(WORK, 'cache', task), jobs=JOBS)
        fn = SW.function(S)
        ifc = FX.interface(S, fn)
        if not ifc:
            sys.exit(f'{task}: its code calls no service; the readings of a function are compared by '
                     f'fcp.software.compare, which does not compare under the assumptions of one reading')
        S.cmp_engine = 'bmc'                                # as effects_demo.readings: bounded
        for peer in todo:
            key = f'{peer}|{name}'
            t = time.time()
            env = S.compare(peer, name, only={'<assumptions>'}).get('<assumptions>', {}).get('relation')
            u = {'assumptions': env, 'engine': engine()}
            if env == 'A-WEAKER':                           # the new reader assumes all that the stored one does, and more
                plain = S.compare(peer, name, env=name)
                rels = {r: {'plain': x['relation'], 'bounded': x.get('depth')} for r, x in plain.items()
                        if r != '<assumptions>'}
                disputed = {r for r, x in rels.items() if x['plain'] not in AGREE}
                if disputed:
                    for r, x in S.compare(peer, name, env=name, context=True, only=disputed).items():
                        if r not in rels:
                            continue
                        rels[r]['context'] = x['relation']
                        for w in ('a_not_b', 'b_not_a'):
                            if x.get(f'witness_{w}'):
                                rels[r][w] = {'lines': ED.conversation_lines(S, fn, ifc, x[f'witness_{w}'])}
                u['relations'] = rels
            u['seconds'] = round(time.time() - t)
            pairs[key]['under'] = u
            write(path, doc)
            print(time.strftime('%H:%M:%S'), task, key, 'assumptions:', env, u['seconds'], 's',
                  sorted(r for r, x in u['relations'].items() if differs(x)) if 'relations' in u
                  else 'the comparison of contracts stands', flush=True)


def relation(x: dict):
    """How two readings stand on a requirement: in context where that was asked, else on its own."""
    return x.get('context', x.get('plain'))


def differs(x: dict) -> bool:
    return relation(x) not in AGREE


IMPLIED = AGREE | {'A-STRONGER'}                        # no run that the stored reading accepts and the new one rejects


def rejects(x: dict) -> bool:
    """In a pair of a stored reading (A) and a new one (B): the new reading may
    reject a run that the stored reading accepts.  The comparison shows such a
    run, or did not show that there is none (UNKNOWN, NO-CONTEXT)."""
    return relation(x) not in IMPLIED


def waits(x: dict) -> bool:
    """The second rule as fcp review applies it (fcp.review.waiting).  In a
    pair of a stored reading (A) and a new one (B) that differ in context, the
    requirement goes without the shared answers only where no run that the
    stored reading accepts and the new one rejects was found in context, and
    none without context.  The comparison in context assumes the other rules
    of both readings: closed there, the direction is still open on a run on
    which another rule of the new reading fails."""
    return differs(x) and (rejects(x) or x.get('plain') not in IMPLIED)


# ---------------------------------------------------------------- what is certified, before and after

def side(v: dict, took: dict) -> str:
    """same: of every phrase the reader was told the reading that both readers
    took; other: of every phrase a reading that neither took; else mixed, or
    not recorded where the two readings do not say what they took."""
    marks = set()
    for a in v['answers']:
        t = took.get((a['req'], a['phrase']))
        marks.add('not recorded' if not t else 'same' if set(t) == {a['reading']}
                  else 'other' if a['reading'] not in t else 'mixed')
    return marks.pop() if len(marks) == 1 else 'not recorded' if 'not recorded' in marks else 'mixed'


def count(cells: list, held: set) -> dict:
    cert = [x for _, r, x in cells if x['fcp'] and r not in held]
    return {'certified': len(cert), 'false': sum(bool(x['violated']) for x in cert)}


ONE_WAY = 'UNKNOWN, with a call'                        # one direction ended with a call that separates the readings
SHOWN = {'A-STRONGER', 'A-WEAKER', 'INCOMPARABLE', ONE_WAY}     # the comparison shows that the readings differ
# how the two readers stand to the reference reading on a requirement on which they agree with each other
APART = {'both': 'both shown to differ from the reference', 'one': 'one of them shown to differ from it',
         'undecided': 'a comparison with it did not end'}


def held_as(x: dict) -> str:
    """The relation that holds a requirement back.  A comparison of which one
    direction ended with a call that one reading accepts and the other rejects
    has shown a difference, also where its other direction did not end and the
    relation is therefore UNKNOWN."""
    rel = relation(x)
    return ONE_WAY if rel == 'UNKNOWN' and (x.get('a_not_b') or x.get('b_not_a')) else rel


def accepts(x: dict) -> bool:
    """In a pair of the reference reading (A) and a reader's (B): the comparison
    shows a run that the reader accepts and the reference rejects."""
    return relation(x) in ('A-STRONGER', 'INCOMPARABLE') or bool(relation(x) == 'UNKNOWN' and x.get('b_not_a'))


def lost(cells: list, held: dict) -> dict:
    """The cells that were certified and are not once `held` (requirement -> the relations that hold it) is
    held: the false ones, the true ones, and of the true ones those behind which no comparison ended."""
    out = {'false': 0, 'true': 0, 'true_undecided': 0}
    for _, r, x in cells:
        if x['fcp'] and r in held:
            if x['violated']:
                out['false'] += 1
            else:
                out['true'] += 1
                out['true_undecided'] += not set(held[r].values()) & SHOWN
    return out


def summary() -> dict:
    """The cells of the code studies (a model's code on a requirement) that
    FCP certified, and those it certifies when every requirement on which a
    new reader differs from one of the two is held."""
    tasks = {}
    for task in TASKS:
        study = read(os.path.join(HERE, 'results', f'code_{task}.json'))
        rows, was = study['assurance']['rows'], study['readings']
        cells = [(m, r, x) for m, rs in rows.items() for r, x in rs.items()]
        path = os.path.join(OUT, f'{task}.json')
        doc, took, ps = (read(path) if os.path.exists(path) else {'readers': {}}), sides(task), phrases(task)
        flagged, readers = {p['req'] for p in ps}, {}
        for v in variants(task):
            rec = doc['readers'].get(v['name']) or {}
            pairs = [(p, (rec.get('pairs') or {}).get(f'{p}|{v["name"]}') or {}) for p in PEERS]
            held, again = {}, {}        # again: with the pairs compared on the runs that meet the new reader's assumptions
            rej, rej_u = {}, {}         # held only where the new reader may reject a run that a stored reader accepts
            wait = {}                   # ... in context, or without context (the rule of fcp review)
            for p, x in pairs:
                u = (x.get('under') or {}).get('relations') or {}
                for r, rel in (x.get('relations') or {}).items():
                    if differs(rel):
                        held.setdefault(r, {})[p] = held_as(rel)
                    if differs(u.get(r, rel)):
                        again.setdefault(r, {})[p] = held_as(u.get(r, rel))
                    if rejects(rel):
                        rej.setdefault(r, {})[p] = held_as(rel)
                    if rejects(u.get(r, rel)):
                        rej_u.setdefault(r, {})[p] = held_as(u.get(r, rel))
                    if waits(rel):
                        wait.setdefault(r, {})[p] = held_as(rel)
            e = {'k': v['k'], 'stored': v['stored'], 'side': side(v, took), 'fixed': len(v['answers']),
                 'compared': all('relations' in x for _, x in pairs),
                 'seconds': sum(x.get('seconds') or 0 for _, x in pairs), 'held': held,
                 'held_unflagged': sorted(set(held) - flagged)}
            why = rec.get('error') or '; '.join(f'{p}: {x["error"]}' for p, x in pairs if x.get('error'))
            if why:
                e['error'] = why
            if e['compared']:
                e.update(count(cells, set(held)), lost=lost(cells, held))
                e['under'] = dict(count(cells, set(again)), lost=lost(cells, again), held=again,
                                  assumptions={p: x['under'].get('assumptions') for p, x in pairs if 'under' in x},
                                  again=[p for p, x in pairs if 'relations' in (x.get('under') or {})])
                e['rejects'] = dict(count(cells, set(rej)), lost=lost(cells, rej), held=rej,
                                    held_under=sorted(rej_u))
                e['waits'] = dict(count(cells, set(wait)), lost=lost(cells, wait), held=wait)
            readers[v['name']] = e
        done = [e for e in readers.values() if e['compared']]
        t = {'cells': len(cells), 'violated': sum(bool(x['violated']) for _, _, x in cells),
             'before': count(cells, set()), 'phrases': len(ps), 'listed': sum(len(p['readings']) for p in ps),
             'recorded': bool(took), 'readers': readers, 'complete': len(done) == len(readers)}
        every, every_u, every_r, every_w = {}, {}, {}, {}   # requirement -> {reader|peer: relation}, of all readers
        for n, e in readers.items():
            for r, by in (e['held'] if e['compared'] else {}).items():
                every.setdefault(r, {}).update({f'{n}|{p}': rel for p, rel in by.items()})
            for r, by in (e['under']['held'] if e['compared'] else {}).items():
                every_u.setdefault(r, {}).update({f'{n}|{p}': rel for p, rel in by.items()})
            for r, by in (e['rejects']['held'] if e['compared'] else {}).items():
                every_r.setdefault(r, {}).update({f'{n}|{p}': rel for p, rel in by.items()})
            for r, by in (e['waits']['held'] if e['compared'] else {}).items():
                every_w.setdefault(r, {}).update({f'{n}|{p}': rel for p, rel in by.items()})
        t['all'] = dict(count(cells, set(every)), lost=lost(cells, every), readers=len(done), held=every)
        t['all_under'] = dict(count(cells, set(every_u)), lost=lost(cells, every_u), readers=len(done), held=every_u,
                              again=sum(len(e['under']['again']) for e in done))
        t['all_rejects'] = dict(count(cells, set(every_r)), lost=lost(cells, every_r), readers=len(done),
                                held=every_r)
        t['all_waits'] = dict(count(cells, set(every_w)), lost=lost(cells, every_w), readers=len(done), held=every_w)
        # which listed reading the two readers' rules for a flagged requirement match, by the comparisons
        t['flagged'] = [{'req': p['req'], 'phrase': p['phrase'], 'recorded': took.get((p['req'], p['phrase'])),
                         'same_as_both': [e['k'] for e in done if e['k'] <= len(p['readings']) and p['req'] not in e['held']]}
                        for p in ps]
        # the requirements on which the two readers agree with each other and not with the reference reading.
        # The reference reading assumes nothing, so for a task whose code calls a service it is compared with
        # each of the two on the runs that meet that reader's assumptions (experiments/compare_env.py)
        env_path = os.path.join(HERE, 'results', f'code_{task}_env.json')
        vs_gold = ({k: {r: {a: b for a, b in x.items() if b is not None} for r, x in rec.items()}
                    for k, rec in read(env_path)['readings'].items()} if os.path.exists(env_path) else was)
        gold = {p: vs_gold.get(f'gold|{p}') or {} for p in PEERS}

        def shown(r, gold=gold) -> str:
            n = sum(r in gold[p] and held_as(gold[p][r]) in SHOWN for p in PEERS)
            return 'both' if n == len(PEERS) else 'one' if n else 'undecided'
        t['apart'] = {r: {'flagged': r in flagged,
                          'gold': {p: relation(gold[p][r]) for p in PEERS if r in gold[p]},
                          'shown': shown(r),
                          'accepts': all(r in gold[p] and accepts(gold[p][r]) for p in PEERS),
                          'held_by': [n for n, e in readers.items() if e['compared'] and r in e['held']],
                          'rejects_by': [n for n, e in readers.items()
                                         if e['compared'] and r in e['rejects']['held']],
                          'waits_by': [n for n, e in readers.items() if e['compared'] and r in e['waits']['held']]}
                      for r, x in sorted(was['agent_a|agent_b'].items())
                      if not differs(x) and any(r in gold[p] and differs(gold[p][r]) for p in PEERS)}
        tasks[task] = t
    full = [t for t in tasks.values() if t['complete']]

    def total(pick) -> dict:
        out = {'tasks': 0, 'cells': 0, 'violated': 0, 'before': {'certified': 0, 'false': 0},
               'after': {'certified': 0, 'false': 0}, 'lost': {'false': 0, 'true': 0, 'true_undecided': 0}}
        for t in full:
            x = pick(t)
            if x:
                out['tasks'] += 1
                out['cells'] += t['cells']
                out['violated'] += t['violated']
                for k in ('certified', 'false'):
                    out['before'][k] += t['before'][k]
                    out['after'][k] += x[k]
                for k in out['lost']:
                    out['lost'][k] += x['lost'][k]
        return out

    apart = [x for t in full for x in t['apart'].values()]

    def part(pick) -> dict:
        xs = [x for x in apart if pick(x)]
        free = [x for x in xs if not x['flagged']]
        return {'requirements': len(xs), 'held': sum(bool(x['held_by']) for x in xs),
                'held_rejects': sum(bool(x['rejects_by']) for x in xs),
                'held_waits': sum(bool(x['waits_by']) for x in xs),
                'unflagged': len(free), 'unflagged_held': sum(bool(x['held_by']) for x in free),
                'unflagged_held_rejects': sum(bool(x['rejects_by']) for x in free),
                'unflagged_held_waits': sum(bool(x['waits_by']) for x in free)}

    def of_side(word):
        return lambda t: next((e for e in t['readers'].values() if e['side'] == word), None)
    runs = []
    if os.path.exists(os.path.join(OUT, 'runs.jsonl')):
        with open(os.path.join(OUT, 'runs.jsonl')) as f:
            runs = [json.loads(line) for line in f if line.strip()]
    doc = {'what': 'the ten code tasks with one more reader per listed answer of the flagged phrases '
                   '(experiments/variant_demo.py); a cell is one model\'s code on one requirement, and the cells, '
                   'the violations and what FCP certified before are those of results/code_<task>.json',
           'rule': 'a requirement on which a new reader differs from one of the two readers, in context '
                   '(a relation other than EQUIVALENT, ONLY-A, ONLY-B), is held: none of its cells is certified',
           'lost': 'the cells that were certified and are not once the requirements are held: false ones '
                   '(the code violates the requirement), true ones, and of the true ones those held only by '
                   'comparisons that did not end (UNKNOWN), where no difference of the readings was shown',
           'tasks': tasks,
           'totals': {'all readers': total(lambda t: t['all']), 'a reader on the other side': total(of_side('other')),
                      'a reader on the same side': total(of_side('same'))},
           'under': 'a comparison compares contracts, so a new reader that assumes more than a stored reader differs '
                    'from it on every requirement, on runs about which its own rules say nothing; such a pair '
                    '(A-WEAKER on <assumptions>) is compared again on the runs that meet the new reader\'s '
                    'assumptions (variant_demo.py under, tasks whose code calls a service), and totals_under '
                    'counts with those comparisons in place of the first ones',
           'totals_under': {'all readers': total(lambda t: t['all_under']),
                            'a reader on the other side': total(lambda t: (of_side('other')(t) or {}).get('under')),
                            'a reader on the same side': total(lambda t: (of_side('same')(t) or {}).get('under'))},
           'rejects': 'a second rule, written after the results of the first were seen: a certificate says that the '
                      'code meets a requirement as the two readers state it, and it stands under a new reading that '
                      'accepts every run they accept; a requirement is held only where a new reader may reject a '
                      'run that one of the two accepts, in context (A-WEAKER, INCOMPARABLE, UNKNOWN, NO-CONTEXT, '
                      'and not A-STRONGER), and totals_rejects counts with it; held_under of a reader is the same '
                      'set taken from the comparisons on the runs that meet its assumptions, where those were made',
           'totals_rejects': {'all readers': total(lambda t: t['all_rejects']),
                              'a reader on the other side': total(lambda t: (of_side('other')(t) or {}).get('rejects')),
                              'a reader on the same side': total(lambda t: (of_side('same')(t) or {}).get('rejects'))},
           'waits': 'the second rule as fcp review applies it (fcp.review.waiting): the comparison in context '
                    'assumes the other rules of both readings and says nothing of a run on which another rule of '
                    'the new reading fails, so a requirement on which a new reader differs from one of the two is '
                    'let go only where no run that one of the two accepts and the new reader rejects was found in '
                    'context and none without context (the relation without context is EQUIVALENT or A-STRONGER); '
                    'totals_waits counts with it',
           'totals_waits': {'all readers': total(lambda t: t['all_waits']),
                            'a reader on the other side': total(lambda t: (of_side('other')(t) or {}).get('waits')),
                            'a reader on the same side': total(lambda t: (of_side('same')(t) or {}).get('waits'))},
           'apart': {'what': 'requirements on which the two readers agree with each other while a comparison '
                             'with the reference reading does not show agreement, in the tasks whose readers '
                             'are all compared (for a task whose code calls a service the reference is compared '
                             'on the runs that meet the reader\'s assumptions, results/code_<task>_env.json); '
                             'both: each of the two is shown to differ from the reference; one: one of them '
                             'is; undecided: neither is, and a comparison did not end; accepts: a run is shown '
                             'that each of the two accepts and the reference rejects, so that a certificate '
                             'can be false; held: those on which a new reader differs from one of the two; '
                             'held_rejects: those on which a new reader may reject a run that one of the two '
                             'accepts; held_waits: those that wait under the rule of fcp review (waits)',
                     **{word: part(lambda x, word=word: x['shown'] == word) for word in APART},
                     'accepts': part(lambda x: x['accepts'])},
           'incomplete': sorted(k for k, t in tasks.items() if not t['complete']),
           'runs': {'count': len(runs), 'stored': sum(bool(r.get('stored')) for r in runs),
                    'seconds': sum(r.get('seconds') or 0 for r in runs),
                    'cost_usd': round(sum(r.get('cost_usd') or 0 for r in runs), 2),
                    'turns': sum(r.get('turns') or 0 for r in runs),
                    'not_as_told': [f'{r["task"]} {r["reader"]}' for r in runs if r.get('stored') and not r.get('as_told')]}}
    write(RESULT, doc)
    return doc


def lost_line(x: dict) -> str:
    return f'{x["false"]} false, {x["true"]} true ({x["true_undecided"]} behind comparisons that did not end)'


def table(doc: dict):
    print(f'{"task":9s} {"cells":>5s} {"viol":>4s} {"cert":>4s} {"false":>5s}   reader (side): held -> certified, false')
    for name, t in doc['tasks'].items():
        b = t['before']
        print(f'{name:9s} {t["cells"]:5d} {t["violated"]:4d} {b["certified"]:4d} {b["false"]:5d}')
        for r, e in t['readers'].items():
            if e['compared']:
                print(f'{"":32s}{r} ({e["side"]}): {", ".join(e["held"]) or "none"} -> {e["certified"]}, {e["false"]}'
                      f'   lost: {lost_line(e["lost"])}')
                u = e['under']
                if u['again']:
                    print(f'{"":34s}on the runs that meet its assumptions (against {", ".join(u["again"])}): '
                          f'{", ".join(u["held"]) or "none"} -> {u["certified"]}, {u["false"]}'
                          f'   lost: {lost_line(u["lost"])}')
                j = e['rejects']
                if set(j['held']) != set(e['held']):
                    also = '' if not u['again'] or set(j['held_under']) == set(j['held']) else \
                        f' (on the runs that meet its assumptions: {", ".join(j["held_under"]) or "none"})'
                    print(f'{"":34s}where it may reject a run that one of the two accepts: '
                          f'{", ".join(j["held"]) or "none"}{also} -> {j["certified"]}, {j["false"]}'
                          f'   lost: {lost_line(j["lost"])}')
                w = e['waits']
                if set(w['held']) != set(j['held']):
                    print(f'{"":34s}... in context or without it (fcp review): '
                          f'{", ".join(w["held"]) or "none"} -> {w["certified"]}, {w["false"]}'
                          f'   lost: {lost_line(w["lost"])}')
            else:
                print(f'{"":32s}{r} ({e["side"]}): not compared {e.get("error", "")[:120]}')
        if t['complete']:
            print(f'{"":32s}all {t["all"]["readers"]}: -> {t["all"]["certified"]}, {t["all"]["false"]}'
                  f'   lost: {lost_line(t["all"]["lost"])}')
            a = t['all_under']
            if a['again']:
                print(f'{"":34s}with those comparisons: -> {a["certified"]}, {a["false"]}   lost: {lost_line(a["lost"])}')
            j = t['all_rejects']
            if set(j['held']) != set(t['all']['held']):
                print(f'{"":34s}held only where a new reader may reject: -> {j["certified"]}, {j["false"]}'
                      f'   lost: {lost_line(j["lost"])}')
            w = t['all_waits']
            if set(w['held']) != set(j['held']):
                print(f'{"":34s}... in context or without it (fcp review): -> {w["certified"]}, {w["false"]}'
                      f'   lost: {lost_line(w["lost"])}')
    for name, x in doc['totals'].items():
        print(f'{name}: {x["tasks"]} tasks, {x["cells"]} cells, {x["violated"]} violated; certified '
              f'{x["before"]["certified"]} -> {x["after"]["certified"]}, false {x["before"]["false"]} -> '
              f'{x["after"]["false"]}; lost: {lost_line(x["lost"])}')
    for name, x in doc['totals_under'].items():
        print(f'{name}, where a new reader assumes more compared on the runs that meet its assumptions: certified '
              f'{x["before"]["certified"]} -> {x["after"]["certified"]}, false {x["before"]["false"]} -> '
              f'{x["after"]["false"]}; lost: {lost_line(x["lost"])}')
    for name, x in doc['totals_rejects'].items():
        print(f'{name}, held only where a new reader may reject a run that one of the two accepts: certified '
              f'{x["before"]["certified"]} -> {x["after"]["certified"]}, false {x["before"]["false"]} -> '
              f'{x["after"]["false"]}; lost: {lost_line(x["lost"])}')
    for name, x in doc['totals_waits'].items():
        print(f'{name}, held where a new reader may reject such a run in context or without it (fcp review): certified '
              f'{x["before"]["certified"]} -> {x["after"]["certified"]}, false {x["before"]["false"]} -> '
              f'{x["after"]["false"]}; lost: {lost_line(x["lost"])}')
    for word, words in list(APART.items()) + [('accepts', 'each shown to accept a run that the reference rejects')]:
        a = doc['apart'][word]
        print(f'the two readers agree with each other, {words}: {a["requirements"]} requirements '
              f'({a["unflagged"]} not flagged); a new reader differs on {a["held"]} ({a["unflagged_held"]}), '
              f'may reject on {a["held_rejects"]} ({a["unflagged_held_rejects"]}), in context or without it on '
              f'{a["held_waits"]} ({a["unflagged_held_waits"]})')
    print('incomplete:', doc['incomplete'] or 'none', '  runs:', json.dumps(doc['runs']))


def main():
    args = sys.argv[1:]
    os.environ['PATH'] = os.path.join(ROOT, '.tools', 'oss-cad-suite', 'bin') + os.pathsep + os.environ['PATH']
    if args[:1] == ['plan']:
        return plan()
    if args[:1] == ['summary']:
        return table(summary())
    if args[:1] == ['compare'] and len(args) >= 2:
        return compare(args[-1], force='--force' in args)
    if args[:1] == ['under'] and len(args) >= 2:
        return under(args[-1], force='--force' in args)
    if args[:1] == ['agents']:
        jobs, tasks, rest = 3, [], args[1:]
        while rest:
            a = rest.pop(0)
            if a == '--jobs':
                jobs = int(rest.pop(0))
            else:
                tasks.append(a)
        return agents(tasks, jobs)
    sys.exit(__doc__)


if __name__ == '__main__':
    main()
