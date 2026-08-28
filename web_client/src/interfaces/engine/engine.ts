/** The facade every entry point calls. All behaviour of the client hangs off this. */
export interface Engine {
  connect(): void;
  startGame(): void;
}
