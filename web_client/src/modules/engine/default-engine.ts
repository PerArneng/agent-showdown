import type { Clock } from "../../interfaces/clock/index.js";
import type {
  ConnectionIndicator,
  PlayerList,
  StartButton,
  StatusText,
} from "../../interfaces/dom/index.js";
import type { Engine } from "../../interfaces/engine/index.js";
import type { EventStream } from "../../interfaces/event_stream/index.js";
import type {
  ClientState,
  GameEvent,
  Renderer,
  StateReducer,
} from "../../interfaces/game/index.js";
import type { GameApi } from "../../interfaces/game_api/index.js";

/**
 * The facade. Holds the current state, and orchestrates events, rendering, sidebar updates,
 * and smooth animations.
 */
export class DefaultEngine implements Engine {
  private state: ClientState;
  private readonly queue: GameEvent[] = [];
  private busy = false;

  constructor(
    private readonly stream: EventStream,
    private readonly api: GameApi,
    private readonly reducer: StateReducer,
    private readonly renderer: Renderer,
    private readonly playerList: PlayerList,
    private readonly statusText: StatusText,
    private readonly startButton: StartButton,
    private readonly connectionIndicator: ConnectionIndicator,
    private readonly clock: Clock,
  ) {
    this.state = reducer.initial();
  }

  connect(): void {
    this.startButton.onClick(() => this.startGame());
    this.show(this.state);
    this.connectionIndicator.show(false);
    // Subscribe first, so no event can slip past while the snapshot is in flight; the snapshot
    // then fills only what the stream has not already told us.
    this.stream.subscribe(
      (event) => this.handle(event),
      (connected) => this.connectionIndicator.show(connected),
    );
    void this.catchUp();
  }

  /** Recover a game already in progress: the stream has no replay, so the board is fetched. */
  private async catchUp(): Promise<void> {
    const snapshot = await this.api.fetchSnapshot();
    this.show(this.reducer.catchUp(this.state, snapshot));
    this.startButton.setEnabled(!snapshot.playing);
  }

  startGame(): void {
    this.startButton.setEnabled(false);
    // A new game starts from nothing, so a replay does not inherit the last one's players.
    this.show(this.reducer.initial());
    this.statusText.show("Starting.");
    void this.api.startGame();
  }

  private handle(event: GameEvent): void {
    this.queue.push(event);
    if (!this.busy) {
      void this.drain();
    }
  }

  private async drain(): Promise<void> {
    this.busy = true;
    while (this.queue.length > 0) {
      const event = this.queue.shift();
      if (event !== undefined) {
        await this.processEvent(event);
      }
    }
    this.busy = false;
  }

  private async processEvent(event: GameEvent): Promise<void> {
    if (event.type === "player_moved") {
      const steps = 4;
      for (let i = 1; i <= steps; i++) {
        const progress = i / steps;
        this.renderer.render({
          ...this.state,
          effect: {
            type: "move",
            player: event.player,
            from: event.source,
            to: event.destination,
            progress,
          },
        });
        await this.clock.sleep(25);
      }
    } else if (event.type === "spell_cast") {
      if (event.path.length > 0) {
        let currentOrigin = event.origin;
        for (const dest of event.path) {
          const steps = 3;
          for (let i = 1; i <= steps; i++) {
            const progress = i / steps;
            this.renderer.render({
              ...this.state,
              effect: {
                type: "fireball",
                from: currentOrigin,
                to: dest,
                progress,
              },
            });
            await this.clock.sleep(20);
          }
          currentOrigin = dest;
        }
      }
    } else if (event.type === "player_hit") {
      const steps = 4;
      for (let i = 1; i <= steps; i++) {
        const progress = i / steps;
        this.renderer.render({
          ...this.state,
          effect: {
            type: "explosion",
            position: event.position,
            progress,
          },
        });
        await this.clock.sleep(30);
      }
    }

    this.show(this.reducer.reduce(this.state, event));
    if (event.type === "game_ended") {
      this.startButton.setEnabled(true);
    }
  }

  private show(state: ClientState): void {
    this.state = state;
    this.renderer.render(state);
    this.playerList.show(state.players, state.thinking);
    this.statusText.show(state.status);
  }
}
