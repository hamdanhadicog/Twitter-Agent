from dataclasses import dataclass
from Twitter_configs import *
import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
import mimetypes
import os
import time
import base64
from Twitter_configs import _DEFAULT_UA, BEARER_TOKEN, Feature_Flags
from typing import List, Optional


def create_twitter_session(ct0: str,auth_token: str,user_agent: str = None) -> requests.Session:

        sess = requests.Session()
        # ── Retry on connection errors & 5xx/429 ─────────────────────────────────────
        retry = Retry(total=5,backoff_factor=1,status_forcelist=[429, 500, 502, 503, 504],allowed_methods=["HEAD", "GET", "OPTIONS", "POST"])

        adapter = HTTPAdapter(max_retries=retry)
        sess.mount("https://", adapter)

        sess.mount("http://", adapter)
        # ─────────────────────────────────────────────────────────────────────────────

        # inject your login cookies
        sess.cookies.set("ct0",        ct0,        domain=".twitter.com", path="/")
        sess.cookies.set("auth_token", auth_token, domain=".twitter.com", path="/")

        # base headers
        sess.headers.update({
            "Authorization":       f"Bearer {BEARER_TOKEN}",
            "X-CSRF-Token":        ct0,
            "User-Agent":          user_agent or _DEFAULT_UA,
            "Accept":              "*/*",
            "Accept-Language":     "en-US,en;q=0.9",
            "Accept-Encoding":     "gzip, deflate, br",
            "Referer":             "https://twitter.com/",
            "Origin":              "https://twitter.com",
        })

        resp = sess.post("https://api.twitter.com/1.1/guest/activate.json")
        resp.raise_for_status()
        sess.headers["X-Guest-Token"] = resp.json()["guest_token"] # fetch guest token
        
        return sess

def upload_media(sess: requests.Session, media_path: str) -> str:

        mime, _     = mimetypes.guess_type(media_path)
        total_bytes = os.path.getsize(media_path)

        if mime and mime.startswith("video"):
            # INIT
            init = sess.post(
                "https://upload.twitter.com/1.1/media/upload.json",
                data={
                    "command":        "INIT",
                    "media_type":     mime,
                    "total_bytes":    total_bytes,
                    "media_category": "tweet_video"
                }
            )
            init.raise_for_status()
            media_id = init.json()["media_id_string"]

            # APPEND in 5MB chunks
            idx = 0
            with open(media_path, "rb") as f:
                while True:
                    chunk = f.read(5 * 1024 * 1024)
                    if not chunk:
                        break
                    part = sess.post(
                        "https://upload.twitter.com/1.1/media/upload.json",
                        data={
                            "command":       "APPEND",
                            "media_id":      media_id,
                            "segment_index": idx
                        },
                        files={"media": chunk}
                    )
                    part.raise_for_status()
                    idx += 1

            # FINALIZE & poll
            fin = sess.post(
                "https://upload.twitter.com/1.1/media/upload.json",
                data={"command":"FINALIZE","media_id":media_id}
            )
            fin.raise_for_status()
            info = fin.json().get("processing_info", {})
            state = info.get("state")
            while state in ("pending","in_progress"):
                time.sleep(info.get("check_after_secs",5))
                status = sess.get(
                    "https://upload.twitter.com/1.1/media/upload.json",
                    params={"command":"STATUS","media_id":media_id}
                )
                status.raise_for_status()
                info = status.json().get("processing_info", {})
                state = info.get("state")
                if state == "failed":
                    raise RuntimeError(f"Video processing failed: {info}")
            return media_id

        # IMAGE → base64
        with open(media_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        resp = sess.post(
            "https://upload.twitter.com/1.1/media/upload.json",
            data={"media_data": b64, "media_category": "tweet_image"}
        )
        resp.raise_for_status()
        return resp.json()["media_id_string"]

def create_tweet_with_media(self,sess: requests.Session,text: str,media_paths: list[str]) -> dict:
    
        if not text.strip():
            text = " "

        media_ids = []
        for path in media_paths:
            media_ids.append(upload_media(sess, path))

        payload = {
            "variables": {
                "tweet_text": text,
                "dark_request": False,
                "media": {
                    "media_entities": [{"media_id": m, "tagged_users": []}
                                    for m in media_ids],
                    "possibly_sensitive": False
                },
                "semantic_annotation_ids": [],
                "disallowed_reply_options": None
            },
            "features": Feature_Flags,
            # "queryId": "IID9x6WsdMnTlXnzXGq8ng"
        }

        url = "https://twitter.com/i/api/graphql/IID9x6WsdMnTlXnzXGq8ng/CreateTweet"
        headers = {
            **sess.headers,
            "Content-Type":               "application/json",
            "X-Twitter-Active-User":      "yes",
            "X-Twitter-Auth-Type":        "OAuth2Session",
            "X-Twitter-Client-Language":  "en",
            "Referer":                    "https://twitter.com/compose/tweet",
            "Origin":                     "https://twitter.com",
        }
        r = sess.post(url, headers=headers, json=payload)
        r.raise_for_status()
        return r.json()