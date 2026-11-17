# Aviac Duo: compact stereo camera for spray drones

A sealed 152 x 98 x 62 mm box with two Mira220 cameras 60 mm apart, a Jetson Orin Nano cooled by its
finned lid (no fan, no duct), and a tilt clamp that fits the 20-25 mm tubes on spray-drone frames.
It checks whether a field was sprayed properly: coverage, deposit on water-sensitive cards, and the
effect a few days later.

Status: concept. Calculated, not built or measured.

| Path | What it is |
| --- | --- |
| `docs/01-stereo-design.md` | Box design, cooling, lens coverage, stereo accuracy, mounting, power decision |
| `docs/02-spray-verification.md` | What the camera can and cannot check about spraying |
| `mechanical/build_model.py` | CadQuery model of the box; outputs in `mechanical/out/` (STEP, printable/machinable STL for body, lid, lens plate, yoke, clamp) |
| `renders/` | Studio renders |

Shared parts, used unchanged from the rest of the repo:

| Part | Where | Duo-specific |
| --- | --- | --- |
| Jetson Orin Nano carrier | `boards/orin-carrier` | Variant `duo`: camera ports 2 and 3 not fitted (16 parts). BOM: `boards/orin-carrier/kicad/bom_duo.csv` |
| Camera modules | `boards/mira220-module` | Two modules: A with the RGB-IR sensor, B with the mono sensor. Module B fits the address strap for I²C 0x55 if the I²C switch is ever removed |
| Renderer | `toolkit/render` | Box shots: `box_hero`, `box_under`, `box_mounted`, `box_exploded`, `box_inside`, `box_filter` |

## Rebuild

```bash
cd cameras/duo/mechanical && python3 build_model.py
```

```bash
cd boards/orin-carrier && /usr/bin/python3 variants.py pcb && kicad-cli pcb export glb --subst-models --include-tracks --no-dnp -f -o kicad/variants/duo.glb kicad/variants/duo.kicad_pcb
```

```bash
cd cameras/duo/mechanical && FOCUS=mira1_bezel blender -b -P ../../../toolkit/render/render.py -- out/model.js ../../../boards/orin-carrier/kicad/variants/duo.glb out/renders 90 box_hero,box_hero_light,box_under,box_mounted,box_exploded,box_inside,box_filter 1920 1200 && python3 ../../../toolkit/render/denoise.py out/renders <path to oidnDenoise>
```
