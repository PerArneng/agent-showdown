import type { GameEvent } from "../game/index.js";
import type { Subscription } from "./subscription.js";

/**
 * Where game events come from. Edge: the live implementation holds a network connection.
 *
 * This is the seam demo mode turns on — a recorded game is just a different implementation.
 */
export interface EventStream {
  subscribe(
    onEvent: (event: GameEvent) => void,
    onConnectionChange?: (connected: boolean) => void,
  ): Subscription;
}
