# Masal AI — Lead Prioritization Assistant

A Streamlit app for real-estate sales teams. It analyzes inbound leads with a real Groq model, ranks leads, suggests next actions and responses, and keeps follow-up context close to the salesperson.

## Features

- Lead intake with name, mobile, email, location, property requirement, budget, buying timeline, and customer message.
- AI-generated summary, intent, requirements, objections, recommended next action, suggested response, score, tier, urgency, and objection-handling talking points.
- Lead pipeline with search, tier filters, scores, and due-date badges.
- Lead-specific grounded chat.
- WhatsApp and email deep links with a prefilled response.
- **Sales Cracker Trio:** Follow-up Trail, Remarks & Anticipation, and AI-generated Interaction Synopsis.
- SQLite persistence.
- Responsive dark dashboard styling built with Streamlit and custom CSS.

## Stack

- Python + Streamlit
- Groq API using `openai/gpt-oss-20b` (configured in `ai.py`; availability depends on the provider)
- SQLite
- `python-dotenv`

## Run locally

1. Install Python 3.10 or newer.
2. Create and activate a virtual environment.
3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project directory:

   ```env
   GROQ_API_KEY=your_groq_api_key
   ```

5. Start the app:

   ```bash
   streamlit run app.py
   ```

SQLite creates `leads.db` automatically on first run. Do not commit `.env` or API keys to GitHub.

## Deploy to Streamlit Community Cloud

1. Push `app.py`, `ai.py`, `db.py`, `prompts.py`, `requirements.txt`, and this README to a public GitHub repository.
2. Create a Streamlit Community Cloud app pointing to `app.py`.
3. In app settings, add `GROQ_API_KEY` under **Secrets** using TOML syntax:

   ```toml
   GROQ_API_KEY = "your_groq_api_key"
   ```

4. Deploy and test lead creation, analysis, follow-ups, and chat on the live URL.

**Persistence note:** Streamlit Community Cloud's local filesystem is not guaranteed to be durable across all app restarts/redeployments. SQLite is convenient for a small demo, but persistent production data should use a managed database with a free tier and appropriate privacy controls.

## Architecture

- `app.py`: Streamlit UI, navigation, lead pipeline, lead detail workspace, follow-up logging, and chat interaction.
- `ai.py`: Groq API calls for analysis, grounded chat, and synopsis generation.
- `prompts.py`: prompts and output instructions for the AI tasks.
- `db.py`: SQLite schema and database operations.
- `leads.db`: created at runtime; local user data, not source code.

The chat prompt is rebuilt from the selected lead, analysis, salesperson notes, synopsis, and recent follow-up trail. RAG is unnecessary for the current scope because each lead's context is small and structured.

## Known limitations

- Chat history is session-only and clears on refresh; lead records and follow-ups are stored in SQLite.
- Due indicators are visual; there are no push notifications or automated email reminders.
- WhatsApp and email are deep links, not direct messaging integrations.
- Groq rate limits and model availability depend on the provider and account.
- Lead scores are model-generated prioritization aids, not calibrated probabilities of conversion. Salespeople should use judgment.
- A deployed local SQLite file may not provide durable storage on ephemeral hosting.

## AI usage disclosure

Update this section before submission to accurately list the AI coding assistants used and what each was used for. Do not claim tools you did not use.
