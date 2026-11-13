"""Static resource validation and installer transaction tests; no game runtime."""
from pathlib import Path
import copy
import importlib.util
import json
import shutil
import tempfile
from unittest.mock import patch
from engine_text import parse, dump, walk, get

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / 'package'
BASE = Path('/workspace/work/extracted')
spec = importlib.util.spec_from_file_location('installer', PKG / 'install.py')
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)
manifest = json.loads((PKG / 'manifest.json').read_text())
checks = []


def passed(message):
    checks.append(message)
    print('PASS', message)


def validate_resources():
    inventory = json.loads(Path('/workspace/work/inventory.json').read_text())
    known = {x['path'].split('/', 1)[1].lower() for x in inventory if '/' in x['path']}
    known.update(x['path'].lower() for x in manifest['files'])
    references = {
        'Parent Skill': [('Data/Resources/', '.Skill')],
        'Skill': [('Data/Resources/', '.Skill')],
        'Acceptable Race': [('Data/Resources/', '.Race')],
        'Derived character attribute to modify': [('Data/Resources/', '.DerivedCharacterAttribute')],
        'Secondary Launchable Type': [('Data/Resources/', '.InventoryItem')],
        'Origonal Item': [('Data/Resources/', '.InventoryItem')],
        'Inventory Item To Give': [('Data/Resources/', '.InventoryItem')],
        'Image': [('Data/Cache/Resources/', '.frm16')],
        'Icon': [('Data/Cache/Resources/', '.frm16')],
        'Projectile Model': [('Data/Cache/Models/', '.mdl16')],
        'Explosion Model': [('Data/Cache/Models/', '.mdl16')],
        'On the ground': [('Data/Cache/Models/', '.mdl16')],
        'Basic': [('Data/Cache/Models/', '.mdl16')],
        'Better': [('Data/Cache/Models/', '.mdl16')],
        'Special': [('Data/Cache/Models/', '.mdl16')],
    }
    executable_strings = Path('/workspace/work/exe-strings.txt').read_text(errors='replace')
    nodes_checked = 0
    for item in manifest['files']:
        raw = (PKG / 'payload' / item['path']).read_bytes()
        assert installer.digest(raw) == item['sha256']
        nodes = parse(raw.decode('ascii'))
        assert parse(dump(nodes)) == nodes
        for n in walk(nodes):
            nodes_checked += 1
            if n.children is not None and n.value.startswith('C'):
                assert n.value in executable_strings, (item['path'], n.value)
            if n.value == 'Array':
                counts = [x for x in n.children if x.key in ['Item Count', 'Array Count']]
                if counts:
                    assert len(counts) == 1
                    assert int(counts[0].value) == len(n.children) - 1, (item['path'], n.key)
            candidates = references.get(n.key)
            if n.key == 'Character Attribute':
                ext = '.CharacterAttribute' if n.value.startswith('Character Attributes/') else '.DerivedCharacterAttribute'
                candidates = [('Data/Resources/', ext)]
            if candidates and n.value not in ['!Unknown Model', '']:
                assert any((pre + n.value + ext).lower() in known for pre, ext in candidates), (item['path'], n.key, n.value)
    passed(f'{len(manifest["files"])} resources: parse/serialize, array counts, classes and references ({nodes_checked} nodes)')


def test_resource_logic():
    race = parse((PKG / 'payload/Data/Resources/Races/Aetherian.Race').read_text())[0].children
    values = [x.value.split(',') for x in get(race, 'Initial CharacterAttribute Values').children]
    assert sum(int(x[0]) for x in values) == 35
    assert int(get(race, 'Initial Character Attribute Maximum Total').value) == 41
    assert all(int(x[1]) <= int(x[0]) <= int(x[2]) for x in values)
    passed('Race: 35 initial attribute points, 6 spendable, valid ranges')
    for patch_ in manifest['patches'][:2]:
        raw = (BASE / patch_['path']).read_bytes()
        replacement = patch_['replacements'][0]
        new = raw.decode('cp1252').replace(replacement['old'], replacement['new']).encode('cp1252')
        original = get(parse(raw.decode('cp1252'))[0].children, 'Expression')
        conditional = get(parse(new.decode('cp1252'))[0].children, 'Expression')
        assert conditional.value == 'CIfExpression'
        false = get(conditional.children, 'Value if False')
        assert false.value == original.value and false.children == original.children
        race_cond = get(conditional.children, 'Condition')
        assert get(get(race_cond.children, 'Acceptable Races').children, 'Acceptable Race').value == 'Races/Aetherian'
        value = int(get(get(conditional.children, 'Value if True ').children, 'Constant Value').value)
        assert value == (100 if 'Mana Capacity.' in patch_['path'] else 3)
    passed('Energy: race-specific 100 capacity/3 regeneration; original expression preserved for other races')
    for skill in ['Chakram Throw', 'Divine Fire', 'Wings of Dawn']:
        nodes = parse((PKG / f'payload/Data/Resources/Skills/Aetherian/{skill}.Skill').read_text())[0].children
        for key in ['Display and Cast Requirements', 'Cast Requirements']:
            assert any(n.value == 'Races/Aetherian' for n in walk([get(nodes, key)]))
    passed('All three active abilities restricted to Aetherian for display and activation')
    gated = 0
    for patch_ in manifest['patches']:
        if not patch_['path'].endswith('.Skill'):
            continue
        original = (BASE / patch_['path']).read_bytes().decode('cp1252')
        updated = original
        for r in patch_['replacements']:
            updated = updated.replace(r['old'], r['new'], 1)
        body = parse(updated)[0].children
        for key in ['Display and Cast Requirements', 'Cast Requirements']:
            items = get(body, key).children
            assert int(get(items, 'Item Count').value) == len(items) - 1
            assert items[-1].value == 'CExpressionNot'
            assert any(n.value == 'Races/Aetherian' for n in walk([items[-1]]))
        gated += 1
    passed(f'{gated} original spell definitions exclude Aetherian in display and cast requirements')


def fixture(root):
    (root / 'Lionheart.exe').write_bytes(b'fixture-only-not-executable')
    for item in manifest['patches']:
        path = root / item['path']
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(BASE / item['path'], path)


def snapshot(root):
    return {str(p.relative_to(root)): p.read_bytes() for p in root.rglob('*') if p.is_file()}


def must_fail(callback):
    try:
        callback()
    except (ValueError, OSError):
        return
    raise AssertionError('Expected rejection')


def transaction_tests():
    with tempfile.TemporaryDirectory(prefix='aetherian-test-', dir=ROOT) as tmp:
        game = Path(tmp)
        fixture(game)
        before = snapshot(game)
        changes = installer.plan(game)
        assert len(changes) == len(manifest['files']) + len(manifest['patches']) and snapshot(game) == before
        passed('Compatibility check writes no game files')
        installer.install(game)
        for path, old, expected in changes:
            assert (game / path).read_bytes() == expected
        passed(f'Installer writes all {len(changes)} changes and stores backups')
        target = game / manifest['files'][0]['path']
        original = target.read_bytes()
        target.write_bytes(original + b'edit')
        edited = snapshot(game)
        must_fail(lambda: installer.uninstall(game))
        assert snapshot(game) == edited
        target.write_bytes(original)
        passed('Uninstall refuses to overwrite user edits; no partial restoration')
        installer.uninstall(game)
        assert snapshot(game) == before
        passed('Install/uninstall restores all original bytes and removes new resources')
        target = game / manifest['patches'][-1]['path']
        original = target.read_bytes()
        target.write_bytes(original + b'edited')
        edited = snapshot(game)
        must_fail(lambda: installer.install(game))
        assert snapshot(game) == edited
        target.write_bytes(original)
        passed('Source mismatch aborts before any game file changes')
        real_atomic = installer.atomic_write
        calls = 0

        def fail_once(path, data):
            nonlocal calls
            calls += 1
            if calls == len(manifest['patches']) + 4:
                raise OSError('Simulated interrupted disk write')
            real_atomic(path, data)

        with patch.object(installer, 'atomic_write', fail_once):
            must_fail(lambda: installer.install(game))
        assert snapshot(game) == before
        passed('Simulated mid-install failure rolls back all game files')


if __name__ == '__main__':
    validate_resources()
    test_resource_logic()
    transaction_tests()
    report = {'scope': 'STATIC VALIDATION AND INSTALLER TESTS ONLY', 'runtime_tested': False,
              'checks_passed': checks}
    (PKG / 'validation.json').write_text(json.dumps(report, indent=2) + '\n')
