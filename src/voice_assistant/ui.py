import itertools
import os
import sys
import threading
import time
import textwrap


RESET = "\033[0m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
DIM = "\033[2m"


class VoiceHUD:
    """Terminal HUD used by the assistant's listening and response states."""

    _box = ("╔", "═", "╗", "║", "╚", "╝")
    _fallback_box = ("+", "=", "+", "|", "+", "+")
    _status_labels = {
        "listening": ("GRABANDO", YELLOW),
        "processing": ("PROCESANDO", MAGENTA),
        "speaking": ("HABLANDO", GREEN),
        "ready": ("LISTO", CYAN),
        "error": ("ERROR", RED),
    }

    def __init__(self, width: int = 68) -> None:
        self.width = max(width, 48)
        self._status = "ready"
        self._transcript = ""
        self._answer = ""
        self._progress = 0
        self._configure_windows_output()
        self._lock = threading.RLock()
        self._supports_unicode = self._can_write_unicode()

    def clear(self) -> None:
        sys.stdout.write("\033[2J\033[H")

    def set_status(self, status: str, progress: int = 0) -> None:
        with self._lock:
            self._status = status
            self._progress = progress % 101
        self.render()

    def set_transcript(self, text: str) -> None:
        with self._lock:
            self._transcript = text
        self.render()

    def set_answer(self, text: str) -> None:
        with self._lock:
            self._answer = text
        self.render()

    def render(self) -> None:
        with self._lock:
            status = self._status
            transcript = self._transcript
            answer = self._answer
            progress = self._progress

        label, color = self._status_labels.get(status, ("ACTIVO", CYAN))
        top, horizontal, right, vertical, bottom, bottom_right = self._box_chars()
        line = horizontal * (self.width - 2)
        output = [
            f"{top}{line}{right}",
            f"{vertical}  {CYAN}V O I C E C O R E{RESET}"
            f"{' ' * max(1, self.width - 22)}{vertical}",
            f"{vertical}  {DIM}LOCAL INTELLIGENCE CONSOLE{RESET}"
            f"{' ' * max(1, self.width - 29)}{vertical}",
            f"{vertical}{' ' * (self.width - 2)}{vertical}",
            f"{vertical}  {color}[ {label} ]{RESET}"
            f"{' ' * max(1, self.width - len(label) - 12)}{vertical}",
        ]
        if status == "processing":
            filled = int(progress / 5)
            bar = "#" * filled + "-" * (20 - filled)
            output.append(
                f"{vertical}  {MAGENTA}QUANTUM CORE  [{bar}] "
                f"{progress:02d}%{RESET}"
                f"{' ' * max(1, self.width - 39)}{vertical}"
            )
        output.extend(self._message_lines(vertical, "TÚ", transcript))
        output.extend(self._message_lines(vertical, "ASISTENTE", answer))
        output.extend(
            [
                f"{vertical}{' ' * (self.width - 2)}{vertical}",
                f"{bottom}{line}{bottom_right}",
            ]
        )
        self.clear()
        self._write("\n".join(output) + "\n")

    def thinking(self) -> "ThinkingAnimation":
        return ThinkingAnimation(self)

    def _message_lines(self, vertical: str, title: str, text: str) -> list[str]:
        prefix = f"  {title}: "
        content_width = self.width - len(prefix) - 3
        if not text:
            return [f"{vertical}{' ' * (self.width - 2)}{vertical}"]
        wrapped = textwrap.wrap(text, width=max(content_width, 1)) or [""]
        lines = [f"{vertical}{prefix}{wrapped[0]}"]
        lines.extend(
            f"{vertical}{' ' * len(prefix)}{line}" for line in wrapped[1:]
        )
        return [f"{line}{' ' * (self.width - len(line) - 1)}{vertical}" for line in lines]

    def _box_chars(self) -> tuple[str, ...]:
        return self._box if self._supports_unicode else self._fallback_box

    @staticmethod
    def _can_write_unicode() -> bool:
        encoding = (getattr(sys.stdout, "encoding", None) or "").lower()
        return "utf" in encoding or encoding in {"cp437", "437"}

    @staticmethod
    def _configure_windows_output() -> None:
        if os.name == "nt" and hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    @staticmethod
    def _write(text: str) -> None:
        try:
            sys.stdout.write(text)
            sys.stdout.flush()
        except UnicodeEncodeError:
            sys.stdout.write(text.encode("ascii", "replace").decode("ascii"))
            sys.stdout.flush()


class ThinkingAnimation:
    def __init__(self, hud: VoiceHUD | None = None) -> None:
        self._hud = hud or VoiceHUD()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def __enter__(self) -> "ThinkingAnimation":
        self._thread = threading.Thread(target=self._animate, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, *context: object) -> None:
        del context
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join()

    def _animate(self) -> None:
        for index in itertools.count():
            if self._stop_event.is_set():
                return
            progress = (index * 4) % 101
            self._hud.set_status("processing", progress)
            time.sleep(0.18)
