# Vessel Visualization — Agnostophage

Real-time cross-section visualization of the NSE research vessel.

## Quick Start

Open `index.html` in a browser. Without a WebSocket connection, it shows mock data.

### Demo mode (animated mock events)

```
index.html?demo=true
```

### Connect to live orchestrator

```
index.html?ws=ws://localhost:8765/ws/vessel
```

## WebSocket Server

The emission layer bridges orchestrator state files to the visualization:

```bash
cd harness/
python3 ws_emission.py                    # Start server on port 8765
python3 ws_emission.py --port 9000        # Custom port
python3 ws_emission.py --snapshot          # Print current state snapshot
python3 ws_emission.py -v                  # Verbose logging
```

Requires: `pip install websockets`

## Files

- `index.html` — iframe target page
- `vessel.js` — All visualization logic (~500 lines, vanilla JS)
- `vessel.css` — Scoped styles (all `.vessel-*` prefixed)
- `morocco-outline.svg` — Simplified coastline for tile inset
- `../harness/ws_emission.py` — WebSocket emission server

## Embedding

In the static site's `index.html`:
```html
<iframe src="vessel/" width="100%" height="480" style="border:none"></iframe>
```

## Design Spec

See `docs/vessel-visualization-spec.md` for the full design specification.
