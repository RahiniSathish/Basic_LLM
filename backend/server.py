import os
import time
from fastapi import FastAPI
from openai import AzureOpenAI  # Import Azure OpenAI client
from dotenv import load_dotenv

# Load environment variables from .env file (if you have one)
load_dotenv()

# Try importing RateLimitError from openai.error; fallback if not available.
try:
    from openai.error import RateLimitError  # type: ignore
except ImportError:
    RateLimitError = Exception  # Fallback: use a generic exception

app = FastAPI()

# Initialize Azure OpenAI client with environment variables
client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_ENDPOINT"),
    api_key=os.getenv("API_KEY"),
    api_version=os.getenv("API_VERSION")
)
deployment_id = os.getenv("DEPLOYMENT_ID")  # Ensure this is set

class AzureOpenAIResponse:
    def __init__(self):
        """Initialize conversation memory."""
        self.query = None
        self.response = None
        self.memory_chain = []

    def set_query(self, query):
        """Store the user's query."""
        self.query = query
        self.memory_chain.append({"role": "user", "content": query})

    def get_response_from_azure(self):
        """Call Azure OpenAI API with a retry mechanism."""
        max_retries = 5  # Retry up to 5 times
        retry_delay = 5  # Initial delay of 5 seconds

        for attempt in range(max_retries):
            try:
                response = client.chat.completions.create(
                    model=deployment_id,  # Use deployment ID as the model identifier
                    messages=self.memory_chain
                )
                self.response = response.choices[0].message.content
                self.memory_chain.append({"role": "assistant", "content": self.response})
                return  # Exit loop on success

            except RateLimitError:
                print(f"Rate limit exceeded. Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff

        self.response = "Rate limit exceeded. Please try again later."
        print("Exceeded maximum retries. Please check your Azure quota.")

# Create a global chatbot instance
chatbot = AzureOpenAIResponse()

@app.get("/query/")
def receive_query(query: str):
    """Receive a query from the client, process it, and return the response."""
    chatbot.set_query(query)
    chatbot.get_response_from_azure()
    return {"response": chatbot.response}

@app.post("/response/")
def send_response():
    """Return the current chatbot response."""
    return {"response": chatbot.response}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)