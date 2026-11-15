"""Write the planted-bug variants bugs/<id>.py from impl/ref.py and the
patches in bugs/bugs.yaml.  Each patch target must occur exactly once."""
from __future__ import annotations

import os

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))


def bugs() -> list[dict]:
    with open(os.path.join(HERE, 'bugs', 'bugs.yaml')) as f:
        return yaml.safe_load(f)['bugs']


def materialize() -> dict[str, str]:
    with open(os.path.join(HERE, 'impl', 'ref.py')) as f:
        ref = f.read()
    out = {}
    for b in bugs():
        old, new = b['patch']['from'], b['patch']['to']
        if ref.count(old) != 1:
            raise ValueError(f'{b["id"]}: patch target occurs {ref.count(old)} times')
        p = os.path.join(HERE, 'bugs', f'{b["id"]}.py')
        with open(p, 'w') as f:
            f.write(ref.replace(old, new))
        out[b['id']] = p
    return out


if __name__ == '__main__':
    for k, v in materialize().items():
        print(k, '->', os.path.relpath(v, HERE))
