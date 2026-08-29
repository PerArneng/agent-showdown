import * as THREE from "three";
import type { ClientState, Renderer } from "../../interfaces/game/index.js";
import { ModelLoader, type ModelKey } from "./model-loader.js";
import { Terrain } from "./terrain.js";

const CAMERA_DISTANCE = 24;
const HOVER_HEIGHT = 0.45;
const BOLT_HOVER_HEIGHT = 0.55;

interface TreeInstance {
  readonly group: THREE.Group;
  readonly position: THREE.Vector3;
  readonly radius: number;
  currentOpacity: number;
  targetOpacity: number;
}

interface PlayerMeshInstance {
  readonly group: THREE.Group;
  readonly shadowMesh: THREE.Mesh;
  readonly runeRingGroup: THREE.Group;
  readonly healthBarGroup: THREE.Group;
  readonly healthFillMesh: THREE.Mesh;
  readonly skullMesh: THREE.Sprite;
  readonly beaconMesh: THREE.Mesh;
  modelGroup: THREE.Group | null;
  currentPos: THREE.Vector3;
  targetPos: THREE.Vector3;
  currentRotationY: number;
  targetRotationY: number;
  phase: number;
}

/**
 * Renders the game arena in Three.js as an isometric low-poly world.
 * Manages procedural faceted terrain, 3D animated player models, tree occlusion transparency,
 * firebolt projectiles, and spell particle effects.
 */
export class ThreeBoardRenderer implements Renderer {
  private readonly scene: THREE.Scene;
  private readonly camera: THREE.OrthographicCamera;
  private readonly renderer: THREE.WebGLRenderer;
  private readonly terrain: Terrain;
  private readonly modelLoader: ModelLoader;

  private terrainMesh: THREE.Mesh | null = null;
  private terrainGroup: THREE.Group;
  private readonly playersMap = new Map<string, PlayerMeshInstance>();
  private readonly trees: TreeInstance[] = [];

  private fireboltGroup: THREE.Group | null = null;
  private fireboltLight: THREE.PointLight | null = null;
  private explosionGroup: THREE.Group | null = null;

  private currentBoardWidth = 0;
  private currentBoardHeight = 0;
  private currentState: ClientState | null = null;

  private animationFrameId: number | null = null;
  private lastTime = 0;
  private isDisposed = false;

  constructor(
    private readonly canvas: HTMLCanvasElement,
    terrain: Terrain = new Terrain(),
    modelLoader: ModelLoader = new ModelLoader(),
  ) {
    this.terrain = terrain;
    this.modelLoader = modelLoader;

    // 1. Scene
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x131722);

    // 2. Camera: Isometric orthographic setup
    const aspect = canvas.clientWidth > 0 ? canvas.clientWidth / canvas.clientHeight : 1;
    const frustumSize = 10.5;
    this.camera = new THREE.OrthographicCamera(
      (-frustumSize * aspect) / 2,
      (frustumSize * aspect) / 2,
      frustumSize / 2,
      -frustumSize / 2,
      0.1,
      200,
    );
    // Classic isometric camera angle: 45 deg azimuth, ~35.26 deg elevation
    this.camera.position.set(CAMERA_DISTANCE, CAMERA_DISTANCE, CAMERA_DISTANCE);
    this.camera.lookAt(0, 0, 0);

    // 3. WebGL Renderer
    this.renderer = new THREE.WebGLRenderer({
      canvas,
      antialias: true,
      alpha: true,
      powerPreference: "high-performance",
    });
    this.renderer.setSize(canvas.width, canvas.height, false);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;

    // 4. Lighting: Warm sun, atmospheric sky bounce, and ambient fill
    this.setupLighting();

    // 5. Container groups
    this.terrainGroup = new THREE.Group();
    this.scene.add(this.terrainGroup);

    // 6. Asynchronously preload 3D models and build default scenery
    void this.initModels();

    // 7. Start render/animation loop
    this.startLoop();

    // 8. Handle canvas resize
    window.addEventListener("resize", this.handleResize);
  }

  private setupLighting(): void {
    // Warm sun light
    const sunLight = new THREE.DirectionalLight(0xfff5e6, 1.8);
    sunLight.position.set(16, 28, 12);
    sunLight.castShadow = true;
    sunLight.shadow.mapSize.width = 2048;
    sunLight.shadow.mapSize.height = 2048;
    sunLight.shadow.camera.near = 0.5;
    sunLight.shadow.camera.far = 80;
    const d = 12;
    sunLight.shadow.camera.left = -d;
    sunLight.shadow.camera.right = d;
    sunLight.shadow.camera.top = d;
    sunLight.shadow.camera.bottom = -d;
    sunLight.shadow.bias = -0.0005;
    this.scene.add(sunLight);

    // Secondary fill light from opposite angle
    const fillLight = new THREE.DirectionalLight(0x7692c8, 0.7);
    fillLight.position.set(-16, 15, -16);
    this.scene.add(fillLight);

    // Hemisphere sky/ground light
    const hemiLight = new THREE.HemisphereLight(0xcae8ff, 0x4a3b2c, 0.6);
    this.scene.add(hemiLight);

    // Ambient light
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.25);
    this.scene.add(ambientLight);
  }

  private async initModels(): Promise<void> {
    try {
      await this.modelLoader.loadAll();
      if (!this.isDisposed && this.currentState) {
        this.render(this.currentState);
      }
    } catch {
      // Model loading fallback handles placeholders gracefully
    }
  }

  render(state: ClientState): void {
    if (this.isDisposed) return;
    this.currentState = state;

    if (state.board === null) {
      this.clearBoard();
      return;
    }

    // Rebuild terrain and trees if board dimensions change
    if (
      this.currentBoardWidth !== state.board.width ||
      this.currentBoardHeight !== state.board.height
    ) {
      this.buildTerrainAndScenery(state.board.width, state.board.height);
      this.currentBoardWidth = state.board.width;
      this.currentBoardHeight = state.board.height;
    }

    // Update players
    this.updatePlayers(state);

    // Update spell and explosion effects
    this.updateEffects(state);
  }

  private clearBoard(): void {
    this.terrainGroup.clear();
    this.terrainMesh = null;
    for (const p of this.playersMap.values()) {
      this.scene.remove(p.group);
    }
    this.playersMap.clear();
    this.trees.length = 0;
    if (this.fireboltGroup) {
      this.scene.remove(this.fireboltGroup);
      this.fireboltGroup = null;
    }
    if (this.explosionGroup) {
      this.scene.remove(this.explosionGroup);
      this.explosionGroup = null;
    }
  }

  private buildTerrainAndScenery(width: number, height: number): void {
    this.terrainGroup.clear();
    this.trees.length = 0;

    // 1. Programmatic Low-Poly Terrain & Diorama Slab Geometry
    const geom = this.generateDioramaGeometry(width, height);
    const mat = new THREE.MeshStandardMaterial({
      vertexColors: true,
      flatShading: true,
      roughness: 0.88,
      metalness: 0.05,
    });

    this.terrainMesh = new THREE.Mesh(geom, mat);
    this.terrainMesh.receiveShadow = true;
    this.terrainMesh.castShadow = true;
    this.terrainGroup.add(this.terrainMesh);

    // 2. Subtle Tile Borders on the Ground
    const gridHelperGroup = this.generateGridLines(width, height);
    this.terrainGroup.add(gridHelperGroup);

    // 3. Place Low-Poly Trees along Scenic Border Outcroppings
    this.placeSceneryTrees(width, height);
  }

  /** Generates the complete 3D diorama geometry: top faceted grass and extruded earth slab. */
  private generateDioramaGeometry(width: number, height: number): THREE.BufferGeometry {
    const positions: number[] = [];
    const colors: number[] = [];
    const normals: number[] = [];

    const margin = 0.9;
    const subs = 2;
    const totalW = width + margin * 2;
    const totalH = height + margin * 2;
    const totalX = Math.round(totalW * subs);
    const totalZ = Math.round(totalH * subs);
    const halfW = totalW / 2;
    const halfH = totalH / 2;
    const stepX = totalW / totalX;
    const stepZ = totalH / totalZ;

    const baseGrassA = new THREE.Color(0x6fae3f);
    const baseGrassB = new THREE.Color(0x63a137);
    const baseGrassC = new THREE.Color(0x7cbc47);
    const baseGrassD = new THREE.Color(0x5a9530);
    const borderGrass = new THREE.Color(0x55902c);

    const getTopVertex = (
      ix: number,
      iz: number,
    ): { x: number; y: number; z: number; gx: number; gy: number; isBorder: boolean } => {
      const x = -halfW + ix * stepX;
      const z = -halfH + iz * stepZ;
      const y = this.terrain.getHeight(x, z);
      const isBorder = Math.abs(x) > width / 2 || Math.abs(z) > height / 2;
      const gx = Math.floor(x + width / 2);
      const gy = Math.floor(z + height / 2);
      return { x, y, z, gx, gy, isBorder };
    };

    // --- Top Surface Mesh ---
    for (let iz = 0; iz < totalZ; iz++) {
      for (let ix = 0; ix < totalX; ix++) {
        const v00 = getTopVertex(ix, iz);
        const v10 = getTopVertex(ix + 1, iz);
        const v11 = getTopVertex(ix + 1, iz + 1);
        const v01 = getTopVertex(ix, iz + 1);

        // Tile-based color variation for playable grid, darker meadow for border margin
        let faceColorA: THREE.Color;
        let faceColorB: THREE.Color;

        if (v00.isBorder || v11.isBorder) {
          faceColorA = (ix + iz) % 2 === 0 ? borderGrass : baseGrassB;
          faceColorB = (ix + iz) % 2 === 0 ? baseGrassB : borderGrass;
        } else {
          const tileSum = v00.gx + v00.gy;
          if (tileSum % 2 === 0) {
            faceColorA = (ix + iz) % 2 === 0 ? baseGrassA : baseGrassC;
            faceColorB = (ix + iz) % 2 === 0 ? baseGrassC : baseGrassA;
          } else {
            faceColorA = (ix + iz) % 2 === 0 ? baseGrassB : baseGrassD;
            faceColorB = (ix + iz) % 2 === 0 ? baseGrassD : baseGrassB;
          }
        }

        // Triangle 1: (v00, v01, v10)
        this.addTriangle(positions, colors, normals, v00, v01, v10, faceColorA);
        // Triangle 2: (v10, v01, v11)
        this.addTriangle(positions, colors, normals, v10, v01, v11, faceColorB);
      }
    }

    // --- Extruded Earth Slab Sides (North, South, East, West) ---
    const slabBottom = -1.2;
    const midTopsoil = -0.3;
    const midDeepSoil = -0.8;

    const topsoilColor = new THREE.Color(0x5b3f27);
    const deepSoilColor = new THREE.Color(0x7a5533);
    const rockColor = new THREE.Color(0x3c251a);

    // Helper to build a multi-layered faceted wall quad
    const buildWallQuad = (
      p1: { x: number; y: number; z: number },
      p2: { x: number; y: number; z: number },
    ) => {
      // 3 vertical layers
      const layer1_a = { x: p1.x, y: midTopsoil, z: p1.z };
      const layer1_b = { x: p2.x, y: midTopsoil, z: p2.z };
      const layer2_a = { x: p1.x, y: midDeepSoil, z: p1.z };
      const layer2_b = { x: p2.x, y: midDeepSoil, z: p2.z };
      const layer3_a = { x: p1.x, y: slabBottom, z: p1.z };
      const layer3_b = { x: p2.x, y: slabBottom, z: p2.z };

      // Topsoil layer
      this.addTriangle(positions, colors, normals, p1, layer1_a, p2, topsoilColor);
      this.addTriangle(positions, colors, normals, p2, layer1_a, layer1_b, topsoilColor);

      // Deep soil layer
      this.addTriangle(positions, colors, normals, layer1_a, layer2_a, layer1_b, deepSoilColor);
      this.addTriangle(positions, colors, normals, layer1_b, layer2_a, layer2_b, deepSoilColor);

      // Rock bedrock layer
      this.addTriangle(positions, colors, normals, layer2_a, layer3_a, layer2_b, rockColor);
      this.addTriangle(positions, colors, normals, layer2_b, layer3_a, layer3_b, rockColor);
    };

    // South wall (iz = totalZ, from left to right)
    for (let ix = 0; ix < totalX; ix++) {
      const p1 = getTopVertex(ix, totalZ);
      const p2 = getTopVertex(ix + 1, totalZ);
      buildWallQuad(p1, p2);
    }
    // East wall (ix = totalX, from top to bottom)
    for (let iz = 0; iz < totalZ; iz++) {
      const p1 = getTopVertex(totalX, iz);
      const p2 = getTopVertex(totalX, iz + 1);
      buildWallQuad(p2, p1);
    }
    // North wall (iz = 0, from right to left)
    for (let ix = 0; ix < totalX; ix++) {
      const p1 = getTopVertex(ix + 1, 0);
      const p2 = getTopVertex(ix, 0);
      buildWallQuad(p1, p2);
    }
    // West wall (ix = 0, from bottom to top)
    for (let iz = 0; iz < totalZ; iz++) {
      const p1 = getTopVertex(0, iz + 1);
      const p2 = getTopVertex(0, iz);
      buildWallQuad(p1, p2);
    }

    // --- Bottom Cap ---
    const bottomColor = new THREE.Color(0x281810);
    const b00 = { x: -halfW, y: slabBottom, z: -halfH };
    const b10 = { x: halfW, y: slabBottom, z: -halfH };
    const b11 = { x: halfW, y: slabBottom, z: halfH };
    const b01 = { x: -halfW, y: slabBottom, z: halfH };
    this.addTriangle(positions, colors, normals, b00, b10, b01, bottomColor);
    this.addTriangle(positions, colors, normals, b10, b11, b01, bottomColor);

    const bufferGeom = new THREE.BufferGeometry();
    bufferGeom.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
    bufferGeom.setAttribute("color", new THREE.Float32BufferAttribute(colors, 3));
    bufferGeom.setAttribute("normal", new THREE.Float32BufferAttribute(normals, 3));
    bufferGeom.computeVertexNormals();

    return bufferGeom;
  }

  private addTriangle(
    positions: number[],
    colors: number[],
    normals: number[],
    p1: { x: number; y: number; z: number },
    p2: { x: number; y: number; z: number },
    p3: { x: number; y: number; z: number },
    color: THREE.Color,
  ): void {
    positions.push(p1.x, p1.y, p1.z, p2.x, p2.y, p2.z, p3.x, p3.y, p3.z);
    for (let i = 0; i < 3; i++) {
      colors.push(color.r, color.g, color.b);
    }
    // Face normal
    const vA = new THREE.Vector3(p1.x, p1.y, p1.z);
    const vB = new THREE.Vector3(p2.x, p2.y, p2.z);
    const vC = new THREE.Vector3(p3.x, p3.y, p3.z);
    const cb = new THREE.Vector3().subVectors(vC, vB);
    const ab = new THREE.Vector3().subVectors(vA, vB);
    const faceNormal = cb.cross(ab).normalize();
    for (let i = 0; i < 3; i++) {
      normals.push(faceNormal.x, faceNormal.y, faceNormal.z);
    }
  }

  private generateGridLines(width: number, height: number): THREE.Group {
    const group = new THREE.Group();
    const halfW = width / 2;
    const halfH = height / 2;
    const points: THREE.Vector3[] = [];

    for (let x = 0; x <= width; x++) {
      const wx = -halfW + x;
      for (let z = 0; z < height; z++) {
        const wz1 = -halfH + z;
        const wz2 = -halfH + z + 1;
        const y1 = this.terrain.getHeight(wx, wz1) + 0.008;
        const y2 = this.terrain.getHeight(wx, wz2) + 0.008;
        points.push(new THREE.Vector3(wx, y1, wz1), new THREE.Vector3(wx, y2, wz2));
      }
    }

    for (let z = 0; z <= height; z++) {
      const wz = -halfH + z;
      for (let x = 0; x < width; x++) {
        const wx1 = -halfW + x;
        const wx2 = -halfW + x + 1;
        const y1 = this.terrain.getHeight(wx1, wz) + 0.008;
        const y2 = this.terrain.getHeight(wx2, wz) + 0.008;
        points.push(new THREE.Vector3(wx1, y1, wz), new THREE.Vector3(wx2, y2, wz));
      }
    }

    const lineGeom = new THREE.BufferGeometry().setFromPoints(points);
    const lineMat = new THREE.LineBasicMaterial({
      color: 0x2f7832,
      transparent: true,
      opacity: 0.35,
    });
    group.add(new THREE.LineSegments(lineGeom, lineMat));
    return group;
  }

  private placeSceneryTrees(width: number, height: number): void {
    const halfW = width / 2;
    const halfH = height / 2;

    // Positions for scenic trees along borders and corner mounds
    const treePositions: Array<{ x: number; z: number; type: "tree-1" | "tree-2"; scale: number }> =
      [
        { x: -halfW - 0.55, z: -halfH - 0.55, type: "tree-1", scale: 0.52 },
        { x: halfW + 0.55, z: -halfH - 0.55, type: "tree-2", scale: 0.55 },
        { x: -halfW - 0.55, z: halfH + 0.55, type: "tree-2", scale: 0.52 },
        { x: halfW + 0.55, z: halfH + 0.55, type: "tree-1", scale: 0.48 },
        { x: -halfW - 0.6, z: 0, type: "tree-2", scale: 0.45 },
        { x: halfW + 0.6, z: 0, type: "tree-1", scale: 0.47 },
        { x: 0, z: -halfH - 0.6, type: "tree-1", scale: 0.46 },
        { x: 0, z: halfH + 0.6, type: "tree-2", scale: 0.44 },
      ];

    for (const info of treePositions) {
      const model = this.modelLoader.instantiate(info.type);
      const groundY = this.terrain.getHeight(info.x, info.z);
      model.position.set(info.x, groundY, info.z);
      model.scale.setScalar(info.scale);
      model.rotation.y = Math.sin(info.x * 3 + info.z * 5) * Math.PI;

      this.terrainGroup.add(model);
      this.trees.push({
        group: model,
        position: new THREE.Vector3(info.x, groundY + 1.2, info.z),
        radius: 1.4 * info.scale,
        currentOpacity: 1.0,
        targetOpacity: 1.0,
      });
    }
  }

  private updatePlayers(state: ClientState): void {
    if (!state.board) return;
    const currentNames = new Set(state.players.map((p) => p.name));

    // Remove deleted players
    for (const [name, instance] of this.playersMap.entries()) {
      if (!currentNames.has(name)) {
        this.scene.remove(instance.group);
        this.playersMap.delete(name);
      }
    }

    // Add or update existing players
    for (let i = 0; i < state.players.length; i++) {
      const player = state.players[i]!;
      let instance = this.playersMap.get(player.name);

      if (!instance) {
        instance = this.createPlayerInstance(player.sprite, player.color, i);
        this.playersMap.set(player.name, instance);
        this.scene.add(instance.group);
      }

      const isDead = player.health <= 0;
      const isThinking = !isDead && state.thinking === player.name;

      // Handle smooth movement interpolation during move effect
      let gx = player.position.x;
      let gy = player.position.y;
      if (state.effect?.type === "move" && state.effect.player === player.name) {
        const from = state.effect.from;
        const to = state.effect.to;
        const p = state.effect.progress;
        gx = from.x + (to.x - from.x) * p;
        gy = from.y + (to.y - from.y) * p;

        // Facing direction of movement
        const dx = to.x - from.x;
        const dy = to.y - from.y;
        if (dx !== 0 || dy !== 0) {
          instance.targetRotationY = Math.atan2(dx, dy);
        }
      }

      // Convert grid position to 3D world position
      const world = this.terrain.gridToWorld(gx, gy, state.board.width, state.board.height);
      instance.targetPos.set(world.x, world.y, world.z);

      // Update active thinking aura ring and beacon
      instance.runeRingGroup.visible = isThinking;
      instance.beaconMesh.visible = isThinking;

      // Update dead state visuals (ghost opacity and skull)
      instance.skullMesh.visible = isDead;
      if (instance.modelGroup) {
        const targetModelOpacity = isDead ? 0.35 : 1.0;
        this.setObjectOpacity(instance.modelGroup, targetModelOpacity);
      }

      // Update mini health bar fill
      const healthRatio = Math.max(0, Math.min(1, player.health / 100));
      instance.healthFillMesh.scale.x = Math.max(0.001, healthRatio);
      instance.healthFillMesh.position.x = -0.3 + 0.3 * healthRatio;
      const hpColor = healthRatio > 0.5 ? 0x22c55e : healthRatio > 0.25 ? 0xeab308 : 0xef4444;
      (instance.healthFillMesh.material as THREE.MeshBasicMaterial).color.setHex(hpColor);
      instance.healthBarGroup.visible = !isDead;
    }
  }

  private createPlayerInstance(sprite: number, color: string, index: number): PlayerMeshInstance {
    const group = new THREE.Group();

    // 1. Shadow Decal on the Ground
    const shadowGeom = new THREE.CircleGeometry(0.36, 16);
    const shadowMat = new THREE.MeshBasicMaterial({
      color: 0x000000,
      transparent: true,
      opacity: 0.5,
      depthWrite: false,
    });
    const shadowMesh = new THREE.Mesh(shadowGeom, shadowMat);
    shadowMesh.rotation.x = -Math.PI / 2;
    shadowMesh.position.y = 0.015;
    group.add(shadowMesh);

    // 2. Active Thinking Rune Ring on Ground
    const runeRingGroup = new THREE.Group();
    runeRingGroup.position.y = 0.02;

    const ringGeom = new THREE.RingGeometry(0.48, 0.54, 24);
    const ringMat = new THREE.MeshBasicMaterial({
      color: 0xffd700,
      side: THREE.DoubleSide,
      transparent: true,
      opacity: 0.85,
      depthWrite: false,
    });
    const ringMesh = new THREE.Mesh(ringGeom, ringMat);
    ringMesh.rotation.x = -Math.PI / 2;
    runeRingGroup.add(ringMesh);

    const innerGlowGeom = new THREE.CircleGeometry(0.46, 16);
    const innerGlowMat = new THREE.MeshBasicMaterial({
      color: 0x4c8dff,
      transparent: true,
      opacity: 0.2,
      depthWrite: false,
    });
    const innerGlowMesh = new THREE.Mesh(innerGlowGeom, innerGlowMat);
    innerGlowMesh.rotation.x = -Math.PI / 2;
    runeRingGroup.add(innerGlowMesh);

    // Rune glyph points around ring
    for (let r = 0; r < 8; r++) {
      const angle = (r * Math.PI) / 4;
      const dotGeom = new THREE.CircleGeometry(0.025, 8);
      const dotMat = new THREE.MeshBasicMaterial({ color: 0xffffff });
      const dot = new THREE.Mesh(dotGeom, dotMat);
      dot.rotation.x = -Math.PI / 2;
      dot.position.set(Math.cos(angle) * 0.51, 0.001, Math.sin(angle) * 0.51);
      runeRingGroup.add(dot);
    }
    runeRingGroup.visible = false;
    group.add(runeRingGroup);

    // 3. 3D Model Instance from ModelLoader
    const modelKey: ModelKey = `robot-${(sprite % 4) + 1}` as ModelKey;
    const modelGroup = this.modelLoader.instantiate(modelKey);
    modelGroup.position.y = HOVER_HEIGHT;

    // Apply appropriate visual scale per robot
    const scaleFactor =
      modelKey === "robot-1"
        ? 0.55
        : modelKey === "robot-2"
          ? 0.7
          : modelKey === "robot-3"
            ? 0.7
            : 0.5;
    modelGroup.scale.setScalar(scaleFactor);
    group.add(modelGroup);

    // Player color accent base ring under the robot
    const accentGeom = new THREE.RingGeometry(0.25, 0.32, 16);
    const accentMat = new THREE.MeshBasicMaterial({
      color: new THREE.Color(color),
      side: THREE.DoubleSide,
      transparent: true,
      opacity: 0.6,
      depthWrite: false,
    });
    const accentMesh = new THREE.Mesh(accentGeom, accentMat);
    accentMesh.rotation.x = -Math.PI / 2;
    accentMesh.position.y = 0.018;
    group.add(accentMesh);

    // 4. Floating Beacon above Head (Thinking Indicator)
    const beaconGeom = new THREE.OctahedronGeometry(0.08, 0);
    const beaconMat = new THREE.MeshBasicMaterial({ color: 0xffd700 });
    const beaconMesh = new THREE.Mesh(beaconGeom, beaconMat);
    beaconMesh.position.y = HOVER_HEIGHT + 1.45;
    beaconMesh.visible = false;
    group.add(beaconMesh);

    // 5. Billboard Health Bar Group
    const healthBarGroup = new THREE.Group();
    healthBarGroup.position.y = HOVER_HEIGHT + 1.3;

    // Track
    const trackGeom = new THREE.PlaneGeometry(0.62, 0.08);
    const trackMat = new THREE.MeshBasicMaterial({
      color: 0x000000,
      transparent: true,
      opacity: 0.75,
      side: THREE.DoubleSide,
    });
    const trackMesh = new THREE.Mesh(trackGeom, trackMat);
    healthBarGroup.add(trackMesh);

    // Fill
    const fillGeom = new THREE.PlaneGeometry(0.6, 0.06);
    const fillMat = new THREE.MeshBasicMaterial({ color: 0x22c55e, side: THREE.DoubleSide });
    const healthFillMesh = new THREE.Mesh(fillGeom, fillMat);
    healthFillMesh.position.z = 0.001;
    healthBarGroup.add(healthFillMesh);
    group.add(healthBarGroup);

    // 6. Defeated Skull Indicator Sprite
    const canvas2d = document.createElement("canvas");
    canvas2d.width = 64;
    canvas2d.height = 64;
    const ctx = canvas2d.getContext("2d");
    if (ctx) {
      ctx.font = "40px sans-serif";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText("💀", 32, 32);
    }
    const texture = new THREE.CanvasTexture(canvas2d);
    const spriteMat = new THREE.SpriteMaterial({ map: texture, transparent: true });
    const skullMesh = new THREE.Sprite(spriteMat);
    skullMesh.scale.set(0.4, 0.4, 1);
    skullMesh.position.y = HOVER_HEIGHT + 1.1;
    skullMesh.visible = false;
    group.add(skullMesh);

    return {
      group,
      shadowMesh,
      runeRingGroup,
      healthBarGroup,
      healthFillMesh,
      skullMesh,
      beaconMesh,
      modelGroup,
      currentPos: new THREE.Vector3(0, 0, 0),
      targetPos: new THREE.Vector3(0, 0, 0),
      currentRotationY: 0,
      targetRotationY: 0,
      phase: index * 1.5,
    };
  }

  private updateEffects(state: ClientState): void {
    if (!state.board) return;

    // 1. Firebolt Spell Flight
    if (state.effect?.type === "fireball") {
      const from = state.effect.from;
      const to = state.effect.to;
      const p = state.effect.progress;

      if (!this.fireboltGroup) {
        this.fireboltGroup = this.modelLoader.instantiate("fire-bolt");
        this.fireboltGroup.scale.setScalar(0.32);
        this.fireboltLight = new THREE.PointLight(0xff6600, 3.0, 4.0);
        this.fireboltGroup.add(this.fireboltLight);
        this.scene.add(this.fireboltGroup);
      }

      const gx = from.x + (to.x - from.x) * p;
      const gy = from.y + (to.y - from.y) * p;
      const world = this.terrain.gridToWorld(gx, gy, state.board.width, state.board.height);

      this.fireboltGroup.position.set(world.x, world.y + BOLT_HOVER_HEIGHT, world.z);

      const dx = to.x - from.x;
      const dy = to.y - from.y;
      this.fireboltGroup.rotation.y = Math.atan2(dx, dy);
      this.fireboltGroup.visible = true;

      // Face the casting robot towards spell target
      const caster = state.players.find((p) => p.name === state.thinking);
      if (caster) {
        const casterMesh = this.playersMap.get(caster.name);
        if (casterMesh) {
          casterMesh.targetRotationY = Math.atan2(dx, dy);
        }
      }
    } else {
      if (this.fireboltGroup) {
        this.fireboltGroup.visible = false;
      }
    }

    // 2. Explosion Hit Shockwave & Blast
    if (state.effect?.type === "explosion") {
      const pos = state.effect.position;
      const p = state.effect.progress;
      const world = this.terrain.gridToWorld(pos.x, pos.y, state.board.width, state.board.height);

      if (!this.explosionGroup) {
        this.explosionGroup = new THREE.Group();

        // Expanding shockwave ring on terrain
        const shockGeom = new THREE.RingGeometry(0.3, 0.45, 24);
        const shockMat = new THREE.MeshBasicMaterial({
          color: 0xff6600,
          side: THREE.DoubleSide,
          transparent: true,
          opacity: 0.9,
          depthWrite: false,
        });
        const shockMesh = new THREE.Mesh(shockGeom, shockMat);
        shockMesh.rotation.x = -Math.PI / 2;
        shockMesh.position.y = 0.03;
        this.explosionGroup.add(shockMesh);

        // Core explosion blast burst
        const blastGeom = new THREE.IcosahedronGeometry(0.35, 1);
        const blastMat = new THREE.MeshStandardMaterial({
          color: 0xffa500,
          emissive: 0xff4400,
          flatShading: true,
          transparent: true,
          opacity: 0.9,
        });
        const blastMesh = new THREE.Mesh(blastGeom, blastMat);
        blastMesh.position.y = 0.4;
        this.explosionGroup.add(blastMesh);

        this.scene.add(this.explosionGroup);
      }

      this.explosionGroup.position.set(world.x, world.y, world.z);
      this.explosionGroup.scale.setScalar(0.4 + p * 1.6);

      const shockMesh = this.explosionGroup.children[0] as THREE.Mesh;
      if (shockMesh && shockMesh.material instanceof THREE.Material) {
        shockMesh.material.opacity = Math.max(0, 1 - p);
      }
      const blastMesh = this.explosionGroup.children[1] as THREE.Mesh;
      if (blastMesh && blastMesh.material instanceof THREE.Material) {
        blastMesh.material.opacity = Math.max(0, 1 - p);
      }
      this.explosionGroup.visible = true;
    } else {
      if (this.explosionGroup) {
        this.explosionGroup.visible = false;
      }
    }
  }

  private startLoop(): void {
    const loop = (timestamp: number) => {
      if (this.isDisposed) return;
      const dt = (timestamp - this.lastTime) * 0.001;
      this.lastTime = timestamp;

      this.tick(timestamp * 0.001, dt);
      this.renderer.render(this.scene, this.camera);

      this.animationFrameId = requestAnimationFrame(loop);
    };
    this.animationFrameId = requestAnimationFrame(loop);
  }

  private tick(time: number, dt: number): void {
    // 1. Animate Players: Smooth bobbing levitation, position gliding, rotation, aura spin
    const activeRobots: THREE.Vector3[] = [];

    for (const p of this.playersMap.values()) {
      // Smooth position lerp
      p.currentPos.lerp(p.targetPos, Math.min(1, dt * 10));

      // Continuous ground height tracking + smooth sinusoidal floating oscillation
      const groundY = this.terrain.getHeight(p.currentPos.x, p.currentPos.z);
      const bob = Math.sin(time * 2.8 + p.phase) * 0.07;
      const totalY = groundY + HOVER_HEIGHT + bob;

      p.group.position.set(p.currentPos.x, groundY, p.currentPos.z);
      if (p.modelGroup) {
        p.modelGroup.position.y = HOVER_HEIGHT + bob;
      }

      // Smooth shortest-path yaw rotation
      let diffRot = p.targetRotationY - p.currentRotationY;
      while (diffRot < -Math.PI) diffRot += Math.PI * 2;
      while (diffRot > Math.PI) diffRot -= Math.PI * 2;
      p.currentRotationY += diffRot * Math.min(1, dt * 10);
      if (p.modelGroup) {
        p.modelGroup.rotation.y = p.currentRotationY;
      }

      // Active aura ring rotation & thought beacon pulse
      if (p.runeRingGroup.visible) {
        p.runeRingGroup.rotation.y = time * 0.8;
      }
      if (p.beaconMesh.visible) {
        p.beaconMesh.rotation.y = time * 2.0;
        p.beaconMesh.position.y = HOVER_HEIGHT + 1.45 + Math.sin(time * 4) * 0.05;
      }

      // Billboard health bar always faces the camera
      p.healthBarGroup.quaternion.copy(this.camera.quaternion);

      // Track active robot position for tree occlusion
      activeRobots.push(new THREE.Vector3(p.currentPos.x, totalY, p.currentPos.z));
    }

    // 2. Dynamic Tree Occlusion Transparency (X-Ray Effect)
    this.updateTreeOcclusion(activeRobots);
  }

  private updateTreeOcclusion(robotPositions: readonly THREE.Vector3[]): void {
    // Camera isometric view direction vector (from scene center towards camera)
    const camDir = new THREE.Vector3(1, 1, 1).normalize();

    for (const tree of this.trees) {
      let isOccluding = false;

      for (const robotPos of robotPositions) {
        // Project robot and tree onto camera view plane
        const toRobot = new THREE.Vector3().subVectors(robotPos, tree.position);
        const depthDiff = toRobot.dot(camDir);

        // Robot must be behind the tree from the camera's perspective
        if (depthDiff < 0) {
          // Distance on view plane
          const lateral = toRobot.clone().sub(camDir.clone().multiplyScalar(depthDiff));
          if (lateral.length() < tree.radius * 1.5) {
            isOccluding = true;
            break;
          }
        }
      }

      tree.targetOpacity = isOccluding ? 0.3 : 1.0;
      tree.currentOpacity += (tree.targetOpacity - tree.currentOpacity) * 0.15;
      this.setObjectOpacity(tree.group, tree.currentOpacity);
    }
  }

  private setObjectOpacity(object: THREE.Object3D, opacity: number): void {
    const isTransparent = opacity < 0.99;
    object.traverse((child) => {
      if (child instanceof THREE.Mesh && child.material) {
        const mats = Array.isArray(child.material) ? child.material : [child.material];
        for (const m of mats) {
          m.transparent = isTransparent;
          m.opacity = opacity;
          m.needsUpdate = true;
        }
      }
    });
  }

  private handleResize = (): void => {
    if (this.isDisposed || !this.canvas) return;
    const width = this.canvas.clientWidth || 780;
    const height = this.canvas.clientHeight || 540;
    const aspect = width / height;
    const frustumSize = 10.5;

    this.camera.left = (-frustumSize * aspect) / 2;
    this.camera.right = (frustumSize * aspect) / 2;
    this.camera.top = frustumSize / 2;
    this.camera.bottom = -frustumSize / 2;
    this.camera.updateProjectionMatrix();

    this.renderer.setSize(width, height, false);
  };

  dispose(): void {
    this.isDisposed = true;
    if (this.animationFrameId !== null) {
      cancelAnimationFrame(this.animationFrameId);
      this.animationFrameId = null;
    }
    window.removeEventListener("resize", this.handleResize);
    this.renderer.dispose();
  }
}
