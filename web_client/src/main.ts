import { createEngine, type Elements } from "./container.js";
import "./styles.css";

/** Composition root. Finds the elements, picks live or demo, and gets out of the way. */
function elements(): Elements {
  const canvas = document.querySelector<HTMLCanvasElement>("#board");
  const playerList = document.querySelector<HTMLElement>("#players");
  const statusText = document.querySelector<HTMLElement>("#status");
  const startButton = document.querySelector<HTMLButtonElement>("#start");
  const connectionIndicator = document.querySelector<HTMLElement>("#connection");
  if (
    canvas === null ||
    playerList === null ||
    statusText === null ||
    startButton === null ||
    connectionIndicator === null
  ) {
    throw new Error("the page is missing an element the client needs");
  }
  return { canvas, playerList, statusText, startButton, connectionIndicator, document };
}

const params = new URLSearchParams(window.location.search);
const demo = params.has("demo");
const stepParam = params.get("step");
const stepMs = stepParam !== null ? parseInt(stepParam, 10) : undefined;
const engine = createEngine(elements(), demo, stepMs);
engine.connect();
