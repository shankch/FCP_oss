"""Write the planted-bug variants bugs/<id>/loyalty from the package
impl/ref/loyalty and the patches in bugs/bugs.yaml.  Each patch names one
module of the package, and its target must occur exactly once there."""
from __future__ import annotations

import os
import shutil

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = 'loyalty'


def bugs() -> list[dict]:
    with open(os.path.join(HERE, 'bugs', 'bugs.yaml')) as f:
        return yaml.safe_load(f)['bugs']


def materialize() -> dict[str, str]:
    ref = os.path.join(HERE, 'impl', 'ref', PKG)
    out = {}
    for b in bugs():
        with open(os.path.join(ref, b['file'])) as f:
            src = f.read()
        old, new = b['patch']['from'], b['patch']['to']
        if src.count(old) != 1:
            raise ValueError(f'{b["id"]}: patch target occurs {src.count(old)} times in {b["file"]}')
        d = os.path.join(HERE, 'bugs', b['id'])
        shutil.rmtree(d, ignore_errors=True)
        shutil.copytree(ref, os.path.join(d, PKG), ignore=shutil.ignore_patterns('__pycache__'))
        with open(os.path.join(d, PKG, b['file']), 'w') as f:
            f.write(src.replace(old, new))
        out[b['id']] = d
    return out


if __name__ == '__main__':
    for k, v in materialize().items():
        print(k, '->', os.path.relpath(v, HERE))
