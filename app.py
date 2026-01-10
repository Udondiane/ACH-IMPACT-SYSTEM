import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from supabase import create_client
import json

SUPABASE_URL = "https://gmjqidqjpzxcpgycawxf.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdtanFpZHFqcHp4Y3BneWNhd3hmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njc3MjYyMDEsImV4cCI6MjA4MzMwMjIwMX0.6jtYlz6yoBQCrh04P0g30JigHyanGYnv7xBz24B5Bm4"
LIVING_WAGE_UK = 12.00

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

INCLUSION_DIMENSIONS = {
    "economic_security": {
        "name": "Economic Security and Stability",
        "employer_questions": {
            "input": "To what extent does the organisation provide stable contracts, transparent pay, and predictable working hours for refugee employees?",
            "conversion": "To what extent are pay and shift arrangements implemented transparently and communicated effectively in daily practice?",
            "capability": "To what extent do refugee employees feel economically secure and able to rely on their work for a stable livelihood?"
        },
        "employee_questions": {
            "input": "Can you describe how predictable your work and income feel here?",
            "conversion": "When schedules or pay change, how do you usually find out?",
            "capability": "Do you feel your income and working hours are reliable enough to plan your life ahead?"
        }
    },
    "skill_growth": {
        "name": "Skill Use and Growth",
        "employer_questions": {
            "input": "To what extent does the organisation provide access to relevant training and skill development opportunities?",
            "conversion": "To what extent can refugee employees realistically participate in these learning opportunities?",
            "capability": "To what extent do refugee employees feel they can use their skills and grow professionally in their roles?"
        },
        "employee_questions": {
            "input": "What kinds of learning or training opportunities do you know about here?",
            "conversion": "Can you share a time you wanted to join training or learn new skills - what helped or stopped you?",
            "capability": "Can you describe a moment when you were able to use your abilities fully at work?"
        }
    },
    "dignity_respect": {
        "name": "Workplace Dignity and Respect",
        "employer_questions": {
            "input": "To what extent does the organisation have formal policies ensuring equal treatment and preventing discrimination?",
            "conversion": "To what extent do managers and coworkers behave respectfully and apply these policies consistently?",
            "capability": "To what extent do refugee employees experience dignity and equal respect in daily work life?"
        },
        "employee_questions": {
            "input": "Have you been told about policies that protect fairness or respect at work?",
            "conversion": "How are you usually treated by colleagues or supervisors?",
            "capability": "Do you feel respected and valued as a person here?"
        }
    },
    "voice_agency": {
        "name": "Voice and Agency",
        "employer_questions": {
            "input": "To what extent does the organisation provide formal channels for refugee employees to express feedback or concerns?",
            "conversion": "To what extent are refugee employees voices heard and acted upon by management?",
            "capability": "To what extent do refugee employees feel confident and empowered to influence decisions affecting their work?"
        },
        "employee_questions": {
            "input": "Are there ways for you to share your opinions or issues with management?",
            "conversion": "Can you tell me about a time when you spoke up about something at work?",
            "capability": "Do you feel you can make choices or influence how your work is done?"
        }
    },
    "belonging_inclusion": {
        "name": "Social Belonging and Inclusion",
        "employer_questions": {
            "input": "To what extent does the organisation provide initiatives to support social connection and inclusion?",
            "conversion": "To what extent do managers and teams actively encourage inclusive interactions in daily work?",
            "capability": "To what extent do refugee employees feel part of the team and socially connected within the organisation?"
        },
        "employee_questions": {
            "input": "When you first joined, were there any activities that helped you meet people or feel included?",
            "conversion": "Can you describe how your team works together day to day?",
            "capability": "What makes you feel you belong here - or sometimes, what makes you feel apart?"
        }
    },
    "wellbeing_confidence": {
        "name": "Wellbeing and Confidence to Plan Ahead",
        "employer_questions": {
            "input": "To what extent does the organisation provide wellbeing and health support?",
            "conversion": "To what extent can refugee employees actually use these wellbeing supports without stigma or barriers?",
            "capability": "To what extent do refugee employees feel safe, healthy, and able to plan their personal and work futures?"
        },
        "employee_questions": {
            "input": "What kinds of wellbeing or health support are available to you here?",
            "conversion": "If you need time off or help for health reasons, how easy is it to ask for and receive support?",
            "capability": "Do you feel safe and confident about your future here?"
        }
    }
}

SCORE_BANDS = {
    "leading": {"min": 81, "max": 100, "label": "Leading", "description": "Strong inclusion capability across all areas"},
    "established": {"min": 61, "max": 80, "label": "Established", "description": "Good practice, some areas to strengthen"},
    "developing": {"min": 41, "max": 60, "label": "Developing", "description": "Policies exist but gaps in practice"},
    "foundational": {"min": 0, "max": 40, "label": "Foundational", "description": "Basic structures missing"}
}

def get_replacement_multiplier(salary):
    if salary < 24000: return 0.15
    elif salary < 28000: return 0.18
    elif salary < 35000: return 0.22
    elif salary < 45000: return 0.25
    else: return 0.30

def calculate_retention_savings(placements, sector, ach_retention_rate):
    benchmark_data = INDUSTRY_BENCHMARKS.get(sector, INDUSTRY_BENCHMARKS["Other"])
    industry_retention = benchmark_data["retention_12m"]
    retention_uplift = max(0, ach_retention_rate - industry_retention)
    total_savings = 0
    for p in placements:
        salary = p.get("salary") or 0
        if salary > 0:
            multiplier = get_replacement_multiplier(salary)
            total_savings += retention_uplift * salary * multiplier
    return {
        "total_savings": round(total_savings, 2),
        "ach_retention_percent": round(ach_retention_rate * 100, 1),
        "industry_retention_percent": round(industry_retention * 100, 1),
        "retention_uplift_percent": round(retention_uplift * 100, 1),
        "sector": sector,
        "benchmark_source": benchmark_data["source"],
        "methodology": f"Based on {benchmark_data['source']} ({round(industry_retention * 100)}% industry retention) and CIPD replacement cost estimates."
    }

def calculate_diversity_contribution(placements, candidates_data):
    country_counts = {}
    for p in placements:
        cid = p.get("candidate_id")
        if cid and cid in candidates_data:
            country = candidates_data[cid].get("country_of_origin", "Unknown")
            country_counts[country] = country_counts.get(country, 0) + 1
    return {
        "total_employees": sum(country_counts.values()),
        "countries_represented": len(country_counts),
        "breakdown": sorted(country_counts.items(), key=lambda x: x[1], reverse=True)
    }

def calculate_inclusion_index(employer_scores, employee_scores):
    results = {"overall_score": 0, "overall_percent": 0, "band": {}, "dimensions": {}, "layer_analysis": {"input": 0, "conversion": 0, "capability": 0}, "gaps": {}, "strengths": [], "improvements": []}
    total_score, max_score = 0, 0
    layer_totals = {"input": [], "conversion": [], "capability": []}
    for dim_key, dim_info in INCLUSION_DIMENSIONS.items():
        emp = employer_scores.get(dim_key, {})
        can = employee_scores.get(dim_key, {})
        employer_total = sum([emp.get("input", 0), emp.get("conversion", 0), emp.get("capability", 0)])
        employee_total = sum([can.get("input", 0), can.get("conversion", 0), can.get("capability", 0)])
        dim_total = employer_total + employee_total
        dim_percent = round((dim_total / 30) * 100) if dim_total else 0
        results["dimensions"][dim_key] = {"name": dim_info["name"], "employer_score": employer_total, "employee_score": employee_total, "total_score": dim_total, "percent": dim_percent, "gap": employer_total - employee_total}
        results["gaps"][dim_key] = {"name": dim_info["name"], "employer": employer_total, "employee": employee_total, "gap": employer_total - employee_total}
        total_score += dim_total
        max_score += 30
        for layer in ["input", "conversion", "capability"]:
            layer_totals[layer].append(emp.get(layer, 0) + can.get(layer, 0))
    results["overall_score"] = total_score
    results["overall_percent"] = round((total_score / max_score) * 100) if max_score else 0
    for bk, bi in SCORE_BANDS.items():
        if bi["min"] <= results["overall_percent"] <= bi["max"]:
            results["band"] = {"key": bk, "label": bi["label"], "description": bi["description"]}
            break
    for layer in ["input", "conversion", "capability"]:
        if layer_totals[layer]:
            results["layer_analysis"][layer] = round((sum(layer_totals[layer]) / len(layer_totals[layer]) / 10) * 100)
    sorted_dims = sorted(results["dimensions"].items(), key=lambda x: x[1]["percent"], reverse=True)
    results["strengths"] = [{"key": k, "name": v["name"], "percent": v["percent"]} for k, v in sorted_dims[:2]]
    results["improvements"] = [{"key": k, "name": v["name"], "percent": v["percent"]} for k, v in sorted_dims[-2:]]
    return results

def get_inclusion_scores(partner_id):
    employer_scores, employee_scores = {}, {}
    try:
        r = supabase.table("inclusion_employer_assessments").select("*").eq("partner_id", partner_id).order("created_at", desc=True).limit(1).execute()
        if r.data:
            s = r.data[0].get("scores", {})
            employer_scores = json.loads(s) if isinstance(s, str) else s
    except: pass
    try:
        placements = supabase.table("placements").select("id").eq("partner_id", partner_id).execute()
        if placements.data:
            dim_scores = {d: {"input": [], "conversion": [], "capability": []} for d in INCLUSION_DIMENSIONS}
            for p in placements.data:
                r = supabase.table("inclusion_employee_assessments").select("*").eq("placement_id", p["id"]).order("created_at", desc=True).limit(1).execute()
                if r.data:
                    s = r.data[0].get("scores", {})
                    s = json.loads(s) if isinstance(s, str) else s
                    for d, layers in s.items():
                        if d in dim_scores:
                            for l, v in layers.items():
                                if l in dim_scores[d]: dim_scores[d][l].append(v)
            for d in dim_scores:
                for l in dim_scores[d]:
                    if dim_scores[d][l]: employee_scores.setdefault(d, {})[l] = round(sum(dim_scores[d][l]) / len(dim_scores[d][l]))
    except: pass
    return employer_scores, employee_scores

@st.cache_resource
def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = get_supabase()

st.set_page_config(page_title="ACH Impact Intelligence", layout="wide", initial_sidebar_state="expanded")

st.markdown("""<style>
.main-header { font-size: 2rem; font-weight: 600; color: #0f1c3f; margin-bottom: 0.5rem; }
.sub-header { font-size: 1rem; color: #64748b; margin-bottom: 2rem; }
.section-header { font-size: 1.3rem; color: #0f1c3f; margin: 2rem 0 1rem 0; padding-bottom: 0.5rem; border-bottom: 2px solid #e2e8f0; }
.quote-box { background: #f8fafc; border-left: 4px solid #0f1c3f; padding: 16px 20px; margin: 16px 0; font-style: italic; color: #475569; }
div[data-testid="stSidebar"] { background: linear-gradient(180deg, #0f1c3f 0%, #1a2d5a 100%); }
div[data-testid="stSidebar"] .stMarkdown { color: white; }
</style>""", unsafe_allow_html=True)

def get_partner_sector(pid):
    try:
        r = supabase.table("impact_partners").select("sector").eq("id", pid).execute()
        if r.data: return r.data[0].get("sector", "Other")
    except: pass
    return "Other"

def calculate_impact_metrics(pid):
    sector = get_partner_sector(pid)
    m = {"total_placements": 0, "active_employees": 0, "retention_rate": 0, "retention_savings": 0, "retention_savings_data": {}, "diversity_data": {}, "inclusion_data": {}, "living_wage_percent": 0, "quotes": [], "progression_count": 0, "training_count": 0, "sector": sector}
    placements = []
    try:
        r = supabase.table("placements").select("*").eq("partner_id", pid).execute()
        if r.data:
            placements = r.data
            m["total_placements"] = len(placements)
            active = [p for p in placements if p.get("status") == "Active"]
            m["active_employees"] = len(active)
            if m["total_placements"] > 0:
                m["retention_rate"] = round((len(active) / m["total_placements"]) * 100)
                sd = calculate_retention_savings(placements, sector, len(active) / m["total_placements"])
                m["retention_savings"] = sd["total_savings"]
                m["retention_savings_data"] = sd
            lw = sum(1 for p in placements if (p.get("hourly_rate") or 0) >= LIVING_WAGE_UK)
            if m["total_placements"] > 0: m["living_wage_percent"] = round((lw / m["total_placements"]) * 100)
    except: pass
    try:
        cr = supabase.table("candidates").select("id, country_of_origin").execute()
        if cr.data: m["diversity_data"] = calculate_diversity_contribution(placements, {c["id"]: c for c in cr.data})
    except: pass
    try:
        es, cs = get_inclusion_scores(pid)
        if es or cs: m["inclusion_data"] = calculate_inclusion_index(es, cs)
    except: pass
    try:
        r = supabase.table("interview_feedback").select("*").eq("partner_id", pid).eq("hired", True).execute()
        if r.data: m["quotes"] = [f.get("standout_reason") for f in r.data if f.get("standout_reason")]
    except: pass
    try:
        r = supabase.table("milestone_reviews_partner").select("*").eq("partner_id", pid).execute()
        if r.data:
            m["quotes"].extend([x.get("contribution_quote") for x in r.data if x.get("contribution_quote")])
            m["progression_count"] = sum(1 for x in r.data if x.get("progression"))
            m["training_count"] = sum(1 for x in r.data if x.get("received_training"))
    except: pass
    return m

def get_pending_reviews(pid):
    pending = []
    try:
        r = supabase.table("placements").select("*").eq("partner_id", pid).eq("status", "Active").execute()
        if r.data:
            for p in r.data:
                sd = datetime.fromisoformat(p["start_date"]) if p.get("start_date") else None
                if sd:
                    months = (datetime.now() - sd).days / 30
                    for m in [3, 6, 12]:
                        if months >= m:
                            rv = supabase.table("milestone_reviews_partner").select("*").eq("placement_id", p["id"]).eq("milestone_month", m).execute()
                            if not rv.data:
                                pending.append({"candidate_name": p.get("candidate_name", "Unknown"), "milestone": f"{m}-month review", "due_date": (sd + timedelta(days=m*30)).strftime("%d %b %Y"), "placement_id": p["id"], "milestone_month": m})
    except: pass
    return pending

def partner_dashboard(pid):
    st.markdown('<p class="main-header">Your Impact Dashboard</p>', unsafe_allow_html=True)
    m = calculate_impact_metrics(pid)
    c1, c2, c3 = st.columns(3)
    c1.metric("Retention Savings", f"GBP {m['retention_savings']:,.0f}", f"vs {m['sector']} avg")
    div = m.get("diversity_data", {})
    c2.metric("Diversity Contribution", f"{div.get('countries_represented', 0)} countries", f"{div.get('total_employees', 0)} employees")
    inc = m.get("inclusion_data", {})
    c3.metric("Inclusion Capability Index", f"{inc.get('overall_percent', 0)}%" if inc else "Not assessed", inc.get("band", {}).get("label", "Complete assessment") if inc else "")
    
    st.markdown('<p class="section-header">Retention Savings Breakdown</p>', unsafe_allow_html=True)
    sd = m.get("retention_savings_data", {})
    if sd:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Your Retention", f"{sd.get('ach_retention_percent', 0)}%")
        c2.metric("Industry Benchmark", f"{sd.get('industry_retention_percent', 0)}%")
        c3.metric("Your Uplift", f"+{sd.get('retention_uplift_percent', 0)}%")
        c4.metric("Total Savings", f"GBP {sd.get('total_savings', 0):,.0f}")
        st.caption(sd.get('methodology', ''))
    
    st.markdown('<p class="section-header">Diversity Contribution</p>', unsafe_allow_html=True)
    bd = m.get("diversity_data", {}).get("breakdown", [])
    if bd:
        cols = st.columns(min(len(bd), 4))
        for i, (country, count) in enumerate(bd[:4]): cols[i].metric(country, count)
    
    if inc and inc.get("overall_percent", 0) > 0:
        st.markdown('<p class="section-header">Inclusion Capability Index</p>', unsafe_allow_html=True)
        c1, c2 = st.columns([1, 2])
        with c1:
            band = inc.get("band", {})
            st.markdown(f'<div style="text-align:center;padding:20px;background:#f8fafc;border-radius:12px;"><div style="font-size:3rem;font-weight:700;color:#0f1c3f;">{inc.get("overall_percent", 0)}%</div><div style="font-weight:600;">{band.get("label", "")}</div><div style="color:#64748b;font-size:0.9rem;">{band.get("description", "")}</div></div>', unsafe_allow_html=True)
        with c2:
            st.write("**Dimension Scores:**")
            for dk, dv in inc.get("dimensions", {}).items():
                st.write(f"{dv.get('name', dk)}: {dv.get('percent', 0)}%")
                st.progress(dv.get("percent", 0) / 100)
    
    st.markdown('<p class="section-header">Additional Metrics</p>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("People Employed", m["active_employees"], f"of {m['total_placements']}")
    c2.metric("Retention Rate", f"{m['retention_rate']}%")
    c3.metric("Living Wage", f"{m['living_wage_percent']}%")
    c4.metric("Progressions", m["progression_count"])
    
    pending = get_pending_reviews(pid)
    if pending:
        st.markdown('<p class="section-header">Action Required</p>', unsafe_allow_html=True)
        for p in pending: st.warning(f"**{p['candidate_name']}** - {p['milestone']} due {p['due_date']}")
    
    if m["quotes"]:
        st.markdown('<p class="section-header">Success Stories</p>', unsafe_allow_html=True)
        for q in m["quotes"][:3]: st.markdown(f'<div class="quote-box">"{q}"</div>', unsafe_allow_html=True)

def partner_inclusion_assessment(pid):
    st.markdown('<p class="main-header">Inclusion Capability Assessment</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Rate your organisation on each dimension (1 = Strongly Disagree, 5 = Strongly Agree)</p>', unsafe_allow_html=True)
    try:
        r = supabase.table("inclusion_employer_assessments").select("*").eq("partner_id", pid).order("created_at", desc=True).limit(1).execute()
        if r.data: st.info(f"Last assessment: {r.data[0].get('created_at', '')[:10]}. Submit new assessment below.")
    except: pass
    with st.form("emp_assess"):
        scores = {}
        for dk, di in INCLUSION_DIMENSIONS.items():
            st.markdown(f'<p class="section-header">{di["name"]}</p>', unsafe_allow_html=True)
            scores[dk] = {}
            for layer in ["input", "conversion", "capability"]:
                lbl = {"input": "Policy/Structure", "conversion": "Implementation", "capability": "Employee Experience"}[layer]
                scores[dk][layer] = st.slider(f"[{lbl}] {di['employer_questions'][layer]}", 1, 5, 3, key=f"e_{dk}_{layer}")
            st.divider()
        if st.form_submit_button("Submit Assessment", use_container_width=True):
            try:
                supabase.table("inclusion_employer_assessments").insert({"partner_id": pid, "scores": json.dumps(scores), "created_at": datetime.now().isoformat()}).execute()
                st.success("Assessment submitted!")
                st.rerun()
            except Exception as e: st.error(f"Error: {e}")

def partner_incluscope_report(pid):
    st.markdown('<p class="main-header">IncluScope Report</p>', unsafe_allow_html=True)
    es, cs = get_inclusion_scores(pid)
    if not es:
        st.warning("No employer assessment found. Complete Inclusion Assessment first.")
        return
    r = calculate_inclusion_index(es, cs)
    st.markdown('<p class="section-header">Executive Summary</p>', unsafe_allow_html=True)
    c1, c2 = st.columns([1, 2])
    with c1:
        band = r.get("band", {})
        st.markdown(f'<div style="text-align:center;padding:30px;background:#f8fafc;border-radius:12px;"><div style="font-size:4rem;font-weight:700;color:#0f1c3f;">{r.get("overall_percent", 0)}</div><div style="font-size:1.2rem;color:#64748b;">out of 100</div><div style="margin-top:16px;font-weight:600;">{band.get("label", "")}</div><div style="color:#64748b;">{band.get("description", "")}</div></div>', unsafe_allow_html=True)
    with c2:
        st.write("**Top Strengths:**")
        for s in r.get("strengths", []): st.write(f"- {s.get('name', '')} ({s.get('percent', 0)}%)")
        st.write("**Areas for Improvement:**")
        for i in r.get("improvements", []): st.write(f"- {i.get('name', '')} ({i.get('percent', 0)}%)")
    
    st.markdown('<p class="section-header">Dimension Scores</p>', unsafe_allow_html=True)
    data = [{"Dimension": v["name"], "Score": f"{v['percent']}%", "Employer": f"{v['employer_score']}/15", "Employee": f"{v['employee_score']}/15"} for k, v in r.get("dimensions", {}).items()]
    if data: st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)
    
    st.markdown('<p class="section-header">Gap Analysis</p>', unsafe_allow_html=True)
    for dk, gi in r.get("gaps", {}).items():
        gap = gi.get("gap", 0)
        c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
        c1.write(gi.get("name", dk))
        c2.write(f"{gi.get('employer', 0)}/15")
        c3.write(f"{gi.get('employee', 0)}/15")
        c4.write(f"{'+' if gap > 0 else ''}{gap}")
    
    st.markdown('<p class="section-header">Layer Analysis</p>', unsafe_allow_html=True)
    la = r.get("layer_analysis", {})
    c1, c2, c3 = st.columns(3)
    c1.metric("Input (Policies exist)", f"{la.get('input', 0)}%")
    c2.metric("Conversion (Implemented)", f"{la.get('conversion', 0)}%")
    c3.metric("Capability (Experienced)", f"{la.get('capability', 0)}%")

def ach_dashboard():
    st.markdown('<p class="main-header">Impact Intelligence Dashboard</p>', unsafe_allow_html=True)
    try:
        partners = supabase.table("impact_partners").select("*").execute()
        candidates = supabase.table("candidates").select("*").execute()
        placements = supabase.table("placements").select("*").execute()
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Partners", len(partners.data) if partners.data else 0)
        c2.metric("Candidates", len(candidates.data) if candidates.data else 0)
        c3.metric("Placements", len(placements.data) if placements.data else 0)
        if placements.data:
            active = len([p for p in placements.data if p.get("status") == "Active"])
            c4.metric("Retention", f"{round((active / len(placements.data)) * 100)}%")
        st.markdown('<p class="section-header">Partner Inclusion Scores</p>', unsafe_allow_html=True)
        if partners.data:
            for p in partners.data:
                es, cs = get_inclusion_scores(p["id"])
                if es:
                    r = calculate_inclusion_index(es, cs)
                    st.write(f"**{p['name']}** - Inclusion Score: {r.get('overall_percent', 0)}% ({r.get('band', {}).get('label', '')})")
                else:
                    st.write(f"**{p['name']}** - Not assessed")
    except Exception as e: st.error(f"Error: {e}")

def ach_employee_inclusion_assessment():
    st.markdown('<p class="main-header">Employee Inclusion Assessment</p>', unsafe_allow_html=True)
    try:
        r = supabase.table("placements").select("*").eq("status", "Active").execute()
        if not r.data:
            st.info("No active placements.")
            return
        opts = {f"{p['candidate_name']} ({p.get('partner_name', '')})": p for p in r.data}
        sel = st.selectbox("Select Employee", [""] + list(opts.keys()))
        if not sel: return
        placement = opts[sel]
        with st.form("can_assess"):
            scores = {}
            for dk, di in INCLUSION_DIMENSIONS.items():
                st.markdown(f"**{di['name']}**")
                scores[dk] = {}
                for layer in ["input", "conversion", "capability"]:
                    scores[dk][layer] = st.slider(di['employee_questions'][layer], 1, 5, 3, key=f"c_{dk}_{layer}")
                st.divider()
            if st.form_submit_button("Submit", use_container_width=True):
                try:
                    supabase.table("inclusion_employee_assessments").insert({"placement_id": placement["id"], "partner_id": placement["partner_id"], "candidate_name": placement["candidate_name"], "scores": json.dumps(scores), "created_at": datetime.now().isoformat()}).execute()
                    st.success("Submitted!")
                    st.rerun()
                except Exception as e: st.error(f"Error: {e}")
    except Exception as e: st.error(f"Error: {e}")

def ach_manage_partners():
    st.markdown('<p class="main-header">Manage Partners</p>', unsafe_allow_html=True)
    t1, t2 = st.tabs(["View", "Add"])
    with t1:
        try:
            r = supabase.table("impact_partners").select("*").execute()
            if r.data:
                for p in r.data:
                    with st.expander(f"**{p['name']}** - {p.get('sector', '')}"):
                        st.write(f"Contact: {p.get('contact_name', '')} | Email: {p.get('contact_email', '')}")
            else: st.info("No partners.")
        except: st.info("No partners.")
    with t2:
        with st.form("add_p"):
            name = st.text_input("Name")
            sector = st.selectbox("Sector", ["", "Healthcare", "Social Care", "Hospitality", "Retail", "Manufacturing", "Logistics", "Public Sector", "Education", "Facilities", "Food Service", "Other"])
            contact = st.text_input("Contact Name")
            email = st.text_input("Email")
            if st.form_submit_button("Add", use_container_width=True) and name and sector:
                try:
                    supabase.table("impact_partners").insert({"name": name, "sector": sector, "contact_name": contact, "contact_email": email, "created_at": datetime.now().isoformat()}).execute()
                    st.success("Added!")
                    st.rerun()
                except Exception as e: st.error(f"Error: {e}")

def ach_manage_candidates():
    st.markdown('<p class="main-header">Manage Candidates</p>', unsafe_allow_html=True)
    t1, t2 = st.tabs(["View", "Add"])
    with t1:
        try:
            r = supabase.table("candidates").select("*").execute()
            if r.data:
                df = pd.DataFrame(r.data)
                cols = [c for c in ["name", "cohort", "country_of_origin", "status"] if c in df.columns]
                st.dataframe(df[cols], use_container_width=True, hide_index=True)
            else: st.info("No candidates.")
        except: st.info("No candidates.")
    with t2:
        with st.form("add_c"):
            name = st.text_input("Name")
            cohort = st.text_input("Cohort")
            country = st.selectbox("Country", ["", "Afghanistan", "Syria", "Sudan", "Ukraine", "Eritrea", "Iran", "Iraq", "Somalia", "Other"])
            if st.form_submit_button("Add", use_container_width=True) and name and country:
                try:
                    supabase.table("candidates").insert({"name": name, "cohort": cohort, "country_of_origin": country, "status": "Available", "created_at": datetime.now().isoformat()}).execute()
                    st.success("Added!")
                    st.rerun()
                except Exception as e: st.error(f"Error: {e}")

def main():
    with st.sidebar:
        st.markdown("### ACH Impact Intelligence")
        st.divider()
        
        view = st.radio("View As", ["ACH Staff", "Partner"], label_visibility="collapsed")
        
        if view == "Partner":
            try:
                partners = supabase.table("impact_partners").select("id, name").execute()
                if partners.data:
                    partner_names = {p["name"]: p["id"] for p in partners.data}
                    selected = st.selectbox("Select Partner", list(partner_names.keys()))
                    pid = partner_names[selected]
                else:
                    st.warning("No partners found")
                    pid = None
            except:
                pid = None
            
            if pid:
                page = st.radio("Nav", ["Dashboard", "Inclusion Assessment", "IncluScope Report"], label_visibility="collapsed")
        else:
            page = st.radio("Nav", ["Dashboard", "Manage Partners", "Manage Candidates", "Employee Inclusion Assessment"], label_visibility="collapsed")
    
    if view == "ACH Staff":
        if page == "Dashboard": ach_dashboard()
        elif page == "Manage Partners": ach_manage_partners()
        elif page == "Manage Candidates": ach_manage_candidates()
        elif page == "Employee Inclusion Assessment": ach_employee_inclusion_assessment()
    else:
        if pid:
            if page == "Dashboard": partner_dashboard(pid)
            elif page == "Inclusion Assessment": partner_inclusion_assessment(pid)
            elif page == "IncluScope Report": partner_incluscope_report(pid)

if __name__ == "__main__":
    main()
