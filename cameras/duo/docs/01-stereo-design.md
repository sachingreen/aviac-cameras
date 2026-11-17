# Aviac Duo: compact stereo camera for spray drones

Status: concept. The numbers below are calculated; nothing has been built or measured.

## What it is

A sealed box, 152 x 98 x 62 mm (111 mm tall with the tube clamp), about 600 g with the mount. Inside:
two Mira220 cameras 60 mm apart on one machined lens plate, both looking down and fired by the same
hardware trigger, and the shared Jetson Orin Nano carrier (duo variant: two of its four camera ports
fitted). No fan and no air duct: the Jetson presses on a finned aluminium lid through a thermal pad,
and the rotor downwash cools the lid.

| | Camera A | Camera B |
| --- | --- | --- |
| Sensor | Mira220 RGB-IR (2QI1WP) recommended, or RGB (2QC1WP) | Mira220 mono (2QM1WP) |
| Gives | Red, green, blue and near-infrared from one sensor | Any band you put a filter on, at full resolution |
| Lens | 4 mm CS-mount, 58° x 52° | same |
| Filter | Dual-band (visible + 850 nm) behind a fixed ring | Twist-lock ring: changed in the field without tools |
| Carrier port | CAM0 (J3) | CAM1 (J4) |

Both sensor types fit the same module, so the choice is made when the modules are ordered.

## Why a box, not the 6-band pod

The 6-band pod is shaped for a fixed-wing belly at 18 m/s and carries a 25 W computer, so it needs a
ram-air duct. A spray drone flies at 2-5 m and 3-7 m/s under its own downwash, and the Duo's work fits
in the Jetson's 15 W mode. A plain finned lid is enough:

| Jetson mode | Lid temperature rise, still air | Under rotor downwash (3-5 m/s) |
| --- | --- | --- |
| 7 W | 9 °C | 4 °C |
| 15 W (recommended in flight) | 19 °C | 8 °C |
| 25 W (MAXN SUPER) | 32 °C | 14 °C |

Lid area 0.065 m² including 19 fins 8.5 mm tall; heat-transfer coefficients assumed 12 W/m²K still
and 28 W/m²K under downwash. Direct sun on a black lid adds to these. Run 7 W on the ground,
15 W in flight; 25 W only with airflow. **Not yet measured.**

An inner wall between the electronics and the cameras keeps the Jetson's heat off the sensors.

## Coverage and detail at spray height (4 mm lens)

| Height | Footprint | Ground detail |
| --- | --- | --- |
| 2 m | 2.2 x 2.0 m | 1.4 mm per pixel |
| 3 m | 3.4 x 2.9 m | 2.1 mm per pixel |
| 5 m | 5.6 x 4.9 m | 3.5 mm per pixel |

Spray swaths are 5-9 m wide, so at 3 m one frame covers roughly half the swath; at 5 m about all of it.
A 3.5 mm lens widens this to 3.8 m at 3 m. The lens is a user choice.

## Stereo

Baseline 60 mm, side by side (across the flight direction). Focal length 4 mm = 1434 px.
Depth error for a 0.25 px matching error:

| Range | Disparity | Depth error |
| --- | --- | --- |
| 2 m | 43 px | ± 1.2 cm |
| 3 m | 29 px | ± 2.6 cm |
| 5 m | 17 px | ± 7.3 cm |

At spray height this is plenty for crop height, boom-to-canopy distance and obstacle checks.

Stereo needs both cameras to see similar images. Plants are dark in red and bright in near infrared,
so a red-filtered and an NIR-filtered camera match badly over crops. For stereo, put the same (or a
clear) filter on camera B; for an extra spectral band, accept weaker stereo over vegetation.

## Mounting

A tilt yoke (0-35° back, locked by two knobs) with a split clamp for 20, 22 or 25 mm tubes, the common
sizes on spray-drone frames. Mount it ahead of the spray boom and tilt it back so the frame sees the
area just sprayed, without the windows sitting in the mist.

Spray on the windows is the practical risk. The windows are hydrophobic-coated and recessed in hoods;
the mounting position matters more than the coating. **Not yet tested.**

## Power: needs a decision

Spray drones mostly run 12S-14S batteries (44-59 V). The shared carrier accepts 3S-6S (9-25 V); its
input protection would be destroyed by a 12S battery. Two options:

1. Power the Duo from the drone's 12 V auxiliary output or a 12S-to-12 V converter (no board change).
2. Carrier rev A2 with a 12-60 V input stage (wider-rated converter, TVS and reverse-polarity MOSFET).

## Synchronisation, data, calibration

- Both shutters fire from one timer on the sync microcontroller (budget 50 µs). The extracted module
  design (`boards/mira220-module`) adds the trigger pin the stock SincereFirst module lacks.
- Up to 60 fps per camera at full resolution, 806 Mbit/s per lane (sensor limit 1.5 Gbit/s).
- Stereo calibration on the bench with a checkerboard; the lens plate is one machined part so it holds.
  Re-check after changing a lens or refocusing.
