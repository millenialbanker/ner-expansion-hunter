import json
import os
import time
import feedparser
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI


def fetch_live_news_feeds():
  """Fetches live real estate and business expansion headlines

  for Kolkata and the North Eastern Region (NER).
  """
  queries = [
      "Kolkata office space lease real estate",
      "Kolkata commercial property expansion",
      "Guwahati office space lease business",
      "North East India corporate expansion office",
  ]

  collected_snippets = []

  for query in queries:
    rss_url = f"https://news.google.com/rss/search?q={query.replace(' ', '+')}&hl=en-IN&gl=IN&ceid=IN:en"
    feed = feedparser.parse(rss_url)

    # Grab the top 5 most recent articles per query
    for entry in feed.entries[:5]:
      headline_snippet = f"{entry.title} - {entry.get('summary', '')}"
      collected_snippets.append(headline_snippet)

  # Deduplicate snippets
  return list(set(collected_snippets))


def run_expansion_hunter():
  if not os.getenv("GEMINI_API_KEY"):
    raise ValueError("GEMINI_API_KEY environment variable is not set.")

  llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash", temperature=0)

  prompt = ChatPromptTemplate.from_messages([
      (
          "system",
          """You are an elite B2B Commercial Real Estate intelligence agent focused on East India (Kolkata) and the North Eastern Region (NER) of India.
Analyze the input text to identify corporate furniture, office setup, or commercial leasing signals.
Return a clean JSON object with the following fields:
- "is_relevant": true/false
- "company_name": string or null
- "region_hub": string or null
- "trigger_type": string or null
- "estimated_scale": string or null
- "summary": brief description""",
      ),
      ("user", "{text_snippet}"),
  ])

  chain = prompt | llm

  print("--- Fetching live news feeds for Kolkata & NER ---")
  live_news = fetch_live_news_feeds()
  print(f"--- Scraped {len(live_news)} live articles. Evaluating via Gemini ---")

  match_count = 0

  for snippet in live_news:
    max_retries = 3
    success = False
    response = None

    for attempt in range(max_retries):
      try:
        response = chain.invoke({"text_snippet": snippet})
        success = True
        break
      except Exception as e:
        print(f"[Attempt {attempt + 1}] Server busy or error: {e}")
        if attempt < max_retries - 1:
          time.sleep(5)
        else:
          break

    if success and response:
      raw_content = response.content
      if isinstance(raw_content, list):
        text_content = "".join(
            [
                item.get("text", "") if isinstance(item, dict) else str(item)
                for item in raw_content
            ]
        )
      else:
        text_content = str(raw_content)

      try:
        cleaned_content = (
            text_content.replace("```json", "").replace("```", "").strip()
        )
        result = json.loads(cleaned_content)

        if result.get("is_relevant"):
          match_count += 1
          print(f"\n🎯 [MATCH FOUND #{match_count}]")
          print(f"Company: {result.get('company_name')}")
          print(f"Region Hub: {result.get('region_hub')}")
          print(f"Trigger Type: {result.get('trigger_type')}")
          print(f"Estimated Scale: {result.get('estimated_scale')}")
          print(f"Summary: {result.get('summary')}")
          print("-" * 40)
      except json.JSONDecodeError:
        continue

  print(
      f"\nScan complete. Total qualified expansion signals found:"
      f" {match_count}"
  )


if __name__ == "__main__":
  run_expansion_hunter()
