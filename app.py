import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from supabase import create_client
import json
import math

SUPABASE_URL = "https://gmjqidqjpzxcpgycawxf.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdtanFpZHFqcHp4Y3BneWNhd3hmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njc3MjYyMDEsImV4cCI6MjA4MzMwMjIwMX0.6jtYlz6yoBQCrh04P0g30JigHyanGYnv7xBz24B5Bm4"

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
    
    .benchmark-bar { display: flex; margin-top: 12px; font-size: 0.65rem; }
    .benchmark-segment { flex: 1; padding: 4px 2px; text-align: center; border-radius: 4px; margin: 0 2px; }
    .benchmark-emerging { background: rgba(239,68,68,0.3); }
    .benchmark-developing { background: rgba(251,191,36,0.3); }
    .benchmark-established { background: rgba(34,197,94,0.3); }
    .benchmark-leading { background: rgba(59,130,246,0.3); }
    .benchmark-active { border: 2px solid white; font-weight: 700; }
    
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
    .badge-danger { background: #fee2e2; color: #991b1b; }
    
    .quote-card { background: #f8fafc; border-left: 4px solid #3b82f6; border-radius: 0 8px 8px 0; padding: 16px; margin: 8px 0; }
    .quote-card.candidate { background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%); border-left-color: #10b981; }
    .quote-text { font-size: 0.9rem; color: #334155; font-style: italic; line-height: 1.5; }
    .quote-source { font-size: 0.75rem; color: #64748b; margin-top: 8px; }
    
    .alert-card { background: #fef3c7; border-radius: 8px; padding: 12px 16px; margin: 8px 0; border-left: 4px solid #f59e0b; }
    .info-card { background: #f0f9ff; border-radius: 8px; padding: 16px; margin: 12px 0; border-left: 4px solid #0284c7; }
    
    .partner-row { background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; margin: 8px 0; display: flex; justify-content: space-between; align-items: center; }
    .partner-name { font-weight: 600; color: #1e293b; }
    .partner-meta { font-size: 0.8rem; color: #64748b; }
    
    .domain-score { display: flex; align-items: center; margin: 8px 0; }
    .domain-label { width: 140px; font-size: 0.85rem; color: #475569; }
    .domain-bar { flex: 1; height: 8px; background: #e2e8f0; border-radius: 4px; margin: 0 12px; overflow: hidden; }
    .domain-fill { height: 100%; border-radius: 4px; }
    .domain-value { width: 40px; font-size: 0.85rem; font-weight: 600; color: #1e293b; }
    
    .stat-card { background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%); border-radius: 12px; padding: 20px; text-align: center; border: 1px solid #e2e8f0; }
    .stat-value { font-size: 2.5rem; font-weight: 800; color: #0f172a; }
    .stat-label { font-size: 0.75rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; margin-top: 4px; }
    
    [data-testid="stSidebar"] { background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%); }
    [data-testid="stSidebar"] * { color: white !important; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

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

# ============ HELPER FUNCTIONS ============
def get_benchmark_level(score):
    if score >= 81:
        return ("Leading", "leading", "Exemplary practice")
    elif score >= 61:
        return ("Established", "established", "Strong foundation")
    elif score >= 41:
        return ("Developing", "developing", "Building capability")
    else:
        return ("Emerging", "emerging", "Early stage")

def render_score_card(label, score, subtitle, show_benchmark=True):
    level, level_class, level_desc = get_benchmark_level(score)
    
    benchmark_html = ""
    if show_benchmark:
        benchmark_html = f'<div style="margin-top: 12px; padding: 8px; background: rgba(255,255,255,0.1); border-radius: 8px; font-size: 0.75rem;"><strong>{level}</strong>: {level_desc}</div>'
    
    return f'''
    <div class="score-card">
        <div class="score-label">{label}</div>
        <div class="score-value">{score}</div>
        <div class="score-subtitle">{subtitle}</div>
        {benchmark_html}
    </div>
    '''

def convert_to_100(mean_score):
    return max(0, min(100, ((mean_score - 1) / 4) * 100))

def calculate_cohens_d(pre_scores, post_scores):
    if len(pre_scores) < 2 or len(post_scores) < 2:
        return 0
    diff = np.array(post_scores) - np.array(pre_scores)
    return np.mean(diff) / np.std(diff, ddof=1) if np.std(diff, ddof=1) > 0 else 0

# ============ LOGIN ============
def login_page():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<p class="main-header">ACH Impact Intelligence</p>', unsafe_allow_html=True)
        st.markdown('<p class="sub-header">Measuring employment outcomes and inclusion capability</p>', unsafe_allow_html=True)
        
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

# ============ CANDIDATE CAPABILITY GROWTH INDEX ============
def calculate_candidate_capability_index(partner_id):
    """Calculate Candidate Capability Growth Index from check-in data"""
    domains = {
        "self_efficacy": {"score": 0, "label": "Self-Efficacy", "color": "#3b82f6"},
        "work_readiness": {"score": 0, "label": "Work Readiness", "color": "#8b5cf6"},
        "social_capital": {"score": 0, "label": "Social Capital", "color": "#06b6d4"},
        "wellbeing": {"score": 0, "label": "Wellbeing", "color": "#10b981"},
        "economic_stability": {"score": 0, "label": "Economic Stability", "color": "#f59e0b"},
    }
    
    try:
        placements = supabase.table("placements").select("id").eq("partner_id", partner_id).execute()
        if not placements.data:
            # Return demo data
            return {
                "self_efficacy": {"score": 82, "label": "Self-Efficacy", "color": "#3b82f6"},
                "work_readiness": {"score": 75, "label": "Work Readiness", "color": "#8b5cf6"},
                "social_capital": {"score": 88, "label": "Social Capital", "color": "#06b6d4"},
                "wellbeing": {"score": 85, "label": "Wellbeing", "color": "#10b981"},
                "economic_stability": {"score": 72, "label": "Economic Stability", "color": "#f59e0b"},
            }, 80
        
        placement_ids = [p["id"] for p in placements.data]
        
        checkins = supabase.table("candidate_checkins").select("*").in_("placement_id", placement_ids).execute()
        
        if checkins.data:
            for domain in domains:
                scores = [c.get(f"{domain}_score", 0) for c in checkins.data if c.get(f"{domain}_score")]
                if scores:
                    domains[domain]["score"] = round(sum(scores) / len(scores))
        else:
            # Demo scores
            domains["self_efficacy"]["score"] = 82
            domains["work_readiness"]["score"] = 75
            domains["social_capital"]["score"] = 88
            domains["wellbeing"]["score"] = 85
            domains["economic_stability"]["score"] = 72
        
        composite = round(sum(d["score"] for d in domains.values()) / len(domains))
        return domains, composite
        
    except:
        # Return demo data on error
        return {
            "self_efficacy": {"score": 82, "label": "Self-Efficacy", "color": "#3b82f6"},
            "work_readiness": {"score": 75, "label": "Work Readiness", "color": "#8b5cf6"},
            "social_capital": {"score": 88, "label": "Social Capital", "color": "#06b6d4"},
            "wellbeing": {"score": 85, "label": "Wellbeing", "color": "#10b981"},
            "economic_stability": {"score": 72, "label": "Economic Stability", "color": "#f59e0b"},
        }, 80

# ============ EMPLOYMENT METRICS ============
def calculate_employment_metrics(partner_id):
    m = {
        "total": 0, "active": 0, "retention": 0, "baseline_retention": 52,
        "hard_roles": 0, "productivity_gained": 0, "retention_value": 0,
        "progressions": 0, "progression_support_score": 0,
        "training_provided": 0, "living_wage_employer": True,
        "placements": [], "employer_quotes": [], "candidate_quotes": [],
        "business_score": 0, "social_score": 0,
        "avg_vacancy_weeks_saved": 6
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
            
            # Calculate productivity gained from filling hard-to-fill roles
            # Based on reduced vacancy time
            total_productivity = 0
            for role in hard:
                salary = role.get("salary", 24000)
                weekly_value = salary / 52
                # Assume ACH fills 6 weeks faster than baseline
                weeks_saved = m["avg_vacancy_weeks_saved"]
                total_productivity += weekly_value * weeks_saved
            m["productivity_gained"] = round(total_productivity)
            
            rates = [b.get("retention_rate", 52) for b in baseline.data if b.get("retention_rate")]
            m["baseline_retention"] = round(sum(rates) / len(rates)) if rates else 52
        
        # Calculate retention value (savings from improved retention)
        # Average cost to replace an employee is ~£4,500
        retention_improvement = max(0, m["retention"] - m["baseline_retention"])
        m["retention_value"] = round((retention_improvement / 100) * 4500 * m["total"])
        
        reviews = supabase.table("milestone_reviews_partner").select("*").eq("partner_id", partner_id).execute()
        if reviews.data:
            m["progressions"] = sum(1 for r in reviews.data if r.get("progression"))
            m["training_provided"] = sum(1 for r in reviews.data if r.get("received_training"))
            
            # Progression support score (employer side)
            total_actions = m["progressions"] + m["training_provided"]
            m["progression_support_score"] = min(100, round((total_actions / max(1, m["total"])) * 50) + 30)
            
            for r in reviews.data:
                if r.get("contribution_quote"):
                    m["employer_quotes"].append((r.get("contribution_quote"), "Milestone Review"))
        
        feedback = supabase.table("interview_feedback").select("*").eq("partner_id", partner_id).eq("hired", True).execute()
        if feedback.data:
            for f in feedback.data:
                if f.get("standout_reason"):
                    m["employer_quotes"].append((f.get("standout_reason"), "Interview Feedback"))
        
        # Candidate quotes from check-ins
        if placements.data:
            for p in placements.data:
                cr = supabase.table("milestone_reviews_candidate").select("*").eq("placement_id", p["id"]).execute()
                if cr.data:
                    for c in cr.data:
                        if c.get("improvement_quote"):
                            m["candidate_quotes"].append((c.get("improvement_quote"), p.get("candidate_name"), "Check-in"))
        
        # Get Candidate Capability Growth Index
        domains, capability_index = calculate_candidate_capability_index(partner_id)
        
        # Business Value Score
        # Based on productivity gained and retention improvement
        retention_improvement = max(0, m["retention"] - m["baseline_retention"])
        productivity_score = min(100, (m["productivity_gained"] / 20000) * 100) if m["productivity_gained"] > 0 else 50
        retention_score = min(100, 50 + retention_improvement)
        m["business_score"] = round(productivity_score * 0.5 + retention_score * 0.5)
        
        # Social Impact Score
        # Candidate Capability Index (40%) + Progression Support (30%) + Living Wage (15%) + Talents Count (15%)
        living_wage_score = 100 if m["living_wage_employer"] else 0
        talents_score = min(100, m["active"] * 10)  # 10 points per active talent, max 100
        m["social_score"] = round(
            capability_index * 0.40 +
            m["progression_support_score"] * 0.30 +
            living_wage_score * 0.15 +
            talents_score * 0.15
        )
        
        m["capability_domains"] = domains
        m["capability_index"] = capability_index
        
    except Exception as e:
        # Demo data on error
        m["business_score"] = 74
        m["social_score"] = 78
        m["capability_index"] = 80
        m["productivity_gained"] = 12500
        m["capability_domains"] = {
            "self_efficacy": {"score": 82, "label": "Self-Efficacy", "color": "#3b82f6"},
            "work_readiness": {"score": 75, "label": "Work Readiness", "color": "#8b5cf6"},
            "social_capital": {"score": 88, "label": "Social Capital", "color": "#06b6d4"},
            "wellbeing": {"score": 85, "label": "Wellbeing", "color": "#10b981"},
            "economic_stability": {"score": 72, "label": "Economic Stability", "color": "#f59e0b"},
        }
    
    return m

# ============ EMPLOYMENT DASHBOARD ============
def employment_dashboard():
    st.markdown(f'<p class="main-header">{st.session_state.user_name}</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Employment Partnership Dashboard</p>', unsafe_allow_html=True)
    
    partner_id = st.session_state.get("user_id", 1)
    m = calculate_employment_metrics(partner_id)
    
    # Two Score Cards with Benchmarks
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(render_score_card(
            "Business Value Score",
            m["business_score"],
            "Productivity & retention gains"
        ), unsafe_allow_html=True)
        st.caption(f"ACH Partner Average: 68")
    
    with col2:
        st.markdown(render_score_card(
            "Social Impact Score", 
            m["social_score"],
            "Candidate outcomes & progression"
        ), unsafe_allow_html=True)
        st.caption(f"ACH Partner Average: 72")
    
    st.markdown("")
    
    # Business Value Metrics
    st.markdown('<p class="section-header">Business Value</p>', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'''
        <div class="metric-card">
            <div class="metric-label">Hard-to-Fill Roles Filled</div>
            <div class="metric-value">{m["hard_roles"]}</div>
            <div class="metric-detail">roles secured through ACH</div>
        </div>
        ''', unsafe_allow_html=True)
    with col2:
        st.markdown(f'''
        <div class="metric-card">
            <div class="metric-label">Productivity Gained</div>
            <div class="metric-value">£{m["productivity_gained"]:,}</div>
            <div class="metric-detail">from faster vacancy fill (~{m["avg_vacancy_weeks_saved"]} wks saved)</div>
        </div>
        ''', unsafe_allow_html=True)
    with col3:
        improvement = m["retention"] - m["baseline_retention"]
        st.markdown(f'''
        <div class="metric-card">
            <div class="metric-label">Retention Rate</div>
            <div class="metric-value">{m["retention"]}%</div>
            <div class="metric-detail">+{improvement}% vs baseline ({m["baseline_retention"]}%)</div>
        </div>
        ''', unsafe_allow_html=True)
    with col4:
        retention_value = m.get("retention_value", round(improvement * 450 * m["total"] / 10))
        st.markdown(f'''
        <div class="metric-card">
            <div class="metric-label">Retention Savings</div>
            <div class="metric-value">£{retention_value:,}</div>
            <div class="metric-detail">from reduced turnover costs</div>
        </div>
        ''', unsafe_allow_html=True)
    
    # Social Impact Metrics
    st.markdown('<p class="section-header">Social Impact</p>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1])
    with col1:
        # Candidate Capability Growth Index
        st.markdown("**Candidate Capability Growth Index**")
        domains = m.get("capability_domains", {})
        for key, domain in domains.items():
            st.markdown(f'''
            <div class="domain-score">
                <div class="domain-label">{domain["label"]}</div>
                <div class="domain-bar"><div class="domain-fill" style="width: {domain["score"]}%; background: {domain["color"]};"></div></div>
                <div class="domain-value">{domain["score"]}</div>
            </div>
            ''', unsafe_allow_html=True)
        st.markdown(f"**Composite Index: {m.get('capability_index', 80)}**/100")
    
    with col2:
        # Other social metrics
        st.markdown(f'''
        <div class="metric-card" style="margin-bottom: 12px;">
            <div class="metric-label">Talents from Refugee/Migrant Backgrounds</div>
            <div class="metric-value">{m["active"]}</div>
            <div class="metric-detail">{m["total"]} total placements</div>
        </div>
        ''', unsafe_allow_html=True)
        
        st.markdown(f'''
        <div class="metric-card" style="margin-bottom: 12px;">
            <div class="metric-label">Progression Support Score</div>
            <div class="metric-value">{m["progression_support_score"]}</div>
            <div class="metric-detail">{m["training_provided"]} training actions, {m["progressions"]} progressions</div>
        </div>
        ''', unsafe_allow_html=True)
        
        badge_class = "badge-success" if m["living_wage_employer"] else "badge-warning"
        badge_text = "Living Wage Employer" if m["living_wage_employer"] else "Not Living Wage Accredited"
        st.markdown(f'''
        <div class="metric-card">
            <div class="metric-label">Living Wage Status</div>
            <div style="margin-top: 8px;"><span class="badge {badge_class}">{badge_text}</span></div>
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
                diff_badge = "badge-danger" if r.get("difficulty") in ["Hard", "Very Hard"] else "badge-info"
                with st.expander(f"{r['role_title']} — £{r.get('salary', 0):,}/year"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"Typical retention: {r.get('retention_rate')}%")
                        st.write(f"Vacancy duration: {r.get('vacancy_time')}")
                    with col2:
                        st.markdown(f"Difficulty: <span class='badge {diff_badge}'>{r.get('difficulty')}</span>", unsafe_allow_html=True)
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
                for milestone in [3, 6, 12]:
                    if months >= milestone:
                        rev = supabase.table("milestone_reviews_partner").select("id").eq("placement_id", p["id"]).eq("milestone_month", milestone).execute()
                        if not rev.data:
                            pending.append({"placement": p, "milestone": milestone})
        
        if not pending:
            st.success("All reviews complete")
            return
        
        st.markdown(f'<div class="alert-card">{len(pending)} review(s) pending</div>', unsafe_allow_html=True)
        
        for item in pending:
            p = item["placement"]
            with st.expander(f"**{p['candidate_name']}** — {item['milestone']}-month review"):
                with st.form(f"review_{p['id']}_{item['milestone']}"):
                    employed = st.selectbox("Still employed?", ["Yes", "No"], key=f"e_{p['id']}_{item['milestone']}")
                    
                    if employed == "Yes":
                        performance = st.selectbox("Performance", ["Excellent", "Good", "Satisfactory", "Needs improvement"], key=f"p_{p['id']}_{item['milestone']}")
                        training = st.selectbox("Training provided?", ["Yes", "No"], key=f"t_{p['id']}_{item['milestone']}")
                        training_type = st.text_input("Training details", key=f"tt_{p['id']}_{item['milestone']}") if training == "Yes" else None
                        progression = st.selectbox("Progression support (promotion, pay rise, study support)?", ["Yes", "No"], key=f"pr_{p['id']}_{item['milestone']}")
                        progression_details = st.text_input("Details", key=f"pd_{p['id']}_{item['milestone']}") if progression == "Yes" else None
                        quote = st.text_area("Observation about this employee's contribution", key=f"q_{p['id']}_{item['milestone']}")
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
    
    # Demo scores
    pre_scores = {"Knowledge": 2.4, "Awareness": 2.6, "Confidence": 2.3, "Psych Safety": 3.0, "Refugee Employment": 2.2}
    post_scores = {"Knowledge": 4.1, "Awareness": 4.0, "Confidence": 3.9, "Psych Safety": 4.2, "Refugee Employment": 3.8}
    total_trained = 87
    sessions_count = 3
    
    sections = {
        "Knowledge": {"weight": 0.15},
        "Awareness": {"weight": 0.15},
        "Confidence": {"weight": 0.20},
        "Psych Safety": {"weight": 0.10},
        "Refugee Employment": {"weight": 0.15},
        "Infrastructure": {"weight": 0.25}
    }
    
    # Staff capability composite (without infrastructure)
    staff_sections = ["Knowledge", "Awareness", "Confidence", "Psych Safety", "Refugee Employment"]
    staff_composite = sum(convert_to_100(post_scores[s]) * sections[s]["weight"] for s in staff_sections)
    
    # Infrastructure score (from assessment)
    infra_score = 75
    
    # Combined Inclusion Capability Score (staff capability + infrastructure)
    inclusion_capability_score = round(staff_composite + (infra_score * sections["Infrastructure"]["weight"]))
    
    # Single Score Card
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(render_score_card(
            "Inclusion Capability Score",
            inclusion_capability_score,
            "Staff capability + organisational infrastructure"
        ), unsafe_allow_html=True)
        st.caption(f"ACH Training Cohort Average: 68")
    
    st.markdown("")
    st.markdown(f'<div class="info-card">Based on <strong>{total_trained} staff trained</strong> across <strong>{sessions_count} sessions</strong></div>', unsafe_allow_html=True)
    
    # Score Components
    st.markdown('<p class="section-header">Score Components</p>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Staff Capability**")
        for section in staff_sections:
            pre_val = convert_to_100(pre_scores[section])
            post_val = convert_to_100(post_scores[section])
            change = post_val - pre_val
            st.markdown(f'''
            <div class="domain-score">
                <div class="domain-label">{section}</div>
                <div class="domain-bar"><div class="domain-fill" style="width: {post_val}%; background: linear-gradient(90deg, #3b82f6 0%, #10b981 100%);"></div></div>
                <div class="domain-value">{round(post_val)}</div>
            </div>
            ''', unsafe_allow_html=True)
    
    with col2:
        st.markdown("**Organisational Infrastructure**")
        st.markdown(f'''
        <div class="metric-card">
            <div class="metric-label">Infrastructure Score</div>
            <div class="metric-value">{infra_score}</div>
            <div class="metric-detail">Policies, practices & support systems</div>
        </div>
        ''', unsafe_allow_html=True)
        st.markdown("")
        st.markdown("Infrastructure measures:")
        st.markdown("- Recruitment bias review")
        st.markdown("- Accessible job descriptions")
        st.markdown("- Alternative qualification recognition")
        st.markdown("- Adapted onboarding")
        st.markdown("- Language support available")
        st.markdown("- Manager training")
        st.markdown("- Flexible policies")
        st.markdown("- Clear progression pathways")

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
        q20 = st.select_slider("20. I am aware of practical barriers refugee employees may face", options=[1,2,3,4,5], value=3, format_func=lambda x: ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"][x-1])
        
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

def training_post_survey():
    st.markdown('<p class="main-header">Post-Training Survey</p>', unsafe_allow_html=True)
    partner_id = st.session_state.get("user_id", 101)
    
    with st.form("post_survey"):
        attendee_code = st.text_input("Attendee Code *", placeholder="Same code as pre-training")
        
        st.markdown("### Please rate your agreement after completing the training")
        
        questions = [
            "1. I understand the legal rights of refugees and asylum seekers in the UK",
            "2. I can explain the difference between a refugee, asylum seeker, and migrant",
            "3. I understand the main barriers refugees face in accessing services/employment",
            "4. I am aware of how trauma may affect behaviour and communication",
            "5. I am aware of my own cultural assumptions and biases",
            "6. I recognise that people from different backgrounds may experience our organisation differently",
            "7. I understand that treating everyone 'the same' may not result in equal outcomes",
            "8. I notice when colleagues or systems may unintentionally exclude people",
            "9. I feel confident supporting colleagues or service users from refugee backgrounds",
            "10. I can adapt my communication style for different English proficiency levels",
            "11. I know what to do if I witness discrimination or exclusion",
            "12. I feel able to ask respectful questions about someone's cultural background",
            "13. In my team, it is safe to raise concerns about inclusion",
            "14. People in my team are not rejected for being different",
            "15. My colleagues value diverse perspectives and experiences",
            "16. I understand how refugee candidates may have skills not reflected in a CV",
            "17. I recognise that standard recruitment may disadvantage refugee candidates",
            "18. I feel confident assessing candidates from refugee backgrounds fairly",
            "19. I know how to support a refugee colleague navigating UK workplace culture",
            "20. I am aware of practical barriers refugee employees may face"
        ]
        
        responses = []
        for i, q in enumerate(questions):
            responses.append(st.select_slider(q, options=[1,2,3,4,5], value=4, format_func=lambda x: ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"][x-1], key=f"post_q{i+1}"))
        
        commitment = st.text_area("I commit to applying my learning by...", placeholder="e.g. Being more mindful of assumptions...")
        
        if st.form_submit_button("Submit Post-Training Survey", use_container_width=True):
            if attendee_code:
                data = {"partner_id": partner_id, "attendee_code": attendee_code, "commitment": commitment, "submitted_at": datetime.now().isoformat()}
                for i, r in enumerate(responses):
                    data[f"q{i+1}"] = r
                supabase.table("training_post_survey").insert(data).execute()
                st.success("Post-training survey submitted")

def training_followup():
    st.markdown('<p class="main-header">3-Month Follow-up</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Measuring sustained learning and organisational change</p>', unsafe_allow_html=True)
    
    partner_id = st.session_state.get("user_id", 101)
    
    with st.form("followup"):
        attendee_code = st.text_input("Attendee Code *", placeholder="Same code used in pre/post surveys")
        
        st.markdown("---")
        st.markdown("### Section A: Sustained Confidence")
        st.caption("Rate your current confidence (same questions as post-training)")
        
        q9 = st.select_slider("I feel confident supporting colleagues or service users from refugee backgrounds", options=[1,2,3,4,5], value=4, format_func=lambda x: ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"][x-1], key="fu_q9")
        q10 = st.select_slider("I can adapt my communication style for people with different English proficiency levels", options=[1,2,3,4,5], value=4, format_func=lambda x: ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"][x-1], key="fu_q10")
        q18 = st.select_slider("I feel confident interviewing or assessing candidates from refugee backgrounds fairly", options=[1,2,3,4,5], value=4, format_func=lambda x: ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"][x-1], key="fu_q18")
        q19 = st.select_slider("I know how to support a refugee colleague navigating UK workplace culture", options=[1,2,3,4,5], value=4, format_func=lambda x: ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"][x-1], key="fu_q19")
        
        st.markdown("---")
        st.markdown("### Section B: Applied Learning")
        
        applied_example = st.text_area(
            "Describe a specific situation where you applied your learning",
            placeholder="E.g., 'I changed how I conduct interviews by...', 'I supported a colleague by...', 'I advocated for a policy change...'",
            help="Be specific about what you did differently as a result of the training"
        )
        
        applied_frequency = st.select_slider(
            "How often have you applied your learning from the training?",
            options=[1,2,3,4,5],
            value=3,
            format_func=lambda x: ["Never", "Once or twice", "A few times", "Regularly", "Very frequently"][x-1]
        )
        
        st.markdown("---")
        st.markdown("### Section C: Organisational Changes Observed")
        
        org_recruitment = st.select_slider("Our recruitment processes have become more inclusive for refugee candidates", options=[1,2,3,4,5], value=3, format_func=lambda x: ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"][x-1])
        org_onboarding = st.select_slider("Our onboarding has been adapted to better support refugee employees", options=[1,2,3,4,5], value=3, format_func=lambda x: ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"][x-1])
        org_support = st.select_slider("There is more support available for refugee employees than before", options=[1,2,3,4,5], value=3, format_func=lambda x: ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"][x-1])
        org_culture = st.select_slider("The overall culture has become more welcoming to people from refugee backgrounds", options=[1,2,3,4,5], value=3, format_func=lambda x: ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"][x-1])
        
        specific_changes = st.text_area(
            "What specific organisational changes have you observed since the training?",
            placeholder="E.g., 'New translated materials', 'Buddy system introduced', 'Flexible policy for immigration appointments'..."
        )
        
        st.markdown("---")
        st.markdown("### Section D: Barriers & Recommendations")
        
        barriers = st.text_area(
            "What barriers (if any) have prevented you from applying your learning?",
            placeholder="E.g., 'Lack of time', 'No opportunities', 'Need more manager support'..."
        )
        
        recommendations = st.text_area(
            "What additional support would help your organisation become more inclusive?",
            placeholder="E.g., 'Refresher training', 'Manager-specific session', 'Resources for team meetings'..."
        )
        
        if st.form_submit_button("Submit 3-Month Follow-up", use_container_width=True):
            if attendee_code:
                # Calculate scores
                confidence_avg = (q9 + q10 + q18 + q19) / 4
                org_change_avg = (org_recruitment + org_onboarding + org_support + org_culture) / 4
                behaviour_code = 2 if len(applied_example) > 100 else (1 if len(applied_example) > 20 else 0)
                
                try:
                    supabase.table("training_followup").insert({
                        "partner_id": partner_id,
                        "attendee_code": attendee_code,
                        "confidence_q9": q9,
                        "confidence_q10": q10,
                        "confidence_q18": q18,
                        "confidence_q19": q19,
                        "confidence_avg": confidence_avg,
                        "applied_learning_text": applied_example,
                        "applied_learning_code": behaviour_code,
                        "applied_frequency": applied_frequency,
                        "org_recruitment": org_recruitment,
                        "org_onboarding": org_onboarding,
                        "org_support": org_support,
                        "org_culture": org_culture,
                        "org_change_avg": org_change_avg,
                        "specific_changes": specific_changes,
                        "barriers": barriers,
                        "recommendations": recommendations,
                        "submitted_at": datetime.now().isoformat()
                    }).execute()
                    st.success("3-month follow-up submitted successfully")
                except Exception as e:
                    st.error(f"Error submitting: {e}")
            else:
                st.warning("Please enter your attendee code")

def training_infrastructure():
    st.markdown('<p class="main-header">Infrastructure Assessment</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Organisational policies and practices (HR/Leadership)</p>', unsafe_allow_html=True)
    
    partner_id = st.session_state.get("user_id", 101)
    
    with st.form("infrastructure"):
        st.markdown("### Refugee Employment Readiness")
        
        items = [
            ("i1", "Recruitment processes reviewed for bias against refugee candidates"),
            ("i2", "Job descriptions use accessible language and focus on core competencies"),
            ("i3", "Alternative evidence accepted for skills/qualifications (not just UK credentials)"),
            ("i4", "Onboarding adapted for employees unfamiliar with UK workplace norms"),
            ("i5", "Language support available (translated materials, speaking pace, buddying)"),
            ("i6", "Managers trained on supporting refugee employees"),
            ("i7", "Flexible policies for employees with asylum/immigration appointments"),
            ("i8", "Clear progression pathways communicated accessibly")
        ]
        
        responses = {}
        for key, label in items:
            responses[key] = st.selectbox(label, ["No", "Partial", "Yes"], key=key)
        
        st.markdown("### Additional Information")
        refugees_interviewed = st.number_input("Refugee candidates interviewed since last assessment", min_value=0, value=0)
        refugees_hired = st.number_input("Refugee employees hired since last assessment", min_value=0, value=0)
        changes_made = st.text_area("Policy or process changes made since training")
        
        if st.form_submit_button("Submit Assessment", use_container_width=True):
            score_map = {"No": 0, "Partial": 1, "Yes": 2}
            total = sum(score_map[v] for v in responses.values())
            score = round((total / 16) * 100)
            
            data = {"partner_id": partner_id, "total_score": score,
                    "refugees_interviewed": refugees_interviewed, "refugees_hired": refugees_hired,
                    "changes_made": changes_made, "submitted_at": datetime.now().isoformat()}
            for key, val in responses.items():
                data[f"{key}_recruitment_bias" if key == "i1" else key] = val
            
            supabase.table("training_infrastructure").insert(data).execute()
            st.success(f"Assessment submitted. Infrastructure Score: {score}/100")

# ============ ACH STAFF DASHBOARD ============
def ach_dashboard():
    st.markdown('<p class="main-header">ACH Programme Dashboard</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Strategic overview of all partnerships</p>', unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["Employment Programme", "Training Programme", "Combined Impact"])
    
    with tab1:
        ach_employment_overview()
    
    with tab2:
        ach_training_overview()
    
    with tab3:
        ach_combined_impact()

def ach_employment_overview():
    # Aggregate stats
    try:
        partners = supabase.table("impact_partners").select("*").execute()
        placements = supabase.table("placements").select("*").execute()
        reviews = supabase.table("milestone_reviews_partner").select("*").execute()
        
        total_partners = len(partners.data) if partners.data else 6
        total_placements = len(placements.data) if placements.data else 20
        active = len([p for p in placements.data if p.get("status") == "Active"]) if placements.data else 18
        retention = round((active / total_placements) * 100) if total_placements > 0 else 90
        progressions = sum(1 for r in reviews.data if r.get("progression")) if reviews.data else 8
        
    except:
        total_partners, total_placements, active, retention, progressions = 6, 20, 18, 90, 8
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'''
        <div class="stat-card">
            <div class="stat-value">{total_partners}</div>
            <div class="stat-label">Employment Partners</div>
        </div>
        ''', unsafe_allow_html=True)
    with col2:
        st.markdown(f'''
        <div class="stat-card">
            <div class="stat-value">{active}</div>
            <div class="stat-label">Active Placements</div>
        </div>
        ''', unsafe_allow_html=True)
    with col3:
        st.markdown(f'''
        <div class="stat-card">
            <div class="stat-value">{retention}%</div>
            <div class="stat-label">Overall Retention</div>
        </div>
        ''', unsafe_allow_html=True)
    with col4:
        st.markdown(f'''
        <div class="stat-card">
            <div class="stat-value">{progressions}</div>
            <div class="stat-label">Career Progressions</div>
        </div>
        ''', unsafe_allow_html=True)
    
    st.markdown("")
    
    # Partner Performance
    st.markdown('<p class="section-header">Partner Performance</p>', unsafe_allow_html=True)
    
    partner_data = [
        {"name": "DoubleTree by Hilton", "placements": 5, "active": 5, "business": 78, "social": 82, "tier": "Leading"},
        {"name": "Radisson Blu", "placements": 4, "active": 4, "business": 74, "social": 79, "tier": "Established"},
        {"name": "Starbucks", "placements": 3, "active": 3, "business": 71, "social": 76, "tier": "Established"},
        {"name": "First Bus", "placements": 3, "active": 3, "business": 82, "social": 85, "tier": "Leading"},
        {"name": "Pret A Manger", "placements": 2, "active": 2, "business": 68, "social": 72, "tier": "Established"},
        {"name": "Bristol Waste", "placements": 3, "active": 3, "business": 76, "social": 80, "tier": "Established"},
    ]
    
    for p in partner_data:
        tier_badge = "badge-success" if p["tier"] == "Leading" else "badge-info"
        st.markdown(f'''
        <div class="partner-row">
            <div>
                <div class="partner-name">{p["name"]}</div>
                <div class="partner-meta">{p["active"]}/{p["placements"]} active placements</div>
            </div>
            <div style="display: flex; gap: 16px; align-items: center;">
                <div style="text-align: center;"><div style="font-size: 1.2rem; font-weight: 700;">{p["business"]}</div><div style="font-size: 0.7rem; color: #64748b;">Business</div></div>
                <div style="text-align: center;"><div style="font-size: 1.2rem; font-weight: 700;">{p["social"]}</div><div style="font-size: 0.7rem; color: #64748b;">Social</div></div>
                <span class="badge {tier_badge}">{p["tier"]}</span>
            </div>
        </div>
        ''', unsafe_allow_html=True)
    
    # Alerts
    st.markdown('<p class="section-header">Alerts & Actions</p>', unsafe_allow_html=True)
    st.markdown('<div class="alert-card">3 milestone reviews overdue (DoubleTree: 2, Radisson: 1)</div>', unsafe_allow_html=True)
    st.markdown('<div class="alert-card">2 candidates approaching 6-month milestone this week</div>', unsafe_allow_html=True)

def ach_training_overview():
    # Aggregate stats
    total_partners = 3
    total_trained = 87
    sessions = 7
    avg_improvement = 42
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'''
        <div class="stat-card">
            <div class="stat-value">{total_partners}</div>
            <div class="stat-label">Training Partners</div>
        </div>
        ''', unsafe_allow_html=True)
    with col2:
        st.markdown(f'''
        <div class="stat-card">
            <div class="stat-value">{total_trained}</div>
            <div class="stat-label">Staff Trained</div>
        </div>
        ''', unsafe_allow_html=True)
    with col3:
        st.markdown(f'''
        <div class="stat-card">
            <div class="stat-value">{sessions}</div>
            <div class="stat-label">Sessions Delivered</div>
        </div>
        ''', unsafe_allow_html=True)
    with col4:
        st.markdown(f'''
        <div class="stat-card">
            <div class="stat-value">+{avg_improvement}%</div>
            <div class="stat-label">Avg Improvement</div>
        </div>
        ''', unsafe_allow_html=True)
    
    st.markdown("")
    
    # Partner Performance
    st.markdown('<p class="section-header">Partner Performance</p>', unsafe_allow_html=True)
    
    training_partners = [
        {"name": "NHS Bristol Trust", "trained": 45, "sessions": 3, "score": 75, "infra": 69, "tier": "Established"},
        {"name": "Bristol City Council", "trained": 28, "sessions": 2, "score": 68, "infra": 44, "tier": "Developing"},
        {"name": "University of Bristol", "trained": 14, "sessions": 2, "score": 82, "infra": 75, "tier": "Leading"},
    ]
    
    for p in training_partners:
        tier_badge = "badge-success" if p["tier"] == "Leading" else ("badge-info" if p["tier"] == "Established" else "badge-warning")
        st.markdown(f'''
        <div class="partner-row">
            <div>
                <div class="partner-name">{p["name"]}</div>
                <div class="partner-meta">{p["trained"]} staff across {p["sessions"]} sessions</div>
            </div>
            <div style="display: flex; gap: 16px; align-items: center;">
                <div style="text-align: center;"><div style="font-size: 1.2rem; font-weight: 700;">{p["score"]}</div><div style="font-size: 0.7rem; color: #64748b;">Capability</div></div>
                <div style="text-align: center;"><div style="font-size: 1.2rem; font-weight: 700;">{p["infra"]}</div><div style="font-size: 0.7rem; color: #64748b;">Infrastructure</div></div>
                <span class="badge {tier_badge}">{p["tier"]}</span>
            </div>
        </div>
        ''', unsafe_allow_html=True)
    
    # Alerts
    st.markdown('<p class="section-header">Alerts & Actions</p>', unsafe_allow_html=True)
    st.markdown('<div class="alert-card">Bristol City Council: 3-month follow-up overdue for March cohort</div>', unsafe_allow_html=True)
    st.markdown('<div class="info-card">University of Bristol requesting additional session for Academic Staff</div>', unsafe_allow_html=True)

def ach_combined_impact():
    st.markdown("### Combined Programme Impact")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f'''
        <div class="score-card">
            <div class="score-label">Employment Programme</div>
            <div class="score-value">76</div>
            <div class="score-subtitle">Average Partner Score</div>
        </div>
        ''', unsafe_allow_html=True)
    with col2:
        st.markdown(f'''
        <div class="score-card">
            <div class="score-label">Training Programme</div>
            <div class="score-value">72</div>
            <div class="score-subtitle">Average Partner Score</div>
        </div>
        ''', unsafe_allow_html=True)
    
    st.markdown("")
    st.markdown('<p class="section-header">Impact Summary</p>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Partners", "9", "Employment: 6, Training: 3")
    with col2:
        st.metric("Lives Impacted", "107", "20 employed + 87 trained")
    with col3:
        st.metric("Business Value Generated", "£52,400", "Across all employment partners")
    
    st.markdown('<p class="section-header">For Funder Reports</p>', unsafe_allow_html=True)
    st.markdown("""
    **Employment Programme:**
    - 20 refugees/migrants placed into employment
    - 90% retention rate (vs 52% sector baseline)
    - 8 career progressions achieved
    - £52,400 productivity value generated for partners
    - Average Candidate Capability Growth Index: 80/100
    
    **Training Programme:**
    - 87 staff trained across 3 organisations
    - 42% average improvement in inclusion capability
    - 78% applied learning in practice at 3 months
    - 9 refugees hired by training partners post-training
    """)

# ============ ACH CANDIDATE SUPPORT ============
def ach_candidate_checkins():
    st.markdown('<p class="main-header">Candidate Check-ins</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">7-Domain Capability Assessment</p>', unsafe_allow_html=True)
    
    # Get active placements
    try:
        placements = supabase.table("placements").select("*").eq("status", "Active").execute()
        placement_list = placements.data if placements.data else []
    except:
        placement_list = []
    
    if not placement_list:
        st.info("No active placements found")
        return
    
    # Pending check-ins
    st.markdown('<p class="section-header">Pending Check-ins</p>', unsafe_allow_html=True)
    
    pending = []
    for p in placement_list:
        if p.get("start_date"):
            months = (datetime.now() - datetime.fromisoformat(p["start_date"])).days / 30
            for milestone in [3, 6, 12]:
                if months >= milestone - 0.5:  # Due within 2 weeks of milestone
                    pending.append({"placement": p, "milestone": milestone, "months": months})
    
    if pending:
        for item in pending[:5]:
            p = item["placement"]
            st.markdown(f'<div class="alert-card"><strong>{p["candidate_name"]}</strong> at {p["partner_name"]} — {item["milestone"]}-month check-in due</div>', unsafe_allow_html=True)
    
    # Check-in form
    st.markdown('<p class="section-header">Submit Check-in</p>', unsafe_allow_html=True)
    
    selected = st.selectbox("Select Candidate", [f"{p['candidate_name']} at {p['partner_name']}" for p in placement_list])
    placement = next((p for p in placement_list if f"{p['candidate_name']} at {p['partner_name']}" == selected), None)
    
    if placement:
        with st.form("candidate_checkin"):
            milestone = st.selectbox("Milestone", [3, 6, 12])
            
            st.markdown("---")
            st.markdown("### Self-Efficacy (Confidence)")
            se1 = st.select_slider("My confidence in my abilities has grown since starting this job", options=[1,2,3,4,5], value=4, format_func=lambda x: ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"][x-1], key="se1")
            se2 = st.select_slider("I feel capable of taking on new challenges at work", options=[1,2,3,4,5], value=4, format_func=lambda x: ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"][x-1], key="se2")
            se3 = st.select_slider("I believe I can progress in my career", options=[1,2,3,4,5], value=4, format_func=lambda x: ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"][x-1], key="se3")
            
            st.markdown("### Work Readiness (Skills)")
            wr1 = st.select_slider("I have received training that helps me do my job better", options=[1,2,3,4,5], value=4, format_func=lambda x: ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"][x-1], key="wr1")
            wr2 = st.select_slider("My English/communication skills have improved", options=[1,2,3,4,5], value=4, format_func=lambda x: ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"][x-1], key="wr2")
            wr3 = st.select_slider("I am developing new skills in this role", options=[1,2,3,4,5], value=4, format_func=lambda x: ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"][x-1], key="wr3")
            
            st.markdown("### Social Capital (Belonging)")
            sc1 = st.select_slider("I feel part of the team", options=[1,2,3,4,5], value=4, format_func=lambda x: ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"][x-1], key="sc1")
            sc2 = st.select_slider("I have colleagues I can ask for help", options=[1,2,3,4,5], value=4, format_func=lambda x: ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"][x-1], key="sc2")
            sc3 = st.select_slider("I feel included in workplace social activities", options=[1,2,3,4,5], value=4, format_func=lambda x: ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"][x-1], key="sc3")
            
            st.markdown("### Wellbeing (Psychological Safety)")
            wb1 = st.select_slider("I feel safe to be myself at work", options=[1,2,3,4,5], value=4, format_func=lambda x: ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"][x-1], key="wb1")
            wb2 = st.select_slider("I feel respected by my manager and colleagues", options=[1,2,3,4,5], value=4, format_func=lambda x: ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"][x-1], key="wb2")
            wb3 = st.select_slider("I can raise concerns without fear of negative consequences", options=[1,2,3,4,5], value=4, format_func=lambda x: ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"][x-1], key="wb3")
            wb4 = st.select_slider("My mental health has improved since starting this job", options=[1,2,3,4,5], value=4, format_func=lambda x: ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"][x-1], key="wb4")
            
            st.markdown("### Economic Stability")
            es1 = st.select_slider("My income is stable and predictable", options=[1,2,3,4,5], value=4, format_func=lambda x: ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"][x-1], key="es1")
            es2 = st.select_slider("I can meet my basic needs with my current salary", options=[1,2,3,4,5], value=4, format_func=lambda x: ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"][x-1], key="es2")
            es3 = st.select_slider("I feel more financially secure than before this job", options=[1,2,3,4,5], value=4, format_func=lambda x: ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"][x-1], key="es3")
            
            st.markdown("### Progression")
            pr1 = st.select_slider("I have a clear understanding of how I can progress", options=[1,2,3,4,5], value=3, format_func=lambda x: ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"][x-1], key="pr1")
            pr2 = st.select_slider("My employer supports my development", options=[1,2,3,4,5], value=4, format_func=lambda x: ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"][x-1], key="pr2")
            pr3 = st.select_slider("I have had opportunities for training or learning", options=[1,2,3,4,5], value=4, format_func=lambda x: ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"][x-1], key="pr3")
            
            st.markdown("### Voice")
            best_thing = st.text_area("What has been the best thing about this job?")
            challenges = st.text_area("What challenges have you faced?")
            support_needed = st.text_area("What would help you succeed even more?")
            
            st.markdown("### Overall")
            overall = st.select_slider("How do you feel about your job overall?", options=[1,2,3,4,5], value=4, format_func=lambda x: ["Very Negative", "Negative", "Neutral", "Positive", "Very Positive"][x-1], key="overall")
            
            if st.form_submit_button("Submit Check-in", use_container_width=True):
                # Calculate domain scores (convert to 0-100)
                self_efficacy_score = round(convert_to_100((se1 + se2 + se3) / 3))
                work_readiness_score = round(convert_to_100((wr1 + wr2 + wr3) / 3))
                social_capital_score = round(convert_to_100((sc1 + sc2 + sc3) / 3))
                wellbeing_score = round(convert_to_100((wb1 + wb2 + wb3 + wb4) / 4))
                economic_stability_score = round(convert_to_100((es1 + es2 + es3) / 3))
                progression_score = round(convert_to_100((pr1 + pr2 + pr3) / 3))
                
                try:
                    supabase.table("candidate_checkins").insert({
                        "placement_id": placement["id"],
                        "partner_id": placement["partner_id"],
                        "milestone_month": milestone,
                        "self_efficacy_score": self_efficacy_score,
                        "work_readiness_score": work_readiness_score,
                        "social_capital_score": social_capital_score,
                        "wellbeing_score": wellbeing_score,
                        "economic_stability_score": economic_stability_score,
                        "progression_score": progression_score,
                        "overall_feeling": overall,
                        "best_thing": best_thing,
                        "challenges": challenges,
                        "support_needed": support_needed,
                        "submitted_at": datetime.now().isoformat()
                    }).execute()
                    
                    # Also update milestone_reviews_candidate for compatibility
                    supabase.table("milestone_reviews_candidate").insert({
                        "placement_id": placement["id"],
                        "milestone_month": milestone,
                        "current_psych_safety": round((wb1 + wb2 + wb3 + wb4) / 4),
                        "improvement_quote": best_thing,
                        "submitted_at": datetime.now().isoformat()
                    }).execute()
                    
                    st.success("Check-in submitted successfully")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

def ach_partner_management():
    st.markdown('<p class="main-header">Partner Management</p>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["Employment Partners", "Training Partners"])
    
    with tab1:
        st.markdown('<p class="section-header">Employment Partners</p>', unsafe_allow_html=True)
        
        partners = [
            {"id": 1, "name": "DoubleTree by Hilton", "sector": "Hospitality", "placements": 5, "score": 80},
            {"id": 2, "name": "Radisson Blu", "sector": "Hospitality", "placements": 4, "score": 76},
            {"id": 3, "name": "Starbucks", "sector": "Food & Beverage", "placements": 3, "score": 73},
            {"id": 4, "name": "First Bus", "sector": "Transport", "placements": 3, "score": 83},
            {"id": 5, "name": "Pret A Manger", "sector": "Food & Beverage", "placements": 2, "score": 70},
            {"id": 6, "name": "Bristol Waste", "sector": "Environmental", "placements": 3, "score": 78},
        ]
        
        for p in partners:
            level, _, _ = get_benchmark_level(p["score"])
            with st.expander(f"**{p['name']}** — {p['sector']} · {p['placements']} placements · Score: {p['score']}"):
                st.write(f"Performance Tier: **{level}**")
                st.write(f"Login: `{p['name'].lower().replace(' ', '').replace('by', '')[:10]}` / `partner123`")
                if st.button(f"View Full Dashboard", key=f"view_{p['id']}"):
                    st.info("In production, this would open the partner's dashboard view")
    
    with tab2:
        st.markdown('<p class="section-header">Training Partners</p>', unsafe_allow_html=True)
        
        partners = [
            {"id": 101, "name": "NHS Bristol Trust", "trained": 45, "score": 75},
            {"id": 102, "name": "Bristol City Council", "trained": 28, "score": 68},
            {"id": 103, "name": "University of Bristol", "trained": 14, "score": 82},
        ]
        
        for p in partners:
            level, _, _ = get_benchmark_level(p["score"])
            with st.expander(f"**{p['name']}** · {p['trained']} trained · Score: {p['score']}"):
                st.write(f"Performance Tier: **{level}**")

def ach_reports():
    st.markdown('<p class="main-header">Reports & Export</p>', unsafe_allow_html=True)
    
    st.markdown('<p class="section-header">Generate Reports</p>', unsafe_allow_html=True)
    
    report_type = st.selectbox("Report Type", [
        "Partner Impact Report",
        "Programme Summary (Employment)",
        "Programme Summary (Training)",
        "Funder Report",
        "Data Export"
    ])
    
    if report_type == "Partner Impact Report":
        partner = st.selectbox("Select Partner", [
            "DoubleTree by Hilton", "Radisson Blu", "Starbucks", 
            "First Bus", "Pret A Manger", "Bristol Waste",
            "NHS Bristol Trust", "Bristol City Council", "University of Bristol"
        ])
        period = st.selectbox("Period", ["Q4 2024", "Q3 2024", "Full Year 2024"])
    
    if st.button("Generate Report", use_container_width=True):
        st.success("Report generated. Download will begin shortly.")
        st.markdown("""
        **Report Preview:**
        
        This would generate a PDF/DOCX report containing:
        - Executive summary
        - Key metrics and scores
        - Trend analysis
        - Candidate/staff outcomes
        - Recommendations
        """)

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
            page = st.radio("", ["Dashboard", "Candidate Check-ins", "Partner Management", "Reports"], label_visibility="collapsed")
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
        {"Dashboard": ach_dashboard, "Candidate Check-ins": ach_candidate_checkins, "Partner Management": ach_partner_management, "Reports": ach_reports}[page]()
    elif st.session_state.partner_type == "employment":
        {"Dashboard": employment_dashboard, "Baseline Data": employment_baseline, "Interview Feedback": employment_interviews, "Milestone Reviews": employment_milestones}[page]()
    elif st.session_state.partner_type == "training":
        {"Dashboard": training_dashboard, "Pre-Training Survey": training_pre_survey, "Post-Training Survey": training_post_survey, "3-Month Follow-up": training_followup, "Infrastructure": training_infrastructure}[page]()

if __name__ == "__main__":
    main()
