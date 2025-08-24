from typing import Dict, Any, List, Optional
from openai import AsyncOpenAI
from supabase import Client
import sys
import os


embedding_model = "text-embedding-3-small"


async def get_embedding(text: str, openai_client: AsyncOpenAI) -> list[float]:
    try:
        response = await openai_client.embeddings.create(
            model="text-embedding-3-small", input=text
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Error getting embedding: {e}")
    return [0] * 1536


async def retrieve_relevant_documentation_helper(
    supabase: Client, embedding_client: AsyncOpenAI, user_query: str
) -> str:
    """
    Retrieve relevant documentation chunks based on the query with RAG.

    Args:
        user_query: The user's question or query

    Returns:
        A formatted string containing the top 5 most relevant documentation chunks
    """
    try:
        query_embedding = await get_embedding(user_query, embedding_client)
        result = supabase.rpc(
            "match_site_pages",
            {
                "query_embedding": query_embedding,
                "match_count": 5,
                "filter": {"source": "pydantic_ai_docs"},
            },
        ).execute()

        if not result.data:
            return "No relevant documentation found."

        formatted_chunks = []
        for doc in result.data:
            chunk_text = f"""
# {doc["title"]}

{doc["content"]}
"""
            formatted_chunks.append(chunk_text)
        return "\n\n---\n\n".join(formatted_chunks)

    except Exception as e:
        print(f"Error retrieving relevant documentation: {e}")
        return "Error: Could not retrieve relevant documentation."


async def list_documentation_pages_helper(supabase: Client) -> list[str]:
    try:
        result = (
            supabase.from_("site_pages")
            .select("url")
            .eq("metadata->>source", "pydantic_ai_docs")
            .execute()
        )

        if not result.data:
            return []

        urls = sorted(set([doc["url"] for doc in result.data]))
        return urls

    except Exception as e:
        print(f"Error retrieving documentation pages: {e}")
        return []


async def get_page_content_helper(supabase: Client, url: str) -> str:
    """
    Retrieve the full content of a specific documentation page by combining all its chunks.

    Args:
        url: The URL of the page to retrieve

    Returns:
        str: The complete page content with all chunks combined in order
    """
    try:
        result = (
            supabase.from_("site_pages")
            .select("title, content, chunk_number")
            .eq("url", url)
            .eq("metadata->>source", "pydantic_ai_docs")
            .order("chunk_number")
            .execute()
        )

        if not result.data:
            return f"No content found for URL: {url}"

        page_title = result.data[0]["title"].split(" - ")[0]
        formatted_content = [f"# {page_title}\n"]

        for chunk in result.data:
            formatted_content.append(chunk["content"])

        # TODO: if too big, rag the page itself
        return "\n\n".join(formatted_content)[:20000]

    except Exception as e:
        print(f"Error retrieving page content: {e}")
        return f"Error retrieving page content: {str(e)}"
