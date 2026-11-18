# Aviac MS: multispectral camera (rev C, rugged body)

96 x 90 mm face, 94 mm deep including the protective hood; the body tapers 3 mm per side toward the back and rounds off at the rear.
The lenses sit in a front tunnel ringed by an overmoulded TPU hood that stands 2 mm proud of every lens, so a
crash lands on the hood, not the glass. Ribbed TPU grips on both sides. One Sony IMX565 on a compact 16 mm C-mount lens (RGB), centred-right; three Mira220 on
M12 lenses with band-pass filters (red edge 723, NIR 840, NIR+ 890) in a column on the left. Jetson Orin NX / Nano
on an 87 x 52 mm carrier; two 6 mm heat pipes carry the heat to a 1.5 mm finned aluminium insert in the rear
wall, with a 30 mm fan. The downwelling light
sensor is a separate puck on top of the drone, cabled to a DLS port on the rear (it must face the sky); XT30 / Ethernet / USB-C / GPS-PPS on the rear, drone bracket with 4 x M3 underneath.
PA12-CF shell with chamfered corner bumpers, gasket line, 4 front screws, thin amber light bar that blinks while capturing,
side vents under the debossed Aviac wing mark. Lens rings are 20 mm, shared with the Duos.

Calculated mass 307 g, 314 g with the PA12-CF bracket (MicaSense RedEdge-P: 315 g, RedEdge-MX: 232 g, both without
onboard compute). Heaviest items: C-mount lens 45 g (estimate), Jetson module 28 g, rear housing about 45 g.

Teardown stages (groups in the model): Optics / Baseboard + image sensors / Processing board / Externals.
Colourways: gunmetal (hero), sand, stealth, bronze (`out/finishes.json`).

Concept model for the website and renders. It replaces the earlier 112 mm aluminium box in `cameras/6band` (kept).

    python3 toolkit/cad/rugged_cameras.py ms

Teardown parts, front to back: front shell with panel, light bar and light pipe, 4 x M3 screws, gasket; O-rings,
lens rings, filter retainers, band-pass filters, three M12 lenses and holders, the C-mount lens, lens plate and its
screws, IR-cut filter and C-mount spacer; three Mira220 boards with FPCs, the IMX565 board on standoffs, the
baseboard; the Jetson carrier (SSD, power stage, SO-DIMM), module, thermal pad, spreader and heat pipes; fan,
rear I/O board (XT30, Ethernet, USB-C, GPS/PPS, DLS), heatsink insert with its pad and screws, rear housing,
bracket and its screws. Calculated mass 344 g including the bracket and DLS puck.
