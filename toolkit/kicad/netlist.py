"""Part / Design: a board described as parts with pin-to-net maps. Shared by every Aviac board."""
from collections import OrderedDict


class Part:
    def __init__(self, ref, sym, value, fp, pins, block, mpn="", mfr="", desc="", mass=0.0, dnp=False, custom=None):
        self.ref, self.sym, self.value, self.fp = ref, sym, value, fp
        self.pins = {str(k): v for k, v in pins.items()}
        self.block, self.mpn, self.mfr, self.desc, self.mass, self.dnp = block, mpn, mfr, desc, mass, dnp
        self.custom = custom          # custom symbol definition (see gen_sch.custom_symbol)


class Design:
    def __init__(self):
        self.parts = OrderedDict()
        self.count = {}
        self.blocks = OrderedDict()

    def block(self, key, title):
        self.blocks[key] = title

    def add(self, prefix_or_ref, *a, **k):
        ref = prefix_or_ref
        if not any(ch.isdigit() for ch in ref):
            self.count[ref] = self.count.get(ref, 0) + 1
            ref = f"{ref}{self.count[ref]}"
        assert ref not in self.parts, ref
        p = Part(ref, *a, **k)
        self.parts[ref] = p
        return p

    # ---- passives
    RFP = {"0402": "Resistor_SMD:R_0402_1005Metric", "0603": "Resistor_SMD:R_0603_1608Metric"}
    CFP = {"0402": "Capacitor_SMD:C_0402_1005Metric", "0603": "Capacitor_SMD:C_0603_1608Metric",
           "0805": "Capacitor_SMD:C_0805_2012Metric", "1210": "Capacitor_SMD:C_1210_3225Metric"}
    CM = {"0402": 0.002, "0603": 0.006, "0805": 0.016, "1210": 0.09}

    def R(self, a, b, value, block, pkg="0402", tol="1%", dnp=False):
        return self.add("R", "Device:R", value, self.RFP[pkg], {1: a, 2: b}, block,
                        mpn=f"RES {value} {tol} {pkg}", mfr="generic (Yageo RC / Vishay CRCW)", desc=f"Resistor {value} {tol} {pkg}",
                        mass=0.001, dnp=dnp)

    def C(self, a, b, value, block, pkg="0402", volt="16V", diel="X7R"):
        return self.add("C", "Device:C", value, self.CFP[pkg], {1: a, 2: b}, block,
                        mpn=f"CAP {value} {volt} {diel} {pkg}", mfr="generic (Murata GRM / Samsung CL)",
                        desc=f"Capacitor {value} {volt} {diel} {pkg}", mass=self.CM[pkg])

    def nets(self):
        n = OrderedDict()
        for p in self.parts.values():
            for pin, net in p.pins.items():
                if net and net != "NC":
                    n.setdefault(net, []).append((p.ref, pin))
        return n
