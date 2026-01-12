#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import time
import json
import requests
import subprocess
import traceback
import MySQLdb
from datetime import datetime


# ================= CONFIG ===================
DEEPGRAM_API_KEY = ""
OPENAI_API_KEY=""

OPENAI_MODEL = "gpt-4o-mini"   # fast & cheap
# ============================================

# ---------------- AGI HELPER ----------------
def agi(cmd):
    sys.stdout.write(cmd + "\n")
    sys.stdout.flush()
    return sys.stdin.readline()

agi_env = {}

# --------------- READ AGI ENV ---------------
while True:
    line = sys.stdin.readline().strip()
    if not line:
        break
    key, val = line.split(":", 1)
    agi_env[key.strip()] = val.strip()
uniqueid = agi_env.get("agi_uniqueid")
caller   = agi_env.get("agi_callerid")
callee   = agi_env.get("agi_extension")


call_start = datetime.now()

db = MySQLdb.connect(
    host="localhost",
    user="root",
    passwd="tec@2020",
    db="asterisk_ai"
)
cursor = db.cursor()

cursor.execute("""
INSERT INTO calls (uniqueid, caller, callee, start_time)
VALUES (%s, %s, %s, %s)
""", (uniqueid, caller, callee, call_start))

db.commit()
agi('VERBOSE "VOICE AI AGENT STARTED" 1')

# -------- Conversation memory ---------------
prompt = """
You are an AI voice assistant for HR interview screening calls.
Your job is to conduct a short pre-interview screening.

Rules:
- Keep responses short, clear, and polite.
- Ask one question at a time.
- Do not explain too much.
- Confirm important details briefly.
- If the user gives unclear answers, ask again politely.

Your goals:
1. Collect candidate name
2. Ask years of experience
3. Ask desired job role
4. Ask availability for interview
5. End the call professionally

Conversation Flow:
- Greet the candidate
- Ask screening questions
- Thank the candidate and end the call
"""
conversation = [
    {"role": "system", "content": prompt}
]

def update_call_end(reason="normal"):
    try:
        call_end = datetime.now()
        duration = int((call_end - call_start).total_seconds())

        cursor.execute("""
        UPDATE calls
        SET end_time=%s,
            duration=%s,
            hangup_cause=%s
        WHERE uniqueid=%s
        """, (call_end, duration, reason, uniqueid))
        db.commit()

        agi('VERBOSE "CALL END UPDATED" 1')
    except Exception as e:
        agi(f'VERBOSE "FINAL DB ERROR: {e}" 1')


try:
    agi("ANSWER")

    turn = 1

    while True:
        agi(f'VERBOSE "TURN {turn}" 1')

        # ---------- RECORD AUDIO ----------
        agi('STREAM FILE beep ""')
        record_base = f"/tmp/user_{turn}"
        wav_file = record_base + ".wav"

        agi(f'RECORD FILE {record_base} wav "#" 20000 0 BEEP s=2')

        if not os.path.exists(wav_file):
            agi('VERBOSE "NO AUDIO FILE" 1')
            continue

        # ---------- DEEPGRAM STT ----------
        with open(wav_file, "rb") as f:
            audio_data = f.read()

        headers = {
            "Authorization": f"Token {DEEPGRAM_API_KEY}",
            "Content-Type": "audio/wav"
        }

        stt_resp = requests.post(
            "https://api.deepgram.com/v1/listen?model=nova-2&punctuate=true",
            headers=headers,
            data=audio_data,
            timeout=15
        )

        result = stt_resp.json()
        user_text = ""

        channels = result.get("results", {}).get("channels", [])
        if channels:
            for alt in channels[0].get("alternatives", []):
                if alt.get("transcript"):
                    user_text = alt["transcript"]
                    break

        agi(f'VERBOSE "USER SAID: {user_text}" 1')

        if not user_text:
            user_text = "I did not hear anything."

        conversation.append({"role": "user", "content": user_text})
        cursor.execute("""
        INSERT INTO conversations (uniqueid, turn, speaker, message)
        VALUES (%s, %s, 'user', %s)
        """, (uniqueid, turn, user_text))
        db.commit()

        # ---------- OPENAI LLM ----------
        llm_headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }

        llm_payload = {
            "model": OPENAI_MODEL,
            "messages": conversation,
            "temperature": 0.4
        }

        llm_resp = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=llm_headers,
            json=llm_payload,
            timeout=20
        )

        llm_data = llm_resp.json()
        bot_text = llm_data["choices"][0]["message"]["content"].strip()

        agi(f'VERBOSE "BOT REPLY: {bot_text}" 1')

        conversation.append({"role": "assistant", "content": bot_text})
        cursor.execute("""
        INSERT INTO conversations (uniqueid, turn, speaker, message)
        VALUES (%s, %s, 'bot', %s)
        """, (uniqueid, turn, bot_text))
        db.commit()


        # ---------- DEEPGRAM TTS ----------
        tts_wav = f"/tmp/bot_{turn}.wav"
        tts_8k  = f"/tmp/bot_{turn}_8k.wav"

        tts_headers = {
            "Authorization": f"Token {DEEPGRAM_API_KEY}",
            "Content-Type": "application/json"
        }

        tts_payload = {
            "text": bot_text
        }

        tts_resp = requests.post(
            "https://api.deepgram.com/v1/speak?model=aura-asteria-en&encoding=linear16&sample_rate=16000",
            headers=tts_headers,
            json=tts_payload,
            timeout=20
        )

        with open(tts_wav, "wb") as f:
            f.write(tts_resp.content)

        # Convert to 8kHz for Asterisk
        subprocess.run(
            ["sox", tts_wav, "-r", "8000", tts_8k],
            check=True
        )

        # ---------- PLAY AUDIO ----------
        agi(f'STREAM FILE {tts_8k.replace(".wav","")} ""')

        # ---------- EXIT CHECK ----------
        agi('VERBOSE "PRESS # TO END OR SPEAK AGAIN" 1')
        r = agi("WAIT FOR DIGIT 2000")

        if "result=-1" in r:
            update_call_end("hangup")
            break

        if "result=35" in r or "result=-1" in r:
            agi('VERBOSE "CALL ENDED" 1')
            break

        turn += 1

except Exception as e:
    agi('VERBOSE "FATAL AGI ERROR" 1')
    agi(f'VERBOSE "{str(e)}" 1')
    agi(f'VERBOSE "{traceback.format_exc()}" 1')
    update_call_end("error")

    time.sleep(5)
finally:
    call_end = datetime.now()
    duration = int((call_end - call_start).total_seconds())

    try:
        cursor.execute("""
        UPDATE calls
        SET end_time=%s,
            duration=%s,
            hangup_cause=%s
        WHERE uniqueid=%s
        """, (call_end, duration, "normal", uniqueid))
        db.commit()
        db.close()
    except:
        pass


       # Project rerun or run after days 
#sudo asterisk -rx "dialplan reload"
#sudo asterisk -rvvv

# sudo dos2unix /home/divya/Divya/diya/voice-agent/voice_agent_stt.py
# sudo chmod 755 /home/divya/Divya/diya/voice-agent/voice_agent_stt.py
# sudo apt install -y python3-requests
# sudo sed -i 's/\r$//' /home/divya/Divya/diya/voice-agent/voice_agent_stt.py
# ls -l /var/lib/asterisk/agi-bin/voice_agent_stt.py
            # lrwxrwxrwx 1 root root 53 Jan  8 17:45 /var/lib/asterisk/agi-bin/voice_agent_stt.py -> /home/divya/Divya/diya/voice-agent/voice_agent_stt.py

# sudo rm -f /var/lib/asterisk/agi-bin/voice_agent_stt.py
# sudo ln -s /home/divya/Divya/diya/voice-agent/voice_agent_stt.py /var/lib/asterisk/agi-bin/voice_agent_stt.py
