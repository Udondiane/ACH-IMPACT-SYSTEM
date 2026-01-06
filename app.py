import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime, date
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
        font-size: 2.5rem;
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
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #0f1c3f;
    }
    .metric-label {
        font-size: 0.875rem;
        color: #64748b;
    }
    .success-metric {
        background: linear-gradient(135deg, #ecfdf5, #d1fae5);
    }
    .success-metric .metric-value {
        color: #059669;
    }
    .highlight-metric {
        background: linear-gradient(135deg, #0f1c3f, #1a2d5a);
    }
    .highlight-metric .metric-value, .highlight-metric .metric-label {
        color: white;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Session state for login
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_type' not in st.session_state:
    st.session_state.user_type = None
if 'user_data' not in st.session_state:
    st.session_state.user_data = None

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

def get_candidate_checkins(candidate_id=None):
    if candidate_id:
        response = supabase.table('candidate_checkins').select('*').eq('candidate_id', candidate_id).execute()
    else:
        response = supabase.table('candidate_checkins').select('*').execute()
    return pd.DataFrame(response.data) if response.data else pd.DataFrame()

def calculate_employer_impact_rating(partner_id):
    candidates = get_candidates(partner_id)
    submissions = get_partner_submissions(partner_id)
    partner = supabase.table('partners').select('*').eq('id', partner_id).execute().data
    
    if not partner:
        return 0
    
    partner = partner[0]
    
    # Living wage score (25%)
    living_wage_score = 100 if partner.get('living_wage_compliant') else 0
    
    # Retention score (25%)
    if len(candidates) > 0:
        active = len(candidates[candidates['status'] == 'Active']) if 'status' in candidates.columns else len(candidates)
        retention_score = (active / len(candidates)) * 100
    else:
        retention_score = 100
    
    # Progression score (20%) - based on submissions
    progression_score = 50  # Default
    if len(submissions) > 0:
        training_avg = submissions['training_hours'].mean() if 'training_hours' in submissions.columns else 0
        promotions = submissions['promoted'].sum() if 'promoted' in submissions.columns else 0
        progression_score = min(100, (training_avg * 2) + (promotions * 20))
    
    # Candidate outcomes score (20%)
    outcomes_score = 50  # Default
    if len(candidates) > 0 and 'current_wellbeing' in candidates.columns and 'baseline_wellbeing' in candidates.columns:
        avg_improvement = (candidates['current_wellbeing'] - candidates['baseline_wellbeing']).mean()
        outcomes_score = min(100, 50 + avg_improvement)
    
    # Inclusive practices score (10%)
    inclusive_score = 50  # Default
    if len(submissions) > 0:
        practices = 0
        if 'flexible_hours' in submissions.columns:
            practices += submissions['flexible_hours'].any() * 25
        if 'language_support' in submissions.columns:
            practices += submissions['language_support'].any() * 25
        if 'mentor_assigned' in submissions.columns:
            practices += submissions['mentor_assigned'].any() * 25
        inclusive_score = min(100, practices + 25)
    
    # Calculate weighted total
    total = (living_wage_score * 0.25 + 
             retention_score * 0.25 + 
             progression_score * 0.20 + 
             outcomes_score * 0.20 + 
             inclusive_score * 0.10)
    
    return round(total)

# Login page
def show_login():
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<h1 style='text-align: center; color: #0f1c3f;'>🌍 ACH Impact System</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #64748b;'>Bridge to Employment Impact Measurement</p>", unsafe_allow_html=True)
        
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
        st.markdown("<p style='text-align: center; font-size: 0.8rem; color: #94a3b8;'>Demo credentials:<br>ACH Staff: ach2025<br>Partner: priya.sharma@birmingham.gov.uk / demo123</p>", unsafe_allow_html=True)

# ACH Dashboard
def show_ach_dashboard():
    st.markdown("<h1 class='main-header'>Impact Dashboard</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-header'>Overview of all Bridge to Employment partnerships</p>", unsafe_allow_html=True)
    
    partners = get_partners()
    candidates = get_candidates()
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        active_candidates = len(candidates[candidates['status'] == 'Active']) if 'status' in candidates.columns else len(candidates)
        st.markdown(f"""
        <div class="metric-card highlight-metric">
            <div class="metric-value">{active_candidates}</div>
            <div class="metric-label">People in Work</div>
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
            <div class="metric-label">Avg Wellbeing Improvement</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{len(partners)}</div>
            <div class="metric-label">Partner Organisations</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Partner rankings
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Partner Organisations")
        if len(partners) > 0:
            partner_data = []
            for _, p in partners.iterrows():
                rating = calculate_employer_impact_rating(p['id'])
                cands = get_candidates(p['id'])
                active = len(cands[cands['status'] == 'Active']) if 'status' in cands.columns else len(cands)
                partner_data.append({
                    'Organisation': p['organisation_name'],
                    'Placements': active,
                    'Living Wage': '✓' if p.get('living_wage_compliant') else '✗',
                    'Impact Rating': rating
                })
            
            df = pd.DataFrame(partner_data).sort_values('Impact Rating', ascending=False)
            st.dataframe(df, use_container_width=True, hide_index=True)
    
    with col2:
        st.subheader("Recent Candidates")
        if len(candidates) > 0:
            display_cols = ['candidate_name', 'role', 'status', 'psychological_safety', 'current_wellbeing']
            available_cols = [c for c in display_cols if c in candidates.columns]
            if available_cols:
                display_df = candidates[available_cols].head(10)
                display_df.columns = [c.replace('_', ' ').title() for c in available_cols]
                st.dataframe(display_df, use_container_width=True, hide_index=True)

# ACH Data Management
def show_ach_data_management():
    st.markdown("<h1 class='main-header'>Data Management</h1>", unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["Partners", "Candidates", "Add New"])
    
    with tab1:
        partners = get_partners()
        if len(partners) > 0:
            st.dataframe(partners, use_container_width=True, hide_index=True)
    
    with tab2:
        candidates = get_candidates()
        if len(candidates) > 0:
            st.dataframe(candidates, use_container_width=True, hide_index=True)
    
    with tab3:
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
                living_wage_rate = st.number_input("Living Wage Rate (£/hr)", min_value=0.0, value=12.60, step=0.10)
                living_wage_compliant = st.checkbox("Living Wage Compliant")
            
            if st.form_submit_button("Add Partner"):
                if org_name and contact_name and contact_email and contact_password:
                    # Generate ID
                    partners = get_partners()
                    new_id = f"P{str(len(partners) + 1).zfill(3)}"
                    
                    # Determine size tier
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
                    st.success(f"Partner added! ID: {new_id}")
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
                    st.warning("No partners available. Add a partner first.")
                    partner_id = None
                
                candidate_name = st.text_input("Candidate Name*")
                role = st.text_input("Role*")
            with col2:
                hourly_rate = st.number_input("Hourly Rate (£)", min_value=0.0, value=12.60, step=0.10)
                start_date = st.date_input("Start Date")
                baseline_wellbeing = st.slider("Baseline Wellbeing Score", 0, 100, 50)
            
            if st.form_submit_button("Add Candidate"):
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
                        "psychological_safety": 50
                    }
                    
                    supabase.table('candidates').insert(data).execute()
                    st.success(f"Candidate added! ID: {new_id}")
                    st.rerun()
                else:
                    st.error("Please fill all required fields")

# Partner Dashboard
def show_partner_dashboard():
    partner = st.session_state.user_data
    
    st.markdown(f"<h1 class='main-header'>{partner['organisation_name']}</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-header'>Your Bridge to Employment Partnership Dashboard</p>", unsafe_allow_html=True)
    
    candidates = get_candidates(partner['id'])
    impact_rating = calculate_employer_impact_rating(partner['id'])
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card highlight-metric">
            <div class="metric-value">{impact_rating}</div>
            <div class="metric-label">Impact Rating</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        active = len(candidates[candidates['status'] == 'Active']) if 'status' in candidates.columns and len(candidates) > 0 else 0
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{active}</div>
            <div class="metric-label">Active Placements</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        if len(candidates) > 0 and 'current_wellbeing' in candidates.columns and 'baseline_wellbeing' in candidates.columns:
            avg_improvement = round((candidates['current_wellbeing'] - candidates['baseline_wellbeing']).mean())
        else:
            avg_improvement = 0
        st.markdown(f"""
        <div class="metric-card success-metric">
            <div class="metric-value">+{avg_improvement}</div>
            <div class="metric-label">Avg Wellbeing Gain</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        wage_status = "✓ Compliant" if partner.get('living_wage_compliant') else "✗ Below"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">£{partner.get('living_wage_rate', 0)}</div>
            <div class="metric-label">Living Wage {wage_status}</div>
        </div>
        """, unsafe_allow_html=True)
    
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
                'Wellbeing Change': f"+{improvement}" if improvement >= 0 else str(improvement),
                'Psychological Safety': f"{c.get('psychological_safety', 0)}%"
            })
        st.dataframe(pd.DataFrame(display_data), use_container_width=True, hide_index=True)
    else:
        st.info("No candidates placed yet")

# Partner Data Submission
def show_partner_submission():
    partner = st.session_state.user_data
    
    st.markdown("<h1 class='main-header'>Submit Quarterly Update</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-header'>Please complete this form for each candidate</p>", unsafe_allow_html=True)
    
    candidates = get_candidates(partner['id'])
    
    if len(candidates) == 0:
        st.warning("No candidates to update")
        return
    
    with st.form("partner_submission"):
        candidate_options = dict(zip(candidates['candidate_name'], candidates['id']))
        selected_candidate = st.selectbox("Select Candidate*", options=list(candidate_options.keys()))
        candidate_id = candidate_options[selected_candidate]
        
        st.markdown("---")
        st.subheader("Employment Status")
        
        col1, col2 = st.columns(2)
        with col1:
            still_employed = st.radio("Still employed?", ["Yes", "No"], horizontal=True)
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
        st.subheader("Compensation & Development")
        
        col1, col2 = st.columns(2)
        with col1:
            current_rate = st.number_input("Current hourly rate (£)", min_value=0.0, value=12.60, step=0.10)
            pay_increase = st.checkbox("Pay increase since last update?")
        with col2:
            training_hours = st.number_input("Training hours provided", min_value=0, value=0)
            training_type = st.text_input("Type of training (if any)")
        
        col1, col2 = st.columns(2)
        with col1:
            promoted = st.checkbox("Promoted or given new responsibilities?")
        with col2:
            if promoted:
                promotion_details = st.text_input("Promotion details")
            else:
                promotion_details = None
        
        st.markdown("---")
        st.subheader("Support Provided")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            flexible_hours = st.checkbox("Flexible hours")
        with col2:
            language_support = st.checkbox("Language support")
        with col3:
            mentor_assigned = st.checkbox("Mentor/buddy assigned")
        
        other_adjustments = st.text_area("Other adjustments or support provided")
        concerns = st.text_area("Any concerns about this candidate?")
        
        if st.form_submit_button("Submit Update", use_container_width=True):
            data = {
                "partner_id": partner['id'],
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
            
            supabase.table('partner_submissions').insert(data).execute()
            
            # Update candidate status if no longer employed
            if still_employed == "No":
                supabase.table('candidates').update({"status": "Left"}).eq('id', candidate_id).execute()
            
            st.success("Update submitted successfully!")
            st.balloons()

# Main app
def main():
    if not st.session_state.logged_in:
        show_login()
        return
    
    # Sidebar
    with st.sidebar:
        st.markdown(f"### 🌍 ACH Impact System")
        st.markdown(f"Logged in as: **{st.session_state.user_data.get('name', st.session_state.user_data.get('contact_name', 'User'))}**")
        
        if st.session_state.user_type == "ach":
            page = st.radio("Navigate", ["Dashboard", "Data Management", "Reports"])
        else:
            page = st.radio("Navigate", ["Dashboard", "Submit Update", "View History"])
        
        st.markdown("---")
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.user_type = None
            st.session_state.user_data = None
            st.rerun()
    
    # Main content
    if st.session_state.user_type == "ach":
        if page == "Dashboard":
            show_ach_dashboard()
        elif page == "Data Management":
            show_ach_data_management()
        elif page == "Reports":
            st.markdown("<h1 class='main-header'>Reports</h1>", unsafe_allow_html=True)
            st.info("Report generation coming soon. For now, export data from Data Management.")
    else:
        if page == "Dashboard":
            show_partner_dashboard()
        elif page == "Submit Update":
            show_partner_submission()
        elif page == "View History":
            st.markdown("<h1 class='main-header'>Submission History</h1>", unsafe_allow_html=True)
            submissions = get_partner_submissions(st.session_state.user_data['id'])
            if len(submissions) > 0:
                st.dataframe(submissions, use_container_width=True, hide_index=True)
            else:
                st.info("No submissions yet")

if __name__ == "__main__":
    main()
