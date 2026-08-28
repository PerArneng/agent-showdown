/** A live subscription. Closed by whoever opened it. */
export interface Subscription {
  close(): void;
}
