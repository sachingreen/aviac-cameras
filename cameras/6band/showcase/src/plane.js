// A small fixed-wing survey drone for scale: 1.6 m span, high wing, V-tail, pusher prop. The 6B hangs in a belly
// bay on its quick-release plate. Built from primitives here; it is an illustration, not a model of a real aircraft.
// Axes as the rest of the scene: x forward (direction of flight), y up, z to the right wing.
import * as THREE from 'three';

export function createPlane(bellyY, cx) {
  const g = new THREE.Group();
  const mats = [];
  const M = (o) => { const m = new THREE.MeshStandardMaterial({roughness: 0.42, metalness: 0.08, envMapIntensity: 0.9, ...o}); mats.push(m); return m; };
  const skin = M({color: new THREE.Color('#8f9aa5'), roughness: 0.55, envMapIntensity: 0.55});
  const dark = M({color: new THREE.Color('#1b1e22'), roughness: 0.35, metalness: 0.4});
  const accent = M({color: new THREE.Color('#ff6b2c'), roughness: 0.4, metalness: 0.2});
  const glass = M({color: new THREE.Color('#0d1a26'), roughness: 0.08, metalness: 0.6, envMapIntensity: 1.6});

  const R = 0.085, axisY = bellyY + R - 0.004;
  // fuselage: a lathe profile laid along x
  const prof = [[0, 0.62], [0.03, 0.6], [0.058, 0.55], [0.075, 0.47], [0.084, 0.36], [0.085, 0.1], [0.08, -0.2], [0.062, -0.45], [0.04, -0.66], [0.026, -0.78], [0, -0.8]]
    .map(([r, x]) => new THREE.Vector2(r, x));
  const fus = new THREE.Mesh(new THREE.LatheGeometry(prof, 48), skin);
  fus.rotation.z = -Math.PI / 2;                       // lathe axis (y) -> x
  fus.position.set(cx, axisY, 0);
  g.add(fus);
  // nose sensor window and a dark belly fairing around the camera bay
  const nose = new THREE.Mesh(new THREE.SphereGeometry(0.032, 24, 16, 0, Math.PI * 2, 0, Math.PI / 2), glass);
  nose.rotation.z = -Math.PI / 2;
  nose.position.set(cx + 0.6, axisY, 0);
  g.add(nose);
  const bay = new THREE.Mesh(new THREE.BoxGeometry(0.2, 0.012, 0.13), dark);
  bay.position.set(cx, bellyY + 0.002, 0);
  g.add(bay);

  // wings: tapered planform, extruded and bevelled, small dihedral
  const wingShape = new THREE.Shape();
  wingShape.moveTo(0.24, 0); wingShape.lineTo(0.18, 0.8); wingShape.lineTo(0.07, 0.8); wingShape.lineTo(0, 0); wingShape.closePath();
  const wingGeo = new THREE.ExtrudeGeometry(wingShape, {depth: 0.012, bevelEnabled: true, bevelThickness: 0.007, bevelSize: 0.008, bevelSegments: 3});
  wingGeo.rotateX(Math.PI / 2);                         // planform in x/z, thickness in y
  const wingY = axisY + R * 0.78;
  for (const side of [1, -1]) {
    const w = new THREE.Mesh(wingGeo, skin);
    w.scale.z = side;
    w.position.set(cx - 0.12, wingY, 0);
    w.rotation.x = side * -0.05;
    g.add(w);
    // orange tip band and a winglet
    const band = new THREE.Mesh(new THREE.BoxGeometry(0.15, 0.03, 0.05), accent);
    band.position.set(cx - 0.12 + 0.125, wingY + 0.055, side * 0.73);
    band.scale.y = 0.6;
    g.add(band);
    const tip = new THREE.Mesh(new THREE.BoxGeometry(0.12, 0.07, 0.008), skin);
    tip.position.set(cx - 0.12 + 0.125, wingY + 0.095, side * 0.805);
    g.add(tip);
  }
  // nav lights: red to the left, green to the right, white strobe on the tail
  const light = (col, x, y, z) => {
    const m = new THREE.MeshBasicMaterial({color: new THREE.Color(col).multiplyScalar(3), transparent: true});
    mats.push(m);
    const s = new THREE.Mesh(new THREE.SphereGeometry(0.009, 12, 8), m);
    s.position.set(x, y, z);
    g.add(s);
    return m;
  };
  const navR = light('#ff2a2a', cx - 0.12 + 0.2, wingY + 0.12, -0.805);
  const navG = light('#2aff6a', cx - 0.12 + 0.2, wingY + 0.12, 0.805);
  const strobe = light('#ffffff', cx - 0.8, axisY + 0.02, 0);

  // V-tail
  const finShape = new THREE.Shape();
  finShape.moveTo(0, 0); finShape.lineTo(0.16, 0); finShape.lineTo(0.09, 0.3); finShape.lineTo(0.02, 0.3); finShape.closePath();
  const finGeo = new THREE.ExtrudeGeometry(finShape, {depth: 0.008, bevelEnabled: true, bevelThickness: 0.004, bevelSize: 0.004, bevelSegments: 2});
  for (const side of [1, -1]) {
    const f = new THREE.Mesh(finGeo, skin);
    f.position.set(cx - 0.74, axisY + 0.02, 0);
    f.rotation.x = side * 0.62;
    g.add(f);
  }
  // pusher prop: hub, two blades, a faint disc
  const hub = new THREE.Mesh(new THREE.ConeGeometry(0.022, 0.06, 20), dark);
  hub.rotation.z = Math.PI / 2;
  hub.position.set(cx - 0.84, axisY, 0);
  g.add(hub);
  const prop = new THREE.Group();
  prop.position.set(cx - 0.825, axisY, 0);
  for (const s of [1, -1]) {
    const b = new THREE.Mesh(new THREE.BoxGeometry(0.008, 0.17, 0.026), dark);
    b.position.y = s * 0.09;
    b.rotation.y = s * 0.3;
    prop.add(b);
  }
  g.add(prop);
  const discM = new THREE.MeshBasicMaterial({color: '#9fb4c8', transparent: true, opacity: 0.1, side: THREE.DoubleSide, depthWrite: false});
  mats.push(discM);
  const disc = new THREE.Mesh(new THREE.CircleGeometry(0.18, 40), discM);
  disc.rotation.y = Math.PI / 2;
  disc.position.set(cx - 0.826, axisY, 0);
  g.add(disc);

  for (const m of mats) { m.userData.base = m.opacity; m.transparent = true; }
  g.traverse((o) => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
  let vis = 1;
  return {
    group: g,
    wingTip: [cx + 0.02, wingY + 0.02, -0.6],
    tail: [cx - 0.7, axisY + 0.2, 0],
    update(a, T, flying) {
      if (Math.abs(a - vis) > 0.002) {
        vis = a;
        for (const m of mats) { m.opacity = m.userData.base * a; m.depthWrite = a > 0.99 && m !== discM; }
      }
      g.visible = a > 0.01;
      if (!g.visible) return;
      prop.rotation.x = flying ? T * 95 : prop.rotation.x;
      const blink = (T % 1.2) < 0.08 ? 1 : 0.15;
      navR.opacity = navG.opacity = a * (0.75 + 0.25 * Math.sin(T * 3));
      strobe.opacity = a * blink;
    },
  };
}
