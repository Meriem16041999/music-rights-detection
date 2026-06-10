import base64
import hashlib
import hmac
import time
from pathlib import Path

import requests

_SESSION = requests.Session()


def _sign(string_to_sign: bytes, secret: str) -> str:
    return base64.b64encode(
        hmac.new(secret.encode(), string_to_sign, hashlib.sha1).digest()
    ).decode()


def recognize_chunk(
    wav_path: str,
    host: str,
    access_key: str,
    access_secret: str,
    *,
    http_uri: str = "/v1/identify",
    timeout=(30, 300),
    retries: int = 4,
    backoff: float = 1.4,
):
    wav_file = Path(wav_path)
    if not wav_file.exists():
        raise FileNotFoundError(f"Chunk introuvable: {wav_path}")

    timestamp = str(int(time.time()))
    string_to_sign = f"POST\n{http_uri}\n{access_key}\naudio\n1\n{timestamp}"
    sign = _sign(string_to_sign.encode(), access_secret)

    data = {
        "access_key": access_key,
        "sample_bytes": wav_file.stat().st_size,
        "timestamp": timestamp,
        "signature": sign,
        "data_type": "audio",
        "signature_version": "1",
    }

    last_exc = None
    for attempt in range(1, retries + 1):
        try:
            with open(wav_path, "rb") as f:
                files = {"sample": f}
                r = _SESSION.post(
                    f"https://{host}{http_uri}",
                    data=data,
                    files=files,
                    timeout=timeout,
                )
            r.raise_for_status()
            return r.json()
        except (
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError,
            requests.exceptions.ChunkedEncodingError,
        ) as e:
            last_exc = e
            time.sleep(backoff ** (attempt - 1))
            continue

    raise requests.exceptions.ConnectionError(
        f"ACR request failed after {retries} retries: {last_exc}"
    )
