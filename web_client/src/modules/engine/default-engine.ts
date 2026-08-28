import type { PlayerList, StartButton, StatusText } from "../../interfaces/dom/index.js";
import type { Engine } from "../../interfaces/engine/index.js";
import type { EventStream } from "../../interfaces/event_stream/index.js";
import type { ClientState, GameEvent, Renderer, StateReducer } from "../../interfaces/game/index.js";
import type { GameApi } from "../../interfaces/game_api/index.js";

/**
 * The facade. Holds the current state, and does the same three things for every event: fold it in,
 * draw the board, refresh the sidebar.
 */
export class DefaultEngine implements Engine {
  private state: ClientState;

  constructor(
    private readonly stream: EventStream,
    private readonly api: GameApi,
    private readonly reducer: StateReducer,
    private readonly renderer: Renderer,
    private readonly playerList: PlayerList,
    private readonly statusText: StatusText,
    private readonly startButton: StartButton
  ) {
    this.state = reducer.initial();
  }

  connect(): void {
    this.startButton.onClick(() => this.startGame());
    this.show(this.state);
    this.stream.subscribe((event) => this.handle(event));
  }

  startGame(): void {
    this.startButton.setEnabled(false);
    // A new game starts from nothing, so a replay does not inherit the last one's players.
    this.show(this.reducer.initial());
    this.statusText.show("Starting.");
    void this.api.startGame();
  }

  private handle(event: GameEvent): void {
    this.show(this.reducer.reduce(this.state, event));
    if (event.type === "game_ended") {
      this.startButton.setEnabled(true);
    }
  }

  private show(state: ClientState): void {
    this.state = state;
    this.renderer.render(state);
    this.playerList.show(state.players);
    this.statusText.show(state.status);
  }
}
