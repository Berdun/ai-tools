r"""Builds the Windows app: PyInstaller (folder mode, fewer antivirus false alarms) + Inno Setup -> dist\*-Setup-*.exe
Usage: python installer\build.py [version]      (needs: pip install pyinstaller; Inno Setup 6 installed)"""
import glob
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERSION = sys.argv[1] if len(sys.argv) > 1 else "1.0.0"
ISCC = next((p for p in [os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Inno Setup 6", "ISCC.exe"),
                         r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"] if os.path.isfile(p)), "ISCC.exe")
os.chdir(ROOT)
for d in ("build", "dist"):
    shutil.rmtree(d, ignore_errors=True)
subprocess.run([sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--onedir", "--console",
                "--name", "ChatWithYourDocuments", "--icon", "installer/app.ico",
                "--hidden-import", "tkinter", "--hidden-import", "chat", "app.py"], check=True)
subprocess.run([ISCC, f"/DAppVersion={VERSION}", "installer/setup.iss"], check=True)
print("built:", glob.glob("dist/*-Setup-*.exe"))
