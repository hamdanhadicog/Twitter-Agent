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
from character import Character
import csv

@dataclass
class TwitterAgent:
    def create_twitter_session(self,ct0: str,auth_token: str,user_agent: str = None) -> requests.Session:

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
    
    def upload_media(self,sess: requests.Session, media_path: str) -> str:

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

    def is_logged_in(self,sess: requests.Session) -> bool:
        """Returns True if the session’s cookies authenticate a user."""
        r = sess.get("https://api.twitter.com/1.1/account/verify_credentials.json")
        return r.status_code == 200
    
    def reply_to_tweet(self,sess: requests.Session,comment: str,reply_to_tweet_id: str,media_paths: list[str] = None) -> dict:
        
        FEATURE_FLAGS = Feature_Flags

        # ─── 1) Ensure non‐empty comment ───────────────────────────────────────────
        if not comment.strip():
            comment = " "

        # ─── 2) Upload any media, gather media_ids ─────────────────────────────────
        media_ids: List[str] = []
        if media_paths:
            for path in media_paths:
                media_ids.append(upload_media(sess, path))  # upload_media should return media_id_string

        # ─── 3) Build the GraphQL request body ─────────────────────────────────────
        variables = {
            "tweet_text": comment,
            "dark_request": False,
            "reply": {
                "in_reply_to_tweet_id": reply_to_tweet_id,
                "exclude_reply_user_ids": []
            },
            "media": {
                "media_entities": [
                    {"media_id": m, "tagged_users": []} for m in media_ids
                ],
                "possibly_sensitive": False
            },
            "semantic_annotation_ids": [],
            "disallowed_reply_options": None
        }

        payload = {
            "variables": variables,
            "features": Feature_Flags,
            #"queryId": QUERY_ID
        }

        # ─── 4) Send the POST ───────────────────────────────────────────────────────
        headers = {
            **sess.headers,
            "Content-Type":              "application/json",
            "X-Twitter-Active-User":     "yes",
            "X-Twitter-Auth-Type":       "OAuth2Session",
            "X-Twitter-Client-Language": "en",
            "Referer":                   "https://twitter.com/compose/tweet",
            "Origin":                    "https://twitter.com",
        }
        resp = sess.post(CREATE_TWEET_URL, headers=headers, json=payload)
        resp.raise_for_status()
        return resp.json()

    def create_repost(self, session: requests.Session, tweet_id: str) -> dict:
        
        # 1) Build the minimal variables + queryId
        variables = {
            "tweet_id":    tweet_id,
            "dark_request": False
        }
        payload = {
            "variables": variables,
        #  "queryId":   "ojPdsZsimiJrUGLR1sjUtA"  # your Mutation ID
        }

        # 2) Compose the request
        url = "https://twitter.com/i/api/graphql/ojPdsZsimiJrUGLR1sjUtA/CreateRetweet"
        headers = {
            **session.headers,
            "Content-Type":              "application/json",
            "X-Twitter-Active-User":     "yes",
            "X-Twitter-Auth-Type":       "OAuth2Session",
            "X-Twitter-Client-Language": "en",
            "Referer":                   "https://twitter.com/home",
            "Origin":                    "https://twitter.com",
        }

        # 3) Send it off
        resp = session.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        return resp.json()
    
    def create_quote_retweet(self,session, comment, tweet_url=None, media_paths=None):

        media_ids = []
        if media_paths:
            for path in media_paths:
                media_ids.append(self.upload_media(session, path))

        # 2) build payload
        vars_payload = {
            "tweet_text": comment,
            "media": {
                "media_entities": [{"media_id": m} for m in media_ids],
                "possibly_sensitive": False
            }
        }
        if tweet_url:
            vars_payload["attachment_url"] = tweet_url

        body = {
            "variables": vars_payload,
            "features": Feature_Flags,
            #"queryId": "dOominYnbOIOpEdRJ7_lHw"
        }

        # 3) send it
        return session.post(CREATE_TWEET_URL, json=body)

    #This codes lets each character share a post and write a text for it
    def repost_campaign(self,text,post_url):
        # Read characters from CSV
        with open('characters.csv', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                Character(
                    username=row['username'],
                    name=row['name'],
                    description="An AI assistant that helps you with your tasks.",
                    ct0=row['ct0'],
                    auth_token=row['auth_token'],
                    password=row['password']
                    
                )

        for character in Character.all_characters:
            sess=self.create_twitter_session(character.ct0,character.auth_token)
            self.create_quote_retweet(sess,text,tweet_url=post_url)
            print('1')
            time.sleep(1)

    

            
TwitterAgent=TwitterAgent()

TwitterAgent.repost_campaign('askdfaskdjfa;sdkjf','https://x.com/Auto_Porn/status/1924767907168366674')

    