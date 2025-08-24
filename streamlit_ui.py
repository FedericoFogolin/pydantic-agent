from __future__ import annotations

import asyncio
import os
import uuid

import logfire
import streamlit as st
from dotenv import load_dotenv
from openai import AsyncOpenAI
from supabase import Client

from pygent.graph import run_graph

load_dotenv()

openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))
supabase: Client = Client(
    os.getenv("SUPABASE_URL", ""), os.getenv("SUPABASE_SERVICE_KEY", "")
)
logfire.configure(scrubbing=False)
logfire.instrument_pydantic_ai()


@st.cache_resource
def get_thread_id():
    return str(uuid.uuid4())


thread_id = get_thread_id()


async def main():
    st.title("Archon - Agent Builder")
    st.write(
        "Describe to me an AI agent you want to build and I'll code it for you with Pydantic AI."
    )
    st.write(
        "Example: Build me an AI agent that can search the web with the Brave API."
    )

    # Initialize chat history in session state if not present
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        message_type = message["type"]
        if message_type in ["human", "ai", "system"]:
            with st.chat_message(message_type):
                st.markdown(message["content"])

    # Chat input for the user
    user_input = st.chat_input("What do you want to build today?")

    if user_input:
        # We append a new request to the conversation explicitly
        st.session_state.messages.append({"type": "human", "content": user_input})

        # Display user prompt in the UI
        with st.chat_message("user"):
            st.markdown(user_input)

        # Run the graph and display the result
        result = await run_graph(thread_id, user_input)
        st.session_state.messages.append({"type": "ai", "content": result})
        with st.chat_message("assistant"):
            st.markdown(result)


if __name__ == "__main__":
    asyncio.run(main())
