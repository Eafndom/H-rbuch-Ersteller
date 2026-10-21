import os
import json
from typing import Dict, Any, List

class ProfileManager:
    def __init__(self, base_dir: str = "novel_to_audio/profiles"):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def get_profile_path(self, profile_name: str) -> str:
        return os.path.join(self.base_dir, profile_name)

    def create_profile(self, profile_name: str) -> str:
        """
        Creates a new profile directory and initializes its files.
        """
        profile_path = self.get_profile_path(profile_name)
        os.makedirs(profile_path, exist_ok=True)
        os.makedirs(os.path.join(profile_path, "audio_output"), exist_ok=True)

        # Initialize config
        self._write_json(os.path.join(profile_path, "profile_config.json"), {
            "name": profile_name,
            "status": "created",
            "current_chunk": 0,
            "total_chunks": 0
        })

        # Initialize memory
        self._write_json(os.path.join(profile_path, "story_memory.json"), {
            "characters": {},
            "summary": "Initial memory.",
            "tone": "Neutral."
        })

        # Initialize audio script
        self._write_json(os.path.join(profile_path, "audio_script.json"), [])

        return profile_path

    def load_config(self, profile_name: str) -> Dict[str, Any]:
        path = os.path.join(self.get_profile_path(profile_name), "profile_config.json")
        return self._read_json(path)

    def save_config(self, profile_name: str, config: Dict[str, Any]):
        path = os.path.join(self.get_profile_path(profile_name), "profile_config.json")
        self._write_json(path, config)

    def load_memory(self, profile_name: str) -> Dict[str, Any]:
        path = os.path.join(self.get_profile_path(profile_name), "story_memory.json")
        return self._read_json(path)

    def save_memory(self, profile_name: str, memory: Dict[str, Any]):
        path = os.path.join(self.get_profile_path(profile_name), "story_memory.json")
        self._write_json(path, memory)

    def load_script(self, profile_name: str) -> List[Dict[str, Any]]:
        path = os.path.join(self.get_profile_path(profile_name), "audio_script.json")
        return self._read_json(path)

    def append_script(self, profile_name: str, new_script_items: List[Dict[str, Any]]):
        script = self.load_script(profile_name)
        script.extend(new_script_items)
        path = os.path.join(self.get_profile_path(profile_name), "audio_script.json")
        self._write_json(path, script)

    def _read_json(self, path: str) -> Any:
        if not os.path.exists(path):
            return {}
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _write_json(self, path: str, data: Any):
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
