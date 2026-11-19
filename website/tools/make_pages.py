#!/usr/bin/env python3
"""Writes the solution pages (one per market) and the TH / SW product pages into website/src/ from the data below.
Run before build.py whenever the copy changes. Demo imagery comes from tools/scenes/*.py."""
import os

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SRC = os.path.join(REPO, "website", "src")


def pin(x, y, label, color):
    side = " lft" if x > 66 else ""
    return f'<span class="pin{side}" style="left:{x}%;top:{y}%"><i style="background:{color}"></i><b>{label}</b></span>'


def compare(left, right, ltag, rtag, pins, title, alt_l, alt_r, note):
    pins_html = "".join(pin(*p) for p in pins)
    return f"""<div class="sample reveal">
      <div style="display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap"><div class="lab">{title} · drag to compare</div><div class="tog"><button data-at="0">{ltag}</button><button data-at="1" class="on">{rtag}</button></div></div>
      <div class="cmpimg"><img src="{{{{R}}}}assets/img/demo/{left}.jpg" alt="{alt_l}" width="1600" height="1200"><div class="ndvi"><img src="{{{{R}}}}assets/img/demo/{right}.jpg" alt="{alt_r}" width="1600" height="1200"></div>
        <div class="handle" role="slider" aria-label="Compare {ltag} and {rtag}" aria-valuemin="0" aria-valuemax="100" aria-valuenow="50" tabindex="0"><span></span></div>
        <span class="tag l">{ltag}</span><span class="tag r">{rtag}</span>{pins_html}</div>
      <p class="note">{note}</p>
    </div>"""


SOL = [
    dict(key="crop", slug="crop-monitoring", name="Crop monitoring", lab="Agriculture · multispectral", cams=["MS"],
         h1="See crop stress <em>before it shows.</em>",
         lead="MS flies the field in six bands and flags stress in the red edge and near infrared days before it shows in colour. Scout the patch, not the whole farm.",
         hero="ms_titanium_hero_green.jpg", hero_alt="MS Agri Spectral camera",
         cmp=("field_rgb", "field_ndvi", "RGB", "NDVI", [(81.3, 33.0, "Stress · 0.21 ac", "#d7301f"), (33.7, 85.9, "Stress · 0.08 ac", "#d7301f")],
              "Same field, two views", "Aerial view of crop fields in colour", "The same fields as an NDVI map with two stressed patches"),
         side=("What the colour view misses", "Two patches, found early.",
               "In colour the stressed patches look like the rest of the field. In NDVI they are the first thing you see.",
               [("0.71", "Average NDVI"), ("0.29 ac", "Flagged for scouting"), ("6", "Bands per pixel"), ("On board", "Processed in flight")]),
         steps=[("Fly", "A fixed-wing or VTOL survey covers up to 1,000 acres in a flying day."), ("Capture", "Six bands fire together: colour, red edge and near infrared."),
                ("Process", "NDVI and red-edge indices are computed on board, on the Jetson."), ("Act", "Stressed zones land in the dashboard as scouting tasks with a map pin.")],
         cam=("MS", "Agri Spectral", "ms_titanium_hero_light.jpg", "product/multispectral/", "Sony IMX565 colour plus three Mira220 sensors for red edge and near infrared, fixed nadir under the wing."),
         spectrum=True),
    dict(key="spraying", slug="spraying", name="Spraying", lab="Spray drones · stereo", cams=["Duos"],
         h1="Know what every pass <em>actually covered.</em>",
         lead="Duos rides on a gimbal at the back of the spray drone, looking at what was just sprayed. Stereo depth measures canopy and boom height, and every pass is logged as coverage.",
         hero="duos_arctic_hero_green.jpg", hero_alt="Duos stereo camera",
         cmp=("field_rgb", "spray_coverage", "RGB", "COVERAGE", [(80.4, 34.6, "Missed strip · one boom width", "#f5761a"), (9.8, 74.5, "Overlap · double dose", "#1a4d9e")],
              "One farm, sprayed", "Aerial view of the farm in colour", "Spray coverage map: sprayed area, one missed strip and one overlap"),
         side=("What the coverage map shows", "Re-spray one strip, not the field.",
               "A skipped pass and an overlap are hard to see from the ground. The coverage map shows both, with the area and the plot.",
               [("97.6 %", "Covered"), ("0.4 ac", "Missed strip"), ("0.3 ac", "Overlap"), ("26 mm", "Stereo baseline")]),
         steps=[("Mount", "Duos sits on its gimbal yoke at the rear of the sprayer, facing aft at the boom."), ("Measure", "Stereo depth gives canopy height and boom height on every frame."),
                ("Map", "Each pass becomes a coverage strip on the field map."), ("Fix", "Missed strips and overlaps are flagged before the drone lands.")],
         cam=("Duos", "Stereo", "duos_arctic_hero_light.jpg", "product/duos/", "Two global-shutter Mira220 sensors on a 26 mm baseline in a 28 g head, on a two-axis gimbal."),
         film="duos_sprayer"),
    dict(key="solar", slug="solar", name="Solar inspection", lab="Solar · thermal", cams=["TH"],
         h1="Find the hot cell. <em>Close the repair.</em>",
         lead="TH flies the array with a 1 MP thermal module and a NIR module side by side. Hotspot candidates become reviewed findings, repair jobs and a report the site owner signs off.",
         hero="th_field_hero_green.jpg", hero_alt="Aviac TH thermal camera",
         cmp=("solar_rgb", "solar_thermal", "RGB", "THERMAL", [(29.7, 25.2, "Hotspot candidate · one cell", "#ffe680"), (61.6, 52.7, "Substring warm", "#f0a020"),
                                                              (81.2, 34.2, "Module warm", "#f0a020"), (47.8, 79.3, "Half a table warm", "#f0a020"), (56.2, 14.2, "Soiling", "#c8a080")],
              "One array, two views", "Solar array from above in colour", "The same array in thermal with hotspot candidates"),
         side=("What the thermal view shows", "Five candidates in one pass.",
               "A hot cell, a warm substring, a warm module, half a table running warm and a soiled row. Each one is a candidate until a qualified reviewer confirms it.",
               [("5", "Candidates flagged"), ("1 MP", "Thermal, plus NIR"), ("1", "Repair job per finding"), ("Versioned", "Customer reports")]),
         steps=[("Schedule", "Pick the site and the purpose; the job records the aircraft, sensor and conditions."), ("Fly", "TH captures thermal and NIR together, every frame time-stamped and geotagged."),
                ("Review", "Candidates are flagged; a qualified reviewer confirms or rejects each one."), ("Repair", "Confirmed findings become repair work orders with evidence."),
                ("Verify", "A post-repair flight checks the fix."), ("Report", "A versioned report goes to the site owner for acceptance.")],
         cam=("TH", "Thermal", "th_field_hero_light.jpg", "product/thermal/", "Two modules in one head: a 1 MP thermal core behind a germanium lens, and a Mira220 NIR camera seeing 400 to 940 nm."),
         workspace=True, demo=True),
    dict(key="industrial", slug="industrial", name="Industrial inspection", lab="Industrial · SWIR", cams=["SW"],
         h1="Moisture, leaks and haze: <em>seen in SWIR.</em>",
         lead="Water absorbs strongly in the short-wave infrared, so wet insulation, ponding and leaks read dark, and haze that hides a site in daylight mostly drops away. SW brings that to roofs, pipe racks and plants.",
         hero="sw_graphite_hero_green.jpg", hero_alt="Aviac SW SWIR camera",
         cmp=("swir_visible", "swir_swir", "VISIBLE", "SWIR", [(70.0, 43.3, "Ponding", "#3a6ea5"), (26.2, 38.3, "Wet insulation", "#3a6ea5"), (53.8, 89.0, "Pipe leak", "#3a6ea5")],
              "One roof, two views", "Industrial roof in hazy daylight", "The same roof in SWIR, showing moisture and a leak"),
         side=("What SWIR shows", "Water you cannot see in daylight.",
               "Moisture under the membrane, standing water and a leak from a pipe joint barely show in a hazy colour image. In SWIR they are dark and sharp.",
               [("0.9–1.7 µm", "InGaAs band"), ("640 × 512", "SWIR resolution"), ("3", "Findings"), ("Through haze", "Better contrast")]),
         steps=[("Plan", "Roofs, pipe racks, tanks and conveyors on a repeatable route."), ("Fly", "SW captures in SWIR, on a gimbal for oblique views."),
                ("Find", "Moisture, leaks and hidden damage stand out against dry material."), ("Track", "Findings go to the dashboard with location, evidence and a repair status.")],
         cam=("SW", "SWIR", "sw_graphite_hero_light.jpg", "product/swir/", "An InGaAs SWIR sensor behind a SWIR-coated 25 mm lens."),
         demo=True),
    dict(key="construction", slug="construction", name="Construction monitoring", lab="Real estate · construction", cams=["MS", "Duos"],
         h1="Every week of the build, <em>on one map.</em>",
         lead="Fly the same route every week. The colour map and stereo surface show what was built, what moved and how much material is left, for owners, lenders and site teams.",
         hero="demo/site_hr_w11.jpg", hero_alt="A high-rise under construction seen from a drone",
         cmp=("site_hr_w3", "site_hr_w11", "WEEK 3", "WEEK 11", [(48.8, 28.5, "Level 14 deck: formwork", "#2f6f4e"), (56.6, 24.6, "Rebar placed", "#2f6f4e"),
                                                           (55.9, 47.2, "Façade to level 8", "#2f6f4e"), (40.8, 21.3, "Crane climbed", "#2f6f4e"), (36.6, 58.8, "Stockpile down", "#2f6f4e")],
              "One tower, two dates", "A tower under construction at week 3: five floors of frame", "The same tower at week 11: fourteen floors, glazed to level 8"),
         side=("What changed in eight weeks", "Nine floors, measured.",
               "Slide between the two dates: the frame went from five floors to fourteen, glazing reached level 8, the crane climbed and the stockpile shrank. Every change is measured from the same drone position.",
               [("+9", "Floors of frame"), ("+6", "Floors glazed"), ("8 weeks", "Between flights"), ("Weekly", "Same route")]),
         steps=[("Fly", "The same route and height every week, so maps line up."), ("Map", "A colour orthomosaic and a stereo surface for every flight."),
                ("Compare", "Dates side by side, with areas and volumes measured."), ("Share", "A progress report for owners, lenders and the site team.")],
         cam=("MS + Duos", "Map and depth", "ms_titanium_hero_light.jpg", "product/multispectral/", "The MS colour camera maps the site at high resolution; Duos adds close-range depth for volumes."),
         ),
]

TEMPLATE = """{{{{HEAD {name} · Aviac Technologies}}}}
<body>
{{{{NAV {key}}}}}

<main id="main">
<header class="phero"><div class="wrap"><div class="grid">
  <div class="reveal">
    <div class="lab g">{lab}{demo_tag}</div>
    <h1 style="margin:14px 0 16px;font-size:clamp(42px,5.2vw,72px)">{h1}</h1>
    <p style="font-size:18px;max-width:540px">{lead}</p>
    <div class="ctas" style="margin-top:22px"><a class="btn p" href="#demo">See the demo <span class="a">&darr;</span></a> <a class="btn" href="{{{{R}}}}#contact">Request a pilot</a></div>
  </div>
  <div class="pic reveal" style="border-radius:var(--r-lg);overflow:hidden"><img src="{{{{R}}}}assets/img/{hero}" alt="{hero_alt}" style="width:100%;display:block"></div>
</div></div></header>

<section id="demo" style="padding-top:30px"><div class="wrap">
  <div class="dgrid">
    {compare}
    <div class="sample reveal" style="justify-content:space-between">
      <div><div class="lab">{s0}</div><h3 style="font-size:28px;margin:10px 0 8px">{s1}</h3><p style="margin:0">{s2}</p></div>
      <div class="stats">{stats}</div>
    </div>
  </div>
</div></section>

<section id="fly" style="padding-top:30px"><div class="wrap">
  <div class="head reveal"><h2>Watch it fly.</h2><p>{fly_text}</p></div>
  <div class="fly reveal" data-scene="{key}"></div>
  <p class="note" style="margin-top:10px">Live simulation. Drag to look around; change the height to see the ground detail and swath change. Time runs faster than real flight.</p>
</div></section>
{extra}
<section><div class="wrap">
  <div class="head reveal"><h2>How it works.</h2><p>{how}</p></div>
  <div class="steps reveal">{steps}</div>
</div></section>

<section style="padding-top:10px"><div class="wrap">
  <a class="cambox reveal" href="{{{{R}}}}{cam_href}" style="text-decoration:none;color:inherit"><img src="{{{{R}}}}assets/img/t/{cam_img}" loading="lazy" alt="{cam_name}">
    <div class="body"><div class="lab g">The camera</div><h3 style="font-size:40px;margin:10px 0 8px">{cam_name} <span style="color:var(--mute);font-size:.55em">{cam_sub}</span>{demo_tag}</h3><p>{cam_text}</p><span class="go" style="color:var(--forest);font-weight:500">See the camera <span class="a">&rarr;</span></span></div></a>
</div></section>

<section id="contact-cta" style="background:var(--bg-2)"><div class="wrap" style="display:flex;justify-content:space-between;align-items:center;gap:24px;flex-wrap:wrap">
  <div class="reveal"><div class="lab">Pilots</div><h2 style="font-size:clamp(32px,4vw,52px);margin:12px 0 0">Try it on your {pilot_word}.</h2></div>
  <a class="btn p reveal" href="{{{{R}}}}#contact">Request a pilot <span class="a">&rarr;</span></a>
</div></section>

</main>
{{{{FOOT}}}}
<script type="module" src="{{{{R}}}}flight.js" data-root="{{{{R}}}}"></script>
<script src="{{{{R}}}}assets/site.js"></script>
</body>
</html>
"""

FLY = {"crop": "MS rides fixed and nadir under the Aviac VTOL and flies a lawnmower survey. The NDVI map builds behind the footprint, and stressed zones are pinned as they pass under the camera.",
       "spraying": "Duos rides at the back of the sprayer, looking aft at the spray that just landed. The coverage map builds lane by lane and flags the missed strip and the overlap.",
       "solar": "TH flies the rows at 30 m with thermal and colour side by side. Hotspot candidates are pinned as the footprint passes over them, ready for review.",
       "industrial": "SW scans the roof in short-wave infrared. Ponding, wet insulation and a pipe leak appear in the SWIR layer as it builds.",
       "construction": "MS maps the site on the same route as every week. This week's map is laid over week 3, and every change is pinned."}

PILOT = {"crop": "farm", "spraying": "farm", "solar": "site", "industrial": "plant", "construction": "project"}

for d in SOL:
    l, r, lt, rt, pins, title, al, ar = d["cmp"]
    note = "Illustrative imagery generated for this demo, not a capture."
    if d["key"] == "solar":
        note = "Illustrative imagery. Thermal colours here are relative, not radiometric temperatures; findings are candidates until reviewed."
    cmp = compare(l, r, lt, rt, pins, title, al, ar, note)
    s0, s1, s2, st = d["side"]
    stats = "".join(f"<div><b>{a}</b><span>{b}</span></div>" for a, b in st)
    steps = "".join(f'<div class="step"><b>{a}</b><p>{b}</p></div>' for a, b in d["steps"])
    extra = ""
    if d.get("spectrum"):
        extra = """
<section style="padding-top:20px"><div class="wrap">
  <div class="bands">
    <div class="reveal">
      <div class="lab">Why six bands</div>
      <h2 style="font-size:clamp(32px,4vw,52px);margin:14px 0 18px">A stressed crop looks healthy until it is too late.</h2>
      <div class="pts">
        <div><b>Stress starts in the red edge.</b><p>Chlorophyll loss shifts reflectance between 700 and 740 nm days before leaves change colour.</p></div>
        <div><b>Healthy leaves glow in near infrared.</b><p>Leaf structure reflects strongly at 800 to 900 nm. Damage, disease and water stress pull it down.</p></div>
        <div><b>An RGB camera sees none of it.</b><p>By the time it shows in colour, the yield is already lost.</p></div>
      </div>
    </div>
    <div class="spec reveal">
      <div class="lab" style="margin-bottom:10px">Leaf reflectance · <span style="color:#16683a">healthy</span> · <span style="color:#c4862f">stressed</span></div>
      <canvas data-spectrum aria-label="Reflectance of a healthy and a stressed leaf from 400 to 950 nm, with the six MS bands marked"></canvas>
      <div class="legend"><span>Wavelength, nm</span><span>Shaded: MS bands</span></div>
    </div>
  </div>
</div></section>
"""
    if d.get("film"):
        extra = f"""
<section style="padding-top:20px"><div class="wrap">
  <div class="cambox reveal"><video data-src="{{{{R}}}}assets/film/{d['film']}.mp4" data-sm="{{{{R}}}}assets/film/{d['film']}_sm.mp4" poster="{{{{R}}}}assets/film/{d['film']}.jpg" muted loop playsinline preload="none" style="width:100%;height:100%;object-fit:cover;aspect-ratio:16/9;display:block" aria-label="Duos on its gimbal at the rear of a spray drone"></video>
    <div class="body"><div class="lab g">On the aircraft</div><h3 style="font-size:34px;margin:10px 0 8px">At the back, facing aft.</h3><p>Mounted behind the boom, Duos sees the spray that just landed, not the crop ahead. The gimbal holds the stereo pair level while the sprayer pitches.</p></div></div>
</div></section>
"""
    if d.get("workspace"):
        extra = """
<section style="padding-top:20px"><div class="wrap">
  <div class="head reveal"><h2>From inspection to customer acceptance.</h2><p>A service workspace for solar installers and O&amp;M teams is in development (working name: Solar Service Hub). Drone evidence is one input; reviewed findings drive the repair work.</p></div>
  <div class="steps reveal">
    <div class="step"><b>Service</b><p>Sites, installed equipment and assigned jobs in one place.</p></div>
    <div class="step"><b>Evidence</b><p>Technician checklists, photos and thermal images, with provenance kept.</p></div>
    <div class="step"><b>Findings</b><p>Open, triaged, planned, resolved, verified. Rejections need a reason.</p></div>
    <div class="step"><b>Delivery</b><p>Versioned reports the customer accepts or sends back with comments.</p></div>
  </div>
  <p class="note" style="margin-top:14px">In development with pilot partners. No automated diagnosis: thermal thresholds and electrical findings need qualified review.</p>
</div></section>
"""
    how = {"crop": "From flight to a scouting task in four steps.", "spraying": "The camera rides with the sprayer; the map is ready when it lands.",
           "solar": "One connected service cycle, from the flight to a signed-off report.", "industrial": "A repeatable route turns into a list of findings.",
           "construction": "The same flight every week becomes a record of the build."}[d["key"]]
    c = d["cam"]
    demo_tag = '<span class="demo-tag">DEMO</span>' if d.get("demo") else ""
    html = TEMPLATE.format(name=d["name"], key=d["key"], lab=d["lab"], demo_tag=demo_tag, h1=d["h1"], lead=d["lead"], hero=d["hero"], hero_alt=d["hero_alt"],
                           compare=cmp, fly_text=FLY[d['key']], s0=s0, s1=s1, s2=s2, stats=stats, extra=extra, how=how, steps=steps, cam_href=c[3], cam_img=c[2], cam_name=c[0],
                           cam_sub=c[1], cam_text=c[4], pilot_word=PILOT[d["key"]])
    out = os.path.join(SRC, "solutions", d["slug"]); os.makedirs(out, exist_ok=True)
    open(os.path.join(out, "index.html"), "w").write(html)
    print("solutions/" + d["slug"])

# ---------------- TH and SW product pages (same layout as Duos)
PROD = [
    dict(key="th", slug="thermal", cam="th", name="TH", sub="Thermal + NIR", lab="Thermal · solar and electrical inspection", finish="field",
         lead="Two modules behind one faceplate: a Mira220 NIR camera seeing 400 to 940 nm through a large clear lens, and a 1 MP thermal core behind a germanium lens below it. Built for solar arrays, substations and electrical rooms.",
         specs=[("Thermal", "1280 × 1024 (1 MP), 12 µm, uncooled"), ("Thermal lens", "13 mm f/1.0 germanium, 8–14 µm"), ("NIR", "Mira220, 1600 × 1400, global shutter"),
                ("NIR band", "400–940 nm, one lens, one filter"), ("Weight", "132 g"), ("Ports", "PoE GigE (M12), USB-C, microSD")],
         cards=[("Optics", "Two lenses, two bands", "A germanium lens for long-wave infrared (the green glint is its coating), and an M12 lens with a 400–940 nm filter for the Mira220. Both are focused and locked for flight.",
                 [("NIR", "8 mm f/1.8, 400–940 nm filter"), ("Thermal", "13 mm f/1.0, germanium"), ("Focus", "locked")]),
                ("Baseboard + image sensors", "Two sensing modules", "The thermal module is a sealed 1 MP VOx core with its own lens mount and germanium window. The NIR module is a Mira220 board: global shutter and enhanced near-infrared sensitivity, so one channel covers visible through 940 nm.",
                 [("Thermal", "1280 × 1024 VOx, 12 µm"), ("NIR", "Mira220, 1600 × 1400"), ("Bands", "8–14 µm · 400–940 nm")]),
                ("Processing board", "Two bands, one frame", "Triggers both modules together, turns thermal counts into temperatures, registers the NIR frame onto the thermal one, and streams both over Ethernet with flight time and position.",
                 [("Sync", "one trigger, both modules"), ("Ports", "PoE GigE (M12) · USB-C · microSD")]),
                ("Externals", "Housing and heat sink", "A field-sage housing with one dark faceplate, fixed from inside so no screws show: both lenses sit flush behind polished bezels, with a label plate by the thermal lens. A black finned aluminium shell behind sheds the core's heat.",
                 [("Faceplate", "aluminium, fixed from inside"), ("Rear", "aluminium, finned"), ("Connector", "M12")])],
         end="Heat and NIR, in one pass.", swatches=[("field", "#5f6b58")], teardown=True,
         gal=("th_field_hero_light.jpg", "th_field_hero_green.jpg"), solution="solutions/solar/",
         gal_head=("Two modules, one head.", "Thermal finds the hot cell; the NIR frame shows exactly which module it is on.")),
    dict(key="sw", slug="swir", cam="sw", name="SW", sub="SWIR", lab="SWIR · industrial inspection", finish="graphite",
         lead="A machine-vision box camera: an InGaAs short-wave infrared sensor behind a C-mount lens, focus and iris set and locked at the factory for flight. Moisture, leaks and haze, on roofs, pipe racks and plants.",
         specs=[("Sensor", "InGaAs, 640 × 512, 5 µm (placeholder)"), ("Band", "about 0.9 to 1.7 µm"), ("Lens", "C-mount, 25 mm f/1.4, fixed focus"),
                ("Body", "54 × 54 × 60 mm"), ("Weight", "145 g"), ("Ports", "PoE GigE (M12), USB-C, microSD")],
         cards=[("Optics", "SWIR lens", "A 25 mm f/1.4 C-mount lens with a SWIR anti-reflection coating, focused and locked at the factory: nothing to knock loose in flight.", [("Lens", "25 mm f/1.4"), ("Coating", "0.9–1.7 µm")]),
                ("Baseboard + image sensors", "InGaAs sensor", "An InGaAs sensor in a ceramic package, with a heat spreader behind it for its cooler.", [("Sensor", "InGaAs, 640 × 512"), ("Pixel", "5 µm")]),
                ("Processing board", "SWIR pipeline", "An FPGA board corrects pixel non-uniformity, syncs capture and sends the stream out over USB-C or Ethernet.", [("Output", "USB-C or Ethernet")]),
                ("Externals", "Sealed head", "A graphite box body with a black anodised front plate and rear rim, the Aviac mark on both sides, and at the back PoE GigE on an M12, a locking USB-C and a microSD slot.", [("Shell", "PA12-CF"), ("Seal", "silicone gasket")])],
                
         end="Locked, sealed, ready.", gal_head=("Sealed for flight.", "A fixed-focus C-mount lens on a sealed box body: nothing to knock out of focus."), swatches=[("graphite", "#2b2d31")], gal=("sw_graphite_hero_light.jpg", "sw_graphite_hero_green.jpg"), solution="solutions/industrial/"),
]

PORTS_HTML = {'th': '<section id="ports"><div class="wrap"><div class="ports reveal"><div class="pimg"><img src="{{R}}assets/img/th_rear.jpg" alt="The back of the TH camera: its connectors" loading="lazy" width="1600" height="1000"></div><div class="pbody"><div class="lab g">At the back</div><h2>One rugged cable to the drone.</h2><p>Power and both streams on one M12, with setup and a backup recorder beside it.</p><ul class="plist"><li><b>M12 X-coded · PoE GigE</b><span><em>Power and data</em>power and both the thermal and NIR streams on one locking cable to the gimbal</span></li><li><b>USB-C</b><span><em>Setup</em>locking; configure palettes, sync and alarms on the bench</span></li><li><b>microSD</b><span><em>Backup recording</em>keeps radiometric frames on board if the link drops</span></li></ul></div></div></div></section>\n\n', 'sw': '<section id="ports"><div class="wrap"><div class="ports reveal"><div class="pimg"><img src="{{R}}assets/img/sw_rear.jpg" alt="The back of the SW camera: its connectors" loading="lazy" width="1600" height="1000"></div><div class="pbody"><div class="lab g">At the back</div><h2>One rugged cable to the drone.</h2><p>Power and data on one M12, with setup and a backup recorder beside it.</p><ul class="plist"><li><b>M12 X-coded · PoE GigE</b><span><em>Power and data</em>power and the SWIR stream on one locking cable to the gimbal or airframe</span></li><li><b>USB-C</b><span><em>Setup</em>locking; set exposure and correction on the bench</span></li><li><b>microSD</b><span><em>Backup recording</em>keeps frames on board if the link drops</span></li></ul></div></div></div></section>\n\n'}

for d in PROD:
    specs = "".join(f"<div><span>{a}</span><b>{b}</b></div>" for a, b in d["specs"])
    n = len(d["cards"])
    cards = ""
    for i, (g, h, p, li) in enumerate(d["cards"]):
        lis = "".join(f"<li><span>{a}</span><b>{b}</b></li>" for a, b in li)
        view = ["0.55,0.25,6.5", "0.5,0.22,3.6", "1.0,0.3,6.5", "1.2,0.3,7.0", "1.1,0.3,7.5"][i]
        cards += f'    <article class="card" data-group="{g}" data-view="{view}"><div class="n">{i + 1} / {n} · {g.upper()}</div><h3>{h}</h3><p>{p}</p>\n      <ul>{lis}</ul></article>\n'
    dots = "<i></i>" * (n + 2)
    teardown = "" if not d.get("teardown") else f"""
<section class="td" id="teardown" aria-label="Teardown" style="height:420vh"><div class="pin">
  <div class="viewer" id="{d['cam']}-td" data-src="{{{{R}}}}models/{d['cam']}/" data-finish="{d['finish']}" data-follow="{d['cam']}-hero" data-dist="3.4" aria-hidden="true"></div>
  <div class="wrap top"><h2>Inside the {d['name']}</h2><div class="prog">{dots}<span>1 / {n + 2}</span></div></div>
  <div class="track">
    <article class="card on" data-view="0.9,0.22,4.6"><div class="n">TEARDOWN</div><h3>Four layers, one core.</h3><p>Scroll to take it apart. Core choice is a placeholder until a supplier is picked.</p></article>
{cards}    <article class="card end" data-view="0.6,0.2,4.4"><div class="n" style="color:#cfe6d6">ASSEMBLED</div><h3>{d['end']}</h3><p>See what it finds on a solar farm.</p><a class="btn" href="{{{{R}}}}{d['solution']}">See it fly <span class="a">&rarr;</span></a></article>
  </div>
</div></section>
"""
    html = f"""{{{{HEAD {d['name']} {d['sub']} · Aviac Technologies}}}}
<body>
{{{{NAV {d['key']}}}}}

<main id="main">
<header class="phero"><div class="wrap"><div class="grid">
  <div class="reveal">
    <div class="lab g">{d['lab']}<span class="demo-tag">DEMO</span></div>
    <h1 style="margin:14px 0 16px">{d['name']} <span style="color:var(--mute);font-size:.45em;letter-spacing:0">{d['sub']}</span></h1>
    <p style="font-size:18px;max-width:520px">{d['lead']}</p>
    <div class="pspecs">{specs}</div>
    {'<a class="btn p" href="#teardown">See inside <span class="a">&darr;</span></a> <a class="btn" href="{{R}}' + d['solution'] + '">See it fly</a>' if d.get('teardown') else '<a class="btn p" href="{{R}}' + d['solution'] + '">See it fly <span class="a">&rarr;</span></a> <a class="btn" href="{{R}}#contact">Request a pilot</a>'}
  </div>
  <div class="stage3d reveal">
    <div class="viewer" id="{d['cam']}-hero" data-src="{{{{R}}}}models/{d['cam']}/" data-finish="{d['finish']}" data-spin="1" data-zoom="1" data-dist="4.4" role="img" aria-label="{d['name']}, interactive 3D model. Drag to turn."></div>
    <span class="chip drag">Drag to turn</span>
    {'' if len(d["swatches"]) < 2 else '<div class="swatches" data-for="#' + d['cam'] + '-hero">' + ''.join(f'<button{" class=on" if f == d["finish"] else ""} data-finish="{f}" title="{f.title()}" style="background:{c}" aria-label="{f.title()}"></button>' for f, c in d["swatches"]) + '<span>' + d['finish'].title() + '</span></div>'}
  </div>
</div></div></header>
{teardown}
{PORTS_HTML.get(d['cam'], '')}<section><div class="wrap">
  <div class="head reveal"><h2>{d.get('gal_head', ('Same family, new band.', ''))[0]}</h2><p>{d.get('gal_head', ('', 'Every lens is fixed and sealed for flight.'))[1]}</p></div>
  <div class="gallery reveal"><img src="{{{{R}}}}assets/img/{d['gal'][1]}" alt="{d['name']} camera"><div class="col"><img src="{{{{R}}}}assets/img/{d['gal'][0]}" alt="{d['name']} camera"></div></div>
</div></section>

</main>
{{{{FOOT}}}}
<script type="module" src="{{{{R}}}}viewer.js"></script>
<script src="{{{{R}}}}assets/site.js"></script>
</body>
</html>
"""
    out = os.path.join(SRC, "product", d["slug"]); os.makedirs(out, exist_ok=True)
    open(os.path.join(out, "index.html"), "w").write(html)
    print("product/" + d["slug"])
