"""Offline package checks; not a Home Assistant schema/runtime validator."""
import argparse
from pathlib import Path
import re
import sys

import yaml

ROOT = Path(__file__).resolve().parents[1]


class UniqueLoader(yaml.SafeLoader):
    pass


def unique_mapping(loader, node):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node)
        if key in result:
            raise ValueError(f"Duplicate YAML key {key!r} at line {key_node.start_mark.line + 1}")
        result[key] = loader.construct_object(value_node)
    return result


UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping)
# Parse include paths as strings; do not read arbitrary local includes.
UniqueLoader.add_constructor('!include_dir_named', lambda loader, node: loader.construct_scalar(node))


def check(path, deploy):
    text = path.read_text(encoding='utf-8')
    data = yaml.load(text, Loader=UniqueLoader)
    assert isinstance(data, dict), 'Package must be a mapping'
    scripts = data['script']
    expected = {'household_music_player_config', 'household_music_sleep_scheduler',
                'bedroom_search_and_play', 'bedroom_music_tools'}
    assert expected <= scripts.keys(), 'Missing required scripts'
    for name in expected:
        assert scripts[name].get('sequence'), f'Missing sequence: {name}'
    players = scripts['household_music_player_config']['sequence'][0]['variables']['players']
    assert isinstance(players, dict) and players, 'players must be a nonempty mapping'
    assert all(isinstance(v, str) and re.fullmatch(r'media_player\.[a-z0-9_]+', v)
               for v in players.values()), 'Invalid media_player entity ID'
    assert len(set(players.values())) == len(players), 'Use one registered name per player'
    for ref in re.findall(r'action:\s*script\.([a-z0-9_]+)', text):
        assert ref in scripts, f'Undefined internal script: {ref}'
    assert 'music_last_room' in data['input_select'], 'Missing room helper'
    assert any(a.get('id') == 'family_music_shared_sleep_scheduler' for a in data['automation']), 'Missing scheduler'
    placeholders = sorted(set(re.findall(r'REPLACE_[A-Z0-9_]+', text)))
    if deploy:
        assert not placeholders, 'Unresolved placeholders: ' + ', '.join(placeholders)
    else:
        assert set(placeholders) == {'REPLACE_WITH_MA_CONFIG_ENTRY_ID', 'REPLACE_WITH_BABY_TRACK_URI'}, 'Unexpected template placeholders'
    print(f'OK: {path} (deploy={deploy}; HA runtime checks still required)')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('package', nargs='?', type=Path, default=ROOT / '迁移配置包/family_music.yaml')
    parser.add_argument('--deploy', action='store_true', help='Reject unresolved template placeholders')
    args = parser.parse_args()
    try:
        check(args.package, args.deploy)
        for path in (ROOT / 'config').glob('*.yaml'):
            yaml.load(path.read_text(encoding='utf-8'), Loader=UniqueLoader)
    except (AssertionError, KeyError, TypeError, ValueError, OSError, yaml.YAMLError) as error:
        print(f'ERROR: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
