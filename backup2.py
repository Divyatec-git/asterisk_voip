#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import time
import json
import requests
import traceback

DEEPGRAM_API_KEY = ""

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

agi('VERBOSE "DEEPGRAM MULTI-TURN AGI STARTED" 1')

try:
    # Answer call
    agi("ANSWER")

    turn = 1

    # ----------- CONVERSATION LOOP ------------
    while True:
        agi(f'VERBOSE "TURN {turn} STARTED" 1')

        # Beep
        agi('STREAM FILE beep ""')

        # Unique file per turn
        record_base = f"/tmp/voice_input_{turn}"
        wav_file = record_base + ".wav"

        # Record
        agi(f'RECORD FILE {record_base} wav "#" 20000 0 BEEP s=2')

        if not os.path.exists(wav_file):
            agi('VERBOSE "NO AUDIO FILE FOUND" 1')
            continue

        # Read audio
        with open(wav_file, "rb") as f:
            audio_data = f.read()

        # Send to Deepgram
        headers = {
            "Authorization": f"Token {DEEPGRAM_API_KEY}",
            "Content-Type": "audio/wav"
        }

        response = requests.post(
            "https://api.deepgram.com/v1/listen?punctuate=true&model=nova-2",
            headers=headers,
            data=audio_data,
            timeout=15
        )

        agi(f'VERBOSE "DEEPGRAM HTTP STATUS: {response.status_code}" 1')

        result = response.json()
        text = ""

        try:
            channels = result.get("results", {}).get("channels", [])
            if channels:
                alternatives = channels[0].get("alternatives", [])
                for alt in alternatives:
                    if alt.get("transcript"):
                        text = alt["transcript"]
                        break
        except Exception as e:
            agi(f'VERBOSE "DEEPGRAM PARSE ERROR: {str(e)}" 1')

        agi(f'VERBOSE "STT TEXT: {text}" 1')

        # -------- EXIT CONDITION --------
        agi('VERBOSE "PRESS # TO END OR SPEAK AGAIN" 1')
        r = agi("WAIT FOR DIGIT 2000")

        if "result=35" in r or "result=-1" in r:
            agi('VERBOSE "CALL ENDED BY USER" 1')
            break

        turn += 1

except Exception as e:
    agi('VERBOSE "AGI FATAL ERROR" 1')
    agi(f'VERBOSE "{str(e)}" 1')
    agi(f'VERBOSE "{traceback.format_exc()}" 1')
    time.sleep(5)
