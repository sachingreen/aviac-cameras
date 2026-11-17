"""Aviac Jetson Orin Nano carrier - single source of truth for the netlist.

Shared by every Aviac camera that runs on an Orin Nano: the 6-band camera fits all four
camera ports, the Duo fits two (CAM2/CAM3 parts are a do-not-fit variant, see variants.py).

Every part is declared once here with its symbol, footprint, value, manufacturer
part number and pin-to-net map. gen_sch.py turns this into the KiCad schematic,
gen_pcb.py into the board. Pin numbers for library parts come from the KiCad 8
symbol libraries; Jetson pins from jetson_pins.py.
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "toolkit", "kicad"))
from netlist import Part, Design
from jetson_pins import PINS as JPINS

PROJECT = "aviac_carrier"
TITLE = "Aviac Jetson Orin Nano carrier (6-band and Duo cameras)"
REV = "A1 (pre-release: camera I2C moved to 1.8 V; not yet reviewed for manufacture)"


D = Design()
for k, t in [
    ("PWR_IN", "POWER INPUT 3S-6S: REVERSE-POLARITY AND SURGE PROTECTION"),
    ("PWR_SYS", "7.5 V 4 A MODULE SUPPLY (VSYS)"),
    ("PWR_3V3", "3.3 V 3 A PERIPHERAL SUPPLY AND 1.8 V ALWAYS-ON"),
    ("SOM", "JETSON ORIN NANO MODULE"),
    ("SOMCTL", "MODULE POWER SEQUENCING, RESET AND RECOVERY"),
    ("CAM", "CAMERA PORTS: 4 x 2-LANE MIPI CSI-2, 22-PIN FPC"),
    ("I2C", "CAMERA I2C SWITCH"),
    ("MCU", "SYNC MICROCONTROLLER"),
    ("TRIG", "TRIGGER FAN-OUT AND AUTOPILOT INTERFACE"),
    ("GNSS", "GNSS RECEIVER WITH PPS"),
    ("IMU", "INERTIAL SENSOR"),
    ("NVME", "M.2 2230 NVME STORAGE"),
    ("USB", "USB-C: FLASHING AND DATA"),
    ("MISC", "DLS PORT, DEBUG, ID EEPROM, MECHANICAL"),
]:
    D.block(k, t)

GND = "GND"

# =============================================================== POWER INPUT
B = "PWR_IN"
D.add("J1", "Connector_Generic:Conn_01x02", "XT30PW-M", "Connector_AMASS:AMASS_XT30PW-M_1x02_P2.50mm_Horizontal",
      {1: "VBAT_IN", 2: GND}, B, mpn="XT30PW-M", mfr="AMASS", desc="Battery input 3S-6S (9-25.2 V), 15 A connector", mass=1.4)
D.add("D1", "Device:D_TVS", "SMBJ26CA", "Diode_SMD:D_SMB", {1: "VBAT_IN", 2: GND}, B,
      mpn="SMBJ26CA", mfr="Littelfuse", desc="TVS 26 V stand-off, bidirectional, 600 W", mass=0.1)
D.add("U1", "Power_Management:LM74700", "LM74700-Q1", "Package_TO_SOT_SMD:SOT-23-6",
      {1: "RP_VCAP", 2: GND, 3: "VBAT_IN", 4: "VBAT", 5: "RP_GATE", 6: "VBAT_IN"}, B,
      mpn="LM74700QDBVRQ1", mfr="Texas Instruments", desc="Ideal-diode controller, reverse-polarity protection, 3.2-65 V", mass=0.02)
D.add("Q1", "Transistor_FET:BSC028N06LS3", "BSC028N06LS3", "Package_TO_SOT_SMD:TDSON-8-1",
      {1: "VBAT_IN", 2: "VBAT_IN", 3: "VBAT_IN", 4: "RP_GATE", 5: "VBAT"}, B,
      mpn="BSC028N06LS3GATMA1", mfr="Infineon", desc="N-MOSFET 60 V 2.8 mOhm, ideal-diode pass element", mass=0.12)
D.C("RP_VCAP", "VBAT_IN", "100n", B, "0603", "50V")
D.C("VBAT_IN", GND, "100n", B, "0603", "50V")
D.C("VBAT", GND, "22u", B, "1210", "50V")
D.C("VBAT", GND, "22u", B, "1210", "50V")
D.C("VBAT", GND, "100n", B, "0603", "50V")
D.R("VBAT", "VBAT_SENSE", "100k", B)
D.R("VBAT_SENSE", GND, "6k8", B)
D.C("VBAT_SENSE", GND, "100n", B)

# =============================================================== VSYS 7.5 V
B = "PWR_SYS"
D.add("U2", "Regulator_Switching:LMR33640ADDA", "LMR33640ADDA", "Package_SO:Texas_HSOP-8-1EP_3.9x4.9mm_P1.27mm_ThermalVias",
      {1: GND, 2: "VBAT", 3: "VSYS_EN", 4: "VSYS_PG", 5: "VSYS_FB", 6: "VSYS_VCC", 7: "VSYS_BOOT", 8: "VSYS_SW", 9: GND}, B,
      mpn="LMR33640ADDAR", mfr="Texas Instruments", desc="Synchronous buck 3.8-36 V in, 4 A, 400 kHz", mass=0.08)
D.add("L1", "Device:L", "6u8 8A", "Inductor_SMD:L_Bourns_SRP6060FA", {1: "VSYS_SW", 2: "VSYS"}, B,
      mpn="SRP6060FA-6R8M", mfr="Bourns", desc="Power inductor 6.8 uH, Isat 8 A, 6.6 x 6.4 x 5.8 mm", mass=1.3)
D.C("VSYS_BOOT", "VSYS_SW", "100n", B, "0603", "50V")
D.C("VSYS_VCC", GND, "1u", B, "0603", "16V")
D.C("VBAT", GND, "10u", B, "1210", "50V")
D.C("VBAT", GND, "100n", B, "0603", "50V")
D.R("VBAT", "VSYS_EN", "100k", B)
D.R("VSYS_EN", GND, "16k2", B)          # UVLO: on at about 8.8 V
D.R("VSYS", "VSYS_FB", "100k", B)
D.R("VSYS_FB", GND, "15k4", B)          # 1.0 V * (1 + 100/15.4) = 7.49 V
D.C("VSYS", "VSYS_FB", "22p", B, "0402", "50V", "C0G")
for _ in range(3):
    D.C("VSYS", GND, "22u", B, "1210", "25V")
D.C("VSYS", GND, "100n", B, "0603", "50V")
D.R("VSYS_VCC", "VSYS_PG", "100k", B)
D.add("TP1", "Connector:TestPoint", "VSYS", "TestPoint:TestPoint_Pad_D1.0mm", {1: "VSYS"}, B, desc="Test point")

# ========================================================= 3V3 and 1V8 rails
B = "PWR_3V3"
D.add("U3", "Regulator_Switching:LMR33630ADDA", "LMR33630ADDA", "Package_SO:Texas_HSOP-8-1EP_3.9x4.9mm_P1.27mm_ThermalVias",
      {1: GND, 2: "VBAT", 3: "P3V3_EN", 4: "P3V3_PG", 5: "P3V3_FB", 6: "P3V3_VCC", 7: "P3V3_BOOT", 8: "P3V3_SW", 9: GND}, B,
      mpn="LMR33630ADDAR", mfr="Texas Instruments", desc="Synchronous buck 3.8-36 V in, 3 A, 400 kHz", mass=0.08)
D.add("L2", "Device:L", "6u8 3.9A", "Inductor_SMD:L_Coilcraft_XAL4030-XXX", {1: "P3V3_SW", 2: "+3V3"}, B,
      mpn="XAL4030-682ME", mfr="Coilcraft", desc="Power inductor 6.8 uH, Isat 3.9 A, 4 x 4 x 3.1 mm", mass=0.26)
D.C("P3V3_BOOT", "P3V3_SW", "100n", B, "0603", "50V")
D.C("P3V3_VCC", GND, "1u", B, "0603", "16V")
D.C("VBAT", GND, "10u", B, "1210", "50V")
D.C("VBAT", GND, "100n", B, "0603", "50V")
D.R("+3V3", "P3V3_FB", "100k", B)
D.R("P3V3_FB", GND, "43k2", B)          # 1.0 V * (1 + 100/43.2) = 3.31 V
D.C("+3V3", "P3V3_FB", "22p", B, "0402", "50V", "C0G")
D.C("+3V3", GND, "22u", B, "0805", "10V", "X5R")
D.C("+3V3", GND, "22u", B, "0805", "10V", "X5R")
D.C("+3V3", GND, "100n", B)
D.R("P3V3_VCC", "P3V3_PG", "100k", B)
D.R("SYS_RESET_N", "P3V3_EN", "10k", B)   # peripherals power up only after the module releases reset
D.R("P3V3_EN", GND, "100k", B)
D.add("U4", "Regulator_Linear:LP2985-1.8", "LP2985-18", "Package_TO_SOT_SMD:SOT-23-5",
      {1: "VSYS", 2: GND, 3: "VSYS", 4: "LDO_BP", 5: "+1V8"}, B,
      mpn="LP2985-18DBVR", mfr="Texas Instruments", desc="LDO 1.8 V 150 mA, 16 V in, always-on rail for the sync MCU", mass=0.02)
D.C("VSYS", GND, "1u", B, "0603", "25V")
D.C("LDO_BP", GND, "10n", B)
D.C("+1V8", GND, "2u2", B, "0603", "10V")
D.add("TP2", "Connector:TestPoint", "3V3", "TestPoint:TestPoint_Pad_D1.0mm", {1: "+3V3"}, B, desc="Test point")
D.add("TP3", "Connector:TestPoint", "1V8", "TestPoint:TestPoint_Pad_D1.0mm", {1: "+1V8"}, B, desc="Test point")
D.add("TP4", "Connector:TestPoint", "GND", "TestPoint:TestPoint_Pad_D1.0mm", {1: GND}, B, desc="Test point")
D.add("D2", "Device:LED", "green", "LED_SMD:LED_0402_1005Metric", {1: "LED_PWR_K", 2: "+3V3"}, B,
      mpn="LTST-C281KGKT", mfr="Lite-On", desc="LED green 0402, peripherals powered", mass=0.001)
D.R("LED_PWR_K", GND, "1k", B)

# ============================================================ JETSON MODULE
B = "SOM"
J = {}
for n, name in JPINS.items():
    if name == "GND":
        J[n] = GND
    elif name == "VDD_IN":
        J[n] = "VSYS"
    else:
        J[n] = "NC"
CSI = {}   # lane map: module port -> camera
for port, cam in ((0, 0), (1, 1), (2, 2), (3, 3)):
    for sig in ("D0", "D1", "CLK"):
        for pol in ("N", "P"):
            CSI[f"CSI{port}_{sig}_{pol}"] = f"CAM{cam}_{sig}_{pol}"
JN = {v: k for k, v in JPINS.items() if v not in ("GND", "VDD_IN")}


def jet(name, net):
    J[JN[name]] = net


for k, v in CSI.items():
    jet(k, v)
jet("CAM_I2C_SCL", "I2C_CAM_SCL"); jet("CAM_I2C_SDA", "I2C_CAM_SDA")
jet("CAM0_PWDN", "CAM0_EN"); jet("CAM1_PWDN", "CAM1_EN"); jet("GPIO02", "CAM2_EN"); jet("GPIO03", "CAM3_EN")
jet("UART0_TXD", "MCU_UART_RX"); jet("UART0_RXD", "MCU_UART_TX")
jet("UART1_TXD", "TELEM_TX_1V8"); jet("UART1_RXD", "TELEM_RX_1V8")
jet("UART2_TXD", "DBG_TX"); jet("UART2_RXD", "DBG_RX")
jet("USB0_D_N", "USB_D_N"); jet("USB0_D_P", "USB_D_P")
jet("GPIO01/CLK", "USB_VBUS_DET")
jet("PCIE0_RX0_N", "PCIE_RX_N"); jet("PCIE0_RX0_P", "PCIE_RX_P")
jet("PCIE0_TX0_N", "PCIE_TX_C_N"); jet("PCIE0_TX0_P", "PCIE_TX_C_P")
jet("PCIE0_CLK_N", "PCIE_CLK_N"); jet("PCIE0_CLK_P", "PCIE_CLK_P")
jet("PCIE0_RST*", "PCIE_RST_N"); jet("PCIE0_CLKREQ*", "PCIE_CLKREQ_N"); jet("PCIE_WAKE*", "PCIE_WAKE_N")
jet("FORCE_RECOVERY*", "FORCE_RECOVERY_N")
jet("POWER_EN", "POWER_EN"); jet("SYS_RESET*", "SYS_RESET_N"); jet("SHUTDOWN_REQ*", "SHUTDOWN_REQ_N")
jet("GPIO09/AUD_MCLK", "PPS_1V8"); jet("GPIO11/CLK", "FRAME_SYNC")
jet("GPIO12/PWM", "MCU_NRST_REQ"); jet("GPIO13/PWM", "MCU_BOOT_REQ")
jet("I2C2_SCL", "I2C_ID_SCL"); jet("I2C2_SDA", "I2C_ID_SDA")

D.add("J2", None, "Jetson Orin Nano 8GB", "aviac:TE_2309413", J, B,
      mpn="2309413-1", mfr="TE Connectivity", desc="260-pin SO-DIMM socket, 9.2 mm, for Jetson Orin Nano module", mass=3.4,
      custom=dict(kind="jetson"))
D.C("VSYS", GND, "22u", B, "1210", "25V")
D.C("VSYS", GND, "22u", B, "1210", "25V")
D.C("VSYS", GND, "100n", B, "0603", "50V")
for nm, hole in (("H1", "MODULE STANDOFF"), ("H2", "MODULE STANDOFF")):
    D.add(nm, "Mechanical:MountingHole_Pad", "M2.5 standoff 6.5 mm", "MountingHole:MountingHole_2.7mm_M2.5_Pad", {1: GND}, B,
          mpn="9774065151R", mfr="Wurth Elektronik", desc="SMT spacer M2.5, 6.5 mm, module retention", mass=0.5)

B = "SOMCTL"
D.R("VSYS", "POWER_EN", "100k", B)       # divider gives 2.4 V: module switches on as soon as VSYS is up
D.R("POWER_EN", GND, "47k", B)
D.R("+1V8", "SHUTDOWN_REQ_N", "100k", B)
D.add("SW1", "Switch:SW_Push", "RECOVERY", "Button_Switch_SMD:SW_SPST_B3U-1000P-B", {1: "FORCE_RECOVERY_N", 2: GND}, B,
      mpn="B3U-1000P-B", mfr="Omron", desc="Tactile switch, force-recovery (hold while powering on to flash)", mass=0.05)
D.add("SW2", "Switch:SW_Push", "RESET", "Button_Switch_SMD:SW_SPST_B3U-1000P-B", {1: "SYS_RESET_N", 2: GND}, B,
      mpn="B3U-1000P-B", mfr="Omron", desc="Tactile switch, system reset", mass=0.05)
D.R("SYS_RESET_N", "SYS_RESET_SENSE", "10k", B)

# ============================================================= CAMERA PORTS
B = "CAM"
CAMDESC = ["CAM0: RGB, IMX565 (via adapter)", "CAM1: red edge, Mira220", "CAM2: NIR, Mira220", "CAM3: extended NIR, Mira220"]
for i in range(4):
    c = f"CAM{i}"
    pins = {1: GND, 2: f"{c}_D0_N", 3: f"{c}_D0_P", 4: GND, 5: f"{c}_D1_N", 6: f"{c}_D1_P", 7: GND,
            8: f"{c}_CLK_N", 9: f"{c}_CLK_P", 10: GND, 11: "NC", 12: "NC", 13: GND, 14: "NC", 15: "NC", 16: GND,
            17: f"{c}_EN", 18: f"{c}_TRIG", 19: GND, 20: f"{c}_SCL", 21: f"{c}_SDA", 22: f"{c}_3V3", "MP": GND}
    if i in (0, 2):
        # top-side connectors: conductor order is mirrored on the board, so the cable for these two ports
        # must be the opposite-side-contact type. Net-to-conductor mapping stays the module's 22-pin pinout.
        pins = {(23 - k if isinstance(k, int) else k): v for k, v in pins.items()}
    D.add(f"J{3+i}", "Connector_Generic_MountingPin:Conn_01x22_MountingPin", CAMDESC[i] + (" (mirrored)" if i in (0, 2) else ""),
          "Connector_FFC-FPC:Hirose_FH12-22S-0.5SH_1x22-1MP_P0.50mm_Horizontal", pins, B,
          mpn="FH12-22S-0.5SH(55)", mfr="Hirose", desc="FPC connector 22-pin 0.5 mm, bottom contact", mass=0.25)
    D.add("FB", "Device:FerriteBead", "600R 1A", "Inductor_SMD:L_0603_1608Metric", {1: "+3V3", 2: f"{c}_3V3"}, B,
          mpn="BLM18KG601SN1D", mfr="Murata", desc="Ferrite bead 600 ohm at 100 MHz, 1.3 A, 0603", mass=0.004)
    D.C(f"{c}_3V3", GND, "10u", B, "0603", "10V", "X5R")
    D.C(f"{c}_3V3", GND, "100n", B)
    D.R(f"{c}_EN", GND, "100k", B)
    # Mira220 I2C and trigger inputs are 1.8 V parts (datasheet: VIH max = VDD18), so the camera side of the
    # I2C switch is pulled up to 1.8 V (rev A0 pulled it to 3.3 V, which overdrove the sensor pins)
    D.R("+1V8", f"{c}_SCL", "2k2", B)
    D.R("+1V8", f"{c}_SDA", "2k2", B)
    D.R(f"TRIG{i}", f"{c}_TRIG", "33R", B)

B = "I2C"
D.add("U5", "Interface_Expansion:TCA9548APWR", "TCA9548A", "Package_SO:TSSOP-24_4.4x7.8mm_P0.65mm",
      {1: GND, 2: GND, 3: "I2C_MUX_RST_N", 4: "CAM0_SDA", 5: "CAM0_SCL", 6: "CAM1_SDA", 7: "CAM1_SCL", 8: "CAM2_SDA", 9: "CAM2_SCL",
       10: "CAM3_SDA", 11: "CAM3_SCL", 12: GND, 13: "NC", 14: "NC", 15: "NC", 16: "NC", 17: "NC", 18: "NC", 19: "NC", 20: "NC",
       21: GND, 22: "I2C_CAM_SCL", 23: "I2C_CAM_SDA", 24: "+1V8"}, B,
      mpn="TCA9548APWR", mfr="Texas Instruments", desc="8-channel I2C switch (address 0x70), powered at 1.8 V so its pass gates translate to the 1.8 V cameras; all Mira220 modules answer at 0x54", mass=0.09)
D.C("+1V8", GND, "100n", B)
D.R("+1V8", "I2C_MUX_RST_N", "10k", B)
D.R("+1V8", "I2C_CAM_SCL", "2k2", B, dnp=True)   # the Jetson module pulls CAM_I2C up itself; fit only if the measured rise time needs it
D.R("+1V8", "I2C_CAM_SDA", "2k2", B, dnp=True)

# ================================================================= SYNC MCU
B = "MCU"
M = {n: "NC" for n in range(1, 49)}
M.update({4: "+1V8", 5: "+1V8", 6: "+1V8", 7: GND,
          8: "MCU_OSC_IN", 9: "MCU_OSC_OUT", 10: "MCU_NRST",
          11: "VBAT_SENSE",          # PA0  ADC
          12: "FC_TRIG_1V8",         # PA1  TIM2_CH2 capture: autopilot camera trigger
          13: "MCU_UART_TX",         # PA2  USART2_TX -> Jetson UART0_RXD
          14: "MCU_UART_RX",         # PA3  USART2_RX <- Jetson UART0_TXD
          15: "IMU_CS_N", 16: "IMU_SCK", 17: "IMU_MISO", 18: "IMU_MOSI",   # PA4..PA7 SPI1
          19: "IMU_INT1",            # PB0
          20: "FC_FB_GATE",          # PB1  exposure feedback to autopilot
          21: "DLS_INT",             # PB2
          22: "GNSS_RXD",            # PB10 USART3_TX
          23: "GNSS_TXD",            # PB11 USART3_RX
          24: "LED_STAT_K",          # PB12 open-drain
          25: "POWER_EN",            # PB13 open-drain: pull low to switch the module off
          26: "SHUTDOWN_REQ_N",      # PB14
          27: "SYS_RESET_SENSE",     # PB15
          28: "TRIG0", 29: "TRIG1", 32: "TRIG2", 33: "TRIG3",   # PA8, PA9, PA10, PA11 = TIM1_CH1..4
          35: "SWDIO", 36: "SWCLK_BOOT0",
          37: "PPS_1V8",             # PA15 TIM2_CH1 capture: GNSS time pulse
          44: "FRAME_SYNC",          # PB5 -> Jetson GPIO11
          47: "DLS_SCL", 48: "DLS_SDA"})   # PB8/PB9 I2C1
D.add("U6", "MCU_ST_STM32G0:STM32G0B1CBTx", "STM32G0B1CBT6", "Package_QFP:LQFP-48_7x7mm_P0.5mm", M, B,
      mpn="STM32G0B1CBT6", mfr="STMicroelectronics", desc="Sync MCU, runs at 1.8 V; one timer drives all four camera triggers", mass=0.18)
for _ in range(3):
    D.C("+1V8", GND, "100n", B)
D.C("+1V8", GND, "4u7", B, "0603", "10V", "X5R")
D.C("MCU_NRST", GND, "100n", B)
D.add("Y1", "Device:Crystal_GND24", "8MHz", "Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm",
      {1: "MCU_OSC_IN", 2: GND, 3: "MCU_OSC_OUT", 4: GND}, B,
      mpn="ABM8-8.000MHZ-10-D1G-T", mfr="Abracon", desc="Crystal 8 MHz, 10 pF, 3.2 x 2.5 mm", mass=0.02)
D.C("MCU_OSC_IN", GND, "12p", B, "0402", "50V", "C0G")
D.C("MCU_OSC_OUT", GND, "12p", B, "0402", "50V", "C0G")
D.add("J7", "Connector_Generic:Conn_02x03_Odd_Even", "SWD (Tag-Connect)", "Connector:Tag-Connect_TC2030-IDC-NL_2x03_P1.27mm_Vertical",
      {1: "+1V8", 2: "SWDIO", 3: "MCU_NRST", 4: "SWCLK_BOOT0", 5: GND, 6: "NC"}, B,
      mpn="(no part: PCB pads for TC2030-IDC-NL cable)", mfr="Tag-Connect", desc="SWD programming footprint, no component fitted")
D.R("MCU_NRST_REQ", "MCU_NRST", "1k", B)
D.R("MCU_BOOT_REQ", "SWCLK_BOOT0", "1k", B)
D.add("D3", "Device:LED", "amber", "LED_SMD:LED_0402_1005Metric", {1: "LED_STAT_K", 2: "LED_STAT_A"}, B,
      mpn="LTST-C281KFKT", mfr="Lite-On", desc="LED amber 0402, sync status", mass=0.001)
D.R("+3V3", "LED_STAT_A", "1k", B)

B = "TRIG"
D.add("J8", "Connector_Generic_MountingPin:Conn_01x06_MountingPin", "TELEM (MAVLink)", "Connector_JST:JST_GH_SM06B-GHS-TB_1x06-1MP_P1.25mm_Horizontal",
      {1: "NC", 2: "TELEM_RX_3V3", 3: "TELEM_TX_3V3", 4: "NC", 5: "NC", 6: GND, "MP": GND}, B,
      mpn="SM06B-GHS-TB", mfr="JST", desc="Autopilot TELEM port, Pixhawk pinout (pin 1 = 5 V not used)", mass=0.3)
D.add("J9", "Connector_Generic_MountingPin:Conn_01x04_MountingPin", "CAM TRIGGER", "Connector_JST:JST_GH_SM04B-GHS-TB_1x04-1MP_P1.25mm_Horizontal",
      {1: "FC_TRIG_IN", 2: "FC_FB_OUT", 3: "PPS_OUT", 4: GND, "MP": GND}, B,
      mpn="SM04B-GHS-TB", mfr="JST", desc="Camera trigger in, exposure feedback out, PPS out", mass=0.25)
D.add("U7", "Logic_LevelTranslator:TXS0102DCU", "TXS0102", "Package_SO:VSSOP-8_2.3x2mm_P0.5mm",
      {1: "TELEM_RX_3V3", 2: GND, 3: "+1V8", 4: "TELEM_RX_1V8", 5: "TELEM_TX_1V8", 6: "TELEM_OE", 7: "+3V3", 8: "TELEM_TX_3V3"}, B,
      mpn="TXS0102DCUR", mfr="Texas Instruments", desc="2-bit level translator 1.8 V <-> 3.3 V for the MAVLink UART", mass=0.01)
D.R("+1V8", "TELEM_OE", "10k", B)
D.C("+1V8", GND, "100n", B)
D.C("+3V3", GND, "100n", B)
D.add("U8", "74xGxx:74LVC2G17", "74LVC2G17", "Package_TO_SOT_SMD:SOT-363_SC-70-6",
      {1: "FC_TRIG_IN_F", 2: GND, 3: "PPS_1V8", 4: "PPS_BUF", 5: "+1V8", 6: "FC_TRIG_1V8"}, B,
      mpn="SN74LVC2G17DCKR", mfr="Texas Instruments", desc="Dual Schmitt buffer at 1.8 V, 5 V-tolerant inputs", mass=0.006)
D.C("+1V8", GND, "100n", B)
D.R("FC_TRIG_IN", "FC_TRIG_IN_F", "1k", B)
D.R("FC_TRIG_IN_F", GND, "100k", B)
D.C("FC_TRIG_IN_F", GND, "100p", B, "0402", "50V", "C0G")
D.R("PPS_BUF", "PPS_OUT", "100R", B)
D.add("Q2", "Transistor_FET:2N7002", "2N7002", "Package_TO_SOT_SMD:SOT-23", {1: "FC_FB_GATE", 2: GND, 3: "FC_FB_OUT"}, B,
      mpn="2N7002NXAKR", mfr="Nexperia", desc="N-MOSFET, open-drain exposure feedback to autopilot", mass=0.008)
D.R("FC_FB_GATE", GND, "100k", B)
D.R("+3V3", "FC_FB_OUT", "10k", B)
D.add("D4", "Power_Protection:PESD3V3L4UG", "PESD3V3L4UG", "Package_TO_SOT_SMD:SOT-353_SC-70-5",
      {1: "TELEM_RX_3V3", 2: GND, 3: "TELEM_TX_3V3", 4: "FC_TRIG_IN", 5: "FC_FB_OUT"}, B,
      mpn="PESD3V3L4UG,115", mfr="Nexperia", desc="4-line ESD protection for the autopilot connectors", mass=0.006)

# ===================================================================== GNSS
B = "GNSS"
D.add("U9", "RF_GPS:MAX-M10S", "MAX-M10S", "RF_GPS:ublox_MAX",
      {1: GND, 2: "GNSS_TXD", 3: "GNSS_RXD", 4: "PPS_1V8", 5: "NC", 6: "+1V8", 7: "+1V8", 8: "GNSS_VCC", 9: "NC", 10: GND,
       11: "GNSS_RF", 12: GND, 13: "NC", 14: "GNSS_VCC_RF", 15: GND, 16: "NC", 17: "NC", 18: "NC"}, B,
      mpn="MAX-M10S-00B", mfr="u-blox", desc="GNSS receiver with time pulse (PPS); VIO_SEL to GND for 1.8 V I/O", mass=0.6)
D.add("FB", "Device:FerriteBead", "600R 1A", "Inductor_SMD:L_0603_1608Metric", {1: "+3V3", 2: "GNSS_VCC"}, B,
      mpn="BLM18KG601SN1D", mfr="Murata", desc="Ferrite bead 600 ohm at 100 MHz, 1.3 A, 0603", mass=0.004)
D.C("GNSS_VCC", GND, "10u", B, "0603", "10V", "X5R")
D.C("GNSS_VCC", GND, "100n", B)
D.C("+1V8", GND, "100n", B)
D.R("GNSS_VCC_RF", "GNSS_BIAS", "10R", B)
D.add("L3", "Device:L", "27n", "Inductor_SMD:L_0402_1005Metric", {1: "GNSS_BIAS", 2: "GNSS_RF"}, B,
      mpn="LQG15HS27NJ02D", mfr="Murata", desc="RF inductor 27 nH, antenna bias feed", mass=0.001)
D.C("GNSS_BIAS", GND, "10n", B)
D.add("J10", "Connector:Conn_Coaxial", "GNSS ANT", "Connector_Coaxial:U.FL_Hirose_U.FL-R-SMT-1_Vertical", {1: "GNSS_RF", 2: GND}, B,
      mpn="U.FL-R-SMT-1(10)", mfr="Hirose", desc="U.FL antenna connector, active antenna on the top unit", mass=0.05)

# ====================================================================== IMU
B = "IMU"
D.add("U10", None, "ICM-42688-P", "Package_LGA:LGA-14_3x2.5mm_P0.5mm_LayoutBorder3x4y",
      {1: "IMU_MISO", 2: "NC", 3: "NC", 4: "IMU_INT1", 5: "+1V8", 6: GND, 7: "NC", 8: "+1V8", 9: "NC", 10: "NC", 11: "NC",
       12: "IMU_CS_N", 13: "IMU_SCK", 14: "IMU_MOSI"}, B,
      mpn="ICM-42688-P", mfr="TDK InvenSense", desc="6-axis IMU, SPI, time-stamped by the sync MCU", mass=0.02,
      custom=dict(kind="box", ref="U", left=[(12, "AP_CS", "input"), (13, "AP_SCLK", "input"), (14, "AP_SDI", "input"),
                                             (1, "AP_SDO", "output"), (4, "INT1", "output"), (9, "INT2/FSYNC", "bidirectional")],
                  right=[(8, "VDD", "power_in"), (5, "VDDIO", "power_in"), (6, "GND", "power_in"), (2, "RESV", "no_connect"),
                         (3, "RESV", "no_connect"), (7, "RESV", "no_connect"), (10, "RESV", "no_connect"), (11, "RESV", "no_connect")]))
D.C("+1V8", GND, "100n", B)
D.C("+1V8", GND, "2u2", B, "0603", "10V")

# ===================================================================== NVMe
B = "NVME"
N = {n: "NC" for n in list(range(1, 59)) + list(range(67, 76))}
for n in (1, 3, 9, 15, 21, 27, 33, 39, 45, 51, 57, 71, 73, 75):
    N[n] = GND
for n in (2, 4, 12, 14, 16, 18, 70, 72, 74):
    N[n] = "+3V3"
N.update({41: "PCIE_RX_N", 43: "PCIE_RX_P", 47: "PCIE_TX_N", 49: "PCIE_TX_P", 50: "PCIE_RST_N", 52: "PCIE_CLKREQ_N",
          53: "PCIE_CLK_N", 54: "PCIE_WAKE_N", 55: "PCIE_CLK_P", "MP1": GND, "MP2": GND})
D.add("J11", "Connector:Bus_M.2_Socket_M", "M.2 Key M", "aviac:Bus_M.2_Socket_Key_M_TE_1-2199230-6", N, B,
      mpn="1-2199230-6", mfr="TE Connectivity", desc="M.2 Key-M socket, PCIe x1 (lane 0) to NVMe 2230", mass=0.9)
D.C("PCIE_TX_C_N", "PCIE_TX_N", "220n", B, "0402", "10V", "X5R")
D.C("PCIE_TX_C_P", "PCIE_TX_P", "220n", B, "0402", "10V", "X5R")
D.C("+3V3", GND, "22u", B, "0805", "10V", "X5R")
D.C("+3V3", GND, "22u", B, "0805", "10V", "X5R")
D.C("+3V3", GND, "100n", B)
D.R("+3V3", "PCIE_CLKREQ_N", "47k", B)
D.R("+3V3", "PCIE_WAKE_N", "47k", B)
D.add("H3", "Mechanical:MountingHole_Pad", "M2 SSD standoff 2230", "MountingHole:MountingHole_2.2mm_M2_DIN965_Pad", {1: GND}, B,
      mpn="9774025243R", mfr="Wurth Elektronik", desc="SMT spacer M2, 2.5 mm, SSD retention at 30 mm", mass=0.3)

# ====================================================================== USB
B = "USB"
D.add("J12", "Connector:USB_C_Receptacle_USB2.0_16P", "USB-C", "Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal",
      {"A1": GND, "A4": "USB_VBUS", "A5": "USB_CC1", "A6": "USB_CON_D_P", "A7": "USB_CON_D_N", "A8": "NC", "A9": "USB_VBUS", "A12": GND,
       "B1": GND, "B4": "USB_VBUS", "B5": "USB_CC2", "B6": "USB_CON_D_P", "B7": "USB_CON_D_N", "B8": "NC", "B9": "USB_VBUS", "B12": GND,
       "S1": GND}, B,
      mpn="USB4105-GF-A", mfr="GCT", desc="USB-C receptacle, USB 2.0, device mode for flashing and data", mass=0.7)
D.R("USB_CC1", GND, "5k1", B)
D.R("USB_CC2", GND, "5k1", B)
D.add("U11", "Power_Protection:USBLC6-2SC6", "USBLC6-2SC6", "Package_TO_SOT_SMD:SOT-23-6",
      {1: "USB_CON_D_N", 2: GND, 3: "USB_CON_D_P", 4: "USB_D_P", 5: "USB_VBUS", 6: "USB_D_N"}, B,
      mpn="USBLC6-2SC6", mfr="STMicroelectronics", desc="USB ESD protection", mass=0.015)
D.C("USB_VBUS", GND, "100n", B, "0603", "50V")
D.R("USB_VBUS", "USB_VBUS_DET", "100k", B)
D.R("USB_VBUS_DET", GND, "56k", B)      # 5 V -> 1.8 V for the Jetson GPIO

# ===================================================================== MISC
B = "MISC"
D.add("J13", "Connector_Generic_MountingPin:Conn_01x05_MountingPin", "DLS", "Connector_JST:JST_GH_SM05B-GHS-TB_1x05-1MP_P1.25mm_Horizontal",
      {1: "+1V8", 2: "DLS_SCL", 3: "DLS_SDA", 4: "DLS_INT", 5: GND, "MP": GND}, B,
      mpn="SM05B-GHS-TB", mfr="JST", desc="Downwelling light sensor port (I2C at 1.8 V, read by the sync MCU)", mass=0.28)
D.R("+1V8", "DLS_SCL", "2k2", B)
D.R("+1V8", "DLS_SDA", "2k2", B)
D.R("+1V8", "DLS_INT", "100k", B)
D.add("J14", "Connector_Generic:Conn_01x03", "DEBUG UART 1V8", "Connector_PinHeader_1.27mm:PinHeader_1x03_P1.27mm_Vertical",
      {1: "DBG_TX", 2: "DBG_RX", 3: GND}, B, mpn="(not fitted)", mfr="", desc="Jetson debug console, 1.8 V levels, pads only", dnp=True)
D.add("U12", "Memory_EEPROM:M24C02-FMN", "M24C02-F", "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
      {1: "+1V8", 2: "+1V8", 3: "+1V8", 4: GND, 5: "I2C_ID_SDA", 6: "I2C_ID_SCL", 7: GND, 8: "+1V8"}, B,
      mpn="M24C02-FMN6TP", mfr="STMicroelectronics", desc="Carrier ID EEPROM at 0x57 on I2C2", mass=0.07)
D.C("+1V8", GND, "100n", B)
for i, nm in enumerate(("H4", "H5", "H6", "H7")):
    D.add(nm, "Mechanical:MountingHole_Pad", "M2.5 board mount", "MountingHole:MountingHole_2.7mm_M2.5_Pad", {1: GND}, B,
          desc="Board mounting hole")

if __name__ == "__main__":
    nets = D.nets()
    print("parts", len(D.parts), "nets", len(nets))
    single = [n for n, v in nets.items() if len(v) == 1]
    print("single-pin nets:", single)
