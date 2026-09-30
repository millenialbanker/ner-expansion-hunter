import json
import os
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI


def run_expansion_hunter():
  # Ensure API key is present
  if not os.getenv("GEMINI_API_KEY"):
    raise ValueError("GEMINI_API_KEY environment variable is not set.")

  # Initialize Gemini with the active model
  llm = ChatGoogleGenerativeAI(model="gemini-3.8-flash", temperature=0)

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

  # Sample news feed for Kolkata & NER signals
  sample_news_feed = [
      (
          "TechCorp Solutions just signed a lease for 40,000 square feet of office"
          " space in Sector V, Salt Lake, Kolkata."
      ),
      ("Local grocery store opens a new neighborhood outlet in Guwahati."),
  ]

  print(
      f"--- Scanning {len(sample_news_feed)} items for Kolkata & NER"
      " signals ---"
  )

  for snippet in sample_news_feed:
    response = chain.invoke({"text_snippet": snippet})

    # Safely extract text content whether it's returned as a string or list
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

    cleaned_content = (
        text_content.replace("```json", "").replace("```", "").strip()
    )
    result = json.loads(cleaned_content)

    if result.get("is_relevant"):
      print(
          f"\n[MATCH FOUND] Company: {result['company_name']} | Region:"
          f" {result['region_hub']}"
      )
      print(f"Trigger: {result['trigger_type']} | Scale:"
            f" {result['estimated_scale']}")
      print(f"Summary: {result['summary']}")


if __name__ == "__main__":
  run_expansion_hunter()
