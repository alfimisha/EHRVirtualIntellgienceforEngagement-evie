#!/usr/bin/env python3
import cv2, os, sys, time, json, re, requests, subprocess, platform
from vosk import Model, KaldiRecognizer

CONFIG = {
    "server_url": "http://127.0.0.1:8000/triage",   # Flask server + Ollama
    "vosk_model": "./vosk-model-small-en-us-0.15",
    "camera_index": 0,
    "haar_cascade": "{cv2_haar}/haarcascade_frontalface_default.xml",
    "questions": [
        {"id": "pain", "prompt": "On a scale of zero to ten, what is your pain level?", "expect": "number_0_10"},
        {"id": "breath", "prompt": "Are you short of breath? Yes or no.", "expect": "yes_no"},
        {"id": "dizziness", "prompt": "Do you feel dizzy right now? Yes or no.", "expect": "yes_no"},
        {"id": "nausea", "prompt": "Are you experiencing nausea? Yes or no.", "expect": "yes_no"},
        {"id": "confusion", "prompt": "Are you feeling confused or disoriented? Yes or no.", "expect": "yes_no"}
    ]
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

def parse_yesno(s):
    s = s.lower()
    if "yes" in s or "yeah" in s: return True
    if "no" in s: return False
    return None

def strip_num(s):
    m = re.search(r"\d+", s)
    return int(m.group(0)) if m else None

def shutil_which(cmd):
    from shutil import which
    return which(cmd) is not None

# ---- Vosk STT ----
vosk_model = Model(CONFIG["vosk_model"])

def ask(prompt, seconds=4):
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

    # Fallback: manual typing
    else:
        return input("Type answer: ")

    # Launch recorder
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    text = ""
    while True:
        data = proc.stdout.read(4000)
        if not data:
            break
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

    # Draw faces (green boxes)
    for (x,y,w,h) in faces:
        cv2.rectangle(frame,(x,y),(x+w,y+h),(0,255,0),2)

    # If in cooldown → overlay text
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

    # Engage if face detected
    if len(faces) > 0:
        say("Hello. Please state your patient ID.")
        pid = ask("Please say or type your patient ID.") or f"anon-{int(time.time())}"

        # Collect answers
        answers = {}
        for q in CONFIG["questions"]:
            raw = ask(q["prompt"])
            if q["expect"] == "number_0_10":
                answers[q["id"]] = strip_num(raw) or 0
            elif q["expect"] == "yes_no":
                answers[q["id"]] = parse_yesno(raw)
            else:
                answers[q["id"]] = raw

        payload = {
            "patient_id": pid,
            "ehr": {"age": 77, "o2_baseline": 93, "hr_baseline": 92, "dx_count": 4},
            "answers": answers
        }

        try:
            resp = requests.post(CONFIG["server_url"], json=payload, timeout=60)
            data = resp.json()
            print("Server response:", data)
            say(f"Your triage score is {int(data['emergency_index'])}. Priority {data['priority_label']}.")
        except Exception as e:
            print("Error contacting server:", e)

        say("Thank you. I will continue rounds now.")

        # ⏱️ Enter cooldown for 10 seconds (simulate moving away)
        cooldown_until = time.time() + 10
