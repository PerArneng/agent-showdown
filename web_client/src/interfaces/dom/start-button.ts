/** The button that starts a game. Edge module. */
export interface StartButton {
  onClick(handler: () => void): void;
  setEnabled(enabled: boolean): void;
}
