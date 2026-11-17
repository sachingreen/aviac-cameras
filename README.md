# Aviac cameras

One repository for Aviac Technologies' drone camera payloads. Each camera has its own folder under `cameras/`.
The scripts that generate the schematic, board, 3D model, renders and teardown page are written to be reused:
a new camera starts from an existing folder and changes the parts list, layout and dimensions.

| Camera | Folder | State |
| --- | --- | --- |
| 6-band crop-mapping camera (IMX565 + 3 x Mira220, Jetson Orin Nano) | `cameras/6band/` | Concept model, schematic passes ERC, board is a first routing pass. Not ready for manufacture. |
| Duo stereo camera (2 x Mira220, Jetson Orin Nano) | `cameras/duo/` | Concept model and stereo design. Uses the shared carrier with two camera ports fitted. |

Shared between cameras:

| Path | What it is |
| --- | --- |
| `boards/orin-carrier/` | Jetson Orin Nano carrier: netlist (`design.py`), placement, routing, KiCad project, BOM per camera (`variants.py`) |
| `boards/mira220-module/` | Mira220 camera module extracted from the SincereFirst schematic, with the hardware trigger added |
| `toolkit/kicad/` | Schematic generator and KiCad library helpers used by every board |
| `toolkit/render/` | Blender studio renderer and denoiser used by every camera |

## What each camera folder holds

| Path | What it is |
| --- | --- |
| `docs/` | Interface findings and design notes |
| `refs/` | Supplied schematics, datasheets |
| `mechanical/` | `build_model.py` (CadQuery), outputs in `out/` |
| `renders/` | Finished studio renders |
| `teardown/` | Interactive teardown page: `src/`, `build.mjs`, built page in `dist/` |

## Rebuilding

Tools: KiCad 8, Python 3 with CadQuery, Blender 4, Node 20, Java (for the Freerouting autorouter), Intel Open Image Denoise.

```bash
python3 toolkit/kicad/gen_sch.py boards/orin-carrier
```

```bash
cd boards/orin-carrier && /usr/bin/python3 gen_pcb.py && /usr/bin/python3 route.py --export
```

```bash
python3 toolkit/kicad/gen_sch.py boards/mira220-module
```

Each camera's README has its model, render and page steps. The 3D board file (`*.glb`) is not stored; export it with `kicad-cli pcb export glb --subst-models --include-tracks`.

## Credits

- Teardown page structure and `teardown/kit/` files: [elvarofficial/teardown](https://github.com/elvarofficial/teardown), MIT.
- Jetson socket and M.2 footprints, module pin names: [antmicro/jetson-orin-baseboard](https://github.com/antmicro/jetson-orin-baseboard), Apache-2.0.
