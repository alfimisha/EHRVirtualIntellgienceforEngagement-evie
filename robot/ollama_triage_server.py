#!/usr/bin/env python3
import json, re, subprocess, uuid
from flask import Flask, request, jsonify

app = Flask(__name__)
OLLAMA_MODEL = "llama3.2"

# Store conversation history per patient
sessions = {}

# ---- Helper to run Ollama ----
def call_ollama(prompt):
    try:
        result = subprocess.run(
            ["ollama", "run", OLLAMA_MODEL],
            input=prompt.encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=60
        )
        return result.stdout.decode("utf-8").strip()
    except Exception as e:
        return f"ERROR: {e}"

# ---- Helper to extract JSON safely ----
def extract_json(text: str):
    """Return first valid JSON object found in text, or None."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except Exception:
        return None

@app.route("/triage", methods=["POST"])
def triage():
    data = request.get_json(force=True)
    patient_id = data.get("patient_id", str(uuid.uuid4()))
    ehr = data.get("ehr", {})
    answer = data.get("answer", "")

    # Initialize session if new
    if patient_id not in sessions:
        sessions[patient_id] = {
            "ehr": ehr,
            "history": []
        }

    # Add patient response to history if provided
    if answer:
        sessions[patient_id]["history"].append({"patient": answer})

    # Build conversation history string
    convo = sessions[patient_id]["history"]
    convo_str = "\n".join(
        [f"Patient: {h['patient']}" if "patient" in h else f"Assistant: {h['assistant']}"
         for h in convo]
    )

    # Prompt for LLM
    prompt = f"""
You are a clinical triage assistant robot.

Context:
- Patient EHR: {json.dumps(ehr)}
- Your goal is to check on the patient, clarify symptoms, and decide urgency.
- Do not read out the patient id. 
- Do not talk in third person. There's only 2 people: you and the patient. 
- Be conversational. If the patient says "maybe" or vague answers, ask a clarifying question.
- Your maximum number of follow up questions is 5.
- Keep it short: no more than 2–3 follow-ups. 
- DO NOT REPEAT THE SAME THING MULTIPLE TIMES.
- When ready, output ONLY a JSON object with:
  {{
    "emergency_index": number 0–100,
    "priority_label": "low|medium|high|critical",
    "rationale": "short explanation"
  }}

Conversation so far:
{convo_str}

Now either:
1. Ask the next question if more info is needed (but only if you’ve asked fewer than 5 questions total).
2. Or if you have enough info, output ONLY the JSON triage summary.
"""

    reply = call_ollama(prompt).strip()

    # ---- 1) Stop at first valid JSON ----
    result = extract_json(reply)
    if result:
        del sessions[patient_id]   # End session immediately
        return jsonify(result)

    # ---- 2) Enforce hard cap of 5 questions ----
        # ---- 2) Enforce hard cap of 5 questions ----
    history = sessions[patient_id]["history"]
    assistant_turns = sum(1 for h in history if "assistant" in h)
    if assistant_turns >= 5:
        # Force Ollama one last time to output JSON
        final_prompt = f"""
You are a clinical triage assistant robot.
You have already asked 5 follow-up questions. 
Now you MUST STOP asking questions and output ONLY the final triage summary.

Patient EHR: {json.dumps(ehr)}
Conversation so far:
{convo_str}

Output ONLY a JSON object in this exact format:
{{
  "emergency_index": number 0–100,
  "priority_label": "low|medium|high|critical",
  "rationale": "short explanation"
}}
"""
        reply = call_ollama(final_prompt).strip()
        result = extract_json(reply)
        del sessions[patient_id]

        if result:
            return jsonify(result)
        else:
            # Fallback if still no valid JSON
            return jsonify({
                "emergency_index": 65,
                "priority_label": "medium",
                "rationale": "Unsure what symptoms mean, insufficient info, defaulting to 65"
            })


    # Otherwise treat reply as next question
    sessions[patient_id]["history"].append({"assistant": reply})
    return jsonify({"next_question": reply})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
