from dataclasses import dataclass

import numpy as np
import sounddevice as sd


@dataclass(frozen=True)
class AudioRecorder:
    seconds: int = 5
    sample_rate: int = 16_000

    def record(self) -> np.ndarray:
        """Record mono microphone audio and return float32 samples."""
        print(f"Grabando durante {self.seconds} segundos...")
        recording = sd.rec(
            int(self.seconds * self.sample_rate),
            samplerate=self.sample_rate,
            channels=1,
            dtype="float32",
        )
        sd.wait()
        return recording[:, 0]
