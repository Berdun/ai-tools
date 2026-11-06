# Chat with your own documents (a bot that never makes things up)

1. **Install:** `pip install -r requirements.txt`, install [Ollama](https://ollama.com), then `ollama pull bge-m3` and `ollama pull llama3.1:8b` (both free; set `OPENAI_API_KEY` if you prefer OpenAI).
2. **Run:** `python chat.py handbook.pdf "How many days of annual leave do I get?"` (no question = chat mode).
3. **Change:** drop your own PDF next to `chat.py`; `THRESHOLD = 0.50` is the "not in the document" line; `python -m pytest -q` checks it, `python measure.py` measures it with 20 questions.

**No code? Download the Windows app:** grab `ChatWithYourDocuments-Setup-x.y.z.exe` from [Releases](https://github.com/Berdun/ai-tools/releases), install, start it from the Start menu (or drag a PDF onto its icon). It installs Ollama and the two free models for you on first start (about 6 GB, once). Needs 8 GB RAM (16 GB recommended) and a text PDF (scanned pages are not supported yet). Windows SmartScreen may warn because the file is new and unsigned: *More info → Run anyway*. The app is built from `app.py` + `chat.py` by `installer/build.py`. Questions in other languages work too (bge-m3 is multilingual), but llama3.1's answers are most reliable in English; when you ask about something the document only half covers, check the source page it prints.

Use it yourself: your contracts, catalogues or notes; nothing leaves your computer. Set it up for a client: their files, their machine. Next tool: the same bot with a free local model and a chat window.
