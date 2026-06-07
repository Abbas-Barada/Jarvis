# pyright: reportOptionalMemberAccess=false
# pyright: reportAttributeAccessIssue=false
# pyright: reportPossiblyUnboundVariable=false
import subprocess
import re
import os

# Try importing optional libs
# Try importing optional libs
try:
    from pycaw.pycaw import AudioUtilities as _AudioUtilities
    from pycaw.pycaw import IAudioEndpointVolume as _IAudioEndpointVolume
    from ctypes import cast, POINTER
    from comtypes import CLSCTX_ALL
    AudioUtilities = _AudioUtilities
    IAudioEndpointVolume = _IAudioEndpointVolume
    PYCAW_AVAILABLE = True
except ImportError:
    AudioUtilities = None  # type: ignore
    IAudioEndpointVolume = None  # type: ignore
    PYCAW_AVAILABLE = False

try:
    import screen_brightness_control as sbc
    SBC_AVAILABLE = True
except ImportError:
    SBC_AVAILABLE = False

try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False


# ── Volume ──────────────────────────────────────────────────────────────────

def _get_volume_interface():
    if not PYCAW_AVAILABLE:
        return None
    try:
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        return cast(interface, POINTER(IAudioEndpointVolume))
    except Exception:
        return None


def set_volume(level: int) -> str:
    """Set volume 0-100."""
    level = max(0, min(100, level))
    vol = _get_volume_interface()
    if vol:
        vol.SetMasterVolumeLevelScalar(level / 100.0, None)
        return f"Volume set to {level}%."
    # fallback using nircmd if available
    try:
        subprocess.run(["nircmd", "setsysvolume", str(int(level * 655.35))],
                       capture_output=True)
        return f"Volume set to {level}%."
    except FileNotFoundError:
        return "Install pycaw to control volume: pip install pycaw"


def get_volume() -> str:
    vol = _get_volume_interface()
    if vol:
        level = int(vol.GetMasterVolumeLevelScalar() * 100)
        muted = vol.GetMute()
        return f"Volume is at {level}%{', muted' if muted else ''}."
    return "Couldn't read volume."


def mute_volume() -> str:
    vol = _get_volume_interface()
    if vol:
        vol.SetMute(1, None)
        return "Muted."
    return "Couldn't mute."


def unmute_volume() -> str:
    vol = _get_volume_interface()
    if vol:
        vol.SetMute(0, None)
        return "Unmuted."
    return "Couldn't unmute."


# ── Brightness ───────────────────────────────────────────────────────────────

def set_brightness(level: int) -> str:
    """Set brightness 0-100."""
    level = max(0, min(100, level))
    if SBC_AVAILABLE:
        try:
            sbc.set_brightness(level)
            return f"Brightness set to {level}%."
        except Exception as e:
            return f"Couldn't set brightness: {e}"
    return "Install screen-brightness-control: pip install screen-brightness-control"


def get_brightness() -> str:
    if SBC_AVAILABLE:
        try:
            level = sbc.get_brightness()[0]
            return f"Brightness is at {level}%."
        except Exception:
            return "Couldn't read brightness."
    return "screen-brightness-control not installed."


# ── Media controls ───────────────────────────────────────────────────────────

def media_play_pause() -> str:
    if PYAUTOGUI_AVAILABLE:
        pyautogui.press("playpause")
        return "Play/pause."
    return "Install pyautogui: pip install pyautogui"


def media_next() -> str:
    if PYAUTOGUI_AVAILABLE:
        pyautogui.press("nexttrack")
        return "Next track."
    return "Install pyautogui: pip install pyautogui"


def media_prev() -> str:
    if PYAUTOGUI_AVAILABLE:
        pyautogui.press("prevtrack")
        return "Previous track."
    return "Install pyautogui: pip install pyautogui"


# ── System actions ───────────────────────────────────────────────────────────

def lock_pc() -> str:
    subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"])
    return "Locking the PC."


def sleep_pc() -> str:
    subprocess.run(["rundll32.exe", "powrprof.dll,SetSuspendState", "0", "1", "0"])
    return "Going to sleep."


def empty_recycle_bin() -> str:
    try:
        import winshell
        winshell.recycle_bin().empty(confirm=False, show_progress=False, sound=False)
        return "Recycle bin emptied."
    except ImportError:
        subprocess.run(
            'PowerShell -Command "Clear-RecycleBin -Force"',
            shell=True, capture_output=True
        )
        return "Recycle bin emptied."


# ── Command parser ────────────────────────────────────────────────────────────

def handle_system_command(text: str):
    """
    Parse text and execute system commands.
    Returns a result string or None if no command matched.
    """
    t = text.lower().strip()

    # Volume set
    match = re.search(r"(set |turn )?(volume|sound)\s*(to)?\s*(\d+)", t)
    if match:
        return set_volume(int(match.group(4)))

    # Volume up/down by amount
    match = re.search(r"(volume|sound)\s*(up|down)\s*(\d+)?", t)
    if match:
        direction = match.group(2)
        amount = int(match.group(3)) if match.group(3) else 10
        vol = _get_volume_interface()
        if vol:
            current = int(vol.GetMasterVolumeLevelScalar() * 100)
            new = current + amount if direction == "up" else current - amount
            return set_volume(new)

    if any(w in t for w in ["mute", "silence", "shut up"]):
        return mute_volume()

    if "unmute" in t or "un-mute" in t:
        return unmute_volume()

    if "volume" in t and any(w in t for w in ["what", "how loud", "check", "current"]):
        return get_volume()

    # Brightness set
    match = re.search(r"(set |turn )?brightness\s*(to)?\s*(\d+)", t)
    if match:
        return set_brightness(int(match.group(3)))

    match = re.search(r"brightness\s*(up|down)\s*(\d+)?", t)
    if match:
        direction = match.group(1)
        amount = int(match.group(2)) if match.group(2) else 10
        if SBC_AVAILABLE:
            try:
                current = sbc.get_brightness()[0]
                new = current + amount if direction == "up" else current - amount
                return set_brightness(new)
            except Exception:
                pass

    if "brightness" in t and any(w in t for w in ["what", "check", "current"]):
        return get_brightness()

    # Media
    if any(w in t for w in ["play", "pause", "resume"]) and any(
        w in t for w in ["music", "song", "track", "media", "spotify", "youtube"]
    ):
        return media_play_pause()

    if "next" in t and any(w in t for w in ["song", "track", "music"]):
        return media_next()

    if "previous" in t and any(w in t for w in ["song", "track", "music"]):
        return media_prev()

    # System
    if "lock" in t and any(w in t for w in ["pc", "computer", "screen", "my"]):
        return lock_pc()

    if "sleep" in t and any(w in t for w in ["pc", "computer", "my"]):
        return sleep_pc()

    if "empty" in t and "recycle" in t:
        return empty_recycle_bin()

    return None