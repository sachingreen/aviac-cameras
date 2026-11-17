# Aviac Duo: two-camera stereo payload

Two Mira220 cameras, 100 mm apart on one machined lens plate, fired together by one hardware trigger.
Used for low-altitude guidance and depth (useful to about 20 m) and for colour + near-infrared maps.
Users change the lens or the front filter on camera B for whatever they are monitoring.

Status: concept. Calculated, not built or measured.

| Path | What it is |
| --- | --- |
| `docs/01-stereo-design.md` | Sensors, baseline, depth accuracy, filter modes, sync, data rates, open decisions |
| `mechanical/build_model.py` | CadQuery model of the pod; outputs in `mechanical/out/` (STEP, STL, model for renders) |
| `renders/` | Studio renders |

Shared parts, used unchanged from the rest of the repo:

| Part | Where | Duo-specific |
| --- | --- | --- |
| Jetson Orin Nano carrier | `boards/orin-carrier` | Variant `duo`: camera ports 2 and 3 not fitted (16 parts). BOM: `boards/orin-carrier/kicad/bom_duo.csv` |
| Camera modules | `boards/mira220-module` | Two modules: A with the RGB-IR sensor, B with the mono sensor. Module B fits the address strap for I²C 0x55 if the I²C switch is ever removed |
| Renderer | `toolkit/render` | Close-up focuses on `mira0_lens_glass` |

## Rebuild

```bash
cd cameras/duo/mechanical && python3 build_model.py
```

```bash
cd boards/orin-carrier && /usr/bin/python3 variants.py pcb && kicad-cli pcb export glb --subst-models --include-tracks --no-dnp -f -o kicad/variants/duo.glb kicad/variants/duo.kicad_pcb
```

```bash
cd cameras/duo/mechanical && FOCUS=mira0_lens_glass blender -b -P ../../../toolkit/render/render.py -- out/model.js ../../../boards/orin-carrier/kicad/variants/duo.glb out/renders 110 hero_lens,hero_lens_light,exploded,inside,inside_top,optics_macro 1920 1200 && python3 ../../../toolkit/render/denoise.py out/renders <path to oidnDenoise>
```
