from dataclasses import dataclass

import pyttsx3


@dataclass
class Speaker:
    rate: int = 175

    def __post_init__(self) -> None:
        self._engine = pyttsx3.init()
        self._engine.setProperty("rate", self.rate)

    def speak(self, text: str) -> None:
        self._engine.say(text)
        self._engine.runAndWait()
