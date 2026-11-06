# VoiceCore

Asistente de voz local en Python con GUI de escritorio cyberpunk y tres módulos
secuenciales:

1. **Audio/STT:** captura el micrófono con `sounddevice` y transcribe localmente con `faster-whisper`.
2. **Cerebro:** envía el texto a Ollama mediante su API HTTP local.
3. **TTS:** reproduce la respuesta con `pyttsx3` y el motor de voz del sistema.

## Estructura

```text
VoiceCore/
├── .env.example
├── pyproject.toml
├── README.md
└── src/
    └── voice_assistant/
        ├── __main__.py
        ├── audio.py
        ├── brain.py
        ├── config.py
        ├── stt.py
        └── tts.py
```

## Instalación

En PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
```

Instala Ollama y descarga un modelo:

```powershell
ollama pull llama3.2
```

Si el micrófono no aparece, revisa los dispositivos con:

```powershell
python -c "import sounddevice as sd; print(sd.query_devices())"
```

## Interfaz gráfica de escritorio

La ejecución normal abre la ventana gráfica:

```powershell
$env:PYTHONPATH = "src"
python -m voice_assistant --seconds 5
```

La ventana incluye un núcleo animado, estados de grabación/procesamiento/habla,
transcripción y respuesta. El trabajo de audio, Whisper, Ollama y TTS se
ejecuta fuera del hilo de la interfaz para que la ventana no se congele.

La primera ejecución de Whisper descargará el modelo seleccionado. Para equipos
modestos, usa `--model tiny`; para mayor precisión, usa `--model small`.

## Modo terminal opcional

El HUD de terminal sigue disponible:

```powershell
python -m voice_assistant --terminal --seconds 5
```

Puedes ajustar Ollama sin editar el código:

```powershell
$env:OLLAMA_TIMEOUT_SECONDS = "240"
$env:OLLAMA_RETRIES = "3"
python -m voice_assistant --ollama-model llama3.2
```

También puedes usar `--ollama-timeout 240`.
