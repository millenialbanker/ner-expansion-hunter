import json
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from tavily import TavilyClient


def fetch_live_signals_via_tavily():
  # Initialize the Tavily client using the GitHub secret
  tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

  queries = [
      "Kolkata office space lease commercial real estate news",
      "Guwahati office space lease expansion workspace",
  ]

  collected_snippets = []

  for query in queries:
    try:
      response = tavily.search(
          query=query, search_depth="basic", max_results=3
      )
      for result in response.get("results", []):
        snippet = (
            f"Title: {result.get('title')} - Content:"
            f" {result.get('content')}"
        )
        collected_snippets.append(snippet)
    except Exception as e:
      print(f"Tavily search error for '{query}': {e}")

  return collected_snippets


def run_expansion_hunter():
  if not os.getenv("GEMINI_API_KEY"):
    raise ValueError("GEMINI_API_KEY environment variable is not set.")

  llm = ChatGoogleGenerativeAI(model="gemini-3.8-flash", temperature=0)

  print("--- Fetching clean web context via Tavily API ---")
  live_snippets = fetch_live_signals_via_tavily()
  print(
      f"--- Fetched {len(live_snippets)} articles. Evaluating via Gemini ---"
  )

  match_count = 0
  for snippet in live_snippets:
    # (Gemini prompt evaluation code goes here...)
    pass


if __name__ == "__main__":
  run_expansion_hunter()
