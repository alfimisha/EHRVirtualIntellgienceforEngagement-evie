#!/usr/bin/env python3
import json, re, subprocess
from flask import Flask, request, jsonify

app = Flask(__name__)

OLLAMA_MODEL = "llama3.2"   # or "phi3", "mistral", etc.

def call_ollama(prompt):
    try:
        result = subprocess.run(
            ["ollama", "run", OLLAMA_MODEL],
            input=prompt.encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=60
        )
        text = result.stdout.decode("utf-8").strip()
        # strip any code fences
        text = re.sub(r"^```json|```$", "", text, flags=re.MULTILINE).strip()
        return text
    except Exception as e:
        return None

@app.route("/triage", methods=["POST"])
def triage():
    data = request.get_json(force=True)
    ehr = data.get("ehr", {})
    answers = data.get("answers", {})

    prompt = (
        "You are a clinical triage assistant. "
        "Given EHR data and questionnaire answers, output ONLY valid JSON with fields: "
        "emergency_index (0-100), priority_label (low|medium|high|critical), rationale.\n\n"
        f"EHR: {json.dumps(ehr)}\n"
        f"Answers: {json.dumps(answers)}\n\n"
        "Return only JSON."
    )

    raw = call_ollama(prompt)
    try:
        resp = json.loads(raw)
    except Exception:
        resp = {
            "emergency_index": 0,
            "priority_label": "low",
            "rationale": f"Parsing failed. Raw response: {raw}"
        }
    return jsonify(resp)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
