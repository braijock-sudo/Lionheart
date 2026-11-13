#!/usr/bin/env python3
"""Reversible, hash-checked installer. Requires Python 3.8 or newer."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile

HERE = Path(__file__).resolve().parent
STATE = '.aetherian-0.1'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def safe_path(root, relative):
    p = Path(relative)
    if p.is_absolute() or '..' in p.parts or '\\' in relative or ':' in relative:
        raise ValueError(f'Unsafe manifest path: {relative}')
    target = root.joinpath(p)
    try:
        target.resolve().relative_to(root.resolve())
    except ValueError:
        raise ValueError(f'Path leaves game directory: {relative}') from None
    return target


def atomic_write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix='.aetherian-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(data)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def plan(game):
    manifest = json.loads((HERE / 'manifest.json').read_text())
    changes = []
    for entry in manifest['files']:
        target = safe_path(game, entry['path'])
        if target.exists():
            raise ValueError(f"New resource already exists: {entry['path']}. Uninstall the old prototype first.")
        payload = safe_path(HERE / 'payload', entry['path']).read_bytes()
        if digest(payload) != entry['sha256']:
            raise ValueError('Damaged mod payload: ' + entry['path'])
        changes.append((entry['path'], None, payload))
    for entry in manifest['patches']:
        target = safe_path(game, entry['path'])
        original = target.read_bytes()
        if digest(original) != entry['source_sha256']:
            raise ValueError('Different or previously modified source file: ' + entry['path'] +
                '\nThis build targets the supplied archive. No files have been installed.')
        encoding = entry.get('encoding', 'cp1252')
        text = original.decode(encoding)
        for replacement in entry['replacements']:
            if text.count(replacement['old']) != replacement['count']:
                raise ValueError('Patch anchor mismatch: ' + entry['path'])
            text = text.replace(replacement['old'], replacement['new'])
        updated = text.encode(encoding)
        if digest(updated) != entry['result_sha256']:
            raise ValueError('Patch checksum mismatch: ' + entry['path'])
        changes.append((entry['path'], original, updated))
    return changes


def recover(game, state, entries):
    for entry in reversed(entries):
        p = safe_path(game, entry['path'])
        if entry['original_sha256'] is None:
            p.unlink(missing_ok=True)
        else:
            atomic_write(p, safe_path(state / 'backup', entry['path']).read_bytes())


def install(game):
    state = game / STATE
    if state.exists():
        raise ValueError('Aetherian state directory already exists. Use --uninstall first.')
    changes = plan(game)  # Validate every input before creating anything in the game.
    records = [{'path': path, 'original_sha256': digest(old) if old is not None else None,
                'installed_sha256': digest(new)} for path, old, new in changes]
    state.mkdir()
    try:
        for path, old, _ in changes:
            if old is not None:
                atomic_write(safe_path(state / 'backup', path), old)
        atomic_write(state / 'state.json', json.dumps({'phase': 'installing', 'files': records}, indent=2).encode())
    except BaseException:
        shutil.rmtree(state)
        raise
    try:
        for path, _, data in changes:
            atomic_write(safe_path(game, path), data)
        atomic_write(state / 'state.json', json.dumps({'phase': 'installed', 'files': records}, indent=2).encode())
    except BaseException:
        recover(game, state, records)
        shutil.rmtree(state)
        raise
    print(f'Installed {len(changes)} experimental resource changes. Backups: {state}')
    print('Start a NEW game, choose Aetherian and Female. See README_PL.md for known limitations.')


def uninstall(game):
    state = game / STATE
    data = json.loads((state / 'state.json').read_text())
    records = data['files']
    # Never overwrite edits made after installation. Validate all backups too.
    for entry in records:
        target = safe_path(game, entry['path'])
        current = digest(target.read_bytes()) if target.is_file() else None
        allowed = {entry['installed_sha256']}
        if data['phase'] == 'installing':
            allowed.add(entry['original_sha256'])
        if current not in allowed:
            raise ValueError('File changed or removed since installation; keep your changes before uninstalling: ' + entry['path'])
        if entry['original_sha256'] is not None:
            original = safe_path(state / 'backup', entry['path']).read_bytes()
            if digest(original) != entry['original_sha256']:
                raise ValueError('Backup damaged: ' + entry['path'])
    recover(game, state, records)
    shutil.rmtree(state)
    print('Uninstalled. Original resource files restored byte for byte. Saves were not changed.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game', required=True, type=Path, help='Directory containing Lionheart.exe and Data')
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--check', action='store_true', help='Validate compatibility without writing game files')
    mode.add_argument('--install', action='store_true')
    mode.add_argument('--uninstall', action='store_true')
    args = parser.parse_args()
    game = args.game.expanduser().resolve()
    if not (game / 'Lionheart.exe').is_file():
        parser.error('The game directory must contain Lionheart.exe')
    try:
        if args.check:
            changes = plan(game)
            print(f'Compatible files: {len(changes)} planned changes. No game files written.')
        elif args.install:
            install(game)
        else:
            uninstall(game)
    except (ValueError, OSError, KeyError) as error:
        print('ERROR: ' + str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    if sys.version_info < (3, 8):
        sys.exit('ERROR: Python 3.8 or newer is required. Check your version with: py -3 --version')
    sys.exit(main())
