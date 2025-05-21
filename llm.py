import os
import random
from typing import List, Dict, Optional
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain

# ================= CONFIGURATION SECTION =================

os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.9)

# Context modifiers to increase diversity
CONTEXT_MODIFIERS = [
    "while feeling nostalgic",
    "with a sarcastic tone",
    "after seeing a trending topic",
    "in a dramatic style",
    "as if you're venting",
    "right before going to bed",
    "in a poetic way",
    "like you're talking to a close friend",
    "with a twist of humor",
    "as if you're tweeting from a coffee shop"
]

# Prompt templates by type
PROMPT_TEMPLATES = {
    "tips": [
        "Write a useful tip or trick {modifier} in the style of someone who is {persona_description}. Language: {language}.",
        "Share a practical tip {modifier} as if you're {persona_description}. Language: {language}. Make it feel personal.",
        "Give a quick, clever advice {modifier} from the perspective of {persona_description}. Language: {language}."
    ],
    "opinion": [
        "Write a personal opinion tweet {modifier} in the voice of someone who is {persona_description}. Language: {language}.",
        "As someone who is {persona_description}, share a brief opinion tweet {modifier}. Language: {language}.",
        "Express an emotional or bold opinion {modifier} like you're {persona_description}. Language: {language}."
    ],
    "fact": [
        "Write a 'Did you know?' tweet {modifier} in the style of someone who is {persona_description}. Language: {language}.",
        "As {persona_description}, share a cool 'Did you know?' fact {modifier} in {language}.",
        "Tweet an interesting or weird fact {modifier} as if you're {persona_description}. Language: {language}."
    ],
    "negative": [
        "Write a tweet with a negative opinion or complaint {modifier} in the voice of someone who is {persona_description}. Language: {language}.",
        "As {persona_description}, rant or complain about something common {modifier}. Language: {language}.",
        "Tweet a short criticism or frustration {modifier} in {language} from the perspective of {persona_description}."
    ],
    "positive": [
        "Write a tweet expressing positivity or motivation {modifier} in the style of someone who is {persona_description}. Language: {language}.",
        "Tweet something wholesome or uplifting {modifier} from the voice of {persona_description}. Language: {language}.",
        "As {persona_description}, spread a bit of joy or hope {modifier}. Language: {language}."
    ],
    "fun": [
        "Write a funny or entertaining tweet {modifier} in the style of someone who is {persona_description}. Language: {language}.",
        "As {persona_description}, make a joke or sarcastic tweet {modifier}. Language: {language}.",
        "Create a humorous or silly tweet {modifier} that matches the tone of {persona_description}. Language: {language}."
    ]
}

# ================= UTILITY FUNCTIONS =================

def get_random_modifier():
    return random.choice(CONTEXT_MODIFIERS)

def enforce_tweet_limit(text: str, max_chars: int = 280) -> str:
    return text.strip()[:max_chars] if len(text) > max_chars else text.strip()

def create_tweet_chain(prompt_text: str):
    prompt = PromptTemplate(
        input_variables=["persona_description", "language", "modifier"],
        template=prompt_text + " Keep it within 280 characters."
    )
    return LLMChain(llm=llm, prompt=prompt)

class ContentGenerator:
    def __init__(self):
        self.prompt_types = list(PROMPT_TEMPLATES.keys())

    def generate_content(self, persona_description: str, language: str = "English") -> str:
        # Step 1: Choose random prompt type
        prompt_type = random.choice(self.prompt_types)

        # Step 2: Choose random prompt from that type
        prompt_template = random.choice(PROMPT_TEMPLATES[prompt_type])

        # Step 3: Choose random modifier
        modifier = get_random_modifier()

        # Step 4: Build chain and run
        chain = create_tweet_chain(prompt_template)
        result = chain.run({
            "persona_description": persona_description,
            "language": language,
            "modifier": modifier
        })

        return enforce_tweet_limit(result)


ContentGenerator = ContentGenerator()



