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
    .score-breakdown {
        background: #f8fafc;
        border-radius: 12px;
        padding: 1.5rem;
        border: 1px solid #e2e8f0;
    }
    .score-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.75rem 0;
        border-bottom: 1px solid #e2e8f0;
    }
    .score-row:last-child {
        border-bottom: none;
    }
    .score-component {
        font-size: 0.9rem;
        color: #1e293b;
    }
    .score-weight {
        font-size: 0.8rem;
        color: #94a3b8;
    }
    .score-value {
        font-weight: 600;
        color: #0f1c3f;
    }
    .alert-box {
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
    .alert-warning {
        background: #fffbeb;
        border: 1px solid #fcd34d;
        color: #92400e;
    }
    .alert-success {
        background: #ecfdf5;
        border: 1px solid #6ee7b7;
        color: #065f46;
    }
    .alert-info {
        background: #eff6ff;
        border: 1px solid #93c5fd;
        color: #1e40af;
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

def calculate_score_breakdown(partner_id):
    """Calculate detailed score breakdown for a partner"""
    candidates = get_candidates(partner_id)
    submissions = get_partner_submissions(partner_id)
    partner = supabase.table('partners').select('*').eq('id', partner_id).execute().data
    
    if not partner:
        return None
    
    partner = partner[0]
    breakdown = {}
    
    # 1. Living Wage (25%)
    if partner.get('living_wage_compliant'):
        breakdown['living_wage'] = {
            'score': 100,
            'weight': 25,
            'weighted': 25,
            'detail': f"£{partner.get('living_wage_rate', 0)}/hr - Above Real Living Wage"
        }
    else:
        rate = partner.get('living_wage_rate', 0)
        score = min(100, (rate / 12.60) * 100) if rate else 0
        breakdown['living_wage'] = {
            'score': round(score),
            'weight': 25,
            'weighted': round(score * 0.25),
            'detail': f"£{rate}/hr - Below £12.60 threshold"
        }
    
    # 2. Retention (25%)
    if len(candidates) > 0:
        active = len(candidates[candidates['status'] == 'Active']) if 'status' in candidates.columns else len(candidates)
        retention_rate = (active / len(candidates)) * 100
        # Compare to industry benchmark of 72%
        retention_score = min(100, (retention_rate / 72) * 100) if retention_rate < 100 else 100
        breakdown['retention'] = {
            'score': round(retention_score),
            'weight': 25,
            'weighted': round(retention_score * 0.25),
            'detail': f"{round(retention_rate)}% retained ({active}/{len(candidates)} candidates)"
        }
    else:
        breakdown['retention'] = {
            'score': 100,
            'weight': 25,
            'weighted': 25,
            'detail': "No candidates yet"
        }
    
    # 3. Progression Support (20%)
    if len(submissions) > 0:
        avg_training = submissions['training_hours'].mean() if 'training_hours' in submissions.columns else 0
        promotions = submissions['promoted'].sum() if 'promoted' in submissions.columns else 0
        
        # Score: up to 50 points for training (20hrs = full), up to 50 for promotions
        training_score = min(50, (avg_training / 20) * 50)
        promotion_score = min(50, promotions * 15)
        progression_score = training_score + promotion_score
        
        breakdown['progression'] = {
            'score': round(progression_score),
            'weight': 20,
            'weighted': round(progression_score * 0.20),
            'detail': f"{round(avg_training)}hrs avg training, {promotions} promotions"
        }
    else:
        breakdown['progression'] = {
            'score': 50,
            'weight': 20,
            'weighted': 10,
            'detail': "No submissions yet - baseline score"
        }
    
    # 4. Candidate Outcomes (20%)
    if len(candidates) > 0 and 'current_wellbeing' in candidates.columns and 'baseline_wellbeing' in candidates.columns:
        avg_improvement = (candidates['current_wellbeing'] - candidates['baseline_wellbeing']).mean()
        # Score: 0 improvement = 50, +30 improvement = 100
        outcomes_score = min(100, max(0, 50 + (avg_improvement * 1.67)))
        breakdown['outcomes'] = {
            'score': round(outcomes_score),
            'weight': 20,
            'weighted': round(outcomes_score * 0.20),
            'detail': f"+{round(avg_improvement)} avg wellbeing improvement"
        }
    else:
        breakdown['outcomes'] = {
            'score': 50,
            'weight': 20,
            'weighted': 10,
            'detail': "Awaiting candidate check-ins"
        }
    
    # 5. Inclusive Practices (10%)
    if len(submissions) > 0:
        practices_count = 0
        practices_list = []
        
        if 'flexible_hours' in submissions.columns and submissions['flexible_hours'].any():
            practices_count += 1
            practices_list.append("Flexible hours")
        if 'language_support' in submissions.columns and submissions['language_support'].any():
            practices_count += 1
            practices_list.append("Language support")
        if 'mentor_assigned' in submissions.columns and submissions['mentor_assigned'].any():
            practices_count += 1
            practices_list.append("Mentoring")
        if 'other_adjustments' in submissions.columns and submissions['other_adjustments'].notna().any():
            practices_count += 1
            practices_list.append("Other adjustments")
        
        inclusive_score = min(100, practices_count * 25)
        breakdown['inclusive'] = {
            'score': inclusive_score,
            'weight': 10,
            'weighted': round(inclusive_score * 0.10),
            'detail': ", ".join(practices_list) if practices_list else "No practices recorded"
        }
    else:
        breakdown['inclusive'] = {
            'score': 50,
            'weight': 10,
            'weighted': 5,
            'detail': "No submissions yet - baseline score"
        }
    
    # Calculate total
    total = sum(item['weighted'] for item in breakdown.values())
    breakdown['total'] = round(total)
    
    return breakdown

def calculate_employer_impact_rating(partner_id):
    breakdown = calculate_score_breakdown(partner_id)
    return breakdown['total'] if breakdown else 0

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
            
        # Check last submission
        candidate_submissions = submissions[submissions['candidate_id'] == candidate['id']] if len(submissions) > 0 else pd.DataFrame()
        
        if len(candidate_submissions) == 0:
            # Never submitted
            needs_update.append({
                'candidate': candidate,
                'status': 'overdue',
                'message': 'No data submitted yet'
            })
        else:
            # Check if last submission was more than 90 days ago
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
        st.subheader("Partner Organisations Ranked")
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
        st.subheader("Candidates Overview")
        if len(candidates) > 0:
            # Create a chart
            if 'current_wellbeing' in candidates.columns and 'baseline_wellbeing' in candidates.columns:
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

# Partner Dashboard
def show_partner_dashboard():
    partner = st.session_state.user_data
    partner_id = partner['id']
    
    # Check if we just submitted
    if st.session_state.just_submitted and st.session_state.previous_score is not None:
        current_score = calculate_employer_impact_rating(partner_id)
        score_change = current_score - st.session_state.previous_score
        
        st.markdown(f"""
        <div class="submission-success">
            <h2 style="color: #059669; margin-bottom: 0.5rem;">✓ Data Submitted Successfully!</h2>
            <p style="font-size: 1.1rem; color: #065f46;">Your Impact Rating has been recalculated</p>
            <div style="font-size: 3rem; font-weight: 700; color: #0f1c3f; margin: 1rem 0;">
                {st.session_state.previous_score} → {current_score}
                <span style="font-size: 1.5rem; color: {'#059669' if score_change >= 0 else '#dc2626'};">
                    ({'+' if score_change >= 0 else ''}{score_change})
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Reset the flag
        st.session_state.just_submitted = False
        st.session_state.previous_score = None
    
    st.markdown(f"<h1 class='main-header'>{partner['organisation_name']}</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-header'>Your Bridge to Employment Partnership Dashboard</p>", unsafe_allow_html=True)
    
    candidates = get_candidates(partner_id)
    breakdown = calculate_score_breakdown(partner_id)
    impact_rating = breakdown['total'] if breakdown else 0
    
    # Metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card highlight-metric">
            <div class="metric-value">{impact_rating}</div>
            <div class="metric-label">Impact Rating</div>
            <div class="metric-sublabel">Out of 100</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        active = len(candidates[candidates['status'] == 'Active']) if 'status' in candidates.columns and len(candidates) > 0 else 0
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{active}</div>
            <div class="metric-label">Active Placements</div>
            <div class="metric-sublabel">{len(candidates)} total</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        if len(candidates) > 0 and 'current_wellbeing' in candidates.columns and 'baseline_wellbeing' in candidates.columns:
            avg_improvement = round((candidates['current_wellbeing'] - candidates['baseline_wellbeing']).mean())
        else:
            avg_improvement = 0
        css_class = "success-metric" if avg_improvement > 0 else ""
        st.markdown(f"""
        <div class="metric-card {css_class}">
            <div class="metric-value">+{avg_improvement}</div>
            <div class="metric-label">Avg Wellbeing Gain</div>
            <div class="metric-sublabel">Points improvement</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        wage_status = "✓" if partner.get('living_wage_compliant') else "✗"
        css_class = "success-metric" if partner.get('living_wage_compliant') else "warning-metric"
        st.markdown(f"""
        <div class="metric-card {css_class}">
            <div class="metric-value">£{partner.get('living_wage_rate', 0)}</div>
            <div class="metric-label">Hourly Rate</div>
            <div class="metric-sublabel">Living Wage: {wage_status}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Two columns - Score breakdown and candidates needing update
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("How Your Score is Calculated")
        
        if breakdown:
            components = [
                ('Living Wage', 'living_wage'),
                ('Retention', 'retention'),
                ('Progression Support', 'progression'),
                ('Candidate Outcomes', 'outcomes'),
                ('Inclusive Practices', 'inclusive')
            ]
            
            for label, key in components:
                data = breakdown[key]
                st.markdown(f"""
                <div style="display: flex; justify-content: space-between; align-items: center; padding: 0.75rem; background: #f8fafc; border-radius: 8px; margin-bottom: 0.5rem;">
                    <div>
                        <div style="font-weight: 600; color: #1e293b;">{label}</div>
                        <div style="font-size: 0.8rem; color: #64748b;">{data['detail']}</div>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-weight: 700; color: #0f1c3f;">{data['score']}/100</div>
                        <div style="font-size: 0.75rem; color: #94a3b8;">×{data['weight']}% = {data['weighted']}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 1rem; background: #0f1c3f; border-radius: 8px; margin-top: 1rem;">
                <div style="font-weight: 600; color: white;">Total Impact Rating</div>
                <div style="font-size: 1.5rem; font-weight: 700; color: white;">{breakdown['total']}</div>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
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
            st.success("All candidates are up to date!")
    
    st.markdown("---")
    
    # Candidates table
    st.subheader("Your Candidates")
    if len(candidates) > 0:
        display_data = []
        for _, c in candidates.iterrows():
            improvement = c.get('current_wellbeing', 0) - c.get('baseline_wellbeing', 0)
            display_data.append({
                'Name': c['candidate_name'],
                'Role': c.get('role', ''),
                'Status': c.get('status', ''),
                'Baseline': c.get('baseline_wellbeing', 0),
                'Current': c.get('current_wellbeing', 0),
                'Change': f"+{improvement}" if improvement >= 0 else str(improvement),
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
    st.markdown("<p class='sub-header'>This data helps us track outcomes and calculate your Impact Rating</p>", unsafe_allow_html=True)
    
    candidates = get_candidates(partner_id)
    active_candidates = candidates[candidates['status'] == 'Active'] if 'status' in candidates.columns else candidates
    
    if len(active_candidates) == 0:
        st.warning("No active candidates to update")
        return
    
    # Show current score
    current_score = calculate_employer_impact_rating(partner_id)
    st.markdown(f"""
    <div class="alert-box alert-info">
        <strong>Current Impact Rating: {current_score}/100</strong><br>
        Submit updates to see your score recalculate in real-time
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("partner_submission"):
        # Candidate selection
        candidate_options = dict(zip(active_candidates['candidate_name'], active_candidates['id']))
        selected_candidate_name = st.selectbox("Select Candidate*", options=list(candidate_options.keys()))
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
            training_type = st.text_input("Type of training (if any)", placeholder="e.g. Health & Safety, Customer Service")
        with col2:
            promoted = st.checkbox("Promoted or given new responsibilities?")
            if promoted:
                promotion_details = st.text_input("Promotion details", placeholder="e.g. Promoted to Team Leader")
            else:
                promotion_details = None
        
        st.markdown("---")
        
        # Support Provided
        st.subheader("Support & Adjustments Provided")
        col1, col2, col3 = st.columns(3)
        with col1:
            flexible_hours = st.checkbox("Flexible working hours")
        with col2:
            language_support = st.checkbox("Language support")
        with col3:
            mentor_assigned = st.checkbox("Mentor or buddy assigned")
        
        other_adjustments = st.text_area(
            "Other adjustments or support provided",
            placeholder="Describe any other workplace adjustments or support..."
        )
        
        st.markdown("---")
        
        # Wellbeing update
        st.subheader("Candidate Wellbeing (Your Assessment)")
        st.write("Based on your observations, how would you rate this candidate's current wellbeing and workplace integration?")
        
        col1, col2 = st.columns(2)
        with col1:
            wellbeing_estimate = st.slider(
                "Overall Wellbeing",
                0, 100,
                value=int(selected_candidate.get('current_wellbeing', 50)),
                help="Your estimate of their overall life stability and wellbeing"
            )
        with col2:
            psych_safety_estimate = st.slider(
                "Psychological Safety at Work",
                0, 100,
                value=int(selected_candidate.get('psychological_safety', 50)),
                help="Do they feel safe to speak up, ask questions, and be themselves?"
            )
        
        concerns = st.text_area(
            "Any concerns about this candidate?",
            placeholder="Optional - note any concerns ACH should be aware of..."
        )
        
        st.markdown("---")
        
        submitted = st.form_submit_button("Submit Update", use_container_width=True, type="primary")
        
        if submitted:
            # Store previous score for comparison
            st.session_state.previous_score = current_score
            
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
            
            # Update candidate record
            update_data = {
                "current_wellbeing": wellbeing_estimate,
                "psychological_safety": psych_safety_estimate,
                "hourly_rate": current_rate
            }
            
            if still_employed == "No":
                update_data["status"] = "Left"
            
            supabase.table('candidates').update(update_data).eq('id', candidate_id).execute()
            
            # Set flag for success message
            st.session_state.just_submitted = True
            
            st.rerun()

# Partner submission history
def show_partner_history():
    partner = st.session_state.user_data
    
    st.markdown("<h1 class='main-header'>Submission History</h1>", unsafe_allow_html=True)
    
    submissions = get_partner_submissions(partner['id'])
    
    if len(submissions) > 0:
        # Join with candidate names
        candidates = get_candidates(partner['id'])
        if len(candidates) > 0:
            candidate_names = dict(zip(candidates['id'], candidates['candidate_name']))
            submissions['Candidate'] = submissions['candidate_id'].map(candidate_names)
        
        display_cols = ['submitted_at', 'Candidate', 'still_employed', 'current_hourly_rate', 'training_hours', 'promoted']
        available_cols = [c for c in display_cols if c in submissions.columns]
        
        display_df = submissions[available_cols].copy()
        display_df.columns = ['Submitted', 'Candidate', 'Still Employed', 'Hourly Rate', 'Training Hrs', 'Promoted']
        display_df = display_df.sort_values('Submitted', ascending=False)
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)
    else:
        st.info("No submissions yet. Go to 'Submit Update' to add your first quarterly update.")

# Main app
def main():
    if not st.session_state.logged_in:
        show_login()
        return
    
    # Sidebar
    with st.sidebar:
        st.markdown("### 🌍 ACH Impact System")
        
        if st.session_state.user_type == "ach":
            st.markdown(f"**ACH Staff**")
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
    
    # Main content
    if st.session_state.user_type == "ach":
        if page == "Dashboard":
            show_ach_dashboard()
        elif page == "Data Management":
            show_ach_data_management()
        elif page == "Reports":
            st.markdown("<h1 class='main-header'>Reports</h1>", unsafe_allow_html=True)
            st.info("Report generation coming in next update. For now, data can be exported from Data Management.")
    else:
        if page == "Dashboard":
            show_partner_dashboard()
        elif page == "Submit Update":
            show_partner_submission()
        elif page == "Submission History":
            show_partner_history()

if __name__ == "__main__":
    main()
