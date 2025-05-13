import os
from twitter_utils import (
    create_twitter_session,
    is_logged_in,
    post_tweet,
    reply_to_tweet,
    create_tweet_with_media,
    create_repost,
    create_quote_retweet,
)

# ─── 1) Define your accounts and their cookies ────────────────────────────────
# Here we only need ct0 & auth_token per account; the Bearer is hard-coded in twitter_client.
ACCOUNTS = {
    "Alex Harper": {
        "ct0":        "18080f65ca2d06911a700e6c922507ee2c76c91add597d556a8f15cc124137af0ae31c6a3e136153411cfa5eea18c0aba54a0dfc42bc7f68ee35bff51f6ed872541534b965b5bd385e064446c8d3ea42",
        "auth_token": "bb69ebe92c5de404f4abedc835a8e1bd99930c0b",
    },
    "Patricia Jouni": {
        "ct0":        "d271c495e080f9e306ea16ed4efcd5cba9fa2bf66c5f9c8862f5727b3aa259ce275cdaabe1a0033dd752b37a1ddf05e334d1f9bd1613041e1c9f95a0fc05a81bfc2ce6dceeeb864be69c36c65b4b6bd4",
        "auth_token": "36882986cd64073552facb198585ac412db29d9f",
    },
    # add more accounts as needed…
}

# ─── 2) Create a Session for each account ─────────────────────────────────────
sessions = {}
for name, creds in ACCOUNTS.items():
    print(f"🔑 Setting up session for {name!r}…")
    sess = create_twitter_session(
        ct0=creds["ct0"],
        auth_token=creds["auth_token"]
    )
    if not is_logged_in(sess):
        raise RuntimeError(f"❌ Login failed for account {name!r}")
    print(f"✅ {name!r} logged in")
    sessions[name] = sess

# # ─── 3) Do your actions per session ──────────────────────────────────────────
# def run_all():
#     for name, sess in sessions.items():
#         print(f"\n--- Running actions for {name!r} ---")

#         # 3a) Simple text tweet
#         text = f"Hello from {name}!"
#         tweet = post_tweet(sess, text)
#         print(f"📝 [{name}] posted tweet: {tweet['text']}")

#         # 3b) Reply to a known tweet ID
#         reply = reply_to_tweet(
#             sess,
#             f"@someuser Hi from {name}",
#             post_id="1234567890123456789"
#         )
#         print(f"🔁 [{name}] replied with: {reply['text']}")

#         # 3c) Tweet with media
#         media_files = ["image1.jpg", "video1.mp4"]  # replace with real paths
#         resp = create_tweet_with_media(
#             sess,
#             text=f"{name} says check this out!",
#             file_paths=media_files
#         )
#         print(f"📸 [{name}] tweeted media: {resp}")

# if __name__ == "__main__":
#     run_all()

# ─── 3) Define exactly what each account should tweet ────────────────────────
user_actions = {
        "Alex Harper": {
        # 1) media_tweet: only runs if text or file_paths is non-empty
        "media_tweet": {
            "text":       "Ronaldo the GOAT! 🐐",
            "media_paths": [""]
        },

        # 2) repost_id: only runs if this string is non-empty
        "repost_id": "1921974805747716211",

        # 3) quote: only runs if quote_url is non-empty
        #    you can also attach your own media here
        "quote": {
            "comment":     "The future GOAT!",
            "tweet_url":   "https://x.com/ESPNFC/status/1921985788272615510/photo/1",
            "media_paths": [""]
        },
        # 4) reply: only runs if both reply_to_id and text are non-empty
        "reply": {
            "reply_to_id": "",
            "text":        "",
            "media_paths": []
        }
    },
    "Patricia Jouni": {
        # does only a media tweet & a quote-retweet
        "media_tweet": {
            "text":       "",
            "media_paths": []
        },
        "repost_id": "1922065006759165963",  # no repost_id ⇒ we skip the pure retweet step

        # no "repost_id" key ⇒ we skip the pure retweet step
        "quote": {
            "comment":     "",
            "tweet_url":   "",
            "media_paths": []
        },
        # no "reply" key ⇒ we skip the reply step
        "reply": {
            "reply_to_id": "1922065006759165963",
            "text":        "Cute Dog!",
            "media_paths": []
        }
    },
    # add more custom content per account…
}

def run_all():
    for name, sess in sessions.items():
        print(f"\n--- Actions for {name!r} ---")
        cfg = user_actions.get(name, {})

        # 1) Media‐attached tweet
        mt = cfg.get("media_tweet", {})
        text = mt.get("text", "").strip()
        files = [p for p in mt.get("media_paths", []) if p and p.strip()]
        if text or files:
            resp = create_tweet_with_media(sess, text=text, media_paths=files)
            print(f"🎥 [{name}] media tweet → {resp}")
        else:
            print(f"🚫 [{name}] skipped media_tweet (no text & no valid files)")

        # 2) Pure repost (retweet)
        rid = cfg.get("repost_id", "").strip()
        if rid:
            resp = create_repost(sess, rid)
            print(f"🔁 [{name}] retweeted ID {rid} → {resp}")
        else:
            print(f"🚫 [{name}] skipped repost (no repost_id)")

        # 3) Quote‐retweet
        quote_cfg = cfg.get("quote", {})
        qurl = quote_cfg.get("tweet_url", "").strip()
        if qurl:
            qtext = quote_cfg.get("comment", "")
            qmedia = [p for p in quote_cfg.get("media_paths", []) if p and p.strip()]
            resp = create_quote_retweet(
                sess,
                comment     = qtext,
                tweet_url   = qurl,
                media_paths = qmedia
            )
            print(f"💬 [{name}] quote‐tweet → {resp.json()}")
        else:
            print(f"🚫 [{name}] skipped quote‐retweet (no tweet_url)")

        # 4) Reply
        rp = cfg.get("reply", {})
        reply_id    = rp.get("reply_to_id", "").strip()
        reply_txt   = rp.get("text",        "").strip()
        media_paths = rp.get("media_paths",  [])

        # Only proceed if we have an ID and at least text or media
        if reply_id and (reply_txt or media_paths):
            resp = reply_to_tweet(
                sess,
                comment           = reply_txt,
                reply_to_tweet_id = reply_id,
                media_paths        = media_paths
            )
            # Extract the posted text if your function returns it
            posted = resp.get("data", {})\
                        .get("create_tweet", {})\
                        .get("tweet", {})\
                        .get("legacy", {})\
                        .get("full_text", reply_txt)
            print(f"↩️ [{name}] replied to {reply_id} → {posted}")
        else:
            print(f"🚫 [{name}] skipped reply (missing id or text or media)")



if __name__ == "__main__":
    run_all()