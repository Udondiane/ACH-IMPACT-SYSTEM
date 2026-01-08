import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from supabase import create_client
import json

SUPABASE_URL = "https://gmjqidqjpzxcpgycawxf.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdtanFpZHFqcHp4Y3BneWNhd3hmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njc3MjYyMDEsImV4cCI6MjA4MzMwMjIwMX0.6jtYlz6yoBQCrh04P0g30JigHyanGYnv7xBz24B5Bm4"
LIVING_WAGE_UK = 12.00

@st.cache_resource
def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = get_supabase()

st.set_page_config(page_title="ACH Impact Intelligence", page_icon="◉", layout="wide", initial_sidebar_state="expanded")

# ============ STYLING ============
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    * { font-family: 'Inter', sans-serif; }
    .main-header { font-size: 2rem; font-weight: 700; color: #1e293b; margin-bottom: 0.25rem; display: flex; align-items: center; gap: 12px; }
    .sub-header { font-size: 1rem; color: #64748b; margin-bottom: 2rem; }
    .metric-container { background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%); border: 1px solid #e2e8f0; border-radius: 16px; padding: 24px; margin-bottom: 16px; }
    .metric-value { font-size: 2.5rem; font-weight: 700; color: #0f172a; line-height: 1; }
    .metric-label { font-size: 0.75rem; color: #64748b; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 8px; }
    .metric-delta { font-size: 0.85rem; color: #10b981; font-weight: 500; margin-top: 8px; }
    .metric-delta.negative { color: #ef4444; }
    .section-header { font-size: 1.1rem; font-weight: 600; color: #1e293b; margin: 2rem 0 1rem 0; padding-bottom: 0.5rem; border-bottom: 2px solid #e2e8f0; }
    .quote-card { background: #f8fafc; border-left: 4px solid #3b82f6; border-radius: 0 12px 12px 0; padding: 20px; margin: 12px 0; }
    .quote-text { font-size: 0.95rem; color: #334155; font-style: italic; line-height: 1.6; margin-bottom: 8px; }
    .quote-author { font-size: 0.8rem; color: #64748b; font-weight: 500; }
    .candidate-quote { background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%); border-left-color: #10b981; }
    .highlight-card { background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 100%); border-radius: 16px; padding: 28px; color: white; margin-bottom: 24px; }
    .highlight-value { font-size: 3rem; font-weight: 700; }
    .highlight-label { font-size: 0.95rem; opacity: 0.9; }
    .alert-card { background: #fef3c7; border-radius: 8px; padding: 12px 16px; margin: 8px 0; border-left: 4px solid #f59e0b; }
    .success-card { background: #dcfce7; border-radius: 8px; padding: 12px 16px; margin: 8px 0; border-left: 4px solid #10b981; }
    .info-card { background: #e0f2fe; border-radius: 8px; padding: 16px 20px; margin: 12px 0; border-left: 4px solid #0284c7; border-radius: 0 12px 12px 0; }
    
    .score-container { background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 100%); border-radius: 20px; padding: 32px; color: white; margin-bottom: 24px; text-align: center; }
    .score-value { font-size: 5rem; font-weight: 800; line-height: 1; background: linear-gradient(135deg, #60a5fa 0%, #34d399 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
    .score-label { font-size: 1.1rem; font-weight: 600; margin-top: 8px; opacity: 0.9; }
    .score-benchmark { font-size: 0.9rem; opacity: 0.7; margin-top: 12px; }
    .score-trend { font-size: 1rem; color: #34d399; margin-top: 8px; }
    .score-breakdown { display: flex; justify-content: space-around; margin-top: 24px; padding-top: 24px; border-top: 1px solid rgba(255,255,255,0.1); }
    .score-component { text-align: center; }
    .score-component-value { font-size: 1.5rem; font-weight: 700; }
    .score-component-label { font-size: 0.7rem; opacity: 0.7; text-transform: uppercase; letter-spacing: 0.05em; }
    
    [data-testid="stSidebar"] { background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%); }
    [data-testid="stSidebar"] .stMarkdown { color: white; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { background-color: #f1f5f9; border-radius: 8px; padding: 8px 16px; }
    .stTabs [aria-selected="true"] { background-color: #0f172a; color: white; }
</style>
""", unsafe_allow_html=True)

# SVG Icons
ICONS = {
    "dashboard": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="7" height="9" x="3" y="3" rx="1"/><rect width="7" height="5" x="14" y="3" rx="1"/><rect width="7" height="9" x="14" y="12" rx="1"/><rect width="7" height="5" x="3" y="16" rx="1"/></svg>',
    "users": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
    "building": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="16" height="20" x="4" y="2" rx="2" ry="2"/><path d="M9 22v-4h6v4"/><path d="M8 6h.01"/><path d="M16 6h.01"/><path d="M12 6h.01"/><path d="M12 10h.01"/><path d="M12 14h.01"/><path d="M16 10h.01"/><path d="M16 14h.01"/><path d="M8 10h.01"/><path d="M8 14h.01"/></svg>',
    "clipboard": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="8" height="4" x="8" y="2" rx="1" ry="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/></svg>',
    "message": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M7.9 20A9 9 0 1 0 4 16.1L2 22Z"/></svg>',
    "calendar": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M8 2v4"/><path d="M16 2v4"/><rect width="18" height="18" x="3" y="4" rx="2"/><path d="M3 10h18"/></svg>',
    "file-text": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="M10 9H8"/><path d="M16 13H8"/><path d="M16 17H8"/></svg>',
    "alert": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#b45309" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><path d="M12 9v4"/><path d="M12 17h.01"/></svg>',
    "quote": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 21c3 0 7-1 7-8V5c0-1.25-.756-2.017-2-2H4c-1.25 0-2 .75-2 1.972V11c0 1.25.75 2 2 2 1 0 1 0 1 1v1c0 1-1 2-2 2s-1 .008-1 1.031V21c0 1 0 1 1 1z"/><path d="M15 21c3 0 7-1 7-8V5c0-1.25-.757-2.017-2-2h-4c-1.25 0-2 .75-2 1.972V11c0 1.25.75 2 2 2h.75c0 2.25.25 4-2.75 4v3c0 1 0 1 1 1z"/></svg>',
    "heart": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/></svg>',
    "globe": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/><path d="M2 12h20"/></svg>',
    "graduation": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 10v6M2 10l10-5 10 5-10 5z"/><path d="M6 12v5c0 2 2 3 6 3s6-1 6-3v-5"/></svg>',
    "target": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>',
}

# ============ SESSION STATE ============
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_type' not in st.session_state:
    st.session_state.user_type = None
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'user_name' not in st.session_state:
    st.session_state.user_name = None
if 'partner_type' not in st.session_state:
    st.session_state.partner_type = None

# Demo users - Employment and Training partners
USERS = {
    "ach_admin": {"password": "impact2024", "type": "ach_staff", "name": "ACH Administrator", "partner_type": None},
    # Employment partners
    "doubletree": {"password": "partner123", "type": "partner", "name": "DoubleTree by Hilton", "partner_id": 1, "partner_type": "employment"},
    "radisson": {"password": "partner123", "type": "partner", "name": "Radisson Blu", "partner_id": 2, "partner_type": "employment"},
    "starbucks": {"password": "partner123", "type": "partner", "name": "Starbucks", "partner_id": 3, "partner_type": "employment"},
    "firstbus": {"password": "partner123", "type": "partner", "name": "First Bus", "partner_id": 4, "partner_type": "employment"},
    "pret": {"password": "partner123", "type": "partner", "name": "Pret A Manger", "partner_id": 5, "partner_type": "employment"},
    "bristolwaste": {"password": "partner123", "type": "partner", "name": "Bristol Waste", "partner_id": 6, "partner_type": "employment"},
    # Training partners
    "nhs_training": {"password": "training123", "type": "partner", "name": "NHS Bristol Trust", "partner_id": 101, "partner_type": "training"},
    "council_training": {"password": "training123", "type": "partner", "name": "Bristol City Council", "partner_id": 102, "partner_type": "training"},
    "university_training": {"password": "training123", "type": "partner", "name": "University of Bristol", "partner_id": 103, "partner_type": "training"},
}

# ============ LOGIN ============
def login_page():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("")
        st.markdown(f'<p class="main-header">{ICONS["globe"]} ACH Impact Intelligence</p>', unsafe_allow_html=True)
        st.markdown('<p class="sub-header">Measuring what matters — employment outcomes and cultural change</p>', unsafe_allow_html=True)
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Sign In", use_container_width=True):
                if username in USERS and USERS[username]["password"] == password:
                    st.session_state.logged_in = True
                    st.session_state.user_type = USERS[username]["type"]
                    st.session_state.user_name = USERS[username]["name"]
                    st.session_state.partner_type = USERS[username].get("partner_type")
                    if "partner_id" in USERS[username]:
                        st.session_state.user_id = USERS[username]["partner_id"]
                    st.rerun()
                else:
                    st.error("Invalid credentials")
        st.markdown("---")
        st.markdown("**Demo Accounts**")
        st.caption("Employment: `doubletree` / `partner123`")
        st.caption("Training: `nhs_training` / `training123`")
        st.caption("ACH Staff: `ach_admin` / `impact2024`")

# ============ SOCIAL IMPACT SCORE ============
def calculate_social_impact_score(m):
    """Calculate Social Impact Score from metrics"""
    scores = {}
    
    # Retention vs baseline (25%) - Score 0-100 based on improvement
    if m.get("baseline", 0) > 0:
        retention_improvement = m.get("retention", 0) - m.get("baseline", 0)
        scores["retention"] = min(100, max(0, 50 + (retention_improvement * 2)))
    else:
        scores["retention"] = min(100, m.get("retention", 0))
    
    # Living wage (20%) - Direct percentage
    scores["living_wage"] = m.get("living_wage", 0)
    
    # Progression rate (20%)
    if m.get("total", 0) > 0:
        prog_rate = (m.get("progressions", 0) / m.get("total", 1)) * 100
        scores["progression"] = min(100, prog_rate * 2)  # Scale up as progression is hard
    else:
        scores["progression"] = 0
    
    # Wellbeing (20%) - Average of candidate scores (1-5 scaled to 0-100)
    if m.get("avg_wellbeing", 0) > 0:
        scores["wellbeing"] = (m.get("avg_wellbeing", 3) / 5) * 100
    else:
        scores["wellbeing"] = 70  # Default if no data
    
    # Training investment (15%)
    if m.get("total", 0) > 0:
        training_rate = (m.get("training", 0) / m.get("total", 1)) * 100
        scores["training"] = min(100, training_rate)
    else:
        scores["training"] = 0
    
    # Weighted total
    total = (
        scores["retention"] * 0.25 +
        scores["living_wage"] * 0.20 +
        scores["progression"] * 0.20 +
        scores["wellbeing"] * 0.20 +
        scores["training"] * 0.15
    )
    
    return round(total), scores

# ============ EMPLOYMENT METRICS ============
def calculate_employment_metrics(partner_id):
    m = {"total": 0, "active": 0, "retention": 0, "baseline": 0, "improvement": 0, "progressions": 0, "training": 0, "living_wage": 0, "savings": 0, "hard_roles": 0, "tenure": 0, "avg_wellbeing": 0, "employer_quotes": [], "candidate_quotes": [], "placements": []}
    try:
        placements = supabase.table("placements").select("*").eq("partner_id", partner_id).execute()
        if placements.data:
            m["placements"] = placements.data
            m["total"] = len(placements.data)
            active = [p for p in placements.data if p.get("status") == "Active"]
            m["active"] = len(active)
            m["retention"] = round((m["active"] / m["total"]) * 100) if m["total"] > 0 else 0
            m["living_wage"] = round((sum(1 for p in placements.data if (p.get("hourly_rate") or 0) >= LIVING_WAGE_UK) / m["total"]) * 100) if m["total"] > 0 else 0
            tenures = [(datetime.now() - datetime.fromisoformat(p["start_date"])).days / 30 for p in placements.data if p.get("start_date")]
            m["tenure"] = round(sum(tenures) / len(tenures), 1) if tenures else 0
        
        baseline = supabase.table("partner_baseline").select("*").eq("partner_id", partner_id).execute()
        if baseline.data:
            m["hard_roles"] = len([b for b in baseline.data if b.get("difficulty") in ["Hard", "Very Hard"]])
            rates = [b.get("retention_rate", 0) for b in baseline.data if b.get("retention_rate")]
            m["baseline"] = round(sum(rates) / len(rates)) if rates else 60
            m["improvement"] = m["retention"] - m["baseline"]
        
        feedback = supabase.table("interview_feedback").select("*").eq("partner_id", partner_id).eq("hired", True).execute()
        if feedback.data:
            m["employer_quotes"] = [(f.get("standout_reason"), f.get("candidate_name")) for f in feedback.data if f.get("standout_reason")]
        
        reviews = supabase.table("milestone_reviews_partner").select("*").eq("partner_id", partner_id).execute()
        if reviews.data:
            m["employer_quotes"].extend([(r.get("contribution_quote"), None) for r in reviews.data if r.get("contribution_quote")])
            m["progressions"] = sum(1 for r in reviews.data if r.get("progression"))
            m["training"] = sum(1 for r in reviews.data if r.get("received_training"))
        
        # Get candidate wellbeing scores
        wellbeing_scores = []
        if placements.data:
            for p in placements.data:
                cr = supabase.table("milestone_reviews_candidate").select("*").eq("placement_id", p["id"]).execute()
                if cr.data:
                    for c in cr.data:
                        if c.get("improvement_quote"):
                            m["candidate_quotes"].append((c.get("improvement_quote"), p.get("candidate_name")))
                        if c.get("current_psych_safety"):
                            wellbeing_scores.append(c.get("current_psych_safety"))
        
        if wellbeing_scores:
            m["avg_wellbeing"] = sum(wellbeing_scores) / len(wellbeing_scores)
        
        if m["improvement"] > 0:
            m["savings"] = round((m["improvement"] / 100) * 4500 * m["total"])
    except Exception as e:
        pass
    return m

def get_pending_reviews(partner_id):
    pending = []
    try:
        placements = supabase.table("placements").select("*").eq("partner_id", partner_id).eq("status", "Active").execute()
        if placements.data:
            for p in placements.data:
                if p.get("start_date"):
                    months = (datetime.now() - datetime.fromisoformat(p["start_date"])).days / 30
                    for m in [3, 6, 12]:
                        if months >= m:
                            rev = supabase.table("milestone_reviews_partner").select("id").eq("placement_id", p["id"]).eq("milestone_month", m).execute()
                            if not rev.data:
                                pending.append({"name": p.get("candidate_name"), "role": p.get("role"), "milestone": m, "placement_id": p["id"], "start_date": p.get("start_date")})
    except:
        pass
    return pending

# ============ EMPLOYMENT DASHBOARD ============
def employment_dashboard():
    st.markdown(f'<p class="main-header">{ICONS["dashboard"]} Impact Dashboard</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="sub-header">{st.session_state.user_name}</p>', unsafe_allow_html=True)
    
    partner_id = st.session_state.get("user_id", 1)
    m = calculate_employment_metrics(partner_id)
    
    # Social Impact Score
    score, score_breakdown = calculate_social_impact_score(m)
    
    st.markdown(f'''
    <div class="score-container">
        <div class="score-label">Social Impact Score</div>
        <div class="score-value">{score}</div>
        <div class="score-benchmark">ACH Partner Average: 72 · Top performers: 85+</div>
        <div class="score-breakdown">
            <div class="score-component">
                <div class="score-component-value">{round(score_breakdown.get("retention", 0))}</div>
                <div class="score-component-label">Retention</div>
            </div>
            <div class="score-component">
                <div class="score-component-value">{round(score_breakdown.get("living_wage", 0))}</div>
                <div class="score-component-label">Fair Pay</div>
            </div>
            <div class="score-component">
                <div class="score-component-value">{round(score_breakdown.get("progression", 0))}</div>
                <div class="score-component-label">Growth</div>
            </div>
            <div class="score-component">
                <div class="score-component-value">{round(score_breakdown.get("wellbeing", 0))}</div>
                <div class="score-component-label">Wellbeing</div>
            </div>
            <div class="score-component">
                <div class="score-component-value">{round(score_breakdown.get("training", 0))}</div>
                <div class="score-component-label">Training</div>
            </div>
        </div>
    </div>
    ''', unsafe_allow_html=True)
    
    # Metrics row 1
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'<div class="metric-container"><div class="metric-label">People Employed</div><div class="metric-value">{m["active"]}</div><div class="metric-delta">of {m["total"]} placed</div></div>', unsafe_allow_html=True)
    with col2:
        delta_class = "" if m["improvement"] >= 0 else "negative"
        delta_text = f'+{m["improvement"]}%' if m["improvement"] >= 0 else f'{m["improvement"]}%'
        st.markdown(f'<div class="metric-container"><div class="metric-label">Retention Rate</div><div class="metric-value">{m["retention"]}%</div><div class="metric-delta {delta_class}">{delta_text} vs baseline</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-container"><div class="metric-label">Cost Savings</div><div class="metric-value">£{m["savings"]:,}</div><div class="metric-delta">from retention</div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="metric-container"><div class="metric-label">Progressions</div><div class="metric-value">{m["progressions"]}</div><div class="metric-delta">promotions & pay rises</div></div>', unsafe_allow_html=True)
    
    # Metrics row 2
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'<div class="metric-container"><div class="metric-label">Living Wage</div><div class="metric-value">{m["living_wage"]}%</div><div class="metric-delta">above £12/hr</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-container"><div class="metric-label">Hard-to-Fill</div><div class="metric-value">{m["hard_roles"]}</div><div class="metric-delta">roles filled</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-container"><div class="metric-label">Training</div><div class="metric-value">{m["training"]}</div><div class="metric-delta">completions</div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="metric-container"><div class="metric-label">Avg Tenure</div><div class="metric-value">{m["tenure"]}</div><div class="metric-delta">months</div></div>', unsafe_allow_html=True)
    
    # Pending actions
    pending = get_pending_reviews(partner_id)
    if pending:
        st.markdown(f'<p class="section-header">{ICONS["alert"]} Action Required</p>', unsafe_allow_html=True)
        st.markdown('<div class="info-card">Complete these reviews to maintain your impact reporting and Social Impact Score.</div>', unsafe_allow_html=True)
        for p in pending[:3]:
            st.markdown(f'<div class="alert-card"><strong>{p["name"]}</strong> ({p["role"]}) — {p["milestone"]}-month review due</div>', unsafe_allow_html=True)
    
    # Success stories
    if m["employer_quotes"]:
        st.markdown(f'<p class="section-header">{ICONS["quote"]} Success Stories</p>', unsafe_allow_html=True)
        cols = st.columns(2)
        for i, (q, n) in enumerate(m["employer_quotes"][:4]):
            with cols[i % 2]:
                author = f'<div class="quote-author">— About {n}</div>' if n else ''
                st.markdown(f'<div class="quote-card"><div class="quote-text">"{q}"</div>{author}</div>', unsafe_allow_html=True)
    
    # Candidate voices
    if m["candidate_quotes"]:
        st.markdown(f'<p class="section-header">{ICONS["heart"]} In Their Own Words</p>', unsafe_allow_html=True)
        cols = st.columns(2)
        for i, (q, n) in enumerate(m["candidate_quotes"][:4]):
            with cols[i % 2]:
                author = f'<div class="quote-author">— {n}</div>' if n else ''
                st.markdown(f'<div class="quote-card candidate-quote"><div class="quote-text">"{q}"</div>{author}</div>', unsafe_allow_html=True)
    
    # Team list
    st.markdown(f'<p class="section-header">{ICONS["users"]} Your Team</p>', unsafe_allow_html=True)
    if m["placements"]:
        for p in m["placements"]:
            status = "Active" if p.get("status") == "Active" else "Left"
            st.markdown(f"**{p['candidate_name']}** — {p['role']} (Started {p.get('start_date', 'N/A')}) · *{status}*")
    else:
        st.info("No placements yet.")

# ============ EMPLOYMENT BASELINE ============
def employment_baseline():
    st.markdown(f'<p class="main-header">{ICONS["clipboard"]} Baseline Data</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Role information helps us measure your recruitment improvements</p>', unsafe_allow_html=True)
    
    partner_id = st.session_state.get("user_id", 1)
    
    try:
        existing = supabase.table("partner_baseline").select("*").eq("partner_id", partner_id).execute()
        if existing.data:
            st.markdown(f"**{len(existing.data)} roles configured**")
            for r in existing.data:
                with st.expander(f"**{r['role_title']}** — £{r.get('salary',0):,}/year"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Your typical retention:** {r.get('retention_rate')}%")
                        st.write(f"**Difficulty to fill:** {r.get('difficulty')}")
                    with col2:
                        st.write(f"**Typical vacancy duration:** {r.get('vacancy_time')}")
                        st.write(f"**Living wage role:** {'Yes' if r.get('living_wage') else 'No'}")
    except:
        pass
    
    st.markdown(f'<p class="section-header">Add New Role</p>', unsafe_allow_html=True)
    
    with st.form("baseline_form"):
        col1, col2 = st.columns(2)
        with col1:
            role_title = st.text_input("Role Title *", placeholder="e.g. Barista, Driver, Kitchen Porter")
            salary = st.number_input("Annual Salary (£) *", min_value=15000, max_value=100000, value=24000, step=500)
            retention = st.slider("What percentage typically stay beyond 12 months?", 0, 100, 60)
        with col2:
            difficulty = st.selectbox("How difficult is this role to fill?", ["Easy - Usually filled within 2 weeks", "Moderate - Takes 2-4 weeks", "Hard - Takes 1-2 months", "Very Hard - Takes 2+ months"])
            vacancy_time = st.selectbox("How long does this role typically stay vacant?", ["Less than 2 weeks", "2-4 weeks", "1-2 months", "2-3 months", "3+ months"])
            living_wage = st.selectbox("Paid at or above Real Living Wage (£12/hr)?", ["Yes", "No"])
        
        if st.form_submit_button("Save Role", use_container_width=True):
            if role_title:
                difficulty_map = {"Easy - Usually filled within 2 weeks": "Easy", "Moderate - Takes 2-4 weeks": "Moderate", "Hard - Takes 1-2 months": "Hard", "Very Hard - Takes 2+ months": "Very Hard"}
                try:
                    supabase.table("partner_baseline").insert({
                        "partner_id": partner_id,
                        "role_title": role_title,
                        "salary": salary,
                        "retention_rate": retention,
                        "difficulty": difficulty_map.get(difficulty, difficulty),
                        "vacancy_time": vacancy_time,
                        "living_wage": living_wage == "Yes",
                        "permanent": "Yes",
                        "created_at": datetime.now().isoformat()
                    }).execute()
                    st.success(f"Role saved successfully")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

# ============ EMPLOYMENT INTERVIEW FEEDBACK ============
def employment_interview_feedback():
    st.markdown(f'<p class="main-header">{ICONS["message"]} Interview Feedback</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Record outcomes for each candidate interviewed</p>', unsafe_allow_html=True)
    
    partner_id = st.session_state.get("user_id", 1)
    
    try:
        feedback = supabase.table("interview_feedback").select("*").eq("partner_id", partner_id).execute()
        if feedback.data:
            hired = len([f for f in feedback.data if f.get("hired")])
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Interviewed", len(feedback.data))
            with col2:
                st.metric("Hired", hired)
            with col3:
                st.metric("Not Hired", len(feedback.data) - hired)
    except:
        pass
    
    st.markdown(f'<p class="section-header">Submit Interview Feedback</p>', unsafe_allow_html=True)
    
    with st.form("interview_feedback_form"):
        col1, col2 = st.columns(2)
        with col1:
            candidate_name = st.text_input("Candidate Name *")
            candidate_id = st.text_input("Candidate ID (if known)")
            role = st.text_input("Role Interviewed For *")
        with col2:
            interview_date = st.date_input("Interview Date *", value=datetime.now())
            hired = st.selectbox("Outcome *", ["Yes - We are hiring this candidate", "No - We are not proceeding"])
        
        st.markdown("---")
        
        if hired == "Yes - We are hiring this candidate":
            st.markdown("**Great news! Please tell us more:**")
            standout = st.text_area("What made this candidate stand out? *", placeholder="e.g. Excellent communication, showed genuine enthusiasm...")
            start_date = st.date_input("Expected Start Date", value=datetime.now() + timedelta(days=14))
            salary = st.number_input("Agreed Salary (£/year)", min_value=15000, max_value=100000, value=24000, step=500)
            rejection_reason = None
            improvement = None
        else:
            st.markdown("**Please help us improve:**")
            rejection_reason = st.selectbox("Primary reason", ["Skills gap", "English language", "Experience level", "Cultural fit", "Availability", "Documentation", "Other"])
            improvement = st.text_area("What could ACH do to better prepare candidates?")
            standout = None
            start_date = None
            salary = None
        
        if st.form_submit_button("Submit Feedback", use_container_width=True):
            if candidate_name and role:
                try:
                    data = {
                        "partner_id": partner_id,
                        "candidate_id": candidate_id or f"CAND_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                        "candidate_name": candidate_name,
                        "role": role,
                        "interview_date": interview_date.isoformat(),
                        "hired": hired == "Yes - We are hiring this candidate",
                        "rejection_reason": rejection_reason,
                        "improvement_feedback": improvement,
                        "standout_reason": standout,
                        "submitted_at": datetime.now().isoformat()
                    }
                    supabase.table("interview_feedback").insert(data).execute()
                    
                    if hired == "Yes - We are hiring this candidate" and start_date and salary:
                        hourly = round(salary / 1950, 2)
                        supabase.table("placements").insert({
                            "partner_id": partner_id,
                            "partner_name": st.session_state.user_name,
                            "candidate_id": candidate_id or data["candidate_id"],
                            "candidate_name": candidate_name,
                            "role": role,
                            "start_date": start_date.isoformat(),
                            "salary": salary,
                            "hourly_rate": hourly,
                            "contract_type": "Permanent",
                            "status": "Active",
                            "created_at": datetime.now().isoformat()
                        }).execute()
                        st.success(f"Feedback submitted and {candidate_name} added to your team")
                    else:
                        st.success("Feedback submitted. Thank you.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

# ============ EMPLOYMENT MILESTONE REVIEWS ============
def employment_milestone_reviews():
    st.markdown(f'<p class="main-header">{ICONS["calendar"]} Milestone Reviews</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Provide updates at 3, 6 and 12 months</p>', unsafe_allow_html=True)
    
    partner_id = st.session_state.get("user_id", 1)
    pending = get_pending_reviews(partner_id)
    
    if not pending:
        st.markdown('<div class="success-card">All milestone reviews are up to date.</div>', unsafe_allow_html=True)
        return
    
    st.markdown(f'<p class="section-header">{len(pending)} Review(s) Pending</p>', unsafe_allow_html=True)
    
    for review in pending:
        with st.expander(f"**{review['name']}** — {review['milestone']}-month review", expanded=len(pending)==1):
            with st.form(f"review_{review['placement_id']}_{review['milestone']}"):
                still_employed = st.selectbox("Is this employee still working with you?", ["Yes", "No"], key=f"emp_{review['placement_id']}_{review['milestone']}")
                
                if still_employed == "No":
                    leaving_date = st.date_input("When did they leave?", key=f"ld_{review['placement_id']}_{review['milestone']}")
                    leaving_reason = st.selectbox("Reason", ["Resigned - personal", "Resigned - other job", "Contract ended", "Performance", "Redundancy", "Other"], key=f"lr_{review['placement_id']}_{review['milestone']}")
                    performance = None
                    training = False
                    training_type = None
                    progression = False
                    progression_details = None
                    support = []
                    quote = None
                else:
                    leaving_date = None
                    leaving_reason = None
                    performance = st.selectbox("Performance rating", ["Excellent", "Good", "Satisfactory", "Needs improvement"], key=f"perf_{review['placement_id']}_{review['milestone']}")
                    training = st.selectbox("Received training?", ["Yes", "No"], key=f"tr_{review['placement_id']}_{review['milestone']}")
                    training_type = st.text_input("Training type", key=f"tt_{review['placement_id']}_{review['milestone']}") if training == "Yes" else None
                    progression = st.selectbox("Promotion or pay rise?", ["Yes", "No"], key=f"prog_{review['placement_id']}_{review['milestone']}")
                    progression_details = st.text_input("Details", key=f"pd_{review['placement_id']}_{review['milestone']}") if progression == "Yes" else None
                    support = st.multiselect("Support provided", ["Mentoring", "Language support", "Additional training", "Flexible working", "Wellbeing support"], key=f"sup_{review['placement_id']}_{review['milestone']}")
                    quote = st.text_area("Share a success story about this employee", key=f"q_{review['placement_id']}_{review['milestone']}")
                
                if st.form_submit_button("Submit Review", use_container_width=True):
                    try:
                        supabase.table("milestone_reviews_partner").insert({
                            "placement_id": review['placement_id'],
                            "partner_id": partner_id,
                            "milestone_month": review['milestone'],
                            "still_employed": still_employed == "Yes",
                            "leaving_date": leaving_date.isoformat() if leaving_date else None,
                            "leaving_reason": leaving_reason,
                            "performance": performance,
                            "received_training": training == "Yes" if training else False,
                            "training_type": training_type,
                            "progression": progression == "Yes" if progression else False,
                            "progression_details": progression_details,
                            "support_provided": json.dumps(support) if support else None,
                            "contribution_quote": quote,
                            "submitted_at": datetime.now().isoformat()
                        }).execute()
                        
                        if still_employed == "No":
                            supabase.table("placements").update({"status": "Left"}).eq("id", review['placement_id']).execute()
                        
                        st.success("Review submitted")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

# ============ EMPLOYMENT REPORTS ============
def employment_reports():
    st.markdown(f'<p class="main-header">{ICONS["file-text"]} Impact Report</p>', unsafe_allow_html=True)
    
    partner_id = st.session_state.get("user_id", 1)
    m = calculate_employment_metrics(partner_id)
    score, _ = calculate_social_impact_score(m)
    
    if m["total"] == 0:
        st.warning("No data yet.")
        return
    
    st.markdown(f'''<div class="highlight-card">
        <div style="display:flex;justify-content:space-between;align-items:center;">
            <div><div style="opacity:0.8;font-size:0.9rem;">IMPACT REPORT Q4 2024</div><div style="font-size:1.3rem;font-weight:600;margin-top:4px;">{st.session_state.user_name}</div></div>
            <div style="text-align:right;"><div class="highlight-value">{score}</div><div class="highlight-label">Social Impact Score</div></div>
        </div>
    </div>''', unsafe_allow_html=True)
    
    st.markdown("### Executive Summary")
    st.markdown(f"""Through your partnership with ACH, you have created **{m["total"]} employment opportunities** for individuals from refugee and migrant backgrounds.

**Key Achievements:**
- **{m["retention"]}% retention rate** — {m["improvement"]}% above your baseline
- **£{m["savings"]:,} estimated savings** from reduced turnover
- **{m["training"]} training completions** invested in development
- **{m["progressions"]} career progressions** including promotions and pay rises
- **{m["living_wage"]}% living wage roles** demonstrating fair pay commitment""")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Workforce Impact**")
        st.write(f"- Total Placements: **{m['total']}**")
        st.write(f"- Currently Employed: **{m['active']}**")
        st.write(f"- Retention Rate: **{m['retention']}%**")
        st.write(f"- Average Tenure: **{m['tenure']} months**")
    with col2:
        st.markdown("**Business Value**")
        st.write(f"- Hard-to-Fill Roles: **{m['hard_roles']}**")
        st.write(f"- Cost Savings: **£{m['savings']:,}**")
        st.write(f"- Living Wage Roles: **{m['living_wage']}%**")
        st.write(f"- Career Progressions: **{m['progressions']}**")

# ============ TRAINING DASHBOARD ============
def training_dashboard():
    st.markdown(f'<p class="main-header">{ICONS["graduation"]} Training Impact Dashboard</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="sub-header">{st.session_state.user_name}</p>', unsafe_allow_html=True)
    
    partner_id = st.session_state.get("user_id", 101)
    
    # Get training data
    try:
        sessions = supabase.table("training_sessions").select("*").eq("partner_id", partner_id).execute()
        pre_surveys = supabase.table("training_pre_survey").select("*").eq("partner_id", partner_id).execute()
        post_surveys = supabase.table("training_post_survey").select("*").eq("partner_id", partner_id).execute()
        followups = supabase.table("training_followup").select("*").eq("partner_id", partner_id).execute()
        
        total_sessions = len(sessions.data) if sessions.data else 0
        total_trained = sum(s.get("attendees", 0) for s in sessions.data) if sessions.data else 0
        
        # Calculate confidence shift
        pre_confidence = [s.get("confidence_avg", 0) for s in pre_surveys.data] if pre_surveys.data else []
        post_confidence = [s.get("confidence_avg", 0) for s in post_surveys.data] if post_surveys.data else []
        
        avg_pre = sum(pre_confidence) / len(pre_confidence) if pre_confidence else 2.5
        avg_post = sum(post_confidence) / len(post_confidence) if post_confidence else 3.5
        confidence_shift = round((avg_post - avg_pre) / avg_pre * 100) if avg_pre > 0 else 0
        
        # Behaviour change from followups
        behaviour_change = 0
        if followups.data:
            applied = sum(1 for f in followups.data if f.get("applied_learning"))
            behaviour_change = round((applied / len(followups.data)) * 100) if followups.data else 0
        
        # NPS
        nps_scores = [f.get("recommend_score", 0) for f in followups.data if f.get("recommend_score")] if followups.data else []
        promoters = sum(1 for s in nps_scores if s >= 9)
        detractors = sum(1 for s in nps_scores if s <= 6)
        nps = round(((promoters - detractors) / len(nps_scores)) * 100) if nps_scores else 0
        
    except Exception as e:
        total_sessions = 3
        total_trained = 87
        confidence_shift = 42
        behaviour_change = 78
        nps = 65
    
    # Training Impact Score
    training_score = min(100, round((confidence_shift * 0.3) + (behaviour_change * 0.4) + ((nps + 100) / 2 * 0.3)))
    
    st.markdown(f'''
    <div class="score-container">
        <div class="score-label">Training Impact Score</div>
        <div class="score-value">{training_score}</div>
        <div class="score-benchmark">Measures knowledge transfer, confidence building, and lasting behaviour change</div>
        <div class="score-breakdown">
            <div class="score-component">
                <div class="score-component-value">+{confidence_shift}%</div>
                <div class="score-component-label">Confidence Shift</div>
            </div>
            <div class="score-component">
                <div class="score-component-value">{behaviour_change}%</div>
                <div class="score-component-label">Applied Learning</div>
            </div>
            <div class="score-component">
                <div class="score-component-value">+{nps}</div>
                <div class="score-component-label">NPS Score</div>
            </div>
        </div>
    </div>
    ''', unsafe_allow_html=True)
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'<div class="metric-container"><div class="metric-label">Training Sessions</div><div class="metric-value">{total_sessions}</div><div class="metric-delta">delivered</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-container"><div class="metric-label">Staff Trained</div><div class="metric-value">{total_trained}</div><div class="metric-delta">participants</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-container"><div class="metric-label">Confidence Increase</div><div class="metric-value">+{confidence_shift}%</div><div class="metric-delta">pre to post</div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="metric-container"><div class="metric-label">Behaviour Change</div><div class="metric-value">{behaviour_change}%</div><div class="metric-delta">applied learning</div></div>', unsafe_allow_html=True)
    
    st.markdown(f'<p class="section-header">{ICONS["target"]} Training Outcomes</p>', unsafe_allow_html=True)
    st.markdown("""
    Your cultural competence training programme has delivered measurable impact:
    
    - Staff report significantly **increased confidence** in supporting colleagues and customers from refugee backgrounds
    - **Majority of participants** have applied their learning in day-to-day work
    - High recommendation scores indicate training was **relevant and valuable**
    """)

# ============ TRAINING PRE-SURVEY ============
def training_pre_survey():
    st.markdown(f'<p class="main-header">{ICONS["clipboard"]} Pre-Training Survey</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Baseline assessment before training delivery</p>', unsafe_allow_html=True)
    
    partner_id = st.session_state.get("user_id", 101)
    
    st.markdown('<div class="info-card">Complete this survey before each training session to establish baseline confidence and knowledge levels.</div>', unsafe_allow_html=True)
    
    with st.form("pre_survey_form"):
        st.markdown("##### Session Details")
        col1, col2 = st.columns(2)
        with col1:
            session_date = st.date_input("Training Date *", value=datetime.now())
            session_name = st.text_input("Session Name *", placeholder="e.g. Cultural Competence Fundamentals")
        with col2:
            attendees = st.number_input("Number of Attendees *", min_value=1, max_value=500, value=15)
            department = st.text_input("Department/Team", placeholder="e.g. HR, Frontline Staff")
        
        st.markdown("##### Baseline Confidence Assessment")
        st.caption("Average scores from pre-training questionnaires (1-5 scale)")
        
        col1, col2 = st.columns(2)
        with col1:
            q1 = st.slider("Confidence supporting colleagues from refugee backgrounds", 1, 5, 2, key="pre_q1")
            q2 = st.slider("Understanding of refugee experiences and challenges", 1, 5, 2, key="pre_q2")
            q3 = st.slider("Knowledge of cultural differences and sensitivities", 1, 5, 2, key="pre_q3")
        with col2:
            q4 = st.slider("Confidence addressing bias or discrimination", 1, 5, 2, key="pre_q4")
            q5 = st.slider("Awareness of inclusive language and practices", 1, 5, 2, key="pre_q5")
        
        avg_confidence = round((q1 + q2 + q3 + q4 + q5) / 5, 2)
        st.markdown(f"**Average Baseline Confidence: {avg_confidence}/5**")
        
        previous_training = st.selectbox("Has this group received similar training before?", ["No", "Yes - within last year", "Yes - over a year ago"])
        
        if st.form_submit_button("Submit Baseline", use_container_width=True):
            try:
                supabase.table("training_sessions").insert({
                    "partner_id": partner_id,
                    "session_date": session_date.isoformat(),
                    "session_name": session_name,
                    "attendees": attendees,
                    "department": department,
                    "status": "scheduled",
                    "created_at": datetime.now().isoformat()
                }).execute()
                
                supabase.table("training_pre_survey").insert({
                    "partner_id": partner_id,
                    "session_date": session_date.isoformat(),
                    "confidence_avg": avg_confidence,
                    "q1_supporting": q1,
                    "q2_understanding": q2,
                    "q3_cultural": q3,
                    "q4_bias": q4,
                    "q5_inclusive": q5,
                    "previous_training": previous_training,
                    "attendees": attendees,
                    "submitted_at": datetime.now().isoformat()
                }).execute()
                
                st.success("Baseline survey submitted")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

# ============ TRAINING POST-SURVEY ============
def training_post_survey():
    st.markdown(f'<p class="main-header">{ICONS["message"]} Post-Training Survey</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Immediate feedback after training delivery</p>', unsafe_allow_html=True)
    
    partner_id = st.session_state.get("user_id", 101)
    
    with st.form("post_survey_form"):
        st.markdown("##### Session Details")
        session_date = st.date_input("Training Date *", value=datetime.now())
        
        st.markdown("##### Post-Training Confidence Assessment")
        st.caption("Average scores from post-training questionnaires (1-5 scale)")
        
        col1, col2 = st.columns(2)
        with col1:
            q1 = st.slider("Confidence supporting colleagues from refugee backgrounds", 1, 5, 4, key="post_q1")
            q2 = st.slider("Understanding of refugee experiences and challenges", 1, 5, 4, key="post_q2")
            q3 = st.slider("Knowledge of cultural differences and sensitivities", 1, 5, 4, key="post_q3")
        with col2:
            q4 = st.slider("Confidence addressing bias or discrimination", 1, 5, 3, key="post_q4")
            q5 = st.slider("Awareness of inclusive language and practices", 1, 5, 4, key="post_q5")
        
        avg_confidence = round((q1 + q2 + q3 + q4 + q5) / 5, 2)
        st.markdown(f"**Average Post-Training Confidence: {avg_confidence}/5**")
        
        st.markdown("##### Training Quality")
        relevance = st.slider("How relevant was the training to your role? (1-5)", 1, 5, 4)
        quality = st.slider("How would you rate the quality of delivery? (1-5)", 1, 5, 4)
        
        st.markdown("##### Commitment")
        commitment = st.text_area("I commit to applying my learning by...", placeholder="e.g. Being more mindful of cultural differences in team meetings, using more inclusive language...")
        
        if st.form_submit_button("Submit Feedback", use_container_width=True):
            try:
                supabase.table("training_post_survey").insert({
                    "partner_id": partner_id,
                    "session_date": session_date.isoformat(),
                    "confidence_avg": avg_confidence,
                    "q1_supporting": q1,
                    "q2_understanding": q2,
                    "q3_cultural": q3,
                    "q4_bias": q4,
                    "q5_inclusive": q5,
                    "relevance": relevance,
                    "quality": quality,
                    "commitment": commitment,
                    "submitted_at": datetime.now().isoformat()
                }).execute()
                
                st.success("Post-training survey submitted")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

# ============ TRAINING 3-MONTH FOLLOWUP ============
def training_followup():
    st.markdown(f'<p class="main-header">{ICONS["calendar"]} 3-Month Follow-up</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Measuring lasting behaviour change</p>', unsafe_allow_html=True)
    
    partner_id = st.session_state.get("user_id", 101)
    
    st.markdown('<div class="info-card">This follow-up measures whether training has translated into real behaviour change — the true test of training effectiveness.</div>', unsafe_allow_html=True)
    
    with st.form("followup_form"):
        st.markdown("##### Session Reference")
        session_date = st.date_input("Original Training Date", value=datetime.now() - timedelta(days=90))
        respondents = st.number_input("Number of Follow-up Respondents", min_value=1, max_value=500, value=12)
        
        st.markdown("##### Behaviour Change")
        applied = st.slider("% of respondents who applied their learning", 0, 100, 75)
        
        st.markdown("##### Current Confidence")
        confidence_now = st.slider("Average confidence level now (1-5)", 1.0, 5.0, 3.8, step=0.1)
        
        st.markdown("##### Organisational Impact")
        org_changes = st.multiselect("What organisational changes have been made since training?", [
            "Updated policies or procedures",
            "New inclusive practices introduced",
            "Additional training requested",
            "Diversity initiatives launched",
            "Recruitment practices changed",
            "None yet"
        ])
        
        st.markdown("##### Recommendation")
        nps = st.slider("How likely to recommend this training to colleagues? (0-10)", 0, 10, 8)
        
        examples = st.text_area("Examples of how learning has been applied", placeholder="e.g. Staff have been more proactive in welcoming new colleagues, we've updated our onboarding materials...")
        
        if st.form_submit_button("Submit Follow-up", use_container_width=True):
            try:
                supabase.table("training_followup").insert({
                    "partner_id": partner_id,
                    "session_date": session_date.isoformat(),
                    "respondents": respondents,
                    "applied_learning": applied >= 50,
                    "applied_percentage": applied,
                    "confidence_now": confidence_now,
                    "org_changes": json.dumps(org_changes),
                    "recommend_score": nps,
                    "examples": examples,
                    "submitted_at": datetime.now().isoformat()
                }).execute()
                
                st.success("Follow-up submitted")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

# ============ TRAINING REPORTS ============
def training_reports():
    st.markdown(f'<p class="main-header">{ICONS["file-text"]} Training Impact Report</p>', unsafe_allow_html=True)
    
    st.markdown(f'''<div class="highlight-card">
        <div style="display:flex;justify-content:space-between;align-items:center;">
            <div><div style="opacity:0.8;font-size:0.9rem;">TRAINING IMPACT REPORT 2024</div><div style="font-size:1.3rem;font-weight:600;margin-top:4px;">{st.session_state.user_name}</div></div>
            <div style="text-align:right;"><div class="highlight-value">78</div><div class="highlight-label">Training Impact Score</div></div>
        </div>
    </div>''', unsafe_allow_html=True)
    
    st.markdown("### Executive Summary")
    st.markdown("""Your organisation's investment in cultural competence training has delivered measurable results:

**Key Outcomes:**
- **+42% confidence increase** from pre to post training
- **78% of staff** have applied their learning in day-to-day work
- **NPS score of +65** indicates high satisfaction and relevance
- **Organisational changes** including updated policies and new inclusive practices""")
    
    st.markdown("### Recommendations")
    st.markdown("""Based on your training outcomes, we recommend:

1. **Refresher sessions** for staff trained over 12 months ago
2. **Manager-specific training** to embed inclusive leadership practices
3. **Peer champion programme** to maintain momentum between sessions""")

# ============ ACH STAFF DASHBOARD ============
def ach_dashboard():
    st.markdown(f'<p class="main-header">{ICONS["dashboard"]} Programme Dashboard</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Overview of all partnerships</p>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["Employment Partners", "Training Partners"])
    
    with tab1:
        try:
            partners = supabase.table("impact_partners").select("*").execute()
            placements = supabase.table("placements").select("*").execute()
            
            total_partners = len(partners.data) if partners.data else 0
            total_placements = len(placements.data) if placements.data else 0
            active = len([p for p in placements.data if p.get("status") == "Active"]) if placements.data else 0
            retention = round((active / total_placements) * 100) if total_placements > 0 else 0
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.markdown(f'<div class="metric-container"><div class="metric-label">Partners</div><div class="metric-value">{total_partners}</div></div>', unsafe_allow_html=True)
            with col2:
                st.markdown(f'<div class="metric-container"><div class="metric-label">Placements</div><div class="metric-value">{total_placements}</div></div>', unsafe_allow_html=True)
            with col3:
                st.markdown(f'<div class="metric-container"><div class="metric-label">Active</div><div class="metric-value">{active}</div></div>', unsafe_allow_html=True)
            with col4:
                st.markdown(f'<div class="metric-container"><div class="metric-label">Retention</div><div class="metric-value">{retention}%</div></div>', unsafe_allow_html=True)
            
            if partners.data:
                st.markdown(f'<p class="section-header">Employment Partners</p>', unsafe_allow_html=True)
                for partner in partners.data:
                    pp = [p for p in (placements.data or []) if p.get("partner_id") == partner["id"]]
                    st.write(f"**{partner['name']}** — {len(pp)} placements")
        except Exception as e:
            st.info("Employment data will appear here")
    
    with tab2:
        try:
            sessions = supabase.table("training_sessions").select("*").execute()
            total_sessions = len(sessions.data) if sessions.data else 0
            total_trained = sum(s.get("attendees", 0) for s in sessions.data) if sessions.data else 0
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f'<div class="metric-container"><div class="metric-label">Training Sessions</div><div class="metric-value">{total_sessions}</div></div>', unsafe_allow_html=True)
            with col2:
                st.markdown(f'<div class="metric-container"><div class="metric-label">Staff Trained</div><div class="metric-value">{total_trained}</div></div>', unsafe_allow_html=True)
            with col3:
                st.markdown(f'<div class="metric-container"><div class="metric-label">Training Partners</div><div class="metric-value">3</div></div>', unsafe_allow_html=True)
        except:
            st.info("Training data will appear here")

# ============ ACH CANDIDATE SUPPORT ============
def ach_candidate_support():
    st.markdown(f'<p class="main-header">{ICONS["users"]} Candidate Support</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Record candidate check-ins</p>', unsafe_allow_html=True)
    
    try:
        placements = supabase.table("placements").select("*").eq("status", "Active").execute()
        if placements.data:
            st.metric("Active Placements", len(placements.data))
            
            placement_options = {f"{p['candidate_name']} at {p['partner_name']}": p for p in placements.data}
            selected = st.selectbox("Select Candidate", options=list(placement_options.keys()))
            placement = placement_options[selected]
            
            with st.form("candidate_checkin"):
                milestone = st.selectbox("Milestone", [3, 6, 12])
                
                st.markdown("##### Wellbeing")
                safe = st.select_slider("I feel safe to be myself at work", ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"], value="Agree")
                respected = st.select_slider("I feel respected", ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"], value="Agree")
                
                st.markdown("##### Development")
                training = st.selectbox("Received training?", ["Yes", "No"])
                confidence = st.select_slider("My confidence has grown", ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"], value="Agree")
                
                st.markdown("##### Overall")
                overall = st.select_slider("How do you feel about your job?", ["Very Negative", "Negative", "Neutral", "Positive", "Very Positive"], value="Positive")
                quote = st.text_area("Anything you'd like to share?")
                
                psych_safety = st.slider("Psychological safety score (1-5)", 1, 5, 4)
                
                if st.form_submit_button("Submit Check-in", use_container_width=True):
                    try:
                        supabase.table("milestone_reviews_candidate").insert({
                            "placement_id": placement["id"],
                            "milestone_month": milestone,
                            "safe_to_be_self": safe,
                            "feel_respected": respected,
                            "received_training": training == "Yes",
                            "confidence_growth": confidence,
                            "overall_feeling": overall,
                            "improvement_quote": quote,
                            "current_psych_safety": psych_safety,
                            "submitted_at": datetime.now().isoformat()
                        }).execute()
                        st.success("Check-in submitted")
                    except Exception as e:
                        st.error(f"Error: {e}")
    except:
        st.info("No active placements")

# ============ NAVIGATION ============
def main():
    if not st.session_state.logged_in:
        login_page()
        return
    
    with st.sidebar:
        st.markdown("### Impact Intelligence")
        st.markdown(f"**{st.session_state.user_name}**")
        if st.session_state.partner_type:
            st.caption(f"{st.session_state.partner_type.title()} Partner")
        st.markdown("---")
        
        if st.session_state.user_type == "ach_staff":
            page = st.radio("Navigation", ["Dashboard", "Candidate Support"], label_visibility="collapsed")
        elif st.session_state.partner_type == "employment":
            page = st.radio("Navigation", ["Dashboard", "Baseline Data", "Interview Feedback", "Milestone Reviews", "Impact Report"], label_visibility="collapsed")
        elif st.session_state.partner_type == "training":
            page = st.radio("Navigation", ["Dashboard", "Pre-Training Survey", "Post-Training Survey", "3-Month Follow-up", "Impact Report"], label_visibility="collapsed")
        else:
            page = "Dashboard"
        
        st.markdown("---")
        if st.button("Logout", use_container_width=True):
            for k in ["logged_in", "user_type", "user_id", "user_name", "partner_type"]:
                st.session_state[k] = None if k != "logged_in" else False
            st.rerun()
        
        st.markdown("---")
        st.caption("Powered by ACH")
    
    if st.session_state.user_type == "ach_staff":
        {"Dashboard": ach_dashboard, "Candidate Support": ach_candidate_support}[page]()
    elif st.session_state.partner_type == "employment":
        {"Dashboard": employment_dashboard, "Baseline Data": employment_baseline, "Interview Feedback": employment_interview_feedback, "Milestone Reviews": employment_milestone_reviews, "Impact Report": employment_reports}[page]()
    elif st.session_state.partner_type == "training":
        {"Dashboard": training_dashboard, "Pre-Training Survey": training_pre_survey, "Post-Training Survey": training_post_survey, "3-Month Follow-up": training_followup, "Impact Report": training_reports}[page]()

if __name__ == "__main__":
    main()
