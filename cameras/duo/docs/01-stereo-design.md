# Aviac Duo: two Mira220 cameras for stereo, guidance and maps

Status: concept. The numbers below are calculated; nothing has been measured.

## What it is

Two Mira220 camera modules on one machined aluminium lens plate, both looking down, both fired by the
same hardware trigger. One Jetson Orin Nano carrier (the same board as the 6-band camera, with two of
its four camera ports fitted) does the stereo depth, the guidance video and the maps.

| | Camera A (front) | Camera B (rear) |
| --- | --- | --- |
| Sensor | Mira220 RGB-IR (2QI1WP) recommended, or RGB (2QC1WP) | Mira220 mono (2QM1WP) |
| Gives | Red, green, blue and near-infrared from one sensor | Any band you put a filter on, at full resolution |
| Lens | 6 mm CS-mount, 40.8° x 36.1° | same |
| Filter | Dual-band (visible + 850 nm) for RGB-IR | 25 mm front filter, swapped by the user |
| Carrier port | CAM0 (J3), CSI0, 2 lanes | CAM1 (J4), CSI1, 2 lanes |

Why RGB-IR for camera A: it gives NDVI from one sensor with no registration, and an RGB-IR sensor sees
roughly the same scene as a mono sensor, which matters for stereo (next section). Both sensor types
use the same module, so the choice is made when the modules are ordered.

## Stereo geometry

Baseline 100 mm, along the flight direction (camera A ahead of camera B). Along-track keeps the pod
92 mm wide; across-track would allow at most about 60 mm.

Focal length 6 mm on 2.79 µm pixels = 2151 px. Depth error for a 0.25 px matching error:

| Range | Disparity | Depth error |
| --- | --- | --- |
| 2 m | 108 px | ± 0.5 cm |
| 5 m | 43 px | ± 3 cm |
| 10 m | 22 px | ± 12 cm |
| 20 m | 11 px | ± 47 cm |
| 50 m | 4.3 px | ± 2.9 m |
| 120 m | 1.8 px | ± 17 m |

Read this as: useful depth from the camera pair up to about 20 m. That covers landing, obstacle
checks, terrain following at low height and crop height from a low pass. At normal mapping height
(120 m) the pair adds nothing; 3D maps there come from consecutive frames along the flight line
(structure from motion), where the baseline is the 12 m flown between frames.

Closest usable range: about 0.8 m (256 px disparity search). Footprints overlap 87 % at 1 m.

## Stereo needs both cameras to see the same thing

Matching works on texture that looks alike in both images. Plants look completely different in red and
in near infrared (dark in one, bright in the other), so a red-filtered camera and an NIR-filtered camera
match badly over crops. Two modes, chosen by the filter on camera B:

| Mode | Camera B filter | Stereo | Spectral output |
| --- | --- | --- | --- |
| Guidance / 3D | Clear, or the same dual-band filter as camera A | Good | RGB + NIR from camera A |
| Mapping | Narrow band for the job (red edge, 940 nm, etc.) | Weak over vegetation; fine over soil and structures | RGB + NIR from A, plus the extra band from B |

At mapping height the two cameras are registered with a fixed offset: the parallax between them is
1.8 px at 120 m and changes by only 0.015 px per metre of crop height.

## Synchronisation

Same as the 6-band camera: the sync microcontroller fires both REQ_EXP lines from one timer, so the two
exposures start together (budget 50 µs; at 18 m/s that is 0.9 mm of travel). The extracted module design
(`boards/mira220-module`) adds the trigger on FPC pin 18, which the stock SincereFirst module lacks.

## Data and processing

- Guidance: both cameras at 60 fps full resolution = 1.6 Gbit/s per camera, 806 Mbit/s per lane of the
  1.5 Gbit/s the sensor allows. Stereo disparity on the Orin Nano with NVIDIA VPI.
- Mapping: one frame pair per trigger, 16-bit TIFF + XMP, as on the 6-band camera.
- Calibration: intrinsics and the stereo extrinsics from a checkerboard on the bench. The lens plate
  is one machined part so the calibration holds; re-check after any lens or filter change that moves
  the lens in its thread (focus).

## Open decisions

- Downward only, or a forward-looking variant for multirotor guidance (a different mount, same internals).
- Whether SincereFirst will build the module with the RGB-IR sensor and the trigger change.
