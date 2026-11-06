"""Tests without network: a fake embedding and a fake model. Run: python -m pytest -q"""
from types import SimpleNamespace

import numpy as np

from chat import NOT_FOUND, answer, build_index, find, prompt

WORDS = ["leave", "office", "expense", "training", "sick", "python"]


def fake_embed(texts):
    v = np.array([[t.lower().count(w) for w in WORDS] for t in texts], dtype=np.float32) + 0.01
    return v / np.linalg.norm(v, axis=1, keepdims=True)


class FakeClient:
    def __init__(self, text="Your annual leave is 18 working days. [1]"):
        self.text, self.calls = text, []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, model, messages, **_):
        self.calls.append(messages)
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=self.text))])


CHUNKS, VECTORS = build_index("handbook.pdf", emb=fake_embed)


def test_chunks_end_at_sentence_end_and_fit():
    for _, text in CHUNKS:
        assert text.endswith(".") and len(text) <= 400


def test_fact_is_not_split_between_chunks():
    assert any("is 18 working days" in text for _, text in CHUNKS)


def test_leave_question_finds_leave_page():
    assert find("how many days of annual leave", CHUNKS, VECTORS, emb=fake_embed)[0][0] in (2, 3)


def test_unrelated_question_returns_no_chunks():
    assert find("what is python", CHUNKS, VECTORS, emb=fake_embed) == []


def test_model_not_called_without_chunks():
    client = FakeClient()
    text, hits = answer("what is python", CHUNKS, VECTORS, client, emb=fake_embed)
    assert text == NOT_FOUND and hits == [] and client.calls == []


def test_found_chunks_go_to_the_prompt_with_pages():
    client = FakeClient()
    answer("how many days of annual leave", CHUNKS, VECTORS, client, emb=fake_embed)
    system = client.calls[0][0]["content"]
    assert "[1] (page" in system and "make things up" in system
    assert "[2] (page 3)" in prompt([(2, "a.", 0.7), (3, "b.", 0.6)])
