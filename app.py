"""Online Voice Generator — Streamlit version (free hosting friendly).

Realistic Microsoft neural voices, unlimited, no credits, no API key.
Runs in the browser via Streamlit Community Cloud (free forever).

Deploy: push this folder to a GitHub repo -> share.streamlit.io -> New app
-> pick repo/branch/app.py -> Deploy. requirements.txt is included.
"""
import asyncio
import io
import re
import time

import streamlit as st

try:
    import edge_tts
except ImportError:
    st.error("edge-tts is not installed. Add it to requirements.txt and redeploy.")
    st.stop()

# Curated voice list: Microsoft neural voices (free, no key, unlimited-ish).
VOICES = {
    "Urdu — Asad (male)": "ur-PK-AsadNeural",
    "Urdu — Uzma (female)": "ur-PK-UzmaNeural",
    "Hindi — Swara (female)": "hi-IN-SwaraNeural",
    "Hindi — Madhur (male)": "hi-IN-MadhurNeural",
    "English — Aria (female, US)": "en-US-AriaNeural",
    "English — Guy (male, US)": "en-US-GuyNeural",
    "English — Neerja (female, India)": "en-IN-NeerjaNeural",
    "English — Prabhat (male, India)": "en-IN-PrabhatNeural",
}

# Honest expression presets: speed + pitch shifts (not true acted emotions).
STYLES = {
    "Normal 🙂": (0, 0),
    "Happy 😄": (10, 5),
    "Excited 🤩": (15, 8),
    "Sad 😢": (-15, -8),
    "Angry 😠": (5, -5),
    "Calm 😌": (-10, -3),
    "Suspenseful 😨": (-5, -10),
}

MAX_CHARS = 5000


def split_sentences(text, max_chars=900):
    """Split into chunks edge-tts handles reliably."""
    text = re.sub(r"\s+", " ", text.strip())
    if not text:
        return []
    parts = re.split(r"(?<=[.!?])\s+", text)
    chunks, cur = [], ""
    for p in parts:
        if len(cur) + len(p) + 1 <= max_chars:
            cur = (cur + " " + p).strip()
        else:
            if cur:
                chunks.append(cur)
            while len(p) > max_chars:
                cut = p.rfind(",", 0, max_chars)
                cut = cut if cut > 0 else max_chars
                chunks.append(p[:cut].strip())
                p = p[cut:].lstrip(", ").strip()
            cur = p
    if cur:
        chunks.append(cur)
    return [c for c in chunks if c]


async def _synth_chunk(text, voice, rate, pitch):
    buf = io.BytesIO()
    communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            buf.write(chunk["data"])
    buf.seek(0)
    return buf.read()


def generate_audio(text, voice_id, style_name):
    rate_pct, pitch_hz = STYLES[style_name]
    rate = f"{rate_pct:+d}%"
    pitch = f"{pitch_hz:+d}Hz"
    chunks = split_sentences(text)
    audio = bytearray()
    for chunk in chunks:
        audio += asyncio.run(_synth_chunk(chunk, voice_id, rate, pitch))
    return bytes(audio)


st.set_page_config(page_title="Voice Generator", page_icon="🎙️")
st.title("🎙️ Voice Generator")
st.caption("Realistic neural voices · Unlimited · No credits · Runs in your browser")

voice_label = st.selectbox("Voice", list(VOICES.keys()))
style_label = st.selectbox(
    "Style",
    list(STYLES.keys()),
    help="Speed + pitch presets. Honest note: these shift delivery, they are not true acted emotions.",
)
text = st.text_area(
    "Text to speak",
    height=180,
    placeholder="Type or paste your script here... (Urdu, Hindi, English)",
    max_chars=MAX_CHARS,
)
st.caption(f"{len(text)}/{MAX_CHARS} characters")

if st.button("Generate Voice", type="primary"):
    if not text.strip():
        st.error("Pehle kuch text likho! / Please type some text first!")
    else:
        with st.spinner("Generating voice... (pehli dafa thora slow ho sakta hai)"):
            try:
                audio_bytes = generate_audio(text, VOICES[voice_label], style_label)
            except Exception as e:  # noqa: BLE001 - surface any TTS failure plainly
                st.error(f"Generation failed: {e}. Dobara try karo.")
            else:
                if not audio_bytes:
                    st.error("Kuch audio nahi bani — text badal kar dobara try karo.")
                else:
                    st.audio(audio_bytes, format="audio/mp3")
                    fname = f"voice_{int(time.time())}.mp3"
                    st.download_button(
                        "⬇️ Download MP3",
                        data=audio_bytes,
                        file_name=fname,
                        mime="audio/mpeg",
                    )
                    st.success(f"Done! {len(audio_bytes) // 1024} KB MP3 ready. ✅")

st.divider()
st.caption(
    "Tip: chhote jumlay (sentences) behtar result dete hain. "
    "Lambi scripts ko hisson mein generate karo."
)
