import os
import json
from dotenv import load_dotenv
from groq import Groq
from prompts import ANALYSIS_PROMPT, CHAT_SYSTEM_PROMPT, SYNOPSIS_PROMPT
from scoring import score_lead

load_dotenv()

client = None
if os.getenv("GROQ_API_KEY"):
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

MODEL = "openai/gpt-oss-20b"


def call_llm(messages, temperature=0.3, json_mode=False):
    if not client:
        raise RuntimeError("GROQ_API_KEY not set")
    kwargs = {
        "model": MODEL,
        "messages": messages,
        "temperature": temperature,
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    response = client.chat.completions.create(**kwargs)
    return response.choices[0].message.content


def analyze_lead(lead):
    prompt = ANALYSIS_PROMPT.format(
        name=lead.get("name", ""),
        location=lead.get("location", ""),
        property_requirement=lead.get("property_requirement", ""),
        budget=lead.get("budget", ""),
        timeline=lead.get("timeline", ""),
        message=lead.get("message", ""),
        mobile=lead.get("mobile", ""),
        email=lead.get("email", ""),
    )
    raw = call_llm([{"role": "user", "content": prompt}], temperature=0.2, json_mode=True)
    try:
        analysis = json.loads(raw)
        if not isinstance(analysis, dict):
            raise ValueError("AI response was not a JSON object")
    except (json.JSONDecodeError, ValueError, TypeError):
        analysis = {
            "summary": "Lead received; more information is needed to qualify it.",
            "intent": "Exploring",
            "key_requirements": [],
            "objections": [],
            "next_action": "Contact the lead to confirm requirements and buying timeline.",
            "suggested_response": "Thank you for your inquiry. Could you share more about your property preferences and expected buying timeline?",
            "objection_busters": [],
        }

    # Never trust an LLM-generated score/tier: apply the same transparent rubric to every lead.
    scored = score_lead(lead, analysis)
    analysis.update(scored)
    return analysis


def chat_about_lead(lead, history, question):
    analysis = lead.get("analysis") or {}
    trail_lines = []
    for fu in lead.get("follow_ups", [])[:8]:
        trail_lines.append(f"- {fu.get('created_at','')[:10]} | {fu.get('outcome','')} | {fu.get('notes','')[:120]}")
    trail = "\n".join(trail_lines) or "None yet"

    system = CHAT_SYSTEM_PROMPT.format(
        name=lead.get("name", ""),
        location=lead.get("location", ""),
        property_requirement=lead.get("property_requirement", ""),
        budget=lead.get("budget", ""),
        timeline=lead.get("timeline", ""),
        message=lead.get("message", ""),
        mobile=lead.get("mobile", ""),
        email=lead.get("email", ""),
        summary=analysis.get("summary", ""),
        intent=analysis.get("intent", ""),
        key_requirements=", ".join(analysis.get("key_requirements", [])),
        objections=", ".join(analysis.get("objections", [])),
        next_action=analysis.get("next_action", ""),
        suggested_response=analysis.get("suggested_response", ""),
        score=lead.get("score", ""),
        tier=lead.get("tier", ""),
        score_reason=analysis.get("score_reason", ""),
        urgency=analysis.get("urgency", ""),
        objection_busters=", ".join(analysis.get("objection_busters", [])),
        remarks=lead.get("remarks", "")[:1500],
        anticipation=lead.get("anticipation", ""),
        synopsis=lead.get("synopsis", ""),
        follow_up_trail=trail,
    )
    messages = [{"role": "system", "content": system}]
    messages += history[-8:]
    messages.append({"role": "user", "content": question})
    return call_llm(messages, temperature=0.3)


def generate_synopsis(lead, latest_notes, outcome):
    prompt = SYNOPSIS_PROMPT.format(
        notes=latest_notes,
        outcome=outcome,
        remarks=lead.get("remarks", "")[:800],
        anticipation=lead.get("anticipation", ""),
    )
    return call_llm([{"role": "user", "content": prompt}], temperature=0.2)
