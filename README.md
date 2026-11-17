# Aviac cameras

One repository for Aviac Technologies' drone camera payloads. Each camera has its own folder under `cameras/`.
The scripts that generate the schematic, board, 3D model, renders and teardown page are written to be reused:
a new camera starts from an existing folder and changes the parts list, layout and dimensions.

| Camera | Folder | State |
| --- | --- | --- |
| 6-band crop-mapping camera (IMX565 + 3 x Mira220, Jetson Orin Nano) | `cameras/6band/` | Concept model, schematic passes ERC, board is a first routing pass. Not ready for manufacture. |

## What each camera folder holds

| Path | What it is |
| --- | --- |
| `docs/` | Interface findings and design notes |
| `refs/` | Supplied schematics, datasheets |
| `hardware/tools/` | `design.py` (parts and nets), `gen_sch.py`, `gen_pcb.py`, `route.py` |
| `hardware/carrier/` | Generated KiCad 8 project, schematic PDF, check reports |
| `mechanical/` | `build_model.py` (CadQuery), `render.py` (Blender), `denoise.py`, outputs in `out/` |
| `renders/` | Finished studio renders |
| `teardown/` | Interactive teardown page: `src/`, `build.mjs`, built page in `dist/` |

## Rebuilding

Tools: KiCad 8, Python 3 with CadQuery, Blender 4, Node 20, Java (for the Freerouting autorouter), Intel Open Image Denoise.

```bash
cd cameras/6band/hardware/tools && python3 gen_sch.py && /usr/bin/python3 gen_pcb.py && /usr/bin/python3 route.py --export
```

```bash
cd cameras/6band/mechanical && python3 build_model.py
```

```bash
cd cameras/6band/teardown && npm install && python3 tools/pack_assets.py && node build.mjs
```

The 3D board file (`board.glb`) is not stored; export it with `kicad-cli pcb export glb --subst-models --include-tracks`.

## Credits

- Teardown page structure and `teardown/kit/` files: [elvarofficial/teardown](https://github.com/elvarofficial/teardown), MIT.
- Jetson socket and M.2 footprints, module pin names: [antmicro/jetson-orin-baseboard](https://github.com/antmicro/jetson-orin-baseboard), Apache-2.0.
