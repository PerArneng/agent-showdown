import demoGame from "../fixtures/demo-game.json" with { type: "json" };
import type { Engine } from "./interfaces/engine/index.js";
import type { EventStream } from "./interfaces/event_stream/index.js";
import type { GameEvent } from "./interfaces/game/index.js";
import type { GameApi } from "./interfaces/game_api/index.js";
import { Html5Canvas } from "./modules/canvas/index.js";
import { SystemClock } from "./modules/clock/index.js";
import {
  ElementConnectionIndicator,
  ElementPlayerList,
  ElementStartButton,
  ElementStatusText,
} from "./modules/dom/index.js";
import { DefaultEngine } from "./modules/engine/index.js";
import { FixtureEventStream, SseEventStream } from "./modules/event_stream/index.js";
import {
  BoardRenderer,
  DefaultStateReducer,
  HashSpritePicker,
  Palette,
} from "./modules/game/index.js";
import { HttpGameApi, OfflineGameApi } from "./modules/game_api/index.js";

const EVENTS_URL = "/api/events";
const NEW_GAME_URL = "/api/new-game";
const STATE_URL = "/api/state";
const DEMO_STEP_MILLISECONDS = 250;

export interface Elements {
  readonly canvas: HTMLCanvasElement;
  readonly context: CanvasRenderingContext2D;
  readonly playerList: HTMLElement;
  readonly statusText: HTMLElement;
  readonly startButton: HTMLButtonElement;
  readonly connectionIndicator: HTMLElement;
  readonly document: Document;
}

/**
 * Wires the object graph. The only place implementations are named, which is what makes demo mode
 * a choice of two constructors rather than a branch scattered through the client.
 */
export function createEngine(elements: Elements, demo: boolean): Engine {
  const clock = new SystemClock();
  const stream: EventStream = demo
    ? new FixtureEventStream(demoGame as readonly GameEvent[], clock, DEMO_STEP_MILLISECONDS)
    : new SseEventStream(EVENTS_URL);
  const api: GameApi = demo ? new OfflineGameApi() : new HttpGameApi(NEW_GAME_URL, STATE_URL);

  return new DefaultEngine(
    stream,
    api,
    new DefaultStateReducer(new Palette(), new HashSpritePicker()),
    new BoardRenderer(new Html5Canvas(elements.canvas, elements.context)),

    new ElementPlayerList(elements.playerList, elements.document),
    new ElementStatusText(elements.statusText),
    new ElementStartButton(elements.startButton),
    new ElementConnectionIndicator(elements.connectionIndicator),
    clock,
  );
}
