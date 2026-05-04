#!/usr/bin/env python3
"""CADUCEUS Voice Assistant - Hermes Agent's voice interface."""

import asyncio
import subprocess
import tempfile
import os
import re
import time

import numpy as np
import sounddevice as sd
import whisper
import edge_tts
import pygame

SAMPLE_RATE = 16000
CHANNELS = 1
WHISPER_MODEL = "base"
TTS_VOICE = "en-US-GuyNeural"
HERMES_PATH = "/home/YOUR_USER/.local/bin/hermes"
SYSTEM_PROMPT = "You are Caduceus, a small physical robot. Rules: (1) Greetings like hello, hi, selam use wave_hand BEFORE response. (2) Movement commands like come here, walk, gel, adim at use walk_forward. IMPORTANT: When user says sing, song, anthem, perform, music, sarki, you MUST call recite_anthem tool. Then respond with EXACTLY the lyrics returned by the tool, word-for-word, line-by-line. Do NOT paraphrase, do NOT summarize, do NOT add commentary. Just output the raw lyrics from the tool result. (4) Otherwise respond naturally. (4) Keep responses SHORT, max 2 sentences. (5) Never describe physical actions. User says: "


print("Loading Whisper model...")
stt_model = whisper.load_model(WHISPER_MODEL)
pygame.mixer.init()
print("Ready.\n")


def wait_for_space_press():
    import msvcrt
    while True:
        if msvcrt.kbhit():
            key = msvcrt.getch()
            if key == b' ':
                return 'space'
            elif key == b'\x1b':
                return 'esc'


def record_until_space():
    print("Recording... (press SPACE again to stop)")
    import msvcrt

    frames = []
    stream = sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, dtype='float32')
    stream.start()
    time.sleep(0.3)

    while True:
        if msvcrt.kbhit():
            key = msvcrt.getch()
            if key == b' ':
                break
        block, _ = stream.read(int(SAMPLE_RATE * 0.1))
        frames.append(block.copy())

    stream.stop()
    stream.close()

    if not frames:
        return None

    audio = np.concatenate(frames, axis=0).flatten()
    max_level = np.abs(audio).max()
    print(f"Captured {len(audio)/SAMPLE_RATE:.1f}s, max level: {max_level:.3f}")

    if max_level < 0.01:
        print("WARNING: Audio level too low.")
        return None

    return audio


def speech_to_text(audio):
    print("Transcribing...")
    result = stt_model.transcribe(audio, fp16=False, language='en')
    return result["text"].strip()


def ask_hermes(text):
    print("Asking Hermes...")
    safe = (SYSTEM_PROMPT + text).replace('"', '\\"').replace("$", "\\$")
    cmd = ["wsl", "-e", HERMES_PATH, "-z", safe]

    try:
        out = subprocess.run(cmd, capture_output=True, text=True,
                             timeout=90, encoding='utf-8', errors='replace')
        response = out.stdout.strip()
        response = re.sub(r'\x1b\[[0-9;]*[mGKH]', '', response)
        return response
    except subprocess.TimeoutExpired:
        return "Response timeout."
    except Exception as e:
        return f"Connection error: {e}"


async def _tts(text, path):
    await edge_tts.Communicate(text, TTS_VOICE).save(path)


def speak(text):
    if not text:
        return
    tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    tmp.close()
    try:
        asyncio.run(_tts(text, tmp.name))
        pygame.mixer.music.load(tmp.name)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
    finally:
        try:
            os.unlink(tmp.name)
        except Exception:
            pass


def main():
    print("=" * 50)
    print("CADUCEUS Voice Assistant")
    print("=" * 50)
    print("SPACE: start/stop recording")
    print("ESC:   quit\n")

    while True:
        print("[Press SPACE to start talking]")
        action = wait_for_space_press()
        if action == 'esc':
            break

        audio = record_until_space()
        if audio is None:
            continue

        if len(audio) < SAMPLE_RATE * 0.5:
            print("Too short.\n")
            continue

        text = speech_to_text(audio)
        if not text:
            print("Nothing detected.\n")
            continue

        print(f"USER:   {text}")

        response = ask_hermes(text)
        if not response:
            print("Empty response.\n")
            continue

        print(f"HERMES: {response}\n")
        speak(response)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass



