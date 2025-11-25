"""
Prompts for the HR Pipeline Agent.
"""

SYSTEM_PROMPT = """You are the JetsMX HR Pipeline automation agent. You manage the hiring workflow including:

- Generating personalized outreach emails to candidates
- Parsing applicant replies and extracting availability
- Scheduling probe calls and interviews
- Posting approval cards to Google Chat for human review
- Updating pipeline stages in Airtable

Key Principles:
1. All outbound emails require human approval via Chat cards
2. Be professional, warm, and aviation-focused in communications
3. Extract structured data from unstructured text (emails, availability)
4. Keep Tyler informed via Chat notifications at key milestones
5. Log all interactions in Airtable for audit trail

You coordinate the entire hiring pipeline from initial outreach through contractor onboarding.
"""

OUTREACH_EMAIL_TEMPLATE = """Subject: Aviation Maintenance Opportunity - JetsMX

Hi {applicant_name},

Thank you for your interest in JetsMX! We're a mobile AOG and line maintenance provider serving business aviation across the Northeast.

I've reviewed your background in {aircraft_types}, and I'd like to learn more about your experience and discuss potential opportunities with our team.

Would you be available for a brief phone conversation this week or next? I'm flexible and happy to work around your schedule.

Looking forward to connecting!

Best regards,
Tyler Fitzgerald
Chief Pilot / Operations
JetsMX LLC
jobs@jetstreammx.com
"""


def build_outreach_email(applicant_name: str, aircraft_types: str) -> dict:
    """Build personalized outreach email."""
    subject = "Aviation Maintenance Opportunity - JetsMX"
    body = OUTREACH_EMAIL_TEMPLATE.format(
        applicant_name=applicant_name,
        aircraft_types=aircraft_types or "aviation maintenance"
    )
    
    return {
        'subject': subject,
        'body': body
    }

