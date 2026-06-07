import sounddevice as sd
import keyboard
import numpy as np
import subprocess
import time
import os

from scipy.io.wavfile import write
from playsound3 import playsound

from config import *

def record_audio():
    print("\nRecording... Press F8 again to stop.")

    recording = []

    # Wait until F8 is fully released before starting
    while keyboard.is_pressed("f8"):
        time.sleep(0.05)

    stream = sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="int16"
    )

    stream.start()

    while True:
        data, _ = stream.read(1024)
        recording.append(data)

        if keyboard.is_pressed("f8"):
            # Wait for release before breaking, avoids re-trigger
            while keyboard.is_pressed("f8"):
                time.sleep(0.05)
            break

    stream.stop()
    stream.close()

    if not recording:
        print("No audio captured.")
        return

    audio = np.concatenate(recording, axis=0)
    write(AUDIO_FILE, SAMPLE_RATE, audio)
    print("Recording saved.")

def transcribe():
    result = subprocess.run(
        [WHISPER_EXE, "-m", WHISPER_MODEL, "-f", AUDIO_FILE, "-nt"],
        capture_output=True,
        text=True
    )

    if os.path.exists(AUDIO_FILE):
        os.remove(AUDIO_FILE)

    text = result.stdout.strip()

    if not text:
        print("Nothing transcribed.")
        return None
    return text

def speak(text):
    process = subprocess.Popen(
        [
            PIPER_EXE,
            "--model",
            PIPER_MODEL,
            "--output_file",
            OUTPUT_WAV
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        text=True
    )

    process.communicate(text)

    playsound(OUTPUT_WAV)

    if os.path.exists(OUTPUT_WAV):
        os.remove(OUTPUT_WAV)