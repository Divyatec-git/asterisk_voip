# asterisk_voip

🔁 Runtime Call Flow (Design View)
User Speaks
   ↓
Asterisk captures RTP audio
   ↓
Audio streamed via EAGI / ARI
   ↓
STT converts speech → text
   ↓
LLM generates response
   ↓
TTS converts text → audio
   ↓
Asterisk plays audio to user


----------------------------------------------------------------------------

Asterisk for Call → AGI Python Script → STT → LLM + Prompt → TTS → Store Call & Conversation in DB → User Listens to Voice

----------------------------------------------------------------------------


## System Architecture

```mermaid
sequenceDiagram
    participant U as Caller
    participant A as Asterisk
    participant G as Python AGI
    participant S as STT
    participant L as LLM
    participant T as TTS
    participant D as Database

    U ->> A: Call
    A ->> G: Invoke AGI
    U ->> A: Speak
    A ->> G: Audio
    G ->> S: STT
    S ->> G: Text
    G ->> L: Prompt + Context
    L ->> G: Response
    G ->> T: TTS
    T ->> G: Audio
    G ->> D: Store conversation
    G ->> A: Playback
    A ->> U: Voice response
```
