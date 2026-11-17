# Sensor interfaces — what the supplied files establish

Status: read from the supplied schematics on 2026-11-16. Items marked **VERIFY** were not
confirmed and must be checked before layout.

Sources
- `refs/sensor-boards/SF3RA220IRY32_schematic_240308.pdf`, `..._spec_240506.pdf` (SincereFirst Mira220 module)
- CircuitValley CHC5 open camera, github.com/circuitvalley/CHC5_Open_Camera @ 0243eec7e
  (`Hardware/Schematic/Sensor/CHC5_Sensor.pdf`, `Adapters/RPI_TO_CAM5_REVF.pdf`,
  `Software/linux-xlnx/drivers/media/i2c/imx565.c`)
- `refs/sensor-boards/Camera_R3_Schematic.pdf` (earlier 5×Mira220 + IMX545 board; not used going forward)

## 1. Mira220 module — SincereFirst SF3RA220IRY32

| Item | Value |
|---|---|
| Sensor | ams OSRAM Mira220, 1600 × 1400, 1/2.7", mono NIR-enhanced, global shutter |
| Board | 30 × 24 mm, 1.0 mm thick, 4 corner holes |
| Connector | 22-pin 0.5 mm FPC, mating part Molex 54548-2271 |
| Supply | 3.3 V only on pin 22; 2.5 / 1.8 / 1.35 V made on the module, sequenced by an LM3880-type sequencer |
| Clock | 38.4 MHz oscillator on the module (no MCLK needed from the host) |
| I²C address | 0x54, fixed (ADDR0/ADDR1 tied low through 12 kΩ) |
| MIPI | 2 data lanes + clock, each through a DLP11SN900HL2L common-mode choke |
| Stock lens | SK6531AP, F2.4, HFOV 55°, DFOV 70°, distortion < 1 % |
| Stock filter variants | -1: 680–720 nm, -2: 780–820 nm, -3: 860–920 nm, -4: 650 nm IR-cut, -5: no filter |

22-pin FPC pinout (same order as the Raspberry Pi / Jetson 22-pin camera connector):

| Pin | Signal | Pin | Signal |
|---|---|---|---|
| 1 | GND | 12 | NC (D2_P) |
| 2 | D0_N | 13 | GND |
| 3 | D0_P | 14 | NC (D3_N) |
| 4 | GND | 15 | NC (D3_P) |
| 5 | D1_N | 16 | GND |
| 6 | D1_P | 17 | GPIO0 = PWDN (enables the power sequencer) |
| 7 | GND | 18 | GPIO1 — not connected to anything on the module |
| 8 | CLK_N | 19 | GND |
| 9 | CLK_P | 20 | SCL |
| 10 | GND | 21 | SDA |
| 11 | NC (D2_N) | 22 | 3.3 V |

Findings that affect the carrier design
1. **No hardware trigger on the stock module.** REQ_EXP and REQ_FRAME are pulled to ground
   through 12 kΩ (R4, R5) and go nowhere else. The ≤ 50 µs skew requirement cannot be met
   until REQ_EXP reaches the FPC. Two routes: (a) ask SincereFirst for a variant with REQ_EXP
   on pin 18 (spare) — preferred; (b) rework: a wire from the sensor side of R4 to pin 18.
   The carrier is designed with the trigger on pin 18 either way. One pin is enough: the
   Mira220 datasheet (`refs/Mira220_datasheet_ams-OSRAM.pdf`, section 7.7.2 "Slave mode")
   defines single-pin exposure — rising edge of REQ_EXP starts exposure, falling edge starts
   readout; minimum pulse 10 µs. Datasheet QE (mono): 95 % at 550 nm, 56 % at 850 nm, 36 % at 940 nm.
2. **All three modules answer at 0x54.** Each must sit on its own I²C segment → I²C mux on the carrier.
3. **Stock lens is 55° HFOV**, not the 44° target, and the stock filter bands do not match
   the wanted RE / NIR / extended-NIR set exactly. See `02-optics-and-bands.md` (to be written).

## 2. IMX565 sensor board — CircuitValley CHC5 sensor board

| Item | Value |
|---|---|
| Sensor | Sony IMX565, 4128 × 3008 (driver), 2.74 µm, ~1/1.1", global shutter, colour (BayerRG) or mono |
| Output | MIPI CSI-2, 2 or 4 lanes (driver `lanes: "2,4"`), link frequencies 594 / 445.5 / 297 MHz |
| Connector | Hirose DF40HC(3.0)-100DS-0.4V on the sensor board; mates with DF40C-100DP-0.4V |
| Supply | single VIN rail; the CHC5 Raspberry-Pi adapter feeds it straight from the 3.3 V FPC pin |
| Clock | oscillator on the sensor board (CAM_CLK from the host is an unfitted option) |
| Control | I²C (level-shifted to 1.8 V on the board), XCLR reset, ENABLE |
| Sync | XTRIG1, XTRIG2, XVS, XHS, XMASTER, TOUT0/1 are on the 100-pin connector |
| Driver | `imx565.c`, GPL-2.0, V4L2, has a "Fast Trigger" mode (TRIGMODE reg 0x3400) |
| Lens mount | CHC5 interchangeable mounts incl. C and CS; min. flange distance 8.75 mm |

Mating-header (DF40C-100DP) nets, read from `RPI_TO_CAM5_REVF.pdf`. **VERIFY: pin numbers are
±1 row — the PDF text positions fall half-way between rows. Confirm against
`Hardware/PCB/Sensor/Source/Sensor_template.SchDoc` before layout.**

| Net | Pin(s) | Net | Pin(s) |
|---|---|---|---|
| VIN | 1–14 | MIPI0_D0_P / N | 72 / 74 |
| I2C0_SCL / SDA | 18 / 20 | MIPI0_D1_N / P | 66 / 68 |
| XCLR | 42 | MIPI0_D2_P / N | 78 / 80 |
| ENABLE | 44 | MIPI0_D3_P / N | 60 / 62 |
| MIPI0_CLK_N / P | 65 / 67 | XTRIG1 / XTRIG2 | 84 / 86 |
| XVS / XHS(FSTROBE) | 77 / 79 | XMASTER | 85 |
| CAM_CLK | 83 | TOUT0 / TOUT1 | 89 / 91 |

Findings that affect the carrier design
1. **It is a board-to-board connector, not an FPC.** To reach the carrier over FPC we need a
   small Aviac adapter board: DF40C-100DP → 22-pin FPC carrying lanes D0, D1, clock, I²C,
   ENABLE and XTRIG1. CircuitValley's own Pi adapter does this for 4 lanes but leaves the
   trigger on test points only.
2. **Licence.** CHC5 hardware files and device-tree files are CC BY-NC-ND 4.0 (non-commercial,
   no derivatives). We may buy and use the sensor board and design our own mating adapter,
   but must not copy or modify their board design for a commercial product. The `imx565.c`
   driver is GPL-2.0 and can be ported.
3. **2-lane throughput.** At 594 MHz (1188 Mbit/s per lane) two lanes carry ≈ 2.4 Gbit/s →
   roughly 14 fps at 12-bit full resolution before blanking. Ample for mapping (1–2 fps).
4. **"PhoMX565 Rev.D"** is not a name that appears in the CHC5 files. **VERIFY** which exact
   sensor board revision was bought, and whether it is the colour variant.
5. **Availability.** The shop page lists the IMX565 camera as pre-order, delivery January 2027.

## 3. Earlier Camera_R3 board (for the record)
5 × Mira220 + 1 × IMX545 on one 95 × 75 mm 8-layer board. The IMX545 leaves on a 40-pin
micro-coax connector as 8-channel SLVS, which a Jetson cannot receive. Superseded by the
four separate modules above.
