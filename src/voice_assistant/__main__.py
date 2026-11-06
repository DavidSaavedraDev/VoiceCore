import argparse

from .audio import AudioRecorder
from .brain import OllamaBrain
from .config import Settings
from .stt import WhisperTranscriber
from .tts import Speaker
from .ui import VoiceHUD
from .gui import launch_gui


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Asistente de voz local")
    parser.add_argument("--seconds", type=int, help="Duración de la grabación")
    parser.add_argument("--model", help="Modelo de Whisper")
    parser.add_argument("--ollama-model", help="Modelo de Ollama")
    parser.add_argument(
        "--ollama-timeout",
        type=int,
        help="Segundos máximos de espera por respuesta de Ollama",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Procesa una interacción y termina (por defecto también es una)",
    )
    parser.add_argument(
        "--terminal",
        action="store_true",
        help="Usa la interfaz de terminal en lugar de la GUI",
    )
    return parser


def run_once(settings: Settings, args: argparse.Namespace) -> None:
    recorder = AudioRecorder(
        seconds=args.seconds or settings.audio_seconds,
        sample_rate=settings.audio_sample_rate,
    )
    transcriber = WhisperTranscriber(
        model_name=args.model or settings.whisper_model,
        language=settings.whisper_language,
    )
    brain = OllamaBrain(
        base_url=settings.ollama_url,
        model=args.ollama_model or settings.ollama_model,
        timeout_seconds=args.ollama_timeout or settings.ollama_timeout_seconds,
        retries=settings.ollama_retries,
    )
    speaker = Speaker()
    hud = VoiceHUD()

    hud.set_status("listening")
    audio = recorder.record()
    text = transcriber.transcribe(audio, recorder.sample_rate)
    if not text:
        hud.set_status("ready")
        print("No se detectó voz.")
        return

    hud.set_transcript(text)
    with hud.thinking():
        answer = brain.answer(text)
    hud.set_answer(answer)
    hud.set_status("speaking")
    speaker.speak(answer)
    hud.set_status("ready")


def main() -> None:
    args = build_parser().parse_args()
    settings = Settings()
    if not args.terminal:
        launch_gui(
            settings,
            seconds=args.seconds,
            whisper_model=args.model,
            ollama_model=args.ollama_model,
            ollama_timeout=args.ollama_timeout,
        )
        return
    run_once(settings, args)


if __name__ == "__main__":
    main()
