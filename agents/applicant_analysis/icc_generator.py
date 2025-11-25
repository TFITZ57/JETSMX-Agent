"""
Initial Candidate Coverage (ICC) PDF generator.
"""
from datetime import datetime
from typing import Dict, Any
from shared.logging.logger import setup_logger

logger = setup_logger(__name__)


def generate_icc_text(applicant_data: Dict[str, Any], analysis: Dict[str, Any]) -> str:
    """
    Generate ICC text content from applicant data and LLM analysis.
    
    Args:
        applicant_data: Parsed resume data
        analysis: LLM-generated analysis
        
    Returns:
        ICC text content
    """
    name = applicant_data.get('applicant_name', 'Unknown')
    email = applicant_data.get('email', 'N/A')
    phone = applicant_data.get('phone', 'N/A')
    location = applicant_data.get('location', 'N/A')
    
    has_ap = applicant_data.get('has_faa_ap', False)
    ap_number = applicant_data.get('faa_ap_number', 'Not found')
    years = applicant_data.get('years_in_aviation', 'Unknown')
    
    baseline_verdict = analysis.get('baseline_verdict', 'Needs Review')
    suitability_score = analysis.get('aog_suitability_score', 0)
    
    aircraft_experience = analysis.get('aircraft_experience', 'Not specified')
    engine_experience = analysis.get('engine_experience', 'Not specified')
    systems_strengths = analysis.get('systems_strengths', 'Not specified')
    
    missing_info = analysis.get('missing_info', '')
    follow_up_questions = analysis.get('follow_up_questions', '')
    
    icc_text = f"""
============================================================
JETSTREAMMX LLC - INITIAL CANDIDATE COVERAGE (ICC)
============================================================

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

CANDIDATE INFORMATION
------------------------------------------------------------
Name:           {name}
Email:          {email}
Phone:          {phone}
Location:       {location}

LICENSING & COMPLIANCE
------------------------------------------------------------
FAA A&P:        {'✓ YES' if has_ap else '✗ NO'}
A&P Number:     {ap_number}
Years in Aviation: {years}

EXPERIENCE SUMMARY
------------------------------------------------------------
Aircraft Families:
{aircraft_experience}

Engine Families:
{engine_experience}

Systems Strengths:
{systems_strengths}

SUITABILITY ASSESSMENT
------------------------------------------------------------
Baseline Verdict:       {baseline_verdict}
AOG Suitability Score:  {suitability_score}/10

Business Aviation:      {'✓ YES' if applicant_data.get('business_aviation_experience') else '✗ NO'}
AOG/Field Experience:   {'✓ YES' if applicant_data.get('aog_field_experience') else '✗ NO'}

MISSING INFORMATION
------------------------------------------------------------
{missing_info if missing_info else 'None identified'}

RECOMMENDED FOLLOW-UP QUESTIONS
------------------------------------------------------------
{follow_up_questions if follow_up_questions else 'None at this time'}

============================================================
END OF ICC - JetsMX Hiring Process
============================================================
"""
    
    return icc_text


def generate_icc_pdf(applicant_data: Dict[str, Any], analysis: Dict[str, Any]) -> bytes:
    """
    Generate ICC PDF from applicant data and analysis.
    
    For simplicity, this generates a text-based PDF. In production, you might
    use reportlab or other PDF libraries for richer formatting.
    
    Args:
        applicant_data: Parsed resume data
        analysis: LLM-generated analysis
        
    Returns:
        PDF content as bytes
    """
    icc_text = generate_icc_text(applicant_data, analysis)
    
    # Simple approach: create a text-based PDF using reportlab
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Preformatted
        from reportlab.lib.units import inch
        import io
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        
        styles = getSampleStyleSheet()
        story = []
        
        # Add content as preformatted text
        pre = Preformatted(icc_text, styles['Code'])
        story.append(pre)
        
        doc.build(story)
        
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        logger.info(f"Generated ICC PDF, size: {len(pdf_bytes)} bytes")
        return pdf_bytes
        
    except ImportError:
        # Fallback: return text as bytes (not a real PDF)
        logger.warning("reportlab not available, returning plain text")
        return icc_text.encode('utf-8')
    except Exception as e:
        logger.error(f"Failed to generate ICC PDF: {str(e)}")
        # Return plain text as fallback
        return icc_text.encode('utf-8')

