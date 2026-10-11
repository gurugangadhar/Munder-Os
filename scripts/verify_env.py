"""
Munder Difflin — Environment Diagnostic and Verification Script
Verifies all prerequisites, Python libraries, FFmpeg binary, Edge-TTS synthesis,
Windows Truststore SSL integration, and disk space.
"""

import sys
import os
import shutil
import asyncio

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

def check_python():
    print(f"[1/6] Python Version: {sys.version.split()[0]} ({sys.executable})")
    if sys.version_info < (3, 11):
        print("  [FAIL] Python 3.11+ required.")
        return False
    print("  [OK] Python version is supported.")
    return True

def check_truststore():
    print("[2/6] Windows Truststore SSL Integration...")
    try:
        import truststore
        truststore.inject_into_ssl()
        import urllib.request
        resp = urllib.request.urlopen("https://www.google.com", timeout=5)
        if resp.status == 200:
            print("  [OK] Corporate SSL inspection successfully bridged via Windows Truststore.")
            return True
        else:
            print(f"  [WARN] Unexpected HTTP status {resp.status}")
            return False
    except Exception as e:
        print(f"  [FAIL] SSL Error: {e}")
        return False

def check_ffmpeg():
    print("[3/6] FFmpeg Video Engine (via imageio-ffmpeg)...")
    try:
        import imageio_ffmpeg
        import subprocess
        exe = imageio_ffmpeg.get_ffmpeg_exe()
        if not os.path.exists(exe):
            print(f"  [FAIL] FFmpeg binary not found at: {exe}")
            return False
        res = subprocess.run([exe, "-version"], capture_output=True, text=True, timeout=5)
        first_line = res.stdout.splitlines()[0] if res.stdout else "Unknown version"
        print(f"  [OK] FFmpeg executable found: {first_line}")
        print(f"       Path: {exe}")
        return True
    except Exception as e:
        print(f"  [FAIL] FFmpeg Error: {e}")
        return False

def check_edge_tts():
    print("[4/6] Edge-TTS Neural Voice Synthesis...")
    try:
        import truststore
        truststore.inject_into_ssl()
        import edge_tts
        test_file = "test_verify_tts.mp3"
        async def _test():
            comm = edge_tts.Communicate("Munder Difflin audio verification.", "en-US-ChristopherNeural")
            await comm.save(test_file)
        asyncio.run(_test())
        if os.path.exists(test_file) and os.path.getsize(test_file) > 1000:
            size = os.path.getsize(test_file)
            os.remove(test_file)
            print(f"  [OK] Edge-TTS synthesized speech successfully ({size} bytes).")
            return True
        else:
            print("  [FAIL] Edge-TTS output file missing or empty.")
            return False
    except Exception as e:
        print(f"  [FAIL] Edge-TTS Error: {e}")
        return False

def check_libraries():
    print("[5/6] Core Python Libraries...")
    libs = [
        ("FastAPI", "fastapi"),
        ("Uvicorn", "uvicorn"),
        ("Pydantic", "pydantic"),
        ("PyYAML", "yaml"),
        ("Pillow (PIL)", "PIL"),
        ("Feedparser", "feedparser"),
        ("Requests", "requests"),
        ("Google GenAI", "google.genai")
    ]
    all_ok = True
    for name, mod in libs:
        try:
            __import__(mod)
            print(f"  [OK] {name}: Ready")
        except ImportError as e:
            print(f"  [FAIL] {name}: Missing ({e})")
            all_ok = False
    return all_ok

def check_disk_space():
    print("[6/6] Local Disk Space (Drive C:)...")
    try:
        total, used, free = shutil.disk_usage("C:\\")
        free_gb = round(free / (1024**3), 1)
        print(f"  [OK] Drive C: {free_gb} GB free.")
        if free_gb < 5:
            print("  [WARN] Free space is below 5 GB!")
            return False
        return True
    except Exception as e:
        print(f"  [WARN] Could not check disk space: {e}")
        return True

def main():
    print("=" * 70)
    print("  MUNDER DIFFLIN -- WORKSTATION ENVIRONMENT VERIFICATION")
    print("=" * 70)
    
    results = [
        check_python(),
        check_truststore(),
        check_ffmpeg(),
        check_edge_tts(),
        check_libraries(),
        check_disk_space()
    ]
    
    print("=" * 70)
    if all(results):
        print(">> ALL CHECKS PASSED! The workstation environment is 100% ready for Phase 1.")
        sys.exit(0)
    else:
        print(">> SOME CHECKS FAILED. Please review the output above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
