# Masal AI — Sales Lead Assistant

Masal AI is an AI-powered lead prioritization assistant designed for real-estate sales teams. It helps salespeople understand inbound enquiries, identify promising prospects, organize follow-ups, and manage their sales pipeline from one interface.

## Features

- **Lead intake and AI analysis:** Capture customer details, location, property requirements, budget, buying timeline, and enquiry message.
- **Lead prioritization:** Assign a numerical score and Hot, Warm, or Cold priority tier to help salespeople focus on promising prospects.
- **AI-generated insights:** Generate a lead summary, customer intent, requirements, objections, recommended next action, and suggested response.
- **Lead management:** Save and review multiple leads, update sales status, filter leads, and delete unwanted records.
- **Grounded lead chat:** Ask follow-up questions using the selected lead's information as context.
- **Sales Cracker Trio:** Follow-up Trail, Remarks & Anticipation, and Interaction Synopsis help salespeople organize follow-up activity and prepare for future interactions.
- **Follow-up planning:** Organize follow-up tasks and to-do lists.
- **Sales communication support:** Use available WhatsApp/email links and objection-handling suggestions to prepare customer outreach.

## Technology Stack

- **Frontend and application framework:** Python, Streamlit
- **AI inference:** Groq API
- **AI model:** `openai/gpt-oss-20b`
- **Database:** SQLite
- **Configuration:** Environment variables for local API credentials

## Architecture Overview

The application is organized into separate modules:

- `app.py` — Streamlit interface, user interactions, lead workspace, and application flow.
- `ai.py` — AI integration and functions used to request AI-generated analysis.
- `prompts.py` — Instructions and prompt templates that guide the AI's responses.
- `scoring.py` — Deterministic lead-scoring logic used to calculate lead priority.
- `db.py` — SQLite database initialization and data-access operations.
- `requirements.txt` — Python dependencies.

### How a lead is processed

1. A salesperson enters the customer's details and enquiry.
2. The application uses the scoring logic to evaluate lead priority using defined criteria.
3. The AI integration sends the relevant prompt and lead information to the Groq API.
4. The AI response provides qualitative insights and suggested sales actions.
5. The application displays the score, priority tier, analysis, and recommended next action.
6. The lead and subsequent management updates are stored through the database layer.

The scoring engine and AI analysis serve different purposes: the scoring engine provides rule-based prioritization, while the language model interprets customer context and generates recommendations.

## AI Model and API Integration

Masal AI uses the Groq API with the `openai/gpt-oss-20b` model.

The AI integration is kept separate from the interface so that model requests and prompt construction can be maintained independently. The prompts provide the lead context and guide the model to generate useful sales insights.

A Groq API key is required for AI-powered features. The key should be supplied through an environment variable or the hosting platform's secrets configuration. It must never be committed to the public repository.

## Run Locally

### 1. Clone the repository

```bash
git clone https://github.com/PratBrat8/Masal-AI---Sales-Lead-Assistant.git
cd Masal-AI---Sales-Lead-Assistant
```

### 2. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Configure the API key

Create a local `.env` file if the application uses `python-dotenv`:

```env
GROQ_API_KEY=your_groq_api_key_here
```

Alternatively, set `GROQ_API_KEY` through your operating system's environment variables.

Never share or commit the real API key.

### 5. Start the application

```bash
python -m streamlit run app.py
```

Open the local URL displayed by Streamlit in your browser.

## Key Technical Decisions

- **Streamlit:** Enables rapid development of an interactive Python application without maintaining a separate frontend and backend.
- **Groq API:** Provides access to the language model for interpreting natural-language enquiries and generating sales recommendations.
- **SQLite:** Offers a lightweight database suitable for a small, self-contained prototype.
- **Rule-based scoring:** Keeps lead prioritization transparent and consistent instead of relying exclusively on a language model's subjective judgment.
- **Modular structure:** Separates UI, AI requests, prompts, scoring, and persistence to make the code easier to maintain and explain.
- **Lead lifecycle management:** Statuses such as Follow Up, Sale Closed, and No Sale Made help distinguish active opportunities from completed or lost prospects.

## Known Limitations

- AI-generated summaries and recommendations can be incorrect or incomplete. Salespeople should verify important information before acting on it.
- Lead scoring is based on the implemented rules and is not a statistically validated prediction of conversion probability.
- The application requires valid Groq API credentials and network access for AI-powered features.
- SQLite is appropriate for a prototype, but a hosted deployment may not provide durable database storage across restarts or rebuilds unless persistent storage is configured.
- The current application is a prototype and does not provide a full multi-user authentication, authorization, or enterprise-grade audit system.
- API availability, rate limits, and model behavior may affect AI features.

## Security and Privacy

Do not commit API keys, local environment files, database files containing real customer information, or private backups. Use synthetic customer information for demonstrations unless appropriate authorization has been obtained.

## Future Improvements

Potential improvements include durable managed database storage, authentication and role-based access, richer sales analytics, configurable scoring criteria, and automated reminders.

## Project

Repository: https://github.com/PratBrat8/Masal-AI---Sales-Lead-Assistant

Live application: Add the deployed application URL here.

## AI Usage Disclosure

AI tools were used as development assistants for project planning, feature design, code drafting and refinement, debugging support, and documentation. The Groq API with `openai/gpt-oss-20b` is also used by the application itself to generate lead insights and sales recommendations. The developer is responsible for reviewing, testing, understanding, and validating the submitted implementation.
### AI Usage Disclosure — Masal AI

I used ChatGPT as a development assistant throughout the Masal AI project for brainstorming and refining features, planning the application architecture, drafting and improving Python code, debugging issues, refining prompts, improving the user interface, preparing documentation, and troubleshooting Git/GitHub workflows.

The application itself integrates the Groq API using the `openai/gpt-oss-20b` model to generate lead summaries, interpret customer intent, identify requirements and objections, and recommend sales actions and responses.

Lead prioritization also uses a separate rule-based scoring engine so that numerical scores and priority tiers follow explicit scoring criteria rather than depending entirely on the language model.

I reviewed and tested the implementation locally and verified the application's main workflow. AI-generated suggestions are treated as assistance for salespeople, not as guaranteed predictions or substitutes for human judgment. I am responsible for reviewing, understanding, and validating the submitted code and its behavior.
