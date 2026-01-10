import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from supabase import create_client
import json

# ============ CONFIGURATION ============
SUPABASE_URL = "https://gmjqidqjpzxcpgycawxf.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdtanFpZHFqcHp4Y3BneWNhd3hmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njc3MjYyMDEsImV4cCI6MjA4MzMwMjIwMX0.6jtYlz6yoBQCrh04P0g30JigHyanGYnv7xBz24B5Bm4"

LIVING_WAGE_UK = 12.00

# ============ INDUSTRY BENCHMARKS ============
# Sources: UK Hospitality 2023, BRC, Skills for Care, NHS Digital, Logistics UK, CILT

INDUSTRY_BENCHMARKS = {
    "Healthcare": {"retention_12m": 0.75, "source": "NHS Digital"},
    "Social Care": {"retention_12m": 0.70, "source": "Skills for Care 2023"},
    "Hospitality": {"retention_12m": 0.63, "source": "UK Hospitality 2023"},
    "Retail": {"retention_12m": 0.65, "source": "British Retail Consortium"},
    "Manufacturing": {"retention_12m": 0.65, "source": "Make UK 2023"},
    "Logistics": {"retention_12m": 0.68, "source": "Logistics UK"},
    "Public Sector": {"retention_12m": 0.80, "source": "ONS Public Sector Employment"},
    "Education": {"retention_12m": 0.78, "source": "DfE School Workforce Census"},
    "Facilities": {"retention_12m": 0.62, "source": "BIFM estimates"},
    "Food Service": {"retention_12m": 0.60, "source": "UK Hospitality 2023"},
    "Other": {"retention_12m": 0.65, "source": "CIPD Labour Market Outlook"},
}

# ============ REPLACEMENT COST MULTIPLIERS ============
# Sources: CIPD Resourcing Survey, Oxford Economics

def get_replacement_multiplier(salary):
    """
    Get replacement cost multiplier based on salary band.
    Based on CIPD/Oxford Economics research.
    """
    if salary < 24000:
        return 0.15  # Entry-level: 15%
    elif salary < 28000:
        return 0.18  # Customer-facing: 18%
    elif salary < 35000:
        return 0.22  # Skilled: 22%
    elif salary < 45000:
        return 0.25  # Supervisor: 25%
    else:
        return 0.30  # Manager: 30%


def calculate_retention_savings(placements, sector, ach_retention_rate):
    """
    Calculate retention savings for a partner.
    
    Formula: Placements × Retention Uplift × Replacement Cost
    
    Where:
    - Retention Uplift = ACH_retention - Industry_benchmark
    - Replacement Cost = Salary × Multiplier (based on salary band)
    """
    benchmark_data = INDUSTRY_BENCHMARKS.get(sector, INDUSTRY_BENCHMARKS["Other"])
    industry_retention = benchmark_data["retention_12m"]
    benchmark_source = benchmark_data["source"]
    
    retention_uplift = max(0, ach_retention_rate - industry_retention)
    
    total_savings = 0
    
    for p in placements:
        salary = p.get("salary") or 0
        if salary > 0:
            multiplier = get_replacement_multiplier(salary)
            replacement_cost = salary * multiplier
            savings = retention_uplift * replacement_cost
            total_savings += savings
    
    return {
        "total_savings": round(total_savings, 2),
        "ach_retention_percent": round(ach_retention_rate * 100, 1),
        "industry_retention_percent": round(industry_retention * 100, 1),
        "retention_uplift_percent": round(retention_uplift * 100, 1),
        "sector": sector,
        "benchmark_source": benchmark_source,
        "methodology": f"Based on {benchmark_source} ({round(industry_retention * 100)}% industry retention) and CIPD replacement cost estimates."
    }


def calculate_diversity_contribution(placements, candidates_data):
    """
    Calculate diversity contribution by country of origin.
    """
    country_counts = {}
    
    for p in placements:
        candidate_id = p.get("candidate_id")
        if candidate_id and candidate_id in candidates_data:
            country = candidates_data[candidate_id].get("country_of_origin", "Unknown")
            country_counts[country] = country_counts.get(country, 0) + 1
    
    sorted_countries = sorted(country_counts.items(), key=lambda x: x[1], reverse=True)
    
    return {
        "total_employees": sum(country_counts.values()),
        "countries_represented": len(country_counts),
        "breakdown": sorted_countries
    }


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
    .main-header { font-size: 2rem; font-weight: 600; color: #0f1c3f; margin-bottom: 0.5rem; }
    .sub-header { font-size: 1rem; color: #64748b; margin-bottom: 2rem; }
    .quote-box { background: #f8fafc; border-left: 4px solid #0f1c3f; padding: 16px 20px; margin: 16px 0; font-style: italic; color: #475569; }
    .section-header { font-size: 1.3rem; color: #0f1c3f; margin: 2rem 0 1rem 0; padding-bottom: 0.5rem; border-bottom: 2px solid #e2e8f0; }
    div[data-testid="stSidebar"] { background: linear-gradient(180deg, #0f1c3f 0%, #1a2d5a 100%); }
    div[data-testid="stSidebar"] .stMarkdown { color: white; }
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

# ============ COUNTRY FLAGS ============
COUNTRY_FLAGS = {
    "Afghanistan": "🇦🇫", "Syria": "🇸🇾", "Sudan": "🇸🇩", "South Sudan": "🇸🇸",
    "Ukraine": "🇺🇦", "Eritrea": "🇪🇷", "Iran": "🇮🇷", "Iraq": "🇮🇶",
    "Somalia": "🇸🇴", "Yemen": "🇾🇪", "Ethiopia": "🇪🇹", "Congo": "🇨🇩",
    "Myanmar": "🇲🇲", "Pakistan": "🇵🇰", "Bangladesh": "🇧🇩", "Nigeria": "🇳🇬",
}

def get_flag(country):
    return COUNTRY_FLAGS.get(country, "🌍")

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
def get_partner_sector(partner_id):
    try:
        result = supabase.table("impact_partners").select("sector").eq("id", partner_id).execute()
        if result.data:
            return result.data[0].get("sector", "Other")
    except:
        pass
    return "Other"


def calculate_impact_metrics(partner_id):
    """Calculate all impact metrics for a partner"""
    
    sector = get_partner_sector(partner_id)
    
    metrics = {
        "total_placements": 0,
        "active_employees": 0,
        "retention_rate": 0,
        "retention_savings": 0,
        "retention_savings_data": {},
        "diversity_data": {},
        "inclusion_index": 0,
        "progression_rate": 0,
        "living_wage_percent": 0,
        "quotes": [],
        "candidate_quotes": [],
        "progression_count": 0,
        "training_count": 0,
        "sector": sector
    }
    
    placements = []
    try:
        result = supabase.table("placements").select("*").eq("partner_id", partner_id).execute()
        if result.data:
            placements = result.data
            metrics["total_placements"] = len(placements)
            active = [p for p in placements if p.get("status") == "Active"]
            metrics["active_employees"] = len(active)
            
            if metrics["total_placements"] > 0:
                metrics["retention_rate"] = round((len(active) / metrics["total_placements"]) * 100)
                ach_retention_decimal = len(active) / metrics["total_placements"]
                
                savings_data = calculate_retention_savings(placements, sector, ach_retention_decimal)
                metrics["retention_savings"] = savings_data["total_savings"]
                metrics["retention_savings_data"] = savings_data
            
            living_wage_count = sum(1 for p in placements if (p.get("hourly_rate") or 0) >= LIVING_WAGE_UK)
            if metrics["total_placements"] > 0:
                metrics["living_wage_percent"] = round((living_wage_count / metrics["total_placements"]) * 100)
    except:
        pass
    
    try:
        candidates_result = supabase.table("candidates").select("id, country_of_origin").execute()
        if candidates_result.data:
            candidates_dict = {c["id"]: c for c in candidates_result.data}
            metrics["diversity_data"] = calculate_diversity_contribution(placements, candidates_dict)
    except:
        pass
    
    try:
        feedback = supabase.table("interview_feedback").select("*").eq("partner_id", partner_id).eq("hired", True).execute()
        if feedback.data:
            metrics["quotes"] = [f.get("standout_reason") for f in feedback.data if f.get("standout_reason")]
    except:
        pass
    
    try:
        reviews = supabase.table("milestone_reviews_partner").select("*").eq("partner_id", partner_id).execute()
        if reviews.data:
            metrics["quotes"].extend([r.get("contribution_quote") for r in reviews.data if r.get("contribution_quote")])
            metrics["progression_count"] = sum(1 for r in reviews.data if r.get("progression"))
            metrics["training_count"] = sum(1 for r in reviews.data if r.get("received_training"))
            if metrics["total_placements"] > 0:
                metrics["progression_rate"] = round((metrics["progression_count"] / metrics["total_placements"]) * 100)
    except:
        pass
    
    try:
        if placements:
            for p in placements:
                cand_reviews = supabase.table("milestone_reviews_candidate").select("*").eq("placement_id", p["id"]).execute()
                if cand_reviews.data:
                    metrics["candidate_quotes"].extend([cr.get("improvement_quote") for cr in cand_reviews.data if cr.get("improvement_quote")])
    except:
        pass
    
    return metrics


def get_pending_reviews(partner_id):
    pending = []
    try:
        placements = supabase.table("placements").select("*").eq("partner_id", partner_id).eq("status", "Active").execute()
        if placements.data:
            for p in placements.data:
                start_date = datetime.fromisoformat(p["start_date"]) if p.get("start_date") else None
                if start_date:
                    months_employed = (datetime.now() - start_date).days / 30
                    for m in [3, 6, 12]:
                        if months_employed >= m:
                            review = supabase.table("milestone_reviews_partner").select("*").eq("placement_id", p["id"]).eq("milestone_month", m).execute()
                            if not review.data:
                                pending.append({
                                    "candidate_name": p.get("candidate_name", "Unknown"),
                                    "milestone": f"{m}-month review",
                                    "due_date": (start_date + timedelta(days=m*30)).strftime("%d %b %Y"),
                                    "placement_id": p["id"],
                                    "milestone_month": m
                                })
    except:
        pass
    return pending


# ============ PARTNER DASHBOARD ============
def partner_dashboard():
    st.markdown('<p class="main-header">📊 Your Impact Dashboard</p>', unsafe_allow_html=True)
    
    partner_id = st.session_state.get("user_id", 1)
    metrics = calculate_impact_metrics(partner_id)
    
    # KEY METRICS
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Retention Savings", f"£{metrics['retention_savings']:,.0f}", f"vs {metrics['sector']} avg")
    
    with col2:
        diversity = metrics.get("diversity_data", {})
        st.metric("Diversity Contribution", f"{diversity.get('countries_represented', 0)} countries", f"{diversity.get('total_employees', 0)} employees")
    
    with col3:
        st.metric("Inclusion Capability Index", "Coming soon", "")
    
    # RETENTION BREAKDOWN
    st.markdown('<p class="section-header">💰 Retention Savings Breakdown</p>', unsafe_allow_html=True)
    
    savings_data = metrics.get("retention_savings_data", {})
    if savings_data:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Your Retention", f"{savings_data.get('ach_retention_percent', 0)}%")
        col2.metric("Industry Benchmark", f"{savings_data.get('industry_retention_percent', 0)}%")
        col3.metric("Your Uplift", f"+{savings_data.get('retention_uplift_percent', 0)}%")
        col4.metric("Total Savings", f"£{savings_data.get('total_savings', 0):,.0f}")
        st.caption(f"📊 {savings_data.get('methodology', '')}")
    
    # DIVERSITY BREAKDOWN
    st.markdown('<p class="section-header">🌍 Diversity Contribution</p>', unsafe_allow_html=True)
    
    breakdown = metrics.get("diversity_data", {}).get("breakdown", [])
    if breakdown:
        cols = st.columns(min(len(breakdown), 4))
        for i, (country, count) in enumerate(breakdown[:4]):
            cols[i].metric(f"{get_flag(country)} {country}", count)
    
    # ADDITIONAL METRICS
    st.markdown('<p class="section-header">📈 Additional Metrics</p>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("People Employed", metrics["active_employees"], f"of {metrics['total_placements']}")
    col2.metric("Retention Rate", f"{metrics['retention_rate']}%")
    col3.metric("Living Wage", f"{metrics['living_wage_percent']}%")
    col4.metric("Progressions", metrics["progression_count"])
    
    # PENDING REVIEWS
    pending = get_pending_reviews(partner_id)
    if pending:
        st.markdown('<p class="section-header">⚠️ Action Required</p>', unsafe_allow_html=True)
        for p in pending:
            st.warning(f"**{p['candidate_name']}** — {p['milestone']} due {p['due_date']}")
    
    # QUOTES
    if metrics["quotes"]:
        st.markdown('<p class="section-header">💬 Success Stories</p>', unsafe_allow_html=True)
        for quote in metrics["quotes"][:3]:
            st.markdown(f'<div class="quote-box">"{quote}"</div>', unsafe_allow_html=True)


# ============ ACH DASHBOARD ============
def ach_dashboard():
    st.markdown('<p class="main-header">📊 Impact Intelligence Dashboard</p>', unsafe_allow_html=True)
    
    try:
        partners = supabase.table("impact_partners").select("*").execute()
        candidates = supabase.table("candidates").select("*").execute()
        placements = supabase.table("placements").select("*").execute()
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Partners", len(partners.data) if partners.data else 0)
        col2.metric("Candidates", len(candidates.data) if candidates.data else 0)
        col3.metric("Placements", len(placements.data) if placements.data else 0)
        
        if placements.data:
            active = len([p for p in placements.data if p.get("status") == "Active"])
            retention = round((active / len(placements.data)) * 100) if placements.data else 0
            col4.metric("Retention", f"{retention}%")
    except Exception as e:
        st.error(f"Error: {e}")


# ============ OTHER PAGES (SIMPLIFIED) ============
def ach_manage_partners():
    st.markdown('<p class="main-header">🏢 Manage Partners</p>', unsafe_allow_html=True)
    st.info("Partner management interface")

def ach_manage_candidates():
    st.markdown('<p class="main-header">👥 Manage Candidates</p>', unsafe_allow_html=True)
    st.info("Candidate management interface")

def ach_candidate_support():
    st.markdown('<p class="main-header">💬 Candidate Support</p>', unsafe_allow_html=True)
    st.info("Candidate support interface")

def partner_baseline():
    st.markdown('<p class="main-header">📋 Baseline Data</p>', unsafe_allow_html=True)
    st.info("Baseline data interface")

def partner_interview_feedback():
    st.markdown('<p class="main-header">🎤 Interview Feedback</p>', unsafe_allow_html=True)
    st.info("Interview feedback interface")

def partner_milestone_review():
    st.markdown('<p class="main-header">📅 Milestone Reviews</p>', unsafe_allow_html=True)
    st.info("Milestone review interface")

def partner_reports():
    st.markdown('<p class="main-header">📑 Impact Reports</p>', unsafe_allow_html=True)
    st.info("Reports interface")


# ============ NAVIGATION ============
def main():
    if not st.session_state.logged_in:
        login_page()
        return
    
    with st.sidebar:
        st.markdown(f"### 👋 {st.session_state.user_name}")
        st.divider()
        
        if st.session_state.user_type == "ach_staff":
            page = st.radio("Navigation", ["Dashboard", "Manage Partners", "Manage Candidates", "Candidate Support"], label_visibility="collapsed")
        else:
            page = st.radio("Navigation", ["Dashboard", "Baseline Data", "Interview Feedback", "Milestone Reviews", "Reports"], label_visibility="collapsed")
        
        st.divider()
        if st.button("Logout", use_container_width=True):
            for key in ["logged_in", "user_type", "user_id", "user_name"]:
                st.session_state[key] = None
            st.session_state.logged_in = False
            st.rerun()
    
    if st.session_state.user_type == "ach_staff":
        {"Dashboard": ach_dashboard, "Manage Partners": ach_manage_partners, "Manage Candidates": ach_manage_candidates, "Candidate Support": ach_candidate_support}[page]()
    else:
        {"Dashboard": partner_dashboard, "Baseline Data": partner_baseline, "Interview Feedback": partner_interview_feedback, "Milestone Reviews": partner_milestone_review, "Reports": partner_reports}[page]()


if __name__ == "__main__":
    main()
