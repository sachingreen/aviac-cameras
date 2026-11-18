# Aviac Duos: stereo head (rugged body)

50 x 30 x 28 mm body, about 48 mm deep with the lenses. Two Mira220 (1600 x 1400 global shutter) on one shared
board, M12 lenses 25 mm long at a 26 mm baseline. No onboard Jetson: an interface board bridges MIPI to USB-C
(or GMSL) for external compute. Rear: USB-C, 4 x M2; base: 1/4"-20 insert. Same family as the Aviac MS: rugged
PA12-CF body, corner bumpers, gasket line, amber LED, debossed wing mark over side vents.

Teardown stages: Optics / Baseboard + image sensors / Processing board (interface) / Externals.
Colourways: gunmetal (hero), sand.

    python3 toolkit/cad/rugged_cameras.py duos
