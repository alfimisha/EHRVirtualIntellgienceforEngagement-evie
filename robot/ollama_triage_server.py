#!/usr/bin/env python3
import json, re, subprocess, uuid
from flask import Flask, request, jsonify

app = Flask(__name__)
OLLAMA_MODEL = "llama3.2"

# Store conversation history per patient
sessions = {}

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
- Be conversational. If the patient says "maybe" or vague answers, ask a clarifying question.
- Keep it short: no more than 2–3 follow-ups.
- When ready, output ONLY a JSON object with:
  {{
    "emergency_index": number 0–100,
    "priority_label": "low|medium|high|critical",
    "rationale": "short explanation"
  }}

Conversation so far:
{convo_str}

Now either:
1. Ask the next question if more info is needed.
2. Or if you have enough info, output ONLY the JSON triage summary.
"""

    reply = call_ollama(prompt)

    # Check if reply is JSON (final result)
    try:
        json_str = re.sub(r"^```json|```$", "", reply.strip(), flags=re.MULTILINE).strip()
        result = json.loads(json_str)
        # End session once summary is given
        del sessions[patient_id]
        return jsonify(result)
    except Exception:
        # Otherwise, treat reply as a next question
        sessions[patient_id]["history"].append({"assistant": reply})
        return jsonify({"next_question": reply})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
