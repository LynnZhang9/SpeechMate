"""API client for SpeechMate Client.

Uses httpx to communicate with the SpeechMate Host Server.
"""

from typing import Tuple
import httpx


class SpeechMateClient:
    """Client for communicating with the SpeechMate Host Server.

    Provides methods for health checks, transcription, and translation.
    """

    DEFAULT_HOST = "http://127.0.0.1:8000"
    DEFAULT_TIMEOUT = 60.0  # seconds

    def __init__(self, host: str = DEFAULT_HOST, timeout: float = DEFAULT_TIMEOUT):
        """Initialize the API client.

        Args:
            host: Base URL of the SpeechMate Host Server.
            timeout: Request timeout in seconds.
        """
        self._host = host.rstrip("/")
        self._timeout = timeout
        self._client = httpx.Client(timeout=timeout)

    def health_check(self) -> bool:
        """Check if the server is healthy.

        Returns:
            True if server is healthy, False otherwise.
        """
        try:
            response = self._client.get(f"{self._host}/health")
            return response.status_code == 200
        except (httpx.HTTPError, httpx.NetworkError, httpx.TimeoutException):
            return False

    def transcribe(self, audio_bytes: bytes) -> Tuple[bool, str]:
        """Send audio to the server for transcription.

        Args:
            audio_bytes: WAV audio data as bytes.

        Returns:
            Tuple of (success, text_or_error):
                - If successful: (True, transcribed_text)
                - If failed: (False, error_message)
        """
        try:
            files = {"audio": ("audio.wav", audio_bytes, "audio/wav")}
            response = self._client.post(
                f"{self._host}/api/speech",
                files=files
            )

            if response.status_code == 200:
                data = response.json()
                return True, data.get("text", "")
            else:
                # Try to extract error message from response
                try:
                    error_data = response.json()
                    if "detail" in error_data:
                        detail = error_data["detail"]
                        if isinstance(detail, dict):
                            error_msg = detail.get("error", str(detail))
                        else:
                            error_msg = str(detail)
                    else:
                        error_msg = error_data.get("error", f"HTTP {response.status_code}")
                except Exception:
                    error_msg = f"HTTP {response.status_code}"
                return False, error_msg

        except httpx.TimeoutException:
            return False, "Request timed out"
        except httpx.NetworkError:
            return False, "Network error - server unreachable"
        except Exception as e:
            return False, f"Error: {str(e)}"

    def translate(self, text: str, target_lang: str = "en") -> Tuple[bool, str]:
        """Translate text to the target language.

        Args:
            text: Text to translate.
            target_lang: Target language code ("en" or "zh").

        Returns:
            Tuple of (success, text_or_error):
                - If successful: (True, translated_text)
                - If failed: (False, error_message)
        """
        try:
            response = self._client.post(
                f"{self._host}/api/translate",
                json={"text": text, "target_lang": target_lang}
            )

            if response.status_code == 200:
                data = response.json()
                return True, data.get("translated_text", "")
            else:
                # Try to extract error message from response
                try:
                    error_data = response.json()
                    if "detail" in error_data:
                        detail = error_data["detail"]
                        if isinstance(detail, dict):
                            error_msg = detail.get("error", str(detail))
                        else:
                            error_msg = str(detail)
                    else:
                        error_msg = error_data.get("error", f"HTTP {response.status_code}")
                except Exception:
                    error_msg = f"HTTP {response.status_code}"
                return False, error_msg

        except httpx.TimeoutException:
            return False, "Request timed out"
        except httpx.NetworkError:
            return False, "Network error - server unreachable"
        except Exception as e:
            return False, f"Error: {str(e)}"

    def close(self):
        """Close the HTTP client connection."""
        self._client.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False
