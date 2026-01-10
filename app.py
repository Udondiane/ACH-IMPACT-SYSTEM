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

# ============ INCLUSION CAPABILITY INDEX QUESTIONS ============

# ORGANISATION QUESTIONS (Employer completes - all scale 1-5)
ORGANISATION_QUESTIONS = {
    "economic_security": {
        "name": "Economic Security and Stability",
        "input": "To what extent does the organisation provide stable contracts, transparent pay, and predictable working hours for refugee employees?",
        "conversion": "To what extent are pay and shift arrangements implemented transparently and communicated effectively in daily practice?",
        "capability": "To what extent do refugee employees feel economically secure and able to rely on their work for a stable livelihood?"
    },
    "skill_growth": {
        "name": "Skill Use and Growth",
        "input": "To what extent does the organisation provide access to relevant training and skill development opportunities?",
        "conversion": "To what extent can refugee employees realistically participate in these learning opportunities (e.g., scheduling, eligibility, support)?",
        "capability": "To what extent do refugee employees feel they can use their skills and grow professionally in their roles?"
    },
    "dignity_respect": {
        "name": "Workplace Dignity and Respect",
        "input": "To what extent does the organisation have formal policies ensuring equal treatment and preventing discrimination?",
        "conversion": "To what extent do managers and coworkers behave respectfully and apply these policies consistently?",
        "capability": "To what extent do refugee employees experience dignity and equal respect in daily work life?"
    },
    "voice_agency": {
        "name": "Voice and Agency",
        "input": "To what extent does the organisation provide formal channels for refugee employees to express feedback or concerns?",
        "conversion": "To what extent are refugee employees' voices heard and acted upon by management?",
        "capability": "To what extent do refugee employees feel confident and empowered to influence decisions affecting their work?"
    },
    "belonging_inclusion": {
        "name": "Social Belonging and Inclusion",
        "input": "To what extent does the organisation provide initiatives to support social connection and inclusion (e.g., buddy schemes, cultural events)?",
        "conversion": "To what extent do managers and teams actively encourage inclusive interactions in daily work?",
        "capability": "To what extent do refugee employees feel part of the team and socially connected within the organisation?"
    },
    "wellbeing": {
        "name": "Wellbeing and Confidence to Plan Ahead",
        "input": "To what extent does the organisation provide wellbeing and health support (e.g., rest time, counselling access, workload policy)?",
        "conversion": "To what extent can refugee employees actually use these wellbeing supports without stigma or barriers?",
        "capability": "To what extent do refugee employees feel safe, healthy, and able to plan their personal and work futures?"
    }
}

# CANDIDATE QUESTIONS (Employee completes - mix of scale and narrative)
CANDIDATE_QUESTIONS = {
    "economic_security": {
        "name": "Economic Security and Stability",
        "input": {
            "type": "narrative",
            "question": "Can you describe how predictable your work and income feel here? What helps you feel secure - or makes it hard?"
        },
        "conversion": {
            "type": "narrative",
            "question": "When schedules or pay change, how do you usually find out? How does that make you feel about the stability of your job?"
        },
        "capability": {
            "type": "scale",
            "question": "Do you feel your income and working hours are reliable enough to plan your life ahead?"
        }
    },
    "skill_growth": {
        "name": "Skill Use and Growth",
        "input": {
            "type": "narrative",
            "question": "What kinds of learning or training opportunities do you know about here?"
        },
        "conversion": {
            "type": "narrative",
            "question": "Can you share a time you wanted to join training or learn new skills - what helped or stopped you?"
        },
        "capability": {
            "type": "narrative",
            "question": "Can you describe a moment when you were able to use your abilities fully at work?"
        }
    },
    "dignity_respect": {
        "name": "Workplace Dignity and Respect",
        "input": {
            "type": "narrative",
            "question": "Have you been told about policies that protect fairness or respect at work?"
        },
        "conversion": {
            "type": "narrative",
            "question": "How are you usually treated by colleagues or supervisors? Can you recall a time that made you feel respected - or not?"
        },
        "capability": {
            "type": "scale",
            "question": "Do you feel respected and valued as a person here?"
        }
    },
    "voice_agency": {
        "name": "Voice and Agency",
        "input": {
            "type": "narrative",
            "question": "Are there ways for you to share your opinions or issues with management?"
        },
        "conversion": {
            "type": "narrative",
            "question": "Can you tell me about a time when you spoke up about something at work? What happened afterwards?"
        },
        "capability": {
            "type": "scale",
            "question": "Do you feel you can make choices or influence how your work is done?"
        }
    },
    "belonging_inclusion": {
        "name": "Social Belonging and Inclusion",
        "input": {
            "type": "narrative",
            "question": "When you first joined, were there any activities that helped you meet people or feel included?"
        },
        "conversion": {
            "type": "narrative",
            "question": "Can you describe how your team works together day to day? Do you feel comfortable joining conversations?"
        },
        "capability": {
            "type": "narrative",
            "question": "What makes you feel you belong here - or sometimes, what makes you feel apart?"
        }
    },
    "wellbeing": {
        "name": "Wellbeing and Confidence to Plan Ahead",
        "input": {
            "type": "narrative",
            "question": "What kinds of wellbeing or health support are available to you here?"
        },
        "conversion": {
            "type": "narrative",
            "question": "If you need time off or help for health reasons, how easy is it to ask for and receive support?"
        },
        "capability": {
            "type": "scale",
            "question": "Do you feel safe and confident about your future here?"
        }
    }
}

# Score bands for Inclusion Capability Index
SCORE_BANDS = [
    {"min": 0, "max": 40, "label": "Foundational", "description": "Basic structures missing or not yet established"},
    {"min": 41, "max": 60, "label": "Developing", "description": "Policies exist but gaps remain in practice"},
    {"min": 61, "max": 80, "label": "Established", "description": "Good practice with some areas to strengthen"},
    {"min": 81, "max": 100, "label": "Leading", "description": "Strong inclusion capability across all areas"}
]


def get_score_band(score):
    for band in SCORE_BANDS:
        if band["min"] <= score <= band["max"]:
            return band
    return SCORE_BANDS[0]


# ============ REPLACEMENT COST MULTIPLIERS ============
def get_replacement_multiplier(salary):
    if salary < 24000:
        return 0.15
    elif salary < 28000:
        return 0.18
    elif salary < 35000:
        return 0.22
    elif salary < 45000:
        return 0.25
    else:
        return 0.30


def calculate_retention_savings(placements, sector, ach_retention_rate):
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


def calculate_inclusion_index(org_scores, candidate_scores):
    """
    Calculate the Inclusion Capability Index from organisation and candidate responses.
    
    org_scores: dict of dimension -> {input: 1-5, conversion: 1-5, capability: 1-5}
    candidate_scores: dict of dimension -> {input: 1-5 or None, conversion: 1-5 or None, capability: 1-5 or None}
    
    Returns overall score (0-100) and dimension breakdown
    """
    dimensions = ["economic_security", "skill_growth", "dignity_respect", "voice_agency", "belonging_inclusion", "wellbeing"]
    
    dimension_scores = {}
    total_org_score = 0
    total_candidate_score = 0
    total_org_max = 0
    total_candidate_max = 0
    
    for dim in dimensions:
        org_dim = org_scores.get(dim, {})
        cand_dim = candidate_scores.get(dim, {})
        
        # Organisation scores (all are 1-5 scale)
        org_input = org_dim.get("input", 0)
        org_conversion = org_dim.get("conversion", 0)
        org_capability = org_dim.get("capability", 0)
        org_total = org_input + org_conversion + org_capability
        org_max = 15
        
        # Candidate scores (only scale questions counted)
        cand_input = cand_dim.get("input", 0) if cand_dim.get("input") else 0
        cand_conversion = cand_dim.get("conversion", 0) if cand_dim.get("conversion") else 0
        cand_capability = cand_dim.get("capability", 0) if cand_dim.get("capability") else 0
        
        # Count how many scale questions exist for this dimension
        cand_scale_count = 0
        cand_total = 0
        if CANDIDATE_QUESTIONS[dim]["input"]["type"] == "scale" and cand_input:
            cand_total += cand_input
            cand_scale_count += 1
        if CANDIDATE_QUESTIONS[dim]["conversion"]["type"] == "scale" and cand_conversion:
            cand_total += cand_conversion
            cand_scale_count += 1
        if CANDIDATE_QUESTIONS[dim]["capability"]["type"] == "scale" and cand_capability:
            cand_total += cand_capability
            cand_scale_count += 1
        
        cand_max = cand_scale_count * 5
        
        # Calculate dimension score
        dim_total = org_total + cand_total
        dim_max = org_max + cand_max if cand_max > 0 else org_max
        dim_percent = round((dim_total / dim_max) * 100) if dim_max > 0 else 0
        
        # Gap analysis
        org_percent = round((org_total / org_max) * 100) if org_max > 0 else 0
        cand_percent = round((cand_total / cand_max) * 100) if cand_max > 0 else 0
        gap = org_percent - cand_percent if cand_max > 0 else 0
        
        dimension_scores[dim] = {
            "name": ORGANISATION_QUESTIONS[dim]["name"],
            "org_score": org_total,
            "org_max": org_max,
            "org_percent": org_percent,
            "candidate_score": cand_total,
            "candidate_max": cand_max,
            "candidate_percent": cand_percent,
            "total_score": dim_total,
            "total_max": dim_max,
            "percent": dim_percent,
            "gap": gap
        }
        
        total_org_score += org_total
        total_candidate_score += cand_total
        total_org_max += org_max
        total_candidate_max += cand_max
    
    # Overall score
    overall_total = total_org_score + total_candidate_score
    overall_max = total_org_max + total_candidate_max if total_candidate_max > 0 else total_org_max
    overall_percent = round((overall_total / overall_max) * 100) if overall_max > 0 else 0
    
    band = get_score_band(overall_percent)
    
    return {
        "overall_score": overall_percent,
        "overall_total": overall_total,
        "overall_max": overall_max,
        "band_label": band["label"],
        "band_description": band["description"],
        "dimensions": dimension_scores,
        "org_total": total_org_score,
        "org_max": total_org_max,
        "candidate_total": total_candidate_score,
        "candidate_max": total_candidate_max
    }


# ============ DATABASE CONNECTION ============
@st.cache_resource
def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = get_supabase()

# ============ PAGE CONFIG ============
st.set_page_config(
    page_title="ACH Impact Intelligence",
    page_icon="A",
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
    .score-card { background: #f8fafc; border-radius: 8px; padding: 20px; margin: 10px 0; }
    .score-large { font-size: 3rem; font-weight: 700; color: #0f1c3f; }
    .score-label { font-size: 0.9rem; color: #64748b; }
    .gap-positive { color: #dc2626; }
    .gap-negative { color: #16a34a; }
</style>
""", unsafe_allow_html=True)

# ============ SESSION STATE ============
if 'user_type' not in st.session_state:
    st.session_state.user_type = "ach_staff"
if 'user_id' not in st.session_state:
    st.session_state.user_id = 1
if 'user_name' not in st.session_state:
    st.session_state.user_name = "ACH Administrator"
if 'partner_id' not in st.session_state:
    st.session_state.partner_id = None

# ============ COUNTRY FLAGS ============
COUNTRY_FLAGS = {
    "Afghanistan": "AF", "Syria": "SY", "Sudan": "SD", "South Sudan": "SS",
    "Ukraine": "UA", "Eritrea": "ER", "Iran": "IR", "Iraq": "IQ",
    "Somalia": "SO", "Yemen": "YE", "Ethiopia": "ET", "Congo": "CD",
    "Myanmar": "MM", "Pakistan": "PK", "Bangladesh": "BD", "Nigeria": "NG",
}

def get_country_code(country):
    return COUNTRY_FLAGS.get(country, "")

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
    sector = get_partner_sector(partner_id)
    
    metrics = {
        "total_placements": 0,
        "active_employees": 0,
        "retention_rate": 0,
        "retention_savings": 0,
        "retention_savings_data": {},
        "diversity_data": {},
        "inclusion_index": 0,
        "inclusion_data": {},
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
    
    # Get Inclusion Capability Index
    try:
        org_assessment = supabase.table("inclusion_assessment_org").select("*").eq("partner_id", partner_id).order("created_at", desc=True).limit(1).execute()
        candidate_assessments = supabase.table("inclusion_assessment_candidate").select("*").eq("partner_id", partner_id).execute()
        
        if org_assessment.data:
            org_scores = org_assessment.data[0].get("scores", {})
            
            # Average candidate scores if multiple
            candidate_scores = {}
            if candidate_assessments.data:
                for dim in CANDIDATE_QUESTIONS.keys():
                    dim_scores = {"input": [], "conversion": [], "capability": []}
                    for ca in candidate_assessments.data:
                        ca_scores = ca.get("scores", {}).get(dim, {})
                        for layer in ["input", "conversion", "capability"]:
                            if ca_scores.get(layer) and CANDIDATE_QUESTIONS[dim][layer]["type"] == "scale":
                                dim_scores[layer].append(ca_scores[layer])
                    
                    candidate_scores[dim] = {
                        "input": round(sum(dim_scores["input"]) / len(dim_scores["input"])) if dim_scores["input"] else 0,
                        "conversion": round(sum(dim_scores["conversion"]) / len(dim_scores["conversion"])) if dim_scores["conversion"] else 0,
                        "capability": round(sum(dim_scores["capability"]) / len(dim_scores["capability"])) if dim_scores["capability"] else 0
                    }
            
            inclusion_data = calculate_inclusion_index(org_scores, candidate_scores)
            metrics["inclusion_index"] = inclusion_data["overall_score"]
            metrics["inclusion_data"] = inclusion_data
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
    st.markdown('<p class="main-header">Your Impact Dashboard</p>', unsafe_allow_html=True)
    
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
        inclusion = metrics.get("inclusion_data", {})
        if inclusion:
            st.metric("Inclusion Capability Index", f"{inclusion.get('overall_score', 0)}/100", inclusion.get('band_label', ''))
        else:
            st.metric("Inclusion Capability Index", "Not assessed", "Complete assessment")
    
    # RETENTION BREAKDOWN
    st.markdown('<p class="section-header">Retention Savings Breakdown</p>', unsafe_allow_html=True)
    
    savings_data = metrics.get("retention_savings_data", {})
    if savings_data:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Your Retention", f"{savings_data.get('ach_retention_percent', 0)}%")
        col2.metric("Industry Benchmark", f"{savings_data.get('industry_retention_percent', 0)}%")
        col3.metric("Your Uplift", f"+{savings_data.get('retention_uplift_percent', 0)}%")
        col4.metric("Total Savings", f"£{savings_data.get('total_savings', 0):,.0f}")
        st.caption(savings_data.get('methodology', ''))
    
    # INCLUSION INDEX BREAKDOWN
    inclusion_data = metrics.get("inclusion_data", {})
    if inclusion_data and inclusion_data.get("dimensions"):
        st.markdown('<p class="section-header">Inclusion Capability Breakdown</p>', unsafe_allow_html=True)
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown(f'<div class="score-card"><span class="score-large">{inclusion_data.get("overall_score", 0)}</span><br/><span class="score-label">{inclusion_data.get("band_label", "")} - {inclusion_data.get("band_description", "")}</span></div>', unsafe_allow_html=True)
        
        with col2:
            dims = inclusion_data.get("dimensions", {})
            for dim_key, dim_data in dims.items():
                col_a, col_b, col_c = st.columns([2, 1, 1])
                with col_a:
                    st.write(f"**{dim_data['name']}**")
                with col_b:
                    st.write(f"{dim_data['percent']}%")
                with col_c:
                    gap = dim_data.get('gap', 0)
                    if gap > 10:
                        st.write(f"Gap: +{gap}")
                    elif gap < -10:
                        st.write(f"Gap: {gap}")
                    else:
                        st.write("Aligned")
    
    # DIVERSITY BREAKDOWN
    st.markdown('<p class="section-header">Diversity Contribution</p>', unsafe_allow_html=True)
    
    breakdown = metrics.get("diversity_data", {}).get("breakdown", [])
    if breakdown:
        cols = st.columns(min(len(breakdown), 6))
        for i, (country, count) in enumerate(breakdown[:6]):
            cols[i].metric(country, count)
    else:
        st.info("Diversity data will appear once placements are recorded with candidate country of origin.")
    
    # ADDITIONAL METRICS
    st.markdown('<p class="section-header">Additional Metrics</p>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("People Employed", metrics["active_employees"], f"of {metrics['total_placements']}")
    col2.metric("Retention Rate", f"{metrics['retention_rate']}%")
    col3.metric("Living Wage", f"{metrics['living_wage_percent']}%")
    col4.metric("Progressions", metrics["progression_count"])
    
    # PENDING REVIEWS
    pending = get_pending_reviews(partner_id)
    if pending:
        st.markdown('<p class="section-header">Action Required</p>', unsafe_allow_html=True)
        for p in pending:
            st.warning(f"**{p['candidate_name']}** - {p['milestone']} due {p['due_date']}")
    
    # QUOTES
    if metrics["quotes"]:
        st.markdown('<p class="section-header">Success Stories</p>', unsafe_allow_html=True)
        for quote in metrics["quotes"][:3]:
            st.markdown(f'<div class="quote-box">"{quote}"</div>', unsafe_allow_html=True)


# ============ INCLUSION ASSESSMENT - ORGANISATION ============
def partner_inclusion_assessment():
    st.markdown('<p class="main-header">Inclusion Capability Assessment</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Rate your organisation across six dimensions of inclusive employment</p>', unsafe_allow_html=True)
    
    partner_id = st.session_state.get("user_id", 1)
    
    # Check for existing assessment
    try:
        existing = supabase.table("inclusion_assessment_org").select("*").eq("partner_id", partner_id).order("created_at", desc=True).limit(1).execute()
        if existing.data:
            last_date = existing.data[0].get("created_at", "")[:10]
            st.info(f"Last assessment completed: {last_date}. You can submit a new assessment below.")
    except:
        pass
    
    with st.form("org_inclusion_assessment"):
        scores = {}
        
        for dim_key, dim_data in ORGANISATION_QUESTIONS.items():
            st.markdown(f"### {dim_data['name']}")
            
            scores[dim_key] = {}
            
            st.markdown("**Input (Policies and Structures)**")
            scores[dim_key]["input"] = st.slider(
                dim_data["input"],
                min_value=1, max_value=5, value=3,
                help="1 = Not at all, 5 = To a great extent",
                key=f"{dim_key}_input"
            )
            
            st.markdown("**Conversion (Implementation in Practice)**")
            scores[dim_key]["conversion"] = st.slider(
                dim_data["conversion"],
                min_value=1, max_value=5, value=3,
                help="1 = Not at all, 5 = To a great extent",
                key=f"{dim_key}_conversion"
            )
            
            st.markdown("**Capability (Employee Experience)**")
            scores[dim_key]["capability"] = st.slider(
                dim_data["capability"],
                min_value=1, max_value=5, value=3,
                help="1 = Not at all, 5 = To a great extent",
                key=f"{dim_key}_capability"
            )
            
            st.divider()
        
        submitted = st.form_submit_button("Submit Assessment", use_container_width=True)
        
        if submitted:
            try:
                data = {
                    "partner_id": partner_id,
                    "scores": scores,
                    "created_at": datetime.now().isoformat()
                }
                supabase.table("inclusion_assessment_org").insert(data).execute()
                st.success("Assessment submitted successfully")
                st.rerun()
            except Exception as e:
                st.error(f"Error saving assessment: {e}")


# ============ ACH DASHBOARD ============
def ach_dashboard():
    st.markdown('<p class="main-header">Impact Intelligence Dashboard</p>', unsafe_allow_html=True)
    
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
        
        # Partner list
        st.markdown('<p class="section-header">Partner Organisations</p>', unsafe_allow_html=True)
        
        if partners.data:
            for p in partners.data:
                partner_placements = [pl for pl in placements.data if pl.get("partner_id") == p["id"]] if placements.data else []
                active = len([pl for pl in partner_placements if pl.get("status") == "Active"])
                total = len(partner_placements)
                retention = round((active / total) * 100) if total > 0 else 0
                
                with st.expander(f"{p['name']} - {p.get('sector', 'N/A')} - {total} placements"):
                    col1, col2, col3 = st.columns(3)
                    col1.write(f"**Placements:** {total}")
                    col2.write(f"**Active:** {active}")
                    col3.write(f"**Retention:** {retention}%")
    except Exception as e:
        st.error(f"Error: {e}")


# ============ ACH CANDIDATE SURVEY ============
def ach_candidate_inclusion_survey():
    st.markdown('<p class="main-header">Candidate Inclusion Survey</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Record candidate responses to inclusion questions</p>', unsafe_allow_html=True)
    
    try:
        placements = supabase.table("placements").select("*").eq("status", "Active").execute()
        
        if not placements.data:
            st.info("No active placements to survey.")
            return
        
        placement_options = {f"{p['candidate_name']} ({p.get('partner_name', 'Unknown')})": p for p in placements.data}
        selected = st.selectbox("Select Employee", [""] + list(placement_options.keys()))
        
        if selected:
            placement = placement_options[selected]
            partner_id = placement.get("partner_id")
            
            with st.form("candidate_inclusion_survey"):
                scores = {}
                narratives = {}
                
                for dim_key, dim_data in CANDIDATE_QUESTIONS.items():
                    st.markdown(f"### {dim_data['name']}")
                    
                    scores[dim_key] = {}
                    narratives[dim_key] = {}
                    
                    for layer in ["input", "conversion", "capability"]:
                        layer_data = dim_data[layer]
                        layer_label = {"input": "Input", "conversion": "Conversion", "capability": "Capability"}[layer]
                        
                        st.markdown(f"**{layer_label}**")
                        
                        if layer_data["type"] == "scale":
                            scores[dim_key][layer] = st.slider(
                                layer_data["question"],
                                min_value=1, max_value=5, value=3,
                                help="1 = Strongly Disagree, 5 = Strongly Agree",
                                key=f"cand_{dim_key}_{layer}"
                            )
                        else:
                            narratives[dim_key][layer] = st.text_area(
                                layer_data["question"],
                                key=f"cand_{dim_key}_{layer}",
                                height=100
                            )
                    
                    st.divider()
                
                submitted = st.form_submit_button("Submit Survey", use_container_width=True)
                
                if submitted:
                    try:
                        data = {
                            "partner_id": partner_id,
                            "placement_id": placement["id"],
                            "candidate_name": placement["candidate_name"],
                            "scores": scores,
                            "narratives": narratives,
                            "created_at": datetime.now().isoformat()
                        }
                        supabase.table("inclusion_assessment_candidate").insert(data).execute()
                        st.success("Survey submitted successfully")
                    except Exception as e:
                        st.error(f"Error: {e}")
    except Exception as e:
        st.error(f"Error: {e}")


# ============ OTHER PAGES ============
def ach_manage_partners():
    st.markdown('<p class="main-header">Manage Partners</p>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["View Partners", "Add Partner"])
    
    with tab1:
        try:
            partners = supabase.table("impact_partners").select("*").execute()
            if partners.data:
                for p in partners.data:
                    with st.expander(f"{p['name']} - {p.get('sector', 'N/A')}"):
                        st.write(f"**Contact:** {p.get('contact_name', 'N/A')}")
                        st.write(f"**Email:** {p.get('contact_email', 'N/A')}")
                        st.write(f"**Employees:** {p.get('employee_count', 'N/A')}")
        except:
            st.info("No partners found.")
    
    with tab2:
        with st.form("add_partner"):
            name = st.text_input("Organisation Name")
            sector = st.selectbox("Sector", ["", "Healthcare", "Social Care", "Hospitality", "Retail", "Manufacturing", "Logistics", "Public Sector", "Education", "Facilities", "Other"])
            employee_count = st.number_input("Number of Employees", min_value=1, value=50)
            contact_name = st.text_input("Contact Name")
            contact_email = st.text_input("Contact Email")
            
            submitted = st.form_submit_button("Add Partner", use_container_width=True)
            
            if submitted and name and sector:
                try:
                    data = {
                        "name": name,
                        "sector": sector,
                        "employee_count": employee_count,
                        "contact_name": contact_name,
                        "contact_email": contact_email,
                        "created_at": datetime.now().isoformat()
                    }
                    supabase.table("impact_partners").insert(data).execute()
                    st.success(f"{name} added successfully")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")


def ach_manage_candidates():
    st.markdown('<p class="main-header">Manage Candidates</p>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["View Candidates", "Add Candidate"])
    
    with tab1:
        try:
            candidates = supabase.table("candidates").select("*").execute()
            if candidates.data:
                df = pd.DataFrame(candidates.data)
                display_cols = [c for c in ["name", "cohort", "country_of_origin", "status"] if c in df.columns]
                st.dataframe(df[display_cols], use_container_width=True)
        except:
            st.info("No candidates found.")
    
    with tab2:
        with st.form("add_candidate"):
            name = st.text_input("Full Name")
            cohort = st.text_input("Cohort/Programme")
            country_of_origin = st.selectbox("Country of Origin", 
                ["", "Afghanistan", "Syria", "Sudan", "South Sudan", "Ukraine", "Eritrea", 
                 "Iran", "Iraq", "Somalia", "Yemen", "Ethiopia", "Congo", "Myanmar", 
                 "Pakistan", "Bangladesh", "Nigeria", "Other"])
            
            submitted = st.form_submit_button("Add Candidate", use_container_width=True)
            
            if submitted and name:
                try:
                    data = {
                        "name": name,
                        "cohort": cohort,
                        "country_of_origin": country_of_origin,
                        "status": "Available",
                        "created_at": datetime.now().isoformat()
                    }
                    supabase.table("candidates").insert(data).execute()
                    st.success(f"{name} added successfully")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")


def ach_candidate_support():
    st.markdown('<p class="main-header">Candidate Support</p>', unsafe_allow_html=True)
    st.info("Candidate milestone check-in interface")


def partner_baseline():
    st.markdown('<p class="main-header">Baseline Data</p>', unsafe_allow_html=True)
    
    partner_id = st.session_state.get("user_id", 1)
    
    try:
        existing = supabase.table("partner_baseline").select("*").eq("partner_id", partner_id).execute()
        if existing.data:
            st.write(f"**{len(existing.data)} role(s) configured**")
            for role in existing.data:
                st.write(f"- {role['role_title']} (£{role.get('salary', 'N/A'):,})")
    except:
        pass
    
    st.markdown('<p class="section-header">Add Role</p>', unsafe_allow_html=True)
    
    with st.form("add_baseline_role"):
        role_title = st.text_input("Role Title")
        salary = st.number_input("Annual Salary (£)", min_value=0, value=22500)
        difficulty = st.selectbox("Difficulty to Fill", ["Easy", "Moderate", "Hard", "Very Hard"])
        
        submitted = st.form_submit_button("Add Role", use_container_width=True)
        
        if submitted and role_title:
            try:
                data = {
                    "partner_id": partner_id,
                    "role_title": role_title,
                    "salary": salary,
                    "difficulty": difficulty,
                    "created_at": datetime.now().isoformat()
                }
                supabase.table("partner_baseline").insert(data).execute()
                st.success(f"{role_title} added")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")


def partner_interview_feedback():
    st.markdown('<p class="main-header">Interview Feedback</p>', unsafe_allow_html=True)
    
    partner_id = st.session_state.get("user_id", 1)
    
    try:
        candidates = supabase.table("candidates").select("*").eq("status", "Available").execute()
        
        if not candidates.data:
            st.info("No candidates available.")
            return
        
        with st.form("interview_feedback"):
            candidate = st.selectbox("Candidate", [""] + [c["name"] for c in candidates.data])
            role = st.text_input("Role Interviewed For")
            interview_date = st.date_input("Interview Date")
            hired = st.radio("Offered Position?", ["Yes", "No"], horizontal=True)
            
            if hired == "Yes":
                standout = st.text_area("What stood out about this candidate?")
                start_date = st.date_input("Start Date")
                salary = st.number_input("Confirmed Salary (£)", min_value=0, value=22500)
            else:
                reason = st.selectbox("Reason", ["Skills gap", "Experience gap", "English proficiency", "Not right fit", "Other"])
            
            submitted = st.form_submit_button("Submit", use_container_width=True)
            
            if submitted and candidate and role:
                try:
                    cand_data = next(c for c in candidates.data if c["name"] == candidate)
                    
                    feedback = {
                        "partner_id": partner_id,
                        "candidate_id": cand_data["id"],
                        "candidate_name": candidate,
                        "role": role,
                        "interview_date": interview_date.isoformat(),
                        "hired": hired == "Yes",
                        "standout_reason": standout if hired == "Yes" else None,
                        "rejection_reason": reason if hired == "No" else None,
                        "created_at": datetime.now().isoformat()
                    }
                    supabase.table("interview_feedback").insert(feedback).execute()
                    
                    if hired == "Yes":
                        partner = supabase.table("impact_partners").select("name").eq("id", partner_id).execute()
                        partner_name = partner.data[0]["name"] if partner.data else "Unknown"
                        
                        placement = {
                            "partner_id": partner_id,
                            "partner_name": partner_name,
                            "candidate_id": cand_data["id"],
                            "candidate_name": candidate,
                            "role": role,
                            "start_date": start_date.isoformat(),
                            "salary": salary,
                            "hourly_rate": round(salary / 52 / 40, 2),
                            "status": "Active",
                            "created_at": datetime.now().isoformat()
                        }
                        supabase.table("placements").insert(placement).execute()
                        supabase.table("candidates").update({"status": "Placed"}).eq("id", cand_data["id"]).execute()
                        
                        st.success(f"{candidate} placed successfully")
                    else:
                        st.success("Feedback recorded")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
    except Exception as e:
        st.error(f"Error: {e}")


def partner_milestone_review():
    st.markdown('<p class="main-header">Milestone Reviews</p>', unsafe_allow_html=True)
    
    partner_id = st.session_state.get("user_id", 1)
    pending = get_pending_reviews(partner_id)
    
    if not pending:
        st.success("All reviews are up to date")
        return
    
    st.warning(f"{len(pending)} review(s) pending")
    
    for review in pending:
        with st.expander(f"{review['candidate_name']} - {review['milestone']} (Due: {review['due_date']})"):
            with st.form(f"review_{review['placement_id']}_{review['milestone_month']}"):
                still_employed = st.radio("Still employed?", ["Yes", "No"], horizontal=True)
                
                if still_employed == "Yes":
                    performance = st.selectbox("Performance", ["Excellent", "Good", "Satisfactory", "Needs Improvement"])
                    received_training = st.radio("Received training?", ["Yes", "No"], horizontal=True)
                    progression = st.radio("Any progression?", ["Yes", "No"], horizontal=True)
                    contribution_quote = st.text_area("Describe their contribution")
                else:
                    leaving_reason = st.selectbox("Reason", ["Resigned", "Dismissed", "Redundancy", "Contract ended", "Other"])
                
                submitted = st.form_submit_button("Submit", use_container_width=True)
                
                if submitted:
                    try:
                        data = {
                            "placement_id": review["placement_id"],
                            "partner_id": partner_id,
                            "milestone_month": review["milestone_month"],
                            "still_employed": still_employed == "Yes",
                            "performance": performance if still_employed == "Yes" else None,
                            "received_training": received_training == "Yes" if still_employed == "Yes" else None,
                            "progression": progression == "Yes" if still_employed == "Yes" else None,
                            "contribution_quote": contribution_quote if still_employed == "Yes" else None,
                            "leaving_reason": leaving_reason if still_employed == "No" else None,
                            "created_at": datetime.now().isoformat()
                        }
                        supabase.table("milestone_reviews_partner").insert(data).execute()
                        
                        if still_employed == "No":
                            supabase.table("placements").update({"status": "Left"}).eq("id", review["placement_id"]).execute()
                        
                        st.success("Review submitted")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")


def partner_reports():
    st.markdown('<p class="main-header">Impact Reports</p>', unsafe_allow_html=True)
    
    partner_id = st.session_state.get("user_id", 1)
    metrics = calculate_impact_metrics(partner_id)
    
    if metrics["total_placements"] == 0:
        st.warning("No placements yet. Reports will be available once you have placed candidates.")
        return
    
    st.markdown(f"### Impact Report: {st.session_state.user_name}")
    st.markdown(f"**Generated:** {datetime.now().strftime('%d %B %Y')}")
    st.divider()
    
    st.markdown("### Executive Summary")
    st.write(f"Through your partnership with ACH, your organisation has created {metrics['total_placements']} employment opportunities for refugees and migrants, achieving {metrics['retention_rate']}% retention and saving an estimated £{metrics['retention_savings']:,.0f} in reduced turnover costs.")
    
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Workforce Impact")
        st.write(f"**Total Placements:** {metrics['total_placements']}")
        st.write(f"**Currently Employed:** {metrics['active_employees']}")
        st.write(f"**Retention Rate:** {metrics['retention_rate']}%")
        st.write(f"**Living Wage Roles:** {metrics['living_wage_percent']}%")
    
    with col2:
        st.markdown("### Business Value")
        st.write(f"**Retention Savings:** £{metrics['retention_savings']:,.0f}")
        st.write(f"**Employees Trained:** {metrics['training_count']}")
        st.write(f"**Career Progressions:** {metrics['progression_count']}")
    
    if metrics.get("inclusion_data"):
        st.divider()
        st.markdown("### Inclusion Capability Index")
        inclusion = metrics["inclusion_data"]
        st.write(f"**Overall Score:** {inclusion.get('overall_score', 0)}/100 ({inclusion.get('band_label', '')})")
    
    if metrics["quotes"]:
        st.divider()
        st.markdown("### Success Stories")
        for quote in metrics["quotes"][:3]:
            st.markdown(f'> "{quote}"')


# ============ NAVIGATION ============
def main():
    with st.sidebar:
        st.markdown(f"### {st.session_state.user_name}")
        st.divider()
        
        # View switcher
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
            except:
                st.warning("No partners found")
                st.session_state.user_type = "ach_staff"
        else:
            st.session_state.user_type = "ach_staff"
            st.session_state.user_name = "ACH Administrator"
        
        st.divider()
        
        if st.session_state.user_type == "ach_staff":
            page = st.radio("Navigation", ["Dashboard", "Manage Partners", "Manage Candidates", "Candidate Inclusion Survey", "Candidate Support"], label_visibility="collapsed")
        else:
            page = st.radio("Navigation", ["Dashboard", "Inclusion Assessment", "Baseline Data", "Interview Feedback", "Milestone Reviews", "Reports"], label_visibility="collapsed")
    
    if st.session_state.user_type == "ach_staff":
        pages = {
            "Dashboard": ach_dashboard,
            "Manage Partners": ach_manage_partners,
            "Manage Candidates": ach_manage_candidates,
            "Candidate Inclusion Survey": ach_candidate_inclusion_survey,
            "Candidate Support": ach_candidate_support
        }
    else:
        pages = {
            "Dashboard": partner_dashboard,
            "Inclusion Assessment": partner_inclusion_assessment,
            "Baseline Data": partner_baseline,
            "Interview Feedback": partner_interview_feedback,
            "Milestone Reviews": partner_milestone_review,
            "Reports": partner_reports
        }
    
    pages[page]()


if __name__ == "__main__":
    main()
