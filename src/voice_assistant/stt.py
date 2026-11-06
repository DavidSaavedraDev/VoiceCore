from dataclasses import dataclass
from typing import Iterable

import numpy as np
from faster_whisper import WhisperModel


@dataclass
class WhisperTranscriber:
    model_name: str = "base"
    language: str = "es"
    device: str = "cpu"
    compute_type: str = "int8"

    def __post_init__(self) -> None:
        self._model = WhisperModel(
            self.model_name,
            device=self.device,
            compute_type=self.compute_type,
        )

    def transcribe(self, audio: np.ndarray, sample_rate: int) -> str:
        segments, _ = self._model.transcribe(
            audio,
            language=self.language,
            vad_filter=True,
        )
        return " ".join(self._segment_text(segment) for segment in segments).strip()

    @staticmethod
    def _segment_text(segment: object) -> str:
        return str(getattr(segment, "text", "")).strip()
