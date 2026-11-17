# Mira220 camera module (extracted)

The schematic of the SincereFirst SF3RA220IRY32 Mira220 module, rebuilt as a KiCad 8 project from the
supplied PDF (`cameras/6band/refs/sensor-boards/SF3RA220IRY32_schematic_240308.pdf`). The sensor's
ball map and decoupling come from the ams OSRAM Mira220 datasheet DS000642 v9-00
(`cameras/6band/refs/Mira220_datasheet_ams-OSRAM.pdf`), table 42 and figure 4.

- `design.py`: every part and connection. Edit this, then run `python3 ../../toolkit/kicad/gen_sch.py .`
- `kicad/mira220_module.kicad_sch`: generated schematic. KiCad's electrical rules check: 0 violations.
- `kicad/mira220_module_schematic.pdf`: the same as a PDF.

State: schematic only. The board layout needs the Mira220 CSP land pattern from the datasheet's
package drawing; not drawn yet.

## What the module does

| Block | Parts | Notes |
| --- | --- | --- |
| Sensor | U5 Mira220, R_EXT 12 kΩ 0.1 %, 15 decoupling capacitors | Same ball map for mono, RGB and RGB-IR sensors |
| Supplies | U1 1.35 V, U2 1.8 V, U3 2.5 V (JW7807 LDOs), U4 LM3880 sequencer | Runs from the 3.3 V on FPC pin 22. Order: 2.5 V, 1.35 V, 1.8 V, then reset released, as the datasheet requires |
| Clock | X1 38.4 MHz at 1.8 V | Datasheet: ±50 ppm, 45–55 % duty, < 200 ps jitter |
| Interface | J1 22-pin 0.5 mm FPC, L1–L3 common-mode filters | Raspberry Pi / Jetson camera pinout, 2 MIPI lanes |
| Address | R2/R3 to ground: I²C 0x54 | Optional R pull-ups for 0x55 / 0x56 |

## Changes from the SincereFirst original

| Change | Why |
| --- | --- |
| **Trigger added:** FPC pin 18 (was GPIO1 / LED enable) now reaches REQ_EXP through a 0 Ω link | The stock module cannot be hardware-triggered; the 12 kΩ pull-down stays so an unconnected module idles |
| **Address straps added** (not fitted by default) | Two modules can share one I²C bus at 0x54 and 0x55 without a switch |
| **Exposure-window output option** (not fitted): ILLUM_TRIGGER to FPC pin 12 | Lets the carrier measure each sensor's real exposure start, to prove the trigger skew |
| **Decoupling per datasheet:** 2.2 µF 16 V (4.7 µF 10 V on VDDINT_7) | The original fits 4.7 µF everywhere; the datasheet specifies value and voltage rating |
| **LDO_DIG_EN left open** | Read from the scan, the original grounds it. The datasheet says leave it open (internal pull-up keeps the digital regulator on). **VERIFY** on a real module |
| **Power LED removed** | It was driven from pin 18, now the trigger |

## Things to check before ordering

- **I/O voltage.** The sensor's I²C and trigger pins are 1.8 V parts (datasheet: input high max = VDD18).
  The module passes SCL/SDA straight to the FPC, so whatever drives the cable must use 1.8 V levels.
  The Aviac carrier does from rev A1; a Raspberry Pi pulling the bus to 3.3 V does not.
- **2.5 V start-up current.** The datasheet asks for 350 mA on 2.5 V at start-up. Confirm the JW7807 can supply it.
- **Connector and filter footprints** are KiCad stand-ins for the original Molex 54548-2271 and Murata DLP11SN900HL2L.
