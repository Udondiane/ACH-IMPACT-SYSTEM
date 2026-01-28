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
    """Map detailed sector to benchmark category"""
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
    """Replacement cost as percentage of salary."""
    if salary < 25000:
        return 0.16
    elif salary < 35000:
        return 0.50
    elif salary < 50000:
        return 0.75
    else:
        return 1.00

def calculate_integration_contribution(placements, candidates_data):
    """Calculate contribution to refugee integration and social cohesion."""
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
        methodology += f"You retained {extra_retained} more employee(s) than industry average, saving an estimated £{total_savings:,.0f} in replacement costs."
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
    """Calculate diversity contribution from placements."""
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
    """Get partner sector from database."""
    try:
        result = supabase.table("impact_partners").select("sector").eq("id", partner_id).execute()
        if result.data:
            return result.data[0].get("sector", "Other")
    except:
        pass
    return "Other"

def calculate_impact_metrics(partner_id):
    """Calculate all impact metrics for a partner."""
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
        "employer_quotes": [],
        "candidate_quotes": [],
        "sector": sector,
        "placements_12m_plus": 0,
        "retained_12m_plus": 0,
        "suitability_details": []
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
    """Calculate Holistic Impact Metrics (HIM) Score out of 1000."""
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
    """Get pending milestone reviews for a partner."""
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
    
    # Success Stories from Employers (shown on ACH dashboard)
    st.markdown('<p class="section-header">Success Stories from Employers</p>', unsafe_allow_html=True)
    
    employer_quotes = [r.get("contribution_quote") for r in reviews_data if r.get("contribution_quote")]
    if employer_quotes:
        for quote in employer_quotes[:3]:
            st.markdown(f"""
            <div class="quote-box">"{quote}"</div>
            """, unsafe_allow_html=True)
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
    
    st.markdown('<p class="section-header">Recent Placements</p>', unsafe_allow_html=True)
    
    if placements_data:
        recent = sorted(placements_data, key=lambda x: x.get("created_at", ""), reverse=True)[:5]
        for p in recent:
            start_date = p.get("start_date", "N/A")
            st.write(f"**{p.get('candidate_name', 'Unknown')}** started as {p.get('role', 'N/A')} at {p.get('partner_name', 'Unknown')} ({start_date})")
    else:
        st.info("No placements yet")
    
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


# ============ ACH MANAGE PARTNERS ============
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
                        
                        st.divider()
                        
                        col_edit, col_delete = st.columns(2)
                        with col_edit:
                            if st.button("✏️ Edit Partner", key=f"edit_btn_{p['id']}", use_container_width=True):
                                st.session_state.edit_partner_id = p['id']
                                st.rerun()
                        
                        with col_delete:
                            if st.button("🗑️ Delete Partner", key=f"delete_partner_{p['id']}", use_container_width=True, type="secondary"):
                                st.session_state[f"confirm_delete_partner_{p['id']}"] = True
                        
                        if st.session_state.get(f"confirm_delete_partner_{p['id']}"):
                            st.warning(f"Are you sure you want to delete {p['name']}? This will also delete all associated placements and reviews.")
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
            sector = st.selectbox("Sector *", [""] + SECTORS, help="Start typing to search sectors")
            employee_count = st.selectbox("Number of Employees *", [""] + EMPLOYEE_RANGES)
            package_tier = st.selectbox("Package Tier *", ["Standard", "Impact Partner"], help="Impact Partners get full dashboard access")
            
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
                        data = {
                            "name": name,
                            "partner_type": partner_type,
                            "sector": sector,
                            "employee_count": employee_count,
                            "package_tier": package_tier,
                            "contact_name": contact_name,
                            "contact_email": contact_email,
                            "contact_phone": contact_phone,
                            "created_at": datetime.now().isoformat()
                        }
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
                
                preselected_name = None
                if "edit_partner_id" in st.session_state:
                    for p in partners.data:
                        if p["id"] == st.session_state.edit_partner_id:
                            preselected_name = p["name"]
                            break
                
                partner_names = [""] + list(partner_options.keys())
                default_index = 0
                if preselected_name and preselected_name in partner_names:
                    default_index = partner_names.index(preselected_name)
                
                selected_name = st.selectbox("Select Partner to Edit", partner_names, index=default_index, key="edit_partner_selector")
                
                if not selected_name:
                    st.info("Select a partner to edit their details")
                else:
                    partner = partner_options[selected_name]
                    
                    if "edit_partner_id" in st.session_state:
                        del st.session_state.edit_partner_id
                    
                    st.divider()
                    st.subheader(f"Editing: {partner['name']}")
                    
                    with st.form("edit_partner_form"):
                        st.markdown("**Organisation Details**")
                        
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
                        st.markdown("**Primary Contact**")
                        
                        edit_contact_name = st.text_input("Contact Name *", value=partner.get("contact_name", ""))
                        edit_contact_email = st.text_input("Contact Email *", value=partner.get("contact_email", ""))
                        edit_contact_phone = st.text_input("Phone (optional)", value=partner.get("contact_phone", ""))
                        
                        st.divider()
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            save_clicked = st.form_submit_button("💾 Save Changes", use_container_width=True, type="primary")
                        with col2:
                            cancel_clicked = st.form_submit_button("Cancel", use_container_width=True)
                        
                        if cancel_clicked:
                            st.rerun()
                        
                        if save_clicked:
                            if not edit_name or not edit_partner_type or not edit_sector or not edit_contact_name or not edit_contact_email:
                                st.error("Please fill in all required fields")
                            else:
                                try:
                                    update_data = {
                                        "name": edit_name,
                                        "partner_type": edit_partner_type,
                                        "sector": edit_sector,
                                        "employee_count": edit_employee_count,
                                        "package_tier": edit_package_tier,
                                        "contact_name": edit_contact_name,
                                        "contact_email": edit_contact_email,
                                        "contact_phone": edit_contact_phone,
                                        "updated_at": datetime.now().isoformat()
                                    }
                                    supabase.table("impact_partners").update(update_data).eq("id", partner["id"]).execute()
                                    st.success(f"{edit_name} updated successfully!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error updating partner: {e}")
        except Exception as e:
            st.error(f"Error: {e}")


# ============ ACH MANAGE CANDIDATES ============
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
                            new_status = st.selectbox(
                                "Change Status",
                                ["Available", "Placed", "Inactive"],
                                index=["Available", "Placed", "Inactive"].index(c.get('status', 'Available')) if c.get('status') in ["Available", "Placed", "Inactive"] else 0,
                                key=f"status_{c['id']}"
                            )
                            
                            if new_status != c.get('status'):
                                if st.button("Update Status", key=f"update_status_{c['id']}"):
                                    try:
                                        supabase.table("candidates").update({"status": new_status}).eq("id", c["id"]).execute()
                                        st.success(f"Status updated to {new_status}")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error: {e}")
                        
                        st.divider()
                        
                        if st.button("🗑️ Delete Candidate", key=f"delete_candidate_{c['id']}", type="secondary"):
                            st.session_state[f"confirm_delete_{c['id']}"] = True
                        
                        if st.session_state.get(f"confirm_delete_{c['id']}"):
                            st.warning(f"Are you sure you want to delete {c['name']}? This will also delete any associated placements.")
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
        except Exception as e:
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


# ============ ACH CAPABILITY ASSESSMENT ============
def ach_capability_assessment():
    st.markdown('<p class="main-header">Candidate Holistic Impact Assessment</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Assess candidates across 7 capability domains</p>', unsafe_allow_html=True)
    
    try:
        candidates = supabase.table("candidates").select("*").execute()
        if not candidates.data:
            st.info("No candidates available")
            return
        
        candidate_options = {c["name"]: c for c in candidates.data}
        selected = st.selectbox("Select Candidate", [""] + list(candidate_options.keys()))
        
        if not selected:
            return
        
        candidate = candidate_options[selected]
        
        assessment_stage = st.selectbox("Assessment Stage", ["Baseline", "3-Month", "6-Month", "12-Month", "Exit"])
        
        domain_names = {k: v["name"] for k, v in CAPABILITY_DOMAINS.items()}
        selected_domain = st.selectbox("Select Domain", [""] + list(domain_names.values()))
        
        if not selected_domain:
            st.info("Select a domain to begin assessment")
            return
        
        domain_key = None
        for k, v in CAPABILITY_DOMAINS.items():
            if v["name"] == selected_domain:
                domain_key = k
                break
        
        if not domain_key:
            return
        
        domain = CAPABILITY_DOMAINS[domain_key]
        
        st.markdown(f"### {domain['name']}")
        st.write(domain['description'])
        
        with st.form(f"assessment_{domain_key}"):
            responses = {}
            
            for factor_type in ["personal", "social", "environmental"]:
                st.markdown(f"**{factor_type.title()} Factors**")
                
                factors = domain["factors"].get(factor_type, [])
                for factor in factors:
                    key = factor["key"]
                    question = factor["question"]
                    q_type = factor["type"]
                    narrative = factor.get("narrative")
                    
                    if q_type == "scale":
                        responses[key] = st.slider(question, 1, 5, 3, key=f"{domain_key}_{key}")
                    elif q_type == "yes_no":
                        responses[key] = st.radio(question, ["Yes", "No"], horizontal=True, key=f"{domain_key}_{key}")
                    elif q_type == "number":
                        responses[key] = st.number_input(question, min_value=0, max_value=100, value=0, key=f"{domain_key}_{key}")
                    
                    if narrative:
                        responses[f"{key}_narrative"] = st.text_area(f"Narrative: {narrative}", key=f"{domain_key}_{key}_narr", height=80)
                
                st.divider()
            
            submitted = st.form_submit_button("Save Assessment", use_container_width=True)
            
            if submitted:
                try:
                    data = {
                        "candidate_id": candidate["id"],
                        "candidate_name": candidate["name"],
                        "domain": domain_key,
                        "stage": assessment_stage,
                        "responses": json.dumps(responses),
                        "created_at": datetime.now().isoformat()
                    }
                    supabase.table("capability_assessments").insert(data).execute()
                    st.success("Assessment saved successfully")
                except Exception as e:
                    st.error(f"Error: {e}")
    
    except Exception as e:
        st.error(f"Error: {e}")


# ============ ACH CANDIDATE SUPPORT ============
def ach_candidate_support():
    st.markdown('<p class="main-header">Candidate Support</p>', unsafe_allow_html=True)
    st.info("Candidate milestone check-in interface - coming soon")


# ============ PARTNER DASHBOARD (ORIGINAL STYLE) ============
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
        # HIM Score Card
        st.markdown("""
        <style>
            .him-score-card { background: linear-gradient(135deg, #0f1c3f 0%, #1a2d5a 100%); border-radius: 20px; padding: 40px; text-align: center; margin-bottom: 30px; color: white; }
            .him-score-value { font-size: 4rem; font-weight: 700; margin-bottom: 10px; }
            .him-progress-bar { background: rgba(255,255,255,0.2); border-radius: 10px; height: 12px; margin-top: 20px; overflow: hidden; }
            .him-progress-fill { background: linear-gradient(90deg, #22c55e 0%, #16a34a 100%); height: 100%; border-radius: 10px; }
            .impact-section { background: white; border-radius: 16px; padding: 25px; margin-bottom: 20px; border: 1px solid #e2e8f0; }
            .impact-section-title { font-size: 1.1rem; font-weight: 600; color: #0f1c3f; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 2px solid #e2e8f0; }
            .impact-row { display: flex; justify-content: space-between; align-items: center; padding: 12px 0; border-bottom: 1px solid #f1f5f9; }
            .impact-row:last-child { border-bottom: none; }
            .impact-metric-name { color: #475569; font-size: 0.95rem; }
            .impact-metric-value { font-weight: 600; color: #0f1c3f; }
            .impact-metric-bar { background: #e2e8f0; border-radius: 4px; height: 8px; width: 100px; margin-left: 15px; overflow: hidden; }
            .impact-metric-fill { background: linear-gradient(90deg, #0f1c3f 0%, #1a2d5a 100%); height: 100%; border-radius: 4px; }
            .quote-card { background: #f8fafc; border-left: 4px solid #0f1c3f; padding: 20px 25px; margin: 15px 0; font-style: italic; color: #475569; border-radius: 0 12px 12px 0; }
            .action-item { background: #fffbeb; border-radius: 10px; padding: 15px 20px; margin: 10px 0; border-left: 4px solid #f59e0b; }
        </style>
        """, unsafe_allow_html=True)
        
        him_total = him_score["total"]
        him_percentage = (him_total / 1000) * 100
        
        if him_total > 0:
            st.markdown(f"""
            <div class="him-score-card">
                <div style="font-size: 1rem; opacity: 0.9; margin-bottom: 10px; letter-spacing: 2px; text-transform: uppercase;">Holistic Impact Score</div>
                <div class="him-score-value">{him_total}<span style="font-size: 1.5rem; color: #94a3b8;"> / 1000</span></div>
                <div class="him-progress-bar">
                    <div class="him-progress-fill" style="width: {him_percentage}%;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="him-score-card">
                <div style="font-size: 1rem; opacity: 0.9; margin-bottom: 10px; letter-spacing: 2px; text-transform: uppercase;">Holistic Impact Score</div>
                <div style="font-size: 1rem; color: #94a3b8; padding: 20px 0;">Your Holistic Impact Score will appear as you record placements and complete the Holistic Impact Assessment</div>
            </div>
            """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        retention_rate = metrics.get("retention_rate")
        has_12m_data = retention_rate is not None
        if retention_rate is None:
            retention_rate = 0
        
        diversity = metrics.get("diversity_data", {})
        employees = diversity.get("total_employees", 0)
        countries = diversity.get("countries_represented", 0)
        
        with col1:
            savings = metrics.get("retention_savings", 0)
            savings_text = f"£{savings:,.0f}" if savings > 0 else "No data yet"
            retention_text = f"{retention_rate}%" if has_12m_data else "No data yet"
            diversity_text = f"{employees} employees, {countries} countries" if employees > 0 else "No data yet"
            
            st.markdown('<div class="impact-section">', unsafe_allow_html=True)
            st.markdown('<div class="impact-section-title">Business Impact Generated</div>', unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class="impact-row">
                <span class="impact-metric-name">12-Month Retention</span>
                <span class="impact-metric-value">{retention_text}</span>
            </div>
            <div class="impact-row">
                <span class="impact-metric-name">Estimated Retention Savings</span>
                <span class="impact-metric-value">{savings_text}</span>
            </div>
            <div class="impact-row">
                <span class="impact-metric-name">Diversity Contribution</span>
                <span class="impact-metric-value">{diversity_text}</span>
            </div>
            """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            social_dimensions = him_score['social_impact']['dimensions']
            employer_completed = him_score['social_impact']['employer_completed']
            employee_responses = him_score['social_impact']['employee_responses']
            
            st.markdown('<div class="impact-section">', unsafe_allow_html=True)
            st.markdown('<div class="impact-section-title">Social Impact Created</div>', unsafe_allow_html=True)
            
            if employer_completed or employee_responses > 0:
                for dim_name, dim_score in social_dimensions.items():
                    st.markdown(f"""
                    <div class="impact-row">
                        <span class="impact-metric-name">{dim_name}</span>
                        <div style="display: flex; align-items: center;">
                            <span class="impact-metric-value">{dim_score}%</span>
                            <div class="impact-metric-bar"><div class="impact-metric-fill" style="width: {dim_score}%;"></div></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                sources = []
                if employer_completed:
                    sources.append("Employer assessment")
                if employee_responses > 0:
                    sources.append(f"{employee_responses} employee response(s)")
                st.markdown(f'<div style="padding-top: 10px; font-size: 0.8rem; color: #64748b;">Based on: {" + ".join(sources)}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div style="padding: 20px; text-align: center; color: #64748b;">Complete the Holistic Impact Assessment to see your Social Impact scores</div>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Retention Breakdown
        st.markdown('<p class="section-header">Estimated Retention Savings Breakdown</p>', unsafe_allow_html=True)
        
        savings_data = metrics.get("retention_savings_data", {})
        
        if has_12m_data and savings_data:
            st.caption(f"Based on {metrics.get('placements_12m_plus', 0)} placements that have reached 12 months")
            
            ach_rate = savings_data.get('ach_retention_percent', 0)
            industry_rate = savings_data.get('industry_retention_percent', 0)
            difference = savings_data.get('retention_uplift_percent', 0)
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Your Retention", f"{ach_rate}%")
            col2.metric("Industry Average", f"{industry_rate}%")
            col3.metric("Your Uplift", f"+{difference}%")
            col4.metric("Estimated Savings", f"£{savings_data.get('total_savings', 0):,.0f}")
            
            st.caption(savings_data.get('methodology', ''))
        else:
            st.info("Retention savings will be calculated once placements reach 12 months")
        
        # Success Stories from Candidates (shown on employer dashboard)
        st.markdown('<p class="section-header">What Your Employees Say</p>', unsafe_allow_html=True)
        
        candidate_quotes = metrics.get("candidate_quotes", [])
        if candidate_quotes:
            for quote in candidate_quotes[:3]:
                st.markdown(f'<div class="quote-card">"{quote}"</div>', unsafe_allow_html=True)
        else:
            st.info("Employee feedback will appear here as candidates complete their milestone reviews")
        
        # Pending Reviews
        pending = get_pending_reviews(partner_id)
        if pending:
            st.markdown('<p class="section-header">Action Required</p>', unsafe_allow_html=True)
            for p in pending:
                st.markdown(f'<div class="action-item"><strong>{p["candidate_name"]}</strong> — {p["milestone"]} due {p["due_date"]}</div>', unsafe_allow_html=True)
    
    else:
        # Standard tier - locked dashboard
        st.markdown("""
        <style>
            .locked-metric { background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%); border-radius: 12px; padding: 20px; text-align: center; margin: 10px 0; }
            .locked-value { font-size: 2rem; font-weight: 700; color: #94a3b8; letter-spacing: 3px; }
            .locked-label { font-size: 0.9rem; color: #64748b; margin-top: 5px; }
            .upgrade-box { background: linear-gradient(135deg, #0f1c3f 0%, #1a2d5a 100%); border-radius: 12px; padding: 30px; color: white; text-align: center; margin: 30px 0; }
        </style>
        """, unsafe_allow_html=True)
        
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
        
        st.markdown("""
        <div class="upgrade-box">
            <h3>Unlock Your Full Impact Dashboard</h3>
            <p>Opt in to our <strong>Workforce Integration Package</strong> to unlock:</p>
            <p>• Full retention savings calculations<br>
            • Diversity contribution insights<br>
            • Social impact reporting<br>
            • Retention guarantee<br>
            • Corporate training</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Learn More About Impact Partnership", use_container_width=True):
            st.info("Contact ACH to become an Impact Partner and unlock your full dashboard.")
        
        pending = get_pending_reviews(partner_id)
        if pending:
            st.markdown('<p class="section-header">Action Required</p>', unsafe_allow_html=True)
            for p in pending:
                st.warning(f"**{p['candidate_name']}** - {p['milestone']} due {p['due_date']}")


# ============ PARTNER HOLISTIC IMPACT ASSESSMENT ============
def partner_inclusion_assessment():
    st.markdown('<p class="main-header">Holistic Impact Assessment</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Rate your organisation across six capability domains</p>', unsafe_allow_html=True)
    
    partner_id = st.session_state.get("user_id", 1)
    
    st.info("This assessment measures your organisation's enablement of employee capabilities. Employee responses from milestone reviews will be combined with your assessment to create a complete picture.")
    
    with st.form("holistic_impact_assessment"):
        scores = {}
        
        for dim_key, dim_data in HOLISTIC_IMPACT_QUESTIONS.items():
            st.markdown(f"### {dim_data['name']}")
            st.caption(dim_data['description'])
            
            scores[dim_key] = {}
            
            scores[dim_key]["employer"] = st.slider(
                dim_data["employer"], 
                1, 5, 3, 
                key=f"{dim_key}_employer",
                help="1 = Strongly Disagree, 5 = Strongly Agree"
            )
            
            st.divider()
        
        submitted = st.form_submit_button("Submit Assessment", use_container_width=True)
        
        if submitted:
            try:
                data = {
                    "partner_id": partner_id,
                    "scores": json.dumps(scores),
                    "created_at": datetime.now().isoformat()
                }
                supabase.table("inclusion_assessment_org").insert(data).execute()
                st.success("Assessment submitted successfully")
            except Exception as e:
                st.error(f"Error: {e}")


# ============ PARTNER CANDIDATES ============
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
                            
                            feedback = {
                                "partner_id": partner_id,
                                "candidate_id": cand_data["id"],
                                "candidate_name": candidate,
                                "role": role,
                                "interview_date": interview_date.isoformat(),
                                "hired": hired == "Yes",
                                "standout_reason": feedback_text if hired == "Yes" else None,
                                "rejection_reason": feedback_text if hired == "No" else None,
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
                                    "status": "Published",
                                    "created_at": datetime.now().isoformat()
                                }
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
                            st.caption("Rate the candidate across key workplace competencies")
                            
                            suitability_ratings = {}
                            for category in SUITABILITY_CATEGORIES:
                                suitability_ratings[category] = st.selectbox(
                                    category,
                                    SUITABILITY_RATINGS,
                                    key=f"suit_{review['placement_id']}_{category}"
                                )
                            
                            suitability_notes = st.text_area(
                                "Additional notes on performance",
                                placeholder="Any specific observations or areas of strength/improvement...",
                                key=f"suit_notes_{review['placement_id']}"
                            )
                            
                            st.divider()
                            
                            received_training = st.radio("Received training?", ["Yes", "No"], horizontal=True, key=f"training_{review['placement_id']}")
                            
                            training_details = None
                            if received_training == "Yes":
                                training_details = st.text_area(
                                    "Training details",
                                    placeholder="What training was provided? (e.g., Health & Safety, Customer Service, Technical skills...)",
                                    key=f"training_details_{review['placement_id']}"
                                )
                            
                            progression = st.radio("Any progression?", ["Yes", "No"], horizontal=True, key=f"progression_{review['placement_id']}")
                            
                            progression_details = None
                            if progression == "Yes":
                                progression_details = st.text_area(
                                    "Progression details",
                                    placeholder="What progression occurred? (e.g., promotion, pay rise, new responsibilities...)",
                                    key=f"progression_details_{review['placement_id']}"
                                )
                            
                            st.divider()
                            
                            contribution_quote = st.text_area(
                                "Describe their contribution",
                                placeholder="Share a success story or highlight their impact...",
                                key=f"contribution_{review['placement_id']}"
                            )
                        else:
                            leaving_reason = st.selectbox(
                                "Reason",
                                ["Resigned", "Dismissed", "Redundancy", "Contract ended", "Other"],
                                key=f"leaving_{review['placement_id']}"
                            )
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
                                data = {
                                    "placement_id": review["placement_id"],
                                    "partner_id": partner_id,
                                    "candidate_name": review["candidate_name"],
                                    "milestone_month": review["milestone_month"],
                                    "still_employed": still_employed == "Yes",
                                    "suitability_ratings": json.dumps(suitability_ratings) if suitability_ratings else None,
                                    "suitability_notes": suitability_notes,
                                    "received_training": received_training == "Yes" if still_employed == "Yes" else None,
                                    "training_details": training_details,
                                    "progression": progression == "Yes" if still_employed == "Yes" else None,
                                    "progression_details": progression_details,
                                    "contribution_quote": contribution_quote if still_employed == "Yes" else None,
                                    "leaving_reason": leaving_reason if still_employed == "No" else None,
                                    "created_at": datetime.now().isoformat()
                                }
                                supabase.table("milestone_reviews_partner").insert(data).execute()
                                
                                placement_update = {
                                    "last_milestone_check": datetime.now().date().isoformat(),
                                    "last_milestone_month": review["milestone_month"]
                                }
                                
                                if still_employed == "No":
                                    placement_update["status"] = "Left"
                                    placement_update["end_date"] = datetime.now().date().isoformat()
                                
                                supabase.table("placements").update(placement_update).eq("id", review["placement_id"]).execute()
                                
                                st.success("Review submitted")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")
    
    with tab3:
        st.markdown('<p class="sub-header">View and edit current employee details</p>', unsafe_allow_html=True)
        
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
                                tenure_days = (datetime.now() - start).days
                                tenure_months = round(tenure_days / 30, 1)
                                st.write(f"**Tenure:** {tenure_months} months")
                        
                        try:
                            latest_review = supabase.table("milestone_reviews_partner").select("suitability_ratings, suitability_notes").eq("placement_id", placement["id"]).order("created_at", desc=True).limit(1).execute()
                            if latest_review.data and latest_review.data[0].get("suitability_ratings"):
                                st.divider()
                                st.markdown("**Latest Suitability Assessment**")
                                ratings = json.loads(latest_review.data[0]["suitability_ratings"]) if isinstance(latest_review.data[0]["suitability_ratings"], str) else latest_review.data[0]["suitability_ratings"]
                                
                                cols = st.columns(4)
                                for i, (category, rating) in enumerate(ratings.items()):
                                    col_idx = i % 4
                                    cols[col_idx].write(f"**{category}:** {rating}")
                                
                                if latest_review.data[0].get("suitability_notes"):
                                    st.caption(f"Notes: {latest_review.data[0]['suitability_notes']}")
                        except:
                            pass
                        
                        st.divider()
                        
                        new_start_date = st.date_input(
                            "Edit Start Date", 
                            value=current_start, 
                            format="DD/MM/YYYY",
                            key=f"start_date_{placement['id']}"
                        )
                        
                        if st.button("Update Start Date", key=f"update_{placement['id']}"):
                            try:
                                supabase.table("placements").update({
                                    "start_date": new_start_date.isoformat()
                                }).eq("id", placement["id"]).execute()
                                st.success("Start date updated")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")
        except Exception as e:
            st.error(f"Error: {e}")


# ============ PARTNER REPORTS (WITH EXECUTIVE SUMMARY) ============
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
    
    # ============ EXECUTIVE SUMMARY ============
    st.markdown("### Executive Summary")
    
    total_placements = metrics.get("total_placements", 0)
    integration_data = metrics.get("integration_data", {})
    person_months = integration_data.get("total_person_months", 0)
    countries = metrics.get("diversity_data", {}).get("countries_represented", 0)
    retention_rate = metrics.get("retention_rate", 0) or 0
    retention_savings = metrics.get("retention_savings", 0)
    integration_interpretation = integration_data.get("interpretation", "")
    
    st.markdown(f"""
Through your partnership with ACH, your organisation has created **{total_placements} jobs** for members of the 
refugee and migrant community, representing **{round(person_months)} person-months** of sustained employment 
across **{countries} countries** of origin. This represents a **{integration_interpretation.lower()}**.

**Your Holistic Impact Metric Score: {him_score['total']} / 1000**

You have scored as follows across the key impact areas:
    """)
    
    # Business Value breakdown
    st.markdown("#### Business Value")
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Retention Performance:** {him_score['business_impact']['retention']['score']}/200")
        st.caption(f"Your {retention_rate}% retention rate has saved an estimated £{retention_savings:,.0f} in turnover costs")
    with col2:
        st.write(f"**Diversity Contribution:** {him_score['business_impact']['diversity']['score']}/200")
        st.caption(f"{metrics.get('diversity_data', {}).get('total_employees', 0)} employees from {countries} countries")
    
    # Social Impact breakdown
    st.markdown("#### Social Impact")
    social_dims = him_score['social_impact']['dimensions']
    if social_dims:
        for dim_name, dim_score in social_dims.items():
            col1, col2 = st.columns([3, 1])
            col1.write(f"**{dim_name}**")
            col2.write(f"{dim_score}%")
            st.progress(dim_score / 100)
    else:
        st.info("Complete the Holistic Impact Assessment to include social impact data in your reports")
    
    st.divider()
    
    # ============ DETAILED BREAKDOWN ============
    st.markdown("### Detailed Breakdown")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Employment Outcomes")
        st.write(f"**Total Placements:** {metrics['total_placements']}")
        st.write(f"**Currently Employed:** {metrics['active_employees']}")
        st.write(f"**12-Month Retention Rate:** {retention_rate}%")
        st.write(f"**Average Tenure:** {metrics.get('avg_tenure_months', 0)} months")
    
    with col2:
        st.markdown("#### Financial Impact")
        st.write(f"**Estimated Retention Savings:** £{retention_savings:,.0f}")
        st.write(f"**Living Wage Roles:** {metrics['living_wage_percent']}%")
        st.write(f"**Employees Trained:** {metrics['training_count']}")
        st.write(f"**Career Progressions:** {metrics['progression_count']}")
    
    # Employee Testimonials
    if metrics.get("candidate_quotes"):
        st.divider()
        st.markdown("### Employee Testimonials")
        for quote in metrics["candidate_quotes"][:3]:
            st.markdown(f'> "{quote}"')


# ============ NAVIGATION ============
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
            page = st.radio("Navigation", [
                "Dashboard",
                "Manage Partners",
                "Manage Candidates",
                "Holistic Impact Assessment",
                "Candidate Support"
            ], label_visibility="collapsed")
        else:
            page = st.radio("Navigation", [
                "Dashboard",
                "Candidates",
                "Holistic Impact Assessment",
                "Reports"
            ], label_visibility="collapsed")
    
    if st.session_state.user_type == "ach_staff":
        pages = {
            "Dashboard": ach_dashboard,
            "Manage Partners": ach_manage_partners,
            "Manage Candidates": ach_manage_candidates,
            "Holistic Impact Assessment": ach_capability_assessment,
            "Candidate Support": ach_candidate_support
        }
    else:
        pages = {
            "Dashboard": partner_dashboard,
            "Holistic Impact Assessment": partner_inclusion_assessment,
            "Candidates": partner_candidates,
            "Reports": partner_reports
        }
    
    pages[page]()


if __name__ == "__main__":
    main()
