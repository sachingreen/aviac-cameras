// The farm under the camera, showcase edition: a patchwork of fields, farm tracks and tree lines that runs out to
// the horizon, with problem patches hidden in the crop. When a patch passes through the camera's footprint it is
// "detected": a ring lights up on the ground, a beam rises from it, and a tag and a log entry appear in the HUD.
// The detections are a demonstration of what the six bands make visible, not output from a trained model.
import * as THREE from 'three';

export const CLASSES = [
  {key: 'veg', name: 'Poor vegetation', short: 'POOR VEGETATION', color: '#ffb020', note: 'low NDVI, thin canopy'},
  {key: 'loss', name: 'Crop loss', short: 'CROP LOSS', color: '#ff4a3a', note: 'bare soil, lodged crop'},
  {key: 'pest', name: 'Pest identified', short: 'PEST IDENTIFIED', color: '#ff3aa8', note: 'feeding damage, red edge drop'},
  {key: 'nut', name: 'Nutrient deficiency', short: 'NUTRIENT DEFICIENCY', color: '#b8ff3a', note: 'chlorosis, nitrogen low'},
];

const TILE = 3200;                     // metres covered by one repeat: about 2,500 acres of broad-acre farmland
const PX = 2048;
const Y0 = TILE / 2;                   // the flight line runs along the middle of the tile

// small deterministic random
let seed = 7;
const rnd = () => ((seed = (seed * 16807) % 2147483647) / 2147483647);

function paintFarm() {
  const c = document.createElement('canvas');
  c.width = c.height = PX;
  const g = c.getContext('2d');
  const m2p = PX / TILE;
  // base: dark earth
  g.fillStyle = '#3b3326';
  g.fillRect(0, 0, PX, PX);
  // fields: a jittered grid of plots, each with its own crop, row direction and tramlines
  const CROPS = [
    {c: [58, 112, 46], row: [40, 86, 34]},       // maize, lush
    {c: [86, 128, 52], row: [64, 104, 40]},      // soybean
    {c: [138, 146, 64], row: [112, 122, 50]},    // wheat, turning
    {c: [176, 156, 82], row: [150, 130, 66]},    // ripe wheat
    {c: [70, 98, 44], row: [52, 80, 34]},        // potato
    {c: [104, 84, 60], row: [84, 68, 48]},       // ploughed
  ];
  const cols = [0, 420, 940, 1280, 1800, 2220, 2660, TILE];
  const rows = [0, 360, 840, 1280, 1920, 2360, 2800, TILE];
  for (let a = 0; a < cols.length - 1; a++) {
    for (let b = 0; b < rows.length - 1; b++) {
      const x0 = cols[a] * m2p, x1 = cols[a + 1] * m2p, y0 = rows[b] * m2p, y1 = rows[b + 1] * m2p;
      // the plots the flight line crosses are crops, not bare ground
      const onLine = rows[b] < Y0 + 120 && rows[b + 1] > Y0 - 120;
      const crop = CROPS[onLine ? Math.floor(rnd() * 5) : Math.floor(rnd() * CROPS.length)];
      g.fillStyle = `rgb(${crop.c.join(',')})`;
      g.fillRect(x0, y0, x1 - x0, y1 - y0);
      // rows
      const vert = rnd() < 0.5;
      g.strokeStyle = `rgba(${crop.row.join(',')},0.55)`;
      g.lineWidth = 1;
      g.beginPath();
      if (vert) for (let x = x0 + 1; x < x1; x += 2) { g.moveTo(x, y0); g.lineTo(x, y1); }
      else for (let y = y0 + 1; y < y1; y += 2) { g.moveTo(x0, y); g.lineTo(x1, y); }
      g.stroke();
      // tramlines every 24 m
      g.strokeStyle = 'rgba(70,58,40,0.55)';
      g.lineWidth = 1.2;
      g.beginPath();
      if (vert) for (let x = x0 + 12 * m2p; x < x1; x += 24 * m2p) { g.moveTo(x, y0); g.lineTo(x, y1); }
      else for (let y = y0 + 12 * m2p; y < y1; y += 24 * m2p) { g.moveTo(x0, y); g.lineTo(x1, y); }
      g.stroke();
    }
  }
  // soft vigour variation over everything
  for (let k = 0; k < 900; k++) {
    const x = rnd() * PX, y = rnd() * PX, r = (40 + rnd() * 180) * m2p;
    const gr = g.createRadialGradient(x, y, 0, x, y, r);
    const light = rnd() < 0.5;
    gr.addColorStop(0, light ? 'rgba(170,190,90,0.10)' : 'rgba(20,40,16,0.12)');
    gr.addColorStop(1, 'rgba(0,0,0,0)');
    g.fillStyle = gr;
    g.fillRect(x - r, y - r, 2 * r, 2 * r);
  }
  // farm tracks between the plots, and hedgerows along some of them
  g.lineCap = 'round';
  for (const x of cols.slice(1, -1)) {
    g.strokeStyle = '#8a7a5c'; g.lineWidth = 4 * m2p; g.beginPath(); g.moveTo(x * m2p, 0); g.lineTo(x * m2p, PX); g.stroke();
  }
  for (const y of rows.slice(1, -1)) {
    g.strokeStyle = '#8a7a5c'; g.lineWidth = 4 * m2p; g.beginPath(); g.moveTo(0, y * m2p); g.lineTo(PX, y * m2p); g.stroke();
  }
  const tree = (x, y, r) => {
    const gr = g.createRadialGradient(x, y, 0, x, y, r);
    gr.addColorStop(0, 'rgba(22,44,20,0.95)'); gr.addColorStop(0.7, 'rgba(18,36,16,0.85)'); gr.addColorStop(1, 'rgba(10,20,10,0)');
    g.fillStyle = gr; g.beginPath(); g.arc(x, y, r, 0, Math.PI * 2); g.fill();
  };
  for (const x of [cols[2], cols[5]]) for (let y = 0; y < TILE; y += 9 + rnd() * 8) tree((x + 5) * m2p, y * m2p, (4 + rnd() * 3) * m2p);
  for (const y of [rows[1], rows[5]]) for (let x = 0; x < TILE; x += 9 + rnd() * 8) tree(x * m2p, (y + 5) * m2p, (4 + rnd() * 3) * m2p);
  // a farmyard: a few roofs and a pond, off the flight line
  const yard = (x, y) => {
    g.fillStyle = '#6d6a64'; g.fillRect((x - 30) * m2p, (y - 25) * m2p, 60 * m2p, 50 * m2p);
    g.fillStyle = '#9a3b2c'; g.fillRect((x - 22) * m2p, (y - 18) * m2p, 26 * m2p, 12 * m2p);
    g.fillStyle = '#a7a9ad'; g.fillRect((x + 6) * m2p, (y - 18) * m2p, 16 * m2p, 30 * m2p);
    g.fillStyle = '#7d4a30'; g.fillRect((x - 22) * m2p, (y + 2) * m2p, 22 * m2p, 12 * m2p);
    g.fillStyle = '#1e3b4a'; g.beginPath(); g.ellipse((x + 50) * m2p, (y + 30) * m2p, 22 * m2p, 14 * m2p, 0.4, 0, Math.PI * 2); g.fill();
  };
  yard(660, 520); yard(2480, 2560); yard(1500, 2900);
  return {canvas: c, g, m2p};
}

/** Problem patches painted into the crop. tx, ty: metres in the texture tile; r: radius in metres. */
function paintPatches(g, m2p) {
  const list = [];
  const base = ['pest', 'veg', 'nut', 'loss', 'veg', 'pest', 'nut', 'loss', 'nut', 'veg', 'pest', 'loss', 'veg', 'nut'];
  const kinds = [...base, ...base];
  kinds.forEach((key, i) => {
    const tx = 60 + i * (TILE - 120) / kinds.length + rnd() * 40;
    const ty = Y0 + (rnd() - 0.5) * 130;          // most lie inside the 85 m swath, a few outside it
    const r = key === 'pest' ? 14 + rnd() * 10 : key === 'loss' ? 18 + rnd() * 14 : 24 + rnd() * 26;     // broad-acre scale
    list.push({key, tx, ty, r, conf: 0.86 + rnd() * 0.12});
    const x = tx * m2p, y = (TILE - ty) * m2p, R = r * m2p;
    const blob = (cx, cy, rr, col, a) => {
      const gr = g.createRadialGradient(cx, cy, 0, cx, cy, rr);
      gr.addColorStop(0, `rgba(${col},${a})`); gr.addColorStop(0.65, `rgba(${col},${a * 0.7})`); gr.addColorStop(1, `rgba(${col},0)`);
      g.fillStyle = gr; g.beginPath(); g.arc(cx, cy, rr, 0, Math.PI * 2); g.fill();
    };
    if (key === 'loss') { blob(x, y, R, '104,78,52', 0.95); for (let k = 0; k < 6; k++) blob(x + (rnd() - 0.5) * R, y + (rnd() - 0.5) * R, R * 0.4, '120,92,60', 0.8); }
    if (key === 'veg') { blob(x, y, R, '150,150,96', 0.75); for (let k = 0; k < 5; k++) blob(x + (rnd() - 0.5) * R, y + (rnd() - 0.5) * R, R * 0.35, '130,112,70', 0.6); }
    if (key === 'nut') blob(x, y, R, '214,208,72', 0.7);
    if (key === 'pest') for (let k = 0; k < 26; k++) blob(x + (rnd() - 0.5) * 2 * R, y + (rnd() - 0.5) * 2 * R, R * (0.12 + rnd() * 0.15), '78,58,36', 0.9);
  });
  return list;
}


// ---------------------------------------------------------------- things people built: power lines, farmyards
// Built in metres for one texture tile (x along the flight line, z = -(v - Y0)); three copies cover the view.
function buildProps(paint) {
  const g = new THREE.Group();
  const M = (c, o = {}) => new THREE.MeshStandardMaterial({color: new THREE.Color(c), roughness: 0.8, metalness: 0.05, envMapIntensity: 0.4, ...o});
  const wood = M('#5a4634'), barnRed = M('#8e3426'), roofGrey = M('#7d8790', {metalness: 0.5, roughness: 0.45}), wall = M('#c9c3b6'),
    silo = M('#b8bec4', {metalness: 0.7, roughness: 0.35}), darkRoof = M('#3a3d42'), tank = M('#e6e8ea', {metalness: 0.3});
  const at = (mesh, x, v, y = 0, ry = 0) => { mesh.position.set(x, y, -(v - Y0)); mesh.rotation.y = ry; g.add(mesh); return mesh; };
  // power lines: two lines of poles across the flight path along farm tracks, wires between them
  const poleG = new THREE.CylinderGeometry(0.5, 0.7, 13, 6).translate(0, 6.5, 0);
  const armG = new THREE.BoxGeometry(4.2, 0.6, 0.6).translate(0, 12.2, 0);
  const wires = [];
  for (const x of [520, 1288, 2228]) {
    let prev = null;
    for (let v = 20; v < TILE; v += 55) {
      const pole = new THREE.Mesh(poleG, wood), arm = new THREE.Mesh(armG, wood);
      at(pole, x, v); at(arm, x, v);
      const z = -(v - Y0);
      if (prev !== null) for (const dx of [-1.4, 0, 1.4]) {
        // a little sag: three segments per span
        const a = [x + 0, 12.5, prev], b = [x + 0, 12.5, z];
        const mid = (k) => [x, 12.5 - 1.4 * Math.sin(Math.PI * k), prev + (z - prev) * k];
        const pts = [a, mid(1 / 3), mid(2 / 3), b];
        for (let i = 0; i < 3; i++) wires.push(pts[i][0] + 0 * dx, pts[i][1], pts[i][2], pts[i + 1][0], pts[i + 1][1], pts[i + 1][2]);
        // offset the three conductors across the crossarm (crossarm runs along z, so offset in x is the wire spacing)
        for (let i = wires.length - 18; i < wires.length; i += 3) wires[i] += dx;
      }
      prev = z;
      paint.fillStyle = 'rgba(40,32,24,0.6)';
      paint.fillRect(x * paint.m2p - 1, (TILE - v) * paint.m2p - 1, 3, 3);
    }
  }
  const wireL = new THREE.LineSegments(new THREE.BufferGeometry().setAttribute('position', new THREE.Float32BufferAttribute(wires, 3)),
    new THREE.LineBasicMaterial({color: '#1c1f22', transparent: true, opacity: 0.8}));
  g.add(wireL);
  // farmyards near the flight line: barn, machine shed, two silos, a house, a water tank, on a gravel pad
  const gable = (w, l, h) => {
    const sh = new THREE.Shape();
    sh.moveTo(-w / 2, 0); sh.lineTo(w / 2, 0); sh.lineTo(0, h); sh.closePath();
    return new THREE.ExtrudeGeometry(sh, {depth: l, bevelEnabled: false}).translate(0, 0, -l / 2);
  };
  const yard = (x, v, ry) => {
    const grp = new THREE.Group();
    const put = (m, px, pz, py = 0) => { m.position.set(px, py, pz); grp.add(m); };
    put(new THREE.Mesh(new THREE.BoxGeometry(14, 7, 26).translate(0, 3.5, 0), barnRed), -18, 0);
    put(new THREE.Mesh(gable(15, 27, 5), darkRoof), -18, 0, 7);
    put(new THREE.Mesh(new THREE.BoxGeometry(18, 6, 34).translate(0, 3, 0), wall), 6, -4);
    put(new THREE.Mesh(gable(19, 35, 3), roofGrey), 6, -4, 6);
    for (const [sx, sz] of [[26, 10], [26, 20]]) {
      put(new THREE.Mesh(new THREE.CylinderGeometry(4, 4, 15, 20).translate(0, 7.5, 0), silo), sx, sz);
      put(new THREE.Mesh(new THREE.ConeGeometry(4.2, 3, 20).translate(0, 16.5, 0), silo), sx, sz);
    }
    put(new THREE.Mesh(new THREE.BoxGeometry(10, 5, 8).translate(0, 2.5, 0), wall), -14, 30);
    put(new THREE.Mesh(gable(11, 9, 3), barnRed), -14, 30, 5);
    put(new THREE.Mesh(new THREE.CylinderGeometry(3, 3, 4, 16).translate(0, 9, 0), tank), 16, -30);
    for (const [lx, lz] of [[14, -32], [18, -32], [14, -28], [18, -28]]) put(new THREE.Mesh(new THREE.CylinderGeometry(0.2, 0.2, 7, 4).translate(0, 3.5, 0), wood), lx, lz);
    grp.rotation.y = ry;
    at(grp, x, v);
    // the gravel pad and a track out to the nearest field road, painted into the texture
    paint.save();
    paint.translate(x * paint.m2p, (TILE - v) * paint.m2p);
    paint.rotate(-ry);
    paint.fillStyle = '#8d8676';
    paint.fillRect(-36 * paint.m2p, -44 * paint.m2p, 72 * paint.m2p, 88 * paint.m2p);
    paint.restore();
  };
  yard(300, Y0 + 95, 0.3);
  yard(860, Y0 - 110, -0.2);
  yard(1500, Y0 + 120, 1.2);
  yard(1960, Y0 - 95, 0.6);
  yard(2600, Y0 + 100, -0.5);
  yard(3050, Y0 - 140, 0.9);
  return g;
}
export function createFarm(groundY, gx, GD) {
  const group = new THREE.Group();
  const {canvas, g, m2p} = paintFarm();
  const patches = paintPatches(g, m2p);
  g.m2p = m2p;
  const propTile = buildProps(g);
  const props = new THREE.Group();
  for (const c of [-1, 0, 1]) { const t = c ? propTile.clone() : propTile; t.position.x = c * TILE; props.add(t); }
  group.add(props);
  const tex = new THREE.CanvasTexture(canvas);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
  tex.anisotropy = 8;
  const B = 22;                                            // the ground plane runs out to the fog
  const ground = new THREE.Mesh(new THREE.PlaneGeometry(B, B), new THREE.MeshStandardMaterial({map: tex, color: new THREE.Color(0.78, 0.82, 0.8), roughness: 0.96, envMapIntensity: 0.12}));
  ground.rotation.x = -Math.PI / 2;
  ground.position.set(gx, groundY, 0);
  ground.receiveShadow = false;
  group.add(ground);
  // a faint scan grid over the farm
  const grid = new THREE.GridHelper(16, 160, '#38e1ff', '#1d5a78');
  Object.assign(grid.material, {transparent: true, opacity: 0.09, blending: THREE.AdditiveBlending, depthWrite: false});
  grid.position.set(gx, groundY + 0.003, 0);
  group.add(grid);

  // markers: a ring, a soft disc and a beam per patch; hidden until detected
  const markers = patches.map((p) => {
    const cls = CLASSES.find((c) => c.key === p.key);
    const col = new THREE.Color(cls.color);
    const m = new THREE.Group();
    const ringM = new THREE.MeshBasicMaterial({color: col.clone().multiplyScalar(1.6), transparent: true, opacity: 0, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide});
    const ring = new THREE.Mesh(new THREE.RingGeometry(0.95, 1, 64), ringM);
    ring.rotation.x = -Math.PI / 2;
    const discM = new THREE.MeshBasicMaterial({color: col, transparent: true, opacity: 0, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide});
    const disc = new THREE.Mesh(new THREE.CircleGeometry(1, 48), discM);
    disc.rotation.x = -Math.PI / 2;
    const pingM = ringM.clone();
    const ping = new THREE.Mesh(new THREE.RingGeometry(0.94, 1, 48), pingM);
    ping.rotation.x = -Math.PI / 2;
    const beamM = new THREE.LineBasicMaterial({color: col.clone().multiplyScalar(1.4), transparent: true, opacity: 0, blending: THREE.AdditiveBlending});
    const beam = new THREE.Line(new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(0, 0, 0), new THREE.Vector3(0, 0.3, 0)]), beamM);
    m.add(ring, disc, ping, beam);
    group.add(m);
    return {p, cls, m, ring, disc, ping, beam, ringM, discM, pingM, beamM, found: -1, lap: 0};
  });

  const counts = Object.fromEntries(CLASSES.map((c) => [c.key, 0]));
  const log = [], events = [];
  const wrap = (d) => ((d % TILE) + TILE * 1.5) % TILE - TILE / 2;
  return {
    group, counts, log, events,
    /** s: frame state (fl, dist, T); returns tags to draw in the HUD */
    update(s) {
      const scale = GD / s.fl.h;
      const R = B / (scale * TILE);
      tex.repeat.set(R, R);
      tex.offset.set((s.dist - B / (2 * scale)) / TILE, (Y0 - B / (2 * scale)) / TILE);
      grid.position.x = gx - ((s.dist * scale) % 0.1);
      props.scale.setScalar(scale);
      props.position.set(gx - (((s.dist % TILE) + TILE) % TILE) * scale, groundY, 0);
      const half = (s.fl.along * scale) / 2, swath = (s.fl.swath * scale) / 2;
      const tags = [];
      for (const k of markers) {
        const xr = wrap(k.p.tx - s.dist), yr = k.p.ty - Y0;
        const x = gx + xr * scale, z = -yr * scale, r = k.p.r * scale;
        k.m.position.set(x, groundY + 0.004, z);
        k.ring.scale.setScalar(r * 1.1); k.disc.scale.setScalar(r);
        // scanned: the footprint centre passes over it and it lies inside the swath
        if (k.found < 0 && Math.abs(xr * scale) < half * 0.5 && Math.abs(z) < swath) {
          k.found = s.T;
          counts[k.cls.key]++;
          log.unshift({cls: k.cls, t: s.T, conf: k.p.conf, area: (Math.PI * k.p.r * k.p.r) / 1e4});
          events.push({cls: k.cls, d: s.dist});
          if (log.length > 6) log.pop();
        }
        if (xr > TILE * 0.3) k.found = -1;                // far behind: it comes round again on the next lap
        const on = k.found >= 0 ? Math.min(1, (s.T - k.found) * 3) : 0;
        const age = k.found >= 0 ? s.T - k.found : 99;
        const pulse = 0.75 + 0.25 * Math.sin(s.T * 4 + k.p.tx);
        k.ringM.opacity = on * pulse;
        k.discM.opacity = on * 0.12;
        k.beamM.opacity = on * 0.8;
        k.beam.scale.y = on * (0.6 + 0.4 * Math.min(1, age));
        const pu = (age % 1.6) / 1.6;
        k.ping.scale.setScalar(r * (1.1 + pu * 1.4));
        k.pingM.opacity = on * (1 - pu) * 0.45;
        k.m.visible = on > 0.01;
        if (on > 0.3 && Math.abs(x - gx) < 2.4) tags.push({p: [x, groundY + 0.3 * k.beam.scale.y, z], cls: k.cls, conf: k.p.conf, area: (Math.PI * k.p.r * k.p.r) / 1e4, a: on});
      }
      return tags;
    },
  };
}
