"""Restore the archived planning atlas and verify the original SHA-256."""

import hashlib
import json
import os
import tempfile
from pathlib import Path


def file_hash(path):
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def main():
    folder = Path(__file__).resolve().parent
    manifest = json.loads((folder / 'manifest.json').read_text(encoding='utf-8'))
    destination = folder.parent / manifest['original_name']
    if destination.exists():
        if file_hash(destination) != manifest['sha256']:
            raise FileExistsError(f'Existing file has a different hash: {destination}')
        print(f'Original already present and verified: {destination}')
        return

    with tempfile.TemporaryDirectory(prefix='atlas-restore-', dir=folder) as temporary:
        restored = Path(temporary) / 'atlas.pdf'
        with restored.open('wb') as output:
            for part in manifest['parts']:
                source = folder / part['name']
                digest = hashlib.sha256()
                size = 0
                with source.open('rb') as handle:
                    for block in iter(lambda: handle.read(1024 * 1024), b''):
                        digest.update(block)
                        size += len(block)
                        output.write(block)
                if size != part['bytes'] or digest.hexdigest() != part['sha256']:
                    raise ValueError(f'Archive part failed verification: {source.name}')
        if restored.stat().st_size != manifest['bytes'] or file_hash(restored) != manifest['sha256']:
            raise ValueError('Restored atlas failed original-file verification')
        try:
            os.link(restored, destination)
        except FileExistsError:
            if file_hash(destination) != manifest['sha256']:
                raise
    print(f'Restored and verified: {destination}')


if __name__ == '__main__':
    main()
