import queue
import threading
import tkinter as tk

from .audio import AudioRecorder
from .brain import OllamaBrain
from .config import Settings
from .stt import WhisperTranscriber
from .tts import Speaker


BG = "#070b16"
PANEL = "#0d1426"
CYAN = "#00e5ff"
MAGENTA = "#ff2bd6"
GREEN = "#39ff88"
TEXT = "#d9f7ff"
MUTED = "#71849d"
ERROR = "#ff5577"


class VoiceCoreGUI:
    """Non-blocking cyberpunk desktop interface for one voice interaction."""

    def __init__(
        self,
        settings: Settings,
        seconds: int | None = None,
        whisper_model: str | None = None,
        ollama_model: str | None = None,
        ollama_timeout: int | None = None,
    ) -> None:
        self.settings = settings
        self.seconds = seconds or settings.audio_seconds
        self.whisper_model = whisper_model or settings.whisper_model
        self.ollama_model = ollama_model or settings.ollama_model
        self.ollama_timeout = ollama_timeout or settings.ollama_timeout_seconds
        self.events: queue.Queue[tuple[str, str]] = queue.Queue()
        self.worker: threading.Thread | None = None
        self.running = False
        self.phase = "LISTO"
        self.animation_step = 0

        self.root = tk.Tk()
        self.root.title("VoiceCore // Local Intelligence")
        self.root.geometry("900x680")
        self.root.minsize(720, 560)
        self.root.configure(bg=BG)
        self.root.protocol("WM_DELETE_WINDOW", self.close)

        self._build_widgets()
        self._animate_core()
        self._poll_events()

    def run(self) -> None:
        self.root.mainloop()

    def _build_widgets(self) -> None:
        header = tk.Frame(self.root, bg=BG)
        header.pack(fill="x", padx=28, pady=(22, 8))
        tk.Label(
            header,
            text="V O I C E C O R E",
            font=("Segoe UI", 24, "bold"),
            fg=CYAN,
            bg=BG,
        ).pack(anchor="w")
        tk.Label(
            header,
            text="LOCAL INTELLIGENCE // NEURAL AUDIO INTERFACE",
            font=("Consolas", 10),
            fg=MUTED,
            bg=BG,
        ).pack(anchor="w", pady=(2, 0))

        self.core = tk.Canvas(
            self.root,
            height=190,
            bg=BG,
            highlightthickness=0,
        )
        self.core.pack(fill="x", padx=28, pady=8)

        self.status = tk.Label(
            self.root,
            text="[ LISTO ]",
            font=("Consolas", 13, "bold"),
            fg=CYAN,
            bg=BG,
        )
        self.status.pack(pady=(0, 12))

        conversation = tk.Frame(self.root, bg=BG)
        conversation.pack(fill="both", expand=True, padx=28)
        self.transcript_box = self._create_text_panel(conversation, "TÚ")
        self.answer_box = self._create_text_panel(conversation, "ASISTENTE")

        controls = tk.Frame(self.root, bg=BG)
        controls.pack(fill="x", padx=28, pady=22)
        self.listen_button = tk.Button(
            controls,
            text="●  INICIAR ESCUCHA",
            command=self.start_interaction,
            font=("Consolas", 12, "bold"),
            fg=BG,
            bg=CYAN,
            activeforeground=BG,
            activebackground="#8df5ff",
            relief="flat",
            padx=24,
            pady=12,
            cursor="hand2",
        )
        self.listen_button.pack(side="left")
        tk.Label(
            controls,
            text=f"Whisper: {self.whisper_model}  |  Ollama: {self.ollama_model}",
            font=("Consolas", 9),
            fg=MUTED,
            bg=BG,
        ).pack(side="right", pady=12)

    def _create_text_panel(self, parent: tk.Frame, title: str) -> tk.Text:
        panel = tk.Frame(parent, bg=PANEL, highlightbackground="#1b3150", highlightthickness=1)
        panel.pack(side="left", fill="both", expand=True, padx=(0, 8) if title == "TÚ" else (8, 0))
        tk.Label(
            panel,
            text=f"  {title}:",
            anchor="w",
            font=("Consolas", 11, "bold"),
            fg=MAGENTA if title == "TÚ" else GREEN,
            bg=PANEL,
        ).pack(fill="x", pady=(10, 4))
        text = tk.Text(
            panel,
            height=7,
            wrap="word",
            font=("Segoe UI", 11),
            fg=TEXT,
            bg=PANEL,
            insertbackground=TEXT,
            relief="flat",
            padx=12,
            pady=6,
        )
        text.pack(fill="both", expand=True)
        text.configure(state="disabled")
        return text

    def start_interaction(self) -> None:
        if self.running:
            return
        self.running = True
        self.listen_button.configure(state="disabled", text="◌  PROCESANDO...")
        self._set_text(self.transcript_box, "")
        self._set_text(self.answer_box, "")
        self._set_status("GRABANDO", "#ffd166")
        self.worker = threading.Thread(target=self._process_voice, daemon=True)
        self.worker.start()

    def _process_voice(self) -> None:
        try:
            recorder = AudioRecorder(self.seconds, self.settings.audio_sample_rate)
            self.events.put(("status", "GRABANDO"))
            audio = recorder.record()

            self.events.put(("status", "TRANSCRIBIENDO"))
            transcriber = WhisperTranscriber(self.whisper_model, self.settings.whisper_language)
            text = transcriber.transcribe(audio, recorder.sample_rate)
            if not text:
                self.events.put(("error", "No se detectó voz. Inténtalo de nuevo."))
                return
            self.events.put(("transcript", text))

            self.events.put(("status", "PROCESANDO"))
            brain = OllamaBrain(
                base_url=self.settings.ollama_url,
                model=self.ollama_model,
                timeout_seconds=self.ollama_timeout,
                retries=self.settings.ollama_retries,
            )
            answer = brain.answer(text)
            self.events.put(("answer", answer))

            self.events.put(("status", "HABLANDO"))
            Speaker().speak(answer)
            self.events.put(("status", "LISTO"))
        except Exception as error:
            self.events.put(("error", str(error)))
        finally:
            self.events.put(("finished", ""))

    def _poll_events(self) -> None:
        try:
            while True:
                event, value = self.events.get_nowait()
                if event == "status":
                    self._set_status(value, self._status_color(value))
                elif event == "transcript":
                    self._set_text(self.transcript_box, value)
                elif event == "answer":
                    self._set_text(self.answer_box, value)
                elif event == "error":
                    self._set_status("ERROR", ERROR)
                    self._set_text(self.answer_box, value)
                elif event == "finished":
                    self.running = False
                    self.listen_button.configure(state="normal", text="●  INICIAR ESCUCHA")
        except queue.Empty:
            pass
        self.root.after(80, self._poll_events)

    def _animate_core(self) -> None:
        self.animation_step = (self.animation_step + 1) % 360
        self.core.delete("all")
        center_x, center_y = self.core.winfo_width() // 2, 95
        if center_x < 10:
            center_x = 450
        pulse = 42 + (self.animation_step % 20)
        self.core.create_oval(
            center_x - pulse,
            center_y - pulse,
            center_x + pulse,
            center_y + pulse,
            outline=MAGENTA if self.running else CYAN,
            width=2,
        )
        self.core.create_oval(
            center_x - 24,
            center_y - 24,
            center_x + 24,
            center_y + 24,
            fill="#11253c",
            outline=CYAN,
            width=2,
        )
        self.core.create_text(
            center_x,
            center_y,
            text="AI",
            fill=TEXT,
            font=("Consolas", 16, "bold"),
        )
        self.root.after(70, self._animate_core)

    def _set_status(self, value: str, color: str) -> None:
        self.phase = value
        self.status.configure(text=f"[ {value} ]", fg=color)

    def _set_text(self, widget: tk.Text, value: str) -> None:
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", value)
        widget.configure(state="disabled")

    @staticmethod
    def _status_color(value: str) -> str:
        return {
            "GRABANDO": "#ffd166",
            "TRANSCRIBIENDO": MAGENTA,
            "PROCESANDO": MAGENTA,
            "HABLANDO": GREEN,
            "LISTO": CYAN,
        }.get(value, TEXT)

    def close(self) -> None:
        self.root.destroy()


def launch_gui(
    settings: Settings,
    seconds: int | None = None,
    whisper_model: str | None = None,
    ollama_model: str | None = None,
    ollama_timeout: int | None = None,
) -> None:
    VoiceCoreGUI(
        settings,
        seconds=seconds,
        whisper_model=whisper_model,
        ollama_model=ollama_model,
        ollama_timeout=ollama_timeout,
    ).run()
