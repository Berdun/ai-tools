"""Chat with your own documents: a bot that never makes things up.

Put a PDF next to this file and ask:   python chat.py handbook.pdf "How many days of leave do I get?"
No question -> interactive mode. Embeddings: bge-m3 in Ollama (free, local).
Answers: llama3.1 in Ollama (free) or OpenAI if OPENAI_API_KEY is set."""
import json
import os
import re
import sys
import urllib.request

import numpy as np
from openai import OpenAI
from pypdf import PdfReader

K = 4               # at most this many chunks go to the model
THRESHOLD = 0.50    # a chunk below this similarity counts as unrelated
NOT_FOUND = "I couldn't find anything about this in the document."
RULES = ("You answer in the same language as the question (e.g. a Turkish "
         "question gets a fluent Turkish answer). Answer briefly but completely, "
         "based only on the document chunks below. If the answer is not in the "
         "chunks, say 'The document doesn't contain this information'; don't "
         "make things up. Write the number of the chunk you used in square "
         "brackets.\n\n")

ollama = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
if os.environ.get("OPENAI_API_KEY"):
    chat_client, MODEL = OpenAI(), "gpt-5.4-mini"
else:
    chat_client, MODEL = ollama, "llama3.1:8b"


def document_text(path):
    """PDF -> [(page_number, text), ...]"""
    reader = PdfReader(path)
    return [(n, p.extract_text()) for n, p in enumerate(reader.pages, start=1)]


def chunk_text(text, size=400, overlap=80):
    """Overlapping chunks that end at a sentence boundary."""
    text = " ".join(text.split())
    chunks, start = [], 0
    while start < len(text):
        last = min(start + size, len(text))
        if last < len(text):
            cut = text.rfind(". ", start + size - 150, last)
            if cut > start:
                last = cut + 1
        chunks.append(text[start:last].strip())
        if last >= len(text):
            break
        start = max(last - overlap, start + 1)
        gap = text.find(" ", start, last)
        if gap >= 0:
            start = gap + 1
    return chunks


def embed(texts):
    """Texts -> unit vectors (cosine similarity = dot product)."""
    reply = ollama.embeddings.create(model="bge-m3", input=texts)
    v = np.array([d.embedding for d in reply.data], dtype=np.float32)
    if np.isnan(v).any():                  # some GPUs return NaN: redo on the CPU
        body = json.dumps({"model": "bge-m3", "input": texts,
                           "options": {"num_gpu": 0}, "keep_alive": "30m"}).encode()
        req = urllib.request.Request("http://localhost:11434/api/embed", body,
                                     {"Content-Type": "application/json"})
        v = np.array(json.load(urllib.request.urlopen(req))["embeddings"], dtype=np.float32)
    return v / np.linalg.norm(v, axis=1, keepdims=True)


def build_index(path, emb=embed):
    """Chunk the document and embed every chunk once."""
    chunks = [(n, c) for n, text in document_text(path) for c in chunk_text(text)]
    return chunks, emb([text for _, text in chunks])


def find(question, chunks, vectors, emb=embed, k=K, threshold=THRESHOLD):
    """The k chunks closest to the question: [(page, text, score), ...]"""
    scores = vectors @ emb([question])[0]
    order = scores.argsort()[::-1][:k]
    return [(chunks[i][0], chunks[i][1], float(scores[i]))
            for i in order if scores[i] >= threshold]


def prompt(hits):
    blocks = [f"[{i}] (page {page})\n{text}" for i, (page, text, _) in enumerate(hits, 1)]
    return RULES + "\n\n".join(blocks)


def answer(question, chunks, vectors, client=None, emb=embed, threshold=THRESHOLD):
    """-> (answer text, hits). Without hits the model is never called."""
    hits = find(question, chunks, vectors, emb, threshold=threshold)
    if not hits:
        return NOT_FOUND, hits
    reply = (client or chat_client).chat.completions.create(
        model=MODEL, temperature=0,
        messages=[{"role": "system", "content": prompt(hits)},
                  {"role": "user", "content": question}])
    return reply.choices[0].message.content, hits


def source_pages(text, hits):
    """Pages behind the [1], [2] citations in the answer."""
    if "doesn't contain" in text:          # a refusal has no source
        return []
    ids = {int(n) for n in re.findall(r"\[(\d+)\]", text)}
    return sorted({hits[n - 1][0] for n in ids if 0 < n <= len(hits)})


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "handbook.pdf"
    chunks, vectors = build_index(path)
    print(f"{path}: {len(chunks)} chunks embedded, model {MODEL}")
    questions = sys.argv[2:] or iter(lambda: input("\nQuestion (empty = quit): "), "")
    for question in questions:
        text, hits = answer(question, chunks, vectors)
        for page, chunk, score in hits:
            print(f"  {score:.2f}  page {page}: {chunk[:50]}...")
        if not hits:
            best = find(question, chunks, vectors, threshold=0)[0][2]
            print(f"  highest score {best:.2f}, threshold {THRESHOLD:.2f}: the model was not called")
        print("Answer:", text)
        if pages := source_pages(text, hits):
            print("Source: page", ", ".join(map(str, pages)))
