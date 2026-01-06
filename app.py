import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime, date, timedelta
import plotly.express as px
import plotly.graph_objects as go

# Page config
st.set_page_config(
    page_title="ACH Impact System",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Supabase connection
@st.cache_resource
def init_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #0f1c3f;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1rem;
        color: #64748b;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #f8fafc, #f1f5f9);
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        text-align: center;
    }
    .metric-value {
        font-size: 2.2rem;
        font-weight: 700;
        color: #0f1c3f;
    }
    .metric-label {
        font-size: 0.875rem;
        color: #64748b;
        margin-top: 0.25rem;
    }
    .metric-sublabel {
        font-size: 0.75rem;
        color: #94a3b8;
        margin-top: 0.25rem;
    }
    .success-metric {
        background: linear-gradient(135deg, #ecfdf5, #d1fae5);
        border-color: #a7f3d0;
    }
    .success-metric .metric-value {
        color: #059669;
    }
    .warning-metric {
        background: linear-gradient(135deg, #fffbeb, #fef3c7);
        border-color: #fcd34d;
    }
    .warning-metric .metric-value {
        color: #d97706;
    }
    .highlight-metric {
        background: linear-gradient(135deg, #0f1c3f, #1a2d5a);
        border: none;
    }
    .highlight-metric .metric-value, .highlight-metric .metric-label, .highlight-metric .metric-sublabel {
        color: white;
    }
    .highlight-metric .metric-sublabel {
        opacity: 0.7;
    }
    .section-card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        border: 1px solid #e2e8f0;
        margin-bottom: 1rem;
    }
    .section-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #0f1c3f;
        margin-bottom: 1rem;
        padding-bottom: 0.75rem;
        border-bottom: 1px solid #e2e8f0;
    }
    .benefit-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.75rem 0;
        border-bottom: 1px solid #f1f5f9;
    }
    .benefit-row:last-child {
        border-bottom: none;
    }
    .benefit-label {
        font-size: 0.9rem;
        color: #475569;
    }
    .benefit-value {
        font-weight: 600;
        color: #0f1c3f;
    }
    .benefit-value.positive {
        color: #059669;
    }
    .benefit-comparison {
        font-size: 0.8rem;
        color: #94a3b8;
    }
    .impact-stat {
        text-align: center;
        padding: 1rem;
    }
    .impact-number {
        font-size: 2rem;
        font-weight: 700;
        color: #0f1c3f;
    }
    .impact-label {
        font-size: 0.85rem;
        color: #64748b;
    }
    .data-due-card {
        background: white;
        border: 2px solid #fcd34d;
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 0.75rem;
    }
    .data-due-card.overdue {
        border-color: #f87171;
        background: #fef2f2;
    }
    .submission-success {
        background: linear-gradient(135deg, #ecfdf5, #d1fae5);
        border: 2px solid #34d399;
        border-radius: 16px;
        padding: 2rem;
        text-align: center;
        margin: 1rem 0;
    }
    .alert-box {
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
    .alert-info {
        background: #eff6ff;
        border: 1px solid #93c5fd;
        color: #1e40af;
    }
</style>
""", unsafe_allow_html=True)

# Session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_type' not in st.session_state:
    st.session_state.user_type = None
if 'user_data' not in st.session_state:
    st.session_state.user_data = None
if 'just_submitted' not in st.session_state:
    st.session_state.just_submitted = False
if 'previous_score' not in st.session_state:
    st.session_state.previous_score = None

# Helper functions
def get_partners():
    response = supabase.table('partners').select('*').execute()
    return pd.DataFrame(response.data) if response.data else pd.DataFrame()

def get_candidates(partner_id=None):
    if partner_id:
        response = supabase.table('candidates').select('*').eq('partner_id', partner_id).execute()
    else:
        response = supabase.table('candidates').select('*').execute()
    return pd.DataFrame(response.data) if response.data else pd.DataFrame()

def get_partner_submissions(partner_id=None):
    if partner_id:
        response = supabase.table('partner_submissions').select('*').eq('partner_id', partner_id).execute()
    else:
        response = supabase.table('partner_submissions').select('*').execute()
    return pd.DataFrame(response.data) if response.data else pd.DataFrame()

def calculate_employer_impact_rating(partner_id):
    """Calculate Impact Rating - methodology hidden from partners"""
    candidates = get_candidates(partner_id)
    submissions = get_partner_submissions(partner_id)
    partner = supabase.table('partners').select('*').eq('id', partner_id).execute().data
    
    if not partner:
        return 0
    
    partner = partner[0]
    
    # Living wage (25%)
    living_wage_score = 100 if partner.get('living_wage_compliant') else (partner.get('living_wage_rate', 0) / 12.60) * 100
    
    # Retention (25%)
    if len(candidates) > 0:
        active = len(candidates[candidates['status'] == 'Active']) if 'status' in candidates.columns else len(candidates)
        retention_score = min(100, (active / len(candidates)) * 100)
    else:
        retention_score = 100
    
    # Progression (20%)
    progression_score = 50
    if len(submissions) > 0:
        avg_training = submissions['training_hours'].mean() if 'training_hours' in submissions.columns else 0
        promotions = submissions['promoted'].sum() if 'promoted' in submissions.columns else 0
        progression_score = min(100, (avg_training * 2.5) + (promotions * 15))
    
    # Outcomes (20%)
    outcomes_score = 50
    if len(candidates) > 0 and 'current_wellbeing' in candidates.columns and 'baseline_wellbeing' in candidates.columns:
        avg_improvement = (candidates['current_wellbeing'] - candidates['baseline_wellbeing']).mean()
        outcomes_score = min(100, max(0, 50 + (avg_improvement * 1.67)))
    
    # Inclusive practices (10%)
    inclusive_score = 50
    if len(submissions) > 0:
        practices = 0
        if 'flexible_hours' in submissions.columns and submissions['flexible_hours'].any():
            practices += 25
        if 'language_support' in submissions.columns and submissions['language_support'].any():
            practices += 25
        if 'mentor_assigned' in submissions.columns and submissions['mentor_assigned'].any():
            practices += 25
        inclusive_score = min(100, practices + 25)
    
    total = (living_wage_score * 0.25 + retention_score * 0.25 + progression_score * 0.20 + outcomes_score * 0.20 + inclusive_score * 0.10)
    
    return round(total)

def get_partner_metrics(partner_id):
    """Get business benefit and social impact metrics for a partner"""
    candidates = get_candidates(partner_id)
    submissions = get_partner_submissions(partner_id)
    partner = supabase.table('partners').select('*').eq('id', partner_id).execute().data[0]
    
    metrics = {}
    
    # Business Benefits
    total = len(candidates) if len(candidates) > 0 else 0
    active = len(candidates[candidates['status'] == 'Active']) if 'status' in candidates.columns and len(candidates) > 0 else 0
    
    metrics['retention_rate'] = round((active / total) * 100) if total > 0 else 0
    metrics['sector_avg_retention'] = 72  # Industry benchmark
    metrics['retention_premium'] = metrics['retention_rate'] - metrics['sector_avg_retention']
    
    # Cost savings (£4,500 avg cost to replace an employee)
    retained_above_avg = max(0, (metrics['retention_rate'] - metrics['sector_avg_retention']) / 100 * total)
    metrics['cost_savings'] = round(retained_above_avg * 4500)
    
    # Training investment
    metrics['training_hours'] = round(submissions['training_hours'].sum()) if len(submissions) > 0 and 'training_hours' in submissions.columns else 0
    
    # Promotions
    metrics['promotions'] = int(submissions['promoted'].sum()) if len(submissions) > 0 and 'promoted' in submissions.columns else 0
    
    # Social Impact
    metrics['people_employed'] = active
    metrics['total_placements'] = total
    
    if len(candidates) > 0 and 'current_wellbeing' in candidates.columns and 'baseline_wellbeing' in candidates.columns:
        metrics['avg_wellbeing_change'] = round((candidates['current_wellbeing'] - candidates['baseline_wellbeing']).mean())
    else:
        metrics['avg_wellbeing_change'] = 0
    
    if len(candidates) > 0 and 'psychological_safety' in candidates.columns:
        metrics['avg_psych_safety'] = round(candidates['psychological_safety'].mean())
    else:
        metrics['avg_psych_safety'] = 0
    
    metrics['living_wage_compliant'] = partner.get('living_wage_compliant', False)
    metrics['living_wage_rate'] = partner.get('living_wage_rate', 0)
    
    return metrics

def get_candidates_needing_update(partner_id):
    """Get candidates who need data submission"""
    candidates = get_candidates(partner_id)
    submissions = get_partner_submissions(partner_id)
    
    needs_update = []
    
    if len(candidates) == 0:
        return needs_update
    
    for _, candidate in candidates.iterrows():
        if candidate.get('status') != 'Active':
            continue
            
        candidate_submissions = submissions[submissions['candidate_id'] == candidate['id']] if len(submissions) > 0 else pd.DataFrame()
        
        if len(candidate_submissions) == 0:
            needs_update.append({
                'candidate': candidate,
                'status': 'overdue',
                'message': 'No data submitted yet'
            })
        else:
            last_sub = pd.to_datetime(candidate_submissions['submitted_at']).max()
            days_since = (datetime.now() - last_sub).days
            
            if days_since > 90:
                needs_update.append({
                    'candidate': candidate,
                    'status': 'overdue',
                    'message': f'Last update {days_since} days ago'
                })
            elif days_since > 75:
                needs_update.append({
                    'candidate': candidate,
                    'status': 'due_soon',
                    'message': f'Update due in {90 - days_since} days'
                })
    
    return needs_update

# Login page
def show_login():
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<h1 style='text-align: center; color: #0f1c3f;'>🌍 ACH Impact System</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #64748b;'>Bridge to Employment — Holistic Impact Measurement</p>", unsafe_allow_html=True)
        
        st.markdown("---")
        
        login_type = st.radio("I am:", ["ACH Staff", "Partner Organisation"], horizontal=True)
        
        if login_type == "ACH Staff":
            password = st.text_input("ACH Staff Password", type="password")
            if st.button("Login", use_container_width=True):
                if password == "ach2025":
                    st.session_state.logged_in = True
                    st.session_state.user_type = "ach"
                    st.session_state.user_data = {"name": "ACH Staff"}
                    st.rerun()
                else:
                    st.error("Incorrect password")
        else:
            email = st.text_input("Organisation Email")
            password = st.text_input("Password", type="password")
            if st.button("Login", use_container_width=True):
                response = supabase.table('partners').select('*').eq('contact_email', email).execute()
                if response.data and response.data[0].get('contact_password') == password:
                    st.session_state.logged_in = True
                    st.session_state.user_type = "partner"
                    st.session_state.user_data = response.data[0]
                    st.rerun()
                else:
                    st.error("Invalid email or password")
        
        st.markdown("---")
        st.markdown("""
        <div style='text-align: center; font-size: 0.8rem; color: #94a3b8;'>
        <strong>Demo Credentials</strong><br>
        ACH Staff: <code>ach2025</code><br>
        Partner: <code>priya.sharma@birmingham.gov.uk</code> / <code>demo123</code>
        </div>
        """, unsafe_allow_html=True)

# ACH Dashboard
def show_ach_dashboard():
    st.markdown("<h1 class='main-header'>Impact Dashboard</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-header'>Overview of all Bridge to Employment partnerships</p>", unsafe_allow_html=True)
    
    partners = get_partners()
    candidates = get_candidates()
    
    # Metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        active_candidates = len(candidates[candidates['status'] == 'Active']) if 'status' in candidates.columns else len(candidates)
        st.markdown(f"""
        <div class="metric-card highlight-metric">
            <div class="metric-value">{active_candidates}</div>
            <div class="metric-label">People in Work</div>
            <div class="metric-sublabel">Across {len(partners)} partners</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        if len(candidates) > 0 and 'psychological_safety' in candidates.columns:
            avg_safety = round(candidates['psychological_safety'].mean())
        else:
            avg_safety = 0
        st.markdown(f"""
        <div class="metric-card success-metric">
            <div class="metric-value">{avg_safety}%</div>
            <div class="metric-label">Feel Safe at Work</div>
            <div class="metric-sublabel">Psychological safety score</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        if len(candidates) > 0 and 'current_wellbeing' in candidates.columns and 'baseline_wellbeing' in candidates.columns:
            avg_improvement = round((candidates['current_wellbeing'] - candidates['baseline_wellbeing']).mean())
        else:
            avg_improvement = 0
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">+{avg_improvement}</div>
            <div class="metric-label">Wellbeing Improvement</div>
            <div class="metric-sublabel">Average point increase</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        all_submissions = get_partner_submissions()
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{len(all_submissions)}</div>
            <div class="metric-label">Data Submissions</div>
            <div class="metric-sublabel">Partner quarterly updates</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Two columns
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Partner Organisations")
        if len(partners) > 0:
            partner_data = []
            for _, p in partners.iterrows():
                rating = calculate_employer_impact_rating(p['id'])
                cands = get_candidates(p['id'])
                active = len(cands[cands['status'] == 'Active']) if 'status' in cands.columns and len(cands) > 0 else 0
                partner_data.append({
                    'Organisation': p['organisation_name'],
                    'Placements': active,
                    'Living Wage': '✓' if p.get('living_wage_compliant') else '✗',
                    'Impact Rating': rating
                })
            
            df = pd.DataFrame(partner_data).sort_values('Impact Rating', ascending=False)
            st.dataframe(df, use_container_width=True, hide_index=True)
    
    with col2:
        st.subheader("Candidate Wellbeing Progress")
        if len(candidates) > 0 and 'current_wellbeing' in candidates.columns and 'baseline_wellbeing' in candidates.columns:
            chart_data = candidates[['candidate_name', 'baseline_wellbeing', 'current_wellbeing']].head(8)
            chart_data = chart_data.melt(id_vars=['candidate_name'], 
                                         value_vars=['baseline_wellbeing', 'current_wellbeing'],
                                         var_name='Type', value_name='Score')
            chart_data['Type'] = chart_data['Type'].replace({
                'baseline_wellbeing': 'Baseline',
                'current_wellbeing': 'Current'
            })
            
            fig = px.bar(chart_data, x='candidate_name', y='Score', color='Type',
                        barmode='group', 
                        color_discrete_map={'Baseline': '#94a3b8', 'Current': '#059669'})
            fig.update_layout(
                xaxis_title="",
                yaxis_title="Wellbeing Score",
                legend_title="",
                height=300,
                margin=dict(l=0, r=0, t=10, b=0)
            )
            st.plotly_chart(fig, use_container_width=True)

# ACH Data Management
def show_ach_data_management():
    st.markdown("<h1 class='main-header'>Data Management</h1>", unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4 = st.tabs(["Partners", "Candidates", "Submissions", "Add New"])
    
    with tab1:
        partners = get_partners()
        if len(partners) > 0:
            display_df = partners[['id', 'organisation_name', 'sector', 'contact_name', 'contact_email', 'living_wage_rate', 'living_wage_compliant', 'status']].copy()
            display_df.columns = ['ID', 'Organisation', 'Sector', 'Contact', 'Email', 'Wage Rate', 'Living Wage', 'Status']
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.info("No partners yet")
    
    with tab2:
        candidates = get_candidates()
        if len(candidates) > 0:
            display_df = candidates[['id', 'partner_id', 'candidate_name', 'role', 'status', 'baseline_wellbeing', 'current_wellbeing', 'psychological_safety']].copy()
            display_df.columns = ['ID', 'Partner', 'Name', 'Role', 'Status', 'Baseline', 'Current', 'Psych Safety']
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.info("No candidates yet")
    
    with tab3:
        submissions = get_partner_submissions()
        if len(submissions) > 0:
            st.dataframe(submissions, use_container_width=True, hide_index=True)
        else:
            st.info("No submissions yet")
    
    with tab4:
        st.subheader("Add New Partner")
        with st.form("new_partner"):
            col1, col2 = st.columns(2)
            with col1:
                org_name = st.text_input("Organisation Name*")
                sector = st.selectbox("Sector", ["Healthcare", "Social Care", "Hospitality", "Retail", "Manufacturing", "Public Sector", "Environmental Services", "Food & Retail", "Other"])
                employee_count = st.number_input("Employee Count", min_value=1, value=100)
                contact_name = st.text_input("Contact Name*")
            with col2:
                contact_email = st.text_input("Contact Email*")
                contact_password = st.text_input("Password for Portal*", type="password")
                living_wage_rate = st.number_input("Hourly Wage Rate (£)", min_value=0.0, value=12.60, step=0.10)
                living_wage_compliant = living_wage_rate >= 12.60
                st.write(f"Living Wage Compliant: {'✓ Yes' if living_wage_compliant else '✗ No (below £12.60)'}")
            
            if st.form_submit_button("Add Partner", use_container_width=True):
                if org_name and contact_name and contact_email and contact_password:
                    partners = get_partners()
                    new_id = f"P{str(len(partners) + 1).zfill(3)}"
                    
                    if employee_count <= 10:
                        size_tier = "Micro"
                    elif employee_count <= 50:
                        size_tier = "Small"
                    elif employee_count <= 250:
                        size_tier = "Medium"
                    elif employee_count <= 1000:
                        size_tier = "Large"
                    else:
                        size_tier = "Enterprise"
                    
                    data = {
                        "id": new_id,
                        "organisation_name": org_name,
                        "sector": sector,
                        "employee_count": employee_count,
                        "size_tier": size_tier,
                        "contact_name": contact_name,
                        "contact_email": contact_email,
                        "contact_password": contact_password,
                        "living_wage_rate": living_wage_rate,
                        "living_wage_compliant": living_wage_compliant,
                        "partnership_start_date": str(date.today()),
                        "status": "Active"
                    }
                    
                    supabase.table('partners').insert(data).execute()
                    st.success(f"✓ Partner added successfully! ID: {new_id}")
                    st.rerun()
                else:
                    st.error("Please fill all required fields")
        
        st.markdown("---")
        
        st.subheader("Add New Candidate")
        with st.form("new_candidate"):
            partners = get_partners()
            col1, col2 = st.columns(2)
            with col1:
                if len(partners) > 0:
                    partner_options = dict(zip(partners['organisation_name'], partners['id']))
                    selected_partner = st.selectbox("Partner Organisation*", options=list(partner_options.keys()))
                    partner_id = partner_options[selected_partner]
                else:
                    st.warning("Add a partner first")
                    partner_id = None
                
                candidate_name = st.text_input("Candidate Name*")
                role = st.text_input("Role*")
            with col2:
                hourly_rate = st.number_input("Hourly Rate (£)", min_value=0.0, value=12.60, step=0.10)
                start_date = st.date_input("Start Date")
                baseline_wellbeing = st.slider("Baseline Wellbeing Score", 0, 100, 50)
            
            if st.form_submit_button("Add Candidate", use_container_width=True):
                if partner_id and candidate_name and role:
                    candidates = get_candidates()
                    new_id = f"C{str(len(candidates) + 1).zfill(3)}"
                    
                    data = {
                        "id": new_id,
                        "partner_id": partner_id,
                        "candidate_name": candidate_name,
                        "role": role,
                        "hourly_rate": hourly_rate,
                        "start_date": str(start_date),
                        "status": "Active",
                        "baseline_wellbeing": baseline_wellbeing,
                        "current_wellbeing": baseline_wellbeing,
                        "psychological_safety": 50,
                        "next_checkin_due": str(start_date + timedelta(days=90))
                    }
                    
                    supabase.table('candidates').insert(data).execute()
                    st.success(f"✓ Candidate added! ID: {new_id}")
                    st.rerun()
                else:
                    st.error("Please fill all required fields")

# Partner Dashboard - Shows metrics, not calculations
def show_partner_dashboard():
    partner = st.session_state.user_data
    partner_id = partner['id']
    
    # Check if we just submitted
    if st.session_state.just_submitted and st.session_state.previous_score is not None:
        current_score = calculate_employer_impact_rating(partner_id)
        score_change = current_score - st.session_state.previous_score
        
        st.markdown(f"""
        <div class="submission-success">
            <h2 style="color: #059669; margin-bottom: 0.5rem;">✓ Data Submitted Successfully</h2>
            <p style="font-size: 1.1rem; color: #065f46;">Your Impact Rating has been updated</p>
            <div style="font-size: 3rem; font-weight: 700; color: #0f1c3f; margin: 1rem 0;">
                {current_score}
                <span style="font-size: 1.2rem; color: {'#059669' if score_change >= 0 else '#dc2626'};">
                    ({'+' if score_change >= 0 else ''}{score_change} from previous)
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.session_state.just_submitted = False
        st.session_state.previous_score = None
    
    st.markdown(f"<h1 class='main-header'>{partner['organisation_name']}</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-header'>Your Bridge to Employment Partnership Dashboard</p>", unsafe_allow_html=True)
    
    impact_rating = calculate_employer_impact_rating(partner_id)
    metrics = get_partner_metrics(partner_id)
    
    # Top metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card highlight-metric">
            <div class="metric-value">{impact_rating}</div>
            <div class="metric-label">Employer Impact Rating</div>
            <div class="metric-sublabel">Out of 100</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{metrics['people_employed']}</div>
            <div class="metric-label">People in Work</div>
            <div class="metric-sublabel">{metrics['total_placements']} total placed</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        css_class = "success-metric" if metrics['avg_wellbeing_change'] > 0 else ""
        sign = "+" if metrics['avg_wellbeing_change'] >= 0 else ""
        st.markdown(f"""
        <div class="metric-card {css_class}">
            <div class="metric-value">{sign}{metrics['avg_wellbeing_change']}</div>
            <div class="metric-label">Wellbeing Improvement</div>
            <div class="metric-sublabel">Average point increase</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        css_class = "success-metric" if metrics['living_wage_compliant'] else "warning-metric"
        status = "✓ Compliant" if metrics['living_wage_compliant'] else "Below threshold"
        st.markdown(f"""
        <div class="metric-card {css_class}">
            <div class="metric-value">£{metrics['living_wage_rate']}</div>
            <div class="metric-label">Hourly Rate</div>
            <div class="metric-sublabel">{status}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Two columns: Business Benefits and Social Impact
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="section-card">
            <div class="section-title">📊 Business Benefits</div>
        """, unsafe_allow_html=True)
        
        # Retention comparison
        retention_class = "positive" if metrics['retention_premium'] > 0 else ""
        retention_sign = "+" if metrics['retention_premium'] > 0 else ""
        
        st.markdown(f"""
            <div class="benefit-row">
                <div>
                    <div class="benefit-label">Staff Retention Rate</div>
                    <div class="benefit-comparison">Sector average: {metrics['sector_avg_retention']}%</div>
                </div>
                <div style="text-align: right;">
                    <div class="benefit-value">{metrics['retention_rate']}%</div>
                    <div class="benefit-value {retention_class}">{retention_sign}{metrics['retention_premium']}% vs sector</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # Cost savings
        st.markdown(f"""
            <div class="benefit-row">
                <div>
                    <div class="benefit-label">Estimated Turnover Savings</div>
                    <div class="benefit-comparison">Based on £4,500 avg replacement cost</div>
                </div>
                <div style="text-align: right;">
                    <div class="benefit-value positive">£{metrics['cost_savings']:,}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # Training
        st.markdown(f"""
            <div class="benefit-row">
                <div>
                    <div class="benefit-label">Training Hours Invested</div>
                    <div class="benefit-comparison">Across all candidates</div>
                </div>
                <div style="text-align: right;">
                    <div class="benefit-value">{metrics['training_hours']} hours</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # Promotions
        st.markdown(f"""
            <div class="benefit-row">
                <div>
                    <div class="benefit-label">Internal Promotions</div>
                    <div class="benefit-comparison">Career progression</div>
                </div>
                <div style="text-align: right;">
                    <div class="benefit-value">{metrics['promotions']}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="section-card">
            <div class="section-title">🌍 Social Impact Generated</div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1rem;">
                <div class="impact-stat">
                    <div class="impact-number">{metrics['people_employed']}</div>
                    <div class="impact-label">Refugees & Migrants<br>in Meaningful Work</div>
                </div>
                <div class="impact-stat">
                    <div class="impact-number">+{metrics['avg_wellbeing_change']}</div>
                    <div class="impact-label">Average Wellbeing<br>Score Improvement</div>
                </div>
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                <div class="impact-stat">
                    <div class="impact-number">{metrics['avg_psych_safety']}%</div>
                    <div class="impact-label">Feel Psychologically<br>Safe at Work</div>
                </div>
                <div class="impact-stat">
                    <div class="impact-number">{'✓' if metrics['living_wage_compliant'] else '✗'}</div>
                    <div class="impact-label">Real Living Wage<br>Employer</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Data collection status and candidates
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Data Collection Status")
        needs_update = get_candidates_needing_update(partner_id)
        
        if needs_update:
            for item in needs_update:
                candidate = item['candidate']
                status_class = "overdue" if item['status'] == 'overdue' else ""
                status_icon = "🔴" if item['status'] == 'overdue' else "🟡"
                
                st.markdown(f"""
                <div class="data-due-card {status_class}">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <strong>{candidate['candidate_name']}</strong><br>
                            <span style="font-size: 0.85rem; color: #64748b;">{candidate.get('role', '')}</span>
                        </div>
                        <div style="text-align: right;">
                            {status_icon} {item['message']}
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.success("✓ All candidates are up to date")
    
    with col2:
        st.subheader("Your Candidates")
        candidates = get_candidates(partner_id)
        if len(candidates) > 0:
            display_data = []
            for _, c in candidates.iterrows():
                improvement = c.get('current_wellbeing', 0) - c.get('baseline_wellbeing', 0)
                display_data.append({
                    'Name': c['candidate_name'],
                    'Role': c.get('role', ''),
                    'Status': c.get('status', ''),
                    'Wellbeing': f"+{improvement}" if improvement >= 0 else str(improvement),
                    'Psych Safety': f"{c.get('psychological_safety', 0)}%"
                })
            st.dataframe(pd.DataFrame(display_data), use_container_width=True, hide_index=True)
        else:
            st.info("No candidates placed yet")

# Partner Data Submission
def show_partner_submission():
    partner = st.session_state.user_data
    partner_id = partner['id']
    
    st.markdown("<h1 class='main-header'>Submit Quarterly Update</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-header'>Provide updates on your candidates to track outcomes</p>", unsafe_allow_html=True)
    
    candidates = get_candidates(partner_id)
    active_candidates = candidates[candidates['status'] == 'Active'] if 'status' in candidates.columns else candidates
    
    if len(active_candidates) == 0:
        st.warning("No active candidates to update")
        return
    
    with st.form("partner_submission"):
        # Candidate selection
        candidate_options = dict(zip(active_candidates['candidate_name'], active_candidates['id']))
        selected_candidate_name = st.selectbox("Select Candidate", options=list(candidate_options.keys()))
        candidate_id = candidate_options[selected_candidate_name]
        
        selected_candidate = active_candidates[active_candidates['id'] == candidate_id].iloc[0]
        
        st.markdown("---")
        
        # Employment Status
        st.subheader("Employment Status")
        col1, col2 = st.columns(2)
        with col1:
            still_employed = st.radio("Is this candidate still employed?", ["Yes", "No"], horizontal=True)
        with col2:
            if still_employed == "No":
                left_reason = st.selectbox("Reason for leaving", [
                    "Resigned - personal reasons",
                    "Resigned - found other employment",
                    "End of contract",
                    "Dismissed - performance",
                    "Dismissed - conduct",
                    "Redundancy",
                    "Other"
                ])
            else:
                left_reason = None
        
        st.markdown("---")
        
        # Compensation
        st.subheader("Compensation")
        col1, col2 = st.columns(2)
        with col1:
            current_rate = st.number_input(
                "Current hourly rate (£)", 
                min_value=0.0, 
                value=float(selected_candidate.get('hourly_rate', 12.60)),
                step=0.10
            )
        with col2:
            pay_increase = st.checkbox("Pay increase since last update?")
        
        st.markdown("---")
        
        # Training & Development
        st.subheader("Training & Development")
        col1, col2 = st.columns(2)
        with col1:
            training_hours = st.number_input("Training hours provided this quarter", min_value=0, value=0)
            training_type = st.text_input("Type of training (if any)", placeholder="e.g. Health & Safety")
        with col2:
            promoted = st.checkbox("Promoted or given new responsibilities?")
            if promoted:
                promotion_details = st.text_input("Promotion details")
            else:
                promotion_details = None
        
        st.markdown("---")
        
        # Support Provided
        st.subheader("Support & Adjustments")
        col1, col2, col3 = st.columns(3)
        with col1:
            flexible_hours = st.checkbox("Flexible working hours")
        with col2:
            language_support = st.checkbox("Language support")
        with col3:
            mentor_assigned = st.checkbox("Mentor or buddy assigned")
        
        other_adjustments = st.text_area("Other support provided", placeholder="Describe any other adjustments...")
        
        st.markdown("---")
        
        # Wellbeing assessment
        st.subheader("Your Assessment")
        col1, col2 = st.columns(2)
        with col1:
            wellbeing_estimate = st.slider(
                "Overall Wellbeing",
                0, 100,
                value=int(selected_candidate.get('current_wellbeing', 50)),
                help="Your estimate of their overall stability"
            )
        with col2:
            psych_safety_estimate = st.slider(
                "Psychological Safety",
                0, 100,
                value=int(selected_candidate.get('psychological_safety', 50)),
                help="Do they feel safe to speak up and be themselves?"
            )
        
        concerns = st.text_area("Any concerns?", placeholder="Optional - note any concerns...")
        
        st.markdown("---")
        
        submitted = st.form_submit_button("Submit Update", use_container_width=True, type="primary")
        
        if submitted:
            # Store previous score
            st.session_state.previous_score = calculate_employer_impact_rating(partner_id)
            
            # Insert submission
            submission_data = {
                "partner_id": partner_id,
                "candidate_id": candidate_id,
                "still_employed": still_employed == "Yes",
                "left_reason": left_reason,
                "current_hourly_rate": current_rate,
                "pay_increase": pay_increase,
                "training_hours": training_hours,
                "training_type": training_type,
                "promoted": promoted,
                "promotion_details": promotion_details,
                "flexible_hours": flexible_hours,
                "language_support": language_support,
                "mentor_assigned": mentor_assigned,
                "other_adjustments": other_adjustments,
                "concerns": concerns
            }
            
            supabase.table('partner_submissions').insert(submission_data).execute()
            
            # Update candidate
            update_data = {
                "current_wellbeing": wellbeing_estimate,
                "psychological_safety": psych_safety_estimate,
                "hourly_rate": current_rate
            }
            
            if still_employed == "No":
                update_data["status"] = "Left"
            
            supabase.table('candidates').update(update_data).eq('id', candidate_id).execute()
            
            st.session_state.just_submitted = True
            st.rerun()

# Partner submission history
def show_partner_history():
    partner = st.session_state.user_data
    
    st.markdown("<h1 class='main-header'>Submission History</h1>", unsafe_allow_html=True)
    
    submissions = get_partner_submissions(partner['id'])
    
    if len(submissions) > 0:
        candidates = get_candidates(partner['id'])
        if len(candidates) > 0:
            candidate_names = dict(zip(candidates['id'], candidates['candidate_name']))
            submissions['Candidate'] = submissions['candidate_id'].map(candidate_names)
        
        display_cols = ['submitted_at', 'Candidate', 'still_employed', 'current_hourly_rate', 'training_hours', 'promoted']
        available_cols = [c for c in display_cols if c in submissions.columns]
        
        display_df = submissions[available_cols].copy()
        display_df.columns = ['Submitted', 'Candidate', 'Employed', 'Rate', 'Training', 'Promoted']
        display_df = display_df.sort_values('Submitted', ascending=False)
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)
    else:
        st.info("No submissions yet")

# Main app
def main():
    if not st.session_state.logged_in:
        show_login()
        return
    
    with st.sidebar:
        st.markdown("### 🌍 ACH Impact System")
        
        if st.session_state.user_type == "ach":
            st.markdown("**ACH Staff**")
        else:
            st.markdown(f"**{st.session_state.user_data.get('organisation_name', 'Partner')}**")
            st.markdown(f"_{st.session_state.user_data.get('contact_name', '')}_")
        
        st.markdown("---")
        
        if st.session_state.user_type == "ach":
            page = st.radio("Navigate", ["Dashboard", "Data Management", "Reports"], label_visibility="collapsed")
        else:
            page = st.radio("Navigate", ["Dashboard", "Submit Update", "Submission History"], label_visibility="collapsed")
        
        st.markdown("---")
        
        if st.button("Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user_type = None
            st.session_state.user_data = None
            st.session_state.just_submitted = False
            st.session_state.previous_score = None
            st.rerun()
    
    if st.session_state.user_type == "ach":
        if page == "Dashboard":
            show_ach_dashboard()
        elif page == "Data Management":
            show_ach_data_management()
        elif page == "Reports":
            st.markdown("<h1 class='main-header'>Reports</h1>", unsafe_allow_html=True)
            st.info("Report generation coming soon")
    else:
        if page == "Dashboard":
            show_partner_dashboard()
        elif page == "Submit Update":
            show_partner_submission()
        elif page == "Submission History":
            show_partner_history()

if __name__ == "__main__":
    main()
