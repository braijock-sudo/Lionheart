"""Build experimental Aetherian resources from the supplied installation.

No executable patching; inherited assets remain in the user's game directory.
"""
from pathlib import Path
import copy
import hashlib
import json
from engine_text import Node, parse, dump, get, scalar as s, obj as o, array as a, constant as c, walk

BASE = Path('/workspace/work/extracted')
OUT = Path('/workspace/work/aetherian/package')
RES = BASE / 'Data/Resources'
RACE = 'Races/Aetherian'
FIRE = 'Derived Character Attributes/Aetherian/Divine Fire Active'
OFFHAND = 'Derived Character Attributes/Aetherian/Offhand Active'
RECEIVED = 'Derived Character Attributes/Aetherian/Starter Received'
MAIN = 'Inventory Items/Aetherian/Dawn Chakram'
LEFT = 'Inventory Items/Aetherian/Dusk Chakram'
PROJECTILE = 'Spell Projectiles/Aetherian/Light Chakram'
THROW = 'Skills/Aetherian/Chakram Throw'
IGNITE = 'Skills/Aetherian/Divine Fire'
WINGS = 'Skills/Aetherian/Wings of Dawn'
manifest = {'version': '0.1.0-experimental', 'runtime_tested': False, 'files': [], 'patches': []}


def load(rel):
    return parse((RES / rel).read_bytes().decode('cp1252'))


def write(rel, nodes):
    data = dump(nodes).encode('ascii')
    path = OUT / 'payload' / 'Data/Resources' / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    manifest['files'].append({'path': 'Data/Resources/' + rel,
                              'sha256': hashlib.sha256(data).hexdigest()})


def ref(key, name):
    return o(key, 'CVariableDerivedCharacterAttribute', [s('Character Attribute', name)])


def binary(key, cls, left, right):
    left, right = copy.deepcopy(left), copy.deepcopy(right)
    left.key, right.key = 'Operand1', 'Operand2'
    return o(key, cls, [left, s('Operator'), right])


def random(key, lo, hi):
    return o(key, 'CRandom', [s('Operator'), c('Minimum', lo), c('Maximum', hi)])


def race_check(key):
    return o(key, 'CIsRace', [a('Acceptable Races', [s('Acceptable Race', RACE)])])


def modifier(attribute, value):
    return o('Modifier', 'CCharacterModifierDerivedAttribute', [
        c('Modification Amount', value), s('Modification amount is a percent', 0),
        s('Allow Accumulation', 0), s('Derived character attribute to modify', attribute)])


def requirements(key='Requirements', extra=()):
    r = race_check('Requirements')
    return a(key, [r, *extra])


def damage(dtype, expression):
    expression = copy.deepcopy(expression)
    expression.key = 'Damage Amount'
    return o('Damage', 'CXRPGDamage', [s('Damage Type', 'Damage Types/' + dtype), expression])


def fire_damage():
    return damage('Fire', binary('', 'CMultiply', ref('', FIRE), random('', 2, 4)))


def offhand_damage():
    return damage('Slashing', binary('', 'CMultiply', ref('', OFFHAND), random('', 1, 3)))


def derived(rel, name, imported=0):
    nodes = load('Derived Character Attributes/Game Scripting Variables/Player has cast a spell.DerivedCharacterAttribute')
    body = nodes[0].children
    get(body, 'Short Name').value = name
    get(body, 'Long Name').value = name
    get(body, 'Description').value = 'Aetherian prototype state.'
    get(body, 'Include in character Import and Export').value = str(imported)
    write('Derived Character Attributes/Aetherian/' + rel + '.DerivedCharacterAttribute', nodes)


def patch_expression(rel, new_value):
    # Preserve every other byte in the original resource; replace one expression.
    raw = (RES / rel).read_bytes()
    nodes = parse(raw.decode('cp1252'))
    old = get(nodes[0].children, 'Expression')
    before = dump([old]).strip()
    replacement = o('Expression', 'CIfExpression', [race_check('Condition'), s('OperatorPart1'),
        c('Value if True ', new_value), s('OperatorPart2'),
        Node('Value if False', old.value, copy.deepcopy(old.children))])
    # The serializer normalizes indent; find original expression range by lines.
    lines = raw.decode('cp1252').splitlines(keepends=True)
    start = next(i for i, x in enumerate(lines) if x.startswith('\tExpression='))
    depth = 0
    end = start + 1
    for i in range(start + 1, len(lines)):
        line = lines[i].strip()
        depth += (line == '{') - (line == '}')
        if depth == 0:
            end = i + 1
            break
    old_bytes = ''.join(lines[start:end]).encode('cp1252')
    new_bytes = ('\r\n'.join('\t' + line for line in dump([replacement]).splitlines()) + '\r\n').encode('ascii')
    updated = raw.replace(old_bytes, new_bytes, 1)
    assert updated != raw
    parse(updated.decode('cp1252'))
    manifest['patches'].append({'path': 'Data/Resources/' + rel,
        'source_sha256': hashlib.sha256(raw).hexdigest(),
        'result_sha256': hashlib.sha256(updated).hexdigest(),
        'replacements': [{'old': old_bytes.decode('cp1252'), 'new': new_bytes.decode('ascii'), 'count': 1}]})


def skill(rel, display, description, image, plugins, order):
    nodes = load('Skills/Fighting/OneHandedMelee.Skill')
    b = nodes[0].children
    get(b, 'PlugIn Behaviors').children = a('', plugins).children
    for k, v in [('Display Name', display), ('Description', description),
        ('Character Creation Screen Description', description), ('Parent Skill', 'Skills/Aetherian'),
        ('Can be selected as Tag Skill', '0'), ('Image', image), ('Sort Priority', str(order)),
        ('Amount To Increase Value By With Each Upgrade', '0'), ('Minimum Value', '1'),
        ('Maximum Value', '1'), ('Initial Minimum & Maximum', '1.000000,1.000000')]:
        get(b, k).value = v
    b[b.index(get(b, 'Initial Value'))] = c('Initial Value', 1)
    for key in ['Display and Cast Requirements', 'Cast Requirements']:
        b[b.index(get(b, key))] = requirements(key)
    write(rel + '.Skill', nodes)


def spell(cost, cooldown, range_=700):
    return o('PlugIn Behavior', 'CPlugInBehaviorSpell', [c('ManaUse', cost), c('Duration', cooldown),
        s('Automatically disable recasting of spell for duration', 1), c('Maximum Range', range_)])


def sequence():
    return o('PlugIn Behavior', 'CPlugInBehaviorPlaySequence', [a('Granny Animations', []),
        s('Sequence Name', 'SpellCast'), s('Random Sequence Selection', 0), s('Sequence Index', -1)])


def attack(location):
    return o('PlugIn Behavior', 'CPlugInBehaviorAttack', [s('Max Attack Range', 700),
        s('Is Location Based', int(location)), s('Can Use Slayer Mode', 0),
        s('Can Use Sniper Mode', 0), s('Action On Hit'), s('Action On Miss')])


def timed_mod(description, modifiers, duration):
    return o('Action', 'CAddCharacterModifierToCharacterAction', [s('Modifier Description', description),
        s('Modification is permanent', 0), s('Character to modify', '$caster'),
        a('Modifiers', modifiers), c('OPTIONAL Duration', duration), s('Expression Context', '$caster')])


def effect(model):
    return o('Action', 'CSpawnEffectAction', [s('Explosion Model', model), s('Location Entity', '$caster'),
        s('Make effect a child of the location entity', 1), s('X Offset', 0), s('Y Offset', 0),
        s('Height Offset', 0), s('Play Default Sound', 1), s('Action to execute After Effect')])


def buff(cost, cooldown, duration, display, mods, model, icon):
    icon_action = o('Action', 'CDisplayAffectingPlayerIconAction', [s('Character Being Affected', '$caster'),
        s('Affect Description', display), s('Icon', icon), c('Duration', duration), s('Expression Context', '$caster')])
    launch = o('PlugIn Behavior', 'CPlugInBehaviorLaunchAction', [
        o('Launch Action', 'CMultipleActionsAction', [a('Action', [timed_mod(display, mods, duration), effect(model), icon_action])])])
    return [spell(cost, cooldown), launch, sequence(), attack(True)]


def give_item(item):
    return o('Action', 'CActionGiveStandardInventoryItem', [s('Who to give to', '$instigator'),
        s('Delete Trigger', 0), s('Notify Player', 1), s('Inventory Item To Give', item), a('Additions to add', [])])


def starter_reply():
    not_received = o('Operand2', 'CIsEqualTo', [ref('Operand1', RECEIVED), s('Operator'), c('Operand2', 0)])
    check = binary('Custom Requirement', 'CAND', race_check(''), not_received)
    flag = o('Action', 'CAddCharacterModifierToCharacterAction', [s('Modifier Description', 'Aetherian starter received'),
        s('Modification is permanent', 1), s('Character to modify', '$instigator'),
        a('Modifiers', [modifier(RECEIVED, 1)]), s('OPTIONAL Duration'), s('Expression Context', '$instigator')])
    return [s('Requirement', '!None'), check,
        s('Reply Text', '[Aetherian] Przywoluje moje czakramy swiatla.'), s('Go to node ID'),
        o('Custom Action', 'CMultipleActionsAction', [a('Action', [give_item(MAIN), give_item(LEFT), flag])])]


def patch_dialogue(rel, node_ids):
    raw = (RES / rel).read_bytes()
    text = raw.decode('cp1252')
    insert = dump(starter_reply()) + '\r\n'
    replacements = []
    for node_id in node_ids:
        # Insert before the first reply, preserving the node's original header/text.
        start = text.index('Node ID=' + node_id + '\r\n')
        pos = text.index('Requirement=', start)
        anchor = text[start:pos]
        assert text.count(anchor) == 1
        replacements.append({'old': anchor, 'new': anchor + insert, 'count': 1})
    updated = text
    for r in replacements:
        updated = updated.replace(r['old'], r['new'], 1)
    parse(updated)
    manifest['patches'].append({'path': 'Data/Resources/' + rel,
        'source_sha256': hashlib.sha256(raw).hexdigest(),
        'result_sha256': hashlib.sha256(updated.encode('cp1252')).hexdigest(),
        'replacements': replacements})


def gate_original_magic():
    """Add a race exclusion to existing spell display AND activation checks."""
    for path in sorted((RES / 'Skills').rglob('*.Skill')):
        raw = path.read_bytes()
        nodes = parse(raw.decode('cp1252'))
        body = nodes[0].children
        plugins = get(body, 'PlugIn Behaviors')
        if not any(n.value == 'CPlugInBehaviorSpell' for n in plugins.children):
            continue
        replacements = []
        for key in ['Display and Cast Requirements', 'Cast Requirements']:
            old = get(body, key)
            old_bytes = ('\r\n'.join('\t' + x for x in dump([old]).splitlines()) + '\r\n').encode('cp1252')
            assert raw.count(old_bytes) == 1, (path, key)
            new = copy.deepcopy(old)
            get(new.children, 'Item Count').value = str(int(get(new.children, 'Item Count').value) + 1)
            new.children.append(o('Requirements', 'CExpressionNot', [race_check('Operand1')]))
            new_bytes = ('\r\n'.join('\t' + x for x in dump([new]).splitlines()) + '\r\n').encode('cp1252')
            replacements.append({'old': old_bytes.decode('cp1252'), 'new': new_bytes.decode('cp1252'), 'count': 1})
        updated = raw.decode('cp1252')
        for r in replacements:
            updated = updated.replace(r['old'], r['new'], 1)
        parse(updated)
        manifest['patches'].append({'path': 'Data/Resources/' + str(path.relative_to(RES)),
            'source_sha256': hashlib.sha256(raw).hexdigest(),
            'result_sha256': hashlib.sha256(updated.encode('cp1252')).hexdigest(),
            'replacements': replacements})


def localize_polish():
    raw = (BASE / 'Local.txt').read_bytes()
    assert raw.startswith(b'\xff\xfe')
    text = raw.decode('utf-16le')
    translations = {
        'Czakram Switu [prototyp]': 'Czakram Świtu [prototyp]',
        'Czakram Brzasku [druga reka]': 'Czakram Brzasku [druga ręka]',
        'Boski Ogien': 'Boski Ogień',
        'Skrzydla Brzasku': 'Skrzydła Brzasku',
        'Aetherian - dyscypliny swiatla': 'Aetherian — dyscypliny światła',
        '[Aetherian] Przywoluje moje czakramy swiatla.': '[Aetherian] Przywołuję moje czakramy światła.',
        'Racial abilities. Energy uses the existing Mana pool in this prototype.':
            'Zdolności rasowe. Energia korzysta w tym prototypie z istniejącego paska many.',
        '2-5 slashing. Offhand chakram adds 1-3 slashing; Divine Fire adds 2-4 fire. Temporary scimitar mesh.':
            '2–5 obrażeń ciętych. Drugi czakram dodaje 1–3 obrażeń ciętych, a Boski Ogień 2–4 obrażeń od ognia. Tymczasowy model szabli; +10% szybkości animacji ataku.',
        'Offhand focus: +1 AC and +1-3 slashing on the Dawn Chakram and Chakram Throw. Temporary shield mesh; no independent offhand animation.':
            'Druga ręka: +1 do klasy pancerza i +1–3 obrażeń ciętych Czakramem Świtu oraz Rzutem Czakramem. Tymczasowy model tarczy; bez osobnej animacji drugiej ręki.',
        '12 Energy; 1.2s recovery. 7-11 slashing, plus offhand and Divine Fire bonuses. Existing luminous ice-ring visual; no return trajectory.':
            '12 energii; odnowienie 1,2 s. 7–11 obrażeń ciętych oraz premie drugiego czakramu i Boskiego Ognia. Zastępczy efekt świetlistego lodowego pierścienia; bez lotu powrotnego.',
        '20 Energy; 12s recovery. For 12 seconds, Dawn Chakram and Chakram Throw deal +2-4 fire damage. Does not stack.':
            '20 energii; odnowienie 12 s. Przez 12 s Czakram Świtu i Rzut Czakramem zadają dodatkowe 2–4 obrażeń od ognia. Efekt nie kumuluje się.',
        '25 Energy; 20s recovery. For 6 seconds, +15% movement speed and +5 AC. No flight; wings are not yet integrated.':
            '25 energii; odnowienie 20 s. Przez 6 s: +15% szybkości ruchu i +5 do klasy pancerza. Bez latania; model skrzydeł nie jest jeszcze zintegrowany.',
    }
    for item in manifest['files']:
        if item['path'].endswith('Aetherian.Race'):
            body = parse((OUT / 'payload' / item['path']).read_text())[0].children
            translations[get(body, 'Description').value] = (
                'Aetherianie to pomniejsze istoty niebiańskie. Prototyp: wybierz płeć żeńską; '
                'obecnie używany jest model człowieka. Czakramy i trzy zdolności rasowe korzystają '
                'ze wspólnej puli 100 energii (silnik nadal nazywa ją maną), odnawianej po 3 na sekundę.')
    appendix = '\r\n' + '\r\n'.join(
        'ENGLISH: ' + eng + '[END]\r\nLOCALIZED: ' + pl + '[END]\r\n'
        for eng, pl in translations.items())
    anchor = text[-500:]
    assert text.count(anchor) == 1
    updated = text + appendix
    manifest['patches'].append({'path': 'Local.txt', 'encoding': 'utf-16le',
        'source_sha256': hashlib.sha256(raw).hexdigest(),
        'result_sha256': hashlib.sha256(updated.encode('utf-16le')).hexdigest(),
        'replacements': [{'old': anchor, 'new': anchor + appendix, 'count': 1}]})


def build():
    for name in ['Divine Fire Active', 'Offhand Active', 'Starter Received']:
        derived(name, name, int(name == 'Starter Received'))

    race = load('Races/Human.Race')
    b = race[0].children
    get(b, 'Display Name').value = 'Aetherian'
    get(b, 'Description').value = ('Aetherians are lesser celestial beings. Prototype: choose Female; '
        'the current appearance uses the human model. Light chakrams and three racial abilities use '
        'a shared 100-point Energy pool (the engine still calls it Mana), regenerating 3 per second.')
    attrs = get(b, 'Initial CharacterAttribute Values').children
    values = {'(AG) Agility': '6,2,10', '(CH) Charisma': '6,2,10', '(EN) Endurance': '4,1,9',
        '(IN) Intelligence': '5,3,10', '(LK) Luck': '4,1,10', '(PE) Perception': '6,2,10', '(ST) Strength': '4,1,9'}
    for n in attrs:
        n.value = values[n.key.removeprefix('Character Attributes/')]
    for n in get(b, 'Character Model').children:
        n.value = 'Characters/Player Characters/Human Female'
    write('Races/Aetherian.Race', race)

    root = load('Skills/Fighting/OneHandedMelee.Skill')
    b = root[0].children
    get(b, 'Display Name').value = 'Aetherian - dyscypliny swiatla'
    get(b, 'Description').value = 'Racial abilities. Energy uses the existing Mana pool in this prototype.'
    get(b, 'Character Creation Screen Description').value = get(b, 'Description').value
    get(b, 'Can be selected as Tag Skill').value = '0'
    get(b, 'Amount To Increase Value By With Each Upgrade').value = '0'
    get(b, 'Image').value = 'Skills/Magic Divine/Defensive/Physical Aura'
    b[b.index(get(b, 'Initial Value'))] = c('Initial Value', 1)
    for key in ['Display and Cast Requirements', 'Cast Requirements']:
        b[b.index(get(b, key))] = requirements(key)
    write('Skills/Aetherian.Skill', root)

    patch_expression('Derived Character Attributes/Mana Capacity.DerivedCharacterAttribute', 100)
    patch_expression('Derived Character Attributes/Mana Replenishment Rate.DerivedCharacterAttribute', 3)

    # Main-hand prototype retains the original scimitar mesh and attack sequence.
    main = load('Inventory Items/Scimitar.InventoryItem')
    b = main[0].children
    plugins = get(b, 'PlugIn Behaviors').children
    dmg = next(n for n in plugins if n.value == 'CPlugInBehaviorDamage')
    get(dmg.children, 'Damages').children = a('', [damage('Slashing', random('', 2, 5)), offhand_damage(), fire_damage()]).children
    get(b, 'Display Name').value = 'Czakram Switu [prototyp]'
    get(b, 'Description').value = '2-5 slashing. Offhand chakram adds 1-3 slashing; Divine Fire adds 2-4 fire. Temporary scimitar mesh.'
    get(b, 'Origonal Item').value = MAIN
    get(b, 'Encumbrance').value = '2'
    get(b, 'Is Magic').value = '1'
    b[b.index(get(b, 'Requirements'))] = requirements()
    for n in get(b, 'Inventory Window Images').children:
        n.value = 'Items/Inventory Images/Misc Items/RingGold White'
    write('Inventory Items/Aetherian/Dawn Chakram.InventoryItem', main)

    left = load('Inventory Items/ShieldSmall.InventoryItem')
    b = left[0].children
    plugins = get(b, 'PlugIn Behaviors').children
    modplugin = next(n for n in plugins if n.value == 'CPlugInBehaviorModifyCharacterWhenSelected')
    get(modplugin.children, 'Modifier Description').value = 'Aetherian second chakram'
    get(modplugin.children, 'Modifiers').children = a('', [modifier(OFFHAND, 1), modifier('Derived Character Attributes/(AC) Armor Class', 1)]).children
    for k, v in [('Display Name', 'Czakram Brzasku [druga reka]'),
        ('Description', 'Offhand focus: +1 AC and +1-3 slashing on the Dawn Chakram and Chakram Throw. Temporary shield mesh; no independent offhand animation.'),
        ('Origonal Item', LEFT), ('Encumbrance', '2'), ('Is Magic', '1')]:
        get(b, k).value = v
    b[b.index(get(b, 'Requirements'))] = requirements()
    for n in get(b, 'Inventory Window Images').children:
        n.value = 'Items/Inventory Images/Misc Items/RingGold White'
    write('Inventory Items/Aetherian/Dusk Chakram.InventoryItem', left)

    projectile = load('Inventory Items/Celestial Smite Projectile.InventoryItem')
    b = projectile[0].children
    plugins = get(b, 'PlugIn Behaviors').children
    get(next(n for n in plugins if n.value == 'CPlugInBehaviorProjectile').children,
        'Projectile Model').value = 'Spell Effects/Shots/Ice Ring'
    dmg = next(n for n in plugins if n.value == 'CPlugInBehaviorDamage')
    get(dmg.children, 'Damages').children = a('', [damage('Slashing', random('', 7, 11)), offhand_damage(), fire_damage()]).children
    get(b, 'Display Name').value = 'Light Chakram Projectile'
    get(b, 'Origonal Item').value = PROJECTILE
    write('Spell Projectiles/Aetherian/Light Chakram.InventoryItem', projectile)

    source = load('Skills/Magic Thought/Offensive/Fire Orb.Skill')
    launcher = copy.deepcopy(next(n for n in get(source[0].children, 'PlugIn Behaviors').children if n.value == 'CXRPGPlugInBehaviorLauncher'))
    get(launcher.children, 'Secondary Launchable Types').children = a('', [s('Secondary Launchable Type', PROJECTILE)]).children
    get(launcher.children, 'Dispersion Angle').value = '0'
    skill('Skills/Aetherian/Chakram Throw', 'Rzut Czakramem',
        '12 Energy; 1.2s recovery. 7-11 slashing, plus offhand and Divine Fire bonuses. Existing luminous ice-ring visual; no return trajectory.',
        'Skills/Magic Thought/Offensive/Ice Missile', [spell(12, 1.2), launcher, sequence(), attack(False)], 1)

    skill('Skills/Aetherian/Divine Fire', 'Boski Ogien',
        '20 Energy; 12s recovery. For 12 seconds, Dawn Chakram and Chakram Throw deal +2-4 fire damage. Does not stack.',
        'Skills/Magic Divine/Defensive/Holy Fire', buff(20, 12, 12, 'Boski Ogien', [modifier(FIRE, 1)],
        'Spell Effects/Hits and Effects/Target Affected/Divine Strength',
        'Temporary Modifier HUD Icons/Divine Spell Effects/Divine Power'), 2)

    skill('Skills/Aetherian/Wings of Dawn', 'Skrzydla Brzasku',
        '25 Energy; 20s recovery. For 6 seconds, +15% movement speed and +5 AC. No flight; wings are not yet integrated.',
        'Skills/Magic Divine/Defensive/Physical Aura', buff(25, 20, 6, 'Skrzydla Brzasku', [
        modifier('Derived Character Attributes/Speed/Walk Magic Speed Multiplier', .15),
        modifier('Derived Character Attributes/(AC) Armor Class', 5)],
        'Spell Effects/Hits and Effects/Divine Radial Cast Effect',
        'Temporary Modifier HUD Icons/Divine Spell Effects/Divine Power'), 3)

    # All three spirit choices provide the same optional, one-time starter reply.
    for spirit in ['Elemental', 'Bestial', 'Demonic']:
        rel = f'Levels/Start Game/Dialog/Spirit {spirit} Introduction.DialogTree'
        patch_dialogue(rel, ['3 Conversation Continue'])
    patch_dialogue('Levels/1 Barcelona/Dialog/Gate District/Blacksmith.DialogTree', [
        '01 Introduction Non-tainted Male', '01 Introduction, Non-Tainted Female',
        '01 Introduction, Sylvant', '01 Introduction, Feralkin', '01 Introduction, Tainted Demokin',
        '03 Return Dialogue 1 Normal'])

    gate_original_magic()
    localize_polish()

    (OUT / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=True, indent=2) + '\n')
    print(f"Built {len(manifest['files'])} new resources and {len(manifest['patches'])} patches")


if __name__ == '__main__':
    build()
