import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from supabase import create_client
import json

# ============ CONFIGURATION ============
SUPABASE_URL = "https://gmjqidqjpzxcpgycawxf.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdtanFpZHFqcHp4Y3BneWNhd3hmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njc3MjYyMDEsImV4cCI6MjA4MzMwMjIwMX0.6jtYlz6yoBQCrh04P0g30JigHyanGYnv7xBz24B5Bm4"

LIVING_WAGE_UK = 12.00

# ============ CANDIDATE SUITABILITY CATEGORIES ============
SUITABILITY_CATEGORIES = [
"Reliability",
"Teamwork",
"Communication",
"Initiative",
"Technical Skills",
"Attitude",
"Punctuality",
"Adaptability"
]

SUITABILITY_RATINGS = ["Excellent", "Good", "Satisfactory", "Needs Improvement"]

# ============ PARTNER TYPES ============
PARTNER_TYPES = [
"Corporate Partner",
"Funder",
"Local Council",
"Training Provider",
"Community Organisation",
"NHS Trust",
"Other"
]

# ============ EMPLOYEE RANGES ============
EMPLOYEE_RANGES = [
"1-10",
"11-50",
"51-100",
"101-250",
"251-500",
"501-1000",
"1000+"
]

# ============ SECTORS (Comprehensive) ============
SECTORS = [
"Accommodation and Food Services",
"Administrative and Support Services",
"Agriculture, Forestry and Fishing",
"Arts, Entertainment and Recreation",
"Automotive",
"Aviation",
"Banking and Finance",
"Charity and Non-Profit",
"Cleaning Services",
"Construction",
"Consulting",
"Creative and Media",
"Defence",
"Education - Early Years",
"Education - Further Education",
"Education - Higher Education",
"Education - Primary",
"Education - Secondary",
"Energy and Utilities",
"Engineering",
"Environmental Services",
"Events and Conferences",
"Facilities Management",
"Fashion and Textiles",
"Financial Services",
"Food and Beverage Manufacturing",
"Government - Central",
"Government - Local",
"Healthcare - Dental",
"Healthcare - GP/Primary Care",
"Healthcare - Hospital/Acute",
"Healthcare - Mental Health",
"Healthcare - Pharmacy",
"Hospitality - Hotels",
"Hospitality - Restaurants",
"Hospitality - Catering",
"Hospitality - Pubs and Bars",
"Housing and Property",
"Human Resources",
"Information Technology",
"Insurance",
"Legal Services",
"Logistics and Distribution",
"Manufacturing - General",
"Manufacturing - Food",
"Manufacturing - Pharmaceutical",
"Marketing and Advertising",
"Mining and Quarrying",
"Performing Arts",
"Pharmaceuticals",
"Professional Services",
"Public Administration",
"Real Estate",
"Recruitment",
"Research and Development",
"Retail - Fashion",
"Retail - Food and Grocery",
"Retail - General",
"Retail - Online",
"Security Services",
"Social Care - Adults",
"Social Care - Children",
"Social Care - Elderly",
"Social Care - Disabilities",
"Sports and Fitness",
"Telecommunications",
"Tourism and Travel",
"Transport - Bus and Coach",
"Transport - Rail",
"Transport - Taxi and Private Hire",
"Transport - Freight",
"Veterinary",
"Warehousing",
"Waste Management",
"Wholesale",
"Other"
]

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

def get_sector_benchmark(sector):
""Map detailed sector to benchmark category""
sector_lower = sector.lower() if sector else ""
if "healthcare" in sector_lower or "hospital" in sector_lower or "nhs" in sector_lower or "dental" in sector_lower or "pharmacy" in sector_lower:
return INDUSTRY_BENCHMARKS["Healthcare"]
elif "social care" in sector_lower:
return INDUSTRY_BENCHMARKS["Social Care"]
elif "hospitality" in sector_lower or "hotel" in sector_lower or "restaurant" in sector_lower or "catering" in sector_lower or "food service" in sector_lower:
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

# ============ ALL COUNTRIES ============
ALL_COUNTRIES = [
"", "Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Antigua and Barbuda", "Argentina", "Armenia", "Australia", "Austria", "Azerbaijan",
"Bahamas", "Bahrain", "Bangladesh", "Barbados", "Belarus", "Belgium", "Belize", "Benin", "Bhutan", "Bolivia", "Bosnia and Herzegovina", "Botswana", "Brazil", "Brunei", "Bulgaria", "Burkina Faso", "Burundi",
"Cambodia", "Cameroon", "Canada", "Cape Verde", "Central African Republic", "Chad", "Chile", "China", "Colombia", "Comoros", "Congo", "Costa Rica", "Croatia", "Cuba", "Cyprus", "Czech Republic",
"Democratic Republic of the Congo", "Denmark", "Djibouti", "Dominica", "Dominican Republic",
"East Timor", "Ecuador", "Egypt", "El Salvador", "Equatorial Guinea", "Eritrea", "Estonia", "Eswatini", "Ethiopia",
"Fiji", "Finland", "France",
"Gabon", "Gambia", "Georgia", "Germany", "Ghana", "Greece", "Grenada", "Guatemala", "Guinea", "Guinea-Bissau", "Guyana",
"Haiti", "Honduras", "Hungary",
"Iceland", "India", "Indonesia", "Iran", "Iraq", "Ireland", "Israel", "Italy", "Ivory Coast",
"Jamaica", "Japan", "Jordan",
"Kazakhstan", "Kenya", "Kiribati", "Kuwait", "Kyrgyzstan",
"Laos", "Latvia", "Lebanon", "Lesotho", "Liberia", "Libya", "Liechtenstein", "Lithuania", "Luxembourg",
"Madagascar", "Malawi", "Malaysia", "Maldives", "Mali", "Malta", "Marshall Islands", "Mauritania", "Mauritius", "Mexico", "Micronesia", "Moldova", "Monaco", "Mongolia", "Montenegro", "Morocco", "Mozambique", "Myanmar",
"Namibia", "Nauru", "Nepal", "Netherlands", "New Zealand", "Nicaragua", "Niger", "Nigeria", "North Korea", "North Macedonia", "Norway",
"Oman",
"Pakistan", "Palau", "Palestine", "Panama", "Papua New Guinea", "Paraguay", "Peru", "Philippines", "Poland", "Portugal",
"Qatar",
"Romania", "Russia", "Rwanda",
"Saint Kitts and Nevis", "Saint Lucia", "Saint Vincent and the Grenadines", "Samoa", "San Marino", "Sao Tome and Principe", "Saudi Arabia", "Senegal", "Serbia", "Seychelles", "Sierra Leone", "Singapore", "Slovakia", "Slovenia", "Solomon Islands", "Somalia", "South Africa", "South Korea", "South Sudan", "Spain", "Sri Lanka", "Sudan", "Suriname", "Sweden", "Switzerland", "Syria",
"Taiwan", "Tajikistan", "Tanzania", "Thailand", "Togo", "Tonga", "Trinidad and Tobago", "Tunisia", "Turkey", "Turkmenistan", "Tuvalu",
"Uganda", "Ukraine", "United Arab Emirates", "United Kingdom", "United States", "Uruguay", "Uzbekistan",
"Vanuatu", "Vatican City", "Venezuela", "Vietnam",
"Yemen",
"Zambia", "Zimbabwe"
]

# ============ 7 CAPABILITY DOMAINS ============
CAPABILITY_DOMAINS = {
"employment": {
"name": "Employment Capability",
"description": "Ability to find, secure and maintain meaningful work",
"factors": {
"personal": [
{"key": "language_proficiency", "question": "How confident are you in describing your work experience in English during an interview?", "type": "scale", "narrative": "Describe a time you used English to manage a work-related task."},
{"key": "digital_literacy", "question": "How often do you use the internet for job searching or CV editing?", "type": "scale", "narrative": "Show us how you would find a job listing online."},
{"key": "self_efficacy", "question": "I believe I can handle unexpected challenges in a work setting.", "type": "scale", "narrative": "Tell me about something difficult you've overcome recently."},
{"key": "career_orientation", "question": "Do you have a specific career goal for the next year?", "type": "yes_no", "narrative": None},
{"key": "work_readiness", "question": "How ready do you feel to attend a UK job interview tomorrow?", "type": "scale", "narrative": "What would you do if you had an interview next week?"}
],
"social": [
{"key": "peer_networks", "question": "How many people do you know who are working in the UK?", "type": "number", "narrative": "Has anyone you know helped you find a job or training?"},
{"key": "mentorship", "question": "Do you know someone with a similar background who is working successfully in the UK?", "type": "yes_no", "narrative": "Tell me about a person who inspired your job path."},
{"key": "trust_institutions", "question": "I trust my job support agency to act in my best interest.", "type": "scale", "narrative": "Have you ever felt discouraged by a job service provider?"}
],
"environmental": [
{"key": "right_to_work", "question": "Do you have the legal right to work in the UK?", "type": "yes_no", "narrative": None},
{"key": "job_market_access", "question": "Are there job opportunities or job fairs you can physically get to?", "type": "yes_no", "narrative": None},
{"key": "credential_recognition", "question": "Do you feel your previous experience is recognised in the UK?", "type": "scale", "narrative": "Tell us if you've had to repeat any past learning or qualifications."},
{"key": "workplace_inclusion", "question": "I feel respected and included at work even if I make mistakes.", "type": "scale", "narrative": "Describe how your first days at a new job felt."}
]
}
},
"housing": {
"name": "Housing Capability",
"description": "Ability to secure and maintain safe, stable housing",
"factors": {
"personal": [
{"key": "housing_rights", "question": "Do you feel confident reading and understanding a UK tenancy agreement?", "type": "scale", "narrative": "What would you do if your landlord raised the rent suddenly?"},
{"key": "budgeting", "question": "Can you estimate how much of your monthly income goes to housing?", "type": "yes_no", "narrative": "Tell us about how you manage your rent and household bills."},
{"key": "navigating_systems", "question": "Have you contacted a housing service by yourself in the past 6 months?", "type": "yes_no", "narrative": None}
],
"social": [
{"key": "housing_advice", "question": "Do you know where to go if you are facing housing difficulties?", "type": "yes_no", "narrative": "Tell us about a time you received housing advice."},
{"key": "community_support", "question": "If you lost your housing tomorrow, would someone help you temporarily?", "type": "yes_no", "narrative": None}
],
"environmental": [
{"key": "affordable_housing", "question": "Is there suitable and affordable housing available in your area?", "type": "scale", "narrative": None},
{"key": "discrimination", "question": "Have you ever been refused housing because of your nationality or status?", "type": "yes_no", "narrative": None},
{"key": "housing_stability", "question": "Do you feel your current home is secure for the next 12 months?", "type": "scale", "narrative": None},
{"key": "housing_suitability", "question": "Is your current housing comfortable and appropriate for your household?", "type": "yes_no", "narrative": None}
]
}
},
"education": {
"name": "Education and Skills Capability",
"description": "Ability to access and benefit from learning opportunities",
"factors": {
"personal": [
{"key": "language_learning", "question": "How confident do you feel understanding lessons taught in English?", "type": "scale", "narrative": "Describe a time you participated in an English-language class."},
{"key": "learning_motivation", "question": "How motivated are you to complete your current learning programme?", "type": "scale", "narrative": "What keeps you going when a course becomes difficult?"},
{"key": "education_bridging", "question": "Have you had your previous education assessed or translated?", "type": "yes_no", "narrative": "Tell us how your prior education is helping/hindering you now."},
{"key": "digital_literacy_edu", "question": "Can you log into and complete tasks on an online learning portal?", "type": "yes_no", "narrative": None}
],
"social": [
{"key": "family_support", "question": "Do your caregiving responsibilities interfere with your learning?", "type": "yes_no", "narrative": "How does your family support or hinder your studies?"},
{"key": "peer_learning", "question": "Do you have someone to help you understand or revise class material?", "type": "yes_no", "narrative": None},
{"key": "tutor_support", "question": "Do you feel your teacher understands your learning needs?", "type": "scale", "narrative": "Describe how your teacher helps you learn."}
],
"environmental": [
{"key": "accessible_learning", "question": "Can you reach your learning centre easily within 45 mins?", "type": "yes_no", "narrative": None},
{"key": "course_recognition", "question": "Does your current course lead to a recognised qualification or next step?", "type": "yes_no", "narrative": None},
{"key": "affordability", "question": "Did cost prevent you from applying for a course in the last year?", "type": "yes_no", "narrative": None},
{"key": "safe_learning", "question": "Do you feel safe and respected in your class environment?", "type": "scale", "narrative": None}
]
}
},
"health": {
"name": "Health and Wellbeing Capability",
"description": "Ability to achieve and maintain physical and mental health",
"factors": {
"personal": [
{"key": "health_literacy", "question": "Do you know how to register with a GP or make a doctor's appointment?", "type": "yes_no", "narrative": None},
{"key": "mental_health_awareness", "question": "Have you received any information about mental health or stress support?", "type": "yes_no", "narrative": "How do you know when you're feeling mentally unwell?"},
{"key": "health_confidence", "question": "How confident are you in describing your health problems to a doctor?", "type": "scale", "narrative": None},
{"key": "self_care", "question": "Do you have regular routines for rest, nutrition, and exercise?", "type": "yes_no", "narrative": "What helps you feel physically and mentally healthy every week?"}
],
"social": [
{"key": "trust_healthcare", "question": "Do you feel respected and listened to by your doctor or nurse?", "type": "scale", "narrative": None},
{"key": "community_wellbeing", "question": "Do people you know talk openly about stress, emotions or illness?", "type": "yes_no", "narrative": None},
{"key": "family_health", "question": "Have family expectations made it harder to take care of your health?", "type": "yes_no", "narrative": None}
],
"environmental": [
{"key": "healthcare_access", "question": "How easy is it to access a GP or dentist when needed?", "type": "scale", "narrative": None},
{"key": "language_services", "question": "Have you received important health information in your language?", "type": "yes_no", "narrative": None},
{"key": "holistic_support", "question": "Have you been supported for multiple needs at the same time?", "type": "yes_no", "narrative": "Have you been supported for multiple needs at the same time (e.g. housing and health)?"},
{"key": "safe_spaces", "question": "Do you feel emotionally safe when discussing personal issues in services?", "type": "scale", "narrative": "Describe how you feel after a health or counselling appointment."}
]
}
},
"belonging": {
"name": "Belonging and Identity Capability",
"description": "Ability to maintain identity and feel part of community",
"factors": {
"personal": [
{"key": "self_confidence", "question": "I feel confident speaking my mind even in unfamiliar spaces.", "type": "scale", "narrative": "Tell me about a time you felt proud of something you did or said."},
{"key": "cultural_identity", "question": "Do you feel able to express your culture or beliefs openly?", "type": "yes_no", "narrative": "Describe a moment you felt 'yourself' in the UK."},
{"key": "psychological_safety", "question": "Do you worry about being judged for how you speak, look, or act?", "type": "yes_no", "narrative": None}
],
"social": [
{"key": "social_recognition", "question": "Do you feel others see you as a person of worth?", "type": "scale", "narrative": "Has someone ever shown you appreciation that mattered deeply?"},
{"key": "role_models", "question": "Can you name someone you relate to who has done well in the UK?", "type": "yes_no", "narrative": "How do their stories influence your thinking about your future?"},
{"key": "relational_stability", "question": "How often do you spend time with someone you trust?", "type": "scale", "narrative": "Describe a friendship that helps you feel at home here."}
],
"environmental": [
{"key": "inclusive_spaces", "question": "Do you feel welcome in community events or spaces like libraries or parks?", "type": "scale", "narrative": None},
{"key": "positive_representation", "question": "Have you seen positive images or stories of people like you in UK media or services?", "type": "yes_no", "narrative": None},
{"key": "cultural_celebration", "question": "Have you joined or led any cultural celebrations here?", "type": "yes_no", "narrative": None},
{"key": "housing_belonging", "question": "Have you moved more than once in the past year?", "type": "yes_no", "narrative": "How does your housing situation affect your sense of home?"}
]
}
},
"participation": {
"name": "Social Participation Capability",
"description": "Ability to participate in community and civic life",
"factors": {
"personal": [
{"key": "participation_confidence", "question": "I feel confident contributing to group discussions or decisions.", "type": "scale", "narrative": "Describe a time you felt your opinion influenced a group or event."},
{"key": "civic_knowledge", "question": "Do you feel you understand how to get involved in local decisions or activities?", "type": "yes_no", "narrative": None},
{"key": "volunteering", "question": "Have you volunteered or helped organise a community event in the last year?", "type": "yes_no", "narrative": "Tell me about a time you led or supported a group activity."}
],
"social": [
{"key": "social_networks", "question": "Do you know someone who helps you connect with social events or groups?", "type": "yes_no", "narrative": None},
{"key": "welcomed", "question": "I feel that people in my area want me to take part in activities with them.", "type": "scale", "narrative": None},
{"key": "mutual_exchange", "question": "Have you been part of a project or group where people worked together equally?", "type": "yes_no", "narrative": None}
],
"environmental": [
{"key": "participatory_platforms", "question": "Do you have opportunities in your local area to join community meetings or projects?", "type": "yes_no", "narrative": None},
{"key": "supportive_structures", "question": "Are community events in your area inclusive of different backgrounds and languages?", "type": "yes_no", "narrative": None},
{"key": "informal_recognition", "question": "Do you feel your informal community contributions are valued?", "type": "yes_no", "narrative": None},
{"key": "accessibility", "question": "Do practical issues like transport or language stop you from joining events?", "type": "yes_no", "narrative": None}
]
}
},
"rights": {
"name": "Rights and Citizenship Capability",
"description": "Ability to understand and exercise legal and civic rights",
"factors": {
"personal": [
{"key": "legal_literacy", "question": "I know where to go if I need legal advice on my immigration status.", "type": "scale", "narrative": "Tell me about a time you had to understand your legal rights in the UK."},
{"key": "system_confidence", "question": "I feel confident completing official forms or speaking with government staff.", "type": "scale", "narrative": None},
{"key": "civic_empowerment", "question": "Do you feel you are a valued participant in UK society?", "type": "scale", "narrative": "What does it mean to you to be part of UK society?"}
],
"social": [
{"key": "trust_institutions", "question": "I trust the local council or service providers to help if I need them.", "type": "scale", "narrative": None},
{"key": "advocacy_support", "question": "Do you know someone who can help you if you need to deal with official processes?", "type": "yes_no", "narrative": None},
{"key": "civic_role_models", "question": "Do you know someone whose path to citizenship or stability inspired you?", "type": "yes_no", "narrative": None}
],
"environmental": [
{"key": "legal_services", "question": "Do you know where to find legal or rights-based help in your local area?", "type": "yes_no", "narrative": None},
{"key": "stable_environment", "question": "Have you ever been confused or set back by unclear rules or sudden changes?", "type": "yes_no", "narrative": None},
{"key": "political_participation", "question": "Have you had the opportunity to participate in political or civic activities?", "type": "yes_no", "narrative": "Have you shared your opinion in a public setting in the UK?"}
]
}
}
}

# ============ EMPLOYER INCLUSION ASSESSMENT (6 dimensions) ============
HOLISTIC_IMPACT_QUESTIONS = {
"economic_security": {
"name": "Economic Security & Stability",
"description": "Ability to meet basic needs and plan financially",
"employer": "We pay at least the real Living Wage and offer stable, predictable hours",
"employee": "I can comfortably cover my basic expenses and plan for the future"
},
"skill_growth": {
"name": "Skill Use & Growth",
"description": "Ability to use existing skills and develop new ones",
"employer": "We provide opportunities for training and skill development relevant to employees' goals",
"employee": "I am able to use my skills and experience, and I have opportunities to learn and grow"
},
"dignity_respect": {
"name": "Workplace Dignity & Respect",
"description": "Freedom from discrimination, fair and respectful treatment",
"employer": "We have clear policies and practices that ensure all employees are treated with dignity and respect",
"employee": "I feel respected and treated fairly at work, regardless of my background"
},
"voice_agency": {
"name": "Voice & Agency",
"description": "Ability to influence decisions and shape one's work",
"employer": "We actively seek and act on employee feedback and involve staff in decisions that affect them",
"employee": "My opinions are valued and I have influence over how I do my work"
},
"belonging_inclusion": {
"name": "Social Belonging & Inclusion",
"description": "Feeling part of the team and workplace community",
"employer": "We foster a culture where all employees feel they belong and can participate fully",
"employee": "I feel like I belong here and have meaningful connections with colleagues"
},
"wellbeing": {
"name": "Wellbeing & Confidence to Plan Ahead",
"description": "Mental health support and ability to envision a future",
"employer": "We support employee wellbeing and help staff see a future with us",
"employee": "I feel positive about my future and can see opportunities ahead for me"
}
}

# Score bands for assessments
SCORE_BANDS = [
{"min": 0, "max": 40, "label": "Foundational", "description": "Basic structures need development"},
{"min": 41, "max": 60, "label": "Developing", "description": "Progress made, gaps remain"},
{"min": 61, "max": 80, "label": "Established", "description": "Good practice, some areas to strengthen"},
{"min": 81, "max": 100, "label": "Leading", "description": "Strong capability across all areas"}
]

def get_score_band(score):
for band in SCORE_BANDS:
if band["min"] <= score <= band["max"]:
return band
return SCORE_BANDS[0]

def get_score_interpretation(score, dimension_name):
"""Get interpretation text for a dimension score"""
band = get_score_band(score)
if band["label"] == "Leading":
return f"Excellent performance in {dimension_name}. You are demonstrating best practice."
elif band["label"] == "Established":
return f"Good performance in {dimension_name}. Minor improvements could strengthen this further."
elif band["label"] == "Developing":
return f"Progress made in {dimension_name}, but there are gaps that need attention."
else:
return f"{dimension_name} needs development. Consider reviewing your practices in this area."

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
.section-header { font-size: 1.3rem; color: #0f1c3f; margin: 2rem 0 1rem 0; padding-bottom: 0.5rem; border-bottom: 2px solid #e2e8f0; }
.metric-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 12px; padding: 20px; color: white; margin: 10px 0; }
.quote-box { background: #f8fafc; border-left: 4px solid #0f1c3f; padding: 16px 20px; margin: 16px 0; font-style: italic; color: #475569; }
.stat-box { background: #f1f5f9; border-radius: 8px; padding: 15px; text-align: center; }
.stat-number { font-size: 2rem; font-weight: 700; color: #0f1c3f; }
.stat-label { font-size: 0.85rem; color: #64748b; }
div[data-testid="stSidebar"] { background: linear-gradient(180deg, #0f1c3f 0%, #1a2d5a 100%); }
div[data-testid="stSidebar"] .stMarkdown { color: white; }
.executive-summary { background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%); border-radius: 16px; padding: 30px; margin-bottom: 30px; border-left: 5px solid #0f1c3f; }
.impact-breakdown { background: white; border-radius: 12px; padding: 20px; margin: 10px 0; border: 1px solid #e2e8f0; }
.dimension-row { display: flex; justify-content: space-between; align-items: center; padding: 12px 0; border-bottom: 1px solid #f1f5f9; }
.dimension-score { font-weight: 600; min-width: 60px; text-align: right; }
.dimension-interpretation { font-size: 0.85rem; color: #64748b; margin-top: 4px; }
</style>
""", unsafe_allow_html=True)

# ============ SESSION STATE ============
if 'user_type' not in st.session_state:
st.session_state.user_type = "ach_staff"
if 'user_id' not in st.session_state:
st.session_state.user_id = 1
if 'user_name' not in st.session_state:
st.session_state.user_name = "ACH Administrator"

# ============ HELPER FUNCTIONS ============
def get_replacement_multiplier(salary):
"""
Replacement cost as percentage of salary.
Based on Oxford Economics, CIPD, and Centric HR research.
"""
if salary < 25000:
return 0.16
elif salary < 35000:
return 0.50
elif salary < 50000:
return 0.75
else:
return 1.00

def calculate_integration_contribution(placements, candidates_data):
"""
Calculate contribution to refugee integration and social cohesion.
Based on: person-months of employment + diversity + progression
"""
total_person_months = 0
countries = set()
progressions = 0

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

# Integration score formula:
# Base: 10 points per person-month of employment
# Bonus: 50 points per country represented (diversity)
# This creates a meaningful metric for social contribution

integration_score = (total_person_months * 10) + (len(countries) * 50)

return {
"total_person_months": round(total_person_months, 1),
"countries_represented": len(countries),
"integration_score": round(integration_score),
"interpretation": get_integration_interpretation(integration_score)
}

def get_integration_interpretation(score):
"""Interpret the integration contribution score"""
if score >= 500:
return "Significant contribution to refugee integration and community diversity"
elif score >= 200:
return "Meaningful contribution to refugee integration"
elif score >= 50:
return "Growing contribution to refugee integration"
else:
return "Early stage contribution to refugee integration"

def calculate_retention_savings(placements, sector, ach_retention_rate):
"""Calculate actual savings based on extra employees retained vs industry average."""
benchmark_data = get_sector_benchmark(sector)
industry_retention = benchmark_data["retention_12m"]
benchmark_source = benchmark_data["source"]

total_placements = len(placements)
if total_placements == 0:
return {
"total_savings": 0,
"ach_retention_percent": 0,
"industry_retention_percent": round(industry_retention * 100, 1),
"retention_uplift_percent": 0,
"extra_retained": 0,
"benchmark_source": benchmark_source,
"methodology": ""
}

retained_placements = [p for p in placements if p.get("status") == "Published" or
(p.get("end_date") and
(datetime.fromisoformat(str(p["end_date"])) - datetime.fromisoformat(str(p["start_date"]))).days >= 365)]

retained_with_costs = []
for p in retained_placements:
salary = p.get("salary") or 0
if salary > 0:
multiplier = get_replacement_multiplier(salary)
replacement_cost = salary * multiplier
retained_with_costs.append({"placement": p, "replacement_cost": replacement_cost})

retained_with_costs.sort(key=lambda x: x["replacement_cost"], reverse=True)

industry_expected_retained = round(total_placements * industry_retention)
actual_retained = len(retained_placements)
extra_retained = max(0, actual_retained - industry_expected_retained)

total_savings = 0
for i in range(extra_retained):
if i < len(retained_with_costs):
total_savings += retained_with_costs[i]["replacement_cost"]

methodology = f"Based on {benchmark_source} ({round(industry_retention * 100)}% industry 12-month retention). "
if extra_retained > 0:
methodology += f"You retained {extra_retained} more employee(s) than industry average, saving an estimated Â£{total_savings:,.0f} in replacement costs."
else:
methodology += f"Replacement costs based on Oxford Economics and CIPD research (16-100% of salary by role level)."

return {
"total_savings": round(total_savings, 2),
"ach_retention_percent": round(ach_retention_rate * 100, 1),
"industry_retention_percent": round(industry_retention * 100, 1),
"retention_uplift_percent": round((ach_retention_rate - industry_retention) * 100, 1),
"extra_retained": extra_retained,
"benchmark_source": benchmark_source,
"methodology": methodology
}

def calculate_diversity_contribution(placements, candidates_data):
country_counts = {}
for p in placements:
candidate_id = p.get("candidate_id")
if candidate_id and candidate_id in candidates_data:
country = candidates_data[candidate_id].get("country_of_origin", "Unknown")
if country and country not in ["United Kingdom", "UK", "England", "Scotland", "Wales", "Northern Ireland", "Unknown", ""]:
country_counts[country] = country_counts.get(country, 0) + 1

sorted_countries = sorted(country_counts.items(), key=lambda x: x[1], reverse=True)
return {
"total_employees": sum(country_counts.values()),
"countries_represented": len(country_counts),
"breakdown": sorted_countries
}

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
"retention_rate": None,
"retention_savings": 0,
"retention_savings_data": {},
"diversity_data": {},
"integration_data": {},
"avg_tenure_months": 0,
"living_wage_percent": 0,
"progression_count": 0,
"training_count": 0,
"employer_quotes": [], # From employer reviews
"candidate_quotes": [], # From candidate reviews
"sector": sector,
"placements_12m_plus": 0,
"retained_12m_plus": 0,
"suitability_details": [] # Detailed suitability ratings
}

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
total_months = 0
for p in active:
if p.get("start_date"):
start = datetime.fromisoformat(str(p["start_date"]))
months = (datetime.now() - start).days / 30
total_months += months
metrics["avg_tenure_months"] = round(total_months / len(active), 1)

# 12-month retention calculation
placements_12m_plus = []
for p in placements:
if p.get("start_date"):
start = datetime.fromisoformat(str(p["start_date"]))
months_since_start = (datetime.now() - start).days / 30
if months_since_start >= 12:
placements_12m_plus.append(p)

metrics["placements_12m_plus"] = len(placements_12m_plus)

if placements_12m_plus:
retained = [p for p in placements_12m_plus if p.get("status") == "Published"]
metrics["retained_12m_plus"] = len(retained)
metrics["retention_rate"] = round((len(retained) / len(placements_12m_plus)) * 100)

ach_retention_decimal = len(retained) / len(placements_12m_plus)
savings_data = calculate_retention_savings(placements_12m_plus, sector, ach_retention_decimal)
metrics["retention_savings"] = savings_data["total_savings"]
metrics["retention_savings_data"] = savings_data

living_wage_count = sum(1 for p in placements if (p.get("hourly_rate") or 0) >= LIVING_WAGE_UK)
if metrics["total_placements"] > 0:
metrics["living_wage_percent"] = round((living_wage_count / metrics["total_placements"]) * 100)

# Calculate integration contribution
metrics["integration_data"] = calculate_integration_contribution(placements, candidates_dict)
metrics["diversity_data"] = calculate_diversity_contribution(placements, candidates_dict)
except:
pass

# Get employer reviews (for employer quotes shown on ACH dashboard)
try:
reviews = supabase.table("milestone_reviews_partner").select("*").eq("partner_id", partner_id).execute()
if reviews.data:
metrics["employer_quotes"] = [r.get("contribution_quote") for r in reviews.data if r.get("contribution_quote")]
metrics["progression_count"] = sum(1 for r in reviews.data if r.get("progression"))
metrics["training_count"] = sum(1 for r in reviews.data if r.get("received_training"))

# Collect detailed suitability ratings
for r in reviews.data:
if r.get("suitability_ratings"):
ratings = json.loads(r["suitability_ratings"]) if isinstance(r["suitability_ratings"], str) else r["suitability_ratings"]
metrics["suitability_details"].append({
"candidate_name": r.get("candidate_name", "Unknown"),
"ratings": ratings,
"notes": r.get("suitability_notes", "")
})
except:
pass

# Get candidate reviews (for candidate quotes shown on employer dashboard)
try:
candidate_reviews = supabase.table("milestone_reviews_candidate").select("*").execute()
if candidate_reviews.data:
# Filter to placements for this partner
placement_ids = [p["id"] for p in placements]
partner_candidate_reviews = [r for r in candidate_reviews.data if r.get("placement_id") in placement_ids]
metrics["candidate_quotes"] = [r.get("feedback_quote") for r in partner_candidate_reviews if r.get("feedback_quote")]
except:
pass

return metrics


def calculate_him_score(partner_id, metrics):
"""
Calculate Holistic Impact Metrics (HIM) Score out of 1000.

Business Impact (400 points):
- Sustained Employment (Retention): 200 points
- Economic Contribution (Diversity): 200 points

Social Impact (600 points):
- 6 dimensions Ã— 100 points each
- Combines employer assessment (50%) + employee voice (50%)
"""

him_score = {
"total": 0,
"business_impact": {
"total": 0,
"retention": {
"score": 0,
"retention_rate_points": 0,
"uplift_points": 0
},
"diversity": {
"score": 0,
"employee_points": 0,
"country_points": 0
}
},
"social_impact": {
"total": 0,
"dimensions": {},
"employer_completed": False,
"employee_responses": 0
}
}

# ============ BUSINESS IMPACT (400 points) ============

retention_rate = metrics.get("retention_rate")

if retention_rate is None:
total_placements = metrics.get("total_placements", 0)
active = metrics.get("active_employees", 0)
if total_placements > 0:
retention_rate = round((active / total_placements) * 100)
else:
retention_rate = 0

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

him_score["business_impact"]["total"] = (
him_score["business_impact"]["retention"]["score"] +
him_score["business_impact"]["diversity"]["score"]
)

# ============ SOCIAL IMPACT (600 points) ============

dimension_names = {
"economic_security": "Economic Security & Stability",
"skill_growth": "Skill Use & Growth",
"dignity_respect": "Workplace Dignity & Respect",
"voice_agency": "Voice & Agency",
"belonging_inclusion": "Social Belonging & Inclusion",
"wellbeing": "Wellbeing & Confidence to Plan Ahead"
}

employer_scores = {}
employee_scores = {}

# Get employer assessment
try:
assessment = supabase.table("inclusion_assessment_org").select("scores").eq("partner_id", partner_id).order("created_at", desc=True).limit(1).execute()

if assessment.data and assessment.data[0].get("scores"):
him_score["social_impact"]["employer_completed"] = True
scores = json.loads(assessment.data[0]["scores"]) if isinstance(assessment.data[0]["scores"], str) else assessment.data[0]["scores"]

for dim_key in dimension_names.keys():
if dim_key in scores:
employer_score = scores[dim_key].get("employer", 0)
if employer_score == 0:
input_score = scores[dim_key].get("input", 0)
conversion_score = scores[dim_key].get("conversion", 0)
employer_score = (input_score + conversion_score) / 2
employer_scores[dim_key] = employer_score
except:
pass

# Get employee scores from candidate milestone reviews
try:
# Get placements for this partner
placements = supabase.table("placements").select("id").eq("partner_id", partner_id).execute()
if placements.data:
placement_ids = [p["id"] for p in placements.data]

reviews = supabase.table("milestone_reviews_candidate").select("scores, placement_id").execute()
if reviews.data:
# Filter to this partner's placements
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

# Calculate combined dimension scores
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


# ============ ACH DASHBOARD ============
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

countries = set()
for c in candidates_data:
country = c.get("country_of_origin")
if country and country not in ["United Kingdom", "UK", "Unknown", ""]:
countries.add(country)
col4.metric("Countries Represented", len(countries))

# Success Stories from Employers
st.markdown('<p class="section-header">Success Stories from Employers</p>', unsafe_allow_html=True)

employer_quotes = [r.get("contribution_quote") for r in reviews_data if r.get("contribution_quote")]
if employer_quotes:
for quote in employer_quotes[:3]:
st.markdown(f"""
<div class="quote-box">"{quote}"</div>
""", unsafe_allow_html=True)
else:
st.info("Success stories will appear here as employers complete milestone reviews")

# Partners by Type
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

# Sector Breakdown
st.markdown('<p class="section-header">Placements by Sector</p>', unsafe_allow_html=True)

sector_counts = {}
for p in partners_data:
sector = p.get("sector", "Other")
partner_placements = [pl for pl in placements_data if pl.get("partner_id") == p.get("id")]
if sector in sector_counts:
sector_counts[sector] += len(partner_placements)
else:
sector_counts[sector] = len(partner_placements)

if sector_counts:
sorted_sectors = sorted(sector_counts.items(), key=lambda x: x[1], reverse=True)[:6]
cols = st.columns(len(sorted_sectors))
for i, (sector, count) in enumerate(sorted_sectors):
display_name = sector.split(" - ")[0] if " - " in sector else sector
cols[i].metric(display_name[:20], count)

# Recent Activity
st.markdown('<p class="section-header">Recent Placements</p>', unsafe_allow_html=True)

if placements_data:
recent = sorted(placements_data, key=lambda x: x.get("created_at", ""), reverse=True)[:5]
for p in recent:
start_date = p.get("start_date", "N/A")
st.write(f"**{p.get('candidate_name', 'Unknown')}** started as {p.get('role', 'N/A')} at {p.get('partner_name', 'Unknown')} ({start_date})")
else:
st.info("No placements yet")

# Candidates by Country
st.markdown('<p class="section-header">Candidates by Country of Origin</p>', unsafe_allow_html=True)

country_counts = {}
for c in candidates_data:
country = c.get("country_of_origin")
if country and country not in ["United Kingdom", "UK", "Unknown", ""]:
country_counts[country] = country_counts.get(country, 0) + 1

if country_counts:
sorted_countries = sorted(country_counts.items(), key=lambda x: x[1], reverse=True)[:8]
cols = st.columns(min(len(sorted_countries), 4))
for i, (country, count) in enumerate(sorted_countries[:4]):
cols[i].metric(country, count)
if len(sorted_countries) > 4:
cols = st.columns(min(len(sorted_countries) - 4, 4))
for i, (country, count) in enumerate(sorted_countries[4:8]):
cols[i].metric(country, count)
else:
st.info("No candidate country data yet")

# Pending Actions
st.markdown('<p class="section-header">Pending Actions</p>', unsafe_allow_html=True)

all_pending = []
for p in partners_data:
pending = get_pending_reviews(p.get("id"))
for review in pending:
review["partner_name"] = p.ge
