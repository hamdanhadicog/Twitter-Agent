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

# ─── SESSION ──────────────────────────────────────────────────────────────────
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


def is_logged_in(sess: requests.Session) -> bool:
    """Returns True if the session’s cookies authenticate a user."""
    r = sess.get("https://api.twitter.com/1.1/account/verify_credentials.json")
    return r.status_code == 200


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

sess = create_twitter_session(
        ct0='18080f65ca2d06911a700e6c922507ee2c76c91add597d556a8f15cc124137af0ae31c6a3e136153411cfa5eea18c0aba54a0dfc42bc7f68ee35bff51f6ed872541534b965b5bd385e064446c8d3ea42',
        auth_token='bb69ebe92c5de404f4abedc835a8e1bd99930c0b'
    )

resp = create_tweet_with_media(sess, text='hasdfasdfasdfasdf', media_paths=[])
