# Aviac 6-band crop-mapping camera

Design work in progress. Nothing here is released for manufacture yet.

- `docs/01-sensor-interfaces.md` — pinouts and constraints read from the supplied sensor-board files
- `docs/02-csi-lane-map.md` — draft Jetson Orin Nano CSI lane assignment
- `refs/sensor-boards/` — the supplied schematics, spec and Gerbers

Hardware shared with other cameras now lives outside this folder:

- `boards/orin-carrier/` — the Jetson Orin Nano carrier (this camera fits all four camera ports; BOM `kicad/bom_6band.csv`)
- `boards/mira220-module/` — the Mira220 module schematic, extracted from the SincereFirst drawing, with the trigger added
- `toolkit/render/` — the studio renderer used for `renders/`

Rev A1 of the carrier moved the camera I²C to 1.8 V: the Mira220's I²C and trigger pins are 1.8 V parts,
and rev A0 pulled them up to 3.3 V.
