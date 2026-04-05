"""Tests for the AudioRecorder class."""

import unittest
from unittest.mock import patch, MagicMock
import numpy as np
from PyQt5.QtCore import QObject
from client.recorder import AudioRecorder


class TestAudioRecorder(unittest.TestCase):
    """Test cases for AudioRecorder."""

    def test_init(self):
        """Test initialization."""
        recorder = AudioRecorder()
        self.assertFalse(recorder.is_recording)
        self.assertEqual(recorder.SAMPLE_RATE, 16000)
        self.assertEqual(recorder.CHANNELS, 1)
        self.assertEqual(recorder.DTYPE, np.int16)

    def test_audio_settings_for_whisper(self):
        """Test that audio settings are compatible with Whisper."""
        recorder = AudioRecorder()
        # Whisper requires 16kHz sample rate
        self.assertEqual(recorder.SAMPLE_RATE, 16000)
        # Mono audio
        self.assertEqual(recorder.CHANNELS, 1)
        # 16-bit PCM
        self.assertEqual(recorder.DTYPE, np.int16)

    def test_start_recording_creates_stream(self):
        """Test that start_recording() creates an InputStream."""
        recorder = AudioRecorder()

        with patch('client.recorder.sd.InputStream') as MockStream:
            mock_stream = MagicMock()
            MockStream.return_value = mock_stream

            result = recorder.start_recording()

            self.assertTrue(result)
            self.assertTrue(recorder.is_recording)
            MockStream.assert_called_once_with(
                samplerate=16000,
                channels=1,
                dtype=np.int16,
                callback=recorder._audio_callback
            )
            mock_stream.start.assert_called_once()

    def test_start_recording_returns_false_if_already_recording(self):
        """Test that start_recording() returns False if already recording."""
        recorder = AudioRecorder()

        with patch('client.recorder.sd.InputStream') as MockStream:
            mock_stream = MagicMock()
            MockStream.return_value = mock_stream

            recorder.start_recording()
            result = recorder.start_recording()

            self.assertFalse(result)
            self.assertTrue(recorder.is_recording)

    def test_start_recording_emits_signal(self):
        """Test that start_recording() emits recording_started signal."""
        recorder = AudioRecorder()

        with patch('client.recorder.sd.InputStream') as MockStream:
            mock_stream = MagicMock()
            MockStream.return_value = mock_stream

            with patch.object(recorder, 'recording_started') as mock_signal:
                recorder.start_recording()
                mock_signal.emit.assert_called_once()

    def test_stop_recording_returns_none_if_not_recording(self):
        """Test that stop_recording() returns None if not recording."""
        recorder = AudioRecorder()
        result = recorder.stop_recording()
        self.assertIsNone(result)

    def test_stop_recording_stops_stream(self):
        """Test that stop_recording() stops and closes the stream."""
        recorder = AudioRecorder()

        with patch('client.recorder.sd.InputStream') as MockStream:
            mock_stream = MagicMock()
            MockStream.return_value = mock_stream

            recorder.start_recording()

            # Add some mock audio data
            recorder._audio_data = [np.zeros((100, 1), dtype=np.int16)]

            result = recorder.stop_recording()

            self.assertIsNotNone(result)
            self.assertFalse(recorder.is_recording)
            mock_stream.stop.assert_called_once()
            mock_stream.close.assert_called_once()

    def test_stop_recording_emits_signal(self):
        """Test that stop_recording() emits recording_stopped signal."""
        recorder = AudioRecorder()

        with patch('client.recorder.sd.InputStream') as MockStream:
            mock_stream = MagicMock()
            MockStream.return_value = mock_stream

            recorder.start_recording()

            # Add some mock audio data
            recorder._audio_data = [np.zeros((100, 1), dtype=np.int16)]

            with patch.object(recorder, 'recording_stopped') as mock_signal:
                recorder.stop_recording()
                mock_signal.emit.assert_called_once()

    def test_create_wav_bytes_returns_valid_wav(self):
        """Test that _create_wav_bytes returns valid WAV data."""
        recorder = AudioRecorder()

        # Create some test audio data
        audio_data = np.array([[100], [200], [300], [400]], dtype=np.int16)

        wav_bytes = recorder._create_wav_bytes(audio_data)

        # Check that we got bytes
        self.assertIsInstance(wav_bytes, bytes)
        self.assertGreater(len(wav_bytes), 0)

        # Verify WAV header (RIFF)
        self.assertEqual(wav_bytes[:4], b'RIFF')
        self.assertEqual(wav_bytes[8:12], b'WAVE')

    def test_audio_callback_appends_data_when_recording(self):
        """Test that _audio_callback appends data when recording."""
        recorder = AudioRecorder()
        recorder._is_recording = True
        recorder._audio_data = []

        # Simulate audio callback
        test_data = np.array([[100], [200]], dtype=np.int16)
        recorder._audio_callback(test_data, 2, None, None)

        self.assertEqual(len(recorder._audio_data), 1)

    def test_audio_callback_does_not_append_when_not_recording(self):
        """Test that _audio_callback doesn't append when not recording."""
        recorder = AudioRecorder()
        recorder._is_recording = False
        recorder._audio_data = []

        # Simulate audio callback
        test_data = np.array([[100], [200]], dtype=np.int16)
        recorder._audio_callback(test_data, 2, None, None)

        self.assertEqual(len(recorder._audio_data), 0)

    def test_stop_recording_with_no_data_returns_empty_bytes(self):
        """Test that stop_recording returns empty bytes if no audio captured."""
        recorder = AudioRecorder()

        with patch('client.recorder.sd.InputStream') as MockStream:
            mock_stream = MagicMock()
            MockStream.return_value = mock_stream

            recorder.start_recording()
            # No audio data added
            recorder._audio_data = []

            result = recorder.stop_recording()

            self.assertEqual(result, b'')


if __name__ == '__main__':
    unittest.main()
