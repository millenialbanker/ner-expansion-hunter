import json
import os
from langchain_google_genai import ChatGoogleGenerativeAI
import requests
import resend


def fetch_live_signals_via_rest():
    tavily_key = os.getenv("TAVILY_API_KEY")
    if not tavily_key:
        print("TAVILY_API_KEY missing.")
        return []

    queries = [
        # Original Core Real Estate & GCC Queries
        "Kolkata office space lease commercial real estate",
        "Sector V Salt Lake Kolkata office leasing expansion",
        "Global Capability Center GCC Kolkata office setup",
        "Guwahati office space lease commercial real estate",
        "Kolkata coworking space expansion Awfis Smartworks Regus",
        "New Town Rajarhat Kolkata commercial property lease",
        "Kolkata IT park office space absorption demand",
        "Kolkata enterprise tech hub office opening",
        "Ballygunge Park Street Kolkata corporate office relocation",
        "West Bengal industrial corridor office manufacturing setup",
        "Guwahati Assam IT Park tech office lease",
        "Shillong Meghalaya tech business park expansion",
        "North East India startup incubator workspace setup",
        "Kolkata flexible workspace managed office provider",
        "Kolkata corporate interior fit-out contract announcement",
        # --- Newly Added Hiring & Expansion Intent Queries ---
        "opening office in Kolkata hiring",
        "expanding to Guwahati hiring",
        "hiring East India head",
        "New Town Kolkata office hiring tech",
        "Sector V Kolkata hiring operations manager",
        "hiring regional sales manager East India",
        "expanding team Kolkata tech startup",
        "Guwahati Assam hiring tech roles office"
    ]

    collected_snippets = []
    url = "https://api.tavily.com/search"

    print(
        f"--- Querying Tavily via REST API ({len(queries)} targeted queries, including hiring intelligence)"
        " ---"
    )

    for query in queries:
        payload = {
            "api_key": tavily_key,
            "query": query,
            "search_depth": "basic",
            "max_results": 1,
        }
        try:
            # Strict 5-second timeout ensures it never hangs your workflow
            response = requests.post(url, json=payload, timeout=5)
            if response.status_code == 200:
                data = response.json()
                for result in data.get("results", []):
                    snippet = (
                        f"Query: [{query}] | Title: {result.get('title')} - Content:"
                        f" {result.get('content')}"
                    )
                    collected_snippets.append(snippet)
        except Exception as e:
            print(f"Skipping query '{query}' due to timeout/error: {e}")

    return list(set(collected_snippets))


def run_expansion_hunter():
    if not os.getenv("GEMINI_API_KEY"):
        raise ValueError("GEMINI_API_KEY environment variable is not set.")

    llm = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite", temperature=0)

    live_snippets = fetch_live_signals_via_rest()
    print(
        f"--- Fetched {len(live_snippets)} signals successfully. Evaluating hiring & CRE intent via Gemini ---"
    )

    hot_leads = []
    cold_signals = []

    for snippet in live_snippets:
        prompt = f"""You are an elite B2B Commercial Real Estate and Equipment-as-a-Service (EaaS) intelligence agent focused on Kolkata and the North Eastern Region (NER) of India.
Analyze this text to identify corporate expansion intent. Look for:
1. Active hiring spikes or regional leadership hiring (e.g., East India head, Kolkata hub lead, bulk tech/ops hiring).
2. Office setup, managed space deployment, GCC expansion, or commercial real estate leasing.

Return a clean JSON object with the following fields:
- "is_relevant": true/false
- "urgency": "hot" (if large-scale hiring spike, active regional office setup, or major lease) or "cold" (if minor regional branch or early rumor/small hiring)
- "company_name": string or null
- "region_hub": string or null
- "trigger_type": string or null (e.g., "Hiring Spike & Team Expansion", "GCC Real Estate Lease", "Regional Leadership Hiring")
- "estimated_scale": string or null (e.g., "50+ laptops/workstations expected", "New regional office setup")
- "summary": brief description highlighting the hiring or expansion signal detected

Text to analyze:
{snippet}"""

        try:
            response = llm.invoke(prompt)
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
                if result.get("urgency") == "hot":
                    hot_leads.append(result)
                else:
                    cold_signals.append(result)
        except Exception as e:
            print(f"Parsing error: {e}")
            continue

    # Build Email HTML Body
    html_body = "<h2>🎯 Expansion & Hiring Intelligence Daily Report</h2>"

    html_body += "<h3>🔥 Hot Leads (Active Hiring & Immediate Action)</h3>"
    if hot_leads:
        for lead in hot_leads:
            html_body += f"""
                <div style="border-left: 4px solid #ff4d4d; padding-left: 10px; margin-bottom: 15px;">
                    <b>Company:</b> {lead.get('company_name')}<br>
                    <b>Region Hub:</b> {lead.get('region_hub')}<br>
                    <b>Trigger:</b> {lead.get('trigger_type')} ({lead.get('estimated_scale')})<br>
                    <b>Summary:</b> {lead.get('summary')}
                </div>"""
    else:
        html_body += "<p>No hot leads found in today's scan.</p>"

    html_body += "<h3>❄️ Cold Signals (Early Hiring / Watchlist)</h3>"
    if cold_signals:
        for signal in cold_signals:
            html_body += f"""
                <div style="border-left: 4px solid #4da6ff; padding-left: 10px; margin-bottom: 15px;">
                    <b>Company:</b> {signal.get('company_name')}<br>
                    <b>Region Hub:</b> {signal.get('region_hub')}<br>
                    <b>Trigger:</b> {signal.get('trigger_type')}<br>
                    <b>Summary:</b> {signal.get('summary')}
                </div>"""
    else:
        html_body += "<p>No cold signals found today.</p>"

    send_email_via_resend(html_body)


def send_email_via_resend(html_content):
    resend.api_key = os.getenv("RESEND_API_KEY")
    if not resend.api_key:
        print("RESEND_API_KEY missing. Skipping email dispatch.")
        return

    try:
        params: resend.Emails.SendParams = {
            "from": "Expansion Hunter <onboarding@resend.dev>",
            "to": [os.getenv("EMAIL_RECIPIENT") or "delivered@resend.dev"],
            "subject": "🏢 Expansion & Hiring Briefing: East India Leads",
            "html": html_content,
        }
        email = resend.Emails.send(params)
        print(f"Resend email dispatched successfully: {email}")
    except Exception as e:
        print(f"Failed to send email via Resend: {e}")


if __name__ == "__main__":
    run_expansion_hunter()
