"""Strands Decider client. This is the request/response contract of the workshop kit's
kit/blocks/b09_decider.py, unchanged: POST {URL}/v1/decide with Bearer key and
{"state": str, "questions": {name: {"type": "noul"|"choice", "instructions": str, "criteria"?: {...}}}};
the reply is {"answers": {name: {"noul": p} | {"choice": label, "confidence": c}}}.
It raises instead of guessing when the key is missing or the answer has an unexpected shape."""
import json
import urllib.error
import urllib.request

from . import config


class DeciderError(RuntimeError):
    pass


class DeciderClient:
    def __init__(self, url: str | None = None, key: str | None = None, timeout: int = 30):
        self.url, self.key, self.timeout = (url or config.DECIDER_URL), (key or config.decider_key()), timeout

    def decide(self, state: str, questions: dict) -> dict:
        if not self.key:
            raise DeciderError("DECIDER_API_KEY is not set (get a team key on awsugmdu.in and export it in the backend's environment).")
        req = urllib.request.Request(self.url + "/v1/decide", data=json.dumps({"state": state, "questions": questions}).encode(),
                                     headers={"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                answers = json.load(r)["answers"]
        except urllib.error.HTTPError as e:
            raise DeciderError(f"Decider API returned HTTP {e.code}") from e
        except (urllib.error.URLError, TimeoutError, KeyError, json.JSONDecodeError) as e:
            raise DeciderError(f"Decider API call failed: {type(e).__name__}") from e
        return answers
