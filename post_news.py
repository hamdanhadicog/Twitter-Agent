from Twitter_Agent import TwitterAgent
from itertools import cycle
from character import Character
import time
import pandas as pd
import re
from character import *
import csv

def is_arabic(text: str) -> bool:
    """
    Returns True if the text contains Arabic characters.
    """
    # Arabic Unicode range: \u0600-\u06FF
    arabic_regex = re.compile(r'[\u0600-\u06FF]')
    return bool(arabic_regex.search(text))

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

# Optional: Access all characters through the class list
print(f"Loaded {len(Character.all_characters)} characters")



Twitter_Agent = TwitterAgent()

df=pd.read_csv("Last24Hours (1).csv")

for text in df.sample(frac=1)['text']:
    try:
        if is_arabic(text):
            print(f"Posting tweet: {text}")
            for character in Character.all_characters:
                try:
                    print(f"Posting with character: {character.name}")

                    sess = Twitter_Agent.create_twitter_session(   
                        ct0= character.ct0,
                        auth_token= character.auth_token,
                    )

                    Twitter_Agent.create_tweet_with_media(sess, text=text, media_paths=[])
                    time.sleep(30)
                except Exception as e:
                    print(f"An error occurred while posting with {character.name}: {e}")
                    time.sleep(30)
            
            time.sleep(1)
    except Exception as e:
        print(f"An error occurred: {e}")
        time.sleep(30)
    time.sleep(30)

