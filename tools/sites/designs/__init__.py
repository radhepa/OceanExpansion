"""The sites, one module each. A design module defines KEY, NAME, FEATURES, SITE, LAYOUTS, LOOT_TABLES and
pieces(); see DESIGN.md ("Design module contract")."""
import importlib
import os

KEYS = ['lighthouse', 'fort', 'galleon', 'whale', 'temple', 'grotto', 'bell', 'smugglers', 'iceberg', 'vents']


def modules(only=None):
    here = os.path.dirname(os.path.abspath(__file__))
    out = []
    for key in KEYS + (['example'] if only and 'example' in only else []):
        if only and key not in only: continue
        name = '_example' if key == 'example' else key
        if os.path.exists(os.path.join(here, name + '.py')):
            out.append(importlib.import_module(f'designs.{name}'))
    return out
