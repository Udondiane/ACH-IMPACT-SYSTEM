import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from supabase import create_client
import json

# ============ CONFIGURATION ============
SUPABASE_URL = "https://gmjqidqjpzxcpgycawxf.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdtanFpZHFqcHp4Y3BneWNhd3hmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njc3MjYyMDEsImV4cCI6MjA4MzMwMjIwMX0.6jtYlz6yoBQCrh04P0g30JigHyanGYnv7xBz24B5Bm4"

LIVING_WAGE_UK = 12.00

SUITABILITY_CATEGORIES = ["Reliability", "Teamwork", "Communication", "Initiative", "Technical Skills", "Attitude", "Punctuality", "Adaptability"]
SUITABILITY_RATINGS = ["Excellent", "Good", "Satisfactory", "Needs Improvement"]

PARTNER_TYPES = ["Corporate Partner", "Funder", "Local Council", "Training Provider", "Community Organisation", "NHS Trust", "Other"]
EMPLOYEE_RANGES = ["1-10", "11-50", "51-100", "101-250", "251-500", "501-1000", "1000+"]

SECTORS = [
    "Accommodation and Food Services", "Administrative and Support Services", "Agriculture, Forestry and Fishing",
    "Arts, Entertainment and Recreation", "Automotive", "Aviation", "Banking and Finance", "Charity and Non-Profit",
    "Cleaning Services", "Construction", "Consulting", "Creative and Media", "Defence", "Education - Early Years",
    "Education - Further Education", "Education - Higher Education", "Education - Primary", "Education - Secondary",
    "Energy and Utilities", "Engineering", "Environmental Services", "Events and Conferences", "Facilities Management",
    "Fashion and Textiles", "Financial Services", "Food and Beverage Manufacturing", "Government - Central",
    "Government - Local", "Healthcare - Dental", "Healthcare - GP/Primary Care", "Healthcare - Hospital/Acute",
    "Healthcare - Mental Health", "Healthcare - Pharmacy", "Hospitality - Hotels", "Hospitality - Restaurants",
    "Hospitality - Catering", "Hospitality - Pubs and Bars", "Housing and Property", "Human Resources",
    "Information Technology", "Insurance", "Legal Services", "Logistics and Distribution", "Manufacturing - General",
    "Manufacturing - Food", "Manufacturing - Pharmaceutical", "Marketing and Advertising", "Mining and Quarrying",
    "Performing Arts", "Pharmaceuticals", "Professional Services", "Public Administration", "Real Estate",
    "Recruitment", "Research and Development", "Retail - Fashion", "Retail - Food and Grocery", "Retail - General",
    "Retail - Online", "Security Services", "Social Care - Adults", "Social Care - Children", "Social Care - Elderly",
    "Social Care - Disabilities", "Sports and Fitness", "Telecommunications", "Tourism and Travel",
    "Transport - Bus and Coach", "Transport - Rail", "Transport - Taxi and Private Hire", "Transport - Freight",
    "Veterinary", "Warehousing", "Waste Management", "Wholesale", "Other"
]

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
    "Other": {"retention_12m": 0.65, "source": "CIPD Labour Market Outlook"},
}

def get_sector_benchmark(sector):
    sector_lower = sector.lower() if sector else ""
    if "healthcare" in sector_lower or "hospital" in sector_lower or "nhs" in sector_lower or "dental" in sector_lower or "pharmacy" in sector_lower:
        return INDUSTRY_BENCHMARKS["Healthcare"]
    elif "social care" in sector_lower:
        return INDUSTRY_BENCHMARKS["Social Care"]
    elif "hospitality" in sector_lower or "hotel" in sector_lower or "restaurant" in sector_lower or "catering" in sector_lower:
        return INDUSTRY_BENCHMARKS["Hospitality"]
    elif "retail" in sector_lower:
        return INDUSTRY_BENCHMARKS["Retail"]
    elif "manufacturing" in sector_lower:
        return INDUSTRY_BENCHMARKS["Manufacturing"]
    elif "logistics" in sector_lower or "warehouse" in sector_lower or "distribution" in sector_lower:
        return INDUSTRY_BENCHMARKS["Logistics"]
    elif "government" in sector_lower or "public" in sector_lower or "council" in sector_lower:
        return INDUSTRY_BENCHMARKS["Public Sector"]
    elif "education" in sector_lower:
        return INDUSTRY_BENCHMARKS["Education"]
    elif "facilities" in sector_lower or "cleaning" in sector_lower:
        return INDUSTRY_BENCHMARKS["Facilities"]
    else:
        return INDUSTRY_BENCHMARKS["Other"]

ALL_COUNTRIES = ["", "Afghanistan", "Albania", "Algeria", "Angola", "Argentina", "Armenia", "Australia", "Austria", "Azerbaijan", "Bangladesh", "Belarus", "Belgium", "Bolivia", "Bosnia and Herzegovina", "Brazil", "Bulgaria", "Cameroon", "Canada", "Chile", "China", "Colombia", "Congo", "Croatia", "Cuba", "Czech Republic", "Democratic Republic of the Congo", "Denmark", "Ecuador", "Egypt", "Eritrea", "Estonia", "Ethiopia", "Finland", "France", "Georgia", "Germany", "Ghana", "Greece", "Guatemala", "Haiti", "Honduras", "Hungary", "India", "Indonesia", "Iran", "Iraq", "Ireland", "Israel", "Italy", "Jamaica", "Japan", "Jordan", "Kazakhstan", "Kenya", "Kuwait", "Kyrgyzstan", "Latvia", "Lebanon", "Libya", "Lithuania", "Malaysia", "Mexico", "Moldova", "Morocco", "Myanmar", "Nepal", "Netherlands", "New Zealand", "Nicaragua", "Nigeria", "North Korea", "North Macedonia", "Norway", "Pakistan", "Palestine", "Peru", "Philippines", "Poland", "Portugal", "Romania", "Russia", "Rwanda", "Saudi Arabia", "Senegal", "Serbia", "Sierra Leone", "Singapore", "Slovakia", "Slovenia", "Somalia", "South Africa", "South Korea", "South Sudan", "Spain", "Sri Lanka", "Sudan", "Sweden", "Switzerland", "Syria", "Taiwan", "Tajikistan", "Tanzania", "Thailand", "Tunisia", "Turkey", "Turkmenistan", "Uganda", "Ukraine", "United Arab Emirates", "United Kingdom", "United States", "Uzbekistan", "Venezuela", "Vietnam", "Yemen", "Zambia", "Zimbabwe"]

HOLISTIC_IMPACT_QUESTIONS = {
    "economic_security": {"name": "Economic Security & Stability", "description": "Ability to meet basic needs and plan financially", "employer": "We pay at least the real Living Wage and offer stable, predictable hours", "employee": "I can comfortably cover my basic expenses and plan for the future"},
    "skill_growth": {"name": "Skill Use & Growth", "description": "Ability to use existing skills and develop new ones", "employer": "We provide opportunities for training and skill development relevant to employees' goals", "employee": "I am able to use my skills and experience, and I have opportunities to learn and grow"},
    "dignity_respect": {"name": "Workplace Dignity & Respect", "description": "Freedom from discrimination, fair and respectful treatment", "employer": "We have clear policies and practices that ensure all employees are treated with dignity and respect", "employee": "I feel respected and treated fairly at work, regardless of my background"},
    "voice_agency": {"name": "Voice & Agency", "description": "Ability to influence decisions and shape one's work", "employer": "We actively seek and act on employee feedback and involve staff in decisions that affect them", "employee": "My opinions are valued and I have influence over how I do my work"},
    "belonging_inclusion": {"name": "Social Belonging & Inclusion", "description": "Feeling part of the team and workplace community", "employer": "We foster a culture where all employees feel they belong and can participate fully", "employee": "I feel like I belong here and have meaningful connections with colleagues"},
    "wellbeing": {"name": "Wellbeing & Confidence to Plan Ahead", "description": "Mental health support and ability to envision a future", "employer": "We support employee wellbeing and help staff see a future with us", "employee": "I feel positive about my future and can see opportunities ahead for me"}
}

@st.cache_resource
def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = get_supabase()

st.set_page_config(page_title="ACH Impact Intelligence", page_icon="A", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    .main-header { font-size: 2rem; font-weight: 600; color: #0f1c3f; margin-bottom: 0.5rem; }
    .sub-header { font-size: 1rem; color: #64748b; margin-bottom: 2rem; }
    .section-header { font-size: 1.3rem; color: #0f1c3f; margin: 2rem 0 1rem 0; padding-bottom: 0.5rem; border-bottom: 2px solid #e2e8f0; }
    .quote-box { background: #f8fafc; border-left: 4px solid #0f1c3f; padding: 16px 20px; margin: 16px 0; font-style: italic; color: #475569; }
    div[data-testid="stSidebar"] { background: linear-gradient(180deg, #0f1c3f 0%, #1a2d5a 100%); }
    div[data-testid="stSidebar"] .stMarkdown { color: white; }
</style>
""", unsafe_allow_html=True)

if 'user_type' not in st.session_state:
    st.session_state.user_type = "ach_staff"
if 'user_id' not in st.session_state:
    st.session_state.user_id = 1
if 'user_name' not in st.session_state:
    st.session_state.user_name = "ACH Administrator"

def get_replacement_multiplier(salary):
    if salary < 25000: return 0.16
    elif salary < 35000: return 0.50
    elif salary < 50000: return 0.75
    else: return 1.00

def calculate_integration_contribution(placements, candidates_data):
    total_person_months = 0
    countries = set()
    for p in placements:
        if p.get("start_date"):
            start = datetime.fromisoformat(str(p["start_date"]))
            if p.get("status") == "Published":
                months = (datetime.now() - start).days / 30
            elif p.get("end_date"):
                end = datetime.fromisoformat(str(p["end_date"]))
                months = (end - start).days / 30
            else:
                months = 0
            total_person_months += months
        candidate_id = p.get("candidate_id")
        if candidate_id and candidate_id in candidates_data:
            country = candidates_data[candidate_id].get("country_of_origin", "")
            if country and country not in ["United Kingdom", "UK", "England", "Scotland", "Wales", "Northern Ireland", "Unknown", ""]:
                countries.add(country)
    return {"total_person_months": round(total_person_months, 1), "countries_represented": len(countries), "integration_score": round((total_person_months * 10) + (len(countries) * 50))}

def calculate_retention_savings(placements, sector, ach_retention_rate):
    benchmark_data = get_sector_benchmark(sector)
    industry_retention = benchmark_data["retention_12m"]
    benchmark_source = benchmark_data["source"]
    total_placements = len(placements)
    if total_placements == 0:
        return {"total_savings": 0, "ach_retention_percent": 0, "industry_retention_percent": round(industry_retention * 100, 1), "retention_uplift_percent": 0, "extra_retained": 0, "benchmark_source": benchmark_source, "methodology": ""}
    retained_placements = [p for p in placements if p.get("status") == "Published" or (p.get("end_date") and (datetime.fromisoformat(str(p["end_date"])) - datetime.fromisoformat(str(p["start_date"]))).days >= 365)]
    retained_with_costs = []
    for p in retained_placements:
        salary = p.get("salary") or 0
        if salary > 0:
            retained_with_costs.append({"placement": p, "replacement_cost": salary * get_replacement_multiplier(salary)})
    retained_with_costs.sort(key=lambda x: x["replacement_cost"], reverse=True)
    industry_expected_retained = round(total_placements * industry_retention)
    actual_retained = len(retained_placements)
    extra_retained = max(0, actual_retained - industry_expected_retained)
    total_savings = sum(retained_with_costs[i]["replacement_cost"] for i in range(extra_retained) if i < len(retained_with_costs))
    methodology = f"Based on {benchmark_source} ({round(industry_retention * 100)}% industry 12-month retention). "
    if extra_retained > 0:
        methodology += f"You retained {extra_retained} more employee(s) than industry average, saving an estimated £{total_savings:,.0f} in replacement costs."
    else:
        methodology += f"Replacement costs based on Oxford Economics and CIPD research (16-100% of salary by role level)."
    return {"total_savings": round(total_savings, 2), "ach_retention_percent": round(ach_retention_rate * 100, 1), "industry_retention_percent": round(industry_retention * 100, 1), "retention_uplift_percent": round((ach_retention_rate - industry_retention) * 100, 1), "extra_retained": extra_retained, "benchmark_source": benchmark_source, "methodology": methodology}

def calculate_diversity_contribution(placements, candidates_data):
    country_counts = {}
    for p in placements:
        candidate_id = p.get("candidate_id")
        if candidate_id and candidate_id in candidates_data:
            country = candidates_data[candidate_id].get("country_of_origin", "Unknown")
            if country and country not in ["United Kingdom", "UK", "England", "Scotland", "Wales", "Northern Ireland", "Unknown", ""]:
                country_counts[country] = country_counts.get(country, 0) + 1
    return {"total_employees": sum(country_counts.values()), "countries_represented": len(country_counts), "breakdown": sorted(country_counts.items(), key=lambda x: x[1], reverse=True)}

def get_partner_sector(partner_id):
    try:
        result = supabase.table("impact_partners").select("sector").eq("id", partner_id).execute()
        if result.data:
            return result.data[0].get("sector", "Other")
    except:
        pass
    return "Other"

def calculate_impact_metrics(partner_id):
    sector = get_partner_sector(partner_id)
    metrics = {"total_placements": 0, "active_employees": 0, "retention_rate": None, "retention_savings": 0, "retention_savings_data": {}, "diversity_data": {}, "integration_data": {}, "avg_tenure_months": 0, "living_wage_percent": 0, "progression_count": 0, "training_count": 0, "employer_quotes": [], "candidate_quotes": [], "sector": sector, "placements_12m_plus": 0, "retained_12m_plus": 0, "suitability_details": []}
    placements = []
    candidates_dict = {}
    try:
        candidates_result = supabase.table("candidates").select("id, country_of_origin").execute()
        if candidates_result.data:
            candidates_dict = {c["id"]: c for c in candidates_result.data}
    except:
        pass
    try:
        result = supabase.table("placements").select("*").eq("partner_id", partner_id).in_("status", ["Published", "Left"]).execute()
        if result.data:
            placements = result.data
            metrics["total_placements"] = len(placements)
            active = [p for p in placements if p.get("status") == "Published"]
            metrics["active_employees"] = len(active)
            if active:
                total_months = sum((datetime.now() - datetime.fromisoformat(str(p["start_date"]))).days / 30 for p in active if p.get("start_date"))
                metrics["avg_tenure_months"] = round(total_months / len(active), 1)
            placements_12m_plus = [p for p in placements if p.get("start_date") and (datetime.now() - datetime.fromisoformat(str(p["start_date"]))).days / 30 >= 12]
            metrics["placements_12m_plus"] = len(placements_12m_plus)
            if placements_12m_plus:
                retained = [p for p in placements_12m_plus if p.get("status") == "Published"]
                metrics["retained_12m_plus"] = len(retained)
                metrics["retention_rate"] = round((len(retained) / len(placements_12m_plus)) * 100)
                savings_data = calculate_retention_savings(placements_12m_plus, sector, len(retained) / len(placements_12m_plus))
                metrics["retention_savings"] = savings_data["total_savings"]
                metrics["retention_savings_data"] = savings_data
            living_wage_count = sum(1 for p in placements if (p.get("hourly_rate") or 0) >= LIVING_WAGE_UK)
            if metrics["total_placements"] > 0:
                metrics["living_wage_percent"] = round((living_wage_count / metrics["total_placements"]) * 100)
            metrics["integration_data"] = calculate_integration_contribution(placements, candidates_dict)
            metrics["diversity_data"] = calculate_diversity_contribution(placements, candidates_dict)
    except:
        pass
    try:
        reviews = supabase.table("milestone_reviews_partner").select("*").eq("partner_id", partner_id).execute()
        if reviews.data:
            metrics["employer_quotes"] = [r.get("contribution_quote") for r in reviews.data if r.get("contribution_quote")]
            metrics["progression_count"] = sum(1 for r in reviews.data if r.get("progression"))
            metrics["training_count"] = sum(1 for r in reviews.data if r.get("received_training"))
    except:
        pass
    try:
        candidate_reviews = supabase.table("milestone_reviews_candidate").select("*").execute()
        if candidate_reviews.data:
            placement_ids = [p["id"] for p in placements]
            partner_candidate_reviews = [r for r in candidate_reviews.data if r.get("placement_id") in placement_ids]
            metrics["candidate_quotes"] = [r.get("feedback_quote") for r in partner_candidate_reviews if r.get("feedback_quote")]
    except:
        pass
    return metrics

def calculate_him_score(partner_id, metrics):
    him_score = {"total": 0, "business_impact": {"total": 0, "retention": {"score": 0, "retention_rate_points": 0, "uplift_points": 0}, "diversity": {"score": 0, "employee_points": 0, "country_points": 0}}, "social_impact": {"total": 0, "dimensions": {}, "employer_completed": False, "employee_responses": 0}}
    retention_rate = metrics.get("retention_rate")
    if retention_rate is None:
        total_placements = metrics.get("total_placements", 0)
        active = metrics.get("active_employees", 0)
        retention_rate = round((active / total_placements) * 100) if total_placements > 0 else 0
    retention_rate_points = min(100, retention_rate)
    savings_data = metrics.get("retention_savings_data", {})
    uplift = savings_data.get("retention_uplift_percent", 0)
    uplift_points = min(100, max(0, uplift * 5))
    him_score["business_impact"]["retention"]["retention_rate_points"] = round(retention_rate_points)
    him_score["business_impact"]["retention"]["uplift_points"] = round(uplift_points)
    him_score["business_impact"]["retention"]["score"] = round(retention_rate_points + uplift_points)
    diversity = metrics.get("diversity_data", {})
    employees = diversity.get("total_employees", 0)
    countries = diversity.get("countries_represented", 0)
    employee_points = min(100, employees * 20)
    country_points = min(100, countries * 25)
    him_score["business_impact"]["diversity"]["employee_points"] = employee_points
    him_score["business_impact"]["diversity"]["country_points"] = country_points
    him_score["business_impact"]["diversity"]["score"] = employee_points + country_points
    him_score["business_impact"]["total"] = him_score["business_impact"]["retention"]["score"] + him_score["business_impact"]["diversity"]["score"]
    dimension_names = {"economic_security": "Economic Security & Stability", "skill_growth": "Skill Use & Growth", "dignity_respect": "Workplace Dignity & Respect", "voice_agency": "Voice & Agency", "belonging_inclusion": "Social Belonging & Inclusion", "wellbeing": "Wellbeing & Confidence to Plan Ahead"}
    employer_scores = {}
    employee_scores = {}
    try:
        assessment = supabase.table("inclusion_assessment_org").select("scores").eq("partner_id", partner_id).order("created_at", desc=True).limit(1).execute()
        if assessment.data and assessment.data[0].get("scores"):
            him_score["social_impact"]["employer_completed"] = True
            scores = json.loads(assessment.data[0]["scores"]) if isinstance(assessment.data[0]["scores"], str) else assessment.data[0]["scores"]
            for dim_key in dimension_names.keys():
                if dim_key in scores:
                    employer_score = scores[dim_key].get("employer", 0)
                    if employer_score == 0:
                        employer_score = (scores[dim_key].get("input", 0) + scores[dim_key].get("conversion", 0)) / 2
                    employer_scores[dim_key] = employer_score
    except:
        pass
    try:
        placements = supabase.table("placements").select("id").eq("partner_id", partner_id).execute()
        if placements.data:
            placement_ids = [p["id"] for p in placements.data]
            reviews = supabase.table("milestone_reviews_candidate").select("scores, placement_id").execute()
            if reviews.data:
                partner_reviews = [r for r in reviews.data if r.get("placement_id") in placement_ids]
                him_score["social_impact"]["employee_responses"] = len(partner_reviews)
                dim_totals = {k: [] for k in dimension_names.keys()}
                for review in partner_reviews:
                    if review.get("scores"):
                        review_scores = json.loads(review["scores"]) if isinstance(review["scores"], str) else review["scores"]
                        for dim_key in dimension_names.keys():
                            if dim_key in review_scores:
                                dim_totals[dim_key].append(review_scores[dim_key].get("employee", 0))
                for dim_key, values in dim_totals.items():
                    if values:
                        employee_scores[dim_key] = sum(values) / len(values)
    except:
        pass
    for dim_key, dim_name in dimension_names.items():
        employer_val = employer_scores.get(dim_key, 0)
        employee_val = employee_scores.get(dim_key, 0)
        if employer_val > 0 and employee_val > 0:
            combined = (employer_val + employee_val) / 2
        elif employer_val > 0:
            combined = employer_val
        elif employee_val > 0:
            combined = employee_val
        else:
            combined = 0
        dimension_score = (combined / 5) * 100
        him_score["social_impact"]["dimensions"][dim_name] = round(dimension_score)
        him_score["social_impact"]["total"] += dimension_score
    him_score["social_impact"]["total"] = round(him_score["social_impact"]["total"])
    him_score["total"] = him_score["business_impact"]["total"] + him_score["social_impact"]["total"]
    return him_score

def get_pending_reviews(partner_id):
    pending = []
    try:
        placements = supabase.table("placements").select("*").eq("partner_id", partner_id).eq("status", "Published").execute()
        if placements.data:
            for p in placements.data:
                start_date = datetime.fromisoformat(p["start_date"]) if p.get("start_date") else None
                if start_date:
                    months_employed = (datetime.now() - start_date).days / 30
                    for m in [3, 6, 12]:
                        if months_employed >= m:
                            review = supabase.table("milestone_reviews_partner").select("*").eq("placement_id", p["id"]).eq("milestone_month", m).execute()
                            if not review.data:
                                pending.append({"candidate_name": p.get("candidate_name", "Unknown"), "milestone": f"{m}-month review", "due_date": (start_date + timedelta(days=m*30)).strftime("%d %b %Y"), "placement_id": p["id"], "milestone_month": m})
    except:
        pass
    return pending

def ach_dashboard():
    st.markdown('<p class="main-header">HIM Dashboard</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Overview of refugee employment outcomes and partner engagement</p>', unsafe_allow_html=True)
    try:
        partners = supabase.table("impact_partners").select("*").execute()
        candidates = supabase.table("candidates").select("*").execute()
        placements = supabase.table("placements").select("*").execute()
        reviews = supabase.table("milestone_reviews_partner").select("*").execute()
    except:
        partners = type('obj', (object,), {'data': []})()
        candidates = type('obj', (object,), {'data': []})()
        placements = type('obj', (object,), {'data': []})()
        reviews = type('obj', (object,), {'data': []})()
    partners_data = partners.data or []
    candidates_data = candidates.data or []
    placements_data = placements.data or []
    reviews_data = reviews.data or []
    st.markdown('<p class="section-header">Programme Overview</p>', unsafe_allow_html=True)
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Partners", len(partners_data))
    col2.metric("Total Candidates", len(candidates_data))
    col3.metric("Total Placements", len(placements_data))
    active_placements = [p for p in placements_data if p.get("status") == "Published"]
    col4.metric("Currently Employed", len(active_placements))
    retention = round((len(active_placements) / len(placements_data)) * 100) if placements_data else 0
    col5.metric("Overall Retention", f"{retention}%")
    col1, col2, col3, col4 = st.columns(4)
    available_candidates = [c for c in candidates_data if c.get("status") == "Available"]
    col1.metric("Available for Placement", len(available_candidates))
    progressions = sum(1 for r in reviews_data if r.get("progression"))
    col2.metric("Career Progressions", progressions)
    training = sum(1 for r in reviews_data if r.get("received_training"))
    col3.metric("Training Completed", training)
    countries = set(c.get("country_of_origin") for c in candidates_data if c.get("country_of_origin") and c.get("country_of_origin") not in ["United Kingdom", "UK", "Unknown", ""])
    col4.metric("Countries Represented", len(countries))
    st.markdown('<p class="section-header">Success Stories from Employers</p>', unsafe_allow_html=True)
    employer_quotes = [r.get("contribution_quote") for r in reviews_data if r.get("contribution_quote")]
    if employer_quotes:
        for quote in employer_quotes[:3]:
            st.markdown(f'<div class="quote-box">"{quote}"</div>', unsafe_allow_html=True)
    else:
        st.info("Success stories will appear here as employers complete milestone reviews")
    st.markdown('<p class="section-header">Partners by Type</p>', unsafe_allow_html=True)
    partner_types_count = {}
    for p in partners_data:
        ptype = p.get("partner_type", "Other")
        partner_types_count[ptype] = partner_types_count.get(ptype, 0) + 1
    if partner_types_count:
        cols = st.columns(len(partner_types_count))
        for i, (ptype, count) in enumerate(partner_types_count.items()):
            cols[i].metric(ptype, count)
    else:
        st.info("No partners registered yet")
    st.markdown('<p class="section-header">Recent Placements</p>', unsafe_allow_html=True)
    if placements_data:
        recent = sorted(placements_data, key=lambda x: x.get("created_at", ""), reverse=True)[:5]
        for p in recent:
            st.write(f"**{p.get('candidate_name', 'Unknown')}** started as {p.get('role', 'N/A')} at {p.get('partner_name', 'Unknown')} ({p.get('start_date', 'N/A')})")
    else:
        st.info("No placements yet")
    st.markdown('<p class="section-header">Pending Actions</p>', unsafe_allow_html=True)
    all_pending = []
    for p in partners_data:
        pending = get_pending_reviews(p.get("id"))
        for review in pending:
            review["partner_name"] = p.get("name", "Unknown")
        all_pending.extend(pending)
    if all_pending:
        for p in all_pending[:5]:
            st.warning(f"**{p['partner_name']}**: {p['candidate_name']} - {p['milestone']} due {p['due_date']}")
    else:
        st.success("All milestone reviews are up to date")

def ach_manage_partners():
    st.markdown('<p class="main-header">Manage Partners</p>', unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["View Partners", "Add Partner", "Edit Partner"])
    with tab1:
        try:
            partners = supabase.table("impact_partners").select("*").execute()
            if partners.data:
                for p in partners.data:
                    with st.expander(f"{p['name']} - {p.get('partner_type', 'N/A')} - {p.get('sector', 'N/A')}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Type:** {p.get('partner_type', 'N/A')}")
                            st.write(f"**Sector:** {p.get('sector', 'N/A')}")
                            st.write(f"**Employees:** {p.get('employee_count', 'N/A')}")
                            st.write(f"**Package:** {p.get('package_tier', 'Standard')}")
                        with col2:
                            st.write(f"**Contact:** {p.get('contact_name', 'N/A')}")
                            st.write(f"**Email:** {p.get('contact_email', 'N/A')}")
                            st.write(f"**Phone:** {p.get('contact_phone', 'N/A')}")
                        if st.button("🗑️ Delete Partner", key=f"delete_partner_{p['id']}", type="secondary"):
                            st.session_state[f"confirm_delete_partner_{p['id']}"] = True
                        if st.session_state.get(f"confirm_delete_partner_{p['id']}"):
                            st.warning(f"Are you sure you want to delete {p['name']}?")
                            col_yes, col_no = st.columns(2)
                            with col_yes:
                                if st.button("Yes, delete", key=f"confirm_yes_partner_{p['id']}"):
                                    try:
                                        supabase.table("milestone_reviews_partner").delete().eq("partner_id", p["id"]).execute()
                                        supabase.table("placements").delete().eq("partner_id", p["id"]).execute()
                                        supabase.table("interview_feedback").delete().eq("partner_id", p["id"]).execute()
                                        supabase.table("inclusion_assessment_org").delete().eq("partner_id", p["id"]).execute()
                                        supabase.table("impact_partners").delete().eq("id", p["id"]).execute()
                                        st.success(f"{p['name']} deleted")
                                        del st.session_state[f"confirm_delete_partner_{p['id']}"]
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error: {e}")
                            with col_no:
                                if st.button("Cancel", key=f"confirm_no_partner_{p['id']}"):
                                    del st.session_state[f"confirm_delete_partner_{p['id']}"]
                                    st.rerun()
            else:
                st.info("No partners registered yet")
        except:
            st.info("No partners registered yet")
    with tab2:
        with st.form("add_partner"):
            st.subheader("Add New Partner")
            name = st.text_input("Organisation Name *")
            partner_type = st.selectbox("Partner Type *", [""] + PARTNER_TYPES)
            sector = st.selectbox("Sector *", [""] + SECTORS)
            employee_count = st.selectbox("Number of Employees *", [""] + EMPLOYEE_RANGES)
            package_tier = st.selectbox("Package Tier *", ["Standard", "Impact Partner"])
            st.divider()
            st.subheader("Primary Contact")
            contact_name = st.text_input("Contact Name *")
            contact_email = st.text_input("Contact Email *")
            contact_phone = st.text_input("Phone (optional)")
            submitted = st.form_submit_button("Add Partner", use_container_width=True)
            if submitted:
                if not name or not partner_type or not sector or not contact_name or not contact_email:
                    st.error("Please fill in all required fields")
                else:
                    try:
                        data = {"name": name, "partner_type": partner_type, "sector": sector, "employee_count": employee_count, "package_tier": package_tier, "contact_name": contact_name, "contact_email": contact_email, "contact_phone": contact_phone, "created_at": datetime.now().isoformat()}
                        supabase.table("impact_partners").insert(data).execute()
                        st.success(f"{name} added successfully")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
    with tab3:
        try:
            partners = supabase.table("impact_partners").select("*").execute()
            if not partners.data:
                st.info("No partners to edit")
            else:
                partner_options = {p["name"]: p for p in partners.data}
                selected_name = st.selectbox("Select Partner to Edit", [""] + list(partner_options.keys()))
                if selected_name:
                    partner = partner_options[selected_name]
                    with st.form("edit_partner_form"):
                        edit_name = st.text_input("Organisation Name *", value=partner.get("name", ""))
                        partner_type_options = [""] + PARTNER_TYPES
                        current_type = partner.get("partner_type", "")
                        type_index = partner_type_options.index(current_type) if current_type in partner_type_options else 0
                        edit_partner_type = st.selectbox("Partner Type *", partner_type_options, index=type_index)
                        sector_options = [""] + SECTORS
                        current_sector = partner.get("sector", "")
                        sector_index = sector_options.index(current_sector) if current_sector in sector_options else 0
                        edit_sector = st.selectbox("Sector *", sector_options, index=sector_index)
                        employee_options = [""] + EMPLOYEE_RANGES
                        current_employees = partner.get("employee_count", "")
                        employee_index = employee_options.index(current_employees) if current_employees in employee_options else 0
                        edit_employee_count = st.selectbox("Number of Employees *", employee_options, index=employee_index)
                        package_options = ["Standard", "Impact Partner"]
                        current_package = partner.get("package_tier", "Standard")
                        package_index = package_options.index(current_package) if current_package in package_options else 0
                        edit_package_tier = st.selectbox("Package Tier *", package_options, index=package_index)
                        st.divider()
                        edit_contact_name = st.text_input("Contact Name *", value=partner.get("contact_name", ""))
                        edit_contact_email = st.text_input("Contact Email *", value=partner.get("contact_email", ""))
                        edit_contact_phone = st.text_input("Phone (optional)", value=partner.get("contact_phone", ""))
                        save_clicked = st.form_submit_button("Save Changes", use_container_width=True, type="primary")
                        if save_clicked:
                            if not edit_name or not edit_partner_type or not edit_sector or not edit_contact_name or not edit_contact_email:
                                st.error("Please fill in all required fields")
                            else:
                                try:
                                    update_data = {"name": edit_name, "partner_type": edit_partner_type, "sector": edit_sector, "employee_count": edit_employee_count, "package_tier": edit_package_tier, "contact_name": edit_contact_name, "contact_email": edit_contact_email, "contact_phone": edit_contact_phone, "updated_at": datetime.now().isoformat()}
                                    supabase.table("impact_partners").update(update_data).eq("id", partner["id"]).execute()
                                    st.success(f"{edit_name} updated successfully!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error: {e}")
        except Exception as e:
            st.error(f"Error: {e}")

def ach_manage_candidates():
    st.markdown('<p class="main-header">Manage Candidates</p>', unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["View Candidates", "Add Candidate"])
    with tab1:
        try:
            candidates = supabase.table("candidates").select("*").execute()
            if candidates.data:
                for c in candidates.data:
                    with st.expander(f"{c['name']} - {c.get('status', 'N/A')}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Name:** {c['name']}")
                            st.write(f"**Cohort:** {c.get('cohort', 'N/A')}")
                            st.write(f"**Country:** {c.get('country_of_origin', 'N/A')}")
                            st.write(f"**Status:** {c.get('status', 'N/A')}")
                        with col2:
                            new_status = st.selectbox("Change Status", ["Available", "Placed", "Inactive"], index=["Available", "Placed", "Inactive"].index(c.get('status', 'Available')) if c.get('status') in ["Available", "Placed", "Inactive"] else 0, key=f"status_{c['id']}")
                            if new_status != c.get('status'):
                                if st.button("Update Status", key=f"update_status_{c['id']}"):
                                    try:
                                        supabase.table("candidates").update({"status": new_status}).eq("id", c["id"]).execute()
                                        st.success(f"Status updated to {new_status}")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error: {e}")
                        if st.button("🗑️ Delete Candidate", key=f"delete_candidate_{c['id']}", type="secondary"):
                            st.session_state[f"confirm_delete_{c['id']}"] = True
                        if st.session_state.get(f"confirm_delete_{c['id']}"):
                            st.warning(f"Are you sure you want to delete {c['name']}?")
                            col_yes, col_no = st.columns(2)
                            with col_yes:
                                if st.button("Yes, delete", key=f"confirm_yes_{c['id']}"):
                                    try:
                                        supabase.table("interview_feedback").delete().eq("candidate_id", c["id"]).execute()
                                        supabase.table("placements").delete().eq("candidate_id", c["id"]).execute()
                                        supabase.table("candidates").delete().eq("id", c["id"]).execute()
                                        st.success(f"{c['name']} deleted")
                                        del st.session_state[f"confirm_delete_{c['id']}"]
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error: {e}")
                            with col_no:
                                if st.button("Cancel", key=f"confirm_no_{c['id']}"):
                                    del st.session_state[f"confirm_delete_{c['id']}"]
                                    st.rerun()
            else:
                st.info("No candidates registered yet")
        except:
            st.info("No candidates registered yet")
    with tab2:
        with st.form("add_candidate"):
            name = st.text_input("Full Name *")
            cohort = st.text_input("Cohort/Programme *")
            country_of_origin = st.selectbox("Country of Origin *", ALL_COUNTRIES)
            submitted = st.form_submit_button("Add Candidate", use_container_width=True)
            if submitted:
                if not name or not country_of_origin:
                    st.error("Please fill in required fields")
                else:
                    try:
                        data = {"name": name, "cohort": cohort, "country_of_origin": country_of_origin, "status": "Available", "created_at": datetime.now().isoformat()}
                        supabase.table("candidates").insert(data).execute()
                        st.success(f"{name} added successfully")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

def ach_capability_assessment():
    st.markdown('<p class="main-header">Candidate Holistic Impact Assessment</p>', unsafe_allow_html=True)
    st.info("Candidate capability assessment interface - coming soon")

def ach_candidate_support():
    st.markdown('<p class="main-header">Candidate Support</p>', unsafe_allow_html=True)
    st.info("Candidate milestone check-in interface - coming soon")

def partner_dashboard():
    st.markdown('<p class="main-header">Your Impact Dashboard</p>', unsafe_allow_html=True)
    partner_id = st.session_state.get("user_id", 1)
    partner_tier = "Standard"
    try:
        partner_data = supabase.table("impact_partners").select("package_tier").eq("id", partner_id).execute()
        if partner_data.data:
            partner_tier = partner_data.data[0].get("package_tier", "Standard")
    except:
        pass
    metrics = calculate_impact_metrics(partner_id)
    him_score = calculate_him_score(partner_id, metrics)
    if partner_tier == "Impact Partner":
        st.markdown("""<style>.him-score-card { background: linear-gradient(135deg, #0f1c3f 0%, #1a2d5a 100%); border-radius: 20px; padding: 40px; text-align: center; margin-bottom: 30px; color: white; } .him-score-value { font-size: 4rem; font-weight: 700; margin-bottom: 10px; } .him-progress-bar { background: rgba(255,255,255,0.2); border-radius: 10px; height: 12px; margin-top: 20px; overflow: hidden; } .him-progress-fill { background: linear-gradient(90deg, #22c55e 0%, #16a34a 100%); height: 100%; border-radius: 10px; } .impact-section { background: white; border-radius: 16px; padding: 25px; margin-bottom: 20px; border: 1px solid #e2e8f0; } .impact-section-title { font-size: 1.1rem; font-weight: 600; color: #0f1c3f; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 2px solid #e2e8f0; }</style>""", unsafe_allow_html=True)
        him_total = him_score["total"]
        him_percentage = (him_total / 1000) * 100
        if him_total > 0:
            st.markdown(f'<div class="him-score-card"><div style="font-size: 1rem; opacity: 0.9; margin-bottom: 10px; letter-spacing: 2px; text-transform: uppercase;">Holistic Impact Score</div><div class="him-score-value">{him_total}<span style="font-size: 1.5rem; color: #94a3b8;"> / 1000</span></div><div class="him-progress-bar"><div class="him-progress-fill" style="width: {him_percentage}%;"></div></div></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="him-score-card"><div style="font-size: 1rem; opacity: 0.9; margin-bottom: 10px; letter-spacing: 2px; text-transform: uppercase;">Holistic Impact Score</div><div style="font-size: 1rem; color: #94a3b8; padding: 20px 0;">Your Holistic Impact Score will appear as you record placements and complete the Holistic Impact Assessment</div></div>', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        retention_rate = metrics.get("retention_rate")
        has_12m_data = retention_rate is not None
        if retention_rate is None:
            retention_rate = 0
        diversity = metrics.get("diversity_data", {})
        employees = diversity.get("total_employees", 0)
        countries = diversity.get("countries_represented", 0)
        with col1:
            st.markdown('<div class="impact-section">', unsafe_allow_html=True)
            st.markdown('<div class="impact-section-title">Business Impact Generated</div>', unsafe_allow_html=True)
            savings = metrics.get("retention_savings", 0)
            col_a, col_b = st.columns([2, 1])
            col_a.write("12-Month Retention")
            col_b.write(f"**{retention_rate}%**" if has_12m_data else "**No data yet**")
            col_a, col_b = st.columns([2, 1])
            col_a.write("Estimated Retention Savings")
            col_b.write(f"**£{savings:,.0f}**" if savings > 0 else "**No data yet**")
            col_a, col_b = st.columns([2, 1])
            col_a.write("Diversity Contribution")
            col_b.write(f"**{employees} employees, {countries} countries**" if employees > 0 else "**No data yet**")
            st.markdown('</div>', unsafe_allow_html=True)
        with col2:
            st.markdown('<div class="impact-section">', unsafe_allow_html=True)
            st.markdown('<div class="impact-section-title">Social Impact Created</div>', unsafe_allow_html=True)
            social_dims = him_score['social_impact']['dimensions']
            employer_completed = him_score['social_impact']['employer_completed']
            employee_responses = him_score['social_impact']['employee_responses']
            if employer_completed or employee_responses > 0:
                for dim_name, dim_score in social_dims.items():
                    col_a, col_b = st.columns([2, 1])
                    col_a.write(dim_name)
                    col_b.write(f"**{dim_score}%**")
                sources = []
                if employer_completed:
                    sources.append("Employer assessment")
                if employee_responses > 0:
                    sources.append(f"{employee_responses} employee response(s)")
                st.caption(f"Based on: {' + '.join(sources)}")
            else:
                st.info("Complete the Holistic Impact Assessment to see your Social Impact scores")
            st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('<p class="section-header">Estimated Retention Savings Breakdown</p>', unsafe_allow_html=True)
        savings_data = metrics.get("retention_savings_data", {})
        retention_rate_12m = metrics.get("retention_rate")
        if retention_rate_12m is not None and savings_data:
            st.caption(f"Based on {metrics.get('placements_12m_plus', 0)} placements that have reached 12 months")
            ach_rate = savings_data.get('ach_retention_percent', 0)
            industry_rate = savings_data.get('industry_retention_percent', 0)
            difference = savings_data.get('retention_uplift_percent', 0)
            col1, col2, col3 = st.columns(3)
            col1.metric("Your Retention Rate", f"{ach_rate}%")
            col2.metric("Industry Average", f"{industry_rate}%")
            col3.metric("Your Uplift", f"+{difference}%")
            st.caption(savings_data.get('methodology', ''))
        else:
            st.caption("Retention savings data will appear once placements reach 12 months")
        st.markdown('<p class="section-header">What Your Employees Say</p>', unsafe_allow_html=True)
        candidate_quotes = metrics.get("candidate_quotes", [])
        if candidate_quotes:
            for quote in candidate_quotes[:3]:
                st.markdown(f'<div class="quote-box">"{quote}"</div>', unsafe_allow_html=True)
        else:
            st.info("Employee feedback will appear here as candidates complete their milestone reviews")
        pending = get_pending_reviews(partner_id)
        if pending:
            st.markdown('<p class="section-header">Action Required</p>', unsafe_allow_html=True)
            for p in pending:
                st.warning(f"**{p['candidate_name']}** — {p['milestone']} due {p['due_date']}")
    else:
        st.markdown("""<style>.locked-metric { background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%); border-radius: 12px; padding: 20px; text-align: center; margin: 10px 0; } .locked-value { font-size: 2rem; font-weight: 700; color: #94a3b8; letter-spacing: 3px; } .locked-label { font-size: 0.9rem; color: #64748b; margin-top: 5px; } .upgrade-box { background: linear-gradient(135deg, #0f1c3f 0%, #1a2d5a 100%); border-radius: 12px; padding: 30px; color: white; text-align: center; margin: 30px 0; }</style>""", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="locked-metric"><div class="locked-value">£████████</div><div class="locked-label">Estimated Retention Savings</div></div>', unsafe_allow_html=True)
        with col2:
            diversity = metrics.get("diversity_data", {})
            employees = diversity.get("total_employees", 0)
            if employees > 0:
                st.markdown(f'<div class="locked-metric"><div class="locked-value">{employees} employees</div><div class="locked-label">Diversity Contribution</div></div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="locked-metric"><div class="locked-value">██████</div><div class="locked-label">Diversity Contribution</div></div>', unsafe_allow_html=True)
        st.markdown('<div class="upgrade-box"><h3 style="margin-bottom: 15px;">Unlock Your Full Impact Dashboard</h3><p>Opt in to our <strong>Workforce Integration Package</strong> to unlock:</p><p>• Full retention savings calculations<br>• Diversity contribution insights<br>• Social impact reporting<br>• Retention guarantee<br>• Corporate training</p></div>', unsafe_allow_html=True)
        if st.button("Learn More About Impact Partnership", use_container_width=True):
            st.info("Contact ACH to become an Impact Partner and unlock your full dashboard.")
        pending = get_pending_reviews(partner_id)
        if pending:
            st.markdown('<p class="section-header">Action Required</p>', unsafe_allow_html=True)
            for p in pending:
                st.warning(f"**{p['candidate_name']}** - {p['milestone']} due {p['due_date']}")

def partner_inclusion_assessment():
    st.markdown('<p class="main-header">Holistic Impact Assessment</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Rate your organisation across six capability domains</p>', unsafe_allow_html=True)
    partner_id = st.session_state.get("user_id", 1)
    st.info("This assessment measures your organisation's enablement of employee capabilities.")
    with st.form("holistic_impact_assessment"):
        scores = {}
        for dim_key, dim_data in HOLISTIC_IMPACT_QUESTIONS.items():
            st.markdown(f"### {dim_data['name']}")
            st.caption(dim_data['description'])
            scores[dim_key] = {}
            scores[dim_key]["employer"] = st.slider(dim_data["employer"], 1, 5, 3, key=f"{dim_key}_employer", help="1 = Strongly Disagree, 5 = Strongly Agree")
            st.divider()
        submitted = st.form_submit_button("Submit Assessment", use_container_width=True)
        if submitted:
            try:
                data = {"partner_id": partner_id, "scores": json.dumps(scores), "created_at": datetime.now().isoformat()}
                supabase.table("inclusion_assessment_org").insert(data).execute()
                st.success("Assessment submitted successfully")
            except Exception as e:
                st.error(f"Error: {e}")

def partner_candidates():
    st.markdown('<p class="main-header">Candidates</p>', unsafe_allow_html=True)
    partner_id = st.session_state.get("user_id", 1)
    tab1, tab2, tab3 = st.tabs(["Recruitment", "Milestone Review", "Current Employees"])
    with tab1:
        st.markdown('<p class="sub-header">Record interview outcomes and new hires</p>', unsafe_allow_html=True)
        try:
            candidates = supabase.table("candidates").select("*").eq("status", "Available").execute()
            if not candidates.data:
                st.info("No candidates available for recruitment")
            else:
                candidate = st.selectbox("Candidate *", [""] + [c["name"] for c in candidates.data])
                role = st.text_input("Role *")
                salary = st.number_input("Annual Salary (£) *", min_value=0, value=22500)
                interview_date = st.date_input("Interview Date", format="DD/MM/YYYY")
                st.divider()
                hired = st.radio("Offered Position? *", ["Yes", "No"], horizontal=True)
                if hired == "Yes":
                    feedback_text = st.text_area("What stood out about this candidate?")
                    start_date = st.date_input("Start Date", format="DD/MM/YYYY")
                else:
                    feedback_text = st.text_area("Reason for not progressing")
                    start_date = None
                st.divider()
                confirmed = st.checkbox("I have reviewed this information and confirm it is correct")
                if st.button("Submit", use_container_width=True):
                    if not candidate or not role:
                        st.error("Please fill in required fields")
                    elif not confirmed:
                        st.error("Please confirm you have reviewed the information")
                    else:
                        try:
                            cand_data = next(c for c in candidates.data if c["name"] == candidate)
                            feedback = {"partner_id": partner_id, "candidate_id": cand_data["id"], "candidate_name": candidate, "role": role, "interview_date": interview_date.isoformat(), "hired": hired == "Yes", "standout_reason": feedback_text if hired == "Yes" else None, "rejection_reason": feedback_text if hired == "No" else None, "created_at": datetime.now().isoformat()}
                            supabase.table("interview_feedback").insert(feedback).execute()
                            if hired == "Yes":
                                partner = supabase.table("impact_partners").select("name").eq("id", partner_id).execute()
                                partner_name = partner.data[0]["name"] if partner.data else "Unknown"
                                placement = {"partner_id": partner_id, "partner_name": partner_name, "candidate_id": cand_data["id"], "candidate_name": candidate, "role": role, "start_date": start_date.isoformat(), "salary": salary, "hourly_rate": round(salary / 52 / 40, 2), "status": "Published", "created_at": datetime.now().isoformat()}
                                supabase.table("placements").insert(placement).execute()
                                supabase.table("candidates").update({"status": "Placed"}).eq("id", cand_data["id"]).execute()
                                st.success(f"{candidate} hired successfully")
                            else:
                                st.success("Feedback recorded")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
        except Exception as e:
            st.error(f"Error: {e}")
    with tab2:
        st.markdown('<p class="sub-header">Complete milestone reviews for your employees</p>', unsafe_allow_html=True)
        pending = get_pending_reviews(partner_id)
        if not pending:
            st.success("All reviews are up to date")
        else:
            st.warning(f"{len(pending)} review(s) pending")
            for review in pending:
                with st.expander(f"{review['candidate_name']} - {review['milestone']} (Due: {review['due_date']})"):
                    with st.form(f"review_{review['placement_id']}_{review['milestone_month']}"):
                        still_employed = st.radio("Still employed?", ["Yes", "No"], horizontal=True)
                        if still_employed == "Yes":
                            st.markdown("**Candidate Suitability Assessment**")
                            suitability_ratings = {}
                            for category in SUITABILITY_CATEGORIES:
                                suitability_ratings[category] = st.selectbox(category, SUITABILITY_RATINGS, key=f"suit_{review['placement_id']}_{category}")
                            suitability_notes = st.text_area("Additional notes on performance", key=f"suit_notes_{review['placement_id']}")
                            st.divider()
                            received_training = st.radio("Received training?", ["Yes", "No"], horizontal=True, key=f"training_{review['placement_id']}")
                            training_details = None
                            if received_training == "Yes":
                                training_details = st.text_area("Training details", key=f"training_details_{review['placement_id']}")
                            progression = st.radio("Any progression?", ["Yes", "No"], horizontal=True, key=f"progression_{review['placement_id']}")
                            progression_details = None
                            if progression == "Yes":
                                progression_details = st.text_area("Progression details", key=f"progression_details_{review['placement_id']}")
                            st.divider()
                            contribution_quote = st.text_area("Describe their contribution", key=f"contribution_{review['placement_id']}")
                        else:
                            leaving_reason = st.selectbox("Reason", ["Resigned", "Dismissed", "Redundancy", "Contract ended", "Other"], key=f"leaving_{review['placement_id']}")
                            suitability_ratings = {}
                            suitability_notes = None
                            received_training = "No"
                            training_details = None
                            progression = "No"
                            progression_details = None
                            contribution_quote = None
                        submitted = st.form_submit_button("Submit", use_container_width=True)
                        if submitted:
                            try:
                                data = {"placement_id": review["placement_id"], "partner_id": partner_id, "candidate_name": review["candidate_name"], "milestone_month": review["milestone_month"], "still_employed": still_employed == "Yes", "suitability_ratings": json.dumps(suitability_ratings) if suitability_ratings else None, "suitability_notes": suitability_notes, "received_training": received_training == "Yes" if still_employed == "Yes" else None, "training_details": training_details, "progression": progression == "Yes" if still_employed == "Yes" else None, "progression_details": progression_details, "contribution_quote": contribution_quote if still_employed == "Yes" else None, "leaving_reason": leaving_reason if still_employed == "No" else None, "created_at": datetime.now().isoformat()}
                                supabase.table("milestone_reviews_partner").insert(data).execute()
                                placement_update = {"last_milestone_check": datetime.now().date().isoformat(), "last_milestone_month": review["milestone_month"]}
                                if still_employed == "No":
                                    placement_update["status"] = "Left"
                                    placement_update["end_date"] = datetime.now().date().isoformat()
                                supabase.table("placements").update(placement_update).eq("id", review["placement_id"]).execute()
                                st.success("Review submitted")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")
    with tab3:
        st.markdown('<p class="sub-header">View current employee details</p>', unsafe_allow_html=True)
        try:
            placements = supabase.table("placements").select("*").eq("partner_id", partner_id).eq("status", "Published").execute()
            if not placements.data:
                st.info("No current employees")
            else:
                for placement in placements.data:
                    with st.expander(f"{placement['candidate_name']} - {placement['role']}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Role:** {placement['role']}")
                            st.write(f"**Salary:** £{placement.get('salary', 0):,}")
                            current_start = datetime.fromisoformat(placement['start_date']).date() if placement.get('start_date') else datetime.now().date()
                            st.write(f"**Start Date:** {current_start.strftime('%d/%m/%Y')}")
                        with col2:
                            if placement.get('start_date'):
                                start = datetime.fromisoformat(placement['start_date'])
                                tenure_months = round((datetime.now() - start).days / 30, 1)
                                st.write(f"**Tenure:** {tenure_months} months")
                        st.divider()
                        new_start_date = st.date_input("Edit Start Date", value=current_start, format="DD/MM/YYYY", key=f"start_date_{placement['id']}")
                        if st.button("Update Start Date", key=f"update_{placement['id']}"):
                            try:
                                supabase.table("placements").update({"start_date": new_start_date.isoformat()}).eq("id", placement["id"]).execute()
                                st.success("Start date updated")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")
        except Exception as e:
            st.error(f"Error: {e}")

def partner_reports():
    st.markdown('<p class="main-header">Impact Reports</p>', unsafe_allow_html=True)
    partner_id = st.session_state.get("user_id", 1)
    metrics = calculate_impact_metrics(partner_id)
    him_score = calculate_him_score(partner_id, metrics)
    if metrics["total_placements"] == 0:
        st.warning("No placements yet. Reports will be available once you have placed candidates.")
        return
    partner_name = st.session_state.user_name
    st.markdown(f"### Impact Report: {partner_name}")
    st.markdown(f"**Generated:** {datetime.now().strftime('%d %B %Y')}")
    st.divider()
    st.markdown("### Executive Summary")
    total_placements = metrics.get("total_placements", 0)
    integration_data = metrics.get("integration_data", {})
    person_months = integration_data.get("total_person_months", 0)
    countries = metrics.get("diversity_data", {}).get("countries_represented", 0)
    retention_rate = metrics.get("retention_rate", 0) or 0
    retention_savings = metrics.get("retention_savings", 0)
    st.markdown(f"Through your partnership with ACH, your organisation has created **{total_placements} jobs** for members of the refugee and migrant community, representing **{round(person_months)} person-months** of sustained employment across **{countries} countries** of origin. This demonstrates a meaningful contribution to refugee integration and social cohesion in the UK.")
    st.markdown(f"**Your Holistic Impact Metric Score: {him_score['total']} / 1000**")
    st.markdown("**You have scored as follows across the impact areas:**")
    st.divider()
    st.markdown("### Business Value Generated")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Retention Performance**")
        st.write(f"- 12-Month Retention Rate: **{retention_rate}%**")
        st.write(f"- Estimated Retention Savings: **£{retention_savings:,.0f}**")
        savings_data = metrics.get("retention_savings_data", {})
        if savings_data:
            industry_rate = savings_data.get('industry_retention_percent', 0)
            uplift = savings_data.get('retention_uplift_percent', 0)
            st.write(f"- Industry Average: **{industry_rate}%**")
            st.write(f"- Your Uplift: **+{uplift}%**")
    with col2:
        st.markdown("**Employment Outcomes**")
        st.write(f"- Total Placements: **{metrics['total_placements']}**")
        st.write(f"- Currently Employed: **{metrics['active_employees']}**")
        st.write(f"- Average Tenure: **{metrics.get('avg_tenure_months', 0)} months**")
        st.write(f"- Living Wage Roles: **{metrics['living_wage_percent']}%**")
    st.divider()
    st.markdown("### Social Impact Created")
    social_dims = him_score['social_impact']['dimensions']
    if social_dims and any(v > 0 for v in social_dims.values()):
        col1, col2 = st.columns(2)
        dims_list = list(social_dims.items())
        half = len(dims_list) // 2
        with col1:
            for dim_name, dim_score in dims_list[:half]:
                st.write(f"- {dim_name}: **{dim_score}%**")
        with col2:
            for dim_name, dim_score in dims_list[half:]:
                st.write(f"- {dim_name}: **{dim_score}%**")
        sources = []
        if him_score['social_impact']['employer_completed']:
            sources.append("Employer assessment")
        if him_score['social_impact']['employee_responses'] > 0:
            sources.append(f"{him_score['social_impact']['employee_responses']} employee response(s)")
        st.caption(f"Based on: {' + '.join(sources)}")
    else:
        st.info("Complete the Holistic Impact Assessment to include social impact data in your reports")
    st.divider()
    st.markdown("### Employee Development")
    col1, col2 = st.columns(2)
    col1.metric("Employees Trained", metrics['training_count'])
    col2.metric("Career Progressions", metrics['progression_count'])
    st.divider()
    if metrics.get("candidate_quotes"):
        st.markdown("### Employee Testimonials")
        for quote in metrics["candidate_quotes"][:3]:
            st.markdown(f'> "{quote}"')

def main():
    with st.sidebar:
        name_placeholder = st.empty()
        st.divider()
        view_type = st.radio("View As", ["ACH Staff", "Partner"], label_visibility="collapsed")
        if view_type == "Partner":
            try:
                partners = supabase.table("impact_partners").select("id, name").execute()
                if partners.data:
                    partner_options = {p["name"]: p["id"] for p in partners.data}
                    selected_partner = st.selectbox("Select Partner", list(partner_options.keys()))
                    st.session_state.user_type = "partner"
                    st.session_state.user_id = partner_options[selected_partner]
                    st.session_state.user_name = selected_partner
                else:
                    st.warning("No partners found")
                    st.session_state.user_type = "ach_staff"
                    st.session_state.user_name = "ACH Administrator"
            except:
                st.warning("No partners found")
                st.session_state.user_type = "ach_staff"
                st.session_state.user_name = "ACH Administrator"
        else:
            st.session_state.user_type = "ach_staff"
            st.session_state.user_name = "ACH Administrator"
        name_placeholder.markdown(f"### {st.session_state.user_name}")
        st.divider()
        if st.session_state.user_type == "ach_staff":
            page = st.radio("Navigation", ["Dashboard", "Manage Partners", "Manage Candidates", "Holistic Impact Assessment", "Candidate Support"], label_visibility="collapsed")
        else:
            page = st.radio("Navigation", ["Dashboard", "Candidates", "Holistic Impact Assessment", "Reports"], label_visibility="collapsed")
    if st.session_state.user_type == "ach_staff":
        pages = {"Dashboard": ach_dashboard, "Manage Partners": ach_manage_partners, "Manage Candidates": ach_manage_candidates, "Holistic Impact Assessment": ach_capability_assessment, "Candidate Support": ach_candidate_support}
    else:
        pages = {"Dashboard": partner_dashboard, "Holistic Impact Assessment": partner_inclusion_assessment, "Candidates": partner_candidates, "Reports": partner_reports}
    pages[page]()

if __name__ == "__main__":
    main()
