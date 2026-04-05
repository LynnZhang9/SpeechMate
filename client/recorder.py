"""Audio recorder for SpeechMate Client.

Uses sounddevice to capture audio from the microphone.
"""

import io
import threading
import wave
from typing import Optional
import numpy as np
import sounddevice as sd
from PyQt5.QtCore import QObject, pyqtSignal


class AudioRecorder(QObject):
    """Audio recorder using sounddevice.

    Captures mono audio at 16kHz with 16-bit PCM format,
    suitable for Whisper speech recognition.

    Signals:
        recording_started: Emitted when recording starts.
        recording_stopped: Emitted when recording stops, emits WAV bytes.
    """

    # Signals
    recording_started = pyqtSignal()
    recording_stopped = pyqtSignal(bytes)

    # Audio settings for Whisper compatibility
    SAMPLE_RATE = 16000  # 16kHz - required by Whisper
    CHANNELS = 1  # Mono
    DTYPE = np.int16  # 16-bit PCM

    def __init__(self, parent: Optional[QObject] = None):
        """Initialize the audio recorder.

        Args:
            parent: Parent QObject.
        """
        super().__init__(parent)
        self._is_recording = False
        self._lock = threading.Lock()
        self._audio_data: list[np.ndarray] = []
        self._stream: Optional[sd.InputStream] = None

    def _audio_callback(self, indata: np.ndarray, frames: int, time, status) -> None:
        """Callback function for audio stream.

        Args:
            indata: Input audio data buffer.
            frames: Number of frames.
            time: Time info (unused).
            status: Status flags (unused).
        """
        if self._is_recording:
            # Make a copy of the data to avoid reference issues
            self._audio_data.append(indata.copy())

    def start_recording(self) -> bool:
        """Start recording audio from the microphone.

        Returns:
            True if recording started successfully, False if already recording.
        """
        with self._lock:
            if self._is_recording:
                return False

            # Clear any previous audio data
            self._audio_data = []

            try:
                # Create and start the input stream
                self._stream = sd.InputStream(
                    samplerate=self.SAMPLE_RATE,
                    channels=self.CHANNELS,
                    dtype=self.DTYPE,
                    callback=self._audio_callback
                )
                self._stream.start()
                self._is_recording = True
                self.recording_started.emit()
                return True
            except Exception as e:
                self._stream = None
                print(f"Error starting recording: {e}")
                return False

    def stop_recording(self) -> Optional[bytes]:
        """Stop recording and return the audio as WAV bytes.

        Returns:
            WAV audio data as bytes, or None if not recording or no data.
        """
        with self._lock:
            if not self._is_recording or self._stream is None:
                return None

            self._is_recording = False

            try:
                # Stop and close the stream
                self._stream.stop()
                self._stream.close()
                self._stream = None

                # Combine all audio chunks
                if not self._audio_data:
                    self.recording_stopped.emit(b'')
                    return b''

                audio_array = np.concatenate(self._audio_data, axis=0)

                # Convert to WAV format in memory
                wav_bytes = self._create_wav_bytes(audio_array)

                # Clear audio data
                self._audio_data = []

                # Emit the recording stopped signal with WAV bytes
                self.recording_stopped.emit(wav_bytes)

                return wav_bytes
            except Exception as e:
                print(f"Error stopping recording: {e}")
                self._audio_data = []
                self.recording_stopped.emit(b'')
                return b''

    def _create_wav_bytes(self, audio_data: np.ndarray) -> bytes:
        """Create WAV formatted bytes from audio data.

        Args:
            audio_data: Numpy array of audio samples.

        Returns:
            WAV formatted audio as bytes.
        """
        buffer = io.BytesIO()

        with wave.open(buffer, 'wb') as wav_file:
            wav_file.setnchannels(self.CHANNELS)
            wav_file.setsampwidth(2)  # 16-bit = 2 bytes
            wav_file.setframerate(self.SAMPLE_RATE)
            wav_file.writeframes(audio_data.tobytes())

        # Get the bytes from the buffer
        wav_bytes = buffer.getvalue()
        buffer.close()

        return wav_bytes

    @property
    def is_recording(self) -> bool:
        """Check if currently recording.

        Returns:
            True if recording, False otherwise.
        """
        return self._is_recording
