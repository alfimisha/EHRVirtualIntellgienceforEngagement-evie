#!/usr/bin/env python3
import cv2, time, json, requests, subprocess, platform, serial
from vosk import Model, KaldiRecognizer
import pandas as pd
from ehr_parser import get_patient_context, get_full_name

CONFIG = {
    "server_url": "http://127.0.0.1:8000/triage",   # Flask server + Ollama
    "vosk_model": "./vosk-model-small-en-us-0.15",
    "camera_index": 0,
    "haar_cascade": "{cv2_haar}/haarcascade_frontalface_default.xml",
    "esp32_port": "/dev/cu.usbserial-1130",   # 🔥 replace with your ESP32 device port
    "esp32_baud": 115200
}

# ---- Serial to ESP32 ----
try:
    ser = serial.Serial(CONFIG["esp32_port"], CONFIG["esp32_baud"], timeout=1)
    print("[ESP32] Connected on", CONFIG["esp32_port"])
except Exception as e:
    ser = None
    print("[ESP32] Serial not available:", e)

def send_gpio(cmd):
    """Send HIGH/LOW to ESP32 over serial."""
    if ser:
        try:
            ser.write((cmd + "\n").encode())
            print(f"[ESP32] Sent: {cmd}")
        except Exception as e:
            print("[ESP32] Send failed:", e)

# ---- auto TTS ----
if platform.system() == "Darwin":
    TTS_CMD = "say"
else:
    TTS_CMD = "espeak"

def say(text):
    if not text:
        return
    try:
        subprocess.run([TTS_CMD, text], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        print(f"[TTS skipped] {text}")

def shutil_which(cmd):
    from shutil import which
    return which(cmd) is not None

# ---- Vosk STT ----
vosk_model = Model(CONFIG["vosk_model"])

def ask(prompt, seconds=4):
    say(prompt)
    print("Q:", prompt)
    rec = KaldiRecognizer(vosk_model, 16000)

    if shutil_which("arecord"):
        cmd = ["arecord","-q","-d",str(seconds),"-f","S16_LE","-r","16000","-c","1"]
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

# Load patient list once
patients_df = pd.read_csv("patients.csv")
patient_index = 0

say("Triage system ready. Waiting for a patient.")
cooldown_until = 0
face_cleared = True   # Ensures old face disappears first

while True:
    ok, frame = cap.read()
    if not ok:
        continue

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = cascade.detectMultiScale(gray, 1.2, 5, minSize=(60,60))

    # Draw faces
    for (x,y,w,h) in faces:
        cv2.rectangle(frame,(x,y),(x+w,y+h),(0,255,0),2)

    now = time.time()

    if now < cooldown_until:
        cv2.putText(frame, "Moving to next patient...", (30,30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,255), 2)
        cv2.imshow("Triage Face", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        continue

    cv2.imshow("Triage Face", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

    if len(faces) == 0:
        face_cleared = True

    if len(faces) > 0 and face_cleared:
        face_cleared = False
        send_gpio("HIGH")   # 🔥 Face detected → GPIO22 HIGH

        if patient_index < len(patients_df):
            pid = str(patients_df.iloc[patient_index]["Id"])
            ehr_dict = get_patient_context(pid)
            patient_index += 1
        else:
            pid = f"anon-{int(time.time())}"
            ehr_dict = {"note": "No more patients in dataset"}

        name = get_full_name(patients_df.iloc[patient_index - 1])
        say(f"Hello {name}. I will use your record for this session.")

        # Conversation loop with server
        answer = ""
        while True:
            try:
                payload = {"patient_id": pid, "ehr": ehr_dict, "answer": answer}
                resp = requests.post(CONFIG["server_url"], json=payload, timeout=60).json()
            except Exception as e:
                print("Error contacting server:", e)
                break

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
                break
            else:
                print("Unexpected response:", resp)
                break

        say("Thank you. I will continue rounds now.")
        cooldown_until = time.time() + 10
        send_gpio("LOW")    # 🔥 After session → GPIO22 LOW
