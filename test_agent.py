import os
import anthropic
from dotenv import load_dotenv

# Step 1: Load values from your .env file into memory
load_dotenv()

# Step 2: Create the Claude client using the key from .env
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Step 3: Define the function that talks to the agent
def ask_agent(user_message):
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        system="""You are a Senior Software and GenAI Architect agent.
        Your job is to help design, plan, and build software products.
        Always be structured, precise, and stay within the scope given.""",
        messages=[
            {"role": "user", "content": user_message}
        ]
    )
    return response.content[0].text

# Step 4: Test the agent with a sample question
if __name__ == "__main__":
    print("Sending request to Claude...\n")
    
    response = ask_agent(
        "Break down a user login and authentication use case into tasks."
    )
    
    print("Agent Response:")
    print("-" * 50)
    print(response)
    print("-" * 50)
    print("\nPhase 1 complete! Your agent is working.")