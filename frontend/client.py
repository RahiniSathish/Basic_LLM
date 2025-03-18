import requests
import os
from dotenv import load_dotenv
import streamlit as st  # type: ignore

# Load environment variables from .env
load_dotenv()

# Retrieve server IP and port from environment, or use defaults if not set
server_ip_address = os.getenv('SERVER_IP_ADDRESS', 'localhost')
server_port_number = os.getenv('SERVER_PORT_NUMBER', '8000')
server_ip_and_port = f"{server_ip_address}:{server_port_number}"

st.set_page_config(page_title="ChatBot")
st.title('Welcome to ChatBot')

with st.form('form_chat_history'):
    query = st.text_area('Enter Query:', 'Hello! You up for a quick chat?')
    submitted = st.form_submit_button('Send Query')

if submitted:
    # Send query to the server's /query endpoint
    try:
        get_response = requests.get(
            f"http://{server_ip_and_port}/query/", 
            params={'query': query}
        )
        # Check if the response was successful
        if get_response.status_code == 200:
            response_data = get_response.json()
            st.info(response_data.get("response", "No response received."))
        else:
            st.error(f"Error from server: {get_response.status_code}")
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")