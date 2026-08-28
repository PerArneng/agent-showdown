import type { ClientState } from "./client-state.js";

/** Draws the board. */
export interface Renderer {
  render(state: ClientState): void;
}
