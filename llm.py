import os
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

key="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"

# Set your OpenAI API key
os.environ["OPENAI_API_KEY"] = key
# Initialize the model
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.5)

# Define the prompt template
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are {persona_description}. You will comment on the text with your unique perspective. Answer in Arabic."),
    ("user", "{text}")
])

# Generate a comment based on text and persona
def generate_comment(text: str, persona_description: str) -> str:
    formatted_prompt = prompt.invoke({
        "text": text,
        "persona_description": persona_description
    })
    response = llm.invoke(formatted_prompt)
    return response.content

# Example usage
if __name__ == "__main__":
    comment = generate_comment(
        text="The government announced a reduction in education costs.",
        persona_description="a person who follows the news and tends to exaggerate a lot"
    )
    print("Response:", comment)
