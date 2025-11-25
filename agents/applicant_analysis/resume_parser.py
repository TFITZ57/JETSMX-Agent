"""
Resume parsing and extraction logic.
"""
import io
import PyPDF2
import pdfplumber
from typing import Dict, Any, Optional
from shared.logging.logger import setup_logger

logger = setup_logger(__name__)


def extract_text_from_pdf(pdf_content: bytes) -> str:
    """
    Extract text from PDF bytes.
    
    Args:
        pdf_content: PDF file content as bytes
        
    Returns:
        Extracted text
    """
    text = ""
    
    # Try pdfplumber first (better for complex PDFs)
    try:
        with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        
        if text.strip():
            logger.info(f"Extracted {len(text)} characters using pdfplumber")
            return text
    except Exception as e:
        logger.warning(f"pdfplumber extraction failed: {str(e)}, trying PyPDF2")
    
    # Fallback to PyPDF2
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        
        logger.info(f"Extracted {len(text)} characters using PyPDF2")
        return text
    except Exception as e:
        logger.error(f"PyPDF2 extraction failed: {str(e)}")
        return ""


def parse_contact_info(text: str) -> Dict[str, Optional[str]]:
    """
    Extract basic contact information from resume text.
    
    This is a simple heuristic parser. In production, you might use
    more sophisticated NLP or regex patterns.
    
    Args:
        text: Resume text
        
    Returns:
        Dictionary with email, phone, location
    """
    import re
    
    contact_info = {
        'email': None,
        'phone': None,
        'location': None
    }
    
    # Extract email
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    email_matches = re.findall(email_pattern, text)
    if email_matches:
        contact_info['email'] = email_matches[0]
    
    # Extract phone (US format)
    phone_pattern = r'(\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})'
    phone_matches = re.findall(phone_pattern, text)
    if phone_matches:
        # Reconstruct phone number
        match = phone_matches[0]
        contact_info['phone'] = f"({match[1]}) {match[2]}-{match[3]}"
    
    # Extract location (basic heuristic - look for City, STATE pattern)
    location_pattern = r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),\s*([A-Z]{2})'
    location_matches = re.findall(location_pattern, text)
    if location_matches:
        city, state = location_matches[0]
        contact_info['location'] = f"{city}, {state}"
    
    return contact_info


def extract_ap_license(text: str) -> tuple[bool, Optional[str]]:
    """
    Check for A&P license in resume text.
    
    Args:
        text: Resume text
        
    Returns:
        Tuple of (has_ap, ap_number)
    """
    import re
    
    text_lower = text.lower()
    
    # Check for A&P keywords
    has_ap_keywords = any(keyword in text_lower for keyword in [
        'a&p', 'a & p', 'airframe and powerplant', 'airframe & powerplant',
        'faa mechanic', 'airframe powerplant'
    ])
    
    # Try to extract A&P number (typically numeric, may have letters)
    # Pattern: numbers with possible letters, typically 6-10 characters
    ap_number_pattern = r'(?:a&p|a\s*&\s*p|license|cert|certificate)[\s:#]*([A-Z0-9]{6,10})'
    ap_matches = re.findall(ap_number_pattern, text, re.IGNORECASE)
    
    ap_number = ap_matches[0] if ap_matches else None
    
    return (has_ap_keywords, ap_number)


def calculate_years_in_aviation(text: str) -> Optional[float]:
    """
    Estimate years in aviation based on work history dates.
    
    This is a simple heuristic that looks for date ranges.
    
    Args:
        text: Resume text
        
    Returns:
        Estimated years or None
    """
    import re
    from datetime import datetime
    
    # Look for date patterns like "2015-2020", "2015 - Present", etc.
    date_pattern = r'(19|20)\d{2}\s*[-–—]\s*(?:(19|20)\d{2}|present|current)'
    
    matches = re.findall(date_pattern, text, re.IGNORECASE)
    
    if not matches:
        return None
    
    # Calculate total years (simple sum of ranges)
    total_years = 0
    current_year = datetime.now().year
    
    for match in matches[:5]:  # Limit to first 5 matches to avoid noise
        start_year = int(match[0][:4]) if match[0] else None
        if match[1]:
            end_year = int(match[1][:4]) if len(match[1]) >= 4 else current_year
        else:
            end_year = current_year
        
        if start_year and end_year >= start_year:
            total_years += (end_year - start_year)
    
    return min(total_years, 50)  # Cap at 50 years


def check_business_aviation_experience(text: str) -> bool:
    """Check for business aviation keywords."""
    text_lower = text.lower()
    
    keywords = [
        'business aviation', 'corporate aviation', 'private jet',
        'business jet', 'corporate jet', 'charter', 'fractional',
        'netjets', 'flexjet', 'gulfstream', 'bombardier', 'citation',
        'hawker', 'falcon', 'embraer phenom', 'embraer praetor'
    ]
    
    return any(keyword in text_lower for keyword in keywords)


def check_aog_experience(text: str) -> bool:
    """Check for AOG and field service keywords."""
    text_lower = text.lower()
    
    keywords = [
        'aog', 'aircraft on ground', 'field service', 'mobile maintenance',
        'on-call', 'emergency', 'rapid response', 'line maintenance',
        'ramp service', 'remote service'
    ]
    
    return any(keyword in text_lower for keyword in keywords)


def parse_resume(pdf_content: bytes) -> Dict[str, Any]:
    """
    Parse a resume PDF and extract structured data.
    
    Args:
        pdf_content: PDF file content as bytes
        
    Returns:
        Dictionary with extracted data
    """
    text = extract_text_from_pdf(pdf_content)
    
    if not text:
        logger.error("Failed to extract text from PDF")
        return {}
    
    # Extract components
    contact_info = parse_contact_info(text)
    has_ap, ap_number = extract_ap_license(text)
    years_aviation = calculate_years_in_aviation(text)
    has_biz_av = check_business_aviation_experience(text)
    has_aog = check_aog_experience(text)
    
    # Build structured data
    parsed_data = {
        'raw_text': text,
        'applicant_name': None,  # Will be filled by LLM in agent
        'email': contact_info['email'],
        'phone': contact_info['phone'],
        'location': contact_info['location'],
        'has_faa_ap': has_ap,
        'faa_ap_number': ap_number,
        'years_in_aviation': years_aviation,
        'business_aviation_experience': has_biz_av,
        'aog_field_experience': has_aog,
        'text_length': len(text)
    }
    
    logger.info(f"Parsed resume: {parsed_data.get('email', 'unknown email')}")
    
    return parsed_data

