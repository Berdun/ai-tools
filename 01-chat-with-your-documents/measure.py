"""Measures the bot with 20 questions (10 in the document, 10 not): how many answers are right,
how often it makes things up, how often the model is called, and how long it takes.
Four setups: no document (plain chatbot), first draft (no threshold, plain prompt), strict prompt only,
strict prompt + threshold 0.50.
Run: python measure.py [handbook.pdf]   -> measure-results.md / .json"""
import json
import sys
import time

import chat

PLAIN = "Answer briefly, based on the document chunks below.\n\n"
REFUSALS = ["doesn't contain", "does not contain", "not contain", "couldn't find", "could not find",
            "not mention", "no mention", "no information", "not specified", "not specify",
            "not provide", "not stated", "not in the document", "not include", "not found",
            "not covered", "doesn't say", "does not say", "can't find", "cannot find", "unable to",
            "no specific", "not explicitly", "not available", "isn't mentioned", "no reference"]
NO_DOC = "You are a helpful assistant for the employees of Nova Software. Answer briefly."
SETUPS = [("no document: the plain chatbot", None, NO_DOC),
          ("first draft: no threshold, plain prompt", 0.0, PLAIN),
          ("strict prompt, no threshold", 0.0, chat.RULES),
          ("strict prompt + threshold 0.50", chat.THRESHOLD, chat.RULES)]


def refused(text):
    return any(r in text.lower() for r in REFUSALS)


def run(setup, threshold, rules, questions, chunks, vectors):
    chat.RULES = rules
    rows, t0 = [], time.perf_counter()
    for item in questions["in_document"] + [{"q": q} for q in questions["not_in_document"]]:
        if threshold is None:                      # the model alone, without the document
            reply = chat.chat_client.chat.completions.create(model=chat.MODEL, temperature=0, messages=[
                {"role": "system", "content": rules}, {"role": "user", "content": item["q"]}])
            text, hits = reply.choices[0].message.content, [True]
        else:
            text, hits = chat.answer(item["q"], chunks, vectors, threshold=threshold)
        top = round(float((vectors @ chat.embed([item["q"]])[0]).max()), 2)
        row = {"q": item["q"], "answer": text, "top_score": top, "called": bool(hits),
               "in_document": "expect" in item, "refused": refused(text)}
        row["correct"] = "expect" in item and any(e.lower() in text.lower() for e in item["expect"])
        row["fabricated"] = "expect" not in item and not row["refused"]
        rows.append(row)
        mark = "OK " if row["correct"] else "FAB" if row["fabricated"] else "   "
        print(f"  {mark} {top:.2f} {item['q'][:52]:<52} -> {text[:60]!r}")
        if "expect" in item and not row["correct"]:
            print(f"      WRONG: {text[:150]!r}")
    seconds = time.perf_counter() - t0
    return {"setup": setup, "threshold": threshold, "model": chat.MODEL, "seconds": round(seconds, 1),
            "per_question": round(seconds / len(rows), 2),
            "correct": sum(r["correct"] for r in rows),
            "wrong_refusals": sum(r["in_document"] and r["refused"] for r in rows),
            "fabricated": sum(r["fabricated"] for r in rows),
            "model_calls": sum(r["called"] for r in rows), "rows": rows}


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "handbook.pdf"
    questions = json.load(open("questions.json", encoding="utf-8"))
    t0 = time.perf_counter()
    chunks, vectors = chat.build_index(path)
    index_seconds = round(time.perf_counter() - t0, 1)
    print(f"{path}: {len(chunks)} chunks in {index_seconds} s, answers by {chat.MODEL}\n")
    results = []
    for setup, threshold, rules in SETUPS:
        print(f"== {setup}")
        results.append(run(setup, threshold, rules, questions, chunks, vectors))
        print()
    tops = [r["top_score"] for r in results[1]["rows"]]
    n_in = len(questions["in_document"])
    summary = {"document": path, "chunks": len(chunks), "index_seconds": index_seconds,
               "top_score_in_document": [min(tops[:n_in]), max(tops[:n_in])],
               "top_score_not_in_document": [min(tops[n_in:]), max(tops[n_in:])], "setups": results}
    json.dump(summary, open("measure-results.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    lines = [f"# 20 questions on {path} ({len(chunks)} chunks, model {chat.MODEL})", "",
             "| Setup | Correct (of 10) | Wrong refusals | Made up (of 10 traps) | Model calls | s / question |",
             "|---|---|---|---|---|---|"]
    for r in results:
        lines.append(f"| {r['setup']} | {r['correct']} | {r['wrong_refusals']} | {r['fabricated']} | "
                     f"{r['model_calls']} | {r['per_question']} |")
    lines += ["", f"Top similarity, questions in the document: {tops[:n_in]}",
              f"Top similarity, questions not in the document: {tops[n_in:]}"]
    open("measure-results.md", "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("\n".join(lines))
