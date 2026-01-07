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
    [data-testid="stSidebar"] { background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%); }
    [data-testid="stSidebar"] .stMarkdown { color: white; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

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
        st.caption("Demo: `partner_demo`/`partner123` or `ach_admin`/`impact2024`")

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

def get_pending(partner_id):
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
                                pending.append({"name": p.get("candidate_name"), "milestone": f"{m}-month", "id": p["id"], "month": m})
    except:
        pass
    return pending

def partner_dashboard():
    st.markdown('<p class="main-header">📊 Impact Dashboard</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="sub-header">{st.session_state.user_name}</p>', unsafe_allow_html=True)
    
    m = calculate_metrics(st.session_state.get("user_id", 1))
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'<div class="metric-container"><div class="metric-label">People Employed</div><div class="metric-value">{m["active"]}</div><div class="metric-delta">of {m["total"]} placed</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-container"><div class="metric-label">Retention Rate</div><div class="metric-value">{m["retention"]}%</div><div class="metric-delta">+{m["improvement"]}% vs baseline</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-container"><div class="metric-label">Cost Savings</div><div class="metric-value">£{m["savings"]:,}</div><div class="metric-delta">from retention</div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="metric-container"><div class="metric-label">Progressions</div><div class="metric-value">{m["progressions"]}</div><div class="metric-delta">promotions & pay rises</div></div>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'<div class="metric-container"><div class="metric-label">Living Wage</div><div class="metric-value">{m["living_wage"]}%</div><div class="metric-delta">above £12/hr</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-container"><div class="metric-label">Hard-to-Fill</div><div class="metric-value">{m["hard_roles"]}</div><div class="metric-delta">roles filled</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-container"><div class="metric-label">Training</div><div class="metric-value">{m["training"]}</div><div class="metric-delta">completions</div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="metric-container"><div class="metric-label">Avg Tenure</div><div class="metric-value">{m["tenure"]}</div><div class="metric-delta">months</div></div>', unsafe_allow_html=True)
    
    pending = get_pending(st.session_state.get("user_id", 1))
    if pending:
        st.markdown('<p class="section-header">⚠️ Reviews Due</p>', unsafe_allow_html=True)
        for p in pending[:3]:
            st.markdown(f'<div class="alert-card"><strong>{p["name"]}</strong> — {p["milestone"]} review due</div>', unsafe_allow_html=True)
    
    if m["employer_quotes"]:
        st.markdown('<p class="section-header">💬 Success Stories</p>', unsafe_allow_html=True)
        cols = st.columns(2)
        for i, (q, n) in enumerate(m["employer_quotes"][:4]):
            with cols[i % 2]:
                author = f'<div class="quote-author">— About {n}</div>' if n else ''
                st.markdown(f'<div class="quote-card"><div class="quote-text">"{q}"</div>{author}</div>', unsafe_allow_html=True)
    
    if m["candidate_quotes"]:
        st.markdown('<p class="section-header">🌟 In Their Own Words</p>', unsafe_allow_html=True)
        cols = st.columns(2)
        for i, (q, n) in enumerate(m["candidate_quotes"][:4]):
            with cols[i % 2]:
                author = f'<div class="quote-author">— {n}</div>' if n else ''
                st.markdown(f'<div class="quote-card candidate-quote"><div class="quote-text">"{q}"</div>{author}</div>', unsafe_allow_html=True)
    
    st.markdown('<p class="section-header">👥 Your Team</p>', unsafe_allow_html=True)
    for p in m["placements"]:
        status = "✅" if p.get("status") == "Active" else "⚪"
        st.markdown(f"{status} **{p['candidate_name']}** — {p['role']} (Started {p.get('start_date', 'N/A')})")

def partner_reports():
    st.markdown('<p class="main-header">📑 Impact Report</p>', unsafe_allow_html=True)
    m = calculate_metrics(st.session_state.get("user_id", 1))
    if m["total"] == 0:
        st.warning("No data yet.")
        return
    
    st.markdown(f'''<div class="highlight-card">
        <div style="display:flex;justify-content:space-between;align-items:center;">
            <div><div style="opacity:0.8;font-size:0.9rem;">IMPACT REPORT Q4 2024</div><div style="font-size:1.3rem;font-weight:600;margin-top:4px;">{st.session_state.user_name}</div></div>
            <div style="text-align:right;"><div class="highlight-value">{m["active"]}</div><div class="highlight-label">Lives Changed</div></div>
        </div>
    </div>''', unsafe_allow_html=True)
    
    st.markdown("### Executive Summary")
    st.markdown(f"""Through your partnership with ACH, you have created **{m["total"]} employment opportunities** for talented individuals from refugee and migrant backgrounds.
    
**Key Achievements:**
- 📈 **{m["retention"]}% retention** — {m["improvement"]}% above your baseline
- 💰 **£{m["savings"]:,} savings** from reduced turnover  
- 🎓 **{m["training"]} training completions**
- ⭐ **{m["progressions"]} career progressions**""")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Workforce Impact**")
        st.write(f"- Placements: **{m['total']}**")
        st.write(f"- Active: **{m['active']}**")
        st.write(f"- Retention: **{m['retention']}%**")
        st.write(f"- Tenure: **{m['tenure']} months**")
    with col2:
        st.markdown("**Business Value**")
        st.write(f"- Hard Roles: **{m['hard_roles']}**")
        st.write(f"- Savings: **£{m['savings']:,}**")
        st.write(f"- Living Wage: **{m['living_wage']}%**")
        st.write(f"- Progressions: **{m['progressions']}**")
    
    if m["employer_quotes"]:
        st.markdown("### Success Stories")
        for q, n in m["employer_quotes"][:3]:
            st.markdown(f'> "{q}"')
    
    if m["candidate_quotes"]:
        st.markdown("### Employee Voices")
        for q, n in m["candidate_quotes"][:3]:
            st.markdown(f'> "{q}"')
            if n: st.caption(f"— {n}")

def partner_baseline():
    st.markdown('<p class="main-header">📋 Baseline Data</p>', unsafe_allow_html=True)
    partner_id = st.session_state.get("user_id", 1)
    try:
        data = supabase.table("partner_baseline").select("*").eq("partner_id", partner_id).execute()
        if data.data:
            for r in data.data:
                with st.expander(f"**{r['role_title']}** — £{r.get('salary',0):,}/year"):
                    st.write(f"Retention: {r.get('retention_rate')}% | Difficulty: {r.get('difficulty')} | Living Wage: {'Yes' if r.get('living_wage') else 'No'}")
    except:
        pass

def partner_interviews():
    st.markdown('<p class="main-header">🎤 Interview Feedback</p>', unsafe_allow_html=True)
    partner_id = st.session_state.get("user_id", 1)
    try:
        data = supabase.table("interview_feedback").select("*").eq("partner_id", partner_id).execute()
        if data.data:
            hired = len([f for f in data.data if f.get("hired")])
            st.metric("Candidates Hired", hired, f"of {len(data.data)} interviewed")
            for f in data.data[:5]:
                status = "✅" if f.get("hired") else "❌"
                st.write(f"{status} **{f.get('candidate_name')}** — {f.get('role')}")
    except:
        st.info("No feedback recorded yet.")

def partner_milestones():
    st.markdown('<p class="main-header">📅 Milestone Reviews</p>', unsafe_allow_html=True)
    pending = get_pending(st.session_state.get("user_id", 1))
    if pending:
        st.warning(f"{len(pending)} reviews pending")
        for p in pending:
            st.write(f"⏰ **{p['name']}** — {p['milestone']} review due")
    else:
        st.success("✓ All reviews complete!")

def ach_dashboard():
    st.markdown('<p class="main-header">📊 Programme Dashboard</p>', unsafe_allow_html=True)
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
                st.write(f"Sector: {partner.get('sector')} | Contact: {partner.get('contact_name')} | Tier: {partner.get('subscription_tier')}")
        
        st.markdown('<p class="section-header">Recent Placements</p>', unsafe_allow_html=True)
        recent = sorted(placements.data or [], key=lambda x: x.get("start_date", ""), reverse=True)[:6]
        for p in recent:
            st.write(f"{'✅' if p.get('status')=='Active' else '⚪'} **{p['candidate_name']}** — {p['role']} at {p['partner_name']}")
    except Exception as e:
        st.error(f"Error: {e}")

def ach_partners():
    st.markdown('<p class="main-header">🏢 Partners</p>', unsafe_allow_html=True)
    try:
        data = supabase.table("impact_partners").select("*").execute()
        for p in (data.data or []):
            with st.expander(f"**{p['name']}**"):
                st.write(f"Sector: {p.get('sector')} | Contact: {p.get('contact_name')} ({p.get('contact_email')})")
    except:
        pass

def ach_candidates():
    st.markdown('<p class="main-header">👥 Candidates</p>', unsafe_allow_html=True)
    try:
        data = supabase.table("placements").select("*").execute()
        active = [p for p in (data.data or []) if p.get("status") == "Active"]
        st.metric("Active Placements", len(active))
        for p in active[:10]:
            st.write(f"✅ **{p['candidate_name']}** — {p['role']} at {p['partner_name']}")
    except:
        pass

def main():
    if not st.session_state.logged_in:
        login_page()
        return
    
    with st.sidebar:
        st.markdown(f"### 👋 Welcome")
        st.markdown(f"**{st.session_state.user_name}**")
        st.markdown("---")
        
        if st.session_state.user_type == "ach_staff":
            page = st.radio("", ["Dashboard", "Partners", "Candidates"], label_visibility="collapsed")
        else:
            page = st.radio("", ["Dashboard", "Baseline", "Interviews", "Milestones", "Report"], label_visibility="collapsed")
        
        st.markdown("---")
        if st.button("Logout", use_container_width=True):
            for k in ["logged_in", "user_type", "user_id", "user_name"]:
                st.session_state[k] = None if k != "logged_in" else False
            st.rerun()
    
    if st.session_state.user_type == "ach_staff":
        {"Dashboard": ach_dashboard, "Partners": ach_partners, "Candidates": ach_candidates}[page]()
    else:
        {"Dashboard": partner_dashboard, "Baseline": partner_baseline, "Interviews": partner_interviews, "Milestones": partner_milestones, "Report": partner_reports}[page]()

if __name__ == "__main__":
    main()
