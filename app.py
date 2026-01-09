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

st.set_page_config(page_title="ACH Impact Intelligence", page_icon="🌍", layout="wide", initial_sidebar_state="expanded")

# ============ STYLING ============
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    * { font-family: 'Inter', sans-serif; }
    .main-header { font-size: 2.2rem; font-weight: 700; color: #1e293b; margin-bottom: 0.25rem; }
    .sub-header { font-size: 1rem; color: #64748b; margin-bottom: 2rem; }
    .metric-container { background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%); border: 1px solid #e2e8f0; border-radius: 16px; padding: 24px; margin-bottom: 16px; }
    .metric-value { font-size: 2.5rem; font-weight: 700; color: #0f172a; line-height: 1; }
    .metric-label { font-size: 0.8rem; color: #64748b; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 8px; }
    .metric-delta { font-size: 0.85rem; color: #10b981; font-weight: 500; margin-top: 8px; }
    .section-header { font-size: 1.25rem; font-weight: 600; color: #1e293b; margin: 2rem 0 1rem 0; padding-bottom: 0.5rem; border-bottom: 2px solid #e2e8f0; }
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
    .form-section { background: #f8fafc; border-radius: 12px; padding: 24px; margin: 16px 0; border: 1px solid #e2e8f0; }
    [data-testid="stSidebar"] { background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%); }
    [data-testid="stSidebar"] .stMarkdown { color: white; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { background-color: #f1f5f9; border-radius: 8px; padding: 8px 16px; }
    .stTabs [aria-selected="true"] { background-color: #0f172a; color: white; }
</style>
""", unsafe_allow_html=True)

# ============ SESSION STATE ============
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_type' not in st.session_state:
    st.session_state.user_type = None
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'user_name' not in st.session_state:
    st.session_state.user_name = None

USERS = {
    "ach_admin": {"password": "impact2024", "type": "ach_staff", "name": "ACH Administrator"},
    "partner_demo": {"password": "partner123", "type": "partner", "name": "Grand Hotel Birmingham", "partner_id": 2},
    "hospital_demo": {"password": "hospital123", "type": "partner", "name": "Birmingham City Hospital NHS Trust", "partner_id": 1},
    "care_demo": {"password": "care123", "type": "partner", "name": "Sunrise Care Home", "partner_id": 3},
}

# ============ LOGIN ============
def login_page():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("")
        st.markdown('<p class="main-header">🌍 ACH Impact Intelligence</p>', unsafe_allow_html=True)
        st.markdown('<p class="sub-header">Track, measure and report on employment partnership impact</p>', unsafe_allow_html=True)
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Sign In", use_container_width=True):
                if username in USERS and USERS[username]["password"] == password:
                    st.session_state.logged_in = True
                    st.session_state.user_type = USERS[username]["type"]
                    st.session_state.user_name = USERS[username]["name"]
                    if "partner_id" in USERS[username]:
                        st.session_state.user_id = USERS[username]["partner_id"]
                    st.rerun()
                else:
                    st.error("Invalid credentials")
        st.markdown("---")
        st.caption("Demo: `hospital_demo`/`hospital123` or `ach_admin`/`impact2024`")

# ============ METRICS CALCULATION ============
def calculate_metrics(partner_id):
    m = {"total": 0, "active": 0, "retention": 0, "baseline": 0, "improvement": 0, "progressions": 0, "training": 0, "living_wage": 0, "savings": 0, "hard_roles": 0, "tenure": 0, "employer_quotes": [], "candidate_quotes": [], "placements": []}
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
        
        if placements.data:
            for p in placements.data:
                cr = supabase.table("milestone_reviews_candidate").select("*").eq("placement_id", p["id"]).execute()
                if cr.data:
                    m["candidate_quotes"].extend([(c.get("improvement_quote"), p.get("candidate_name")) for c in cr.data if c.get("improvement_quote")])
        
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

def get_candidates_awaiting_feedback(partner_id):
    """Get candidates who have been interviewed but no feedback submitted"""
    awaiting = []
    try:
        # Get all placements for this partner
        placements = supabase.table("placements").select("*").eq("partner_id", partner_id).execute()
        if placements.data:
            for p in placements.data:
                # Check if feedback exists
                feedback = supabase.table("interview_feedback").select("id").eq("partner_id", partner_id).eq("candidate_id", p.get("candidate_id")).execute()
                if not feedback.data:
                    awaiting.append(p)
    except:
        pass
    return awaiting

# ============ PARTNER DASHBOARD ============
def partner_dashboard():
    st.markdown('<p class="main-header">📊 Impact Dashboard</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="sub-header">{st.session_state.user_name}</p>', unsafe_allow_html=True)
    
    partner_id = st.session_state.get("user_id", 1)
    m = calculate_metrics(partner_id)
    
    # Metrics row 1
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'<div class="metric-container"><div class="metric-label">People Employed</div><div class="metric-value">{m["active"]}</div><div class="metric-delta">of {m["total"]} placed</div></div>', unsafe_allow_html=True)
    with col2:
        delta_text = f'+{m["improvement"]}%' if m["improvement"] >= 0 else f'{m["improvement"]}%'
        st.markdown(f'<div class="metric-container"><div class="metric-label">Retention Rate</div><div class="metric-value">{m["retention"]}%</div><div class="metric-delta">{delta_text} vs baseline</div></div>', unsafe_allow_html=True)
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
        st.markdown('<p class="section-header">⚠️ Action Required</p>', unsafe_allow_html=True)
        st.markdown('<div class="info-card">Complete these reviews to maintain your impact reporting. Without timely data, your quarterly report cannot be generated.</div>', unsafe_allow_html=True)
        for p in pending[:3]:
            st.markdown(f'<div class="alert-card"><strong>{p["name"]}</strong> ({p["role"]}) — {p["milestone"]}-month review due</div>', unsafe_allow_html=True)
        if len(pending) > 3:
            st.caption(f"+ {len(pending) - 3} more reviews pending")
    
    # Success stories
    if m["employer_quotes"]:
        st.markdown('<p class="section-header">💬 Success Stories</p>', unsafe_allow_html=True)
        cols = st.columns(2)
        for i, (q, n) in enumerate(m["employer_quotes"][:4]):
            with cols[i % 2]:
                author = f'<div class="quote-author">— About {n}</div>' if n else ''
                st.markdown(f'<div class="quote-card"><div class="quote-text">"{q}"</div>{author}</div>', unsafe_allow_html=True)
    
    # Candidate voices
    if m["candidate_quotes"]:
        st.markdown('<p class="section-header">🌟 In Their Own Words</p>', unsafe_allow_html=True)
        cols = st.columns(2)
        for i, (q, n) in enumerate(m["candidate_quotes"][:4]):
            with cols[i % 2]:
                author = f'<div class="quote-author">— {n}</div>' if n else ''
                st.markdown(f'<div class="quote-card candidate-quote"><div class="quote-text">"{q}"</div>{author}</div>', unsafe_allow_html=True)
    
    # Team list
    st.markdown('<p class="section-header">👥 Your Team</p>', unsafe_allow_html=True)
    if m["placements"]:
        for p in m["placements"]:
            status = "✅" if p.get("status") == "Active" else "⚪"
            st.markdown(f"{status} **{p['candidate_name']}** — {p['role']} (Started {p.get('start_date', 'N/A')})")
    else:
        st.info("No placements yet. Once candidates are hired, they will appear here.")

# ============ PARTNER BASELINE DATA ============
def partner_baseline():
    st.markdown('<p class="main-header">📋 Baseline Data</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Role information helps us measure your recruitment improvements</p>', unsafe_allow_html=True)
    
    partner_id = st.session_state.get("user_id", 1)
    
    # Show existing roles
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
    
    # Add new role form
    st.markdown('<p class="section-header">Add New Role</p>', unsafe_allow_html=True)
    st.markdown('<div class="info-card">Adding baseline data for each role helps us accurately measure the impact of your partnership — comparing outcomes against your typical experience.</div>', unsafe_allow_html=True)
    
    with st.form("baseline_form"):
        col1, col2 = st.columns(2)
        with col1:
            role_title = st.text_input("Role Title *", placeholder="e.g. Healthcare Assistant")
            salary = st.number_input("Annual Salary (£) *", min_value=15000, max_value=100000, value=24000, step=500)
            retention = st.slider("What percentage of staff typically stay beyond 12 months in this role?", 0, 100, 60, help="Your historical retention rate for this position")
        with col2:
            difficulty = st.selectbox("How difficult is this role to fill?", ["Easy - Usually filled within 2 weeks", "Moderate - Takes 2-4 weeks", "Hard - Takes 1-2 months", "Very Hard - Takes 2+ months or often unfilled"])
            vacancy_time = st.selectbox("How long does this role typically stay vacant?", ["Less than 2 weeks", "2-4 weeks", "1-2 months", "2-3 months", "3+ months"])
            living_wage = st.selectbox("Is this role paid at or above Real Living Wage (£12/hr)?", ["Yes", "No"])
            permanent = st.selectbox("Contract type", ["Permanent", "Fixed-term", "Variable"])
        
        if st.form_submit_button("Save Role", use_container_width=True):
            if role_title:
                difficulty_map = {"Easy - Usually filled within 2 weeks": "Easy", "Moderate - Takes 2-4 weeks": "Moderate", "Hard - Takes 1-2 months": "Hard", "Very Hard - Takes 2+ months or often unfilled": "Very Hard"}
                try:
                    supabase.table("partner_baseline").insert({
                        "partner_id": partner_id,
                        "role_title": role_title,
                        "salary": salary,
                        "retention_rate": retention,
                        "difficulty": difficulty_map.get(difficulty, difficulty),
                        "vacancy_time": vacancy_time,
                        "living_wage": living_wage == "Yes",
                        "permanent": permanent,
                        "created_at": datetime.now().isoformat()
                    }).execute()
                    st.success(f"✓ {role_title} saved successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error saving: {e}")
            else:
                st.warning("Please enter a role title")

# ============ PARTNER INTERVIEW FEEDBACK ============
def partner_interview_feedback():
    st.markdown('<p class="main-header">🎤 Interview Feedback</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Record outcomes for each candidate interviewed</p>', unsafe_allow_html=True)
    
    partner_id = st.session_state.get("user_id", 1)
    
    # Show existing feedback summary
    try:
        feedback = supabase.table("interview_feedback").select("*").eq("partner_id", partner_id).execute()
        if feedback.data:
            hired = len([f for f in feedback.data if f.get("hired")])
            not_hired = len([f for f in feedback.data if not f.get("hired")])
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Interviewed", len(feedback.data))
            with col2:
                st.metric("Hired", hired)
            with col3:
                st.metric("Not Hired", not_hired)
            
            st.markdown("**Recent Feedback:**")
            for f in sorted(feedback.data, key=lambda x: x.get("interview_date", ""), reverse=True)[:5]:
                status = "✅ Hired" if f.get("hired") else "❌ Not hired"
                st.write(f"- **{f.get('candidate_name')}** for {f.get('role')} — {status} ({f.get('interview_date', 'N/A')})")
    except:
        pass
    
    # Submit new feedback
    st.markdown('<p class="section-header">Submit Interview Feedback</p>', unsafe_allow_html=True)
    st.markdown('<div class="info-card">Your feedback helps ACH continuously improve candidate preparation and provides valuable data for impact measurement.</div>', unsafe_allow_html=True)
    
    with st.form("interview_feedback_form"):
        col1, col2 = st.columns(2)
        with col1:
            candidate_name = st.text_input("Candidate Name *", placeholder="e.g. Ahmed Hassan")
            candidate_id = st.text_input("Candidate ID (if known)", placeholder="e.g. BCH001")
            role = st.text_input("Role Interviewed For *", placeholder="e.g. Healthcare Assistant")
        with col2:
            interview_date = st.date_input("Interview Date *", value=datetime.now())
            hired = st.selectbox("Outcome *", ["Yes - We are hiring this candidate", "No - We are not proceeding"])
        
        st.markdown("---")
        
        if hired == "Yes - We are hiring this candidate":
            st.markdown("**🎉 Great news! Please tell us more:**")
            standout = st.text_area("What made this candidate stand out? *", placeholder="e.g. Excellent communication skills, showed genuine empathy during role play, asked thoughtful questions about the role...", help="This helps ACH understand what qualities employers value and informs future training")
            start_date = st.date_input("Expected Start Date", value=datetime.now() + timedelta(days=14))
            salary = st.number_input("Agreed Salary (£/year)", min_value=15000, max_value=100000, value=24000, step=500)
            rejection_reason = None
            improvement = None
        else:
            st.markdown("**📝 Please help us improve:**")
            rejection_reason = st.selectbox("Primary reason for not proceeding", [
                "Skills gap - technical skills need development",
                "English language proficiency",
                "Experience level not sufficient",
                "Cultural fit concerns",
                "Availability/shift patterns",
                "Right to work documentation",
                "Other"
            ])
            improvement = st.text_area("What could ACH do to better prepare candidates like this? *", placeholder="e.g. More focus on interview techniques, additional English language support, more exposure to workplace scenarios...", help="Your constructive feedback directly improves our training programmes")
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
                    
                    # If hired, create placement
                    if hired == "Yes - We are hiring this candidate" and start_date and salary:
                        partner_name = st.session_state.user_name
                        hourly = round(salary / 1950, 2)
                        placement_data = {
                            "partner_id": partner_id,
                            "partner_name": partner_name,
                            "candidate_id": candidate_id or data["candidate_id"],
                            "candidate_name": candidate_name,
                            "role": role,
                            "start_date": start_date.isoformat(),
                            "salary": salary,
                            "hourly_rate": hourly,
                            "contract_type": "Permanent",
                            "status": "Active",
                            "created_at": datetime.now().isoformat()
                        }
                        supabase.table("placements").insert(placement_data).execute()
                        st.success(f"✓ Feedback submitted and {candidate_name} added to your team!")
                    else:
                        st.success("✓ Feedback submitted. Thank you for helping us improve.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                st.warning("Please complete all required fields")

# ============ PARTNER MILESTONE REVIEWS ============
def partner_milestone_reviews():
    st.markdown('<p class="main-header">📅 Milestone Reviews</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Provide updates on employee progress at 3, 6 and 12 months</p>', unsafe_allow_html=True)
    
    partner_id = st.session_state.get("user_id", 1)
    pending = get_pending_reviews(partner_id)
    
    # Show completed reviews count
    try:
        completed = supabase.table("milestone_reviews_partner").select("id").eq("partner_id", partner_id).execute()
        st.metric("Reviews Completed", len(completed.data) if completed.data else 0)
    except:
        pass
    
    if not pending:
        st.markdown('<div class="success-card">✓ All milestone reviews are up to date!</div>', unsafe_allow_html=True)
        return
    
    st.markdown('<div class="info-card">Milestone reviews are essential for tracking employee progress and generating your impact reports. Please complete all pending reviews.</div>', unsafe_allow_html=True)
    
    st.markdown(f'<p class="section-header">⚠️ {len(pending)} Review(s) Pending</p>', unsafe_allow_html=True)
    
    for review in pending:
        with st.expander(f"**{review['name']}** — {review['milestone']}-month review", expanded=len(pending)==1):
            st.write(f"**Role:** {review['role']}")
            st.write(f"**Start Date:** {review['start_date']}")
            
            with st.form(f"review_{review['placement_id']}_{review['milestone']}"):
                st.markdown("##### Employment Status")
                still_employed = st.selectbox("Is this employee still working with you?", ["Yes", "No"], key=f"emp_{review['placement_id']}_{review['milestone']}")
                
                if still_employed == "No":
                    leaving_date = st.date_input("When did they leave?", key=f"leave_date_{review['placement_id']}_{review['milestone']}")
                    leaving_reason = st.selectbox("Reason for leaving", ["Resigned - personal reasons", "Resigned - found other employment", "Resigned - returned to education", "Contract ended", "Performance issues", "Redundancy", "Other"], key=f"leave_reason_{review['placement_id']}_{review['milestone']}")
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
                    
                    st.markdown("##### Performance & Development")
                    performance = st.selectbox("How would you rate their overall performance?", ["Excellent - Exceeds expectations", "Good - Meets all expectations", "Satisfactory - Meets most expectations", "Needs improvement"], key=f"perf_{review['placement_id']}_{review['milestone']}")
                    
                    training = st.selectbox("Have they received any training since starting/last review?", ["Yes", "No"], key=f"train_{review['placement_id']}_{review['milestone']}")
                    training_type = None
                    if training == "Yes":
                        training_type = st.text_input("What training did they complete?", placeholder="e.g. Manual handling, Food safety Level 2", key=f"train_type_{review['placement_id']}_{review['milestone']}")
                    
                    progression = st.selectbox("Has this employee received a promotion, pay rise, or increased responsibilities?", ["Yes", "No"], key=f"prog_{review['placement_id']}_{review['milestone']}")
                    progression_details = None
                    if progression == "Yes":
                        progression_details = st.text_input("Please describe", placeholder="e.g. Promoted to Senior HCA, Pay increased to £25,000", key=f"prog_detail_{review['placement_id']}_{review['milestone']}")
                    
                    st.markdown("##### Support Provided")
                    support = st.multiselect("What support have you provided?", ["Mentoring or buddy system", "Language support", "Additional training", "Flexible working arrangements", "Reasonable adjustments", "Wellbeing support", "Other"], key=f"support_{review['placement_id']}_{review['milestone']}")
                    
                    st.markdown("##### Success Story")
                    quote = st.text_area("Share a success story or highlight about this employee (optional)", placeholder="e.g. Ahmed has become indispensable on our ward. Patients ask for him by name and his colleagues rely on him.", key=f"quote_{review['placement_id']}_{review['milestone']}", help="These stories feature in your impact reports and help demonstrate the value of the partnership")
                
                if st.form_submit_button("Submit Review", use_container_width=True):
                    try:
                        perf_map = {"Excellent - Exceeds expectations": "Excellent", "Good - Meets all expectations": "Good", "Satisfactory - Meets most expectations": "Satisfactory", "Needs improvement": "Needs improvement"}
                        data = {
                            "placement_id": review['placement_id'],
                            "partner_id": partner_id,
                            "milestone_month": review['milestone'],
                            "still_employed": still_employed == "Yes",
                            "leaving_date": leaving_date.isoformat() if leaving_date else None,
                            "leaving_reason": leaving_reason,
                            "performance": perf_map.get(performance, performance) if performance else None,
                            "received_training": training == "Yes" if training else False,
                            "training_type": training_type,
                            "progression": progression == "Yes" if progression else False,
                            "progression_details": progression_details,
                            "support_provided": json.dumps(support) if support else None,
                            "contribution_quote": quote,
                            "submitted_at": datetime.now().isoformat()
                        }
                        supabase.table("milestone_reviews_partner").insert(data).execute()
                        
                        # Update placement status if left
                        if still_employed == "No":
                            supabase.table("placements").update({"status": "Left"}).eq("id", review['placement_id']).execute()
                        
                        st.success("✓ Review submitted successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

# ============ PARTNER REPORTS ============
def partner_reports():
    st.markdown('<p class="main-header">📑 Impact Report</p>', unsafe_allow_html=True)
    m = calculate_metrics(st.session_state.get("user_id", 1))
    
    if m["total"] == 0:
        st.warning("No data yet. Once you have placed candidates and submitted reviews, your impact report will be generated here.")
        return
    
    st.markdown(f'''<div class="highlight-card">
        <div style="display:flex;justify-content:space-between;align-items:center;">
            <div><div style="opacity:0.8;font-size:0.9rem;">IMPACT REPORT Q4 2024</div><div style="font-size:1.3rem;font-weight:600;margin-top:4px;">{st.session_state.user_name}</div></div>
            <div style="text-align:right;"><div class="highlight-value">{m["active"]}</div><div class="highlight-label">Lives Changed</div></div>
        </div>
    </div>''', unsafe_allow_html=True)
    
    st.markdown("### Executive Summary")
    st.markdown(f"""Through your partnership with ACH's Bridge to Employment programme, your organisation has created **{m["total"]} employment opportunities** for talented individuals from refugee and migrant backgrounds.

**Key Achievements:**
- 📈 **{m["retention"]}% retention rate** — {m["improvement"]}% above your baseline
- 💰 **£{m["savings"]:,} estimated savings** from reduced turnover
- 🎓 **{m["training"]} training completions** invested in development
- ⭐ **{m["progressions"]} career progressions** including promotions and pay rises
- ✓ **{m["living_wage"]}% living wage roles** demonstrating fair pay commitment""")
    
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
    
    if m["employer_quotes"]:
        st.markdown("### Success Stories")
        for q, n in m["employer_quotes"][:3]:
            st.markdown(f'> "{q}"')
            if n:
                st.caption(f"— About {n}")
    
    if m["candidate_quotes"]:
        st.markdown("### Employee Voices")
        for q, n in m["candidate_quotes"][:3]:
            st.markdown(f'> "{q}"')
            if n:
                st.caption(f"— {n}")
    
    st.markdown("### Diversity & Inclusion Impact")
    st.markdown(f"""Your organisation has welcomed **{m['active']} employees** from refugee and migrant backgrounds, demonstrating genuine commitment to workforce diversity and inclusive hiring practices.""")
    
    st.markdown("---")
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.button("📥 Download Full Report (PDF)", use_container_width=True, disabled=True, help="PDF generation coming soon")

# ============ ACH STAFF DASHBOARD ============
def ach_dashboard():
    st.markdown('<p class="main-header">📊 Programme Dashboard</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Overview of all partnerships and placements</p>', unsafe_allow_html=True)
    
    try:
        partners = supabase.table("impact_partners").select("*").execute()
        placements = supabase.table("placements").select("*").execute()
        reviews = supabase.table("milestone_reviews_partner").select("*").execute()
        
        total_p = len(partners.data) if partners.data else 0
        total_pl = len(placements.data) if placements.data else 0
        active = len([p for p in placements.data if p.get("status") == "Active"]) if placements.data else 0
        retention = round((active / total_pl) * 100) if total_pl > 0 else 0
        progs = len([r for r in reviews.data if r.get("progression")]) if reviews.data else 0
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f'<div class="metric-container"><div class="metric-label">Partners</div><div class="metric-value">{total_p}</div></div>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div class="metric-container"><div class="metric-label">Placements</div><div class="metric-value">{total_pl}</div><div class="metric-delta">{active} active</div></div>', unsafe_allow_html=True)
        with col3:
            st.markdown(f'<div class="metric-container"><div class="metric-label">Retention</div><div class="metric-value">{retention}%</div></div>', unsafe_allow_html=True)
        with col4:
            st.markdown(f'<div class="metric-container"><div class="metric-label">Progressions</div><div class="metric-value">{progs}</div></div>', unsafe_allow_html=True)
        
        st.markdown('<p class="section-header">Partner Performance</p>', unsafe_allow_html=True)
        for partner in (partners.data or []):
            pp = [p for p in (placements.data or []) if p.get("partner_id") == partner["id"]]
            pa = len([p for p in pp if p.get("status") == "Active"])
            pr = round((pa / len(pp)) * 100) if pp else 0
            with st.expander(f"**{partner['name']}** — {len(pp)} placements, {pr}% retention"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Sector:** {partner.get('sector')}")
                    st.write(f"**Contact:** {partner.get('contact_name')}")
                    st.write(f"**Email:** {partner.get('contact_email')}")
                with col2:
                    st.write(f"**Employees:** {partner.get('employee_count')}")
                    st.write(f"**Tier:** {partner.get('subscription_tier')}")
                    st.write(f"**Since:** {partner.get('created_at', 'N/A')[:10]}")
        
        st.markdown('<p class="section-header">Recent Placements</p>', unsafe_allow_html=True)
        recent = sorted(placements.data or [], key=lambda x: x.get("start_date", ""), reverse=True)[:8]
        for p in recent:
            st.write(f"{'✅' if p.get('status')=='Active' else '⚪'} **{p['candidate_name']}** — {p['role']} at {p['partner_name']} ({p.get('start_date', 'N/A')})")
    except Exception as e:
        st.error(f"Error: {e}")

# ============ ACH CANDIDATE SUPPORT ============
def ach_candidate_support():
    st.markdown('<p class="main-header">👥 Candidate Support</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Record candidate check-ins and wellbeing data</p>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["Pending Check-ins", "Submit Check-in"])
    
    with tab1:
        try:
            placements = supabase.table("placements").select("*").eq("status", "Active").execute()
            if placements.data:
                pending = []
                for p in placements.data:
                    if p.get("start_date"):
                        months = (datetime.now() - datetime.fromisoformat(p["start_date"])).days / 30
                        for m in [3, 6, 12]:
                            if months >= m:
                                rev = supabase.table("milestone_reviews_candidate").select("id").eq("placement_id", p["id"]).eq("milestone_month", m).execute()
                                if not rev.data:
                                    pending.append({"placement": p, "milestone": m})
                
                if pending:
                    st.warning(f"{len(pending)} candidate check-in(s) due")
                    for item in pending[:10]:
                        p = item["placement"]
                        st.write(f"⏰ **{p['candidate_name']}** at {p['partner_name']} — {item['milestone']}-month check-in due")
                else:
                    st.success("✓ All candidate check-ins are up to date!")
            else:
                st.info("No active placements")
        except Exception as e:
            st.error(f"Error: {e}")
    
    with tab2:
        st.markdown('<div class="info-card">Candidate check-ins capture wellbeing, psychological safety, and career development data directly from employees.</div>', unsafe_allow_html=True)
        
        try:
            placements = supabase.table("placements").select("*").eq("status", "Active").execute()
            if placements.data:
                placement_options = {f"{p['candidate_name']} at {p['partner_name']}": p for p in placements.data}
                selected = st.selectbox("Select Candidate", options=list(placement_options.keys()))
                placement = placement_options[selected]
                
                months_employed = (datetime.now() - datetime.fromisoformat(placement["start_date"])).days / 30
                milestone = st.selectbox("Milestone", [3, 6, 12])
                
                if months_employed < milestone:
                    st.warning(f"This candidate has only been employed {months_employed:.1f} months. {milestone}-month check-in not yet due.")
                else:
                    with st.form("candidate_checkin"):
                        st.markdown("##### Psychological Safety")
                        safe_self = st.select_slider("I feel safe to be myself at work", ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"], value="Agree")
                        respected = st.select_slider("I feel respected by my colleagues and managers", ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"], value="Agree")
                        welcoming = st.select_slider("My workplace is welcoming and inclusive", ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"], value="Agree")
                        
                        st.markdown("##### Economic Wellbeing")
                        col1, col2 = st.columns(2)
                        with col1:
                            hourly = st.number_input("Current hourly rate (£)", min_value=8.0, max_value=30.0, value=float(placement.get("hourly_rate", 12.0)), step=0.25)
                            contract = st.selectbox("Contract type", ["Permanent", "Fixed-term", "Zero-hours", "Variable"])
                        with col2:
                            hours = st.number_input("Weekly hours", min_value=0, max_value=60, value=37)
                            enough_hours = st.selectbox("Are you getting enough hours?", ["Yes", "No - I want more", "No - I want fewer"])
                        
                        st.markdown("##### Development")
                        training = st.selectbox("Have you received any training?", ["Yes", "No"])
                        training_type = st.text_input("If yes, what training?", placeholder="e.g. Manual handling, Food safety") if training == "Yes" else None
                        confidence = st.select_slider("My confidence has grown since starting", ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"], value="Agree")
                        
                        st.markdown("##### Overall Wellbeing")
                        overall = st.select_slider("Overall, how do you feel about your job?", ["Very Negative", "Negative", "Neutral", "Positive", "Very Positive"], value="Positive")
                        quote = st.text_area("Is there anything you would like to share about your experience?", placeholder="e.g. This job has changed my life. I wake up excited to go to work...")
                        
                        st.markdown("##### Capability Assessment")
                        st.caption("Rate current capability (1-5)")
                        col1, col2 = st.columns(2)
                        with col1:
                            efficacy = st.slider("Self-efficacy (confidence in abilities)", 1, 5, 4)
                            readiness = st.slider("Work readiness", 1, 5, 4)
                            language = st.slider("Language confidence", 1, 5, 4)
                        with col2:
                            digital = st.slider("Digital skills", 1, 5, 4)
                            psych = st.slider("Psychological safety", 1, 5, 4)
                        
                        if st.form_submit_button("Submit Check-in", use_container_width=True):
                            try:
                                data = {
                                    "placement_id": placement["id"],
                                    "milestone_month": milestone,
                                    "safe_to_be_self": safe_self,
                                    "feel_respected": respected,
                                    "workplace_welcoming": welcoming,
                                    "hourly_rate": hourly,
                                    "contract_type": contract,
                                    "weekly_hours": hours,
                                    "enough_hours": enough_hours,
                                    "received_training": training == "Yes",
                                    "training_type": training_type,
                                    "confidence_growth": confidence,
                                    "overall_feeling": overall,
                                    "improvement_quote": quote,
                                    "current_self_efficacy": efficacy,
                                    "current_work_readiness": readiness,
                                    "current_language": language,
                                    "current_digital": digital,
                                    "current_psych_safety": psych,
                                    "submitted_at": datetime.now().isoformat()
                                }
                                supabase.table("milestone_reviews_candidate").insert(data).execute()
                                st.success("✓ Check-in submitted!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")
        except Exception as e:
            st.error(f"Error loading placements: {e}")

# ============ ACH PARTNERS ============
def ach_partners():
    st.markdown('<p class="main-header">🏢 Partner Organisations</p>', unsafe_allow_html=True)
    
    try:
        data = supabase.table("impact_partners").select("*").execute()
        for p in (data.data or []):
            with st.expander(f"**{p['name']}** — {p.get('sector', 'N/A')}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Contact:** {p.get('contact_name')}")
                    st.write(f"**Email:** {p.get('contact_email')}")
                    st.write(f"**Phone:** {p.get('contact_phone')}")
                with col2:
                    st.write(f"**Employees:** {p.get('employee_count')}")
                    st.write(f"**Tier:** {p.get('subscription_tier')}")
                    st.write(f"**Since:** {p.get('created_at', '')[:10] if p.get('created_at') else 'N/A'}")
    except Exception as e:
        st.error(f"Error: {e}")

# ============ NAVIGATION ============
def main():
    if not st.session_state.logged_in:
        login_page()
        return
    
    with st.sidebar:
        st.markdown("### 🌍 Impact Intelligence")
        st.markdown(f"**{st.session_state.user_name}**")
        st.markdown("---")
        
        if st.session_state.user_type == "ach_staff":
            page = st.radio("Navigation", ["Dashboard", "Partners", "Candidate Support"], label_visibility="collapsed")
        else:
            page = st.radio("Navigation", ["Dashboard", "Baseline Data", "Interview Feedback", "Milestone Reviews", "Impact Report"], label_visibility="collapsed")
        
        st.markdown("---")
        if st.button("Logout", use_container_width=True):
            for k in ["logged_in", "user_type", "user_id", "user_name"]:
                st.session_state[k] = None if k != "logged_in" else False
            st.rerun()
        
        st.markdown("---")
        st.caption("Powered by ACH")
    
    if st.session_state.user_type == "ach_staff":
        {"Dashboard": ach_dashboard, "Partners": ach_partners, "Candidate Support": ach_candidate_support}[page]()
    else:
        {"Dashboard": partner_dashboard, "Baseline Data": partner_baseline, "Interview Feedback": partner_interview_feedback, "Milestone Reviews": partner_milestone_reviews, "Impact Report": partner_reports}[page]()

if __name__ == "__main__":
    main()
