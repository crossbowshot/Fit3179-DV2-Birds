"""
Convert every chart spec in js/ to the dark navy page (#292d39, the colour at the bottom of the title photo).

1. Adds a dark `config` to each spec: navy background, light text, axes, legends and gridlines.
2. Swaps hard-coded colours. Sequential green scales are FLIPPED: on a dark background the brightest colour stands
   out most, so the highest values must be the brightest (on white it was the reverse).
Run from the project root: .venv/bin/python processing_scripts/dark_theme.py
"""
import glob, json

NAVY = '#292d39'
TEXT, TEXT_2, MUTED = '#e8eaed', '#b8bcc6', '#8a8f9c'
GRID, LINE, NO_DATA = '#3a3f4d', '#5b6070', '#3d4250'
LOW_HIGH_GREENS = ['#1d4a33', '#d2f2c4']          # continuous scales: dark green = few, pale bright green = many

SWAP = {
    'white': NAVY,                                  # shape borders and text halos become navy gaps
    '#222': TEXT, '#222222': TEXT, '#444': TEXT, '#4d4d4d': TEXT, '#555': TEXT,
    '#666': MUTED, '#8a8a8a': MUTED, '#8c8c8c': MUTED, '#999999': MUTED,
    '#eeeeee': GRID, '#e6e6e6': GRID,
    '#c4c4c4': LINE, '#c8c8c8': LINE, '#cccccc': LINE,
    '#dedede': NO_DATA, '#ececec': NO_DATA, '#f1f1ed': NO_DATA,   # "no data" / "no trees" / base land
    # suburb rate bands, light-to-dark on white -> dark-to-bright on navy
    '#c7e9c0': '#1d4a33', '#a1d99b': '#2b6e46', '#74c476': '#3f9459', '#41ab5d': '#6cc47a',
    '#238b45': '#9ad78f', '#005a32': '#d2f2c4',
    # tree-cover bands
    '#d9efd3': '#1f4a34', '#a8d99c': '#2f7246', '#5fb365': '#55a862', '#21823f': '#a6dc95',
    # accents made brighter so they read on navy
    '#d94801': '#ff8a3d', '#e6550d': '#ff8a3d', '#d55e00': '#ff8a3d',
    '#0072b2': '#56b4e9', '#a6761d': '#c9963a',
}

DARK_CONFIG = {
    'background': NAVY,
    'view': {'stroke': None},
    'title': {'color': TEXT},
    'axis': {'labelColor': TEXT_2, 'titleColor': TEXT, 'domainColor': LINE, 'tickColor': LINE, 'gridColor': GRID},
    'legend': {'labelColor': TEXT_2, 'titleColor': TEXT},
    'header': {'labelColor': TEXT_2, 'titleColor': TEXT},
    'text': {'color': TEXT},
}


def walk(o):
    if isinstance(o, dict):
        if o.get('scheme') == 'greens':             # continuous green scales: flip so bright = more
            del o['scheme']
            o['range'] = LOW_HIGH_GREENS
        return {k: walk(v) for k, v in o.items()}
    if isinstance(o, list):
        return [walk(v) for v in o]
    if isinstance(o, str):
        return SWAP.get(o.lower(), o)
    return o


for p in sorted(glob.glob('js/*.vl.json')):
    s = json.load(open(p))
    if p.endswith('map_states.vl.json'):
        # state labels: dark text on the brightest state (NT), light text everywhere else (incl. TAS/ACT over the sea)
        color = s['layer'][2]['encoding']['color']
        color['condition']['value'] = '#1b1e27'
        color['value'] = TEXT
        s['layer'][2]['encoding']['color'] = json.loads(json.dumps(color).replace('"white"', '"KEEP"'))
    s = walk(s)
    if p.endswith('map_states.vl.json'):
        s['layer'][2]['encoding']['color']['condition']['value'] = '#1b1e27'
    cfg = s.get('config', {})
    s['config'] = {**DARK_CONFIG, **{k: v for k, v in cfg.items() if k != 'view'}}
    with open(p, 'w') as f:
        json.dump(s, f, indent=2, ensure_ascii=False); f.write('\n')
    print('converted', p)
