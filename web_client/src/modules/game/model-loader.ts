import * as THREE from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";

import fireboltUrl from "../../assets/models/fire-bolt.glb";
import robot1Url from "../../assets/models/player-robot-1.glb";
import robot2Url from "../../assets/models/player-robot-2.glb";
import robot3Url from "../../assets/models/player-robot-3.glb";
import robot4Url from "../../assets/models/player-robot-4.glb";
import tree1Url from "../../assets/models/tree-1.glb";
import tree2Url from "../../assets/models/tree-2.glb";

export type ModelKey =
  "robot-1" | "robot-2" | "robot-3" | "robot-4" | "tree-1" | "tree-2" | "fire-bolt";

const MODEL_URLS: Record<ModelKey, string> = {
  "robot-1": robot1Url,
  "robot-2": robot2Url,
  "robot-3": robot3Url,
  "robot-4": robot4Url,
  "tree-1": tree1Url,
  "tree-2": tree2Url,
  "fire-bolt": fireboltUrl,
};

/**
 * Loads, caches, and clones low-poly 3D models with flat-shading materials.
 */
export class ModelLoader {
  private readonly templates = new Map<ModelKey, THREE.Group>();
  private readonly loader = new GLTFLoader();
  private loadedPromise: Promise<void> | null = null;

  /** Loads all models in parallel. */
  async loadAll(): Promise<void> {
    if (this.loadedPromise !== null) {
      return this.loadedPromise;
    }

    const keys = Object.keys(MODEL_URLS) as ModelKey[];
    this.loadedPromise = Promise.all(
      keys.map(async (key) => {
        const url = MODEL_URLS[key];
        const group = await this.loadModel(url);
        this.normalizeMaterials(group);
        this.templates.set(key, group);
      }),
    ).then(() => undefined);

    return this.loadedPromise;
  }

  private async loadModel(url: string): Promise<THREE.Group> {
    if (url.startsWith("data:")) {
      const base64 = url.includes(",") ? url.split(",")[1]! : url;
      const binary = atob(base64);
      const bytes = new Uint8Array(binary.length);
      for (let i = 0; i < binary.length; i++) {
        bytes[i] = binary.charCodeAt(i);
      }
      return new Promise<THREE.Group>((resolve, reject) => {
        this.loader.parse(
          bytes.buffer,
          "",
          (gltf) => resolve(gltf.scene),
          (err) => reject(err),
        );
      });
    }

    return new Promise<THREE.Group>((resolve, reject) => {
      this.loader.load(
        url,
        (gltf) => resolve(gltf.scene),
        undefined,
        (err) => reject(err),
      );
    });
  }

  private normalizeMaterials(object: THREE.Object3D): void {
    object.traverse((child) => {
      if (child instanceof THREE.Mesh) {
        child.castShadow = true;
        child.receiveShadow = true;
        if (child.material) {
          const mats = Array.isArray(child.material) ? child.material : [child.material];
          for (const mat of mats) {
            if ("flatShading" in mat) {
              mat.flatShading = true;
              mat.needsUpdate = true;
            }
            if ("roughness" in mat) {
              mat.roughness = 0.85;
            }
          }
        }
      }
    });
  }

  /**
   * Instantiates a new copy of a model template with cloned materials so its opacity,
   * color, and transforms can be updated independently.
   */
  instantiate(key: ModelKey): THREE.Group {
    const template = this.templates.get(key);
    if (!template) {
      // Fallback placeholder group if loading hasn't finished
      const fallback = new THREE.Group();
      const geom = new THREE.BoxGeometry(0.8, 0.8, 0.8);
      const mat = new THREE.MeshStandardMaterial({
        color: 0x888888,
        flatShading: true,
      });
      fallback.add(new THREE.Mesh(geom, mat));
      return fallback;
    }

    const clone = template.clone(true);
    // Clone materials for instance isolation (e.g. tree transparency, player ghosts)
    clone.traverse((child) => {
      if (child instanceof THREE.Mesh) {
        if (Array.isArray(child.material)) {
          child.material = child.material.map((m) => m.clone());
        } else if (child.material) {
          child.material = child.material.clone();
        }
      }
    });

    return clone;
  }
}
