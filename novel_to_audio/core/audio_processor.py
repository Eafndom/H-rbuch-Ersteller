import os
from typing import List, Dict, Any

class AudioProcessor:
    def __init__(self):
        pass

    def apply_effect(self, input_path: str, output_path: str, effect: str):
        """
        Applies basic effects to an audio file using pydub/pedalboard.
        If no effect or 'none', simply copies or renames.
        """
        if effect == "none" or not effect:
            if input_path != output_path:
                import shutil
                shutil.copy2(input_path, output_path)
            return

        try:
            from pydub import AudioSegment
        except ImportError:
            raise ImportError("Please install pydub to apply audio effects.")

        audio = AudioSegment.from_file(input_path)

        if effect == "reverb":
            # Simple simulation using pydub overlay (not true reverb, but a poor man's version)
            # For real reverb, pedalboard is better.
            delayed = audio - 5
            audio = audio.overlay(delayed, position=50)
        elif effect == "bass_boost":
            # Boost low frequencies
            audio = audio.low_pass_filter(250).apply_gain(5) + audio
        elif effect == "radio_distortion":
            # Telephone effect: bandpass filter
            audio = audio.high_pass_filter(300).low_pass_filter(3000)

        audio.export(output_path, format="mp3")

    def stitch_audio(self, input_paths: List[str], output_path: str, pause_ms: int = 300):
        """
        Stitches multiple audio files together with a given pause between them.
        """
        if not input_paths:
            return

        try:
            from pydub import AudioSegment
        except ImportError:
            raise ImportError("Please install pydub to stitch audio files.")

        final_audio = AudioSegment.empty()
        silence = AudioSegment.silent(duration=pause_ms)

        for path in input_paths:
            if os.path.exists(path):
                segment = AudioSegment.from_file(path)
                final_audio += segment + silence

        final_audio.export(output_path, format="mp3")
