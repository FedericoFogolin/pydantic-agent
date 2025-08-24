import asyncio
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict
from urllib.parse import urlparse
from xml.etree import ElementTree

import html2text
import requests
from crawl4ai import AsyncWebCrawler, BrowserConfig, CacheMode, CrawlerRunConfig
from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from supabase import Client, create_client

load_dotenv()

url: str = os.getenv("SUPABASE_URL", "")
key: str = os.getenv("SUPABASE_SERVICE_KEY", "")

if not url or not key:
    logging.error(
        "SUPABASE_URL and SUPABASE_KEY must be set in the environment variables."
    )
    raise ValueError(
        "SUPABASE_URL and SUPABASE_KEY must be set in the environment variables."
    )
supabase: Client = create_client(url, key)
embedding_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))

# Initialize HTML to Markdown converter
html_converter = html2text.HTML2Text()
html_converter.ignore_links = False
html_converter.ignore_images = False
html_converter.ignore_tables = False
html_converter.body_width = 0  # No wrapping


@dataclass
class ProcessedChunk:
    url: str
    chunk_number: int
    title: str
    summary: str
    content: str
    metadata: Dict[str, Any]
    embedding: list[float]


def chunk_text(text: str, chunk_size: int = 5000) -> list[str]:
    chunks = []
    start = 0
    text_length = len(text)
    while start < text_length:
        # Calculate end position
        end = start + chunk_size
        # If we're at the end of the text, just take what's left
        if end >= text_length:
            chunks.append(text[start:].strip())
            break
        # Try to find a code block boundary first (```)
        chunk = text[start:end]
        code_block = chunk.rfind("```")
        if code_block != -1 and code_block > chunk_size * 0.3:
            end = start + code_block
        # If no code block, try to break at a paragraph
        elif "\n\n" in chunk:
            # Find the last paragraph break
            last_break = chunk.rfind("\n\n")
            if (
                last_break > chunk_size * 0.3
            ):  # Only break if we're past 30% of chunk_size
                end = start + last_break
        # If no paragraph break, try to break at a sentence
        elif ". " in chunk:
            # Find the last sentence break
            last_period = chunk.rfind(". ")
            if (
                last_period > chunk_size * 0.3
            ):  # Only break if we're past 30% of chunk_size
                end = start + last_period + 1
        # Extract chunk and clean it up
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        # Move start position for next chunk
        start = max(start + 1, end)
    return chunks


async def get_title_and_summary(chunk: str, url: str) -> Dict[str, str]:
    system_prompt = """You are an AI that extracts titles and summaries from documentation chunks.
    Return 'title' and 'summary' keys.
    For the title: If this seems like the start of a document, extract its title. If it's a middle chunk, derive a descriptive title.
    For the summary: Create a concise summary of the main points in this chunk.
    Keep both title and summary concise but informative."""

    class TitleAndSummary(BaseModel):
        title: str = Field(
            ...,
            description="The title of the document. If this seems like the start of a document, extract its title. If it's a middle chunk, derive a descriptive title.",
        )
        summary: str = Field(
            ..., description="A concise summary of the main points in this chunk."
        )

    agent = Agent(
        os.getenv("PRIMARY_MODEL"),
        output_type=TitleAndSummary,
        system_prompt=system_prompt,
    )

    try:
        response = await agent.run(f"URL: {url}\n\nContent:\n{chunk}...")
        return {"title": response.output.title, "summary": response.output.summary}
    except Exception as e:
        logging.error(f"Error processing chunk: {e}")
        return {"title": "", "summary": ""}


async def get_embedding(text: str) -> list[float]:
    try:
        response = await embedding_client.embeddings.create(
            model="text-embedding-3-small",
            input=text,
        )
        return response.data[0].embedding
    except Exception as e:
        logging.error(f"Error getting embedding: {e}")
        return [0] * 1536


async def process_chunk(chunk: str, chunk_number: int, url: str) -> ProcessedChunk:
    extracted = await get_title_and_summary(chunk, url)
    embedding = await get_embedding(chunk)

    metadata = {
        "source": "pydantic_ai_docs",
        "chunk_size": len(chunk),
        "crawled_at": datetime.now(timezone.utc).isoformat(),
        "url_path": urlparse(url).path,
    }

    return ProcessedChunk(
        url=url,
        chunk_number=chunk_number,
        title=extracted["title"],
        summary=extracted["summary"],
        content=chunk,  # Store the original chunk content
        metadata=metadata,
        embedding=embedding,
    )


async def insert_chunk(chunk: ProcessedChunk):
    try:
        data = {
            "url": chunk.url,
            "chunk_number": chunk.chunk_number,
            "title": chunk.title,
            "summary": chunk.summary,
            "content": chunk.content,
            "metadata": chunk.metadata,
            "embedding": chunk.embedding,
        }
        result = supabase.table("site_pages").insert(data).execute()
        logging.info(f"Inserted chunk {chunk.chunk_number} for {chunk.url}")
        return result

    except Exception as e:
        logging.error(f"Error inserting chunk: {e}")
        return None


async def process_and_store_document(url: str, markdown: str):
    chunks = chunk_text(markdown)
    tasks = [process_chunk(chunk, i, url) for i, chunk in enumerate(chunks)]
    processed_chunk = await asyncio.gather(*tasks)

    insert_tasks = [insert_chunk(chunk) for chunk in processed_chunk]
    await asyncio.gather(*insert_tasks)


async def crawl_parallel_urls(urls: list[str], max_concurrent: int = 5):
    browser_config = BrowserConfig(
        headless=True,
        verbose=False,
        extra_args=["--disable-gpu", "--disable-dev-shm-usage", "--no-sandbox"],
    )
    crawl_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)

    crawler = AsyncWebCrawler(config=browser_config)
    await crawler.start()

    try:
        semaphore = asyncio.Semaphore(max_concurrent)

        async def process_url(url: str):
            async with semaphore:
                result = await crawler.arun(
                    url=url,
                    config=crawl_config,
                    session_id="session1",
                )
                if result.success:  # type: ignore
                    await process_and_store_document(
                        url,
                        result.markdown.raw_markdown,  # type: ignore
                    )
                else:
                    logging.error(
                        f"Failed to crawl {url}, error: {result.error_message}"  # type: ignore
                    )

        await asyncio.gather(*[process_url(url) for url in urls])
    finally:
        await crawler.close()


def get_pydantic_ai_docs_urls() -> list[str]:
    sitemap_url = "https://ai.pydantic.dev/sitemap.xml"
    try:
        response = requests.get(sitemap_url)
        response.raise_for_status()
        root = ElementTree.fromstring(response.content)
        namespace = {"ns": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        urls = [
            loc.text
            for loc in root.findall(".//ns:loc", namespace)
            if loc.text is not None
        ]
        return urls

    except Exception as e:
        logging.error(f"Error fetching sitemap: {e}")
        return []


def clear_existing_records():
    try:
        result = (
            supabase.table("site_pages")
            .delete()
            .eq("metadata->>source", "pydantic_ai_docs")
            .execute()
        )
        print("Cleared existing pydantic_ai_docs records from site_pages")
        return result
    except Exception as e:
        print(f"Error clearing existing records: {e}")
        return None


async def main():
    urls = get_pydantic_ai_docs_urls()
    logging.info(f"Found {len(urls)} urls in sitemap")

    if not urls:
        logging.warning("No URLs found")
        return

    await crawl_parallel_urls(urls)


if __name__ == "__main__":
    asyncio.run(main())
