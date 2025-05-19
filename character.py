from dataclasses import dataclass
from llm import *

@dataclass
class Character:
    name: str
    username: str
    password: str
    description: str
    ct0: str
    auth_token: str

    # Class-level list to store all created characters
    all_characters = []

    def __post_init__(self):
        # Automatically add the new instance to the list
        self.all_characters.append(self)

    def repost(self, text: str,post_id: str):   
        """
        Repost the given text with text.
        """

        