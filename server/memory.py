import json
import os
from datetime import datetime
import ollama

MEMORY_DIR = "memories"
os.makedirs(MEMORY_DIR, exist_ok=True)

def load_data(npc_id: str) -> dict:
    """Load full NPC data (memories + interaction counter)."""
    path = f"{MEMORY_DIR}/{npc_id}.json"
    if not os.path.exists(path):
        return {"interaction_count": 0, "memories": []}
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def save_data(npc_id: str, data: dict):
    """Save NPC data."""
    path = f"{MEMORY_DIR}/{npc_id}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def add_memory(npc_id: str, event: str, count_interaction: bool = False):
    """Add an observation to NPC memory stream."""
    data = load_data(npc_id)
    data["memories"].append({
        "time": datetime.now().isoformat(),
        "event": event
    })
    if count_interaction:
        data["interaction_count"] += 1
    # Keep last 50 memories
    if len(data["memories"]) > 50:
        data["memories"] = data["memories"][-50:]
    save_data(npc_id, data)

def load_memories(npc_id: str) -> list:
    """Load memories list for a given NPC."""
    return load_data(npc_id)["memories"]

def get_interaction_count(npc_id: str) -> int:
    """Return number of player interactions."""
    return load_data(npc_id)["interaction_count"]

def get_recent_memories(npc_id: str, n: int = 10) -> str:
    """Return N most recent memories as formatted text."""
    memories = load_memories(npc_id)
    recent = memories[-n:] if len(memories) >= n else memories
    if not recent:
        return "No memories yet."
    return "\n".join(f"- [{m['time'][:16]}] {m['event']}" for m in recent)

def reflect(npc_id: str) -> str:
    """Synthesize memories into high-level insights. Called every 5 interactions."""
    memories = load_memories(npc_id)
    if len(memories) < 5:
        return ""

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
    """Get current NPC plan. Regenerate every 10 interactions."""
    plan_path = f"{MEMORY_DIR}/{npc_id}_plan.txt"
    count = get_interaction_count(npc_id)

    should_replan = (
        not os.path.exists(plan_path) or
        count % 10 == 0
    )

    if not should_replan:
        with open(plan_path, encoding="utf-8") as f:
            return f.read()

    reflections = [
        m["event"] for m in load_memories(npc_id)
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
