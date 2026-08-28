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
  const context = canvas.getContext("2d");
  if (context === null) {
    throw new Error("this browser has no 2D canvas context");
  }
  return { canvas, context, playerList, statusText, startButton, connectionIndicator, document };
}

const demo = new URLSearchParams(window.location.search).has("demo");
const engine = createEngine(elements(), demo);
engine.connect();
if (demo) {
  // Nothing to ask a server for: the recording is already playing.
  engine.startGame();
}
