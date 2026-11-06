import json
import time
from dataclasses import dataclass
from socket import timeout as SocketTimeout
from urllib.error import URLError
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class OllamaBrain:
    base_url: str = "http://localhost:11434"
    model: str = "llama3.2"
    timeout_seconds: int = 180
    retries: int = 2

    def answer(self, text: str) -> str:
        payload = json.dumps(
            {
                "model": self.model,
                "prompt": (
                    "Responde en español, de forma breve y útil. "
                    f"Usuario: {text}"
                ),
                "stream": False,
            }
        ).encode("utf-8")
        request = Request(
            f"{self.base_url.rstrip('/')}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        last_error: Exception | None = None
        for attempt in range(self.retries + 1):
            try:
                with urlopen(request, timeout=self.timeout_seconds) as response:
                    result = json.load(response)
                break
            except (URLError, SocketTimeout, TimeoutError) as error:
                last_error = error
                if attempt == self.retries:
                    raise RuntimeError(
                        "Ollama no respondió a tiempo o no está disponible. "
                        "Comprueba que esté ejecutándose y que el modelo exista."
                    ) from error
                time.sleep(2**attempt)
        else:
            raise RuntimeError("No se pudo obtener una respuesta de Ollama.") from last_error

        answer = str(result.get("response", "")).strip()
        if not answer:
            raise RuntimeError("Ollama devolvió una respuesta vacía.")
        return answer
