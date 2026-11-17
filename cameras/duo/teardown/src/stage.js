// The stage: a pale studio, soft boxes for the dark parts to catch, a soft shadow, ambient occlusion.
// Pattern follows the teardown kit's example stages (elvarofficial/teardown, MIT).
import * as THREE from 'three';
import {EffectComposer} from 'three/addons/postprocessing/EffectComposer.js';
import {GTAOPass} from 'three/addons/postprocessing/GTAOPass.js';
import {OutputPass} from 'three/addons/postprocessing/OutputPass.js';
import {RenderPass} from 'three/addons/postprocessing/RenderPass.js';

export const BG = {top: '#f4f4f2', mid: '#ebebe8', low: '#e2e2de'};

export function createStage(canvas) {
  const renderer = new THREE.WebGLRenderer({canvas, antialias: false, preserveDrawingBuffer: true, powerPreference: 'high-performance'});
  renderer.toneMapping = THREE.NeutralToneMapping;
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.VSMShadowMap;
  const scene = new THREE.Scene();
  {
    const c = document.createElement('canvas');
    c.width = 4; c.height = 512;
    const g = c.getContext('2d');
    const gr = g.createLinearGradient(0, 0, 0, 512);
    gr.addColorStop(0, BG.top); gr.addColorStop(0.55, BG.mid); gr.addColorStop(1, BG.low);
    g.fillStyle = gr; g.fillRect(0, 0, 4, 512);
    const tex = new THREE.CanvasTexture(c);
    tex.colorSpace = THREE.SRGBColorSpace;
    scene.background = tex;
  }
  const camera = new THREE.PerspectiveCamera(24, 16 / 9, 0.02, 30);
  const composer = new EffectComposer(renderer, new THREE.WebGLRenderTarget(4, 4, {type: THREE.HalfFloatType, samples: 4}));
  composer.addPass(new RenderPass(scene, camera));
  const gtao = new GTAOPass(scene, camera, 4, 4);
  gtao.output = GTAOPass.OUTPUT.Default;
  gtao.blendIntensity = 0.8;
  gtao.updateGtaoMaterial({radius: 0.02, distanceExponent: 1.4, thickness: 0.6, scale: 1.0, samples: 16, distanceFallOff: 1.0, screenSpaceRadius: false});
  gtao.updatePdMaterial({lumaPhi: 10, depthPhi: 2, normalPhi: 3, radius: 6, rings: 2, samples: 16});
  composer.addPass(gtao);
  composer.addPass(new OutputPass());

  // studio: a big top box, two side strips, a low front strip
  {
    const env = new THREE.Scene();
    env.background = new THREE.Color('#dcdcd8');
    const box = (w, h, pos, k) => {
      const m = new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshBasicMaterial({color: new THREE.Color(1, 1, 1).multiplyScalar(k), side: THREE.DoubleSide}));
      m.position.copy(pos); m.lookAt(0, 0, 0); env.add(m);
    };
    box(12, 12, new THREE.Vector3(0, 14, 2), 2.8);
    box(3, 14, new THREE.Vector3(-12, 4, 6), 3.6);
    box(3, 14, new THREE.Vector3(12, 4, -4), 2.4);
    box(18, 2, new THREE.Vector3(0, -3, 14), 1.8);
    box(14, 3, new THREE.Vector3(2, -10, -6), 1.2);
    const pm = new THREE.PMREMGenerator(renderer);
    scene.environment = pm.fromScene(env, 0.02).texture;
    scene.environmentIntensity = 1.0;
    pm.dispose();
  }
  const sun = new THREE.DirectionalLight('#ffffff', 2.4);
  sun.position.set(-0.5, 1.4, 0.7);
  sun.castShadow = true;
  Object.assign(sun.shadow.camera, {left: -0.4, right: 0.4, top: 0.4, bottom: -0.4, near: 0.2, far: 4});
  sun.shadow.mapSize.set(2048, 2048);
  sun.shadow.radius = 10;
  sun.shadow.blurSamples = 16;
  sun.shadow.bias = -0.0004;
  sun.shadow.normalBias = 0.002;
  scene.add(sun, sun.target);
  scene.add(new THREE.HemisphereLight('#ffffff', '#d2d2ce', 0.75));
  const under = new THREE.DirectionalLight('#fff4e6', 0.9);       // lifts the underside, where the lenses are
  under.position.set(0.3, -1.0, 0.8);
  scene.add(under);

  const size = {w: 1600, h: 900};
  const resize = (w, h, pr) => {
    size.w = w; size.h = h;
    renderer.setPixelRatio(pr); renderer.setSize(w, h, false);
    composer.setPixelRatio(pr); composer.setSize(w, h);
    camera.aspect = w / h; camera.updateProjectionMatrix();
  };
  // cam: target, azimuth from +z toward +x, elevation, distance; sx/sy shift the picture on screen (CSS px)
  const frame = (cam) => {
    const {tx, ty, tz, az, el, d} = cam;
    sun.target.position.set(tx, ty, tz);
    sun.position.set(tx - 0.5, ty + 1.4, tz + 0.7);
    camera.position.set(tx + d * Math.cos(el) * Math.sin(az), ty + d * Math.sin(el), tz + d * Math.cos(el) * Math.cos(az));
    camera.lookAt(tx, ty, tz);
    camera.setViewOffset(size.w, size.h, -(cam.sx ?? 0), -(cam.sy ?? 0), size.w, size.h);
    camera.updateMatrixWorld();
    composer.render();
  };
  const pv = new THREE.Vector3();
  const project = (x, y, z) => {
    pv.set(x, y, z).project(camera);
    if (pv.z > 1) return null;
    return [(pv.x * 0.5 + 0.5) * size.w, (-pv.y * 0.5 + 0.5) * size.h];
  };
  const setQuality = ({samples, ao, shadow}) => {
    if (samples !== undefined) for (const t of [composer.renderTarget1, composer.renderTarget2]) { t.samples = samples; t.dispose(); }
    if (ao !== undefined) gtao.enabled = ao;
    if (shadow !== undefined) { sun.shadow.mapSize.set(shadow, shadow); sun.shadow.map?.dispose(); sun.shadow.map = null; }
  };
  return {renderer, scene, camera, composer, gtao, sun, resize, frame, project, size, setQuality};
}
