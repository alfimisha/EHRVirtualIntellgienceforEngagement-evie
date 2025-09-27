#!/usr/bin/env python3
import cv2, time, json, requests, subprocess, platform
from vosk import Model, KaldiRecognizer

CONFIG = {
    "server_url": "http://127.0.0.1:8000/triage",   # Flask server + Ollama
    "vosk_model": "./vosk-model-small-en-us-0.15",
    "camera_index": 0,
    "haar_cascade": "{cv2_haar}/haarcascade_frontalface_default.xml",
}

# ---- auto TTS ----
if platform.system() == "Darwin":   # macOS
    TTS_CMD = "say"
else:                               # Linux/Edison
    TTS_CMD = "espeak"

def say(text):
    if not text: return
    try:
        subprocess.run([TTS_CMD, text], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        print(f"[TTS skipped] {text}")

def shutil_which(cmd):
    from shutil import which
    return which(cmd) is not None

# ---- Critical alert helper ----
def send_critical_alert(patient_id, score, priority, rationale):
    """Send critical patient info to the laptop Flask backend."""
    try:
        LAPTOP_SERVER_URL = "http://192.168.56.1:5000/alert"  # Replace with your laptop's IP
        payload = {
            "patient_id": patient_id,
            "name": f"Patient-{patient_id}",
            "score": score,
            "priority": priority,
            "rationale": rationale
        }
        r = requests.post(LAPTOP_SERVER_URL, json=payload, timeout=10)
        if r.ok:
            print(f"[ALERT SENT] Patient {patient_id} flagged as critical.")
        else:
            print(f"[ALERT FAILED] Status: {r.status_code}")
    except Exception as e:
        print(f"[ALERT ERROR] Could not send alert: {e}")

# ---- Vosk STT ----
vosk_model = Model(CONFIG["vosk_model"])

def ask(prompt, seconds=4):
    """Speak a prompt, capture audio reply, transcribe with Vosk."""
    say(prompt)
    print("Q:", prompt)
    rec = KaldiRecognizer(vosk_model, 16000)

    # Linux: arecord
    if shutil_which("arecord"):
        cmd = ["arecord","-q","-d",str(seconds),"-f","S16_LE","-r","16000","-c","1"]
    # macOS: SoX 'rec'
    elif shutil_which("rec"):
        cmd = [
            "rec", "-q", "-c", "1", "-b", "16", "-r", "16000",
            "-e", "signed-integer", "-t", "raw", "-", "trim", "0", str(seconds)
        ]
    else:
        return input("Type answer: ")

    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    text = ""
    while True:
        data = proc.stdout.read(4000)
        if not data: break
        if rec.AcceptWaveform(data):
            part = json.loads(rec.Result()).get("text", "")
            text += " " + part
    part = json.loads(rec.FinalResult()).get("text", "")
    text += " " + part
    ans = text.strip()
    print("A:", ans)
    return ans


# ---- Face detection ----
haar = CONFIG["haar_cascade"].replace("{cv2_haar}", cv2.data.haarcascades)
cap = cv2.VideoCapture(CONFIG["camera_index"])
cascade = cv2.CascadeClassifier(haar)

say("Triage system ready. Waiting for a patient.")
cooldown_until = 0

while True:
    ok, frame = cap.read()
    if not ok:
        continue

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = cascade.detectMultiScale(gray, 1.2, 5, minSize=(60,60))

    # Draw faces
    for (x,y,w,h) in faces:
        cv2.rectangle(frame,(x,y),(x+w,y+h),(0,255,0),2)

    # Cooldown overlay
    now = time.time()
    if now < cooldown_until:
        cv2.putText(frame, "Moving to next patient...", (30,30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,255), 2)
        cv2.imshow("Triage Face", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        continue

    # Normal display
    cv2.imshow("Triage Face", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

    # Engage if a face detected
    if len(faces) > 0:
        say("Hello. Please state your patient ID.")
        pid = ask("Please say or type your patient ID.") or f"anon-{int(time.time())}"

        # Conversation loop with server
        answer = ""
        while True:
            try:
                payload = {"patient_id": pid, "ehr": {"age": 77}, "answer": answer}
                resp = requests.post(CONFIG["server_url"], json=payload, timeout=60).json()
            except Exception as e:
                print("Error contacting server:", e)
                break

            # Check server response
            if "next_question" in resp:
                q = resp["next_question"]
                answer = ask(q)
                continue

            elif "emergency_index" in resp:
                score = int(resp.get("emergency_index", 0))
                priority = resp.get("priority_label", "low")
                rationale = resp.get("rationale", "")
                print("Triage result:", resp)
                say(f"Your triage score is {score}. Priority {priority}.")

                # ---- Send critical alert if score > 60 ----
                if score > 60:
                    send_critical_alert(pid, score, priority, rationale)

                break

            else:
                print("Unexpected response:", resp)
                break

        say("Thank you. I will continue rounds now.")
        cooldown_until = time.time() + 10
