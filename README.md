# Unity LLM NPC System

Voice-enabled NPC system for Unity based on Generative Agents architecture.

## Structure

```
server/
  main.py       — FastAPI server: STT + LLM + TTS
  memory.py     — Memory Stream, Reflection, Planning

unity/Assets/Scripts/
  NPCClient.cs           — Push-to-Talk, sends audio to server
  WorldContextBuilder.cs — Builds world context JSON
  NPCController.cs       — Applies NPC decisions (point, quest, shop)
  NPCResponse.cs         — JSON response structure
```

## Setup

### Server
```bash
pip install fastapi uvicorn ollama faster-whisper edge-tts python-multipart
ollama run mistral
python -m uvicorn main:app --reload
```

### Unity
- Install Input System package
- Add WavUtility.cs from https://github.com/deadlyfingers/UnityWav
- Attach to one GameObject: NPCClient, WorldContextBuilder, NPCController, AudioSource
- Create empty GameObjects in scene named: tavern, blacksmith, market, tower, crypt, alchemist

## Based on
Park J.S. et al. "Generative Agents: Interactive Simulacra of Human Behavior"
https://arxiv.org/abs/2304.03442
