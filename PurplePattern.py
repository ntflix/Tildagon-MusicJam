from patterns.base import BasePattern
import math
import random


class PurpleRandom(BasePattern):
    random_phases: list[float] = []

    def __init__(self, num_leds=12):
        super().__init__(num_leds)
        self.fps = 30
        self.num_pixels = num_leds
        self.num_frames = 60
        # Generate random phase offsets for each LED (0 to 2π)
        self.random_phases = [random.uniform(0, 2 * math.pi) for _ in range(num_leds)]
        self.make_frames()

    def make_frames(self):
        self.frames = []
        for j in range(self.num_frames):
            current_row = []
            for i in range(self.num_pixels):
                # Use the random phase instead of position-based phase
                brightness = (
                    math.sin(
                        (j / self.num_frames) * 2 * math.pi
                        + self.random_phases[i]  # Random offset, not position-based
                    )
                    + 1
                ) / 2
                brightness = int(brightness * 255)
                current_row.append((brightness, 0, brightness))
            self.frames.append(current_row)
