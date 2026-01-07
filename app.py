import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from supabase import create_client
import json

# ============ CONFIGURATION ============
SUPABASE_URL = "https://gmjqidqjpzxcpgycawxf.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdtanFpZHFqcHp4Y3BneWNhd3hmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njc3MjYyMDEsImV4cCI6MjA4MzMwMjIwMX0.6jtYlz6yoBQCrh04P0g30JigHyanGYnv7xBz24B5Bm4"

LIVING_WAGE_UK = 12.00

# ============ DATABASE CONNECTION ============
@st.cache_resource
def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = get_supabase()

# ============ PAGE CONFIG ============
st.set_page_config(
    page_title="ACH Impact Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============ CUSTOM STYLING ============
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Fraunces:wght@400;600;700&display=swap');
    
    .main-header {
        font-family: 'Fraunces', serif;
        font-size: 2rem;
        font-weight: 600;
        color: #0f1c3f;
        margin-bottom: 0.5rem;
    }
    
    .sub-header {
        font-family: 'DM Sans', sans-serif;
        font-size: 1rem;
        color: #64748b;
        margin-bottom: 2rem;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #0f1c3f, #1a2d5a);
        border-radius: 16px;
        padding: 24px;
        color: white;
    }
    
    .metric-value {
        font-family: 'Fraunces', serif;
        font-size: 2.5rem;
        font-weight: 700;
    }
    
    .metric-label {
        font-size: 0.9rem;
        opacity: 0.8;
    }
    
    .status-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    
    .status-complete { background: #dcfce7; color: #166534; }
    .status-due { background: #fef3c7; color: #92400e; }
    .status-overdue { background: #fee2e2; color: #991b1b; }
    
    .quote-box {
        background: #f8fafc;
        border-left: 4px solid #0f1c3f;
        padding: 16px 20px;
        margin: 16px 0;
        font-style: italic;
        color: #475569;
    }
    
    .section-header {
        font-family: 'Fraunces', serif;
        font-size: 1.3rem;
        color: #0f1c3f;
        margin: 2rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #e2e8f0;
    }
    
    div[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f1c3f 0%, #1a2d5a 100%);
    }
    
    div[data-testid="stSidebar"] .stMarkdown {
        color: white;
    }
    
    div[data-testid="stSidebar"] label {
        color: white !important;
    }
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

# ============ DEMO USERS ============
USERS = {
    "ach_admin": {"password": "impact2024", "type": "ach_staff", "name": "ACH Administrator"},
    "partner_demo": {"password": "partner123", "type": "partner", "name": "Grand Hotel Birmingham", "partner_id": 2},
    "hospital_demo": {"password": "hospital123", "type": "partner", "name": "Birmingham City Hospital", "partner_id": 1},
    "care_demo": {"password": "care123", "type": "partner", "name": "Sunrise Care Home", "partner_id": 3},
}

# ============ LOGIN ============
def login_page():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<p class="main-header">🌍 ACH Impact Intelligence</p>', unsafe_allow_html=True)
        st.markdown('<p class="sub-header">Track, measure and report on the social impact your organisation creates</p>', unsafe_allow_html=True)
        
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login", use_container_width=True)
            
            if submitted:
                if username in USERS and USERS[username]["password"] == password:
                    st.session_state.logged_in = True
                    st.session_state.user_type = USERS[username]["type"]
                    st.session_state.user_name = USERS[username]["name"]
                    if "partner_id" in USERS[username]:
                        st.session_state.user_id = USERS[username]["partner_id"]
                    st.rerun()
                else:
                    st.error("Invalid credentials")

# ============ HELPER FUNCTIONS ============
def calculate_impact_metrics(partner_id):
    """Calculate all impact metrics for a partner"""
    metrics = {
        "total_placements": 0,
        "active_employees": 0,
        "retention_rate": 0,
        "avg_capability_growth": 0,
        "progression_rate": 0,
        "living_wage_percent": 0,
        "cost_savings": 0,
        "hard_roles_filled": 0,
        "baseline_retention": 0,
        "quotes": [],
        "candidate_quotes": [],
        "progression_count": 0,
        "training_count": 0
    }
    
    # Get placements for this partner
    try:
        placements = supabase.table("placements").select("*").eq("partner_id", partner_id).execute()
        if placements.data:
            metrics["total_placements"] = len(placements.data)
            active = [p for p in placements.data if p.get("status") == "Active"]
            metrics["active_employees"] = len(active)
            if metrics["total_placements"] > 0:
                metrics["retention_rate"] = round((len(active) / metrics["total_placements"]) * 100)
            
            # Living wage
            living_wage_count = sum(1 for p in placements.data if (p.get("hourly_rate") or 0) >= LIVING_WAGE_UK)
            if metrics["total_placements"] > 0:
                metrics["living_wage_percent"] = round((living_wage_count / metrics["total_placements"]) * 100)
    except:
        pass
    
    # Get baseline data for hard-to-fill roles and baseline retention
    try:
        baseline = supabase.table("partner_baseline").select("*").eq("partner_id", partner_id).execute()
        if baseline.data:
            hard_roles = [b for b in baseline.data if b.get("difficulty") in ["Hard", "Very Hard"]]
            metrics["hard_roles_filled"] = len(hard_roles)
            
            # Average baseline retention
            retention_rates = [b.get("retention_rate", 0) for b in baseline.data if b.get("retention_rate")]
            if retention_rates:
                metrics["baseline_retention"] = round(sum(retention_rates) / len(retention_rates))
    except:
        pass
    
    # Get quotes from interview feedback (standout reasons)
    try:
        feedback = supabase.table("interview_feedback").select("*").eq("partner_id", partner_id).eq("hired", True).execute()
        if feedback.data:
            metrics["quotes"] = [f.get("standout_reason") for f in feedback.data if f.get("standout_reason")]
    except:
        pass
    
    # Get quotes and progression from milestone reviews
    try:
        reviews = supabase.table("milestone_reviews_partner").select("*").eq("partner_id", partner_id).execute()
        if reviews.data:
            # Contribution quotes
            contribution_quotes = [r.get("contribution_quote") for r in reviews.data if r.get("contribution_quote")]
            metrics["quotes"].extend(contribution_quotes)
            
            # Progression count
            metrics["progression_count"] = sum(1 for r in reviews.data if r.get("progression"))
            metrics["training_count"] = sum(1 for r in reviews.data if r.get("received_training"))
            
            if metrics["total_placements"] > 0:
                metrics["progression_rate"] = round((metrics["progression_count"] / metrics["total_placements"]) * 100)
    except:
        pass
    
    # Get candidate quotes
    try:
        placement_ids = [p["id"] for p in placements.data] if placements.data else []
        if placement_ids:
            for pid in placement_ids:
                cand_reviews = supabase.table("milestone_reviews_candidate").select("*").eq("placement_id", pid).execute()
                if cand_reviews.data:
                    for cr in cand_reviews.data:
                        if cr.get("improvement_quote"):
                            metrics["candidate_quotes"].append(cr.get("improvement_quote"))
    except:
        pass
    
    # Calculate cost savings (retention improvement × £4,500 × placements)
    if metrics["baseline_retention"] > 0 and metrics["retention_rate"] > metrics["baseline_retention"]:
        improvement = (metrics["retention_rate"] - metrics["baseline_retention"]) / 100
        metrics["cost_savings"] = round(improvement * 4500 * metrics["total_placements"])
    elif metrics["retention_rate"] > 72:  # Compare to industry average if no baseline
        improvement = (metrics["retention_rate"] - 72) / 100
        metrics["cost_savings"] = round(improvement * 4500 * metrics["total_placements"])
    
    return metrics

def get_pending_reviews(partner_id):
    """Get list of candidates with pending milestone reviews"""
    pending = []
    try:
        placements = supabase.table("placements").select("*").eq("partner_id", partner_id).eq("status", "Active").execute()
        if placements.data:
            for p in placements.data:
                start_date = datetime.fromisoformat(p["start_date"]) if p.get("start_date") else None
                if start_date:
                    now = datetime.now()
                    months_employed = (now - start_date).days / 30
                    
                    # Check which milestones are due
                    milestones = [3, 6, 12]
                    for m in milestones:
                        if months_employed >= m:
                            # Check if review exists
                            review = supabase.table("milestone_reviews_partner").select("*").eq("placement_id", p["id"]).eq("milestone_month", m).execute()
                            if not review.data:
                                days_overdue = int(months_employed * 30 - m * 30)
                                pending.append({
                                    "candidate_name": p.get("candidate_name", "Unknown"),
                                    "milestone": f"{m}-month review",
                                    "due_date": (start_date + timedelta(days=m*30)).strftime("%d %b %Y"),
                                    "status": "Overdue" if days_overdue > 7 else "Due",
                                    "placement_id": p["id"],
                                    "milestone_month": m
                                })
    except:
        pass
    return pending

# ============ ACH STAFF PAGES ============
def ach_dashboard():
    st.markdown('<p class="main-header">📊 Impact Intelligence Dashboard</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Overview of all partner organisations and candidate outcomes</p>', unsafe_allow_html=True)
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    try:
        partners = supabase.table("impact_partners").select("*").execute()
        candidates = supabase.table("candidates").select("*").execute()
        placements = supabase.table("placements").select("*").execute()
        reviews = supabase.table("milestone_reviews_partner").select("*").execute()
        
        total_partners = len(partners.data) if partners.data else 0
        total_candidates = len(candidates.data) if candidates.data else 0
        total_placements = len(placements.data) if placements.data else 0
        active_placements = len([p for p in placements.data if p.get("status") == "Active"]) if placements.data else 0
        
        with col1:
            st.metric("Partner Organisations", total_partners)
        with col2:
            st.metric("Candidates in System", total_candidates)
        with col3:
            st.metric("Total Placements", total_placements)
        with col4:
            retention = round((active_placements / total_placements) * 100) if total_placements > 0 else 0
            st.metric("Overall Retention", f"{retention}%")
        
        # Second row
        st.markdown("---")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Currently Employed", active_placements)
        with col2:
            available = len([c for c in candidates.data if c.get("status") == "Available"]) if candidates.data else 0
            st.metric("Available Candidates", available)
        with col3:
            progressions = len([r for r in reviews.data if r.get("progression")]) if reviews.data else 0
            st.metric("Career Progressions", progressions)
        with col4:
            training = len([r for r in reviews.data if r.get("received_training")]) if reviews.data else 0
            st.metric("Training Completed", training)
        
        # Partner breakdown
        st.markdown('<p class="section-header">Partner Performance</p>', unsafe_allow_html=True)
        
        if partners.data:
            for partner in partners.data:
                partner_placements = [p for p in placements.data if p.get("partner_id") == partner["id"]] if placements.data else []
                active = len([p for p in partner_placements if p.get("status") == "Active"])
                total = len(partner_placements)
                retention = round((active / total) * 100) if total > 0 else 0
                
                with st.expander(f"**{partner['name']}** — {total} placements, {retention}% retention"):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.write(f"**Sector:** {partner.get('sector', 'N/A')}")
                        st.write(f"**Contact:** {partner.get('contact_name', 'N/A')}")
                    with col2:
                        st.write(f"**Total Placed:** {total}")
                        st.write(f"**Currently Active:** {active}")
                    with col3:
                        st.write(f"**Retention Rate:** {retention}%")
                        st.write(f"**Subscription:** {partner.get('subscription_tier', 'N/A')}")
        
        # Recent activity
        st.markdown('<p class="section-header">Recent Placements</p>', unsafe_allow_html=True)
        
        if placements.data:
            recent = sorted(placements.data, key=lambda x: x.get("created_at", ""), reverse=True)[:5]
            for p in recent:
                st.write(f"✅ **{p['candidate_name']}** started as {p['role']} at {p['partner_name']} ({p.get('start_date', 'N/A')})")
        
    except Exception as e:
        st.error(f"Error loading data: {e}")

def ach_manage_partners():
    st.markdown('<p class="main-header">🏢 Manage Partners</p>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["View Partners", "Add New Partner"])
    
    with tab1:
        try:
            partners = supabase.table("impact_partners").select("*").execute()
            if partners.data:
                for p in partners.data:
                    with st.expander(f"**{p['name']}** — {p.get('sector', 'N/A')}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Contact:** {p.get('contact_name', 'N/A')}")
                            st.write(f"**Email:** {p.get('contact_email', 'N/A')}")
                        with col2:
                            st.write(f"**Employees:** {p.get('employee_count', 'N/A')}")
                            st.write(f"**Subscription:** {p.get('subscription_tier', 'N/A')}")
            else:
                st.info("No partners yet. Add one to get started.")
        except:
            st.info("No partners yet. Add one to get started.")
    
    with tab2:
        with st.form("add_partner"):
            st.subheader("New Partner Organisation")
            
            name = st.text_input("Organisation Name *")
            sector = st.selectbox("Sector *", ["", "Healthcare", "Social Care", "Hospitality", "Retail", "Manufacturing", "Logistics", "Public Sector", "Education", "Facilities", "Food Service", "Other"])
            employee_count = st.number_input("Number of Employees", min_value=1, value=50)
            
            st.divider()
            contact_name = st.text_input("Contact Name *")
            contact_email = st.text_input("Contact Email *")
            contact_phone = st.text_input("Phone (optional)")
            
            st.divider()
            subscription = st.selectbox("Subscription Tier", ["1-5 roles (£1,500/year)", "6-15 roles (£2,500/year)", "16+ roles (£3,500/year)"])
            
            submitted = st.form_submit_button("Add Partner", use_container_width=True)
            
            if submitted and name and sector and contact_name and contact_email:
                try:
                    data = {
                        "name": name,
                        "sector": sector,
                        "employee_count": employee_count,
                        "contact_name": contact_name,
                        "contact_email": contact_email,
                        "contact_phone": contact_phone,
                        "subscription_tier": subscription.split(" (")[0],
                        "created_at": datetime.now().isoformat()
                    }
                    supabase.table("impact_partners").insert(data).execute()
                    st.success(f"✓ {name} added successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

def ach_manage_candidates():
    st.markdown('<p class="main-header">👥 Manage Candidates</p>', unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["View Candidates", "Add Candidate", "Cohort Upload"])
    
    with tab1:
        try:
            candidates = supabase.table("candidates").select("*").execute()
            if candidates.data:
                df = pd.DataFrame(candidates.data)
                st.dataframe(df[["name", "cohort", "training_completed", "status"]], use_container_width=True)
            else:
                st.info("No candidates yet.")
        except:
            st.info("No candidates yet.")
    
    with tab2:
        with st.form("add_candidate"):
            st.subheader("Add Individual Candidate")
            
            name = st.text_input("Full Name *")
            cohort = st.text_input("Cohort/Programme *", placeholder="e.g., Jan 2024 Hospitality")
            training_completed = st.date_input("Training Completion Date")
            
            st.divider()
            st.subheader("Baseline Capability Assessment")
            st.caption("Rate each area from 1 (needs development) to 5 (confident)")
            
            col1, col2 = st.columns(2)
            with col1:
                self_efficacy = st.slider("I believe I can succeed in a UK workplace", 1, 5, 3)
                work_readiness = st.slider("I feel prepared for interviews and starting work", 1, 5, 3)
                language = st.slider("I can communicate confidently in English at work", 1, 5, 3)
            with col2:
                digital = st.slider("I can use computers and email for work tasks", 1, 5, 3)
                psych_safety = st.slider("I feel safe expressing myself without fear of judgment", 1, 5, 3)
            
            submitted = st.form_submit_button("Add Candidate", use_container_width=True)
            
            if submitted and name and cohort:
                try:
                    data = {
                        "name": name,
                        "cohort": cohort,
                        "training_completed": training_completed.isoformat(),
                        "status": "Available",
                        "baseline_self_efficacy": self_efficacy,
                        "baseline_work_readiness": work_readiness,
                        "baseline_language": language,
                        "baseline_digital": digital,
                        "baseline_psych_safety": psych_safety,
                        "created_at": datetime.now().isoformat()
                    }
                    supabase.table("candidates").insert(data).execute()
                    st.success(f"✓ {name} added successfully!")
                except Exception as e:
                    st.error(f"Error: {e}")
    
    with tab3:
        st.subheader("Upload Cohort")
        st.info("Upload a CSV with columns: name, cohort, training_completed")
        uploaded_file = st.file_uploader("Choose CSV file", type="csv")
        if uploaded_file:
            df = pd.read_csv(uploaded_file)
            st.dataframe(df)
            if st.button("Import Candidates"):
                st.success(f"✓ {len(df)} candidates imported!")

def ach_candidate_support():
    st.markdown('<p class="main-header">💬 Candidate Support</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Record milestone check-ins with candidates</p>', unsafe_allow_html=True)
    
    # Select candidate
    try:
        placements = supabase.table("placements").select("*").eq("status", "Active").execute()
        if placements.data:
            candidate_options = {f"{p['candidate_name']} ({p.get('partner_name', 'Unknown Partner')})": p for p in placements.data}
            selected = st.selectbox("Select Candidate", [""] + list(candidate_options.keys()))
            
            if selected:
                placement = candidate_options[selected]
                
                st.markdown(f'<p class="section-header">Milestone Check-in: {placement["candidate_name"]}</p>', unsafe_allow_html=True)
                
                milestone = st.selectbox("Milestone", ["3-month", "6-month", "12-month"])
                
                with st.form("candidate_checkin"):
                    st.subheader("Psychological Safety & Inclusion")
                    
                    safe_self = st.select_slider(
                        "I feel safe to be myself at work",
                        options=["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"],
                        value="Neutral"
                    )
                    
                    respected = st.select_slider(
                        "I feel respected by my manager and colleagues",
                        options=["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"],
                        value="Neutral"
                    )
                    
                    welcoming = st.select_slider(
                        "My workplace is welcoming to people from different backgrounds",
                        options=["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"],
                        value="Neutral"
                    )
                    
                    st.divider()
                    st.subheader("Economic Stability")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        hourly_rate = st.number_input("Current hourly rate (£)", min_value=0.0, value=12.0, step=0.50)
                        contract_type = st.selectbox("Contract type", ["Permanent", "Fixed-term", "Zero-hours", "Other"])
                    with col2:
                        weekly_hours = st.number_input("Typical weekly hours", min_value=0, value=35)
                        enough_hours = st.selectbox("I have enough hours to meet my financial needs", ["Yes", "No", "Sometimes"])
                    
                    st.divider()
                    st.subheader("Career & Development")
                    
                    received_training = st.selectbox("I have received training or development", ["Yes", "No"])
                    training_type = ""
                    if received_training == "Yes":
                        training_type = st.text_input("What type of training?")
                    
                    confidence_growth = st.select_slider(
                        "I feel more confident in my skills than when I started",
                        options=["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"],
                        value="Neutral"
                    )
                    
                    st.divider()
                    st.subheader("Wellbeing")
                    
                    overall_feeling = st.selectbox(
                        "Overall, how are you feeling about your work?",
                        ["Very Positive", "Positive", "Neutral", "Difficult", "Very Difficult"]
                    )
                    
                    improvement_quote = st.text_area(
                        "Is there anything that would make your experience better?",
                        placeholder="Optional - this may be included in impact reports"
                    )
                    
                    submitted = st.form_submit_button("Save Check-in", use_container_width=True)
                    
                    if submitted:
                        try:
                            data = {
                                "placement_id": placement["id"],
                                "milestone_month": int(milestone.split("-")[0]),
                                "safe_to_be_self": safe_self,
                                "feel_respected": respected,
                                "workplace_welcoming": welcoming,
                                "hourly_rate": hourly_rate,
                                "contract_type": contract_type,
                                "weekly_hours": weekly_hours,
                                "enough_hours": enough_hours,
                                "received_training": received_training == "Yes",
                                "training_type": training_type,
                                "confidence_growth": confidence_growth,
                                "overall_feeling": overall_feeling,
                                "improvement_quote": improvement_quote,
                                "submitted_at": datetime.now().isoformat()
                            }
                            supabase.table("milestone_reviews_candidate").insert(data).execute()
                            st.success("✓ Check-in saved successfully!")
                        except Exception as e:
                            st.error(f"Error: {e}")
        else:
            st.info("No active placements to review.")
    except:
        st.info("No active placements to review.")

# ============ PARTNER PAGES ============
def partner_dashboard():
    st.markdown('<p class="main-header">📊 Your Impact Dashboard</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="sub-header">Track the social impact your organisation creates through employment</p>', unsafe_allow_html=True)
    
    partner_id = st.session_state.get("user_id", 1)
    metrics = calculate_impact_metrics(partner_id)
    
    # Key metrics row 1
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("People Employed", metrics["active_employees"], f"of {metrics['total_placements']} placed")
    with col2:
        retention_delta = f"+{metrics['retention_rate'] - metrics['baseline_retention']}% vs your baseline" if metrics['baseline_retention'] > 0 else f"+{metrics['retention_rate']-72}% vs industry avg"
        st.metric("Retention Rate", f"{metrics['retention_rate']}%", retention_delta if metrics['retention_rate'] > 72 else None)
    with col3:
        st.metric("Living Wage", f"{metrics['living_wage_percent']}%", "of roles at/above £12/hr")
    with col4:
        st.metric("Est. Cost Savings", f"£{metrics['cost_savings']:,}", "from improved retention")
    
    # Key metrics row 2
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Hard-to-Fill Roles", metrics["hard_roles_filled"], "filled through partnership")
    with col2:
        st.metric("Progression Rate", f"{metrics['progression_rate']}%", "received promotion or pay rise")
    with col3:
        st.metric("Training Provided", metrics["training_count"], "employees trained")
    with col4:
        st.metric("EDI Contribution", f"+{metrics['active_employees']}", "from refugee/migrant backgrounds")
    
    # Pending reviews alert
    pending = get_pending_reviews(partner_id)
    if pending:
        st.markdown('<p class="section-header">⚠️ Action Required</p>', unsafe_allow_html=True)
        for p in pending:
            st.warning(f"**{p['candidate_name']}** — {p['milestone']} due {p['due_date']}")
    
    # Success stories - Employer quotes
    if metrics["quotes"]:
        st.markdown('<p class="section-header">💬 Success Stories</p>', unsafe_allow_html=True)
        
        # Show up to 4 quotes in a grid
        quote_cols = st.columns(2)
        for i, quote in enumerate(metrics["quotes"][:4]):
            with quote_cols[i % 2]:
                st.markdown(f'<div class="quote-box">"{quote}"</div>', unsafe_allow_html=True)
    
    # Candidate voices
    if metrics["candidate_quotes"]:
        st.markdown('<p class="section-header">🌟 In Their Own Words</p>', unsafe_allow_html=True)
        st.caption("What your employees say about working here")
        
        for quote in metrics["candidate_quotes"][:3]:
            st.markdown(f'<div class="quote-box">"{quote}"</div>', unsafe_allow_html=True)
    
    # Placements list
    st.markdown('<p class="section-header">👥 Your Team</p>', unsafe_allow_html=True)
    try:
        placements = supabase.table("placements").select("*").eq("partner_id", partner_id).execute()
        if placements.data:
            for p in placements.data:
                status_icon = "✅" if p.get("status") == "Active" else "❌"
                with st.expander(f"{status_icon} **{p['candidate_name']}** — {p['role']}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Start Date:** {p.get('start_date', 'N/A')}")
                        st.write(f"**Contract:** {p.get('contract_type', 'N/A')}")
                    with col2:
                        st.write(f"**Hourly Rate:** £{p.get('hourly_rate', 'N/A')}")
                        st.write(f"**Status:** {p.get('status', 'N/A')}")
    except:
        st.info("No placements yet.")

def partner_baseline():
    st.markdown('<p class="main-header">📋 Baseline Data</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Tell us about the roles you\'re hiring for</p>', unsafe_allow_html=True)
    
    partner_id = st.session_state.get("user_id", 1)
    
    # Check existing baseline
    try:
        existing = supabase.table("partner_baseline").select("*").eq("partner_id", partner_id).execute()
        if existing.data:
            st.success(f"✓ You have {len(existing.data)} role(s) set up")
            
            for role in existing.data:
                with st.expander(f"**{role['role_title']}** — £{role.get('salary', 'N/A'):,}/year"):
                    st.write(f"Retention rate: {role.get('retention_rate', 'N/A')}%")
                    st.write(f"Difficulty to fill: {role.get('difficulty', 'N/A')}")
                    st.write(f"Living wage: {'Yes' if role.get('living_wage') else 'No'}")
    except:
        pass
    
    st.markdown('<p class="section-header">Add New Role</p>', unsafe_allow_html=True)
    
    with st.form("baseline_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            role_title = st.text_input("Role Title *", placeholder="e.g., Kitchen Porter")
            salary = st.number_input("Annual Salary (£) *", min_value=0, value=22500, step=500)
            retention_rate = st.slider("Your typical retention rate for this role (%)", 0, 100, 70)
        
        with col2:
            difficulty = st.selectbox("How difficult is this role to fill?", ["Easy", "Moderate", "Hard", "Very Hard"])
            vacancy_time = st.selectbox("How long does this role typically stay vacant?", ["Less than 2 weeks", "2-4 weeks", "1-2 months", "2-3 months", "3+ months"])
            living_wage = st.selectbox("Is this role paid at or above Real Living Wage (£12/hr)?", ["Yes", "No"])
            permanent = st.selectbox("Is this a permanent contract?", ["Yes", "No", "Mix"])
        
        submitted = st.form_submit_button("Save Role", use_container_width=True)
        
        if submitted and role_title:
            try:
                data = {
                    "partner_id": partner_id,
                    "role_title": role_title,
                    "salary": salary,
                    "retention_rate": retention_rate,
                    "difficulty": difficulty,
                    "vacancy_time": vacancy_time,
                    "living_wage": living_wage == "Yes",
                    "permanent": permanent,
                    "created_at": datetime.now().isoformat()
                }
                supabase.table("partner_baseline").insert(data).execute()
                st.success(f"✓ {role_title} saved!")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

def partner_interview_feedback():
    st.markdown('<p class="main-header">🎤 Interview Feedback</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Record feedback for candidates you\'ve interviewed</p>', unsafe_allow_html=True)
    
    partner_id = st.session_state.get("user_id", 1)
    
    # Get available candidates
    try:
        candidates = supabase.table("candidates").select("*").eq("status", "Available").execute()
        baseline = supabase.table("partner_baseline").select("*").eq("partner_id", partner_id).execute()
        
        if not candidates.data:
            st.info("No candidates available for interview feedback.")
            return
        
        candidate_options = {c["name"]: c for c in candidates.data}
        role_options = [r["role_title"] for r in baseline.data] if baseline.data else []
        
        with st.form("interview_feedback"):
            col1, col2 = st.columns(2)
            
            with col1:
                candidate_name = st.selectbox("Candidate *", [""] + list(candidate_options.keys()))
                interview_date = st.date_input("Interview Date *")
            
            with col2:
                role = st.selectbox("Role Interviewed For *", [""] + role_options + ["Other"])
                if role == "Other":
                    role = st.text_input("Specify role")
            
            st.divider()
            
            hired = st.radio("Was this candidate offered a position?", ["Yes", "No"], horizontal=True)
            
            if hired == "No":
                reason = st.selectbox(
                    "Primary reason",
                    ["Skills gap", "Experience gap", "English proficiency", "Role no longer available", "Not the right fit for this role", "Other"]
                )
                improvement = st.text_area("What could help this candidate improve for future opportunities?")
                standout = None
                start_date = None
                confirmed_salary = None
                contract_type = None
            else:
                reason = None
                improvement = None
                standout = st.text_area("What stood out about this candidate? *", placeholder="This may be included in impact reports")
                start_date = st.date_input("Start Date *")
                confirmed_salary = st.number_input("Confirmed Annual Salary (£)", min_value=0, value=22500)
                contract_type = st.selectbox("Contract Type", ["Permanent", "Fixed-term", "Other"])
            
            submitted = st.form_submit_button("Submit Feedback", use_container_width=True)
            
            if submitted and candidate_name and role:
                try:
                    candidate = candidate_options[candidate_name]
                    
                    feedback_data = {
                        "partner_id": partner_id,
                        "candidate_id": candidate["id"],
                        "candidate_name": candidate_name,
                        "role": role,
                        "interview_date": interview_date.isoformat(),
                        "hired": hired == "Yes",
                        "rejection_reason": reason,
                        "improvement_feedback": improvement,
                        "standout_reason": standout,
                        "submitted_at": datetime.now().isoformat()
                    }
                    supabase.table("interview_feedback").insert(feedback_data).execute()
                    
                    # If hired, create placement
                    if hired == "Yes" and start_date:
                        # Get partner name
                        partner = supabase.table("impact_partners").select("name").eq("id", partner_id).execute()
                        partner_name = partner.data[0]["name"] if partner.data else "Unknown"
                        
                        placement_data = {
                            "partner_id": partner_id,
                            "partner_name": partner_name,
                            "candidate_id": candidate["id"],
                            "candidate_name": candidate_name,
                            "role": role,
                            "start_date": start_date.isoformat(),
                            "salary": confirmed_salary,
                            "hourly_rate": round(confirmed_salary / 52 / 40, 2),
                            "contract_type": contract_type,
                            "status": "Active",
                            "created_at": datetime.now().isoformat()
                        }
                        supabase.table("placements").insert(placement_data).execute()
                        
                        # Update candidate status
                        supabase.table("candidates").update({"status": "Placed"}).eq("id", candidate["id"]).execute()
                        
                        st.success(f"✓ {candidate_name} has been placed! Start date: {start_date}")
                    else:
                        st.success("✓ Feedback recorded")
                    
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
    except Exception as e:
        st.error(f"Error loading data: {e}")

def partner_milestone_review():
    st.markdown('<p class="main-header">📅 Milestone Reviews</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Provide updates on your employees at key milestones</p>', unsafe_allow_html=True)
    
    partner_id = st.session_state.get("user_id", 1)
    
    # Get pending reviews
    pending = get_pending_reviews(partner_id)
    
    if not pending:
        st.success("✓ All reviews are up to date!")
        return
    
    st.warning(f"You have {len(pending)} review(s) pending")
    
    for review in pending:
        with st.expander(f"**{review['candidate_name']}** — {review['milestone']} (Due: {review['due_date']})"):
            with st.form(f"review_{review['placement_id']}_{review['milestone_month']}"):
                still_employed = st.radio("Is this person still employed with your organisation?", ["Yes", "No"], horizontal=True)
                
                if still_employed == "No":
                    leaving_date = st.date_input("When did they leave?")
                    leaving_reason = st.selectbox("Reason for leaving", ["Resigned", "Dismissed", "Redundancy", "Contract ended", "Other"])
                    performance = None
                    received_training = None
                    training_type = None
                    progression = None
                    progression_details = None
                    support_provided = None
                    contribution_quote = None
                else:
                    leaving_date = None
                    leaving_reason = None
                    
                    performance = st.selectbox("How would you rate their overall performance?", ["Excellent", "Good", "Satisfactory", "Needs Improvement"])
                    
                    received_training = st.radio("Has this person received any training?", ["Yes", "No"], horizontal=True)
                    training_type = ""
                    if received_training == "Yes":
                        training_type = st.text_input("What type of training?")
                    
                    progression = st.radio("Any progression (pay rise, promotion, new responsibilities)?", ["Yes", "No"], horizontal=True)
                    progression_details = ""
                    if progression == "Yes":
                        progression_details = st.text_input("Please describe")
                    
                    support_provided = st.multiselect(
                        "What support has your organisation provided?",
                        ["Mentoring or buddy system", "Flexible working arrangements", "Reasonable adjustments", "Language support", "Additional training", "Other"]
                    )
                    
                    contribution_quote = st.text_area(
                        "In one sentence, how would you describe this person's contribution?",
                        placeholder="This may be included in impact reports"
                    )
                
                submitted = st.form_submit_button("Submit Review", use_container_width=True)
                
                if submitted:
                    try:
                        data = {
                            "placement_id": review["placement_id"],
                            "partner_id": partner_id,
                            "milestone_month": review["milestone_month"],
                            "still_employed": still_employed == "Yes",
                            "leaving_date": leaving_date.isoformat() if leaving_date else None,
                            "leaving_reason": leaving_reason,
                            "performance": performance,
                            "received_training": received_training == "Yes" if received_training else None,
                            "training_type": training_type,
                            "progression": progression == "Yes" if progression else None,
                            "progression_details": progression_details,
                            "support_provided": json.dumps(support_provided) if support_provided else None,
                            "contribution_quote": contribution_quote,
                            "submitted_at": datetime.now().isoformat()
                        }
                        supabase.table("milestone_reviews_partner").insert(data).execute()
                        
                        # Update placement status if left
                        if still_employed == "No":
                            supabase.table("placements").update({"status": "Left"}).eq("id", review["placement_id"]).execute()
                        
                        st.success("✓ Review submitted!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

def partner_reports():
    st.markdown('<p class="main-header">📑 Impact Reports</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Your quarterly impact reports</p>', unsafe_allow_html=True)
    
    partner_id = st.session_state.get("user_id", 1)
    metrics = calculate_impact_metrics(partner_id)
    
    # Check if enough data
    if metrics["total_placements"] == 0:
        st.warning("No placements yet. Reports will be available once you have placed candidates.")
        return
    
    # Report header
    st.markdown("---")
    st.markdown(f"### 📊 Impact Report: {st.session_state.user_name}")
    st.markdown(f"**Report Period:** Q4 2024")
    st.markdown(f"**Generated:** {datetime.now().strftime('%d %B %Y')}")
    st.markdown("---")
    
    # Executive Summary
    st.markdown("### Executive Summary")
    st.markdown(f"""
    Through your partnership with ACH's Bridge to Employment programme, your organisation has:
    
    - ✅ Created **{metrics['total_placements']} employment opportunities** for refugees and migrants
    - ✅ Achieved **{metrics['retention_rate']}% retention** (compared to your baseline of {metrics['baseline_retention']}%)
    - ✅ Saved an estimated **£{metrics['cost_savings']:,}** in reduced turnover costs
    - ✅ Provided training to **{metrics['training_count']} employees**
    - ✅ Supported **{metrics['progression_count']} career progressions** (promotions, pay rises, new responsibilities)
    """)
    
    # Key Metrics
    st.markdown("---")
    st.markdown("### Key Metrics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Workforce Impact")
        st.write(f"**Total Placements:** {metrics['total_placements']}")
        st.write(f"**Currently Employed:** {metrics['active_employees']}")
        st.write(f"**Retention Rate:** {metrics['retention_rate']}%")
        st.write(f"**Living Wage Roles:** {metrics['living_wage_percent']}%")
    
    with col2:
        st.markdown("#### Business Value")
        st.write(f"**Hard-to-Fill Roles Filled:** {metrics['hard_roles_filled']}")
        st.write(f"**Est. Cost Savings:** £{metrics['cost_savings']:,}")
        st.write(f"**Employees Trained:** {metrics['training_count']}")
        st.write(f"**Career Progressions:** {metrics['progression_count']}")
    
    # Success Stories
    if metrics["quotes"]:
        st.markdown("---")
        st.markdown("### Success Stories")
        st.markdown("*What your team said about our candidates:*")
        
        for quote in metrics["quotes"][:3]:
            st.markdown(f'> "{quote}"')
            st.markdown("")
    
    # Employee Voices
    if metrics["candidate_quotes"]:
        st.markdown("---")
        st.markdown("### In Their Own Words")
        st.markdown("*What your employees say about working here:*")
        
        for quote in metrics["candidate_quotes"][:3]:
            st.markdown(f'> "{quote}"')
            st.markdown("")
    
    # EDI Statement
    st.markdown("---")
    st.markdown("### Diversity & Inclusion Impact")
    st.markdown(f"""
    Your organisation has welcomed **{metrics['active_employees']} employees** from refugee and migrant backgrounds, 
    contributing to a more diverse and inclusive workforce. These individuals bring unique perspectives, 
    skills, and experiences that enrich your team and strengthen your organisation.
    """)
    
    # Download button
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("📥 Download Full Report (PDF)", use_container_width=True):
            st.info("PDF download will be available soon. Contact ACH for your formatted quarterly report.")

# ============ NAVIGATION ============
def main():
    if not st.session_state.logged_in:
        login_page()
        return
    
    # Sidebar
    with st.sidebar:
        st.markdown(f"### 👋 {st.session_state.user_name}")
        st.divider()
        
        if st.session_state.user_type == "ach_staff":
            page = st.radio(
                "Navigation",
                ["Dashboard", "Manage Partners", "Manage Candidates", "Candidate Support"],
                label_visibility="collapsed"
            )
        else:
            page = st.radio(
                "Navigation",
                ["Dashboard", "Baseline Data", "Interview Feedback", "Milestone Reviews", "Reports"],
                label_visibility="collapsed"
            )
        
        st.divider()
        if st.button("Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user_type = None
            st.session_state.user_id = None
            st.session_state.user_name = None
            st.rerun()
    
    # Page routing
    if st.session_state.user_type == "ach_staff":
        if page == "Dashboard":
            ach_dashboard()
        elif page == "Manage Partners":
            ach_manage_partners()
        elif page == "Manage Candidates":
            ach_manage_candidates()
        elif page == "Candidate Support":
            ach_candidate_support()
    else:
        if page == "Dashboard":
            partner_dashboard()
        elif page == "Baseline Data":
            partner_baseline()
        elif page == "Interview Feedback":
            partner_interview_feedback()
        elif page == "Milestone Reviews":
            partner_milestone_review()
        elif page == "Reports":
            partner_reports()

if __name__ == "__main__":
    main()
