import json
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from tavily import TavilyClient


def fetch_live_signals_via_tavily():
  tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

  # Comprehensive query list targeting CRE, GCCs, Managed Offices, and Expansions
  queries = [
      # Kolkata - Commercial Leasing & Parks
      "Kolkata office space lease commercial real estate",
      "Sector V Salt Lake Kolkata office leasing expansion",
      "New Town Rajarhat Kolkata IT park office space",
      "Kolkata corporate headquarters relocation new office",
      # Kolkata - GCCs & Managed / Flex Spaces
      "Global Capability Center GCC Kolkata office setup",
      "Kolkata managed office space launch provider",
      "Kolkata coworking space expansion Awfis Smartworks Regus",
      "Kolkata flex space operator corporate leasing",
      "Kolkata IT ITeS office space demand",
      "Kolkata office fit-out interior design contract announcement",
      # North Eastern Region (NER) - Guwahati & Hubs
      "Guwahati office space lease commercial real estate",
      "Guwahati managed office space coworking expansion",
      "Assam corporate expansion office setup tech",
      "North East India tech park office leasing business",
      "Shillong Guwahati IT park business expansion office",
      # Regional Hiring & Infrastructure Spikes
      "Kolkata tech company hiring expansion office space",
      "Guwahati enterprise tech center office opening",
      "Kolkata commercial property development project lease",
      "West Bengal corporate investment office expansion",
      "NER regional business hub office leasing",
  ]

  collected_snippets = []

  print(
      f"--- Executing {len(queries)} targeted intelligence queries via"
      " Tavily ---"
  )

  for query in queries:
    try:
      # max_results=1 per query keeps response payload fast and saves credits
      response = tavily.search(query=query, search_depth="basic", max_results=1)
      for result in response.get("results", []):
        snippet = (
            f"Query: [{query}] | Title: {result.get('title')} - Content:"
            f" {result.get('content')}"
        )
        collected_snippets.append(snippet)
    except Exception as e:
      print(f"Tavily search error for '{query}': {e}")

  return list(set(collected_snippets))


def run_expansion_hunter():
  if not os.getenv("GEMINI_API_KEY"):
    raise ValueError("GEMINI_API_KEY environment variable is not set.")

  llm = ChatGoogleGenerativeAI(model="gemini-3.8-flash", temperature=0)

  live_snippets = fetch_live_signals_via_tavily()
  print(
      f"--- Filtered {len(live_snippets)} unique articles. Evaluating via"
      " Gemini ---"
  )

  match_count = 0
  for snippet in live_snippets:
    try:
      response = llm.invoke(
          f"Analyze this text for corporate furniture, office setup, managed space, GCC, or commercial leasing signals in Kolkata/NER:\n\n{snippet}"
      )
      # Process and print matching results...
      if "is_relevant" in str(response.content):
        match_count += 1
        print(f"\n🎯 [MATCH FOUND #{match_count}]\n{response.content}")
    except Exception as e:
      continue

  print(f"\nScan complete. Qualified opportunities found: {match_count}")


if __name__ == "__main__":
  run_expansion_hunter()
