import requests
import json
import base64
import mimetypes
import os
import time
from urllib.parse import unquote
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ─── CONFIG ────────────────────────────────────────────────────────────────────
# Paste your one, universal raw (URL-encoded) Bearer token here:
_RAW_BEARER    = "AAAAAAAAAAAAAAAAAAAAAMupswEAAAAANC5Yk%2FHGiZmGDRV3EhXMBO3uX08%3DEwAT9YySxXZXGrYScXeoKUaeyqXQFeNVWUW4SaZUvtegCUVjIi"
BEARER_TOKEN   = unquote(_RAW_BEARER)
CREATE_TWEET_URL = "https://twitter.com/i/api/graphql/dOominYnbOIOpEdRJ7_lHw/CreateTweet"
Feature_Flags  = {
        "premium_content_api_read_enabled": False,
        "communities_web_enable_tweet_community_results_fetch": True,
        "c9s_tweet_anatomy_moderator_badge_enabled": True,
        "responsive_web_grok_analyze_button_fetch_trends_enabled": False,
        "responsive_web_grok_analyze_post_followups_enabled": True,
        "responsive_web_jetfuel_frame": False,
        "responsive_web_grok_share_attachment_enabled": True,
        "responsive_web_edit_tweet_api_enabled": True,
        "graphql_is_translatable_rweb_tweet_is_translatable_enabled": True,
        "view_counts_everywhere_api_enabled": True,
        "longform_notetweets_consumption_enabled": True,
        "responsive_web_twitter_article_tweet_consumption_enabled": True,
        "tweet_awards_web_tipping_enabled": False,
        "responsive_web_grok_show_grok_translated_post": False,
        "responsive_web_grok_analysis_button_from_backend": True,
        "creator_subscriptions_quote_tweet_preview_enabled": False,
        "longform_notetweets_rich_text_read_enabled": True,
        "longform_notetweets_inline_media_enabled": True,
        "profile_label_improvements_pcf_label_in_post_enabled": True,
        "rweb_tipjar_consumption_enabled": True,
        "verified_phone_label_enabled": False,
        "articles_preview_enabled": True,
        "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
        "freedom_of_speech_not_reach_fetch_enabled": True,
        "standardized_nudges_misinfo": True,
        "tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled": True,
        "responsive_web_grok_image_annotation_enabled": True,
        "responsive_web_graphql_timeline_navigation_enabled": True,
        "responsive_web_enhance_cards_enabled": False
    }

# Default User-Agent (override by passing user_agent to create_twitter_session)
_DEFAULT_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/114.0.0.0 Safari/537.36"
)
# ────────────────────────────────────────────────────────────────────────────────

def create_twitter_session(ct0: str,
                           auth_token: str,
                           user_agent: str = None) -> requests.Session:
    """
    Returns a retry-enabled, logged-in Session.  
    You only need to supply ct0 and auth_token.
    """
    sess = requests.Session()

    # ── Retry on connection errors & 5xx/429 ─────────────────────────────────────
    retry = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS", "POST"]
    )
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

    # fetch guest token
    resp = sess.post("https://api.twitter.com/1.1/guest/activate.json")
    resp.raise_for_status()
    sess.headers["X-Guest-Token"] = resp.json()["guest_token"]
    
    return sess

def is_logged_in(sess: requests.Session) -> bool:
    """Returns True if the session’s cookies authenticate a user."""
    r = sess.get("https://api.twitter.com/1.1/account/verify_credentials.json")
    return r.status_code == 200

# def post_tweet(sess: requests.Session, text: str) -> dict:
#     """Post a text-only tweet."""
#     url = "https://api.twitter.com/1.1/statuses/update.json"
#     payload = {"status": text}
#     headers = {
#         **sess.headers,
#         "Content-Type":              "application/x-www-form-urlencoded; charset=UTF-8",
#         "X-Twitter-Active-User":     "yes",
#         "X-Twitter-Client-Language": "en",
#     }
#     r = sess.post(url, headers=headers, data=payload)
#     r.raise_for_status()
#     return r.json()

import requests
from typing import List, Optional

def reply_to_tweet(
    sess: requests.Session,
    comment: str,
    reply_to_tweet_id: str,
    media_paths: list[str] = None
) -> dict:
    """
    Reply to a tweet (by ID) with optional media attachments.

    Args:
      sess:                  a requests.Session pre‐configured with auth headers & cookies
      comment:               the reply text to post
      reply_to_tweet_id:     the ID of the tweet you’re replying to
      media_paths:            optional list of local file paths to upload & attach

    Returns:
      The JSON response from Twitter’s CreateTweet GraphQL endpoint.
    """
    # ─── GraphQL endpoint, queryId & feature flags ────────────────────────────
    # CREATE_TWEET_URL = "https://twitter.com/i/api/graphql/dOominYnbOIOpEdRJ7_lHw/CreateTweet"
    # QUERY_ID = "dOominYnbOIOpEdRJ7_lHw"
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


def upload_media(sess: requests.Session, media_path: str) -> str:
    """
    Upload an image or video.  
    Images: simple base64 → media_id  
    Videos: INIT/APPEND/FINALIZE chunked flow → media_id
    """
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

def create_tweet_with_media(sess: requests.Session,
                            text: str,
                            media_paths: list[str]) -> dict:
    """
    Upload multiple media files, then post a single tweet attaching them all.
    """
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

def create_repost(session: requests.Session, tweet_id: str) -> dict:
    """
    Programmatically “click” the Retweet button on a given tweet.
    Uses the same GraphQL endpoint pattern you discovered in the network tab.
    """
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

def create_quote_retweet(session, comment, tweet_url=None, media_paths=None):
    """
    Post a tweet with:
      - comment text
      - optional upload+attach of local media files
      - optional quote of another Tweet/video via its full URL

    Args:
      session:      a requests.Session already configured with headers & cookies
      comment:      the text content of your Tweet
      quote_url:    (optional) full twitter.com URL to quote, e.g.
                    "https://twitter.com/ESPNFC/status/1921610762142810456"
      media_paths:  (optional) list of local file paths to upload & attach
    """
    # your GraphQL endpoint + flags
    # CREATE_TWEET_URL = "https://twitter.com/i/api/graphql/dOominYnbOIOpEdRJ7_lHw/CreateTweet"
  
    # 1) upload any media_paths, if provided
    media_ids = []
    if media_paths:
        for path in media_paths:
            media_ids.append(upload_media(session, path))

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
