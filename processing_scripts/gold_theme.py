"""
Convert every chart spec in js/ to the gold page (#dda66a, the colour at the bottom edge of the sunset photo).
Run from the project root AFTER dark_theme.py (it converts the dark-navy colours that script wrote):
    .venv/bin/python processing_scripts/gold_theme.py

On a light background the darkest colour stands out most, so green scales go back to light = few, dark = many.
Orange-family colours are replaced by deep red, because orange disappears against gold.
"""
import glob, json

GOLD = '#dda66a'
TEXT, TEXT_2, MUTED = '#2b2118', '#4a3b2c', '#6b5a48'
GRID, LINE, NO_DATA = '#c99556', '#8c7458', '#eadcc6'
RED = '#a1221b'

SWAP = {
    '#292d39': GOLD,                                          # backgrounds, shape borders, text halos
    '#e8eaed': TEXT, '#b8bcc6': TEXT_2, '#8a8f9c': MUTED,
    '#3a3f4d': GRID, '#5b6070': LINE, '#3d4250': NO_DATA,
    # suburb rate bands back to light = few, dark = many
    '#1d4a33': '#c7e9c0', '#2b6e46': '#a1d99b', '#3f9459': '#74c476', '#6cc47a': '#41ab5d',
    '#9ad78f': '#238b45', '#d2f2c4': '#005a32',
    # tree-cover bands
    '#1f4a34': '#d9efd3', '#2f7246': '#a8d99c', '#55a862': '#5fb365', '#a6dc95': '#21823f',
    # accents
    '#ff8a3d': RED,                                           # introduced birds, canopy dots, bird records, Common Myna
    '#e69f00': RED,                                           # summer ridges, slope "ranks higher by records"
    '#56b4e9': '#0b5f99',                                     # blues darkened for a light background
    '#c9963a': '#6e4518',                                     # autumn ridges: dark brown, not gold-on-gold
    '#009e73': '#0b6e4f',                                     # spring ridges
    '#cc79a7': '#8e3b74',                                     # Red Wattlebird line
}
CONTINUOUS = ['#e5f5e0', '#00441b']                           # light green = few, dark green = many


def walk(o):
    if isinstance(o, dict):
        if o.get('range') == ['#1d4a33', '#d2f2c4']:
            o = {**o, 'range': CONTINUOUS}
        return {k: walk(v) for k, v in o.items()}
    if isinstance(o, list):
        return [walk(v) for v in o]
    if isinstance(o, str):
        return SWAP.get(o.lower(), o)
    return o


for p in sorted(glob.glob('js/*.vl.json')):
    s = walk(json.load(open(p)))
    if p.endswith('map_states.vl.json'):
        # state labels: white text on the darkest state (NT), dark text elsewhere (incl. TAS/ACT over the background)
        s['layer'][2]['encoding']['color']['condition']['value'] = 'white'
    with open(p, 'w') as f:
        json.dump(s, f, indent=2, ensure_ascii=False); f.write('\n')
    print('converted', p)
