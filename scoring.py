"""Deterministic lead scoring for Masal AI. The LLM extracts meaning; this module owns score and tier."""
import re


def _text(value):
    if isinstance(value, (list, tuple)):
        return " ".join(str(x) for x in value if x is not None).lower()
    return str(value or "").lower().strip()


def _timeline_points(timeline, message):
    # Prefer the dedicated timeline field. Only inspect the message when that field
    # does not contain a recognizable time horizon, avoiding unrelated date mentions.
    text = _text(timeline)
    if not re.search(r"\b(today|tonight|immediately|immediate|asap|urgent|this week|within a week|7 days|15 days|within 2 weeks|within two weeks|30 days|within 30|within a month|this month|next 4 weeks|2\s*[-–]?\s*4 weeks|30\s*[-–]?\s*60 days?|1\s*[-–]?\s*2 months?|within 60 days|two months|2\s*[-–]?\s*3 months?|60\s*[-–]?\s*90 days?|quarter|3\s*[-–]?\s*6 months?|three to six months|few months|later this year|6 months?|six months|one year|12 months?|next year|after a year|no rush|just browsing|not sure when|someday|just exploring|no timeline)\b", text):
        text = f"{text} {_text(message)}"
    if re.search(r"\b(6\s*months?|six months|one year|12\s*months?|next year|after a year)\b", text):
        return 2, "Long buying horizon"
    if re.search(r"\b(3\s*[-–]?\s*6\s*months?|three to six months|few months|later this year)\b", text):
        return 7, "Buying horizon is several months away"
    if re.search(r"\b(2\s*[-–]?\s*3\s*months?|60\s*[-–]?\s*90\s*days?|quarter)\b", text):
        return 11, "Buying horizon is 2–3 months"
    if re.search(r"\b(30\s*[-–]?\s*60\s*days?|1\s*[-–]?\s*2\s*months?|within 60 days|two months)\b", text):
        return 16, "Buying horizon is within 1–2 months"
    if re.search(r"\b(30 days|within a month|this month|next 4 weeks|2\s*[-–]?\s*4 weeks|within 30)\b", text):
        return 22, "Buying horizon is within 30 days"
    if re.search(r"\b(today|tonight|immediately|immediate|asap|urgent|this week|within a week|7 days|15 days|within 2 weeks|within two weeks)\b", text):
        return 25, "Near-term buying timeline"
    if re.search(r"\b(no rush|just browsing|not sure when|someday|just exploring|no timeline)\b", text):
        return 4, "No clear near-term timeline"
    return 10, "Timeline needs confirmation"


def score_lead(lead, analysis):
    message = _text(lead.get("message"))
    property_req = _text(lead.get("property_requirement"))
    location = _text(lead.get("location"))
    budget = _text(lead.get("budget"))
    timeline = _text(lead.get("timeline"))
    intent = _text(analysis.get("intent"))
    requirements = _text(analysis.get("key_requirements"))
    objections = _text(analysis.get("objections"))
    combined = " ".join([message, intent, requirements, objections])

    if re.search(r"\b(ready to buy|ready to purchase|want to buy|looking to purchase|book( a| the)?|booking|token advance|pay advance|loan approved|finali[sz]e|close the deal|purchase this week)\b", combined):
        intent_points, intent_label = 30, "Strong purchase intent"
    elif re.search(r"\b(site visit|property visit|schedule a visit|viewing|quotation|quote|price breakdown|negotiate|shortlist|shortlisted|compare|comparing|specific requirements|floor plan|availability)\b", combined) or "comparing" in intent:
        intent_points, intent_label = 22, "Actively evaluating options"
    elif re.search(r"\b(exploring|looking around|researching|considering|might buy|may buy|interested|enquir|inquir)\b", combined) or "exploring" in intent:
        intent_points, intent_label = 14, "Some buying interest, needs qualification"
    elif re.search(r"\b(information only|just information|curious|just browsing|not interested)\b", combined):
        intent_points, intent_label = 4, "Low or informational intent"
    else:
        intent_points, intent_label = 10, "Intent is not explicit"

    timeline_points, timeline_label = _timeline_points(timeline, message)

    action_signals = [
        (r"\b(call me|please call|callback|contact me|reach me)\b", 5),
        (r"\b(site visit|property visit|viewing|schedule|appointment)\b", 6),
        (r"\b(quote|quotation|price breakdown|payment plan|emi|loan|financing)\b", 4),
        (r"\b(available|availability|floor plan|amenities|possession|documents)\b", 3),
        (r"\b(negotiat|discount|final price|offer)\b", 3),
    ]
    engagement_points = min(20, sum(points for pattern, points in action_signals if re.search(pattern, message)))
    if len(message.split()) >= 35:
        engagement_points = min(20, engagement_points + 3)
    elif len(message.split()) >= 15:
        engagement_points = min(20, engagement_points + 1)

    specificity_points = 0
    if property_req and property_req not in {"property", "any property", "not sure", "n/a", "na"}:
        specificity_points += 6
        if re.search(r"\b(\d\s*bhk|\d\s*bedroom|villa|plot|land|studio|apartment|flat|independent house|commercial|office|shop)\b", property_req):
            specificity_points += 3
    if location and location not in {"anywhere", "any location", "not sure", "n/a", "na"}:
        specificity_points += 4
    if budget and re.search(r"\d", budget) and not re.search(r"\b(unknown|not sure|flexible|negotiable|no budget)\b", budget):
        specificity_points += 2
    specificity_points = min(15, specificity_points)

    penalty, penalty_reasons = 0, []
    if re.search(r"\b(not interested|do not contact|don't contact|stop calling|already purchased|bought another property)\b", combined):
        penalty += 30
        penalty_reasons.append("explicitly not pursuing this lead")
    if re.search(r"\b(no budget|cannot afford|can't afford|unable to afford|no funds)\b", combined):
        penalty += 12
        penalty_reasons.append("stated affordability blocker")
    if re.search(r"\b(just browsing|only researching|information only|no plan to buy)\b", combined):
        penalty += 8
        penalty_reasons.append("research-only signal")

    score = max(0, min(100, int(round(intent_points + timeline_points + engagement_points + specificity_points - penalty))))
    tier = "Hot" if score >= 70 else "Warm" if score >= 40 else "Cold"
    if re.search(r"\b(not interested|do not contact|don't contact|stop calling|already purchased|bought another property)\b", combined):
        urgency = "Do not pursue unless re-qualified"
    elif tier == "Hot" and timeline_points >= 22:
        urgency = "Call within 1 hour"
    elif tier == "Hot" or timeline_points >= 22:
        urgency = "Follow up today"
    elif tier == "Warm":
        urgency = "Follow up in 24-48 hours"
    else:
        urgency = "Nurture later"

    reasons = [intent_label, timeline_label]
    reasons.append("clear actionable engagement" if engagement_points >= 10 else "few actionable engagement signals" if engagement_points <= 3 else "some engagement signals")
    if specificity_points >= 11:
        reasons.append("specific property/budget/location details")
    reasons.extend(penalty_reasons)
    return {"score": score, "tier": tier, "score_reason": f"{score}/100: " + "; ".join(reasons) + ".", "urgency": urgency}
