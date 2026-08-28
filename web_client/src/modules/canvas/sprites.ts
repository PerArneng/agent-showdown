import robot0 from "../../assets/sprites/robot-0.png";
import robot1 from "../../assets/sprites/robot-1.png";
import robot2 from "../../assets/sprites/robot-2.png";
import robot3 from "../../assets/sprites/robot-3.png";
import robot4 from "../../assets/sprites/robot-4.png";
import robot5 from "../../assets/sprites/robot-5.png";
import robot6 from "../../assets/sprites/robot-6.png";
import robot7 from "../../assets/sprites/robot-7.png";
import robot8 from "../../assets/sprites/robot-8.png";
import robot9 from "../../assets/sprites/robot-9.png";

export const SPRITE_URLS: readonly string[] = [
  robot0,
  robot1,
  robot2,
  robot3,
  robot4,
  robot5,
  robot6,
  robot7,
  robot8,
  robot9,
];

export function spriteUrlFor(sprite: number): string {
  const index = Math.abs(sprite) % SPRITE_URLS.length;
  return SPRITE_URLS[index] ?? SPRITE_URLS[0] ?? "";
}
