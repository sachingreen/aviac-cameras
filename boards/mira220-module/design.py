"""Mira220 camera module - extracted from the SincereFirst SF3RA220IRY32 schematic (rev 2024-03-08).

Source: refs/SF3RA220IRY32_schematic_240308.pdf (supplied), pin table from the ams OSRAM Mira220
datasheet DS000642 v9-00, table 42. Every part of the original is here with its original reference
designator where it had one. Changes from the original are marked CHANGED or ADDED with the reason.
The module stays a drop-in replacement: same 22-pin FPC pinout, same 30 x 24 mm outline intent.

Not done yet: PCB layout (needs the Mira220 CSP land pattern from the datasheet's package drawing).
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "toolkit", "kicad"))
from netlist import Design

PROJECT = "mira220_module"
TITLE = "Mira220 camera module (extracted from SincereFirst SF3RA220IRY32, trigger added)"
REV = "A0 (extraction; not yet laid out)"
BLOCK_WIDTH = {"SENSOR": 330, "PWR": 300, "IO": 300}

D = Design()
for k, t in [("SENSOR", "MIRA220 IMAGE SENSOR, 1600 x 1400, GLOBAL SHUTTER"),
             ("PWR", "SUPPLIES 2.5 V / 1.35 V / 1.8 V FROM 3.3 V, SEQUENCED 2.5 -> 1.35 -> 1.8 -> RESET"),
             ("IO", "22-PIN FPC, MIPI COMMON-MODE FILTERS, CLOCK, ADDRESS AND TRIGGER")]:
    D.block(k, t)

GND = "GND"
# ---------------------------------------------------------------- sensor ball map (datasheet table 42)
BALLS = {
    "VDD25": "A7 A10 B3 B4 D2 D9 E9 F2 G2 H1 J4 K1 K3", "VDD25R": "B2", "VDD25A": "D8", "VDDINT_1": "A3 G3 J3",
    "VDD18": "E10 J6 J9", "VDD13D": "B5", "VDD13P": "B7", "VDD13A": "B10",
    "VDD11D": "A5 F10 H6 H9 J7", "VDD11A": "C9", "VDD11P": "B6",
    "VDDINT_2": "D1", "VDDINT_3": "B1", "VDDINT_4": "E1", "VDDINT_5": "C1", "VDDINT_6": "H3", "VDDINT_7": "C2 J1 K5 K7",
    "VDDNEG_1": "G1", "VDDNEG_2": "J2",
    "VSSA": "C5 D7 D10", "VSSD": "A4 A6 C4 F9 H10 K8 K10", "VSSPIX": "A2 C3 E2 F1 H2 K2 K4 K6", "NC_VSS": "E3 F3",
    "R_EXT": "E8", "C_EXT": "C6", "CLK_IN": "G10", "CCI_ADDR0": "H4", "CCI_ADDR1": "J8", "CCI_SDA": "H8", "CCI_SCL": "H7",
    "MIPI_CLK_P": "A8", "MIPI_CLK_N": "B8", "MIPI_D0_P": "C7", "MIPI_D0_N": "C8", "MIPI_D1_P": "A9", "MIPI_D1_N": "B9",
    "JTAG_MODE": "K9", "ATPG_MODE": "J5", "REQ_FRAME": "G9", "REQ_EXP": "G8", "ILLUM_TRIGGER": "H5", "READ_TRIGGER": "J10",
    "ARST_N": "F8", "LDO_DIG_EN": "D3", "NC": "C10 E7 F7 G7",
}
NET = {"VDD25": "VDD25", "VDD25R": "VDD25", "VDD25A": "VDD25", "VDDINT_1": "VDD25", "VDD18": "VDD18",
       "VDD13D": "VDD135", "VDD13P": "VDD135", "VDD13A": "VDD135",
       "VSSA": GND, "VSSD": GND, "VSSPIX": GND, "NC_VSS": GND, "JTAG_MODE": GND, "ATPG_MODE": GND,
       "CLK_IN": "MCLK", "CCI_ADDR0": "ADDR0", "CCI_ADDR1": "ADDR1", "CCI_SDA": "SDA", "CCI_SCL": "SCL",
       "MIPI_CLK_P": "CP", "MIPI_CLK_N": "CN", "MIPI_D0_P": "DP0", "MIPI_D0_N": "DN0", "MIPI_D1_P": "DP1", "MIPI_D1_N": "DN1",
       "ARST_N": "ARST_N", "REQ_EXP": "REQ_EXP", "REQ_FRAME": "REQ_FRAME", "ILLUM_TRIGGER": "ILLUM_TRIGGER",
       # CHANGED: the original ties LDO_DIG_EN to ground (as read from the scan). The datasheet says it may be left
       # open and has an internal pull-up to VDD25, which keeps the on-chip VDD11D regulator enabled. VERIFY on hardware.
       "LDO_DIG_EN": "NC", "READ_TRIGGER": "NC", "NC": "NC"}
TYPE = {"VDD25": "power_in", "VDD25R": "power_in", "VDD25A": "power_in", "VDDINT_1": "power_in", "VDD18": "power_in",
        "VDD13D": "power_in", "VDD13P": "power_in", "VDD13A": "power_in", "VSSA": "power_in", "VSSD": "power_in",
        "VSSPIX": "power_in", "NC_VSS": "passive", "CLK_IN": "input", "CCI_ADDR0": "input", "CCI_ADDR1": "input",
        "CCI_SDA": "bidirectional", "CCI_SCL": "bidirectional", "JTAG_MODE": "input", "ATPG_MODE": "input",
        "REQ_FRAME": "input", "REQ_EXP": "input", "ILLUM_TRIGGER": "output", "READ_TRIGGER": "output", "ARST_N": "input",
        "LDO_DIG_EN": "input", "NC": "no_connect"}
pins, left, right = {}, [], []
for name, balls in BALLS.items():
    for b in balls.split():
        net = NET.get(name, name)          # internal-supply pins get a net of their own name, decoupled below
        pins[b] = net
        t = TYPE.get(name, "passive")
        (right if t == "power_in" or name.startswith(("VDD", "VSS", "NC_VSS")) or name in ("R_EXT", "C_EXT") else left).append((b, name, t))
assert len(pins) == len(set(pins)), "duplicate ball"
D.add("U5", None, "Mira220", "aviac:Mira220_CSP", pins, "SENSOR",
      mpn="MIRA220-2QM1WP (mono) / -2QC1WP (RGB) / -2QI1WP (RGB-IR)", mfr="ams OSRAM",
      desc="2.2 MP global-shutter image sensor, CSP; the three colour versions share this ball map", mass=0.05,
      custom=dict(kind="box", ref="U", left=left, right=right))

# decoupling exactly as datasheet figure 4 (value, voltage rating)
# CHANGED: the original fits 4.7 uF on every regulator net; the datasheet asks 2.2 uF / 16 V (4.7 uF / 10 V on VDDINT_7)
B = "SENSOR"
for net in ("VDDINT_2", "VDDINT_3", "VDDINT_4", "VDDINT_5", "VDDINT_6", "VDD11A", "VDD11D", "VDD11P", "VDDNEG_1", "VDDNEG_2"):
    D.C(net, GND, "2u2", B, "0402", "16V", "X5R")
D.C("VDDINT_7", GND, "4u7", B, "0402", "10V", "X5R")
for _ in range(3):                        # VDDINT_1, VDD25R, VDD25A: on the VDD25 net, one 2.2 uF each
    D.C("VDD25", GND, "2u2", B, "0402", "16V", "X5R")
D.C("C_EXT", GND, "1u", B, "0402", "16V", "X5R")
D.R("R_EXT", GND, "12k", B, tol="0.1% 25ppm")
D.R("ILLUM_TRIGGER", "EXPOSING", "0R", B, dnp=True)   # ADDED option: fit to send the exposure window to FPC pin 12

# ---------------------------------------------------------------- supplies and sequencing (U1-U4, R6-R8, C1-C9)
B = "PWR"
LDO = "Regulator_Linear:AP2112K-1.8"        # same SOT-23-5 pinout as the original JW7807 (VIN GND EN NC VOUT)
for ref, vout, en, v in (("U1", "VDD135", "EN_VDD135", "1.35"), ("U2", "VDD18", "VDD135", "1.8"), ("U3", "VDD25", "EN_VDD25", "2.5")):
    D.add(ref, LDO, f"JW7807-{v}", "Package_TO_SOT_SMD:SOT-23-5", {1: "VCC3V3", 2: GND, 3: en, 4: "NC", 5: vout}, B,
          mpn=f"JW7807-{v}SOTA#TRPBF", mfr="Joulwatt",
          desc=f"LDO {v} V, SOT-23-5 (as in the original). VERIFY current rating: the sensor needs 350 mA on 2.5 V at start-up", mass=0.01)
D.add("U4", "Power_Supervisor:LM3880", "LM3880MF-1AA", "Package_TO_SOT_SMD:SOT-23-6",
      {1: "VCC3V3", 2: GND, 3: "PWDN", 4: "ARST_N", 5: "EN_VDD135", 6: "EN_VDD25"}, B,
      mpn="LM3880MF-1AA/NOPB", mfr="Texas Instruments",
      desc="Power sequencer: 2.5 V, then 1.35 V, then reset release (the original marks it EN/SOT-23-6; LM3880 per the Camera R3 board)", mass=0.01)
D.R("VCC3V3", "EN_VDD25", "12k", B)       # R6
D.R("VCC3V3", "EN_VDD135", "12k", B)      # R7
D.R("VDD18", "ARST_N", "12k", B)          # R8
for net, n in (("VCC3V3", 2), ("VDD25", 2), ("VDD18", 2), ("VDD135", 2)):
    for _ in range(n):
        D.C(net, GND, "4u7", B, "0402", "10V", "X5R")

# ---------------------------------------------------------------- connector, filters, clock, straps
B = "IO"
D.add("J1", "Connector_Generic_MountingPin:Conn_01x22_MountingPin", "FPC 22-pin",
      "Connector_FFC-FPC:Hirose_FH12-22S-0.5SH_1x22-1MP_P0.50mm_Horizontal",
      {1: GND, 2: "MDN0", 3: "MDP0", 4: GND, 5: "MDN1", 6: "MDP1", 7: GND, 8: "MCN", 9: "MCP", 10: GND,
       11: "NC", 12: "EXPOSING", 13: GND, 14: "NC", 15: "NC", 16: GND, 17: "PWDN",
       18: "TRIG",                          # CHANGED: GPIO1 / LED enable in the original, now the hardware trigger
       19: GND, 20: "SCL", 21: "SDA", 22: "VCC3V3", "MP": GND}, B,
      mpn="54548-2271", mfr="Molex", desc="22-pin 0.5 mm FPC (original part; footprint shown is the Hirose FH12 equivalent, VERIFY)", mass=0.2)
for ref, (a, b, c, d) in (("L1", ("CP", "MCP", "CN", "MCN")), ("L2", ("DP0", "MDP0", "DN0", "MDN0")), ("L3", ("DP1", "MDP1", "DN1", "MDN1"))):
    D.add(ref, "Device:Filter_EMI_CommonMode", "DLP11SN900HL2L", "Inductor_SMD:L_CommonModeChoke_TDK_ACM2520-2P",
          {1: a, 2: b, 4: c, 3: d}, B, mpn="DLP11SN900HL2L", mfr="Murata",
          desc="Common-mode filter for MIPI D-PHY, 90 ohm (footprint is a stand-in, VERIFY)", mass=0.005)
D.add("X1", "Oscillator:ASE-xxxMHz", "38.4MHz", "Oscillator:Oscillator_SMD_Abracon_ASE-4Pin_3.2x2.5mm",
      {1: "VDD18", 2: GND, 3: "MCLK", 4: "VDD18"}, B, mpn="38.4 MHz 1.8 V XO, +/-50 ppm", mfr="(original part unmarked)",
      desc="Sensor reference clock: 38.4 MHz, 45-55 % duty, <200 ps jitter per datasheet", mass=0.02)
D.C("VDD18", GND, "100n", B)
D.R("ADDR0", GND, "12k", B)               # R2: address bit 0 low
D.R("ADDR1", GND, "12k", B)               # R3: address bit 1 low -> I2C address 0x54
D.R("VDD18", "ADDR0", "12k", B, dnp=True)   # ADDED: fit this and remove R2 for address 0x55 (second camera on one bus)
D.R("VDD18", "ADDR1", "12k", B, dnp=True)   # ADDED: fit this and remove R3 for 0x56
D.R("REQ_EXP", GND, "12k", B)             # R4: keeps the sensor idle when no trigger is connected
D.R("REQ_FRAME", GND, "12k", B)           # R5
D.R("TRIG", "REQ_EXP", "0R", B)           # ADDED: the trigger from FPC pin 18 reaches the sensor
# REMOVED: D1 power LED (it was driven from GPIO1, which is now the trigger)

if __name__ == "__main__":
    nets = D.nets()
    print("parts", len(D.parts), "nets", len(nets), "balls", len(pins))
    print("single-pin nets:", [n for n, v in nets.items() if len(v) == 1])
