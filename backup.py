#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import time
import json
import requests
import traceback
import os

DEEPGRAM_API_KEY = ""

def agi(cmd):
    sys.stdout.write(cmd + "\n")
    sys.stdout.flush()
    return sys.stdin.readline()

# Read AGI environment
while True:
    line = sys.stdin.readline().strip()
    if not line:
        break

agi('VERBOSE "DEEPGRAM AGI STARTED" 1')

try:
    # Answer call
    agi("ANSWER")
    agi('STREAM FILE beep ""')

    # Record audio
    record_path = "/tmp/voice_input"
    wav_file = record_path + ".wav"

    agi('VERBOSE "RECORDING AUDIO" 1')
    agi(f'RECORD FILE {record_path} wav "#" 20000 0 BEEP s=2')

    if not os.path.exists(wav_file):
        agi('VERBOSE "NO AUDIO FILE FOUND" 1')
    else:
        agi('VERBOSE "SENDING AUDIO TO DEEPGRAM" 1')

        with open(wav_file, "rb") as f:
            audio_data = f.read()

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

        agi(f'VERBOSE "DEEPGRAM STATUS: {response.status_code}" 1')
        result = response.json()
        text= ""
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

        agi(f'VERBOSE "DEEPGRAM STATUS: {text}" 1')

    # 🔒 KEEP CALL ALIVE
    agi('VERBOSE "CALL ACTIVE — PRESS # TO END" 1')

    while True:
        r = agi("WAIT FOR DIGIT 1000")
        if "result=-1" in r or "result=35" in r:
            break

except Exception as e:
    agi('VERBOSE "AGI ERROR OCCURRED" 1')
    agi(f'VERBOSE "{str(e)}" 1')
    agi(f'VERBOSE "{traceback.format_exc()}" 1')
    time.sleep(10)
