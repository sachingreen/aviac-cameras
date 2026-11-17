# Aviac 6-band crop-mapping camera

Design work in progress. Nothing here is released for manufacture yet.

Rev B enclosure: one compact 112 x 108 x 99 mm box (125 mm with the quick-release), down from the
216 mm belly pod. The four cameras sit in a centred 2 x 2 grid, 40 mm apart, with every lens front on one
plane and every window flush on the bottom face. The body is 6061-T6 machined from solid, Type III hard
anodised (gunmetal) and bead-blasted. It has overmoulded TPU corner guards, grip grooves, tethered silicone
port covers and captive stainless lid screws. A 316 stainless skid rim keeps the sapphire windows 2.5 mm
off the ground when the box is put down face first. There is no fan and no duct: the Jetson is mounted
upside down against the finned lid, and the flight air runs along the fins. Calculated at 25 W and 40 °C
air, flying at 18 m/s: lid about 52 °C, module plate about 74 °C (it throttles at 99 °C). In still air on
the ground the module would pass 99 °C, so the module runs in 15 W mode until it is flying.
About 1.27 kg with the mount (calculated).

- `mechanical/build_model.py`: the box (CadQuery). `build_model_pod.py` is the earlier pod, kept for reference.
- `mechanical/out/renders/`: studio renders
- `teardown/`: interactive teardown page (`npm install && python3 tools/pack_assets.py && node build.mjs`)

- `docs/01-sensor-interfaces.md` — pinouts and constraints read from the supplied sensor-board files
- `docs/02-csi-lane-map.md` — draft Jetson Orin Nano CSI lane assignment
- `refs/sensor-boards/` — the supplied schematics, spec and Gerbers

Hardware shared with other cameras now lives outside this folder:

- `boards/orin-carrier/` — the Jetson Orin Nano carrier (this camera fits all four camera ports; BOM `kicad/bom_6band.csv`)
- `boards/mira220-module/` — the Mira220 module schematic, extracted from the SincereFirst drawing, with the trigger added
- `toolkit/render/` — the studio renderer used for `renders/`

Rev A1 of the carrier moved the camera I²C to 1.8 V: the Mira220's I²C and trigger pins are 1.8 V parts,
and rev A0 pulled them up to 3.3 V.
