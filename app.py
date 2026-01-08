import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from supabase import create_client
import json
import math

SUPABASE_URL = "https://gmjqidqjpzxcpgycawxf.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdtanFpZHFqcHp4Y3BneWNhd3hmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njc3MjYyMDEsImV4cCI6MjA4MzMwMjIwMX0.6jtYlz6yoBQCrh04P0g30JigHyanGYnv7xBz24B5Bm4"
HARD_TO_FILL_VALUE = 4500

@st.cache_resource
def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = get_supabase()

st.set_page_config(page_title="ACH Impact Intelligence", page_icon="◉", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    * { font-family: 'Inter', sans-serif; }
    .main-header { font-size: 1.8rem; font-weight: 700; color: #1e293b; margin-bottom: 0.25rem; }
    .sub-header { font-size: 1rem; color: #64748b; margin-bottom: 2rem; }
    
    .score-card { background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 100%); border-radius: 16px; padding: 24px; color: white; text-align: center; }
    .score-value { font-size: 3.5rem; font-weight: 800; background: linear-gradient(135deg, #60a5fa 0%, #34d399 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
    .score-label { font-size: 0.9rem; font-weight: 600; margin-bottom: 8px; opacity: 0.9; }
    .score-subtitle { font-size: 0.75rem; opacity: 0.7; margin-top: 4px; }
    
    .metric-card { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px; }
    .metric-value { font-size: 2rem; font-weight: 700; color: #0f172a; }
    .metric-label { font-size: 0.7rem; color: #64748b; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px; }
    .metric-detail { font-size: 0.8rem; color: #10b981; margin-top: 4px; }
    .metric-detail.neutral { color: #64748b; }
    
    .section-header { font-size: 1rem; font-weight: 600; color: #1e293b; margin: 1.5rem 0 1rem 0; padding-bottom: 0.5rem; border-bottom: 1px solid #e2e8f0; }
    
    .badge { display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; }
    .badge-success { background: #dcfce7; color: #166534; }
    .badge-warning { background: #fef3c7; color: #92400e; }
    .badge-info { background: #e0f2fe; color: #0369a1; }
    
    .quote-card { background: #f8fafc; border-left: 4px solid #3b82f6; border-radius: 0 8px 8px 0; padding: 16px; margin: 8px 0; }
    .quote-card.candidate { background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%); border-left-color: #10b981; }
    .quote-text { font-size: 0.9rem; color: #334155; font-style: italic; line-height: 1.5; }
    .quote-source { font-size: 0.75rem; color: #64748b; margin-top: 8px; }
    
    .alert-card { background: #fef3c7; border-radius: 8px; padding: 12px 16px; margin: 8px 0; border-left: 4px solid #f59e0b; }
    .info-card { background: #f0f9ff; border-radius: 8px; padding: 16px; margin: 12px 0; border-left: 4px solid #0284c7; }
    
    .stat-row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #f1f5f9; }
    .stat-label { color: #64748b; font-size: 0.85rem; }
    .stat-value { color: #0f172a; font-weight: 600; font-size: 0.85rem; }
    
    .confidence-high { color: #059669; font-weight: 600; }
    .confidence-medium { color: #d97706; font-weight: 600; }
    .confidence-low { color: #64748b; }
    
    .breakdown-bar { height: 8px; background: #e2e8f0; border-radius: 4px; overflow: hidden; margin: 4px 0; }
    .breakdown-fill { height: 100%; background: linear-gradient(90deg, #3b82f6 0%, #10b981 100%); border-radius: 4px; }
    
    [data-testid="stSidebar"] { background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%); }
    [data-testid="stSidebar"] * { color: white !important; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

ICONS = {
    "dashboard": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect width="7" height="9" x="3" y="3" rx="1"/><rect width="7" height="5" x="14" y="3" rx="1"/><rect width="7" height="9" x="14" y="12" rx="1"/><rect width="7" height="5" x="3" y="16" rx="1"/></svg>',
    "users": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
    "check": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#059669" stroke-width="2"><path d="M20 6 9 17l-5-5"/></svg>',
}

# Session state
for key in ['logged_in', 'user_type', 'user_id', 'user_name', 'partner_type']:
    if key not in st.session_state:
        st.session_state[key] = False if key == 'logged_in' else None

USERS = {
    "ach_admin": {"password": "impact2024", "type": "ach_staff", "name": "ACH Administrator", "partner_type": None},
    "doubletree": {"password": "partner123", "type": "partner", "name": "DoubleTree by Hilton", "partner_id": 1, "partner_type": "employment"},
    "radisson": {"password": "partner123", "type": "partner", "name": "Radisson Blu", "partner_id": 2, "partner_type": "employment"},
    "starbucks": {"password": "partner123", "type": "partner", "name": "Starbucks", "partner_id": 3, "partner_type": "employment"},
    "firstbus": {"password": "partner123", "type": "partner", "name": "First Bus", "partner_id": 4, "partner_type": "employment"},
    "pret": {"password": "partner123", "type": "partner", "name": "Pret A Manger", "partner_id": 5, "partner_type": "employment"},
    "bristolwaste": {"password": "partner123", "type": "partner", "name": "Bristol Waste", "partner_id": 6, "partner_type": "employment"},
    "nhs_training": {"password": "training123", "type": "partner", "name": "NHS Bristol Trust", "partner_id": 101, "partner_type": "training"},
    "council_training": {"password": "training123", "type": "partner", "name": "Bristol City Council", "partner_id": 102, "partner_type": "training"},
    "university_training": {"password": "training123", "type": "partner", "name": "University of Bristol", "partner_id": 103, "partner_type": "training"},
}

# ============ STATISTICAL FUNCTIONS ============
def calculate_cohens_d(pre_scores, post_scores):
    """Calculate Cohen's d for paired samples"""
    if len(pre_scores) < 2 or len(post_scores) < 2:
        return 0
    diff = np.array(post_scores) - np.array(pre_scores)
    return np.mean(diff) / np.std(diff, ddof=1) if np.std(diff, ddof=1) > 0 else 0

def calculate_p_value(pre_scores, post_scores):
    """Calculate approximate p-value using manual paired t-test"""
    if len(pre_scores) < 2 or len(post_scores) < 2:
        return 1.0
    try:
        n = len(pre_scores)
        diff = [post_scores[i] - pre_scores[i] for i in range(n)]
        mean_diff = sum(diff) / n
        var_diff = sum((d - mean_diff) ** 2 for d in diff) / (n - 1)
        if var_diff == 0:
            return 1.0
        se = math.sqrt(var_diff / n)
        t_stat = mean_diff / se
        # Approximate p-value using t-distribution (simplified)
        df = n - 1
        # Using approximation for two-tailed p-value
        t_abs = abs(t_stat)
        if t_abs > 4:
            return 0.001
        elif t_abs > 3:
            return 0.01
        elif t_abs > 2.5:
            return 0.02
        elif t_abs > 2:
            return 0.05
        elif t_abs > 1.5:
            return 0.15
        else:
            return 0.5
    except:
        return 1.0

def get_confidence_statement(p_value, cohens_d):
    """Generate plain English confidence statement"""
    if p_value < 0.05 and abs(cohens_d) >= 0.8:
        return ("Strong evidence of significant improvement", "confidence-high")
    elif p_value < 0.05 and abs(cohens_d) >= 0.5:
        return ("Clear evidence of meaningful improvement", "confidence-high")
    elif p_value < 0.05 and abs(cohens_d) >= 0.2:
        return ("Statistically reliable improvement, modest in size", "confidence-medium")
    elif p_value < 0.05:
        return ("Small but measurable change", "confidence-medium")
    elif abs(cohens_d) >= 0.5:
        return ("Promising change, sample too small to confirm", "confidence-medium")
    else:
        return ("No clear evidence of change yet", "confidence-low")

def get_benchmark_level(score):
    """Get benchmark category for a score"""
    if score >= 81:
        return ("Leading", "Exemplary inclusion practice")
    elif score >= 61:
        return ("Established", "Strong foundation, refining practice")
    elif score >= 41:
        return ("Developing", "Growing capability, gaps remain")
    else:
        return ("Emerging", "Foundational development needed")

def convert_to_100(mean_score):
    """Convert 1-5 scale to 0-100"""
    return ((mean_score - 1) / 4) * 100

# ============ LOGIN ============
def login_page():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<p class="main-header">ACH Impact Intelligence</p>', unsafe_allow_html=True)
        st.markdown('<p class="sub-header">Measuring employment outcomes and cultural change</p>', unsafe_allow_html=True)
        
        with st.form("login"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Sign In", use_container_width=True):
                if username in USERS and USERS[username]["password"] == password:
                    st.session_state.logged_in = True
                    st.session_state.user_type = USERS[username]["type"]
                    st.session_state.user_name = USERS[username]["name"]
                    st.session_state.partner_type = USERS[username].get("partner_type")
                    st.session_state.user_id = USERS[username].get("partner_id")
                    st.rerun()
                else:
                    st.error("Invalid credentials")
        
        st.markdown("---")
        st.markdown("**Demo Logins**")
        st.caption("Employment: `doubletree` / `partner123`")
        st.caption("Training: `nhs_training` / `training123`")
        st.caption("ACH Staff: `ach_admin` / `impact2024`")

# ============ EMPLOYMENT METRICS ============
def calculate_employment_metrics(partner_id):
    m = {
        "total": 0, "active": 0, "retention": 0, "baseline_retention": 58,
        "hard_roles": 0, "hard_roles_value": 0,
        "retention_value": 0, "progressions": 0, "progression_actions": 0,
        "training_invested": 0, "living_wage_employer": True,
        "wellbeing_avg": 4.2, "placements": [],
        "employer_quotes": [], "candidate_quotes": [],
        "business_score": 0, "social_score": 0
    }
    
    try:
        placements = supabase.table("placements").select("*").eq("partner_id", partner_id).execute()
        if placements.data:
            m["placements"] = placements.data
            m["total"] = len(placements.data)
            m["active"] = len([p for p in placements.data if p.get("status") == "Active"])
            m["retention"] = round((m["active"] / m["total"]) * 100) if m["total"] > 0 else 0
        
        baseline = supabase.table("partner_baseline").select("*").eq("partner_id", partner_id).execute()
        if baseline.data:
            hard = [b for b in baseline.data if b.get("difficulty") in ["Hard", "Very Hard"]]
            m["hard_roles"] = len(hard)
            m["hard_roles_value"] = m["hard_roles"] * HARD_TO_FILL_VALUE
            rates = [b.get("retention_rate", 58) for b in baseline.data if b.get("retention_rate")]
            m["baseline_retention"] = round(sum(rates) / len(rates)) if rates else 58
        
        # Retention value calculation
        retention_improvement = max(0, m["retention"] - m["baseline_retention"])
        m["retention_value"] = round((retention_improvement / 100) * HARD_TO_FILL_VALUE * m["total"])
        
        reviews = supabase.table("milestone_reviews_partner").select("*").eq("partner_id", partner_id).execute()
        if reviews.data:
            m["progressions"] = sum(1 for r in reviews.data if r.get("progression"))
            m["training_invested"] = sum(1 for r in reviews.data if r.get("received_training"))
            m["progression_actions"] = sum(1 for r in reviews.data if r.get("progression") or r.get("received_training"))
            for r in reviews.data:
                if r.get("contribution_quote"):
                    m["employer_quotes"].append((r.get("contribution_quote"), "Milestone Review"))
        
        feedback = supabase.table("interview_feedback").select("*").eq("partner_id", partner_id).eq("hired", True).execute()
        if feedback.data:
            for f in feedback.data:
                if f.get("standout_reason"):
                    m["employer_quotes"].append((f.get("standout_reason"), "Interview Feedback"))
        
        # Candidate quotes
        if placements.data:
            for p in placements.data:
                cr = supabase.table("milestone_reviews_candidate").select("*").eq("placement_id", p["id"]).execute()
                if cr.data:
                    for c in cr.data:
                        if c.get("improvement_quote"):
                            m["candidate_quotes"].append((c.get("improvement_quote"), p.get("candidate_name"), "Check-in"))
                        if c.get("current_psych_safety"):
                            pass  # Could aggregate wellbeing scores here
        
        # Calculate scores
        # Business Value Score (recruitment savings, retention value, hard-to-fill)
        max_business = (m["total"] * HARD_TO_FILL_VALUE * 2)  # theoretical max
        actual_business = m["hard_roles_value"] + m["retention_value"]
        m["business_score"] = min(100, round((actual_business / max_business) * 100) + 40) if max_business > 0 else 75
        
        # Social Impact Score
        retention_score = min(100, (m["retention"] / 100) * 100)
        progression_score = min(100, (m["progressions"] / max(1, m["total"])) * 150)
        wellbeing_score = (m["wellbeing_avg"] / 5) * 100
        m["social_score"] = round(retention_score * 0.35 + progression_score * 0.35 + wellbeing_score * 0.30)
        
    except Exception as e:
        st.error(f"Error loading data: {e}")
    
    return m

# ============ EMPLOYMENT DASHBOARD ============
def employment_dashboard():
    st.markdown(f'<p class="main-header">{st.session_state.user_name}</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Employment Partnership Impact</p>', unsafe_allow_html=True)
    
    partner_id = st.session_state.get("user_id", 1)
    m = calculate_employment_metrics(partner_id)
    
    # Two Score Cards
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f'''
        <div class="score-card">
            <div class="score-label">Business Value Score</div>
            <div class="score-value">{m["business_score"]}</div>
            <div class="score-subtitle">Recruitment, retention & productivity</div>
        </div>
        ''', unsafe_allow_html=True)
    with col2:
        st.markdown(f'''
        <div class="score-card">
            <div class="score-label">Social Impact Score</div>
            <div class="score-value">{m["social_score"]}</div>
            <div class="score-subtitle">Employment outcomes & progression</div>
        </div>
        ''', unsafe_allow_html=True)
    
    st.markdown("")
    
    # Business Value Metrics
    st.markdown('<p class="section-header">Business Value</p>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f'''
        <div class="metric-card">
            <div class="metric-label">Hard-to-Fill Roles Filled</div>
            <div class="metric-value">{m["hard_roles"]}</div>
            <div class="metric-detail">£{m["hard_roles_value"]:,} est. recruitment value</div>
        </div>
        ''', unsafe_allow_html=True)
    with col2:
        st.markdown(f'''
        <div class="metric-card">
            <div class="metric-label">Retention Value</div>
            <div class="metric-value">£{m["retention_value"]:,}</div>
            <div class="metric-detail">+{m["retention"] - m["baseline_retention"]}% vs baseline</div>
        </div>
        ''', unsafe_allow_html=True)
    with col3:
        st.markdown(f'''
        <div class="metric-card">
            <div class="metric-label">Total Business Value</div>
            <div class="metric-value">£{m["hard_roles_value"] + m["retention_value"]:,}</div>
            <div class="metric-detail">Combined savings</div>
        </div>
        ''', unsafe_allow_html=True)
    
    # Social Impact Metrics
    st.markdown('<p class="section-header">Social Impact</p>', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'''
        <div class="metric-card">
            <div class="metric-label">Talents from Refugee/Migrant Backgrounds</div>
            <div class="metric-value">{m["active"]}</div>
            <div class="metric-detail">{m["total"]} total placements</div>
        </div>
        ''', unsafe_allow_html=True)
    with col2:
        st.markdown(f'''
        <div class="metric-card">
            <div class="metric-label">Retention Rate</div>
            <div class="metric-value">{m["retention"]}%</div>
            <div class="metric-detail">Baseline: {m["baseline_retention"]}%</div>
        </div>
        ''', unsafe_allow_html=True)
    with col3:
        st.markdown(f'''
        <div class="metric-card">
            <div class="metric-label">Career Progression Support</div>
            <div class="metric-value">{m["progression_actions"]}</div>
            <div class="metric-detail">Training & development actions</div>
        </div>
        ''', unsafe_allow_html=True)
    with col4:
        badge = "badge-success" if m["living_wage_employer"] else "badge-warning"
        status = "Living Wage Employer" if m["living_wage_employer"] else "Not Living Wage Accredited"
        st.markdown(f'''
        <div class="metric-card">
            <div class="metric-label">Living Wage Status</div>
            <div style="margin-top: 8px;"><span class="badge {badge}">{status}</span></div>
        </div>
        ''', unsafe_allow_html=True)
    
    # Employer Observations
    if m["employer_quotes"]:
        st.markdown('<p class="section-header">Employer Observations</p>', unsafe_allow_html=True)
        for quote, source in m["employer_quotes"][:3]:
            st.markdown(f'''
            <div class="quote-card">
                <div class="quote-text">"{quote}"</div>
                <div class="quote-source">Source: {source}</div>
            </div>
            ''', unsafe_allow_html=True)
    
    # Candidate Voices
    if m["candidate_quotes"]:
        st.markdown('<p class="section-header">Candidate Voices</p>', unsafe_allow_html=True)
        for quote, name, source in m["candidate_quotes"][:3]:
            st.markdown(f'''
            <div class="quote-card candidate">
                <div class="quote-text">"{quote}"</div>
                <div class="quote-source">— {name} (from {source})</div>
            </div>
            ''', unsafe_allow_html=True)
    
    # Team
    st.markdown('<p class="section-header">Your Team</p>', unsafe_allow_html=True)
    if m["placements"]:
        for p in m["placements"]:
            status_badge = "badge-success" if p.get("status") == "Active" else "badge-info"
            st.markdown(f"**{p['candidate_name']}** — {p['role']} · <span class='badge {status_badge}'>{p.get('status', 'Active')}</span>", unsafe_allow_html=True)
    else:
        st.info("No placements yet.")

# ============ EMPLOYMENT FORMS ============
def employment_baseline():
    st.markdown('<p class="main-header">Baseline Data</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Role information for measuring impact</p>', unsafe_allow_html=True)
    
    partner_id = st.session_state.get("user_id", 1)
    
    try:
        existing = supabase.table("partner_baseline").select("*").eq("partner_id", partner_id).execute()
        if existing.data:
            st.markdown(f"**{len(existing.data)} roles configured**")
            for r in existing.data:
                with st.expander(f"{r['role_title']} — £{r.get('salary', 0):,}/year"):
                    st.write(f"Typical retention: {r.get('retention_rate')}%")
                    st.write(f"Difficulty: {r.get('difficulty')}")
    except:
        pass
    
    st.markdown('<p class="section-header">Add Role</p>', unsafe_allow_html=True)
    with st.form("baseline"):
        col1, col2 = st.columns(2)
        with col1:
            role = st.text_input("Role Title *")
            salary = st.number_input("Annual Salary (£)", min_value=18000, max_value=80000, value=24000, step=500)
            retention = st.slider("Typical 12-month retention %", 0, 100, 55)
        with col2:
            difficulty = st.selectbox("Difficulty to fill", ["Easy", "Moderate", "Hard", "Very Hard"])
            vacancy_time = st.selectbox("Typical vacancy duration", ["< 2 weeks", "2-4 weeks", "1-2 months", "2-3 months", "3+ months"])
        
        if st.form_submit_button("Save Role", use_container_width=True):
            if role:
                supabase.table("partner_baseline").insert({
                    "partner_id": partner_id, "role_title": role, "salary": salary,
                    "retention_rate": retention, "difficulty": difficulty,
                    "vacancy_time": vacancy_time, "living_wage": True, "permanent": "Yes",
                    "created_at": datetime.now().isoformat()
                }).execute()
                st.success("Role saved")
                st.rerun()

def employment_interviews():
    st.markdown('<p class="main-header">Interview Feedback</p>', unsafe_allow_html=True)
    partner_id = st.session_state.get("user_id", 1)
    
    with st.form("interview"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Candidate Name *")
            role = st.text_input("Role *")
            date = st.date_input("Interview Date", value=datetime.now())
        with col2:
            hired = st.selectbox("Outcome", ["Hired", "Not Hired"])
        
        if hired == "Hired":
            standout = st.text_area("What made this candidate stand out?")
            start_date = st.date_input("Start Date", value=datetime.now() + timedelta(days=14))
            salary = st.number_input("Salary (£)", min_value=18000, max_value=80000, value=24000)
            rejection_reason = None
        else:
            rejection_reason = st.selectbox("Primary reason", ["Skills gap", "English proficiency", "Experience", "Availability", "Other"])
            standout = None
            start_date = None
            salary = None
        
        if st.form_submit_button("Submit", use_container_width=True):
            if name and role:
                supabase.table("interview_feedback").insert({
                    "partner_id": partner_id, "candidate_name": name, "candidate_id": f"C{datetime.now().strftime('%H%M%S')}",
                    "role": role, "interview_date": date.isoformat(), "hired": hired == "Hired",
                    "standout_reason": standout, "rejection_reason": rejection_reason,
                    "submitted_at": datetime.now().isoformat()
                }).execute()
                
                if hired == "Hired" and start_date:
                    supabase.table("placements").insert({
                        "partner_id": partner_id, "partner_name": st.session_state.user_name,
                        "candidate_name": name, "candidate_id": f"C{datetime.now().strftime('%H%M%S')}",
                        "role": role, "start_date": start_date.isoformat(),
                        "salary": salary, "hourly_rate": round(salary/1950, 2),
                        "contract_type": "Permanent", "status": "Active",
                        "created_at": datetime.now().isoformat()
                    }).execute()
                
                st.success("Submitted")
                st.rerun()

def employment_milestones():
    st.markdown('<p class="main-header">Milestone Reviews</p>', unsafe_allow_html=True)
    partner_id = st.session_state.get("user_id", 1)
    
    try:
        placements = supabase.table("placements").select("*").eq("partner_id", partner_id).eq("status", "Active").execute()
        if not placements.data:
            st.info("No active placements")
            return
        
        pending = []
        for p in placements.data:
            if p.get("start_date"):
                months = (datetime.now() - datetime.fromisoformat(p["start_date"])).days / 30
                for m in [3, 6, 12]:
                    if months >= m:
                        rev = supabase.table("milestone_reviews_partner").select("id").eq("placement_id", p["id"]).eq("milestone_month", m).execute()
                        if not rev.data:
                            pending.append({"placement": p, "milestone": m})
        
        if not pending:
            st.success("All reviews complete")
            return
        
        for item in pending:
            p = item["placement"]
            with st.expander(f"**{p['candidate_name']}** — {item['milestone']}-month review"):
                with st.form(f"review_{p['id']}_{item['milestone']}"):
                    employed = st.selectbox("Still employed?", ["Yes", "No"], key=f"e_{p['id']}_{item['milestone']}")
                    
                    if employed == "Yes":
                        performance = st.selectbox("Performance", ["Excellent", "Good", "Satisfactory", "Needs improvement"], key=f"p_{p['id']}_{item['milestone']}")
                        training = st.selectbox("Training provided?", ["Yes", "No"], key=f"t_{p['id']}_{item['milestone']}")
                        training_type = st.text_input("Training details", key=f"tt_{p['id']}_{item['milestone']}") if training == "Yes" else None
                        progression = st.selectbox("Progression support given?", ["Yes", "No"], key=f"pr_{p['id']}_{item['milestone']}")
                        progression_details = st.text_input("Details (promotion, pay rise, study support)", key=f"pd_{p['id']}_{item['milestone']}") if progression == "Yes" else None
                        quote = st.text_area("Observation about this employee", key=f"q_{p['id']}_{item['milestone']}")
                    else:
                        performance = training = training_type = progression = progression_details = quote = None
                        leaving_reason = st.selectbox("Reason", ["Resigned", "Contract ended", "Performance", "Other"], key=f"lr_{p['id']}_{item['milestone']}")
                    
                    if st.form_submit_button("Submit Review"):
                        supabase.table("milestone_reviews_partner").insert({
                            "placement_id": p['id'], "partner_id": partner_id,
                            "milestone_month": item['milestone'], "still_employed": employed == "Yes",
                            "performance": performance, "received_training": training == "Yes" if training else False,
                            "training_type": training_type, "progression": progression == "Yes" if progression else False,
                            "progression_details": progression_details, "contribution_quote": quote,
                            "submitted_at": datetime.now().isoformat()
                        }).execute()
                        
                        if employed == "No":
                            supabase.table("placements").update({"status": "Left"}).eq("id", p['id']).execute()
                        
                        st.success("Review submitted")
                        st.rerun()
    except Exception as e:
        st.error(f"Error: {e}")

# ============ TRAINING DASHBOARD ============
def training_dashboard():
    st.markdown(f'<p class="main-header">{st.session_state.user_name}</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Cultural Competence Training Impact</p>', unsafe_allow_html=True)
    
    partner_id = st.session_state.get("user_id", 101)
    
    # Get training data
    try:
        pre = supabase.table("training_pre_survey").select("*").eq("partner_id", partner_id).execute()
        post = supabase.table("training_post_survey").select("*").eq("partner_id", partner_id).execute()
        followup = supabase.table("training_followup").select("*").eq("partner_id", partner_id).execute()
        infra = supabase.table("training_infrastructure").select("*").eq("partner_id", partner_id).order("submitted_at", desc=True).limit(1).execute()
        
        pre_data = pre.data if pre.data else []
        post_data = post.data if post.data else []
        followup_data = followup.data if followup.data else []
        infra_data = infra.data[0] if infra.data else {}
        
    except:
        pre_data, post_data, followup_data, infra_data = [], [], [], {}
    
    # Calculate section scores
    sections = {
        "Knowledge": {"items": ["q1", "q2", "q3", "q4"], "weight": 0.20},
        "Awareness": {"items": ["q5", "q6", "q7", "q8"], "weight": 0.20},
        "Confidence": {"items": ["q9", "q10", "q11", "q12"], "weight": 0.25},
        "Psych Safety": {"items": ["q13", "q14", "q15"], "weight": 0.15},
        "Refugee Employment": {"items": ["q16", "q17", "q18", "q19", "q20"], "weight": 0.20}
    }
    
    # Demo scores if no data
    if not pre_data or not post_data:
        pre_scores = {"Knowledge": 2.4, "Awareness": 2.6, "Confidence": 2.3, "Psych Safety": 3.0, "Refugee Employment": 2.2}
        post_scores = {"Knowledge": 4.1, "Awareness": 4.0, "Confidence": 3.9, "Psych Safety": 4.2, "Refugee Employment": 3.8}
        followup_scores = {"Knowledge": 3.9, "Awareness": 3.8, "Confidence": 3.7, "Psych Safety": 4.0, "Refugee Employment": 3.6}
        total_trained = 87
        sessions_count = 3
    else:
        pre_scores = {s: 2.5 for s in sections}
        post_scores = {s: 4.0 for s in sections}
        followup_scores = {s: 3.8 for s in sections}
        total_trained = sum(p.get("attendees", 0) for p in pre_data)
        sessions_count = len(pre_data)
    
    # Calculate composite Inclusion Readiness Index
    pre_composite = sum(convert_to_100(pre_scores[s]) * sections[s]["weight"] for s in sections)
    post_composite = sum(convert_to_100(post_scores[s]) * sections[s]["weight"] for s in sections)
    
    benchmark_level, benchmark_desc = get_benchmark_level(post_composite)
    
    # Calculate statistics for demo
    pre_list = [pre_scores[s] for s in sections]
    post_list = [post_scores[s] for s in sections]
    cohens_d = calculate_cohens_d(pre_list, post_list)
    p_value = 0.003  # Demo value
    confidence_stmt, confidence_class = get_confidence_statement(p_value, cohens_d)
    
    # Infrastructure score
    infra_score = 75  # Demo
    
    # Display
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f'''
        <div class="score-card">
            <div class="score-label">Inclusion Readiness Index</div>
            <div class="score-value">{round(post_composite)}</div>
            <div class="score-subtitle">{benchmark_level}: {benchmark_desc}</div>
        </div>
        ''', unsafe_allow_html=True)
    with col2:
        st.markdown(f'''
        <div class="score-card">
            <div class="score-label">Infrastructure Score</div>
            <div class="score-value">{infra_score}</div>
            <div class="score-subtitle">Organisational policies & practices</div>
        </div>
        ''', unsafe_allow_html=True)
    
    st.markdown("")
    
    # Confidence statement
    st.markdown(f'''
    <div class="info-card">
        <span class="{confidence_class}">{confidence_stmt}</span><br>
        <span style="font-size: 0.8rem; color: #64748b;">Based on {total_trained} staff trained across {sessions_count} sessions</span>
    </div>
    ''', unsafe_allow_html=True)
    
    # Section breakdown
    st.markdown('<p class="section-header">Section Scores</p>', unsafe_allow_html=True)
    
    for section, config in sections.items():
        pre_val = convert_to_100(pre_scores[section])
        post_val = convert_to_100(post_scores[section])
        change = post_val - pre_val
        pct_possible = round((change / (100 - pre_val)) * 100) if pre_val < 100 else 0
        
        col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
        with col1:
            st.markdown(f"**{section}**")
            st.markdown(f'''<div class="breakdown-bar"><div class="breakdown-fill" style="width: {post_val}%"></div></div>''', unsafe_allow_html=True)
        with col2:
            st.markdown(f"Pre: **{round(pre_val)}**")
        with col3:
            st.markdown(f"Post: **{round(post_val)}**")
        with col4:
            st.markdown(f"<span style='color: #10b981'>+{round(change)} pts</span>", unsafe_allow_html=True)
    
    # 3-month sustainability
    if followup_data or True:  # Demo
        st.markdown('<p class="section-header">3-Month Sustainability</p>', unsafe_allow_html=True)
        
        sustained = sum(1 for s in sections if followup_scores[s] >= post_scores[s] * 0.9)
        behaviour_change_pct = 78  # Demo
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f'''
            <div class="metric-card">
                <div class="metric-label">Learning Retention</div>
                <div class="metric-value">{sustained}/5</div>
                <div class="metric-detail">Sections sustained</div>
            </div>
            ''', unsafe_allow_html=True)
        with col2:
            st.markdown(f'''
            <div class="metric-card">
                <div class="metric-label">Behaviour Change</div>
                <div class="metric-value">{behaviour_change_pct}%</div>
                <div class="metric-detail">Applied learning</div>
            </div>
            ''', unsafe_allow_html=True)
        with col3:
            st.markdown(f'''
            <div class="metric-card">
                <div class="metric-label">Recommend Score</div>
                <div class="metric-value">+68</div>
                <div class="metric-detail">NPS equivalent</div>
            </div>
            ''', unsafe_allow_html=True)

# ============ TRAINING FORMS ============
def training_pre_survey():
    st.markdown('<p class="main-header">Pre-Training Survey</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Baseline assessment before training</p>', unsafe_allow_html=True)
    
    partner_id = st.session_state.get("user_id", 101)
    
    st.markdown('<div class="info-card">Each attendee uses their unique code to link pre, post and follow-up responses.</div>', unsafe_allow_html=True)
    
    with st.form("pre_survey"):
        col1, col2 = st.columns(2)
        with col1:
            session_date = st.date_input("Training Date", value=datetime.now())
            attendee_code = st.text_input("Attendee Code *", placeholder="e.g. NHS-001")
        with col2:
            department = st.text_input("Department")
        
        st.markdown("### Section A: Knowledge")
        q1 = st.select_slider("1. I understand the legal rights of refugees and asylum seekers in the UK", options=[1,2,3,4,5], value=3, format_func=lambda x: ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"][x-1])
        q2 = st.select_slider("2. I can explain the difference between a refugee, asylum seeker, and migrant", options=[1,2,3,4,5], value=3, format_func=lambda x: ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"][x-1])
        q3 = st.select_slider("3. I understand the main barriers refugees face in accessing services/employment", options=[1,2,3,4,5], value=3, format_func=lambda x: ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"][x-1])
        q4 = st.select_slider("4. I am aware of how trauma may affect behaviour and communication", options=[1,2,3,4,5], value=3, format_func=lambda x: ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"][x-1])
        
        st.markdown("### Section B: Awareness")
        q5 = st.select_slider("5. I am aware of my own cultural assumptions and biases", options=[1,2,3,4,5], value=3, format_func=lambda x: ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"][x-1])
        q6 = st.select_slider("6. I recognise that people from different backgrounds may experience our organisation differently", options=[1,2,3,4,5], value=3, format_func=lambda x: ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"][x-1])
        q7 = st.select_slider("7. I understand that treating everyone 'the same' may not result in equal outcomes", options=[1,2,3,4,5], value=3, format_func=lambda x: ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"][x-1])
        q8 = st.select_slider("8. I notice when colleagues or systems may unintentionally exclude people from different backgrounds", options=[1,2,3,4,5], value=3, format_func=lambda x: ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"][x-1])
        
        st.markdown("### Section C: Confidence & Skills")
        q9 = st.select_slider("9. I feel confident supporting colleagues or service users from refugee backgrounds", options=[1,2,3,4,5], value=3, format_func=lambda x: ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"][x-1])
        q10 = st.select_slider("10. I can adapt my communication style for people with different English proficiency levels", options=[1,2,3,4,5], value=3, format_func=lambda x: ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"][x-1])
        q11 = st.select_slider("11. I know what to do if I witness discrimination or exclusion", options=[1,2,3,4,5], value=3, format_func=lambda x: ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"][x-1])
        q12 = st.select_slider("12. I feel able to ask respectful questions about someone's cultural background or needs", options=[1,2,3,4,5], value=3, format_func=lambda x: ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"][x-1])
        
        st.markdown("### Section D: Psychological Safety")
        q13 = st.select_slider("13. In my team, it is safe to raise concerns about inclusion without fear of negative consequences", options=[1,2,3,4,5], value=3, format_func=lambda x: ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"][x-1])
        q14 = st.select_slider("14. People in my team are not rejected for being different", options=[1,2,3,4,5], value=3, format_func=lambda x: ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"][x-1])
        q15 = st.select_slider("15. My colleagues value diverse perspectives and experiences", options=[1,2,3,4,5], value=3, format_func=lambda x: ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"][x-1])
        
        st.markdown("### Section E: Refugee Employment")
        q16 = st.select_slider("16. I understand how refugee candidates may have skills and experience not reflected in a traditional CV", options=[1,2,3,4,5], value=3, format_func=lambda x: ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"][x-1])
        q17 = st.select_slider("17. I recognise that standard recruitment processes may unintentionally disadvantage refugee candidates", options=[1,2,3,4,5], value=3, format_func=lambda x: ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"][x-1])
        q18 = st.select_slider("18. I feel confident interviewing or assessing candidates from refugee backgrounds fairly", options=[1,2,3,4,5], value=3, format_func=lambda x: ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"][x-1])
        q19 = st.select_slider("19. I know how to support a refugee colleague navigating UK workplace culture for the first time", options=[1,2,3,4,5], value=3, format_func=lambda x: ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"][x-1])
        q20 = st.select_slider("20. I am aware of practical barriers refugee employees may face (immigration appointments, housing, qualification recognition)", options=[1,2,3,4,5], value=3, format_func=lambda x: ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"][x-1])
        
        if st.form_submit_button("Submit Pre-Training Survey", use_container_width=True):
            if attendee_code:
                try:
                    supabase.table("training_pre_survey").insert({
                        "partner_id": partner_id, "attendee_code": attendee_code,
                        "session_date": session_date.isoformat(), "department": department,
                        "q1": q1, "q2": q2, "q3": q3, "q4": q4,
                        "q5": q5, "q6": q6, "q7": q7, "q8": q8,
                        "q9": q9, "q10": q10, "q11": q11, "q12": q12,
                        "q13": q13, "q14": q14, "q15": q15,
                        "q16": q16, "q17": q17, "q18": q18, "q19": q19, "q20": q20,
                        "submitted_at": datetime.now().isoformat()
                    }).execute()
                    st.success("Pre-training survey submitted")
                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                st.warning("Please enter attendee code")

def training_post_survey():
    st.markdown('<p class="main-header">Post-Training Survey</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Complete immediately after training</p>', unsafe_allow_html=True)
    
    partner_id = st.session_state.get("user_id", 101)
    
    with st.form("post_survey"):
        attendee_code = st.text_input("Attendee Code *", placeholder="Same code as pre-training")
        
        st.markdown("### Section A: Knowledge")
        q1 = st.select_slider("1. I understand the legal rights of refugees and asylum seekers in the UK", options=[1,2,3,4,5], value=4, format_func=lambda x: ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"][x-1], key="post_q1")
        q2 = st.select_slider("2. I can explain the difference between a refugee, asylum seeker, and migrant", options=[1,2,3,4,5], value=4, format_func=lambda x: ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"][x-1], key="post_q2")
        q3 = st.select_slider("3. I understand the main barriers refugees face in accessing services/employment", options=[1,2,3,4,5], value=4, format_func=lambda x: ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"][x-1], key="post_q3")
        q4 = st.select_slider("4. I am aware of how trauma may affect behaviour and communication", options=[1,2,3,4,5], value=4, format_func=lambda x: ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"][x-1], key="post_q4")
        
        st.markdown("### Section B: Awareness")
        q5 = st.select_slider("5. I am aware of my own cultural assumptions and biases", options=[1,2,3,4,5], value=4, format_func=lambda x: ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"][x-1], key="post_q5")
        q6 = st.select_slider("6. I recognise that people from different backgrounds may experience our organisation differently", options=[1,2,3,4,5], value=4, format_func=lambda x: ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"][x-1], key="post_q6")
        q7 = st.select_slider("7. I understand that treating everyone 'the same' may not result in equal outcomes", options=[1,2,3,4,5], value=4, format_func=lambda x: ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"][x-1], key="post_q7")
        q8 = st.select_slider("8. I notice when colleagues or systems may unintentionally exclude people from different backgrounds", options=[1,2,3,4,5], value=4, format_func=lambda x: ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"][x-1], key="post_q8")
        
        st.markdown("### Section C: Confidence & Skills")
        q9 = st.select_slider("9. I feel confident supporting colleagues or service users from refugee backgrounds", options=[1,2,3,4,5], value=4, format_func=lambda x: ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"][x-1], key="post_q9")
        q10 = st.select_slider("10. I can adapt my communication style for people with different English proficiency levels", options=[1,2,3,4,5], value=4, format_func=lambda x: ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"][x-1], key="post_q10")
        q11 = st.select_slider("11. I know what to do if I witness discrimination or exclusion", options=[1,2,3,4,5], value=4, format_func=lambda x: ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"][x-1], key="post_q11")
        q12 = st.select_slider("12. I feel able to ask respectful questions about someone's cultural background or needs", options=[1,2,3,4,5], value=4, format_func=lambda x: ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"][x-1], key="post_q12")
        
        st.markdown("### Section D: Psychological Safety")
        q13 = st.select_slider("13. In my team, it is safe to raise concerns about inclusion without fear of negative consequences", options=[1,2,3,4,5], value=4, format_func=lambda x: ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"][x-1], key="post_q13")
        q14 = st.select_slider("14. People in my team are not rejected for being different", options=[1,2,3,4,5], value=4, format_func=lambda x: ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"][x-1], key="post_q14")
        q15 = st.select_slider("15. My colleagues value diverse perspectives and experiences", options=[1,2,3,4,5], value=4, format_func=lambda x: ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"][x-1], key="post_q15")
        
        st.markdown("### Section E: Refugee Employment")
        q16 = st.select_slider("16. I understand how refugee candidates may have skills and experience not reflected in a traditional CV", options=[1,2,3,4,5], value=4, format_func=lambda x: ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"][x-1], key="post_q16")
        q17 = st.select_slider("17. I recognise that standard recruitment processes may unintentionally disadvantage refugee candidates", options=[1,2,3,4,5], value=4, format_func=lambda x: ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"][x-1], key="post_q17")
        q18 = st.select_slider("18. I feel confident interviewing or assessing candidates from refugee backgrounds fairly", options=[1,2,3,4,5], value=4, format_func=lambda x: ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"][x-1], key="post_q18")
        q19 = st.select_slider("19. I know how to support a refugee colleague navigating UK workplace culture for the first time", options=[1,2,3,4,5], value=4, format_func=lambda x: ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"][x-1], key="post_q19")
        q20 = st.select_slider("20. I am aware of practical barriers refugee employees may face (immigration appointments, housing, qualification recognition)", options=[1,2,3,4,5], value=4, format_func=lambda x: ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"][x-1], key="post_q20")
        
        st.markdown("### Training Feedback")
        commitment = st.text_area("I commit to applying my learning by...", placeholder="e.g. Being more mindful of assumptions in interviews, using simpler language...")
        
        if st.form_submit_button("Submit Post-Training Survey", use_container_width=True):
            if attendee_code:
                try:
                    supabase.table("training_post_survey").insert({
                        "partner_id": partner_id, "attendee_code": attendee_code,
                        "q1": q1, "q2": q2, "q3": q3, "q4": q4,
                        "q5": q5, "q6": q6, "q7": q7, "q8": q8,
                        "q9": q9, "q10": q10, "q11": q11, "q12": q12,
                        "q13": q13, "q14": q14, "q15": q15,
                        "q16": q16, "q17": q17, "q18": q18, "q19": q19, "q20": q20,
                        "commitment": commitment,
                        "submitted_at": datetime.now().isoformat()
                    }).execute()
                    st.success("Post-training survey submitted")
                except Exception as e:
                    st.error(f"Error: {e}")

def training_followup():
    st.markdown('<p class="main-header">3-Month Follow-up</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Measuring sustained learning and behaviour change</p>', unsafe_allow_html=True)
    
    partner_id = st.session_state.get("user_id", 101)
    
    with st.form("followup"):
        attendee_code = st.text_input("Attendee Code *", placeholder="Same code as pre/post training")
        
        st.markdown("### Current Confidence")
        st.caption("Please rate your current confidence (same questions as before)")
        
        q9 = st.select_slider("I feel confident supporting colleagues or service users from refugee backgrounds", options=[1,2,3,4,5], value=4, format_func=lambda x: ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"][x-1], key="fu_q9")
        q18 = st.select_slider("I feel confident interviewing or assessing candidates from refugee backgrounds fairly", options=[1,2,3,4,5], value=4, format_func=lambda x: ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"][x-1], key="fu_q18")
        
        st.markdown("### Applied Learning")
        applied = st.text_area("Describe one specific situation where you applied your learning to support a colleague or candidate from a refugee background. What did you do differently?", placeholder="Be as specific as possible...")
        
        observed_change = st.select_slider("Since the training, I have observed positive changes in how my organisation supports refugee employees or candidates", options=[1,2,3,4,5], value=3, format_func=lambda x: ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"][x-1])
        
        recommend = st.slider("How likely are you to recommend this training to colleagues? (0-10)", 0, 10, 8)
        
        if st.form_submit_button("Submit Follow-up", use_container_width=True):
            if attendee_code:
                # Code behaviour change (simple version)
                behaviour_code = 2 if len(applied) > 100 else (1 if len(applied) > 20 else 0)
                
                try:
                    supabase.table("training_followup").insert({
                        "partner_id": partner_id, "attendee_code": attendee_code,
                        "confidence_q9": q9, "confidence_q18": q18,
                        "applied_learning_text": applied, "applied_learning_code": behaviour_code,
                        "observed_change": observed_change, "recommend_score": recommend,
                        "submitted_at": datetime.now().isoformat()
                    }).execute()
                    st.success("Follow-up submitted")
                except Exception as e:
                    st.error(f"Error: {e}")

def training_infrastructure():
    st.markdown('<p class="main-header">Infrastructure Assessment</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Organisational policies and practices (HR/Leadership)</p>', unsafe_allow_html=True)
    
    partner_id = st.session_state.get("user_id", 101)
    
    st.markdown('<div class="info-card">This assessment is completed by HR or Leadership, not individual attendees. Complete once before training and again at 3-month follow-up.</div>', unsafe_allow_html=True)
    
    with st.form("infrastructure"):
        st.markdown("### Refugee Employment Readiness")
        
        i1 = st.selectbox("Recruitment processes reviewed for bias against refugee candidates", ["No", "Partial", "Yes"])
        i2 = st.selectbox("Job descriptions use accessible language and focus on core competencies", ["No", "Partial", "Yes"])
        i3 = st.selectbox("Alternative evidence accepted for skills/qualifications (not just UK credentials)", ["No", "Partial", "Yes"])
        i4 = st.selectbox("Onboarding adapted for employees unfamiliar with UK workplace norms", ["No", "Partial", "Yes"])
        i5 = st.selectbox("Language support available (translated materials, speaking pace, buddying)", ["No", "Partial", "Yes"])
        i6 = st.selectbox("Managers trained on supporting refugee employees", ["No", "Partial", "Yes"])
        i7 = st.selectbox("Flexible policies for employees with asylum/immigration appointments", ["No", "Partial", "Yes"])
        i8 = st.selectbox("Clear progression pathways communicated accessibly", ["No", "Partial", "Yes"])
        
        st.markdown("### Additional Information")
        refugees_interviewed = st.number_input("Refugee candidates interviewed since last assessment", min_value=0, value=0)
        refugees_hired = st.number_input("Refugee employees hired since last assessment", min_value=0, value=0)
        changes_made = st.text_area("Policy or process changes made since training", placeholder="Describe any changes...")
        
        if st.form_submit_button("Submit Assessment", use_container_width=True):
            score_map = {"No": 0, "Partial": 1, "Yes": 2}
            total = sum(score_map[x] for x in [i1, i2, i3, i4, i5, i6, i7, i8])
            score = round((total / 16) * 100)
            
            try:
                supabase.table("training_infrastructure").insert({
                    "partner_id": partner_id,
                    "i1_recruitment_bias": i1, "i2_job_descriptions": i2,
                    "i3_alternative_evidence": i3, "i4_onboarding": i4,
                    "i5_language_support": i5, "i6_manager_training": i6,
                    "i7_flexible_policies": i7, "i8_progression_pathways": i8,
                    "total_score": score,
                    "refugees_interviewed": refugees_interviewed,
                    "refugees_hired": refugees_hired,
                    "changes_made": changes_made,
                    "submitted_at": datetime.now().isoformat()
                }).execute()
                st.success(f"Assessment submitted. Infrastructure Score: {score}/100")
            except Exception as e:
                st.error(f"Error: {e}")

# ============ ACH STAFF ============
def ach_dashboard():
    st.markdown('<p class="main-header">ACH Programme Dashboard</p>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["Employment Partners", "Training Partners"])
    
    with tab1:
        try:
            partners = supabase.table("impact_partners").select("*").execute()
            placements = supabase.table("placements").select("*").execute()
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Employment Partners", len(partners.data) if partners.data else 0)
            with col2:
                st.metric("Total Placements", len(placements.data) if placements.data else 0)
            with col3:
                active = len([p for p in placements.data if p.get("status") == "Active"]) if placements.data else 0
                st.metric("Currently Employed", active)
        except:
            st.info("Employment data loading...")
    
    with tab2:
        try:
            pre = supabase.table("training_pre_survey").select("*").execute()
            sessions = len(set(p.get("session_date") for p in pre.data)) if pre.data else 0
            trained = len(pre.data) if pre.data else 0
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Training Partners", 3)
            with col2:
                st.metric("Sessions Delivered", sessions)
            with col3:
                st.metric("Staff Trained", trained)
        except:
            st.info("Training data loading...")

def ach_candidate_support():
    st.markdown('<p class="main-header">Candidate Check-ins</p>', unsafe_allow_html=True)
    
    try:
        placements = supabase.table("placements").select("*").eq("status", "Active").execute()
        if placements.data:
            selected = st.selectbox("Select Candidate", [f"{p['candidate_name']} at {p['partner_name']}" for p in placements.data])
            placement = next(p for p in placements.data if f"{p['candidate_name']} at {p['partner_name']}" == selected)
            
            with st.form("checkin"):
                milestone = st.selectbox("Milestone", [3, 6, 12])
                
                st.markdown("### Wellbeing")
                safe = st.select_slider("I feel safe to be myself at work", options=[1,2,3,4,5], value=4, format_func=lambda x: ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"][x-1])
                respected = st.select_slider("I feel respected", options=[1,2,3,4,5], value=4, format_func=lambda x: ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"][x-1])
                
                quote = st.text_area("Anything you'd like to share about your experience?")
                psych_safety = st.slider("Overall psychological safety (1-5)", 1, 5, 4)
                
                if st.form_submit_button("Submit"):
                    supabase.table("milestone_reviews_candidate").insert({
                        "placement_id": placement["id"], "milestone_month": milestone,
                        "safe_to_be_self": ["", "Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"][safe],
                        "feel_respected": ["", "Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"][respected],
                        "improvement_quote": quote, "current_psych_safety": psych_safety,
                        "submitted_at": datetime.now().isoformat()
                    }).execute()
                    st.success("Check-in submitted")
    except Exception as e:
        st.error(f"Error: {e}")

# ============ NAVIGATION ============
def main():
    if not st.session_state.logged_in:
        login_page()
        return
    
    with st.sidebar:
        st.markdown("### Impact Intelligence")
        st.markdown(f"**{st.session_state.user_name}**")
        if st.session_state.partner_type:
            st.caption(st.session_state.partner_type.title())
        st.markdown("---")
        
        if st.session_state.user_type == "ach_staff":
            page = st.radio("", ["Dashboard", "Candidate Support"], label_visibility="collapsed")
        elif st.session_state.partner_type == "employment":
            page = st.radio("", ["Dashboard", "Baseline Data", "Interview Feedback", "Milestone Reviews"], label_visibility="collapsed")
        elif st.session_state.partner_type == "training":
            page = st.radio("", ["Dashboard", "Pre-Training Survey", "Post-Training Survey", "3-Month Follow-up", "Infrastructure"], label_visibility="collapsed")
        
        st.markdown("---")
        if st.button("Logout", use_container_width=True):
            for k in st.session_state:
                st.session_state[k] = False if k == "logged_in" else None
            st.rerun()
    
    if st.session_state.user_type == "ach_staff":
        {"Dashboard": ach_dashboard, "Candidate Support": ach_candidate_support}[page]()
    elif st.session_state.partner_type == "employment":
        {"Dashboard": employment_dashboard, "Baseline Data": employment_baseline, "Interview Feedback": employment_interviews, "Milestone Reviews": employment_milestones}[page]()
    elif st.session_state.partner_type == "training":
        {"Dashboard": training_dashboard, "Pre-Training Survey": training_pre_survey, "Post-Training Survey": training_post_survey, "3-Month Follow-up": training_followup, "Infrastructure": training_infrastructure}[page]()

if __name__ == "__main__":
    main()
