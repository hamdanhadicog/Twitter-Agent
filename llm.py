import os
import random
from typing import Dict, Optional
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain
# ========== CONFIGURATION ==========
load_dotenv()
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.9)
# ========== MODIFIERS ==========
MODIFIERS = {
    "support": [
        "with admiration", "in a motivational tone", "like you're cheering them on",
        "while celebrating their achievements", "in a way that inspires others",
        "as if you truly believe in them", "in an empowering tone"
    ],
    "comment": [
        "with a dramatic tone", "as if you're fed up", "sarcastically",
        "in a calm, wise tone", "like you're talking to a neighbor",
        "while sipping tea", "with a hint of nostalgia"
    ],
    "retweet": [
        "with a dramatic tone"
    #"with excitement", "as if you totally agree", "in a supportive tone",
        # "adding your personal touch", "with enthusiasm",
        # "with a touch of admiration", "like you're recommending it to your friends"
    ],
    "content": [
        "while feeling nostalgic", "with a sarcastic tone",
        "after seeing a trending topic", "in a dramatic style",
        "as if you're venting", "right before going to bed",
        "in a poetic way", "like you're talking to a close friend",
        "with a twist of humor", "as if you're tweeting from a coffee shop"
    ]
}
# ========== PROMPT TEMPLATES ==========
PROMPT_TEMPLATES = {
    "support": (
    "You are {persona_description}, an expert in crafting highly engaging and emotionally intelligent tweets "
    "that sound real, relatable, and human. Based on the text below, write a tweet in {language} {modifier} that clearly and "
    "passionately supports the idea, cause, or person described. Your goal is to amplify their message in a way "
    "that feels authentic, heartfelt, and share-worthy.\n\n"
    "✴️ Use casual or emotionally expressive language—like a friend cheering someone on.\n"
    "✴️ Use tone that fits the original content (e.g. excited, grateful, proud, moved, inspired).\n"
    "✴️ Do *not* quote the original text. Don't explain or summarize. Add emotional weight and voice your support "
    "as if it's your own belief.\n"
    "✴️ No robotic phrases. Make it sound like something you'd see from a thoughtful, passionate person on social media.\n\n"
    "🧠 Tips: Think like you're replying to or retweeting a message that deeply resonated with you. Make others feel that emotion too.\n\n"
    "🔹 Max 280 characters\n"
    "🔹 No quotation marks\n"
    "🔹 One tweet only\n\n"
    "Text to support:\n{text}"
    ),
    "comment": (
        "You are a person with the following description: {persona_description}. Comment on the text with your unique perspective {modifier} in {language}. "
        "Keep it short and human. Here is the text:\n\n{text}\n\nYour comment:"
    ),
    "retweet": (
       "You are a person with the following description: {persona_description}. retweet on the text with your unique perspective {modifier} in {language}. "
        "Keep it short and human. Here is the text:\n\n{tweet_text}\n\nYour retweet:"
    ),
    "content": {
        "tips": [
            "Write a useful tip {modifier} in {language} as {persona_description}.",
            "Share a practical tip {modifier} in {language} like {persona_description}."
        ],
        "opinion": [
            "Share a personal opinion {modifier} in {language} as {persona_description}.",
            "Express an opinion {modifier} in {language} from {persona_description}'s perspective."
        ],
        "fact": [
            "Share an interesting fact {modifier} in {language} as {persona_description}.",
            "Write a 'Did you know?' tweet {modifier} in {language} from {persona_description}."
        ],
        "negative": [
            "Complain about something {modifier} in {language} as {persona_description}.",
            "Express frustration {modifier} in {language} like {persona_description}."
        ],
        "positive": [
            "Write something positive {modifier} in {language} as {persona_description}.",
            "Share motivational content {modifier} in {language} from {persona_description}."
        ],
        "fun": [
            "Create funny content {modifier} in {language} as {persona_description}.",
            "Make a joke {modifier} in {language} from {persona_description}'s perspective."
        ]
    }
}
class UnifiedSocialGenerator:
    def __init__(self):
        self.content_types = list(PROMPT_TEMPLATES["content"].keys())
    def generate(
        self,
        mode: str,
        persona_description: str,
        language: str,
        text: Optional[str] = None,
        tweet_text: Optional[str] = None,
        content_type: Optional[str] = None
    ) -> str:
        """Generate social media content based on specified parameters."""
        # Validate mode
        valid_modes = ["support", "comment", "retweet", "content"]
        if mode not in valid_modes:
            raise ValueError(f"Invalid mode. Choose from {valid_modes}")
        # Get appropriate modifier
        modifier = random.choice(MODIFIERS[mode])
        # Handle different modes
        if mode == "content":
            if not content_type or content_type not in self.content_types:
                raise ValueError(f"Must specify valid content_type from {self.content_types}")
            prompt_template = random.choice(PROMPT_TEMPLATES["content"][content_type])
            input_vars = ["persona_description", "modifier", "language"]
            inputs = {
                "persona_description": persona_description,
                "modifier": modifier,
                "language": language
            }
        else:
            prompt_template = PROMPT_TEMPLATES[mode]
            input_vars = ["persona_description", "modifier", "language"]
            inputs = {
                "persona_description": persona_description,
                "modifier": modifier,
                "language": language
            }
            if mode in ["support", "comment"]:
                input_vars.append("text")
                inputs["text"] = text
            elif mode == "retweet":
                input_vars.append("tweet_text")
                inputs["tweet_text"] = tweet_text
        # Create and run chain
        prompt = PromptTemplate(
            input_variables=input_vars,
            template=prompt_template
        )
        chain = LLMChain(llm=llm, prompt=prompt)
        result = chain.run(inputs)
        # Post-processing
        max_length = 200 if mode == "retweet" else 280
        return self._clean_output(result, max_length)
    def _clean_output(self, text: str, max_chars: int) -> str:

        cleaned = text.strip().strip('"').strip('""')

        return cleaned[:max_chars] if len(cleaned) > max_chars else cleaned
    

UnifiedSocialGenerator = UnifiedSocialGenerator()
                                                
        