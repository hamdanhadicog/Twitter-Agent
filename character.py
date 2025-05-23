from dataclasses import dataclass
from llm import *
from typing import List
from get_telegram_posts import *
import requests

def get_last_4_tweet_ids(sess: requests.Session, username: str) -> list[str]:
        
    url = "https://api.twitter.com/1.1/statuses/user_timeline.json"
    params = {
        "screen_name": username,
        "count": 10,
        "exclude_replies": True,
        "include_rts": False,
        "tweet_mode": "extended"
    }
    resp = sess.get(url, params=params)
    resp.raise_for_status()
    tweets = resp.json()

    tweet_ids = [tweet["id_str"] for tweet in tweets[:4]]
    return tweet_ids

@dataclass
class Character:
    name: str
    username: str
    password: str
    description: str
    ct0: str
    auth_token: str
    sources: List[str] = None

    # Class-level list to store all created characters
    all_characters = []

    def __post_init__(self):
        # Only add if this username is not already present
        if not any(c.username == self.username for c in Character.all_characters):
            Character.all_characters.append(self)

    def get_all_tweet_ids(self, twitter_agent, session):
        all_tweet_ids = []

        if not self.sources:
            print(f"{self.username} has no sources. Nothing to collect.")
            return all_tweet_ids

        for source_username in self.sources:
            try:
                print(f"Fetching recent tweets from source: @{source_username}")
                tweet_ids = get_last_4_tweet_ids(session, source_username)
                all_tweet_ids.extend(tweet_ids)
            except Exception as e:
                print(f"⚠️ Failed to fetch tweets from @{source_username}: {str(e)}")

        # Shuffle to avoid always using the same ones
        random.shuffle(all_tweet_ids)

        return all_tweet_ids

    # def get_combined_news(self, max_news_items: int = 4) -> str:
        
    #     all_news = []

    #     for source in self.sources:
    #         try:
    #             print(f"Fetching from source: @{source}")
    #             news_text = get_latest_news(source, limit=5)  # Get up to 5 per source
    #             if news_text.strip():
    #                 # Split into individual tweets/posts
    #                 news_list = [item.strip() for item in news_text.split("\n\n") if item.strip()]
    #                 all_news.extend(news_list)
    #         except Exception as e:
    #             print(f"⚠️ Error fetching from {source}: {e}")

    #     # Shuffle and select up to max_news_items
    #     random.shuffle(all_news)
    #     selected_news = all_news[:max_news_items]

    #     # Combine into one string
    #     return "\n\n".join(selected_news)





       

        

        