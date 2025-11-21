// Lightweight SPA: main scene (DNA helix) + per-module canvas renderers
import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.152.2/build/three.module.js';
import { OrbitControls } from 'https://cdn.jsdelivr.net/npm/three@0.152.2/examples/jsm/controls/OrbitControls.js';

const container = document.getElementById('canvas-container');
const panel = document.getElementById('module-panel');
const moduleTitle = document.getElementById('module-title');
const moduleInfo = document.getElementById('module-info');
const openDemo = document.getElementById('open-demo');
const closePanel = document.getElementById('close-panel');

let renderer, scene, camera, controls, raycaster;
let helixGroup;

function initMain() {
  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setSize(container.clientWidth, container.clientHeight);
  container.appendChild(renderer.domElement);

  scene = new THREE.Scene();
  camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 2000);
  camera.position.set(0, 30, 90);

  controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.06;
  controls.autoRotate = false;

  scene.add(new THREE.AmbientLight(0x88f0ff, 0.6));
  const dir = new THREE.DirectionalLight(0x88ffb3, 0.8);
  dir.position.set(1, 2, 3);
  scene.add(dir);

  raycaster = new THREE.Raycaster();

  helixGroup = new THREE.Group();
  scene.add(helixGroup);

  createHelix(helixGroup);

  window.addEventListener('resize', onWindowResize);
  renderer.domElement.addEventListener('pointerdown', onPointerDown);

  animate();
}

function onWindowResize() {
  const w = container.clientWidth;
  const h = container.clientHeight;
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
  renderer.setSize(w, h);
}

function animate(time) {
  requestAnimationFrame(animate);
  helixGroup.rotation.y += 0.0025;
  controls.update();
  renderer.render(scene, camera);
}

// Minimal helix curve
class HelixCurve extends THREE.Curve {
  constructor(radius = 8, turns = 6, pitch = 3) {
    super();
    this.radius = radius;
    this.turns = turns;
    this.pitch = pitch;
  }
  getPoint(t) {
    const theta = t * Math.PI * 2 * this.turns;
    const x = Math.cos(theta) * this.radius;
    const y = (t - 0.5) * this.turns * this.pitch * 2;
    const z = Math.sin(theta) * this.radius;
    return new THREE.Vector3(x, y, z);
  }
}

function createHelix(parent) {
  const helixTurns = 6;
  const curveA = new HelixCurve(7, helixTurns, 3);
  const curveB = new HelixCurve(5.6, helixTurns, 3);

  const matA = new THREE.MeshStandardMaterial({ color: 0x00b3ff, metalness: 0.3, emissive: 0x003d4d });
  const matB = new THREE.MeshStandardMaterial({ color: 0x00ff9f, metalness: 0.2, emissive: 0x002d1f });

  const tubeA = new THREE.TubeGeometry(curveA, 400, 0.55, 8, false);
  const meshA = new THREE.Mesh(tubeA, matA);
  parent.add(meshA);

  const tubeB = new THREE.TubeGeometry(curveB, 400, 0.55, 8, false);
  const meshB = new THREE.Mesh(tubeB, matB);
  parent.add(meshB);

  // base pairs (connecting rods) and hotspots
  const hotspotPositions = [];
  for (let i = 0; i < 36; i++) {
    const t = i / 36;
    const pA = curveA.getPoint(t);
    const pB = curveB.getPoint(t);
    const mid = new THREE.Vector3().addVectors(pA, pB).multiplyScalar(0.5);

    // connector
    const dir = new THREE.Vector3().subVectors(pB, pA);
    const length = dir.length();
    dir.normalize();
    const cylGeom = new THREE.CylinderGeometry(0.12, 0.12, length, 6);
    const cyl = new THREE.Mesh(cylGeom, new THREE.MeshStandardMaterial({ color: 0x80d7ff }));
    cyl.position.copy(mid);
    cyl.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir);
    parent.add(cyl);

    // hotspot at midpoints for interactions
    if (i % 9 === 0) {
      const sphere = new THREE.Mesh(new THREE.SphereGeometry(0.9, 12, 12), new THREE.MeshStandardMaterial({ color: 0x00ff9f, emissive: 0x00ff9f, emissiveIntensity: 0.6 }));
      sphere.position.copy(mid);
      sphere.userData = { module: pickModule(i) };
      parent.add(sphere);
      hotspotPositions.push(sphere.position.clone());
    }
  }

  // subtle glow: a faint rim
  const ring = new THREE.Mesh(new THREE.TorusGeometry(18, 0.6, 8, 120), new THREE.MeshBasicMaterial({ color: 0x002a33, opacity: 0.06, transparent: true }));
  ring.rotation.x = Math.PI / 2.4;
  ring.position.y = -2;
  parent.add(ring);
}

function pickModule(i) {
  const modules = ['Input', 'Processing', 'Output', 'Error Handling', 'Demo Notebook'];
  return modules[(i / 9) % modules.length | 0];
}

function onPointerDown(event) {
  const rect = renderer.domElement.getBoundingClientRect();
  const x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
  const y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
  raycaster.setFromCamera({ x, y }, camera);
  const intersects = raycaster.intersectObjects(helixGroup.children, true);
  for (const hit of intersects) {
    if (hit.object && hit.object.userData && hit.object.userData.module) {
      const module = hit.object.userData.module;
      openModulePanel(module);
      return;
    }
  }
}

// Module panel + module-canvas renderer
let moduleRenderer, moduleScene, moduleCam, moduleControls;
function openModulePanel(module) {
  moduleTitle.textContent = module;
  moduleInfo.textContent = `Loading ${module} visualization...`;
  panel.classList.remove('hidden');
  createModuleCanvas(module);
}

function closeModulePanel() {
  panel.classList.add('hidden');
  disposeModuleRenderer();
}

function createModuleCanvas(module) {
  const canvas = document.getElementById('module-canvas');
  disposeModuleRenderer();
  moduleRenderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
  moduleRenderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  moduleRenderer.setSize(canvas.clientWidth, canvas.clientHeight, false);

  moduleScene = new THREE.Scene();
  moduleCam = new THREE.PerspectiveCamera(40, canvas.clientWidth / canvas.clientHeight, 0.1, 1000);
  moduleCam.position.set(0, 10, 30);
  moduleControls = new OrbitControls(moduleCam, moduleRenderer.domElement);
  moduleControls.enableDamping = true;

  moduleScene.add(new THREE.AmbientLight(0x88f0ff, 0.6));
  const d = new THREE.DirectionalLight(0x88ffb3, 0.6);
  d.position.set(1, 2, 3);
  moduleScene.add(d);

  // route to one of the module visualizers
  if (module === 'Input') renderInputModule(moduleScene);
  else if (module === 'Processing') renderProcessingModule(moduleScene);
  else if (module === 'Output') renderOutputModule(moduleScene);
  else if (module === 'Error Handling') renderErrorModule(moduleScene);
  else renderDemoModule(moduleScene);

  (function loop() {
    if (!moduleRenderer) return;
    requestAnimationFrame(loop);
    moduleControls.update();
    moduleRenderer.render(moduleScene, moduleCam);
  })();
}

function disposeModuleRenderer() {
  if (moduleRenderer) {
    try { moduleRenderer.forceContextLoss(); } catch (e) {}
  }
  moduleRenderer = null; moduleScene = null; moduleCam = null; moduleControls = null;
}

// Module visualizers
function renderInputModule(scene) {
  // represent a FASTA file: stacked colored blocks
  const group = new THREE.Group();
  const colors = [0x00b3ff, 0x00ff9f, 0x6fb3ff, 0x55e6a6];
  for (let i = 0; i < 20; i++) {
    const w = Math.random() * 8 + 4;
    const h = 1.6;
    const g = new THREE.BoxGeometry(w, h, 1.5);
    const m = new THREE.MeshStandardMaterial({ color: colors[i % colors.length], roughness: 0.4, metalness: 0.1 });
    const mesh = new THREE.Mesh(g, m);
    mesh.position.set((i - 10) * 3.2, (i % 2) * 1.2 - 2, 0);
    group.add(mesh);
  }
  scene.add(group);
  moduleInfo.textContent = 'Input: FASTA sequences rendered as stacked blocks. Rotate/zoom to explore.';
}

function renderProcessingModule(scene) {
  // simple BLAST alignment arcs between sequences
  const group = new THREE.Group();
  const ptsA = [], ptsB = [];
  for (let i = 0; i < 8; i++) ptsA.push(new THREE.Vector3(-20 + i * 6, -4, 0));
  for (let j = 0; j < 8; j++) ptsB.push(new THREE.Vector3(-20 + j * 6, 6, 0));
  const matLine = new THREE.LineBasicMaterial({ color: 0x00b3ff, linewidth: 2 });
  for (let i = 0; i < 8; i++) {
    const pA = ptsA[i]; const pB = ptsB[(i + 2) % 8];
    const curve = new THREE.CatmullRomCurve3([pA, new THREE.Vector3((pA.x + pB.x) / 2, 2, -6), pB]);
    const geom = new THREE.TubeGeometry(curve, 40, 0.18, 8, false);
    const mesh = new THREE.Mesh(geom, new THREE.MeshStandardMaterial({ color: 0x3fd8ff, emissive: 0x003a46 }));
    group.add(mesh);
  }
  scene.add(group);
  moduleInfo.textContent = 'Processing: BLAST-like alignments shown as curved arcs between sequences.';
}

function renderOutputModule(scene) {
  // 3D bar chart for antibiotic class counts
  const group = new THREE.Group();
  const classes = ['Beta-lactam','Macrolide','Tetracycline','Aminoglycoside','Sulfonamide'];
  for (let i = 0; i < classes.length; i++) {
    const val = Math.random() * 12 + 2;
    const geo = new THREE.BoxGeometry(2.2, val, 2.2);
    const mat = new THREE.MeshStandardMaterial({ color: 0x00ff9f, roughness: 0.35 });
    const bar = new THREE.Mesh(geo, mat);
    bar.position.set((i - 2) * 4.5, val / 2 - 2, 0);
    group.add(bar);
  }
  scene.add(group);
  moduleInfo.innerHTML = '<strong>Output:</strong> sample counts by antibiotic class. Use orbit controls to inspect.';
}

function renderErrorModule(scene) {
  const geo = new THREE.SphereGeometry(6, 40, 32);
  const mat = new THREE.MeshStandardMaterial({ color: 0xff3860, emissive: 0x440000, metalness: 0.2 });
  const s = new THREE.Mesh(geo, mat);
  scene.add(s);
  moduleInfo.textContent = 'Error Handling: illustrative alert bubble. Shows how the pipeline surfaces errors and logs.';
}

function renderDemoModule(scene) {
  // small sequence of steps as boxes animated
  const root = new THREE.Group();
  for (let i = 0; i < 5; i++) {
    const geo = new THREE.BoxGeometry(5, 2.2, 1.8);
    const mat = new THREE.MeshStandardMaterial({ color: i % 2 ? 0x6fb3ff : 0x00ff9f, roughness: 0.4 });
    const m = new THREE.Mesh(geo, mat);
    m.position.set((i - 2) * 6.5, 0, 0);
    root.add(m);
  }
  scene.add(root);
  moduleInfo.textContent = 'Demo Notebook: step-by-step pipeline stages. Inspect each stage in 3D.';
}

// UI wiring
openDemo.addEventListener('click', () => openModulePanel('Demo Notebook'));
closePanel.addEventListener('click', closeModulePanel);

initMain();
