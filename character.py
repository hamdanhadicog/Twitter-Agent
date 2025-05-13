from dataclasses import dataclass

@dataclass
class Character:
    name: str
    description: str
    ct0: str
    auth_token: str


Hadi= Character(
    name="Hadi",
    description="An AI assistant that helps you with your tasks.",
    ct0="uff"
)

