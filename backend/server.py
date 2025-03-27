import os
import time
from fastapi import FastAPI
from openai import AzureOpenAI  
from dotenv import load_dotenv
load_dotenv()

try:
    from openai.error import RateLimitError  
except ImportError:
    RateLimitError = Exception  
app = FastAPI()

client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_ENDPOINT"),
    api_key=os.getenv("API_KEY"),
    api_version=os.getenv("API_VERSION")
)
deployment_id = os.getenv("DEPLOYMENT_ID")  
class AzureOpenAIResponse:
    def __init__(self):
        self.query = None
        self.response = None
        self.memory_chain = []

    def set_query(self, query):
        self.query = query
        self.memory_chain.append({"role": "user", "content": query})

    def get_response_from_azure(self):
        max_retries = 5  
        retry_delay = 5  

        for attempt in range(max_retries):
            try:
                response = client.chat.completions.create(
                    model=deployment_id,   
                    messages=self.memory_chain
                )
                self.response = response.choices[0].message.content
                self.memory_chain.append({"role": "assistant", "content": self.response})
                return  

            except RateLimitError:
                print(f"Rate limit exceeded. Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2  

        self.response = "Rate limit exceeded. Please try again later."
        print("Exceeded maximum retries. Please check your Azure quota.")
chatbot = AzureOpenAIResponse()
@app.get("/query/")
def receive_query(query: str):
    chatbot.set_query(query)
    chatbot.get_response_from_azure()
    return {"response": chatbot.response}
@app.post("/response/")
def send_response():
    return {"response": chatbot.response}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
