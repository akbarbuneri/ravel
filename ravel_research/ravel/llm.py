"""Ollama client with a persistent, thread-safe response cache.

Solver calls are deterministic (temperature 0, fixed seed), so a cache hit replays the recorded
response together with its recorded token counts and latency. Cost and latency accounting is
therefore identical whether or not a call was served from cache.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import threading
import time

import requests

OLLAMA = "http://localhost:11434/api/chat"


class LLM:
    def __init__(self, model: str, cache_path: str, num_ctx: int = 4096, max_concurrent: int = 2):
        self.model = model
        self.num_ctx = num_ctx
        self._lock = threading.Lock()
        self._db = sqlite3.connect(cache_path, check_same_thread=False, timeout=60)
        self._db.execute("PRAGMA journal_mode=WAL")
        self._db.execute("CREATE TABLE IF NOT EXISTS cache (k TEXT PRIMARY KEY, v TEXT)")
        self._db.commit()
        self.live_calls = 0
        self.cached_calls = 0
        self._inflight: dict[str, threading.Event] = {}
        # the server runs this model with a single slot; bounding client concurrency avoids long queues and timeouts
        self._slots = threading.Semaphore(max_concurrent)

    def _key(self, payload):
        return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()

    def chat(self, prompt: str, *, system: str | None = None, max_tokens: int = 256,
             temperature: float = 0.0, seed: int = 0, think: bool = False, timeout: float = 1800) -> dict:
        msgs = ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": prompt}]
        payload = {"model": self.model, "messages": msgs, "max_tokens": max_tokens,
                   "temperature": temperature, "seed": seed, "think": think, "num_ctx": self.num_ctx}
        k = self._key(payload)
        while True:
            with self._lock:
                row = self._db.execute("SELECT v FROM cache WHERE k=?", (k,)).fetchone()
                if row:
                    self.cached_calls += 1
                    return json.loads(row[0])
                ev = self._inflight.get(k)
                if ev is None:  # we own this request; identical concurrent requests wait for it
                    self._inflight[k] = threading.Event()
                    break
            ev.wait()
        try:
            with self._slots:
                return self._call(k, msgs, max_tokens, temperature, seed, think, timeout)
        finally:
            with self._lock:
                self._inflight.pop(k).set()

    def _call(self, k, msgs, max_tokens, temperature, seed, think, timeout):
        t0 = time.time()
        for attempt in range(4):
            try:
                r = requests.post(OLLAMA, timeout=timeout, json={
                    "model": self.model, "messages": msgs, "stream": False, "think": think,
                    "options": {"temperature": temperature, "seed": seed, "num_predict": max_tokens,
                                "num_ctx": self.num_ctx}}).json()
                break
            except (requests.RequestException, ValueError):
                if attempt == 3:
                    raise
                time.sleep(3 * (attempt + 1))
        out = {"text": r.get("message", {}).get("content", ""),
               "prompt_tokens": r.get("prompt_eval_count", 0) or 0,
               "completion_tokens": r.get("eval_count", 0) or 0,
               "latency_s": round(time.time() - t0, 3)}
        with self._lock:
            self._db.execute("INSERT OR REPLACE INTO cache VALUES (?,?)", (k, json.dumps(out, ensure_ascii=False)))
            self._db.commit()
        self.live_calls += 1
        return out
