"""Tests for the Gemini service helpers."""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest  # noqa: E402

from services.gemini import clean_json, normalize_question  # noqa: E402


# ---------- clean_json ----------

def test_clean_json_plain():
    assert clean_json('{"a": 1}') == '{"a": 1}'


def test_clean_json_code_block():
    text = '```json\n{"a": 1}\n```'
    assert clean_json(text) == '{"a": 1}'


def test_clean_json_extra_text():
    text = 'Here is your question: {"a": 1} Thanks!'
    assert clean_json(text) == '{"a": 1}'


def test_clean_json_no_json_returns_text():
    assert clean_json("not json") == "not json"


# ---------- normalize_question ----------

def test_valid_multiple_choice_preserved():
    q = {"type": "multiple", "question": "q?", "alternatives": {"A": "a", "B": "b", "C": "c", "D": "d"}, "correct": "A"}
    out = normalize_question(q)
    assert out["type"] == "multiple"
    assert len(out["alternatives"]) == 4


def test_missing_alternatives_fallback_to_open():
    q = {"type": "multiple", "question": "q?", "alternatives": None, "correct": "A"}
    out = normalize_question(q)
    assert out["type"] == "open"
    assert out["alternatives"] is None


def test_single_alternative_fallback_to_open():
    q = {"type": "multiple", "question": "q?", "alternatives": {"A": "a"}, "correct": "A"}
    out = normalize_question(q)
    assert out["type"] == "open"
    assert out["alternatives"] is None


def test_empty_alternatives_filtered():
    q = {
        "type": "multiple",
        "question": "q?",
        "alternatives": {"A": "", "B": "b", "C": "c", "D": "d", "E": None},
        "correct": "B",
    }
    out = normalize_question(q)
    assert "A" not in out["alternatives"]
    assert "B" in out["alternatives"]


def test_question_without_question_field_raises():
    with pytest.raises(ValueError):
        normalize_question({"type": "open", "correct": "A"})


def test_question_without_correct_raises():
    with pytest.raises(ValueError):
        normalize_question({"type": "open", "question": "q?"})


# ---------- generate_gemini_question ----------

def _fake_session_factory(monkeypatch, status=200, payload=None, error_text=""):
    class FakeResp:
        def __init__(self, status, payload, error_text):
            self.status = status
            self._payload = payload
            self._error_text = error_text

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def json(self):
            return self._payload

        async def text(self):
            return self._error_text

    class FakeSession:
        def __init__(self, status, payload, error_text):
            self._resp = FakeResp(status, payload, error_text)

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        def post(self, *a, **kw):
            return self._resp

    monkeypatch.setattr(
        "services.gemini.aiohttp.ClientSession",
        lambda *a, **kw: FakeSession(status, payload, error_text),
    )


@pytest.mark.asyncio
async def test_generate_gemini_question_missing_alternative_e(monkeypatch):
    """A Gemini response missing alternative E must not crash and stays valid."""
    payload = {
        "choices": [
            {
                "message": {
                    "content": (
                        '{"type":"multiple","question":"q?",'
                        '"alternatives":{"A":"a","B":"b","C":"c","D":"d"},'
                        '"correct":"B"}'
                    )
                }
            }
        ]
    }
    _fake_session_factory(monkeypatch, status=200, payload=payload)

    from services.gemini import generate_gemini_question

    result = await generate_gemini_question("Math", "Algebra")
    assert result["question"] == "q?"
    assert result["type"] == "multiple"
    assert set(result["alternatives"]) == {"A", "B", "C", "D"}


@pytest.mark.asyncio
async def test_generate_gemini_question_invalid_json(monkeypatch):
    """A non-JSON Gemini response must raise a clean ValueError."""
    payload = {"choices": [{"message": {"content": "parapapam, not json"}}]}
    _fake_session_factory(monkeypatch, status=200, payload=payload)

    from services.gemini import generate_gemini_question

    with pytest.raises(ValueError):
        await generate_gemini_question("Math", "Algebra")


@pytest.mark.asyncio
async def test_generate_gemini_question_http_error(monkeypatch):
    _fake_session_factory(monkeypatch, status=500, payload={}, error_text="internal error")

    from services.gemini import generate_gemini_question

    with pytest.raises(ValueError):
        await generate_gemini_question("Math", "Algebra")