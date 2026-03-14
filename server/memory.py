import json
import os
from datetime import datetime
import ollama

MEMORY_DIR = "memories"
os.makedirs(MEMORY_DIR, exist_ok=True)

def add_memory(npc_id: str, event: str):
    """Add an observation to NPC memory stream."""
    path = f"{MEMORY_DIR}/{npc_id}.json"
    memories = load_memories(npc_id)
    memories.append({
        "time": datetime.now().isoformat(),
        "event": event
    })
    # Keep last 50 memories
    if len(memories) > 50:
        memories = memories[-50:]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(memories, f, ensure_ascii=False, indent=2)

def load_memories(npc_id: str) -> list:
    """Load all memories for a given NPC."""
    path = f"{MEMORY_DIR}/{npc_id}.json"
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def get_recent_memories(npc_id: str, n: int = 10) -> str:
    """Return N most recent memories as formatted text."""
    memories = load_memories(npc_id)
    recent = memories[-n:] if len(memories) >= n else memories
    if not recent:
        return "No memories yet."
    return "\n".join(f"- [{m['time'][:16]}] {m['event']}" for m in recent)

def reflect(npc_id: str) -> str:
    """Synthesize memories into high-level insights. Called every N interactions."""
    memories = load_memories(npc_id)
    if len(memories) < 5:
        return ""  # Not enough data yet

    recent = memories[-20:]
    memory_text = "\n".join(f"- {m['event']}" for m in recent)

    response = ollama.chat(
        model="mistral",
        messages=[
            {
                "role": "system",
                "content": "You are analyzing an NPC's memories. Be concise."
            },
            {
                "role": "user",
                "content": (
                    f"Based on these recent memories of NPC '{npc_id}':\n"
                    f"{memory_text}\n\n"
                    "Write 3 short insights about this player and situation. "
                    "Format: bullet points, max 1 sentence each."
                )
            }
        ]
    )

    insights = response["message"]["content"]
    add_memory(npc_id, f"[REFLECTION] {insights}")
    return insights

def get_or_create_plan(npc_id: str) -> str:
    """Get current NPC plan. Regenerate if outdated."""
    plan_path = f"{MEMORY_DIR}/{npc_id}_plan.txt"
    memories  = load_memories(npc_id)

    should_replan = (
        not os.path.exists(plan_path) or
        len(memories) % 10 == 0
    )

    if not should_replan:
        with open(plan_path, encoding="utf-8") as f:
            return f.read()

    # Use reflections as basis for planning
    reflections = [
        m["event"] for m in memories
        if "[REFLECTION]" in m["event"]
    ]
    reflection_text = "\n".join(reflections[-3:]) if reflections else "No reflections yet."

    response = ollama.chat(
        model="mistral",
        messages=[
            {
                "role": "system",
                "content": "You are a fantasy NPC planning your behavior. Be concise."
            },
            {
                "role": "user",
                "content": (
                    f"You are NPC '{npc_id}', a villager.\n"
                    f"Your recent insights:\n{reflection_text}\n\n"
                    "Write your current intentions as 2-3 short bullet points. "
                    "Example: '- Help lost travelers find the tavern'"
                )
            }
        ]
    )

    plan = response["message"]["content"]
    with open(plan_path, "w", encoding="utf-8") as f:
        f.write(plan)
    return plan
