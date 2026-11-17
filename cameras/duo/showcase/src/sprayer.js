// An agricultural spray drone for scale: hexacopter, about 2.2 m across the rotors, 20 L tank, landing skids
// and a nozzle boom. The Duo clamps to the front crossbar of the skids. Built from primitives; an illustration of
// the class of aircraft, not a model of any real one. Axes: x forward, y up, z to the right.
import * as THREE from 'three';

export function createSprayer(tubeY, cx) {
  const g = new THREE.Group();
  const mats = [];
  const M = (o) => { const m = new THREE.MeshStandardMaterial({roughness: 0.5, metalness: 0.1, envMapIntensity: 0.7, ...o}); mats.push(m); return m; };
  const shell = M({color: new THREE.Color('#9aa4ad')});
  const carbon = M({color: new THREE.Color('#1a1c1f'), roughness: 0.35, metalness: 0.3});
  const tankM = M({color: new THREE.Color('#d9dee2'), roughness: 0.3, transparent: true, opacity: 0.85});
  const accent = M({color: new THREE.Color('#ff6b2c'), roughness: 0.4});
  const add = (geo, mat, x, y, z) => { const m = new THREE.Mesh(geo, mat); m.position.set(x, y, z); g.add(m); return m; };

  const hubY = tubeY + 0.42;
  // centre body and canopy
  add(new THREE.BoxGeometry(0.46, 0.12, 0.46), shell, cx, hubY, 0);
  const canopy = add(new THREE.SphereGeometry(0.26, 32, 16, 0, Math.PI * 2, 0, Math.PI / 2), shell, cx, hubY + 0.06, 0);
  canopy.scale.set(1, 0.45, 1);
  add(new THREE.BoxGeometry(0.47, 0.02, 0.47), accent, cx, hubY - 0.05, 0);
  // tank under the body
  const tank = add(new THREE.CylinderGeometry(0.17, 0.15, 0.3, 28), tankM, cx, hubY - 0.21, 0);
  tank.scale.z = 1.25;
  // six arms, motors and rotors
  const rotors = [];
  const discM = new THREE.MeshBasicMaterial({color: '#9fb4c8', transparent: true, opacity: 0.12, side: THREE.DoubleSide, depthWrite: false});
  mats.push(discM);
  for (let k = 0; k < 6; k++) {
    const a = Math.PI / 6 + (k * Math.PI) / 3, R = 0.86;
    const ax = cx + Math.cos(a) * R, az = Math.sin(a) * R;
    const arm = add(new THREE.CylinderGeometry(0.022, 0.026, R - 0.2, 12), carbon, cx + Math.cos(a) * (R / 2 + 0.1), hubY + 0.01, Math.sin(a) * (R / 2 + 0.1));
    arm.rotation.z = Math.PI / 2;
    arm.rotation.y = -a;
    add(new THREE.CylinderGeometry(0.05, 0.05, 0.07, 18), carbon, ax, hubY + 0.04, az);
    const rotor = new THREE.Group();
    rotor.position.set(ax, hubY + 0.09, az);
    for (const s of [1, -1]) {
      const b = new THREE.Mesh(new THREE.BoxGeometry(0.36, 0.006, 0.05), carbon);
      b.position.x = s * 0.18;
      rotor.add(b);
    }
    g.add(rotor);
    rotors.push(rotor);
    const disc = add(new THREE.CircleGeometry(0.38, 40), discM, ax, hubY + 0.088, az);
    disc.rotation.x = -Math.PI / 2;
    // a nozzle under each rear motor
    if (Math.cos(a) < 0) add(new THREE.ConeGeometry(0.015, 0.04, 10), accent, ax, hubY - 0.03, az);
  }
  // landing skids: legs, two skid tubes along x, crossbars along z (the Duo clamps to the front one)
  const legY0 = tubeY - 0.16, legY1 = hubY - 0.05;
  for (const sz of [-0.36, 0.36]) {
    add(new THREE.CylinderGeometry(0.014, 0.014, 0.9, 10), carbon, cx - 0.05, legY0, sz).rotation.z = Math.PI / 2;
    for (const sx of [-0.22, 0.16]) {
      const leg = add(new THREE.CylinderGeometry(0.014, 0.014, legY1 - legY0, 10), carbon, cx + sx, (legY0 + legY1) / 2, sz * 0.82);
      leg.rotation.x = Math.sign(sz) * 0.2;
    }
  }
  const bar = add(new THREE.CylinderGeometry(0.0125, 0.0125, 0.74, 12), carbon, cx, tubeY, 0);
  bar.rotation.x = Math.PI / 2;
  add(new THREE.CylinderGeometry(0.0125, 0.0125, 0.74, 12), carbon, cx - 0.3, tubeY, 0).rotation.x = Math.PI / 2;
  // spray boom with nozzles, behind the camera (the camera looks at ground already sprayed... the boom is ahead)
  const boomX = cx + 0.12, boomY = hubY - 0.32;
  add(new THREE.CylinderGeometry(0.01, 0.01, 1.7, 10), carbon, boomX, boomY, 0).rotation.x = Math.PI / 2;
  const nozzles = [];
  for (let z = -0.8; z <= 0.801; z += 0.2) {
    add(new THREE.ConeGeometry(0.012, 0.03, 10), accent, boomX, boomY - 0.02, z).rotation.x = Math.PI;
    nozzles.push([boomX, boomY - 0.035, z]);
  }
  for (const m of mats) { m.userData.base = m.opacity; m.transparent = true; }
  g.traverse((o) => { if (o.isMesh) o.castShadow = true; });
  let vis = 1;
  return {
    group: g, nozzles, boomX, boomY,
    label: [cx + 0.6, hubY + 0.1, -0.5],
    update(a, T) {
      if (Math.abs(a - vis) > 0.002) {
        vis = a;
        for (const m of mats) { m.opacity = m.userData.base * a; m.depthWrite = a > 0.99 && m !== discM; }
      }
      g.visible = a > 0.01;
      if (g.visible) rotors.forEach((r, i) => (r.rotation.y = T * 60 * (i % 2 ? 1 : -1)));
    },
  };
}
