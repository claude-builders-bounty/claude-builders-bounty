#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extract real Chrome from Google official installer and place at user-level path
for Playwright's `channel="chrome"` on Windows.

Playwright on Windows ONLY resolves `%LOCALAPPDATA%\\Google\\Chrome\\Application\\chrome.exe`
(not Program Files). This script extracts the 492 MB Chrome payload from the
160 MB official installer and places it at the user-level path, using a
junction to keep payload on D: drive.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

INSTALLER_URL = "https://dl.google.com/chrome/install/standalonesetup64.exe"
EXPECTED_SIZE = 167879096  # bytes (160 MB)

# 7z extraction offsets discovered via binary analysis
offsets = {
    "outer_7z": 0x48C894,      # 7z signature in installer
    "updater_7z": 0x4FB4,       # 7z signature in chrome_installer.exe
}

def verify_installer(path: Path) -> bool:
    """Verify installer is complete and signed."""
    if not path.exists():
        return False
    if path.stat().st_size != EXPECTED_SIZE:
        print(f"Size mismatch: {path.stat().st_size} != {EXPECTED_SIZE}")
        return False
    # Check digital signature
    try:
        result = subprocess.run(["powershell", "-Command",
            f"(Get-AuthenticodeSignature '{path}').Status"],
            capture_output=True, text=True, timeout=10)
        if "Valid" not in result.stdout:
            print(f"Signature invalid: {result.stdout.strip()}")
            return False
    except Exception as e:
        print(f"Signature check failed: {e}")
        return False
    return True

def extract_7z_at_offset(src: Path, offset: int, dst: Path) -> bool:
    """Extract 7z payload starting at byte offset."""
    try:
        with open(src, "rb") as f:
            f.seek(offset)
            payload = f.read()
        if not payload.startswith(b"7z\xbc\xaf'\x1c"):
            print(f"No 7z magic at offset {hex(offset)}")
            return False
        dst.write_bytes(payload)
        return True
    except Exception as e:
        print(f"Extract failed: {e}")
        return False

def run_7z_extract(archive: Path, out_dir: Path) -> bool:
    """Extract 7z using Bandizip CLI (bz.exe)."""
    bz = Path(r"D:\\Bandizip\\bz.exe")
    if not bz.exists():
        print("Bandizip not found at D:\\Bandizip\\bz.exe")
        return False
    try:
        subprocess.run([str(bz), "x", "-aoa", "-o:", str(out_dir), str(archive)],
                       check=True, capture_output=True, timeout=300)
        return True
    except subprocess.CalledProcessError as e:
        print(f"7z extract failed: {e.stderr.decode()}")
        return False

def main():
    work_dir = Path("D:\\Ai\\Agent\\xiangmu\\xianyu_pipeline\\logs\\_migration")
    installer = work_dir / "ChromeStandaloneSetup64.exe"
    
    if not verify_installer(installer):
        print("Downloading complete installer...")
        subprocess.run(["curl", "-L", "-C", "-", "-o", str(installer), INSTALLER_URL], check=True)
        if not verify_installer(installer):
            sys.exit(1)
    
    print("[1/5] Extracting outer 7z (updater.7z)...")
    updater_7z = work_dir / "updater.7z"
    if not extract_7z_at_offset(installer, offsets["outer_7z"], updater_7z):
        sys.exit(1)
    
    print("[2/5] Extracting updater.7z...")
    updater_dir = work_dir / "updater_extract"
    if not run_7z_extract(updater_7z, updater_dir):
        sys.exit(1)
    
    chrome_installer = next(updater_dir.rglob("*chrome_installer*.exe"), None)
    if not chrome_installer:
        sys.exit("chrome_installer.exe not found")
    
    print("[3/5] Extracting inner 7z (chrome.7z)...")
    chrome_7z = work_dir / "chrome.7z"
    if not extract_7z_at_offset(chrome_installer, offsets["updater_7z"], chrome_7z):
        sys.exit(1)
    
    print("[4/5] Extracting chrome.7z (491 MB)...")
    chrome_dir = work_dir / "chrome_files"
    if not run_7z_extract(chrome_7z, chrome_dir):
        sys.exit(1)
    
    chrome_bin = chrome_dir / "Chrome-bin"
    if not (chrome_bin / "chrome.exe").exists():
        sys.exit("Chrome binary not found in extracted payload")
    
    print("[5/5] Installing to D:\\Ai\\Google\\Chrome via junction...")
    target = Path(r"D:\\Ai\\Google\\Chrome\\Application")
    target.parent.mkdir(parents=True, exist_ok=True)
    
    # Move Chrome-bin contents to Application
    for item in chrome_bin.iterdir():
        dst = target / item.name
        if dst.exists():
            shutil.rmtree(dst) if dst.is_dir() else dst.unlink()
        shutil.move(str(item), str(dst))
    
    # Create junction
    link = Path.home() / "AppData" / "Local" / "Google" / "Chrome"
    if link.exists():
        if link.is_symlink() or (link.stat().st_file_attributes & 0x400):  # junction
            subprocess.run(["cmd", "/c", "rmdir", str(link)], check=True)
        else:
            sys.exit(f"{link} exists and is not a junction, aborting")
    subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(target.parent)], check=True)
    
    # Verify
    verify = link / "Application" / "chrome.exe"
    if verify.exists():
        print(f"SUCCESS: Chrome installed at {verify}")
        print(f"Physical payload on D: {target / 'chrome.exe'}")
    else:
        sys.exit("Verification failed")

if __name__ == "__main__":
    main()
