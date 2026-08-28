import { describe, expect, it } from "vitest";
import { HashSpritePicker } from "../../src/modules/game/index.js";

describe("HashSpritePicker", () => {
  const picker = new HashSpritePicker();

  it("returns an index within 0..9", () => {
    const sprite = picker.pick("agent-one", []);
    expect(sprite).toBeGreaterThanOrEqual(0);
    expect(sprite).toBeLessThan(10);
  });

  it("is deterministic for the same name", () => {
    const first = picker.pick("dummy-1", []);
    const second = picker.pick("dummy-1", []);
    expect(first).toBe(second);
  });

  it("picks an untaken slot when preferred slot is free", () => {
    const sprite = picker.pick("simple-strands-1", []);
    expect(picker.pick("simple-strands-1", [])).toBe(sprite);
  });

  it("probes to the next free slot when collision occurs", () => {
    const name = "test-agent";
    const initial = picker.pick(name, []);

    // Take the initial slot
    const next = picker.pick(name, [initial]);
    expect(next).toBe((initial + 1) % 10);

    // Take the next slot as well
    const third = picker.pick(name, [initial, next]);
    expect(third).toBe((initial + 2) % 10);
  });

  it("wraps around 0..9 during collision probing", () => {
    // If slot 9 is taken, next probed is 0
    const taken = [0, 1, 2, 3, 4, 5, 6, 7, 8];
    const sprite = picker.pick("anyone", taken);
    expect(sprite).toBe(9);
  });

  it("falls back gracefully when all 10 slots are taken", () => {
    const allTaken = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9];
    const sprite = picker.pick("extra-agent", allTaken);
    expect(sprite).toBeGreaterThanOrEqual(0);
    expect(sprite).toBeLessThan(10);
  });

  it("assigns distinct sprites to different players in sequence", () => {
    const names = ["dummy-1", "simple-strands-1", "deep-blue", "stockfish", "alpha-zero"];
    const assigned: number[] = [];
    for (const name of names) {
      const sprite = picker.pick(name, assigned);
      expect(assigned).not.toContain(sprite);
      assigned.push(sprite);
    }
    expect(assigned).toHaveLength(names.length);
    expect(new Set(assigned).size).toBe(names.length);
  });
});
