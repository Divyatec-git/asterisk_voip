┌──────────────────────────┐
│        Caller / User      │
│   (PSTN / SIP / WebRTC)   │
└─────────────┬────────────┘
              │ RTP / SIP
┌─────────────▼────────────┐
│        Asterisk PBX       │
│  - Call Control           │
│  - RTP Audio              │
│  - Dialplan               │
│  - AGI / EAGI / ARI       │
└─────────────┬────────────┘
              │ Raw Audio Stream
┌─────────────▼────────────┐
│     Audio Streaming Layer │
│  - EAGI / ARI / RTP       │
│  - VAD / Framing          │
└─────────────┬────────────┘
              │ PCM / WAV
┌─────────────▼────────────┐
│   Speech-to-Text (STT)    │
│  - Partial Transcripts    │
│  - Final Transcripts      │
└─────────────┬────────────┘
              │ Text
┌─────────────▼────────────┐
│     LLM / AI Engine       │
│  - Prompt Logic           │
│  - Context Memory         │
│  - Intent Handling        │
└─────────────┬────────────┘
              │ Response Text
┌─────────────▼────────────┐
│    Text-to-Speech (TTS)   │
│  - Voice Synthesis        │
│  - Audio Encoding         │
└─────────────┬────────────┘
              │ Audio (WAV / μ-law)
┌─────────────▼────────────┐
│        Asterisk PBX       │
│  - Playback / Streaming   │
└─────────────┬────────────┘
              │
┌─────────────▼────────────┐
│        Caller / User      │
└──────────────────────────┘
