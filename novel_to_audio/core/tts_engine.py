import os
import asyncio
from typing import Dict, Any

class TTSEngine:
    def generate_audio(self, text: str, output_path: str, params: Dict[str, Any]):
        raise NotImplementedError

class EdgeTTSEngine(TTSEngine):
    def __init__(self):
        # Basic mapping for characters (can be extended)
        self.voice_map = {
            "default": "en-US-AriaNeural",
            "Erzähler": "de-DE-KillianNeural", # German narrator
            "female": "de-DE-KatjaNeural",
            "male": "de-DE-ConradNeural",
            "monster": "de-DE-BerndNeural"
        }

    def generate_audio(self, text: str, output_path: str, params: Dict[str, Any]):
        """
        Uses Edge-TTS to generate audio. Since edge-tts is an async library,
        we run it in a synchronous wrapper for simplicity in threads, or use asyncio.run.
        """
        try:
            import edge_tts
        except ImportError:
            raise ImportError("Please install edge-tts to use the EdgeTTSEngine.")

        speaker = params.get("speaker", "default")
        # Try to map based on some heuristic or use default narrator
        voice = self.voice_map.get(speaker, self.voice_map["Erzähler"])

        # We can map speed to edge-tts rate parameter
        speed = params.get("speed", 1.0)
        rate_str = f"+{int((speed - 1.0) * 100)}%" if speed >= 1.0 else f"{int((speed - 1.0) * 100)}%"

        # Pitch
        pitch_val = params.get("pitch", "0")
        try:
            pitch_float = float(pitch_val)
            pitch_str = f"+{int(pitch_float * 10)}Hz" if pitch_float >= 0 else f"{int(pitch_float * 10)}Hz"
        except ValueError:
            pitch_str = "+0Hz" # Fallback if pitch is 'peak high' etc., can refine later.

        async def _generate():
            communicate = edge_tts.Communicate(text, voice, rate=rate_str, pitch=pitch_str)
            await communicate.save(output_path)

        asyncio.run(_generate())

# Placeholder for Kokoro
class KokoroTTSEngine(TTSEngine):
    def generate_audio(self, text: str, output_path: str, params: Dict[str, Any]):
        # Implementation for Kokoro would go here
        raise NotImplementedError("Kokoro-TTS is not fully implemented in this wrapper yet.")
