#!/usr/bin/env python3
from flask import Flask, request, jsonify
import time, json, os

app = Flask(__name__)
ALERT_FILE = "critical_alerts.json"
alerts = []  # in-memory queue

# ---- Helpers ----
def save_alerts():
    with open(ALERT_FILE, "w") as f:
        json.dump(alerts, f, indent=2)

def load_alerts():
    global alerts
    if os.path.exists(ALERT_FILE):
        with open(ALERT_FILE, "r") as f:
            alerts = json.load(f)

# ---- Routes ----
@app.route("/alert", methods=["POST"])
def receive_alert():
    """Receive critical patient alert from Edison."""
    data = request.get_json(force=True)
    if not data:
        return jsonify({"status": "error", "msg": "No data received"}), 400

    entry = {
        "patient_id": data.get("patient_id", "unknown"),
        "name": data.get("name", "unknown"),
        "score": data.get("score", 0),
        "priority": data.get("priority", "unknown"),
        "rationale": data.get("rationale", ""),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    }

    alerts.append(entry)
    save_alerts()

    print(f"[ALERT RECEIVED] {entry}")
    return jsonify({"status": "ok", "msg": "Alert queued"})

@app.route("/alerts", methods=["GET"])
def get_alerts():
    """Return the current alert queue."""
    return jsonify(alerts)

@app.route("/clear", methods=["POST"])
def clear_alerts():
    """Clear the alert queue (after HCP acknowledgment)."""
    alerts.clear()
    save_alerts()
    return jsonify({"status": "ok", "msg": "Queue cleared"})

if __name__ == "__main__":
    load_alerts()
    app.run(host="0.0.0.0", port=5000)
