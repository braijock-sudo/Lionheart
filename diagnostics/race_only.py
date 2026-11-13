#!/usr/bin/env python3
"""Install just the race resource from an existing Aetherian prototype package.

Place this script beside the prototype's install.py and manifest.json.
No game resources are embedded or downloaded by this diagnostic tool.
"""
import importlib.util
from pathlib import Path
import sys


def load_installer(folder):
    if not (folder / 'install.py').is_file() or not (folder / 'manifest.json').is_file():
        raise ValueError('Place race_only.py in the unpacked mod folder, beside install.py and manifest.json.')
    spec = importlib.util.spec_from_file_location('aetherian_diagnostic_installer', folder / 'install.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.STATE = '.aetherian-race-test'
    original_plan = module.plan

    def race_plan(game):
        if (game / '.aetherian-0.1').exists():
            raise ValueError('Uninstall the full prototype with install.py --uninstall before testing only the race.')
        # Validate the original package and restored source files before filtering.
        changes = original_plan(game)
        selected = [x for x in changes if x[0] == 'Data/Resources/Races/Aetherian.Race']
        if len(selected) != 1 or selected[0][1] is not None:
            raise ValueError('Expected exactly one new Aetherian race resource in the original package.')
        return selected

    module.plan = race_plan
    return module


def main():
    if sys.version_info < (3, 8):
        print('ERROR: Python 3.8 or newer is required.', file=sys.stderr)
        return 1
    print('DIAGNOSTIC: race resource only. No skill, spell, mana, dialogue or localization changes.')
    try:
        installer = load_installer(Path(__file__).resolve().parent)
        return installer.main()
    except (ValueError, OSError) as error:
        print('ERROR: ' + str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
