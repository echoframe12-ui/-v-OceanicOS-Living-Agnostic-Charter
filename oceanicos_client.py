"""A thin Python client for the OceanicOS VaaS API — the "Python API Proxy" interface.

Wraps the platform's HTTP endpoints in a small, typed surface so a consumer can
attest, read the trust posture, and verify the record without hand-rolling
requests. The transport is injectable: by default it speaks HTTP to a running
service, but a test (or an in-process caller) can pass an `opener` backed by the
Flask test client, so the client is exercised against the real routes and cannot
drift from them.

    from oceanicos_client import OceanicOSClient
    kai = OceanicOSClient("http://localhost:8000")
    print(kai.cvi()["cvi"])
    token = kai.register("analyst")          # sets the client's token
    print(kai.consensus("ship it")["dissent_score"])
"""
from __future__ import annotations

from typing import Any, Callable, Optional
from urllib.parse import quote

# opener(method, path, headers, json) -> (status_code, parsed_body)
Opener = Callable[[str, str, dict, Optional[dict]], "tuple[int, Any]"]


class OceanicOSError(RuntimeError):
    """A non-2xx response from the platform."""

    def __init__(self, status: int, body: Any) -> None:
        message = body.get("error") if isinstance(body, dict) else body
        super().__init__(f"HTTP {status}: {message}")
        self.status = status
        self.body = body


def _requests_opener(base_url: str) -> Opener:
    """The default transport — real HTTP via `requests` (imported lazily)."""
    import requests

    def opener(method: str, path: str, headers: dict, json: Optional[dict]):
        resp = requests.request(method, base_url + path, headers=headers, json=json, timeout=30)
        try:
            body = resp.json()
        except ValueError:
            body = resp.text
        return resp.status_code, body

    return opener


class OceanicOSClient:
    """A small client over the OceanicOS API. Token is optional; set it via `register`."""

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        token: Optional[str] = None,
        opener: Optional[Opener] = None,
    ) -> None:
        self._base = base_url.rstrip("/")
        self._token = token
        self._opener = opener or _requests_opener(self._base)

    # ---- transport ----
    def _headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    def _call(self, method: str, path: str, json: Optional[dict] = None) -> Any:
        status, body = self._opener(method, path, self._headers(), json)
        if status >= 400:
            raise OceanicOSError(status, body)
        return body

    # ---- auth ----
    def register(self, username: str) -> str:
        """Register (or re-fetch) a token for `username` and remember it on the client."""
        body = self._call("POST", "/auth/register", {"username": username})
        self._token = body["token"]
        return self._token

    # ---- reads (public) ----
    def health(self) -> Any:
        return self._call("GET", "/health")

    def cvi(self) -> Any:
        return self._call("GET", "/cvi")

    def status(self) -> Any:
        """The machine-readable trust posture (`/status.json`)."""
        return self._call("GET", "/status.json")

    def status_digest(self) -> Any:
        return self._call("GET", "/status/digest")

    def evolution(self) -> Any:
        return self._call("GET", "/evolution")

    def doctrine(self) -> Any:
        return self._call("GET", "/doctrine")

    def verify(self) -> Any:
        """The whole-chain integrity report (`/attestations/verify`)."""
        return self._call("GET", "/attestations/verify")

    def stats(self) -> Any:
        return self._call("GET", "/attestations/stats")

    def receipt(self, att_id: int) -> Any:
        return self._call("GET", f"/attestations/{int(att_id)}/receipt")

    def subject_history(self, subject: str) -> Any:
        return self._call("GET", "/attestations/history?subject=" + quote(subject, safe=""))

    def lookup(self, content: str) -> Any:
        """Content-addressable lookup — was this exact output attested?"""
        return self._call("POST", "/attestations/lookup", {"content": content})

    # ---- writes (authed) ----
    def consensus(self, prompt: str) -> Any:
        """Convene the dissent panel on a prompt (requires a token)."""
        return self._call("POST", "/models/consensus", {"prompt": prompt})

    def attention(self) -> Any:
        """The steward attention worklist (requires an admin token)."""
        return self._call("GET", "/attestations/attention")
