from dataclasses import dataclass

@dataclass
class Character:
    name: str
    description: str
    ct0: str
    auth_token: str

    # Class-level list to store all created characters
    all_characters = []

    def __post_init__(self):
        # Automatically add the new instance to the list
        self.all_characters.append(self)