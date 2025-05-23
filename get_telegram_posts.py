

from telethon.sync import TelegramClient
import asyncio
import nest_asyncio
import pandas as pd

# Apply nest_asyncio to avoid event loop issues
nest_asyncio.apply()

# Telegram credentials
api_id = 27659374
api_hash = '0d834c7f06b6006489145d85b1573d18'
session_name = 'hamdan8'

# Function to get only message texts and combine them into one string
def get_latest_news(channel_username, limit=4):
    """
    Fetches the latest N messages from a Telegram channel and returns only the text content,
    joined into a single string.
    
    Args:
        channel_username (str): The public username of the Telegram channel
        limit (int): Number of messages to fetch
    
    Returns:
        str: Combined message texts
    """
    try:
        # Initialize the client
        client = TelegramClient(session_name, api_id, api_hash)

        # List to store message texts
        message_texts = []

        async def scrape_messages():
            await client.start()
            print(f"Connected to Telegram... fetching from @{channel_username}")

            try:
                messages = await client.get_messages(channel_username, limit=limit)
            except Exception as e:
                raise ValueError(f"Error fetching messages from @{channel_username}: {e}")

            for message in messages:
                if message.text:
                    message_texts.append(message.text.strip())

        async def main():
            async with client:
                await scrape_messages()

        asyncio.run(main())

        # Join all texts into one string separated by newlines
        combined_text = "\n\n".join(message_texts)
        return combined_text

    except Exception as e:
        print(f"Error: {e}")
        return ""
    

