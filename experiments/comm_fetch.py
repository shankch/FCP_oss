"""HumanEvalComm, fetched at a pinned commit and checked against recorded hashes.

    python experiments/comm_fetch.py

HumanEvalComm (Wu and Fard, ACM TOSEM 2025, arXiv 2406.00215) rewrites the
164 HumanEval problem descriptions so that they are ambiguous (1a),
inconsistent (1c) or incomplete (1p).  Its data is published under
Apache-2.0 (Hugging Face dataset jie-jw-wu/HumanEvalComm); HumanEval itself
is MIT.  The files go to .tools/humanevalcomm-dl/, which is not committed;
they are data only: nothing in them is run.
"""
import hashlib
import os
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEST = os.path.join(ROOT, '.tools', 'humanevalcomm-dl')
COMMIT = '794a91f3c520e3939b8361e9f4ae927c25756a6e'
BASE = f'https://raw.githubusercontent.com/jie-jw-wu/human-eval-comm/{COMMIT}/'
FILES = {       # path in the repository -> sha256
    'Benchmark/HumanEvalComm_v2.jsonl': 'd00e17962e8bfe9d383431f42b5591cd8f431f9ac8b66b9e4b7d1515cc8ab2aa',
}


def main():
    os.makedirs(DEST, exist_ok=True)
    for path, want in FILES.items():
        dst = os.path.join(DEST, os.path.basename(path))
        if not os.path.exists(dst):
            req = urllib.request.Request(BASE + path, headers={'User-Agent': 'fcp-build'})
            with urllib.request.urlopen(req, timeout=120) as r, open(dst + '.part', 'wb') as f:
                f.write(r.read())
            os.replace(dst + '.part', dst)
        with open(dst, 'rb') as f:
            got = hashlib.sha256(f.read()).hexdigest()
        if got != want:
            sys.exit(f'{dst}: sha256 {got}, expected {want}')
        print('ok', os.path.relpath(dst, ROOT))


if __name__ == '__main__':
    main()
