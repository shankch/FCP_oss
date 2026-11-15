"""The models' own tests against mutants of their own code.

    python experiments/own_tests_mutants.py <corpus>

The planted variants of a study are edits of the reference.  A suite that
imports the functions its own package defines does not import on another
package, so it cannot be run on them.  Here the self-check baseline is
measured where it always runs: on every observable mutant of a model's own
code (the mutants of code_demo.py, with the verdicts recorded in
results/<corpus>.json), under that model's own tests.  A mutant is killed
by the tests if a test fails on it.  Writes results/<corpus>_own_tests.json.
"""
from __future__ import annotations

import itertools
import json
import os
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from fcp import software as SW  # noqa: E402

MODELS = ['haiku', 'sonnet', 'opus']
LIMIT = 60                                   # as code_demo.mutation_level
TIMEOUT = 120                                # seconds for one suite on one mutant (a suite takes about one)


def mutants_of(src: str) -> list[dict]:
    """The mutants SW.mutation takes of an implementation, in its order."""
    if not os.path.isdir(src):
        with open(src) as f:
            return [dict(m, file=None) for m in SW.mutants(f.read(), LIMIT)]
    per = []
    for path in SW.py_files(src):
        rel = os.path.relpath(path, src)
        with open(path) as f:
            per.append([dict(m, id=f'{rel}:{m["id"]}', desc=f'{rel}: {m["desc"]}', file=rel)
                        for m in SW.mutants(f.read(), LIMIT)])
    return [m for row in itertools.zip_longest(*per) for m in row if m is not None][:LIMIT]


def main():
    corpus = sys.argv[1]
    B = os.path.join(ROOT, 'corpus', corpus)
    with open(os.path.join(B, 'design.yaml')) as f:
        module = next(ln.split(':', 1)[1].strip() for ln in f if ln.strip().startswith('module:'))
    top = module.split('.')[0]
    with open(os.path.join(HERE, 'results', f'{corpus}.json')) as f:
        recorded = json.load(f)['mutation']
    support = os.path.join(B, 'support')
    out = {}
    for m in MODELS:
        home = os.path.join(B, 'agents', f'coder_{m}')
        src = home if '.' in module else os.path.join(home, f'{module}.py')
        tests = os.path.join(home, f'test_{top}.py')
        rec = {r['id']: r for r in recorded[m]['all']}
        muts = [mu for mu in mutants_of(src) if rec.get(mu['id'], {}).get('observable')]
        assert len(muts) == recorded[m]['observable'], (m, len(muts), recorded[m]['observable'])
        base = SW.run_tests(tests, src, module, support=support)
        assert base['ok'], (m, base['summary'])

        def one(mu):
            with tempfile.TemporaryDirectory(prefix='fcp_own_') as d:
                if mu['file']:
                    p = os.path.join(d, 'pkg')
                    shutil.copytree(src, p, ignore=shutil.ignore_patterns('__pycache__'))
                    with open(os.path.join(p, mu['file']), 'w') as f:
                        f.write(mu['code'])
                else:
                    p = os.path.join(d, os.path.basename(src))
                    with open(p, 'w') as f:
                        f.write(mu['code'])
                try:
                    r = SW.run_tests(tests, p, module, timeout=TIMEOUT, support=support)
                except subprocess.TimeoutExpired:       # the mutant never returns: the suite does not pass
                    r = {'failing': [], 'ok': False, 'timeout': True}
            return {'id': mu['id'], 'desc': mu['desc'], 'tests_failing': len(r['failing']) or (0 if r['ok'] else 1),
                    'killed_by_tests': not r['ok'], 'timeout': bool(r.get('timeout')),
                    'killed_by': {s: bool(k) for s, k in rec[mu['id']]['killed_by'].items()},
                    'example': rec[mu['id']].get('example')}
        with ThreadPoolExecutor(max_workers=8) as ex:
            rows = list(ex.map(one, muts))
        sets = sorted(rows[0]['killed_by']) if rows else []
        out[m] = {'tests': base['passed'], 'observable': len(rows),
                  'killed_by_tests': sum(r['killed_by_tests'] for r in rows),
                  'timeouts': sum(r['timeout'] for r in rows),
                  'killed_by_fcp': {s: sum(r['killed_by'][s] for r in rows) for s in sets},
                  'only_fcp': [r for r in rows if r['killed_by'].get('gold') and not r['killed_by_tests']],
                  'only_tests': [r for r in rows if r['killed_by_tests'] and not r['killed_by'].get('gold')],
                  'all': rows}
        x = out[m]
        print(f'{m:6s} {x["tests"]} tests; {x["observable"]} observable mutants; killed by its own tests '
              f'{x["killed_by_tests"]} ({x["timeouts"]} by a timeout), by FCP ' + ' '.join(f'{s}:{n}' for s, n in x['killed_by_fcp'].items()))
        for tag, key in (('only FCP (gold)', 'only_fcp'), ('only the tests', 'only_tests')):
            for r in x[key]:
                e = r['example'] or {}
                print(f'    {tag}: {r["desc"]}: {e.get("call")} -> {e.get("mutant")} instead of {e.get("original")}')
    with open(os.path.join(HERE, 'results', f'{corpus}_own_tests.json'), 'w') as f:
        json.dump(out, f, indent=1)


if __name__ == '__main__':
    main()
