from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import FileResponse
from faster_whisper import WhisperModel
from memory import add_memory, get_recent_memories, reflect, get_or_create_plan, get_interaction_count
import edge_tts
import ollama
import json

app = FastAPI()
whisper = WhisperModel("base", device="cpu", compute_type="int8")
# device="cpu" — runs on CPU, no GPU required
# compute_type="int8" — faster inference on CPU

SYSTEM_PROMPT = """
You are a villager NPC in a fantasy world.
You have memories of past conversations and a personal plan.

Always respond ONLY in valid JSON. No extra text, no markdown.

Format:
{
  "reply_text": "Your spoken reply (1-2 sentences, in character)",
  "action": "none|point|give_quest|open_shop",
  "target": "poi_id from WORLD_CONTEXT or null"
}

Rules:
- Stay in character, use your memories naturally
- action rules:
  - "point": when player asks WHERE something is — use this to point at a location
  - "give_quest": when player asks for help with a task or problem
  - "open_shop": when player wants to buy something
  - "none": for general conversation
- target: only IDs from WORLD_CONTEXT, or null
- Never break the JSON format
"""

@app.get("/npc")
def npc_reply(text: str):
    resp = ollama.chat(
        model="mistral",
        messages=[
            {"role": "system", "content": "You are a villager in a fantasy kingdom. Keep answers short. You have a memory of past conversations — use it naturally in your responses."},
            {"role": "user", "content": text}
        ]
    )
    return {"reply": resp["message"]["content"]}

@app.post("/voice")
async def voice(
    file: UploadFile,
    world_context: str = Form(""),
    npc_id: str = Form("default")
):
    # STT — save uploaded audio and transcribe
    path = "voice.wav"
    with open(path, "wb") as f:
        f.write(await file.read())

    segments, _ = whisper.transcribe(path)
    player_text = " ".join(s.text for s in segments).strip()

    # Memory — record interaction and increment counter
    add_memory(npc_id, f"Player said: '{player_text}'", count_interaction=True)

    # Reflection every 5 interactions
    count = get_interaction_count(npc_id)
    if count % 5 == 0:
        insights = reflect(npc_id)
        if insights:
            print(f"[REFLECTION] {insights}")

    recent   = get_recent_memories(npc_id, n=8)
    npc_plan = get_or_create_plan(npc_id)  # updates every 10 interactions
    print(f"[PLAN] {npc_plan}")

    # LLM — generate structured response
    raw = ollama.chat(
        model="mistral",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "system", "content": f"YOUR CURRENT PLAN:\n{npc_plan}"},
            {"role": "system", "content": f"YOUR RECENT MEMORIES:\n{recent}"},
            {"role": "system", "content": f"WORLD_CONTEXT: {world_context}"},
            {"role": "user",   "content": player_text}
        ]
    )["message"]["content"]

    # JSON validation — fallback if model breaks format
    try:
        decision = json.loads(raw)
    except json.JSONDecodeError:
        decision = {"reply_text": raw, "action": "none", "target": None}

    reply_text = decision.get("reply_text", raw)
    add_memory(npc_id, f"I replied: '{reply_text}'")

    # TTS — generate MP3 response
    communicate = edge_tts.Communicate(reply_text, voice="en-GB-RyanNeural")
    await communicate.save("reply.mp3")

    # Return audio + JSON decision in header
    response = FileResponse("reply.mp3", media_type="audio/mpeg")
    response.headers["X-NPC-Decision"] = json.dumps(decision)
    return response
