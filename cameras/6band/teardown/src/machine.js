// The camera itself: every part of the CAD model as its own mesh, plus the things that show it working:
// the four fields of view, the ground sliding underneath, the footprints left by each trigger, the frames
// travelling down the flat cables, and the air going through the heatsink duct.
import * as THREE from 'three';
import {toCreasedNormals} from 'three/addons/utils/BufferGeometryUtils.js';
import {FOV, ndvi} from './sim.js';

export const ACCENT = '#e2531a';
const BANDCOL = ['#e2531a', '#b3202a', '#7a1440', '#4a1446'];     // RGB (accent), red edge, NIR, ext. NIR
export const GROUND_D = 0.17;      // the ground is drawn 17 cm under the lenses: angles are true, the height is not

function material(kind, c) {
  const col = new THREE.Color(c[0], c[1], c[2]);
  const P = (o) => new THREE.MeshStandardMaterial({color: col, roughness: 0.5, metalness: 0, envMapIntensity: 0.6, ...o});
  switch (kind) {
    case 'shell': return P({color: new THREE.Color(c[0] * 0.75, c[1] * 0.75, c[2] * 0.78), roughness: 0.62, envMapIntensity: 0.5});
    case 'pcb': return P({roughness: 0.45, envMapIntensity: 0.5});
    case 'ic': return P({color: new THREE.Color('#141416'), roughness: 0.5});
    case 'ceramic': return P({roughness: 0.6});
    case 'ceramic_dark': return P({roughness: 0.4});
    case 'ferrite': return P({color: new THREE.Color('#232325'), roughness: 0.75});
    case 'gold': return P({color: new THREE.Color('#d9a544'), metalness: 1, roughness: 0.35});
    case 'accent': return P({color: new THREE.Color('#c8501c'), metalness: 0.9, roughness: 0.45, emissive: new THREE.Color(ACCENT), emissiveIntensity: 0});
    case 'steel': return P({color: new THREE.Color('#c9cacc'), metalness: 1, roughness: 0.4});
    case 'steel_black': return P({color: new THREE.Color('#1a1a1c'), metalness: 1, roughness: 0.45});
    case 'alu': return P({color: new THREE.Color('#c6c8cb'), metalness: 1, roughness: 0.45});
    case 'anodised': return P({color: new THREE.Color('#18181a'), metalness: 0.85, roughness: 0.5, envMapIntensity: 0.55});
    case 'rubberised': return P({color: new THREE.Color('#111113'), roughness: 0.8});
    case 'rubber': return P({roughness: 0.75});
    case 'plastic_gloss': return P({roughness: 0.45});
    case 'fpc': return P({color: new THREE.Color('#d06a12'), roughness: 0.45, side: THREE.DoubleSide});
    case 'lens': return new THREE.MeshPhysicalMaterial({color: new THREE.Color(c[0] * 0.5 + 0.03, c[1] * 0.5 + 0.02, c[2] * 0.5 + 0.06), metalness: 0.85, roughness: 0.12, clearcoat: 1, clearcoatRoughness: 0.05, envMapIntensity: 1.1});
    case 'window': return P({color: new THREE.Color('#dfeaf0'), transparent: true, opacity: 0.16, roughness: 0.05, depthWrite: false});
    case 'filter': return P({color: new THREE.Color('#7fd4de'), transparent: true, opacity: 0.45, roughness: 0.05, depthWrite: false});
    case 'bandpass': return new THREE.MeshPhysicalMaterial({color: new THREE.Color(c[0] * 0.55 + 0.02, c[1] * 0.4 + 0.01, c[2] * 0.5 + 0.02), metalness: 0.8, roughness: 0.15, clearcoat: 1, clearcoatRoughness: 0.04});
    case 'cfrp': return P({color: new THREE.Color('#161618'), roughness: 0.4, metalness: 0.2});
    case 'emit': return P({emissive: col, emissiveIntensity: 0.9});
    case 'sensor': return P({color: new THREE.Color('#1f6f62'), metalness: 1, roughness: 0.25});
    case 'ptfe': return P({color: new THREE.Color('#ecebe6'), roughness: 0.6});
    case 'black': return P({color: new THREE.Color('#050506'), roughness: 0.9});
    case 'paper': return P({roughness: 0.8});
    default: return P({});
  }
}

export function buildMachine(data, bin, boardTex) {
  const root = new THREE.Group();
  const parts = [];
  const byName = {};
  const f32 = new Float32Array(bin);
  for (const p of data.parts) {
    let geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.BufferAttribute(f32.subarray(p.o * 3, (p.o + p.k) * 3), 3));
    geo = toCreasedNormals(geo, 0.62);
    const mat = material(p.m, p.c);
    const mesh = new THREE.Mesh(geo, mat);
    mesh.castShadow = !/window|filter|lens|fpc/.test(p.m);
    mesh.receiveShadow = true;
    mesh.userData = p;
    root.add(mesh);
    const rec = {p, mesh, mat, base: mat.opacity, wasT: mat.transparent, vis: 1};
    parts.push(rec);
    byName[p.n] = rec;
  }
  // the routed board: a texture of the real copper, mask and silkscreen on top of the carrier
  const b = data.board;
  boardTex.colorSpace = THREE.SRGBColorSpace;
  boardTex.anisotropy = 8;
  const top = new THREE.Mesh(new THREE.PlaneGeometry(b.l, b.w), new THREE.MeshStandardMaterial({map: boardTex, roughness: 0.42, metalness: 0.05, envMapIntensity: 0.6, transparent: true}));
  top.rotation.x = -Math.PI / 2;
  top.position.set(b.x0 + b.l / 2, b.y + 0.00006, b.z0 + b.w / 2);
  top.receiveShadow = true;
  root.add(top);
  const carrier = byName.carrier_pcb;

  // ---------------------------------------------------------------- optics: lens fronts and fields of view
  const lensNames = ['rgb_lens_glass', 'mira0_lens_glass', 'mira1_lens_glass', 'mira2_lens_glass'];
  const lenses = lensNames.map((n, i) => {
    const c = byName[n].p.ctr;
    const H = i === 0 ? FOV.rgbH : FOV.miraH, V = i === 0 ? FOV.rgbV : FOV.miraV;
    return {x: c[0], y: c[1], z: c[2], hw: GROUND_D * Math.tan(H / 2), hl: GROUND_D * Math.tan(V / 2), col: new THREE.Color(BANDCOL[i])};
  });
  const groundY = lenses[0].y - GROUND_D;
  const optics = new THREE.Group();
  root.add(optics);
  const cones = lenses.map((L) => {
    const v = [L.x, L.y, L.z];
    const c = [[L.x - L.hl, groundY, L.z - L.hw], [L.x + L.hl, groundY, L.z - L.hw], [L.x + L.hl, groundY, L.z + L.hw], [L.x - L.hl, groundY, L.z + L.hw]];
    const pos = [];
    for (let i = 0; i < 4; i++) pos.push(...v, ...c[i], ...c[(i + 1) % 4]);
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
    const m = new THREE.Mesh(g, new THREE.MeshBasicMaterial({color: L.col, transparent: true, opacity: 0.05, side: THREE.DoubleSide, depthWrite: false}));
    const lp = [];
    for (let i = 0; i < 4; i++) lp.push(...v, ...c[i]);
    const lines = new THREE.LineSegments(new THREE.BufferGeometry().setAttribute('position', new THREE.Float32BufferAttribute(lp, 3)),
      new THREE.LineBasicMaterial({color: L.col, transparent: true, opacity: 0.5}));
    optics.add(m, lines);
    return {m, lines};
  });

  // ---------------------------------------------------------------- the ground: a made-up field that slides under the camera
  const GL = 0.46, GW = 0.30, gx = lenses[0].x;
  const gc = document.createElement('canvas');
  gc.width = 1024; gc.height = 512;
  {
    const g = gc.getContext('2d');
    const img = g.createImageData(1024, 512);
    for (let j = 0; j < 512; j++) {
      for (let i = 0; i < 1024; i++) {
        // periodic in x so the texture can scroll for ever: cross-fade the field with itself one period back
        const xm = i * 0.42, ym = j * 0.42, Lp = 1024 * 0.42, wgt = i / 1024;
        const n = ndvi(xm, ym) * (1 - wgt) + ndvi(xm - Lp, ym) * wgt;
        const row = 0.5 + 0.5 * Math.cos((j / 512) * Math.PI * 2 * 40);
        const soil = [168, 140, 108], leaf = [40 + 110 * (1 - n), 96 + 70 * n, 44 + 20 * (1 - n)];
        const k = Math.min(1, Math.max(0, (n - 0.12) * 1.7)) * (0.45 + 0.55 * row);
        const o = (j * 1024 + i) * 4;
        for (let c = 0; c < 3; c++) img.data[o + c] = soil[c] * (1 - k) + leaf[c] * k;
        img.data[o + 3] = 255;
      }
    }
    g.putImageData(img, 0, 0);
  }
  const gtex = new THREE.CanvasTexture(gc);
  gtex.colorSpace = THREE.SRGBColorSpace;
  gtex.wrapS = THREE.RepeatWrapping;
  gtex.anisotropy = 8;
  const ground = new THREE.Mesh(new THREE.PlaneGeometry(GL, GW), new THREE.MeshStandardMaterial({map: gtex, roughness: 0.95, metalness: 0, envMapIntensity: 0.25, transparent: true, opacity: 1}));
  ground.rotation.x = -Math.PI / 2;
  ground.position.set(gx, groundY, 0);
  ground.receiveShadow = true;
  optics.add(ground);
  const rim = new THREE.LineLoop(new THREE.BufferGeometry().setAttribute('position', new THREE.Float32BufferAttribute(
    [gx - GL / 2, groundY, -GW / 2, gx + GL / 2, groundY, -GW / 2, gx + GL / 2, groundY, GW / 2, gx - GL / 2, groundY, GW / 2], 3)),
    new THREE.LineBasicMaterial({color: '#8b8f95'}));
  optics.add(rim);
  // footprints: the last triggers, each a set of four rectangles that travel with the ground
  const NST = 7;
  const stamps = [];
  for (let s = 0; s < NST; s++) {
    const set = lenses.map((L) => {
      const y = groundY + 0.0006;
      const pts = [L.x - L.hl, y, L.z - L.hw, L.x + L.hl, y, L.z - L.hw, L.x + L.hl, y, L.z + L.hw, L.x - L.hl, y, L.z + L.hw];
      const l = new THREE.LineLoop(new THREE.BufferGeometry().setAttribute('position', new THREE.Float32BufferAttribute(pts, 3)),
        new THREE.LineBasicMaterial({color: L.col, transparent: true, opacity: 0}));
      optics.add(l);
      return l;
    });
    stamps.push(set);
  }

  // ---------------------------------------------------------------- frames travelling down the flat cables
  const J = ['brd_J3', 'brd_J4', 'brd_J5', 'brd_J6'].map((n) => byName[n].p.ctr);
  const camC = ['rgb_adapter_fpc', 'mira0_fpc_conn', 'mira1_fpc_conn', 'mira2_fpc_conn'].map((n) => byName[n].p.ctr);
  const cable = ['fpc_J3', 'fpc_J4', 'fpc_J5', 'fpc_J6'].map((n) => byName[n].p.ctr);
  const soc = byName.jetson_soc.p.ctr;
  const paths = camC.map((c, i) => new THREE.CatmullRomCurve3([new THREE.Vector3(...c), new THREE.Vector3(...cable[i]), new THREE.Vector3(...J[i]),
    new THREE.Vector3(J[i][0] - 0.02, J[i][1], J[i][2] * 0.6), new THREE.Vector3(soc[0] + 0.012, J[i][1], soc[2])]));
  const NP = 5;
  const pulses = paths.map((_, i) => {
    const m = new THREE.InstancedMesh(new THREE.SphereGeometry(0.0016, 10, 8), new THREE.MeshBasicMaterial({color: new THREE.Color(BANDCOL[i]).lerp(new THREE.Color('#ffffff'), 0.25)}), NP);
    m.frustumCulled = false;
    root.add(m);
    return m;
  });

  // ---------------------------------------------------------------- air through the duct
  const NA = 90;
  const air = new THREE.InstancedMesh(new THREE.BoxGeometry(0.009, 0.0005, 0.0005), new THREE.MeshBasicMaterial({transparent: true, opacity: 0.85}), NA);
  air.frustumCulled = false;
  air.instanceColor = new THREE.InstancedBufferAttribute(new Float32Array(NA * 3), 3);
  root.add(air);
  const hs = byName.heatsink.p.ctr;
  const seeds = [...Array(NA)].map((_, i) => ({s: (i * 0.618034) % 1, z: (((i * 0.3819) % 1) - 0.5) * 0.064, y: (((i * 0.7548) % 1) - 0.5) * 0.007}));
  const M4 = new THREE.Matrix4(), Q = new THREE.Quaternion(), V = new THREE.Vector3(), SC = new THREE.Vector3(1, 1, 1), EU = new THREE.Euler();
  const cool = new THREE.Color('#3d8fe0'), warm = new THREE.Color(ACCENT), tmpc = new THREE.Color();

  const groupsOf = [...new Set(data.parts.map((p) => p.g))];
  const bezels = parts.filter((r) => r.p.m === 'accent');
  const setFade = (rec, a) => {
    if (Math.abs(rec.vis - a) < 0.002) return;
    rec.vis = a;
    const m = rec.mat;
    m.transparent = rec.wasT || a < 0.999;
    m.opacity = rec.base * a;
    m.depthWrite = a > 0.5 && !rec.wasT;
    rec.mesh.visible = a > 0.01;
    rec.mesh.castShadow = a > 0.6 && !/window|filter|lens|fpc/.test(rec.p.m);
  };

  /**
   * s: {k explode 0..1, shell 0..1 (1 = shown), xray 0..1, iso: group or null, foot, airOn, sigOn 0..1,
   *     fl: flight(), th: thermal(), dist: metres flown, trig: [times since each recent trigger], T: seconds}
   */
  function update(s) {
    for (const rec of parts) {
      const p = rec.p;
      rec.mesh.position.set(p.e[0] * s.k, p.e[1] * s.k, p.e[2] * s.k);
      let a = 1;
      if (p.g === 'DLS + GNSS top unit') a = s.top;
      if (p.g === 'Enclosure' || p.g === 'Mount') a = Math.min(a, s.shell * (1 - 0.8 * s.xray));
      if (s.iso && p.g !== s.iso && !(s.iso === 'optics' && /camera|Optics/.test(p.g))) a = Math.min(a, 0.06);
      setFade(rec, a);
    }
    top.position.y = b.y + 0.00006 + carrier.p.e[1] * s.k;
    top.material.opacity = carrier.vis;
    top.visible = carrier.vis > 0.01;

    // optics
    const fo = s.foot * (1 - s.k);
    optics.visible = fo > 0.01;
    const since = s.trig.length ? s.trig[0] : 9;
    const flash = Math.exp(-since * 9);
    cones.forEach((c) => {
      c.m.material.opacity = fo * (0.045 + 0.16 * flash);
      c.lines.material.opacity = fo * (0.35 + 0.5 * flash);
    });
    for (const r of bezels) r.mat.emissiveIntensity = 1.6 * flash * (1 - s.k);
    ground.material.opacity = fo;
    rim.material.opacity = fo;
    rim.material.transparent = true;
    const vg = (s.fl.v * GROUND_D) / s.fl.h;                      // ground speed at drawing scale
    gtex.offset.x = (s.dist * GROUND_D) / s.fl.h / GL;
    stamps.forEach((set, i) => {
      const age = s.trig[i];
      set.forEach((l) => {
        if (age === undefined) { l.material.opacity = 0; return; }
        const dx = -vg * age;
        l.position.x = dx;
        const edge = 1 - Math.min(1, Math.max(0, (-dx - GL * 0.30) / (GL * 0.12)));
        l.material.opacity = fo * edge * (i === 0 ? 1 : 0.55);
      });
    });

    // frames on the cables: drawn 5x slower than the real read-out so the eye can follow them
    pulses.forEach((m, i) => {
      const dur = (i === 0 ? s.fl.readRgb : s.fl.readMira) * 5 + 0.12;
      let any = false;
      for (let j = 0; j < NP; j++) {
        const u = (since - j * 0.035) / dur;
        if (s.sigOn > 0.01 && u > 0 && u < 1) {
          paths[i].getPoint(u, V);
          V.y += carrier.p.e[1] * s.k * Math.min(1, u * 2.2);
          const sc = (1 - j / NP) * s.sigOn;
          M4.compose(V, Q.identity(), SC.set(sc, sc, sc));
          any = true;
        } else M4.makeScale(0, 0, 0);
        m.setMatrixAt(j, M4);
      }
      m.visible = any;
      m.instanceMatrix.needsUpdate = true;
    });

    // air: in at the nose, along the fins, out through the louvres on both flanks
    air.visible = s.airOn > 0.01;
    if (air.visible) {
      const sp = 0.25 + s.th.u * 0.11;
      const yoff = byName.heatsink.p.e[1] * s.k;
      seeds.forEach((d, i) => {
        const u = (d.s + s.T * sp * (0.8 + 0.4 * ((i * 0.37) % 1))) % 1;
        const x = -0.035 + u * 0.145;
        const out = Math.max(0, (u - 0.66) / 0.34);
        const z = d.z + Math.sign(d.z || 1) * out * out * 0.03;
        V.set(x - out * 0.012, hs[1] - 0.003 + d.y + yoff, z);
        Q.setFromEuler(EU.set(0, -Math.sign(d.z || 1) * out * 1.1, 0));
        const fade = Math.min(1, u * 8) * Math.min(1, (1 - u) * 6) * s.airOn;
        M4.compose(V, Q, SC.set(0.6 + s.th.u * 0.12, fade, fade));
        air.setMatrixAt(i, M4);
        tmpc.copy(cool).lerp(warm, Math.min(1, Math.max(0, (x - 0.02) / 0.06)));
        air.setColorAt(i, tmpc);
      });
      air.instanceMatrix.needsUpdate = true;
      air.instanceColor.needsUpdate = true;
    }
  }
  const anchor = (name, k = 0) => {
    const r = byName[name];
    return [r.p.ctr[0] + r.p.e[0] * k, r.p.ctr[1] + r.p.e[1] * k, r.p.ctr[2] + r.p.e[2] * k];
  };
  return {root, parts, byName, update, lenses, groundY, groups: groupsOf, anchor};
}
