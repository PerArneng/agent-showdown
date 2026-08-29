import type { ClientState, Renderer } from "../../src/interfaces/game/index.js";

/** In-memory fake renderer for engine and lifecycle testing without DOM or WebGL. */
export class RecordingRenderer implements Renderer {
  readonly states: ClientState[] = [];

  render(state: ClientState): void {
    this.states.push(state);
  }

  last(): ClientState | undefined {
    return this.states[this.states.length - 1];
  }
}
