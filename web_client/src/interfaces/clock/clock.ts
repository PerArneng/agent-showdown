/** The time edge, same role as the Python `Clock`: waiting is injected, never called for. */
export interface Clock {
  sleep(milliseconds: number): Promise<void>;
}
