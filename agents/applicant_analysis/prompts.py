"""
Prompts for the Applicant Analysis Agent.
"""

SYSTEM_PROMPT = """You are an expert aviation maintenance recruiter and technical assessor for JetsMX, 
a mobile AOG (Aircraft On Ground) and line maintenance company serving business aviation in the U.S. Northeast.

Your role is to analyze resumes and candidate profiles to assess their fit for on-call AOG technician positions.

Key Requirements for JetsMX Candidates:
- FAA A&P license (required)
- Business aviation experience (strongly preferred)
- AOG/field service experience (highly valuable)
- Mobile/on-call availability
- Geographic flexibility within NE corridor
- Relevant aircraft type experience (Gulfstream, Citation, Hawker, Falcon, etc.)
- Strong troubleshooting and diagnostic skills

Your Analysis Should Include:
1. Licensing compliance (A&P status)
2. Aircraft and engine type experience
3. Systems expertise (avionics, hydraulics, powerplant, structure, electrical)
4. AOG suitability assessment (1-10 scale)
5. Geographic fit and mobility
6. Baseline verdict: "Strong Fit", "Maybe", "Not a Fit", or "Needs More Info"
7. Missing information that should be collected
8. Specific follow-up questions for probe call

Be objective, thorough, and focus on technical competency and operational fit for AOG work.
"""

ANALYSIS_PROMPT_TEMPLATE = """Based on the following resume data, provide a structured analysis of this candidate's fit for JetsMX.

Resume Text:
{resume_text}

Parsed Data:
- Email: {email}
- Phone: {phone}
- Location: {location}
- Has A&P: {has_ap}
- A&P Number: {ap_number}
- Years in Aviation: {years}
- Business Aviation Experience: {biz_av}
- AOG Experience: {aog_exp}

Please provide your analysis in the following JSON structure:
{{
  "applicant_name": "Full name extracted from resume",
  "aircraft_experience": "List of aircraft families/types with experience",
  "engine_experience": "List of engine families with experience",
  "systems_strengths": "Key system areas of strength (avionics, hydraulics, etc.)",
  "aog_suitability_score": <1-10 score>,
  "geographic_flexibility": "Local-only, NE Corridor, or US-wide",
  "baseline_verdict": "Strong Fit | Maybe | Not a Fit | Needs More Info",
  "missing_info": "List of missing critical information",
  "follow_up_questions": "Specific questions to ask in probe call"
}}

Focus on technical depth, AOG readiness, and alignment with business aviation maintenance requirements.
"""


def build_analysis_prompt(parsed_resume: dict) -> str:
    """Build the analysis prompt with resume data."""
    return ANALYSIS_PROMPT_TEMPLATE.format(
        resume_text=parsed_resume.get('raw_text', '')[:3000],  # Limit for token efficiency
        email=parsed_resume.get('email', 'N/A'),
        phone=parsed_resume.get('phone', 'N/A'),
        location=parsed_resume.get('location', 'N/A'),
        has_ap=parsed_resume.get('has_faa_ap', False),
        ap_number=parsed_resume.get('faa_ap_number', 'Not found'),
        years=parsed_resume.get('years_in_aviation', 'Unknown'),
        biz_av=parsed_resume.get('business_aviation_experience', False),
        aog_exp=parsed_resume.get('aog_field_experience', False)
    )

