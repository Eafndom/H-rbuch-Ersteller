import os
from core.file_extractor import FileExtractor
from core.memory_manager import ProfileManager
from core.llm_client import LLMClient
from core.tts_engine import EdgeTTSEngine
from core.audio_processor import AudioProcessor

def run_test():
    pm = ProfileManager("test_profiles")
    profile_path = pm.create_profile("test_profile")

    # Mock extract
    text = "Dies ist ein Test. Der Erzähler spricht. Der Monster grollt tief."

    extractor = FileExtractor()
    chunks = extractor.chunk_text(text)

    # Mock LLM Client
    class MockLLM:
        def process_chunk(self, text, mem):
            return mem, [{"speaker": "Erzähler", "text": "Dies ist ein Test.", "pitch": "0", "speed": 1.0, "effect": "none"}]

    llm = MockLLM()
    mem, script = llm.process_chunk(chunks[0], {})

    pm.append_script("test_profile", script)

    loaded_script = pm.load_script("test_profile")
    assert len(loaded_script) == 1

    # Mock TTS
    tts = EdgeTTSEngine()

    out_dir = os.path.join(profile_path, "audio_output")
    os.makedirs(out_dir, exist_ok=True)
    raw_path = os.path.join(out_dir, "raw_0.mp3")
    final_path = os.path.join(out_dir, "line_0.mp3")

    # Actually run edge_tts to make sure it works
    tts.generate_audio(loaded_script[0]["text"], raw_path, loaded_script[0])

    assert os.path.exists(raw_path)

    # Audio Processor
    ap = AudioProcessor()
    ap.apply_effect(raw_path, final_path, "none")

    assert os.path.exists(final_path)

    # Stitch
    final_stitched = os.path.join(out_dir, "final.mp3")
    ap.stitch_audio([final_path], final_stitched)

    assert os.path.exists(final_stitched)
    print("Pipeline test successful!")

if __name__ == "__main__":
    run_test()
