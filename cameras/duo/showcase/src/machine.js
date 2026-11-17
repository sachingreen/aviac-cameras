// The Duo itself: every part of the CAD model as its own mesh, plus what shows it working: the two fields of
// view, the field sliding underneath with the sprayed swath drawn on it (gap included), spray mist under the
// boom, the footprints left by each trigger, frames travelling down the flat cables, and heat leaving the lid.
// Structure after the teardown kit's example machines (elvarofficial/teardown, MIT).
import * as THREE from 'three';
import {toCreasedNormals} from 'three/addons/utils/BufferGeometryUtils.js';
import {FOV, SWATH, sprayAt, vigour} from './sim.js';
import {createFarmyard} from './farmyard.js';
import {createSprayer} from './sprayer.js';

export const ACCENT = '#ff6b2c';
const CAMCOL = ['#38c8ff', '#ff4a3a'];          // camera A (RGB + NIR), camera B (your band)
export const GROUND_D = 1.2;                    // the crop is drawn 1.2 m under the lenses: angles true, height compressed
const SPRAY = new THREE.Color('#2f8fd8');

function material(kind, c) {
  const col = new THREE.Color(c[0], c[1], c[2]);
  const P = (o) => new THREE.MeshStandardMaterial({color: col, roughness: 0.5, metalness: 0, envMapIntensity: 0.6, ...o});
  switch (kind) {
    case 'shell': return P({color: new THREE.Color(c[0] * 0.8, c[1] * 0.8, c[2] * 0.85), roughness: 0.6, envMapIntensity: 0.5});
    case 'pcb': return P({roughness: 0.45, envMapIntensity: 0.5});
    case 'ic': return P({color: new THREE.Color('#141416'), roughness: 0.5});
    case 'ceramic': return P({roughness: 0.6});
    case 'ceramic_dark': return P({roughness: 0.4});
    case 'ferrite': return P({color: new THREE.Color('#232325'), roughness: 0.75});
    case 'gold': return P({color: new THREE.Color('#d9a544'), metalness: 1, roughness: 0.35});
    case 'accent': return P({color: new THREE.Color('#c8501c'), metalness: 0.9, roughness: 0.42, emissive: new THREE.Color(ACCENT), emissiveIntensity: 0});
    case 'steel': return P({color: new THREE.Color('#c9cacc'), metalness: 1, roughness: 0.4});
    case 'steel_black': return P({color: new THREE.Color('#1a1a1c'), metalness: 1, roughness: 0.45});
    case 'alu': return P({color: new THREE.Color('#b9bcc0'), metalness: 1, roughness: 0.42, envMapIntensity: 0.9});
    case 'hardcoat': return P({color: new THREE.Color('#62666c'), metalness: 0.8, roughness: 0.46, envMapIntensity: 0.85});
    case 'steel_brushed': return P({color: new THREE.Color('#b4b6b9'), metalness: 1, roughness: 0.32});
    case 'etch': return P({color: new THREE.Color('#a9adb3'), metalness: 0.5, roughness: 0.6});
    case 'paper': return P({color: new THREE.Color('#f4f4f1'), roughness: 0.9});
    case 'anodised': return P({color: new THREE.Color('#18181a'), metalness: 0.85, roughness: 0.5, envMapIntensity: 0.55});
    case 'rubberised': return P({color: new THREE.Color('#111113'), roughness: 0.8});
    case 'rubber': return P({roughness: 0.75});
    case 'plastic_gloss': return P({roughness: 0.45});
    case 'fpc': return P({color: new THREE.Color('#d06a12'), roughness: 0.45, side: THREE.DoubleSide});
    case 'lens': return new THREE.MeshPhysicalMaterial({color: new THREE.Color(c[0] * 0.5 + 0.03, c[1] * 0.5 + 0.02, c[2] * 0.5 + 0.06), metalness: 0.85, roughness: 0.12, clearcoat: 1, clearcoatRoughness: 0.05, envMapIntensity: 1.1});
    case 'window': return P({color: new THREE.Color('#dfeaf0'), transparent: true, opacity: 0.16, roughness: 0.05, depthWrite: false});
    case 'bandpass': return new THREE.MeshPhysicalMaterial({color: new THREE.Color(c[0] * 0.55 + 0.02, c[1] * 0.4 + 0.01, c[2] * 0.5 + 0.02), metalness: 0.8, roughness: 0.15, clearcoat: 1, clearcoatRoughness: 0.04});
    case 'cfrp': return P({color: new THREE.Color('#161618'), roughness: 0.38, metalness: 0.2});
    case 'emit': return P({emissive: col, emissiveIntensity: 1.0});
    case 'sensor': return P({color: new THREE.Color('#1f6f62'), metalness: 1, roughness: 0.25});
    case 'black': return P({color: new THREE.Color('#050506'), roughness: 0.9});
    default: return P({});
  }
}

const isLid = (n) => /^(lid|gasket|lid_screw|tim_pad)/.test(n);

export function buildMachine(data, bin, boardTex) {
  const root = new THREE.Group();
  const parts = [], byName = {};
  const f32 = new Float32Array(bin);
  for (const p of data.parts) {
    let geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.BufferAttribute(f32.subarray(p.o * 3, (p.o + p.k) * 3), 3));
    geo = toCreasedNormals(geo, 0.62);
    const mat = material(p.m, p.c);
    const mesh = new THREE.Mesh(geo, mat);
    mesh.castShadow = !/window|lens|fpc/.test(p.m);
    mesh.receiveShadow = true;
    mesh.userData = p;
    root.add(mesh);
    const rec = {p, mesh, mat, base: mat.opacity, wasT: mat.transparent, vis: 1};
    parts.push(rec);
    byName[p.n] = rec;
  }
  // the routed board: mounted socket-side up, so its copper, mask and silkscreen face down toward the cameras
  const b = data.board;
  boardTex.colorSpace = THREE.SRGBColorSpace;
  boardTex.anisotropy = 8;
  const face = new THREE.Mesh(new THREE.PlaneGeometry(b.l, b.w), new THREE.MeshStandardMaterial({map: boardTex, roughness: 0.42, metalness: 0.05, envMapIntensity: 0.6, transparent: true}));
  face.rotation.x = b.flip ? Math.PI / 2 : -Math.PI / 2;
  const faceY = b.y + (b.flip ? -0.00006 : 0.00006);
  face.position.set(b.x0 + b.l / 2, faceY, b.z0 + b.w / 2);
  face.receiveShadow = true;
  root.add(face);
  const carrier = byName.carrier_pcb;

  // ---------------------------------------------------------------- fields of view
  const lenses = ['mira0_lens_glass', 'mira1_lens_glass'].map((n, i) => {
    const c = byName[n].p.ctr;
    return {x: c[0], y: c[1], z: c[2], hw: GROUND_D * Math.tan(FOV.h / 2), hl: GROUND_D * Math.tan(FOV.v / 2), col: new THREE.Color(CAMCOL[i])};
  });
  const groundY = lenses[0].y - GROUND_D;
  const gx = lenses[0].x;
  const optics = new THREE.Group();
  root.add(optics);
  const cones = lenses.map((L) => {
    const v = [L.x, L.y, L.z];
    // the sensors' long side runs across the flight line (z)
    const c = [[L.x - L.hl, groundY, L.z - L.hw], [L.x + L.hl, groundY, L.z - L.hw], [L.x + L.hl, groundY, L.z + L.hw], [L.x - L.hl, groundY, L.z + L.hw]];
    const pos = [];
    for (let i = 0; i < 4; i++) pos.push(...v, ...c[i], ...c[(i + 1) % 4]);
    const m = new THREE.Mesh(new THREE.BufferGeometry().setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)),
      new THREE.MeshBasicMaterial({color: L.col, transparent: true, opacity: 0.05, side: THREE.DoubleSide, depthWrite: false, blending: THREE.AdditiveBlending}));
    const lp = [];
    for (let i = 0; i < 4; i++) lp.push(...v, ...c[i]);
    const lines = new THREE.LineSegments(new THREE.BufferGeometry().setAttribute('position', new THREE.Float32BufferAttribute(lp, 3)),
      new THREE.LineBasicMaterial({color: L.col.clone().lerp(new THREE.Color('#ffffff'), 0.35), transparent: true, opacity: 0.5, blending: THREE.AdditiveBlending}));
    optics.add(m, lines);
    return {m, lines};
  });

  // ---------------------------------------------------------------- the field: crop rows that slide under the camera
  const GL = 24, GW = 16;
  const gc = document.createElement('canvas');
  gc.width = 1024; gc.height = 768;
  {
    const g = gc.getContext('2d');
    const img = g.createImageData(gc.width, gc.height);
    for (let j = 0; j < gc.height; j++) {
      for (let i = 0; i < gc.width; i++) {
        const xm = i * 0.02, ym = j * 0.02, Lp = gc.width * 0.02, wgt = i / gc.width;
        const n = vigour(xm, ym) * (1 - wgt) + vigour(xm - Lp, ym) * wgt;          // periodic in x
        const row = Math.pow(0.5 + 0.5 * Math.cos((j / gc.height) * Math.PI * 2 * 22), 2.2);
        const leaf = [34 + 90 * (1 - n), 92 + 70 * n, 40 + 18 * (1 - n)], soil = [150, 124, 96];
        const k = Math.min(1, 0.15 + 0.85 * row * (0.5 + 0.6 * n));
        const o = (j * gc.width + i) * 4;
        for (let c = 0; c < 3; c++) img.data[o + c] = soil[c] * (1 - k) + leaf[c] * k;
        img.data[o + 3] = 255;
      }
    }
    g.putImageData(img, 0, 0);
  }
  const gtex = new THREE.CanvasTexture(gc);
  gtex.colorSpace = THREE.SRGBColorSpace;
  gtex.wrapS = gtex.wrapT = THREE.RepeatWrapping;
  gtex.anisotropy = 8;
  // soft edges: the sprayed field fades into the farm around it
  const ac = document.createElement('canvas');
  ac.width = ac.height = 256;
  {
    const g = ac.getContext('2d');
    const gr = g.createRadialGradient(128, 128, 40, 128, 128, 128);
    gr.addColorStop(0, '#fff'); gr.addColorStop(0.6, '#eee'); gr.addColorStop(1, '#000');
    g.fillStyle = gr; g.fillRect(0, 0, 256, 256);
  }
  const ground = new THREE.Mesh(new THREE.PlaneGeometry(GL, GW), new THREE.MeshStandardMaterial({map: gtex, alphaMap: new THREE.CanvasTexture(ac), color: new THREE.Color(0.82, 0.86, 0.82), roughness: 0.95, envMapIntensity: 0.2, transparent: true, depthWrite: false}));
  ground.rotation.x = -Math.PI / 2;
  ground.position.set(gx, groundY, 0);
  ground.receiveShadow = true;
  root.add(ground);
  const farmyard = createFarmyard(groundY, gx, GROUND_D);
  root.add(farmyard.group);
  const sprayer = createSprayer(byName.drone_tube.p.ctr[1], byName.drone_tube.p.ctr[0]);
  root.add(sprayer.group);
  const rim = new THREE.LineLoop(new THREE.BufferGeometry().setAttribute('position', new THREE.Float32BufferAttribute(
    [gx - GL / 2, groundY, -GW / 2, gx + GL / 2, groundY, -GW / 2, gx + GL / 2, groundY, GW / 2, gx - GL / 2, groundY, GW / 2], 3)),
    new THREE.LineBasicMaterial({color: '#8b8f95', transparent: true}));
  rim.visible = false;
  optics.add(rim);

  // the sprayed swath: one column per strip of ground, painted from where the pump was on when the boom passed it
  const NC = 256;
  const sc = document.createElement('canvas');
  sc.width = NC; sc.height = 4;
  const sctx = sc.getContext('2d');
  const stex = new THREE.CanvasTexture(sc);
  stex.colorSpace = THREE.SRGBColorSpace;
  const swathMesh = new THREE.Mesh(new THREE.PlaneGeometry(GL, 1), new THREE.MeshBasicMaterial({map: stex, alphaMap: new THREE.CanvasTexture(ac), transparent: true, depthWrite: false}));
  swathMesh.rotation.x = -Math.PI / 2;
  swathMesh.position.set(gx, groundY + 0.004, 0);
  root.add(swathMesh);
  const BOOM_DX = sprayer.boomX - gx;          // the boom sprays just ahead of the cameras' centre line
  // spray mist under the boom
  const NM = 160;
  const mist = new THREE.InstancedMesh(new THREE.SphereGeometry(0.008, 6, 4), new THREE.MeshBasicMaterial({color: SPRAY.clone().multiplyScalar(1.4), transparent: true, opacity: 0.5, depthWrite: false, blending: THREE.AdditiveBlending}), NM);
  mist.frustumCulled = false;
  optics.add(mist);
  const mseed = [...Array(NM)].map((_, i) => ({u: (i * 0.618034) % 1, z: ((i * 0.7548) % 1) - 0.5, x: ((i * 0.5698) % 1) - 0.5}));
  // footprints of the last triggers, travelling with the ground
  const stamps = [];
  for (let s = 0; s < 6; s++) {
    stamps.push(lenses.map((L) => {
      const y = groundY + 0.006;
      const l = new THREE.LineLoop(new THREE.BufferGeometry().setAttribute('position', new THREE.Float32BufferAttribute(
        [L.x - L.hl, y, L.z - L.hw, L.x + L.hl, y, L.z - L.hw, L.x + L.hl, y, L.z + L.hw, L.x - L.hl, y, L.z + L.hw], 3)),
        new THREE.LineBasicMaterial({color: L.col.clone().lerp(new THREE.Color('#ffffff'), 0.4), transparent: true, opacity: 0, blending: THREE.AdditiveBlending}));
      optics.add(l);
      return l;
    }));
  }

  // ---------------------------------------------------------------- frames travelling down the flat cables to the Jetson
  const J = ['brd_J3', 'brd_J4'].map((n) => byName[n].p.ctr);
  const camC = ['mira0_fpc_conn', 'mira1_fpc_conn'].map((n) => byName[n].p.ctr);
  const cable = ['fpc_J3', 'fpc_J4'].map((n) => byName[n].p.ctr);
  const soc = byName.jetson_soc.p.ctr;
  const paths = camC.map((c, i) => new THREE.CatmullRomCurve3([new THREE.Vector3(...c), new THREE.Vector3(...cable[i]), new THREE.Vector3(...J[i]),
    new THREE.Vector3(soc[0] + 0.02, (J[i][1] + soc[1]) / 2, J[i][2] * 0.5), new THREE.Vector3(soc[0], soc[1] - 0.004, soc[2])]));
  const NP = 5;
  const pulses = paths.map((_, i) => {
    const m = new THREE.InstancedMesh(new THREE.SphereGeometry(0.0016, 10, 8), new THREE.MeshBasicMaterial({color: new THREE.Color(CAMCOL[i]).lerp(new THREE.Color('#ffffff'), 0.3)}), NP);
    m.frustumCulled = false;
    root.add(m);
    return m;
  });

  // ---------------------------------------------------------------- heat leaving the fins
  const NH = 120;
  const heat = new THREE.InstancedMesh(new THREE.BoxGeometry(0.0012, 0.006, 0.0012), new THREE.MeshBasicMaterial({transparent: true, opacity: 0.7, depthWrite: false}), NH);
  heat.frustumCulled = false;
  heat.instanceColor = new THREE.InstancedBufferAttribute(new Float32Array(NH * 3), 3);
  root.add(heat);
  const lidP = byName.lid.p.ctr;
  const hseed = [...Array(NH)].map((_, i) => ({s: (i * 0.618034) % 1, x: (((i * 0.3819) % 1) - 0.5) * 0.09, z: (((i * 0.7548) % 1) - 0.5) * 0.08}));
  const M4 = new THREE.Matrix4(), Q = new THREE.Quaternion(), V = new THREE.Vector3(), SC = new THREE.Vector3(1, 1, 1);
  const hot = new THREE.Color(ACCENT), cool = new THREE.Color('#f2c38a'), tmpc = new THREE.Color();

  const bezels = parts.filter((r) => r.p.m === 'accent' && /bezel/.test(r.p.n));
  const setFade = (rec, a) => {
    if (Math.abs(rec.vis - a) < 0.002) return;
    rec.vis = a;
    const m = rec.mat;
    m.transparent = rec.wasT || a < 0.999;
    m.opacity = rec.base * a;
    m.depthWrite = a > 0.5 && !rec.wasT;
    rec.mesh.visible = a > 0.01;
    rec.mesh.castShadow = a > 0.6 && !/window|lens|fpc/.test(rec.p.m);
  };

  /**
   * s: {k explode 0..1, lid 0..1, body 0..1, mount 0..1, iso group or null, foot, sigOn, heatOn 0..1,
   *     fl: flight(), th: thermal(), dist: metres flown, trig: [s since each recent trigger], T}
   */
  function update(s) {
    for (const rec of parts) {
      const p = rec.p;
      rec.mesh.position.set(p.e[0] * s.k, p.e[1] * s.k, p.e[2] * s.k);
      let a = 1;
      if (isLid(p.n)) a = s.lid;
      else if (p.g === 'Enclosure') a = s.body;
      else if (p.g === 'Mount' || p.g === 'Drone') a = s.mount;
      if (s.iso && p.g !== s.iso) a = Math.min(a, p.g === 'Drone' ? 0 : 0.06);
      setFade(rec, a);
    }
    face.position.y = faceY + carrier.p.e[1] * s.k;
    face.material.opacity = carrier.vis;
    face.visible = carrier.vis > 0.01;

    // field, swath, mist, footprints
    const fo = s.foot * (1 - s.k);
    optics.visible = fo > 0.01;
    const since = s.trig.length ? s.trig[0] : 9;
    const flash = Math.exp(-since * 9);
    cones.forEach((c) => {
      c.m.material.opacity = fo * (0.05 + 0.22 * flash);
      c.lines.material.opacity = fo * (0.5 + 0.5 * flash);
    });
    for (const r of bezels) r.mat.emissiveIntensity = 1.4 * flash * (1 - s.k);
    farmyard.update(s);
    sprayer.update(s.plane ?? 0, s.T);
    {
      const scale = GROUND_D / s.fl.h;                                  // metres on the field -> metres in the drawing
      gtex.repeat.set(GL / (20.48 * scale), GW / (15.36 * scale));
      gtex.offset.set(s.dist / 20.48 - gtex.repeat.x / 2, 0.5 - gtex.repeat.y / 2);
      const boomX = gx + BOOM_DX;
      sctx.clearRect(0, 0, NC, 4);
      for (let i = 0; i < NC; i++) {
        const x = gx - GL / 2 + ((i + 0.5) / NC) * GL;
        if (x > boomX) continue;                                         // the boom has not reached this ground yet
        const st = sprayAt(s.dist - (boomX - x) / scale);
        if (!st.onField) continue;
        sctx.fillStyle = st.spraying ? 'rgba(40,150,255,0.30)' : 'rgba(255,70,50,0.75)';
        sctx.fillRect(i, 0, 1, 4);
      }
      stex.needsUpdate = true;
      swathMesh.scale.set(1, Math.min(GW, SWATH * scale), 1);
      swathMesh.material.opacity = 1;
      const now = sprayAt(s.dist);
      const half = Math.min(GW, SWATH * scale) / 2;
      mseed.forEach((d, i) => {
        const u = (d.u + s.T * 1.6) % 1;
        if (now.spraying && (s.plane ?? 0) > 0.05) {
          V.set(boomX + d.x * 0.08 - u * 0.25, sprayer.boomY - u * (sprayer.boomY - groundY), d.z * (1.7 + u * (half * 2 - 1.7)));
          const k = (1 - u * 0.5) * (s.plane ?? 0);
          M4.compose(V, Q.identity(), SC.set(k, k, k));
        } else M4.makeScale(0, 0, 0);
        mist.setMatrixAt(i, M4);
      });
      mist.instanceMatrix.needsUpdate = true;
      const vg = s.fl.v * scale;
      stamps.forEach((set, i) => {
        const age = s.trig[i];
        set.forEach((l) => {
          if (age === undefined) { l.material.opacity = 0; return; }
          const dx = -vg * age;
          l.position.x = dx;
          const edge = 1 - Math.min(1, Math.max(0, (-dx - GL * 0.3) / (GL * 0.15)));
          l.material.opacity = fo * edge * (i === 0 ? 1 : 0.5);
        });
      });
    }

    // frames on the cables, 5x slower than the real read-out so the eye can follow them
    pulses.forEach((m, i) => {
      const dur = s.fl.read * 5 + 0.12;
      let any = false;
      for (let j = 0; j < NP; j++) {
        const u = (since - j * 0.035) / dur;
        if (s.sigOn > 0.01 && u > 0 && u < 1) {
          paths[i].getPoint(u, V);
          V.y += carrier.p.e[1] * s.k * Math.min(1, u * 2.2);
          const k = (1 - j / NP) * s.sigOn;
          M4.compose(V, Q.identity(), SC.set(k, k, k));
          any = true;
        } else M4.makeScale(0, 0, 0);
        m.setMatrixAt(j, M4);
      }
      m.visible = any;
      m.instanceMatrix.needsUpdate = true;
    });

    // heat rising off the fins; faster and thinner when the downwash carries it away
    heat.visible = s.heatOn > 0.01;
    if (heat.visible) {
      const yTop = lidP[1] + 0.006 + byName.lid.p.e[1] * s.k;
      const rate = 0.35 + s.th.air * 0.08;
      hseed.forEach((d, i) => {
        const u = (d.s + s.T * rate * (0.8 + 0.4 * ((i * 0.37) % 1))) % 1;
        V.set(lidP[0] + d.x, yTop + u * 0.05, lidP[2] + d.z + Math.sin(u * 9 + i) * 0.002);
        const f = Math.min(1, u * 6) * (1 - u) * s.heatOn * Math.min(1.4, s.th.rise / 14);
        M4.compose(V, Q.identity(), SC.set(f, f * 1.2, f));
        heat.setMatrixAt(i, M4);
        heat.setColorAt(i, tmpc.copy(hot).lerp(cool, u));
      });
      heat.instanceMatrix.needsUpdate = true;
      heat.instanceColor.needsUpdate = true;
    }
  }
  const anchor = (name, k = 0) => {
    const r = byName[name];
    return [r.p.ctr[0] + r.p.e[0] * k, r.p.ctr[1] + r.p.e[1] * k, r.p.ctr[2] + r.p.e[2] * k];
  };
  return {root, parts, byName, update, lenses, groundY, anchor, sprayer};
}
