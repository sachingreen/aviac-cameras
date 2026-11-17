# CSI lane map — Jetson Orin Nano, 4 × 2-lane

Status: DRAFT. Pin numbers below are taken from the Jetson module symbol in Antmicro's open
Jetson Orin baseboard (github.com/antmicro/jetson-orin-baseboard, Apache-2.0, KiCad).
**VERIFY against NVIDIA DG-10931-001 (Orin NX / Orin Nano Design Guide), chapter 10 and
Table 10-3, before layout** — NVIDIA forum threads report a D1/D0 naming swap between
CSI0 and CSI1 inside the module that is only documented there.

| Camera | Band(s) | Module port | D0 N/P | D1 N/P | CLK N/P | Lanes |
|---|---|---|---|---|---|---|
| CAM0 | RGB — IMX565 | CSI0 | 4 / 6 | 16 / 18 | 10 / 12 | 2 |
| CAM1 | Red edge — Mira220 | CSI1 | 3 / 5 | 15 / 17 | 9 / 11 | 2 |
| CAM2 | NIR — Mira220 | CSI2 | 22 / 24 | 34 / 36 | 28 / 30 | 2 |
| CAM3 | Extended NIR — Mira220 | CSI3 | 21 / 23 | 33 / 35 | 27 / 29 | 2 |

Total 8 data lanes + 4 clocks = every CSI pin the Orin Nano exposes; nothing spare.

Sensor-side lane use
- IMX565: 2-lane mode uses sensor lanes D0 and D1 (CHC5 "CAM Lane 0 / Lane 1"); D2, D3 left open on the adapter.
- Mira220: module lanes D0, D1 (FPC pins 2/3 and 5/6), clock on 8/9.

Routing rules to apply (to be confirmed with the design guide values)
- 100 Ω differential, intra-pair skew and pair-to-clock matching per the guide's D-PHY table.
- No lane swaps or polarity inversions planned; if layout needs one, it must be declared in
  the device tree (`lane_polarity`) and noted here.
- Carrier connectors: 22-pin 0.5 mm FPC, same pinout as the sensor side (see `01-sensor-interfaces.md`),
  with pin 18 repurposed as the hardware trigger.
