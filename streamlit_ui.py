from __future__ import annotations

import asyncio
import os
from typing import Literal, TypedDict

import logfire
import streamlit.components.v1 as components
import streamlit as st
from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic_ai.messages import (
    ModelRequest,
    ModelResponse,
    TextPart,
    UserPromptPart,
)
from supabase import Client

from py_ai_expert import PydanticAIDeps, pydantic_ai_expert

load_dotenv()

openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))
supabase: Client = Client(
    os.getenv("SUPABASE_URL", ""), os.getenv("SUPABASE_SERVICE_KEY", "")
)
logfire.configure(scrubbing=False)
logfire.instrument_pydantic_ai()


class ChatMessage(TypedDict):
    """Format of messages sent to the browser/API."""

    role: Literal["user", "model"]
    timestamp: str
    content: str


def log_to_browser_console(message: str):
    """Log a message to the browser console."""
    components.html(
        f"<script>console.log({repr(message)});</script>",
        height=0,
        width=0,
    )


def display_message_part(part):
    """
    Display a single part of a message in the Streamlit UI.
    Customize how you display system prompts, user prompts,
    tool calls, tool returns, etc.
    """
    # system-prompt
    if part.part_kind == "system-prompt":
        with st.chat_message("system"):
            st.markdown(f"**System**: {part.content}")
    # user-prompt
    elif part.part_kind == "user-prompt":
        with st.chat_message("user"):
            st.markdown(part.content)
    # text
    elif part.part_kind == "text":
        with st.chat_message("assistant"):
            st.markdown(part.content)


async def run_agent_with_streaming(user_input: str):
    """
    Run the agent with streaming text for the user_input prompt,
    while maintaining the entire conversation in `st.session_state.messages`.
    """
    deps = PydanticAIDeps(supabase=supabase, openai_client=openai_client)

    # Run the agent in a stream
    async with pydantic_ai_expert.run_stream(
        user_input,
        deps=deps,
        message_history=st.session_state.messages[
            :-1
        ],  # pass entire conversation so far
    ) as result:
        partial_text = ""
        message_placeholder = st.empty()

        # Render partial text as it arrives
        async for chunk in result.stream_text(delta=True):
            partial_text += chunk
            message_placeholder.markdown(partial_text)

        # Now that the stream is finished, we have a final result.
        # Add new messages from this run, excluding user-prompt messages
        filtered_messages = [
            msg
            for msg in result.new_messages()
            if not (
                hasattr(msg, "parts")
                and any(part.part_kind == "user-prompt" for part in msg.parts)
            )
        ]
        st.session_state.messages.extend(filtered_messages)

        message_placeholder.markdown(partial_text)

        # Check if the final response is already in the messages
        if not any(
            isinstance(msg, ModelResponse) and msg.parts == [TextPart(content=partial_text)]
            for msg in st.session_state.messages
        ):

            # Add the final response to the messages
            st.session_state.messages.append(
                ModelResponse(parts=[TextPart(content=partial_text)])
            )


async def main():
    st.title("Archon - Agent Builder")
    st.write(
        "Describe to me an AI agent you want to build and I'll code it for you with Pydantic AI."
    )

    # Initialize chat history in session state if not present
    if "messages" not in st.session_state:
        st.session_state.messages = []

    log_to_browser_console(f":{st.session_state.messages}")
    # Display all messages from the conversation so far
    # Each message is either a ModelRequest or ModelResponse.
    # We iterate over their parts to decide how to display them.
    for msg in st.session_state.messages:
        if isinstance(msg, ModelRequest) or isinstance(msg, ModelResponse):
            for part in msg.parts:
                display_message_part(part)

    # Chat input for the user
    user_input = st.chat_input("What do you want to build today?")

    if user_input:
        # We append a new request to the conversation explicitly
        st.session_state.messages.append(
            ModelRequest(parts=[UserPromptPart(content=user_input)])
        )

        # Display user prompt in the UI
        with st.chat_message("user"):
            st.markdown(user_input)

        # Display the assistant's partial response while streaming
        with st.chat_message("assistant"):
            # Actually run the agent now, streaming the text
            await run_agent_with_streaming(user_input)


if __name__ == "__main__":
    asyncio.run(main())
