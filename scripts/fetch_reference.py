#!/usr/bin/env python3
"""Download pinned GenePattern reference tables, checking Git blob SHA-1 and size."""
import argparse
import hashlib
import json
from pathlib import Path
import urllib.request

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('output', type=Path)
a = p.parse_args()
manifest = json.loads((Path(__file__).resolve().parents[1]/'tests/genepattern-reference.json').read_text())
a.output.mkdir(parents=True, exist_ok=False)
for item in manifest['files']:
    url = f"https://raw.githubusercontent.com/{manifest['repository']}/{manifest['commit']}/{item['path']}"
    data = urllib.request.urlopen(url,timeout=120).read()
    digest = hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
    if digest != item['sha'] or len(data) != item['size']:
        raise ValueError(f'integrity check failed: {url}')
    name = Path(item['path']).name.removeprefix('segmentationfile.')
    (a.output/name).write_bytes(data)
    print(name, digest, flush=True)
print('Use the genepattern profile; the standalone example uses different options.')
