import html
import urllib.parse
import calendar as pycalendar
from datetime import date, datetime

import streamlit as st
from dotenv import load_dotenv

from db import (
    init_db, list_leads, save_lead, get_lead, add_follow_up,
    update_remarks_anticipation, is_due_soon, update_lead_status, delete_lead,
    list_task_lists, create_task_list, list_tasks, add_task, toggle_task, delete_task, delete_task_list,
    rescore_existing_leads,
)
from ai import analyze_lead, chat_about_lead, generate_synopsis

load_dotenv()
init_db()
st.set_page_config(
    page_title="Masal AI — Lead Prioritization Assistant",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------- Design system ----------
st.markdown(r"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');
:root { --bg:#182235; --panel:#202d43; --panel2:#263650; --line:#405371; --muted:#b8c6dc; --text:#f5f7ff; --red:#ff4d61; --blue:#85b2ff; --green:#36d6b0; --amber:#ffc45c; }
html, body, [class*="css"] { font-family:'DM Sans',sans-serif; }
.stApp { background: radial-gradient(ellipse at 12% 0%, #344865 0%, #202d42 48%, var(--bg) 100%); color:var(--text); }
.block-container { max-width: 1800px; padding-top:1.35rem; padding-bottom:2rem; }
header[data-testid="stHeader"] { background:transparent; }
#MainMenu, footer { visibility:hidden; }
h1,h2,h3,h4 { font-family:'Manrope',sans-serif !important; letter-spacing:-.035em; color:var(--text); }
h1 { font-size:1.75rem !important; font-weight:800 !important; }
h2 { font-size:1.25rem !important; font-weight:750 !important; }
h3 { font-size:1.05rem !important; font-weight:750 !important; }
p, label, .stCaption { color:var(--text); }
small, [data-testid="stCaptionContainer"] { color:var(--muted) !important; }
div[data-testid="stVerticalBlock"] > div:has(> div.metric-card) { min-width:0; }
.metric-card { background:linear-gradient(145deg,#263650,#202d43); border:1px solid #405371; border-radius:15px; padding:17px 18px; min-height:102px; box-shadow:0 8px 24px #00000014; }
.metric-top { display:flex; align-items:center; gap:12px; }
.metric-icon { display:flex; align-items:center; justify-content:center; width:42px;height:42px;border-radius:12px;font-size:20px;background:#202c49; }
.metric-value { font-family:'Manrope',sans-serif;font-size:27px;font-weight:800;line-height:1.1;color:#f5f7ff; }
.metric-label { font-size:13px;color:#c4cee0;margin-top:4px; }
.metric-hint { font-size:11px;color:#8391aa;margin-top:2px; }
.panel { background:linear-gradient(150deg,#263650,#202d43); border:1px solid #405371; border-radius:16px; padding:16px; }
.panel-head { display:flex;justify-content:space-between;align-items:center;gap:10px;margin-bottom:8px; }
.panel-title { font-family:'Manrope',sans-serif;font-size:18px;font-weight:800;color:#edf2ff; }
.panel-sub { color:#94a3bc;font-size:12px;margin-top:3px; }
.lead-row { border:1px solid #34445f; background:#222f45; border-radius:12px; padding:12px; margin:7px 0; }
.lead-row.selected { border-color:#ff5266; box-shadow:inset 3px 0 #ff5266,0 0 0 1px #ff52661a; background:linear-gradient(90deg,#342b3d,#202d43 70%); }
.lead-name { font-weight:700;color:#eef3ff;font-size:14px; }
.lead-meta { color:#93a2bb;font-size:11px;line-height:1.6; }
.score { color:#f1f5ff;font-weight:800;font-size:15px; }
.pill { display:inline-block;padding:4px 9px;border-radius:999px;font-size:11px;font-weight:700;white-space:nowrap;border:1px solid transparent; }
.pill-hot { color:#ff7888;background:#3b1d2a;border-color:#743044; }
.pill-warm { color:#ffd27c;background:#382d1a;border-color:#705322; }
.pill-cold { color:#9bc0ff;background:#1c2b43;border-color:#344d72; }
.pill-due { color:#ff8590;background:#3b1d2a;border-color:#743044; }
.pill-soon { color:#ffd27c;background:#382d1a;border-color:#705322; }
.pill-neutral { color:#b8c4da;background:#1c2637;border-color:#35435b; }
.score-track { height:5px;border-radius:10px;background:#283247;margin-top:5px;overflow:hidden; }
.score-fill { height:100%;border-radius:10px;background:linear-gradient(90deg,#ff5266,#ff7780); }
.info-tile { background:#2a3952;border:1px solid #405371;border-radius:11px;padding:11px 12px;height:100%; }
.info-label { color:#94a3bc;font-size:11px; }
.info-value { color:#edf2ff;font-size:13px;font-weight:700;margin-top:4px;overflow-wrap:anywhere; }
.action-card { background:linear-gradient(110deg,#2a1b2b,#171c2b);border:1px solid #623044;border-radius:12px;padding:13px 14px; }
.action-label { color:#ff7182;font-size:11px;font-weight:800;text-transform:uppercase;letter-spacing:.04em; }
.action-text { color:#ffd5dc;font-weight:700;font-size:14px;margin-top:5px; }
.section-label { color:#dce5f7;font-weight:750;font-size:14px;margin:10px 0 6px; }
div[data-testid="stExpander"] { background:#202d43;border:1px solid #405371;border-radius:12px; }
div[data-testid="stExpander"] details summary p { color:#edf2ff;font-weight:650; }
.stTextInput input,.stTextArea textarea,.stSelectbox div[data-baseweb="select"],.stDateInput input { background:#2a3952 !important;color:#f5f7ff !important;border-color:#4a5e7d !important;border-radius:9px !important; }
.stTextInput label,.stTextArea label,.stSelectbox label,.stDateInput label { color:#cbd5e6 !important;font-size:12px !important; }
.stButton > button,.stFormSubmitButton > button { border:1px solid #405371;border-radius:9px;background:#2a3952;color:#f2f5ff;font-weight:650;min-height:39px;transition:all .15s ease; }
.stButton > button:hover,.stFormSubmitButton > button:hover { border-color:#ff596b;color:#fff;background:#35445d; }
button[kind="primaryFormSubmit"],.stButton button[kind="primary"] { background:linear-gradient(100deg,#ff4058,#f34b5c) !important;border:0 !important;color:white !important; }
.stTabs [data-baseweb="tab-list"] { gap:6px;border-bottom:1px solid #273248; }
.stTabs [data-baseweb="tab"] { background:transparent;color:#aab7cd;border-radius:8px 8px 0 0;padding:9px 12px; }
.stTabs [aria-selected="true"] { color:#ff6879 !important;border-bottom:2px solid #ff5266 !important; }
hr { border-color:#273248 !important; }
[data-testid="stChatMessage"] { background:#263650;border:1px solid #405371;border-radius:12px;padding:10px; }
[data-testid="stChatInput"] textarea { background:#2a3952 !important;color:#edf2ff !important; }
div[data-testid="stAlert"] { border-radius:10px; }
@media (max-width: 900px) { .block-container{padding-left:1rem;padding-right:1rem;} .metric-card{padding:12px;min-height:90px;} .metric-value{font-size:22px;} }
</style>
""", unsafe_allow_html=True)


def esc(value):
    return html.escape(str(value or ""))


def tier_class(tier):
    return {"Hot": "pill-hot", "Warm": "pill-warm", "Cold": "pill-cold"}.get(tier, "pill-neutral")


def due_badge(date_value):
    due = is_due_soon(date_value)
    if due == "today":
        return '<span class="pill pill-due">● Due today</span>'
    if due == "tomorrow":
        return '<span class="pill pill-soon">◷ Due tomorrow</span>'
    if due == "overdue":
        return '<span class="pill pill-due">! Overdue</span>'
    if date_value:
        return f'<span class="pill pill-neutral">◷ {esc(date_value)}</span>'
    return '<span class="pill pill-neutral">No follow-up</span>'


def metric(icon, value, label, hint, color):
    st.markdown(f'''<div class="metric-card"><div class="metric-top"><div class="metric-icon" style="background:{color}22">{icon}</div><div><div class="metric-value">{value}</div><div class="metric-label">{label}</div><div class="metric-hint">{hint}</div></div></div></div>''', unsafe_allow_html=True)


# ---------- Header ----------
leads = list_leads()
if "selected_lead_id" not in st.session_state:
    st.session_state.selected_lead_id = leads[0]["id"] if leads else None
if st.session_state.selected_lead_id and not any(x["id"] == st.session_state.selected_lead_id for x in leads):
    st.session_state.selected_lead_id = leads[0]["id"] if leads else None

head_a, head_b = st.columns([5, 1.5], vertical_alignment="center")
with head_a:
    st.markdown("<div style='display:flex;align-items:center;gap:13px'><div style='font-size:34px'>🏠</div><div><div style='font-family:Manrope;font-weight:800;font-size:25px;letter-spacing:-1px;color:#f3f6ff'>Masal AI <span style='color:#596780;font-weight:400'>|</span> <span style='font-size:18px;font-weight:600'>Lead Prioritization Assistant</span></div><div style='font-size:12px;color:#9aa8c0'>Sales Cracker Trio • AI-powered lead scoring, follow-ups & grounded chat</div></div></div>", unsafe_allow_html=True)
with head_b:
    st.markdown("<div style='text-align:right;color:#5ce0b9;font-size:12px;font-weight:800;padding:8px'>● AI WORKSPACE</div>", unsafe_allow_html=True)
st.write("")

hot = sum(1 for l in leads if l.get("tier") == "Hot")
warm = sum(1 for l in leads if l.get("tier") == "Warm")
due_today = sum(1 for l in leads if is_due_soon(l.get("next_follow_up")) == "today")
m1, m2, m3, m4, addcol = st.columns([1, 1, 1, 1.15, .85], gap="small")
with m1: metric("♟", len(leads), "Total Leads", "All incoming leads", "#6c8dff")
with m2: metric("🔥", hot, "Hot Leads", "Score ≥ 70", "#ff5266")
with m3: metric("🟡", warm, "Warm Leads", "Score 40–69", "#ffc45c")
with m4: metric("▣", due_today, "Follow-ups Due Today", "Action required", "#ff5266")
with addcol:
    st.write("")
    st.write("")
    add_clicked = st.button("＋  Add New Lead", type="primary", use_container_width=True)

follow_up_count = sum(1 for item in leads if item.get("status", "Follow Up") == "Follow Up")
sale_closed_count = sum(1 for item in leads if item.get("status", "Follow Up") == "Sale Closed")
no_sale_count = sum(1 for item in leads if item.get("status", "Follow Up") == "No Sale Made")
s1, s2, s3 = st.columns(3, gap="small")
with s1: metric("↻", follow_up_count, "Follow Up", "Leads still in progress", "#6c8dff")
with s2: metric("✓", sale_closed_count, "Sale Closed", "Successful conversions", "#36d6b0")
with s3: metric("×", no_sale_count, "No Sale Made", "Lost opportunities", "#ff5266")

if leads:
    with st.expander("⚙️ Lead scoring tools", expanded=False):
        st.caption("Recalculate saved leads using the same transparent scoring rules. This does not call the AI API or change the qualitative summaries.")
        if st.button("Recalculate all lead scores", key="rescore_existing_leads"):
            count = rescore_existing_leads()
            st.success(f"Recalculated scores for {count} saved lead(s).")
            st.rerun()

if add_clicked:
    st.session_state.show_add_form = not st.session_state.get("show_add_form", False)

if st.session_state.get("show_add_form", False):
    with st.container(border=True):
        st.markdown("### Add a lead · AI analysis")
        with st.form("lead_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            with c1:
                name = st.text_input("Full name *", placeholder="Priya Nair")
                mobile = st.text_input("Mobile *", placeholder="9876543210")
                location = st.text_input("Preferred location *", placeholder="Whitefield, Bengaluru")
            with c2:
                email = st.text_input("Email *", placeholder="priya@example.com")
                property_req = st.text_input("Property requirement *", placeholder="3 BHK apartment")
                budget = st.text_input("Budget *", placeholder="₹85 lakh")
            with c3:
                timeline = st.text_input("Buying timeline *", placeholder="Within 30 days")
                message = st.text_area("Customer message *", placeholder="Share the customer's inquiry or transcript…", height=150)
            submitted = st.form_submit_button("✦ Analyze & Save Lead", type="primary", use_container_width=True)
            if submitted:
                if not all([name.strip(), mobile.strip(), email.strip(), location.strip(), property_req.strip(), budget.strip(), timeline.strip(), message.strip()]):
                    st.error("Please complete all required fields.")
                else:
                    lead_input = {"name": name.strip(), "mobile": mobile.strip(), "email": email.strip(), "location": location.strip(), "property_requirement": property_req.strip(), "budget": budget.strip(), "timeline": timeline.strip(), "message": message.strip()}
                    try:
                        with st.spinner("Masal AI is analyzing the lead…"):
                            analysis = analyze_lead(lead_input)
                            new_id = save_lead(lead_input, analysis)
                        st.session_state.selected_lead_id = new_id
                        st.session_state.show_add_form = False
                        st.success("Lead analyzed and saved.")
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Could not analyze this lead. Check your Groq API configuration and try again. Details: {exc}")

st.write("")
left, right = st.columns([1.35, 1], gap="large")

# ---------- Lead pipeline ----------
with left:
    st.markdown('<div class="panel-head"><div><div class="panel-title">▤ &nbsp; Lead Pipeline</div><div class="panel-sub">Review incoming leads, ranked by priority</div></div></div>', unsafe_allow_html=True)
    search = st.text_input("Search leads", placeholder="⌕  Search by name, location or requirement…", label_visibility="collapsed", key="lead_search")
    filters = st.radio("Filter leads", ["All", "🔥 Hot", "🟡 Warm", "❄ Cold", "▣ Due Today"], horizontal=True, label_visibility="collapsed", key="lead_filter")
    status_filter = st.selectbox("Sales status", ["All statuses", "Follow Up", "Sale Closed", "No Sale Made"], key="lead_status_filter")
    filtered = []
    for lead in leads:
        haystack = " ".join(str(lead.get(k, "")) for k in ["name", "location", "property_requirement", "budget"]).lower()
        if search.lower().strip() and search.lower().strip() not in haystack:
            continue
        due = is_due_soon(lead.get("next_follow_up"))
        if filters == "🔥 Hot" and lead.get("tier") != "Hot": continue
        if filters == "🟡 Warm" and lead.get("tier") != "Warm": continue
        if filters == "❄ Cold" and lead.get("tier") != "Cold": continue
        if filters == "▣ Due Today" and due != "today": continue
        if status_filter != "All statuses" and lead.get("status", "Follow Up") != status_filter: continue
        filtered.append(lead)
    st.markdown(f'<div class="panel-sub" style="margin:8px 0 10px">Showing <b style="color:#edf2ff">{len(filtered)}</b> of {len(leads)} leads</div>', unsafe_allow_html=True)
    if filtered:
        lead_choices = {f"{x.get('name', 'Unnamed')} · {x.get('tier', 'Cold')} · {x.get('score', 0)}/100 · ID {x['id']}": x["id"] for x in filtered}
        current_label = next((label for label, lead_id in lead_choices.items() if lead_id == st.session_state.selected_lead_id), next(iter(lead_choices)))
        chosen_label = st.selectbox("Selected lead workspace", list(lead_choices.keys()), index=list(lead_choices.keys()).index(current_label), label_visibility="collapsed", key="workspace_lead_choice")
        chosen_id = lead_choices[chosen_label]
        if chosen_id != st.session_state.selected_lead_id:
            st.session_state.selected_lead_id = chosen_id
            st.rerun()
    if not filtered:
        st.info("No leads match this view. Add a lead or adjust your filters.")
    for lead in filtered:
        is_selected = lead["id"] == st.session_state.selected_lead_id
        tier = lead.get("tier", "Cold")
        due = lead.get("next_follow_up")
        score = max(0, min(100, int(lead.get("score") or 0)))
        icon = {"Hot": "🔥", "Warm": "🟡", "Cold": "❄️"}.get(tier, "•")
        status = lead.get("status", "Follow Up")
        status_icon = {"Follow Up": "↻", "Sale Closed": "✓", "No Sale Made": "×"}.get(status, "↻")
        st.markdown(f'''<div class="lead-row {"selected" if is_selected else ""}"><div style="display:flex;align-items:center;gap:10px"><div style="flex:1;min-width:0"><div class="lead-name">{icon} &nbsp;{esc(lead.get('name'))}</div><div class="lead-meta">{esc(lead.get('property_requirement'))} &nbsp;·&nbsp; 📍 {esc(lead.get('location'))}</div></div><div style="text-align:right;min-width:55px"><div class="score">{score}<span style="font-size:10px;color:#7e8ba3"> /100</span></div><div class="score-track"><div class="score-fill" style="width:{score}%;background:{'#ff5266' if tier == 'Hot' else '#ffc45c' if tier == 'Warm' else '#8ba2c7'}"></div></div></div><span class="pill {tier_class(tier)}">{esc(tier)}</span></div><div style="display:flex;justify-content:space-between;align-items:center;gap:8px;margin-top:8px"><div class="lead-meta">Budget <b style="color:#dce5f7">{esc(lead.get('budget'))}</b> &nbsp;·&nbsp; Timeline {esc(lead.get('timeline'))}</div><span class="pill pill-neutral">{status_icon} {esc(status)}</span>{due_badge(due)}</div></div>''', unsafe_allow_html=True)
        if is_selected:
            st.caption("✓ Selected · details shown in the workspace")


# ---------- Selected lead workspace ----------
with right:
    st.markdown('<div class="panel-head"><div><div class="panel-title">▤ &nbsp; Selected Lead</div><div class="panel-sub">AI analysis, follow-ups and grounded chat</div></div></div>', unsafe_allow_html=True)
    selected_id = st.session_state.get("selected_lead_id")
    lead = get_lead(selected_id) if selected_id else None
    if not lead:
        st.markdown('<div class="panel" style="text-align:center;padding:40px 18px"><div style="font-size:32px">👤</div><h3>No lead selected</h3><div class="panel-sub">Add a lead or choose one from the pipeline.</div></div>', unsafe_allow_html=True)
    else:
        analysis = lead.get("analysis") or {}
        tier = lead.get("tier", "Cold")
        score = max(0, min(100, int(lead.get("score") or 0)))
        c1, c2 = st.columns([3, 1])
        with c1:
            st.markdown(f'<div style="font-family:Manrope;font-size:21px;font-weight:800;color:#f1f5ff">{esc(lead.get("name"))} &nbsp;<span class="pill {tier_class(tier)}">{esc(tier)}</span></div><div class="panel-sub">⌂ &nbsp;{esc(lead.get("property_requirement"))} &nbsp; · &nbsp; 📍 {esc(lead.get("location"))}</div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div style="text-align:right"><div class="panel-sub">Lead score</div><div style="font-size:26px;font-weight:800;color:#f2f5ff">{score}<span style="font-size:13px;color:#8d9bb4"> /100</span></div><div class="score-track"><div class="score-fill" style="width:{score}%"></div></div></div>', unsafe_allow_html=True)
        st.write("")
        a, b, c = st.columns(3)
        for col, label, value in [(a, "BUDGET", lead.get("budget")), (b, "BUYING TIMELINE", lead.get("timeline")), (c, "FOLLOW-UPS", lead.get("follow_up_count", 0))]:
            with col:
                st.markdown(f'<div class="info-tile"><div class="info-label">{label}</div><div class="info-value">{esc(value)}</div></div>', unsafe_allow_html=True)
        st.write("")
        st.markdown('<div class="section-label">▣ &nbsp; Sales outcome</div>', unsafe_allow_html=True)
        status_options = ["Follow Up", "Sale Closed", "No Sale Made"]
        saved_status = lead.get("status", "Follow Up")
        status_col, status_btn_col = st.columns([2, 1])
        with status_col:
            chosen_status = st.selectbox(
                "Lead status", status_options,
                index=status_options.index(saved_status) if saved_status in status_options else 0,
                key=f"lead_status_{selected_id}",
            )
        with status_btn_col:
            st.write("")
            st.write("")
            if st.button("Save status", key=f"save_lead_status_{selected_id}", use_container_width=True):
                update_lead_status(selected_id, chosen_status)
                st.success(f"Status updated to {chosen_status}.")
                st.rerun()

        with st.expander("⚠️ Delete this lead", expanded=False):
            st.warning(f"This permanently deletes {lead.get('name', 'this lead')} and its follow-up history. This cannot be undone.")
            confirm_delete = st.checkbox("I understand — permanently delete this lead", key=f"confirm_delete_lead_{selected_id}")
            if st.button("Delete lead permanently", key=f"delete_lead_{selected_id}", type="primary", disabled=not confirm_delete, use_container_width=True):
                deleted = delete_lead(selected_id)
                st.session_state.get("chat_history", {}).pop(selected_id, None)
                remaining = list_leads()
                st.session_state.selected_lead_id = remaining[0]["id"] if remaining else None
                st.success("Lead deleted." if deleted else "Lead was already deleted.")
                st.rerun()

        st.write("")
        st.markdown('<div class="section-label">✦ &nbsp; AI Summary</div>', unsafe_allow_html=True)
        st.write(analysis.get("summary", "No summary available."))
        if analysis.get("intent"):
            st.markdown(f'<div class="info-tile"><div class="info-label">CUSTOMER INTENT</div><div class="info-value">{esc(analysis.get("intent"))}</div></div>', unsafe_allow_html=True)
        st.write("")
        st.markdown(f'<div class="action-card"><div class="action-label">➤ &nbsp; Next best action</div><div class="action-text">{esc(analysis.get("next_action", "Qualify requirements"))}</div></div>', unsafe_allow_html=True)
        st.write("")
        st.markdown('<div class="section-label">✉ &nbsp; Suggested Response</div>', unsafe_allow_html=True)
        response = analysis.get("suggested_response", "Thank you for your inquiry. Could you share more details about your requirements?")
        st.text_area("Customer-ready message · editable copy", value=response, height=360, key=f"suggested_response_{selected_id}", help="The larger editor is designed to show long replies without a small horizontal-scroll code box.")
        wa_number = "".join(ch for ch in str(lead.get("mobile", "")) if ch.isdigit())
        encoded = urllib.parse.quote(response)
        email_body = urllib.parse.quote(response)
        wa_url = f"https://wa.me/{wa_number}?text={encoded}"
        email_url = f"mailto:{urllib.parse.quote(str(lead.get('email','')))}?subject=Property%20inquiry&body={email_body}"
        b1, b2 = st.columns(2)
        with b1: st.link_button("☏  Open WhatsApp", wa_url, use_container_width=True)
        with b2: st.link_button("✉  Send Email", email_url, use_container_width=True)
        if analysis.get("objections"):
            with st.expander("⚑  Objections & concerns"):
                for item in analysis.get("objections", []): st.write(f"• {item}")
        if analysis.get("objection_busters"):
            with st.expander("✦  Objection Buster · Talking points"):
                for item in analysis.get("objection_busters", []): st.write(f"• {item}")



# ---------- Calendar + multi-list task planner ----------
st.markdown("---")
st.markdown('<div class="panel-title">🗓️ &nbsp; Work Planner</div><div class="panel-sub">Coordinate follow-ups and keep personal or team task lists in one place.</div>', unsafe_allow_html=True)
cal_col, todo_col = st.columns([1, 1], gap="large")

# Selected calendar date and month navigation live in session state.
if "planner_month" not in st.session_state:
    st.session_state.planner_month = date.today().replace(day=1)
if "planner_selected_date" not in st.session_state:
    st.session_state.planner_selected_date = date.today()

with cal_col:
    st.markdown('<div class="panel-head"><div><div class="panel-title">🗓️ Calendar</div><div class="panel-sub">Lead follow-ups and task due dates</div></div></div>', unsafe_allow_html=True)
    nav_prev, nav_label, nav_next = st.columns([1, 4, 1])
    with nav_prev:
        if st.button("←", key="cal_prev", use_container_width=True):
            m = st.session_state.planner_month
            st.session_state.planner_month = (m.replace(day=1) - __import__('datetime').timedelta(days=1)).replace(day=1)
            st.rerun()
    with nav_label:
        st.markdown(f"<div style='text-align:center;padding:8px;font-weight:800'>{st.session_state.planner_month.strftime('%B %Y')}</div>", unsafe_allow_html=True)
    with nav_next:
        if st.button("→", key="cal_next", use_container_width=True):
            m = st.session_state.planner_month
            st.session_state.planner_month = (m.replace(day=28) + __import__('datetime').timedelta(days=4)).replace(day=1)
            st.rerun()

    # Build date markers from saved lead follow-ups and to-do tasks.
    event_counts = {}
    for item in leads:
        dstr = item.get("next_follow_up")
        try:
            if dstr:
                d = date.fromisoformat(dstr[:10]); event_counts[d] = event_counts.get(d, 0) + 1
        except ValueError:
            pass
    try:
        for task in list_tasks():
            if task.get("due_date") and not task.get("completed"):
                d = date.fromisoformat(task["due_date"][:10]); event_counts[d] = event_counts.get(d, 0) + 1
    except Exception:
        pass

    weekdays = st.columns(7, gap="small")
    for col, day_name in zip(weekdays, ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]):
        with col:
            st.caption(day_name)
    month_grid = pycalendar.monthcalendar(st.session_state.planner_month.year, st.session_state.planner_month.month)
    for week_index, week in enumerate(month_grid):
        day_cols = st.columns(7, gap="small")
        for col, day_num in zip(day_cols, week):
            with col:
                if day_num == 0:
                    st.write(" ")
                else:
                    d = date(st.session_state.planner_month.year, st.session_state.planner_month.month, day_num)
                    marker = " •" if event_counts.get(d) else ""
                    label = f"{day_num}{marker}"
                    if st.button(label, key=f"cal_day_{d.isoformat()}", use_container_width=True, type="primary" if d == st.session_state.planner_selected_date else "secondary"):
                        st.session_state.planner_selected_date = d
                        st.rerun()
    selected_date = st.session_state.planner_selected_date
    st.markdown(f"**{selected_date.strftime('%A, %d %B %Y')}**")
    selected_events = []
    for item in leads:
        if (item.get("next_follow_up") or "")[:10] == selected_date.isoformat():
            selected_events.append(("Lead follow-up", f"{item.get('name','Lead')} · {item.get('tier','Cold')} lead"))
    try:
        for task in list_tasks():
            if task.get("due_date") == selected_date.isoformat() and not task.get("completed"):
                selected_events.append(("To-do", task.get("title", "Task")))
    except Exception:
        pass
    if selected_events:
        for kind, description in selected_events:
            st.markdown(f"<div class='lead-row'><span class='pill pill-neutral'>{esc(kind)}</span> &nbsp; {esc(description)}</div>", unsafe_allow_html=True)
    else:
        st.caption("No follow-ups or open tasks scheduled for this date.")
    with st.form("calendar_quick_task", clear_on_submit=True):
        st.markdown("**Quick-add a task for this date**")
        quick_title = st.text_input("Task", placeholder="e.g. Call Priya with property options")
        task_lists_for_quick = list_task_lists()
        quick_list_options = {x["name"]: x["id"] for x in task_lists_for_quick}
        quick_list_name = st.selectbox("List", list(quick_list_options.keys()) or ["General"])
        if st.form_submit_button("＋ Add task to calendar", use_container_width=True):
            if quick_title.strip():
                list_id = quick_list_options.get(quick_list_name)
                if list_id is None:
                    list_id = create_task_list("General")
                add_task(list_id, quick_title.strip(), selected_date.isoformat())
                st.success("Task added to calendar.")
                st.rerun()
            else:
                st.warning("Enter a task title first.")

with todo_col:
    st.markdown('<div class="panel-head"><div><div class="panel-title">☑️ To-do lists</div><div class="panel-sub">Create multiple lists and track tasks across your workday.</div></div></div>', unsafe_allow_html=True)
    lists = list_task_lists()
    with st.form("create_task_list_form", clear_on_submit=True):
        new_list_name = st.text_input("Create a new list", placeholder="e.g. Site visits, High-priority leads, Admin")
        create_list_clicked = st.form_submit_button("＋ Create list", use_container_width=True)
        if create_list_clicked:
            if new_list_name.strip():
                create_task_list(new_list_name.strip())
                st.success("List created.")
                st.rerun()
            else:
                st.warning("Enter a name for the list.")
    lists = list_task_lists()
    if not lists:
        default_list_id = create_task_list("My tasks")
        st.rerun()
    list_names = {x["name"]: x["id"] for x in lists}
    selected_list_name = st.selectbox("Current list", list(list_names.keys()), key="todo_selected_list")
    selected_list_id = list_names[selected_list_name]
    with st.form(f"add_task_form_{selected_list_id}", clear_on_submit=True):
        task_title = st.text_input("Task title", placeholder="e.g. Send property shortlist to Ajith")
        task_due = st.date_input("Due date", value=st.session_state.planner_selected_date, key=f"task_due_{selected_list_id}")
        add_task_clicked = st.form_submit_button("＋ Add task", use_container_width=True)
        if add_task_clicked:
            if task_title.strip():
                add_task(selected_list_id, task_title.strip(), task_due.isoformat())
                st.success("Task added.")
                st.rerun()
            else:
                st.warning("Enter a task title first.")
    tasks = list_tasks(selected_list_id)
    open_tasks = [t for t in tasks if not t.get("completed")]
    done_tasks = [t for t in tasks if t.get("completed")]
    st.caption(f"{len(open_tasks)} open · {len(done_tasks)} completed")
    if not tasks:
        st.info("This list is empty. Add your first task above.")
    for task in open_tasks + done_tasks:
        row = st.columns([0.12, 0.70, 0.18], vertical_alignment="center")
        with row[0]:
            checked = st.checkbox("Complete", value=bool(task.get("completed")), key=f"task_done_{task['id']}", label_visibility="collapsed")
            if checked != bool(task.get("completed")):
                toggle_task(task["id"], checked)
                st.rerun()
        with row[1]:
            title_style = "text-decoration:line-through;color:#91a0b7" if task.get("completed") else "color:#edf2ff"
            st.markdown(f"<div style='{title_style};font-weight:650'>{esc(task.get('title'))}</div><div class='panel-sub'>Due {esc(task.get('due_date') or 'No date')}</div>", unsafe_allow_html=True)
        with row[2]:
            if st.button("✕", key=f"delete_task_{task['id']}", help="Delete task"):
                delete_task(task["id"])
                st.rerun()
    if len(lists) > 1:
        with st.expander("Manage lists"):
            st.caption("Deleting a list also deletes the tasks inside it.")
            list_to_delete = st.selectbox("List to delete", [x["name"] for x in lists], key="delete_list_choice")
            if st.button("Delete selected list", key="delete_task_list_button"):
                if len(lists) <= 1:
                    st.warning("Keep at least one task list.")
                else:
                    delete_task_list(list_names[list_to_delete])
                    st.rerun()


# Full-width interaction workspace: prevents the long detail panel from leaving a large empty left column.
if lead:
    st.markdown("---")
    st.markdown('<div class="panel-title">✨ &nbsp; Sales Cracker Trio</div><div class="panel-sub">Keep every interaction connected to the next best action.</div>', unsafe_allow_html=True)
    t1, t2, t3 = st.tabs(["↻ Follow-up Trail", "✎ Remarks & Anticipation", "▤ Interaction Synopsis"])
    with t1:
        st.markdown(f"**Follow-up history** · {lead.get('follow_up_count', 0)} logged interactions")
        if lead.get("next_follow_up"):
            st.markdown(due_badge(lead.get("next_follow_up")), unsafe_allow_html=True)
        if lead.get("follow_ups"):
            for fu in lead["follow_ups"]:
                st.markdown(f"**{esc(fu.get('created_at','')[:16])}** · {esc(fu.get('outcome',''))}")
                if fu.get("follow_up_date"):
                    st.caption(f"Next follow-up: {fu.get('follow_up_date')}")
                st.write(fu.get("notes", ""))
                st.divider()
        else:
            st.caption("No interactions logged yet. Add the first touch below.")
        with st.form(f"fu_form_{selected_id}"):
            st.markdown("**Log a new follow-up**")
            fu_date = st.date_input("Next follow-up date", value=date.today(), key=f"fu_date_{selected_id}")
            fu_notes = st.text_area("Interaction notes", placeholder="What happened on the call? What did the customer say?", key=f"fu_notes_{selected_id}", height=90)
            fu_outcome = st.selectbox("Outcome", ["Interested", "Callback", "Site visit scheduled", "Not interested", "Nurture", "Closed"], key=f"fu_outcome_{selected_id}")
            log_fu = st.form_submit_button("＋ Add to trail", use_container_width=True)
            if log_fu:
                try:
                    add_follow_up(selected_id, fu_date.isoformat(), fu_notes, fu_outcome)
                    with st.spinner("Writing interaction synopsis…"):
                        syn = generate_synopsis(lead, fu_notes, fu_outcome)
                        update_remarks_anticipation(selected_id, lead.get("remarks", ""), lead.get("anticipation", ""), syn)
                    st.success("Follow-up logged and synopsis updated.")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Follow-up was saved, but synopsis generation failed: {exc}")
    with t2:
        st.caption("These notes are included in the context used by grounded chat and synopsis generation.")
        remarks = st.text_area("Remarks · How did the call go?", value=lead.get("remarks", ""), max_chars=12000, height=140, key=f"remarks_{selected_id}", placeholder="Customer's reaction, questions, preferences, and details from the call…")
        anticipation = st.text_area("Anticipation · What do you expect next?", value=lead.get("anticipation", ""), height=100, key=f"anticipation_{selected_id}", placeholder="Likely objection, expected next question, or planned approach…")
        if st.button("Save remarks & anticipation", key=f"save_notes_{selected_id}", use_container_width=True):
            update_remarks_anticipation(selected_id, remarks, anticipation, lead.get("synopsis", ""))
            st.success("Sales notes saved.")
            st.rerun()
    with t3:
        synopsis = lead.get("synopsis", "")
        if synopsis:
            st.info(synopsis)
        else:
            st.caption("No synopsis yet. Log a follow-up to generate a short recap of the latest interaction.")
        st.markdown("**What this gives the salesperson**")
        st.write("A concise handover into the next conversation, based on the latest outcome and the salesperson's notes.")

    st.markdown("---")
    st.markdown('<div class="panel-title">☏ &nbsp; Grounded Chat</div><div class="panel-sub">Ask about this lead. Answers use the lead profile, analysis, notes and follow-up trail.</div>', unsafe_allow_html=True)
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = {}
    history = st.session_state.chat_history.get(selected_id, [])
    for msg in history[-10:]:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
    question = st.chat_input("Ask about this lead (e.g. what should I emphasize on the call?)", key=f"chat_{selected_id}")
    if question:
        try:
            with st.spinner("Thinking with this lead's context…"):
                answer = chat_about_lead(lead, history, question)
            history.extend([{"role": "user", "content": question}, {"role": "assistant", "content": answer}])
            st.session_state.chat_history[selected_id] = history[-20:]
            st.rerun()
        except Exception as exc:
            st.error(f"Chat could not reach the AI model. Check your Groq API configuration. Details: {exc}")
st.markdown("<div style='text-align:center;color:#65738d;font-size:11px;padding:24px 0 4px'>MASAL AI · LEAD INTELLIGENCE WORKSPACE · BUILT FOR SALES TEAMS</div>", unsafe_allow_html=True)
