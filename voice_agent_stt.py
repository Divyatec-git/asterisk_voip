#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import time
import json
import requests
import subprocess
import traceback

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

# --------------- READ AGI ENV ---------------
while True:
    line = sys.stdin.readline().strip()
    if not line:
        break

agi('VERBOSE "VOICE AI AGENT STARTED" 1')

# -------- Conversation memory ---------------
conversation = [
    {"role": "system", "content": "You are a helpful voice assistant for phone calls. Keep answers short and clear."}
]

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

        if "result=35" in r or "result=-1" in r:
            agi('VERBOSE "CALL ENDED" 1')
            break

        turn += 1

except Exception as e:
    agi('VERBOSE "FATAL AGI ERROR" 1')
    agi(f'VERBOSE "{str(e)}" 1')
    agi(f'VERBOSE "{traceback.format_exc()}" 1')
    time.sleep(5)


# sudo dos2unix /home/divya/Divya/diya/voice-agent/voice_agent_stt.py
# sudo chmod 755 /home/divya/Divya/diya/voice-agent/voice_agent_stt.py
# sudo apt install -y python3-requests
# sudo sed -i 's/\r$//' /home/divya/Divya/diya/voice-agent/voice_agent_stt.py
# ls -l /var/lib/asterisk/agi-bin/voice_agent_stt.py
            # lrwxrwxrwx 1 root root 53 Jan  8 17:45 /var/lib/asterisk/agi-bin/voice_agent_stt.py -> /home/divya/Divya/diya/voice-agent/voice_agent_stt.py

# sudo rm -f /var/lib/asterisk/agi-bin/voice_agent_stt.py
# sudo ln -s /home/divya/Divya/diya/voice-agent/voice_agent_stt.py /var/lib/asterisk/agi-bin/voice_agent_stt.py