"""Chat with your own documents: the desktop app (no Python needed).

This is the Windows app built from chat.py. It checks that Ollama and the two free models are on this
computer (and installs them if you say yes), then opens a PDF and answers your questions from it.
Start it from the Start menu, or drag a PDF onto the icon.  Everything runs on your computer."""
import ctypes
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request

APP = "Chat with your documents"
OLLAMA_URL = "http://localhost:11434"
OLLAMA_SETUP = "https://ollama.com/download/OllamaSetup.exe"
MODELS = {"bge-m3": "the embedding model (about 1.2 GB)", "llama3.1:8b": "the answer model (about 4.9 GB)"}
SIZE_GB = {"bge-m3": 1.2, "llama3.1:8b": 4.9}
HERE = os.path.dirname(sys.executable if getattr(sys, "frozen", False) else os.path.abspath(__file__))


def say(text=""):
    print(text, flush=True)


def ask_yes(question):
    return input(f"{question} [Y/n] ").strip().lower() in ("", "y", "yes")


def get(path, timeout=3):
    with urllib.request.urlopen(OLLAMA_URL + path, timeout=timeout) as r:
        return json.load(r)


def server_up():
    try:
        get("/api/tags")
        return True
    except Exception:
        return False


def ollama_exe():
    found = shutil.which("ollama")
    local = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Ollama", "ollama.exe")
    return found or (local if os.path.isfile(local) else None)


def download(url, target):
    """Download with a one-line progress counter."""
    def hook(count, block, total):
        done = count * block
        if total > 0:
            print(f"\r  {done / 1e6:6.0f} / {total / 1e6:.0f} MB", end="", flush=True)
    urllib.request.urlretrieve(url, target, hook)
    print()


def install_ollama():
    say("Ollama is the free program that runs the AI models on your computer. It is not installed yet.")
    say("The installer is about 1.7 GB and takes a few minutes.")
    if not ask_yes("Download and install Ollama now?"):
        say(f"You can also install it yourself from https://ollama.com, then start this app again.")
        return False
    setup = os.path.join(tempfile.gettempdir(), "OllamaSetup.exe")
    say("Downloading Ollama...")
    download(OLLAMA_SETUP, setup)
    say("Installing (a Windows prompt may ask for permission)...")
    subprocess.run([setup, "/SILENT", "/NORESTART"], check=False)
    os.environ["PATH"] += os.pathsep + os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Ollama")
    return ollama_exe() is not None


def start_server(exe):
    app_exe = os.path.join(os.path.dirname(exe), "ollama app.exe")
    if os.path.isfile(app_exe):
        subprocess.Popen([app_exe], creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP)
    else:
        subprocess.Popen([exe, "serve"], creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS)
    for _ in range(30):
        if server_up():
            return True
        time.sleep(1)
    return False


def installed_models():
    return {m["name"] for m in get("/api/tags")["models"]}


def pull(model):
    """Download a model through Ollama, showing progress."""
    req = urllib.request.Request(OLLAMA_URL + "/api/pull", json.dumps({"model": model}).encode(),
                                 {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        for line in r:
            d = json.loads(line)
            if "error" in d:
                raise RuntimeError(d["error"])
            if d.get("total"):
                print(f"\r  {d['status']}: {d.get('completed', 0) / 1e9:5.2f} / {d['total'] / 1e9:.2f} GB", end="", flush=True)
    print(f"\r  {model}: ready" + " " * 40)


def models_dir():
    """Where Ollama stores models (OLLAMA_MODELS or the .ollama folder in the user profile)."""
    return os.environ.get("OLLAMA_MODELS") or os.path.join(os.path.expanduser("~"), ".ollama", "models")


def ensure_models():
    have = installed_models()
    missing = [m for m in MODELS if not any(n == m or n == m + ":latest" for n in have)]
    if not missing:
        return True
    need = sum(SIZE_GB[m] for m in missing)
    say(f"{'One' if len(missing) == 1 else 'Two'} free AI model{'s' if len(missing) > 1 else ''} "
        f"still need{'s' if len(missing) == 1 else ''} to be downloaded (once; later starts are instant):")
    for m in missing:
        say(f"  - {m}: {MODELS[m]}")
    free_gb = shutil.disk_usage(os.path.dirname(models_dir()) if os.path.isdir(os.path.dirname(models_dir()))
                                else os.path.expanduser("~")).free / 1e9
    say(f"Needed: about {need:.1f} GB. Free on the model drive ({models_dir()}): {free_gb:.0f} GB.")
    if free_gb < need + 1:
        say("Not enough free space. Free some space, or set the OLLAMA_MODELS environment variable to a folder "
            "on a bigger drive, then start this app again.")
        return False
    if not ask_yes("Download now?"):
        return False
    for m in missing:
        say(f"Downloading {m}...")
        pull(m)
    return True


def pick_pdf():
    if len(sys.argv) > 1 and sys.argv[1].lower().endswith(".pdf"):
        return sys.argv[1]
    samples = os.path.join(HERE, "samples")
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk(); root.withdraw(); root.attributes("-topmost", True)
        path = filedialog.askopenfilename(title="Choose the PDF you want to ask about",
                                          filetypes=[("PDF files", "*.pdf")], initialdir=samples if os.path.isdir(samples) else os.path.expanduser("~"))
        root.destroy()
        return path or None
    except Exception:
        return input("Path of the PDF: ").strip().strip('"') or None


def chat_loop(path):
    import chat                      # the 121-line tool from the video, unchanged
    say(f"\nReading {os.path.basename(path)}...")
    chunks, vectors = chat.build_index(path)
    if not chunks:
        say("No text found in this PDF. Scanned (image-only) PDFs are not supported yet.")
        return
    say(f"{len(chunks)} chunks ready. Answers come from {chat.MODEL}. Ask anything about the document.")
    say("(empty question = quit)")
    while True:
        question = input("\nQuestion: ").strip()
        if not question:
            return
        t = time.time()
        text, hits = chat.answer(question, chunks, vectors)
        say(f"\n{text}")
        if pages := chat.source_pages(text, hits):
            say(f"Source: page {', '.join(map(str, pages))}")
        elif not hits:
            best = chat.find(question, chunks, vectors, threshold=0)[0][2]
            say(f"(closest chunk scored {best:.2f}, below the {chat.THRESHOLD:.2f} line: the model was not asked)")
        say(f"({time.time() - t:.1f} s)")


def main():
    try:
        ctypes.windll.kernel32.SetConsoleTitleW(APP)
    except Exception:
        pass
    say(f"=== {APP} ===  a bot that answers from your PDF and never makes things up\n")
    exe = ollama_exe()
    if not exe and not install_ollama():
        return
    exe = ollama_exe()
    if not server_up():
        say("Starting Ollama...")
        if not start_server(exe):
            say("Ollama did not start. Open the Ollama app from the Start menu, then start this app again.")
            return
    if not ensure_models():
        return
    path = pick_pdf()
    if not path:
        say("No PDF chosen.")
        return
    chat_loop(path)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    try:
        main()
    except KeyboardInterrupt:
        pass
    except Exception as e:                       # keep the window open so the message can be read
        say(f"\nSomething went wrong: {e}")
    input("\nPress Enter to close.")
