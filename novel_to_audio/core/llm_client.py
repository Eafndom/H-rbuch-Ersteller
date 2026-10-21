import json
from openai import OpenAI
from typing import Dict, Any, List, Tuple

class LLMClient:
    def __init__(self, api_key: str, base_url: str = "https://opencode.ai/zen/go/v1", model: str = "deepseek"):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def process_chunk(self, chunk_text: str, current_memory: Dict[str, Any]) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Sends the text chunk and memory to the LLM and returns updated memory and the audio script.
        """
        prompt = self._build_prompt(chunk_text, current_memory)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional audio drama scriptwriter and character consistency engine."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.7
            )

            result_text = response.choices[0].message.content
            result_json = json.loads(result_text)

            updated_memory = result_json.get("memory_update", current_memory)
            audio_script = result_json.get("audio_script", [])

            # Simple merge for characters
            if "characters" in updated_memory and "characters" in current_memory:
                for char, attrs in updated_memory["characters"].items():
                    current_memory["characters"][char] = attrs

            return current_memory, audio_script

        except Exception as e:
            # Fallback or re-raise
            raise RuntimeError(f"Error communicating with LLM: {str(e)}")

    def _build_prompt(self, chunk_text: str, current_memory: Dict[str, Any]) -> str:
        memory_str = json.dumps(current_memory, indent=2, ensure_ascii=False)
        return f"""
We are creating a multi-role audio drama from a novel.

Current Story Memory & Characters:
{memory_str}

Please process the following text chunk.
1. Condense long "status window" spam, long descriptions, or repetitive info.
2. Rewrite the narrative into an audio drama script with speaker roles. Use "Erzähler" for the narrator.
3. Assign audio parameters for each line:
   - pitch: integer or string (e.g., -4 for monster, peak high for panic)
   - speed: float (e.g., 0.8 to 1.2)
   - effect: string (e.g., 'none', 'reverb', 'bass_boost', 'radio_distortion')
4. Identify any NEW characters or updated attributes (like a change in tone/status) and provide them in "memory_update".

Return EXACTLY a JSON object with this structure:
{{
  "memory_update": {{
    "characters": {{
       "CharacterName": {{"gender": "...", "tone": "...", "pitch_default": "...", "effect_default": "..."}}
    }},
    "summary": "Updated brief summary of the story so far"
  }},
  "audio_script": [
    {{
      "speaker": "Erzähler",
      "text": "The dark corridor echoed...",
      "pitch": "0",
      "speed": 1.0,
      "effect": "none"
    }},
    {{
      "speaker": "Space Monster",
      "text": "Grrrr, who goes there?",
      "pitch": "-4",
      "speed": 0.8,
      "effect": "reverb"
    }}
  ]
}}

Text Chunk:
{chunk_text}
"""
