// The farm around the field being sprayed, showcase edition: smallholder plots, a farm road, a farmhouse, a cattle
// shed, a water tank, trees and power poles. Everything is built in metres and scrolls with the flight; the scale
// follows the height slider, so the ground always matches the camera's footprint. Illustration only.
import * as THREE from 'three';

const TILE = 600;                       // metres per repeat of the surroundings
const PX = 2048;
let seed = 3;
const rnd = () => ((seed = (seed * 16807) % 2147483647) / 2147483647);

function paint() {
  const c = document.createElement('canvas');
  c.width = c.height = PX;
  const g = c.getContext('2d');
  const k = PX / TILE;
  g.fillStyle = '#4a3f2e';
  g.fillRect(0, 0, PX, PX);
  const CROPS = [[62, 116, 50], [84, 130, 56], [128, 140, 66], [168, 150, 80], [96, 82, 58], [72, 104, 48], [110, 128, 60]];
  // small plots, 30-90 m, separated by bunds
  for (let y = 0; y < TILE;) {
    const h = 30 + rnd() * 60;
    for (let x = 0; x < TILE;) {
      const w = 30 + rnd() * 70;
      const col = CROPS[Math.floor(rnd() * CROPS.length)];
      g.fillStyle = `rgb(${col.join(',')})`;
      g.fillRect(x * k, y * k, w * k, h * k);
      g.strokeStyle = 'rgba(0,0,0,0.12)';
      g.lineWidth = 1;
      g.beginPath();
      const vert = rnd() < 0.5;
      if (vert) for (let xx = x * k; xx < (x + w) * k; xx += 2.2) { g.moveTo(xx, y * k); g.lineTo(xx, (y + h) * k); }
      else for (let yy = y * k; yy < (y + h) * k; yy += 2.2) { g.moveTo(x * k, yy); g.lineTo((x + w) * k, yy); }
      g.stroke();
      g.strokeStyle = '#7b6a4c';
      g.lineWidth = 1.2 * k;
      g.strokeRect(x * k, y * k, w * k, h * k);
      x += w;
    }
    y += h;
  }
  // the farm road and an irrigation channel, parallel to the flight line
  g.fillStyle = '#9a8a6a';
  g.fillRect(0, (TILE / 2 + 34) * k, PX, 5 * k);
  g.fillStyle = '#2a4a5a';
  g.fillRect(0, (TILE / 2 - 30) * k, PX, 1.6 * k);
  return {canvas: c, g, k};
}

function props(pg) {
  const grp = new THREE.Group();
  const M = (c, o = {}) => new THREE.MeshStandardMaterial({color: new THREE.Color(c), roughness: 0.8, metalness: 0.05, envMapIntensity: 0.4, ...o});
  const wallM = M('#e8e2d4'), tileM = M('#a8452f'), tinM = M('#8c959e', {metalness: 0.6, roughness: 0.4}), woodM = M('#5a4634'),
    leafM = M('#2f5a2a'), leafM2 = M('#3d6b30'), tankM = M('#2b2f33'), concM = M('#a9a59b');
  const at = (m, x, z, y = 0, ry = 0) => { m.position.set(x, y, z); m.rotation.y = ry; grp.add(m); return m; };
  const gable = (w, l, h) => {
    const s = new THREE.Shape();
    s.moveTo(-w / 2, 0); s.lineTo(w / 2, 0); s.lineTo(0, h); s.closePath();
    return new THREE.ExtrudeGeometry(s, {depth: l, bevelEnabled: false}).translate(0, 0, -l / 2);
  };
  // z = -(metres across from the flight line); the road is 34 m to one side
  const farm = (x, zc) => {
    at(new THREE.Mesh(new THREE.BoxGeometry(12, 4, 9).translate(0, 2, 0), wallM), x, zc);
    at(new THREE.Mesh(gable(13, 10, 2.6), tileM), x, zc, 4);
    at(new THREE.Mesh(new THREE.BoxGeometry(16, 0.25, 9).translate(0, 3.6, 0), tinM), x + 18, zc + 2);
    for (const [px, pz] of [[-7.5, -4], [7.5, -4], [-7.5, 4], [7.5, 4]]) at(new THREE.Mesh(new THREE.CylinderGeometry(0.15, 0.15, 3.6, 6).translate(0, 1.8, 0), woodM), x + 18 + px, zc + 2 + pz);
    at(new THREE.Mesh(new THREE.CylinderGeometry(1.6, 1.6, 2.2, 16).translate(0, 7, 0), tankM), x - 12, zc - 6);
    for (const [px, pz] of [[-1, -1], [1, -1], [-1, 1], [1, 1]]) at(new THREE.Mesh(new THREE.BoxGeometry(0.25, 6, 0.25).translate(0, 3, 0), concM), x - 12 + px, zc - 6 + pz);
    at(new THREE.Mesh(new THREE.BoxGeometry(3, 2.5, 3).translate(0, 1.25, 0), wallM), x - 22, zc + 8);
    pg.fillStyle = '#8d8676';
    pg.fillRect((x - 30) * pg.k, (TILE / 2 - zc - 14) * pg.k, 60 * pg.k, 28 * pg.k);
  };
  farm(140, -58);
  farm(430, 62);
  // trees along the bunds and around the yards
  const tree = (x, z, s) => {
    at(new THREE.Mesh(new THREE.CylinderGeometry(0.25 * s, 0.35 * s, 3 * s, 6).translate(0, 1.5 * s, 0), woodM), x, z);
    at(new THREE.Mesh(new THREE.SphereGeometry(2.4 * s, 10, 8).translate(0, 4.4 * s, 0), rnd() < 0.5 ? leafM : leafM2), x, z);
    at(new THREE.Mesh(new THREE.SphereGeometry(1.7 * s, 10, 8).translate(0.9 * s, 5.6 * s, 0.4 * s), leafM2), x, z);
  };
  for (let x = 0; x < TILE; x += 9 + rnd() * 14) tree(x, -(28 + rnd() * 4), 0.8 + rnd() * 0.5);
  for (let i = 0; i < 26; i++) tree(rnd() * TILE, (rnd() < 0.5 ? -1 : 1) * (40 + rnd() * 120), 0.8 + rnd() * 0.6);
  // power poles along the road, with wires
  const wires = [];
  let prev = null;
  for (let x = 0; x <= TILE; x += 40) {
    at(new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.18, 9, 6).translate(0, 4.5, 0), concM), x, 40);
    at(new THREE.Mesh(new THREE.BoxGeometry(0.15, 0.15, 1.8).translate(0, 8.6, 0), woodM), x, 40);
    if (prev !== null) for (const dz of [-0.75, 0, 0.75]) {
      const pts = [0, 1 / 3, 2 / 3, 1].map((t) => [prev + (x - prev) * t, 8.8 - 0.8 * Math.sin(Math.PI * t), 40 + dz]);
      for (let i = 0; i < 3; i++) wires.push(...pts[i], ...pts[i + 1]);
    }
    prev = x;
  }
  grp.add(new THREE.LineSegments(new THREE.BufferGeometry().setAttribute('position', new THREE.Float32BufferAttribute(wires, 3)),
    new THREE.LineBasicMaterial({color: '#1c1f22', transparent: true, opacity: 0.8})));
  return grp;
}

export function createFarmyard(groundY, gx, GD) {
  const group = new THREE.Group();
  const {canvas, g, k} = paint();
  g.k = k;
  const tile = props(g);
  const pr = new THREE.Group();
  for (const c of [-1, 0, 1]) { const t = c ? tile.clone() : tile; t.position.x = c * TILE; pr.add(t); }
  group.add(pr);
  const tex = new THREE.CanvasTexture(canvas);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
  tex.anisotropy = 8;
  const B = 90;
  const ground = new THREE.Mesh(new THREE.PlaneGeometry(B, B), new THREE.MeshStandardMaterial({map: tex, color: new THREE.Color(0.8, 0.84, 0.8), roughness: 0.96, envMapIntensity: 0.12}));
  ground.rotation.x = -Math.PI / 2;
  ground.position.set(gx, groundY - 0.01, 0);
  group.add(ground);
  return {
    group,
    update(s) {
      const scale = GD / s.fl.h;
      const R = B / (scale * TILE);
      tex.repeat.set(R, R);
      tex.offset.set((s.dist - B / (2 * scale)) / TILE, (TILE / 2 - B / (2 * scale)) / TILE);
      pr.scale.setScalar(scale);
      pr.position.set(gx - (((s.dist % TILE) + TILE) % TILE) * scale, groundY - 0.01, 0);
    },
  };
}
