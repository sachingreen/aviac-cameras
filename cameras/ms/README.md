# Aviac MS: multispectral camera (rev C, rugged body)

96 x 90 x 90 mm. One Sony IMX565 on a compact 16 mm C-mount lens (RGB), centred-right; three Mira220 on
M12 lenses with band-pass filters (red edge 723, NIR 840, NIR+ 890) in a column on the left. Jetson Orin NX / Nano
on an 87 x 52 mm carrier, thermal block to a finned aluminium rear plate with a 30 mm fan. Downwelling light
sensor on top, XT30 / Ethernet / USB-C / GPS-PPS on the rear, drone bracket with 4 x M3 underneath.
PA12-CF shell with chamfered corner bumpers, gasket line, 4 front screws, amber status LED, side vents under the
debossed Aviac wing mark. Calculated mass 553 g with the bracket.

Teardown stages (groups in the model): Optics / Baseboard + image sensors / Processing board / Externals.
Colourways: gunmetal (hero), sand, stealth, bronze (`out/finishes.json`).

Concept model for the website and renders. It replaces the earlier 112 mm aluminium box in `cameras/6band` (kept).

    python3 toolkit/cad/rugged_cameras.py ms
