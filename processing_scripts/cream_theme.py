"""
Move every chart spec in js/ from the gold background (#dda66a) to light cream (#fbf3e6).
Run from the project root AFTER gold_theme.py:  .venv/bin/python processing_scripts/cream_theme.py
Only the background-related colours change; the chart colours chosen for a light background stay.
"""
import glob, json

SWAP = {
    '#dda66a': '#fbf3e6',   # chart backgrounds, shape borders, text halos
    '#c99556': '#e8d9c3',   # gridlines: a soft line on cream instead of a strong one on gold
    '#eadcc6': '#ddd0bb',   # "no data" / "no trees": a touch darker so it doesn't vanish into the cream
}


def walk(o):
    if isinstance(o, dict):
        return {k: walk(v) for k, v in o.items()}
    if isinstance(o, list):
        return [walk(v) for v in o]
    if isinstance(o, str):
        return SWAP.get(o.lower(), o)
    return o


for p in sorted(glob.glob('js/*.vl.json')):
    s = walk(json.load(open(p)))
    with open(p, 'w') as f:
        json.dump(s, f, indent=2, ensure_ascii=False); f.write('\n')
    print('converted', p)
