"""
Email reply parser for extracting availability and contact info from applicant responses.
"""
import re
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from shared.logging.logger import setup_logger

logger = setup_logger(__name__)


def extract_phone_number(body_text: str) -> Optional[str]:
    """
    Extract phone number from email body.
    
    Handles formats like:
    - (123) 456-7890
    - 123-456-7890
    - 123.456.7890
    - 1234567890
    - +1 123 456 7890
    
    Args:
        body_text: Email body text
        
    Returns:
        Phone number string or None
    """
    # Common phone number patterns
    patterns = [
        r'\+?1?\s*\(?(\d{3})\)?[\s.-]?(\d{3})[\s.-]?(\d{4})',  # US format with various separators
        r'(\d{3})[\s.-]?(\d{3})[\s.-]?(\d{4})',  # Simple 10-digit
    ]
    
    for pattern in patterns:
        match = re.search(pattern, body_text)
        if match:
            # Normalize to format: (XXX) XXX-XXXX
            groups = match.groups()
            if len(groups) >= 3:
                phone = f"({groups[0]}) {groups[1]}-{groups[2]}"
                logger.info(f"Extracted phone number: {phone}")
                return phone
    
    logger.warning("No phone number found in email body")
    return None


def extract_availability(body_text: str) -> List[str]:
    """
    Extract availability windows from email body.
    
    Looks for patterns like:
    - "Monday 2-4pm"
    - "available Tuesday afternoon"
    - "Wednesday morning works"
    - "I can do Thursday at 10am"
    - "Friday between 1-3"
    
    Args:
        body_text: Email body text
        
    Returns:
        List of availability window strings
    """
    availability_windows = []
    
    # Days of week pattern
    days_pattern = r'\b(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday|Mon|Tue|Wed|Thu|Fri|Sat|Sun)\b'
    
    # Time patterns
    time_patterns = [
        r'(\d{1,2})\s*(?:am|pm|AM|PM)',  # 2pm, 10am
        r'(\d{1,2}):(\d{2})\s*(?:am|pm|AM|PM)',  # 2:30pm
        r'\b(morning|afternoon|evening)\b',  # morning, afternoon, evening
        r'between\s+(\d{1,2}(?::\d{2})?)\s*(?:am|pm|AM|PM)?\s*(?:and|-)\s*(\d{1,2}(?::\d{2})?)\s*(?:am|pm|AM|PM)?',
    ]
    
    # Find sentences with day references
    sentences = re.split(r'[.!?\n]', body_text)
    
    for sentence in sentences:
        sentence_lower = sentence.lower()
        
        # Check for availability indicators
        availability_indicators = [
            'available', 'free', 'work', 'can do', 'good for me',
            'open', 'flexible', 'prefer', 'best'
        ]
        
        has_indicator = any(indicator in sentence_lower for indicator in availability_indicators)
        
        if has_indicator:
            # Look for day + time combination
            day_match = re.search(days_pattern, sentence, re.IGNORECASE)
            if day_match:
                day = day_match.group(1)
                
                # Try to find time in same sentence
                time_info = None
                for pattern in time_patterns:
                    time_match = re.search(pattern, sentence, re.IGNORECASE)
                    if time_match:
                        time_info = time_match.group(0)
                        break
                
                if time_info:
                    window = f"{day} {time_info}"
                else:
                    window = f"{day}"
                
                availability_windows.append(window.strip())
    
    # Deduplicate
    availability_windows = list(set(availability_windows))
    
    if availability_windows:
        logger.info(f"Extracted {len(availability_windows)} availability windows: {availability_windows}")
    else:
        logger.warning("No availability windows found in email")
    
    return availability_windows


def extract_constraints(body_text: str) -> Optional[str]:
    """
    Extract scheduling constraints or preferences from email.
    
    Looks for:
    - Time zone mentions
    - "Not available on..."
    - "Prefer not to..."
    - "Can't do..."
    
    Args:
        body_text: Email body text
        
    Returns:
        Constraints string or None
    """
    constraints = []
    
    # Negative availability patterns
    negative_patterns = [
        r'(?:not available|can\'t|cannot|unable)\s+(?:on|during|at)?\s*([^.!?\n]+)',
        r'(?:prefer not|would prefer not|don\'t want)\s+(?:to)?\s*([^.!?\n]+)',
        r'(?:avoid|can\'t do|won\'t work)\s+([^.!?\n]+)',
    ]
    
    for pattern in negative_patterns:
        matches = re.finditer(pattern, body_text, re.IGNORECASE)
        for match in matches:
            constraint = match.group(0).strip()
            if len(constraint) < 100:  # Reasonable length
                constraints.append(constraint)
    
    # Time zone mentions
    tz_pattern = r'\b([A-Z]{2,4}T|Eastern|Central|Mountain|Pacific|EST|CST|MST|PST|EDT|CDT|MDT|PDT)\b'
    tz_match = re.search(tz_pattern, body_text)
    if tz_match:
        constraints.append(f"Mentioned timezone: {tz_match.group(0)}")
    
    if constraints:
        result = "; ".join(constraints)
        logger.info(f"Extracted constraints: {result}")
        return result
    
    return None


def generate_proposed_times(
    availability_windows: List[str],
    num_proposals: int = 3,
    default_duration_minutes: int = 30
) -> List[Dict[str, Any]]:
    """
    Generate proposed probe call times based on applicant availability.
    
    Args:
        availability_windows: List of availability strings from extract_availability
        num_proposals: Number of time slots to propose
        default_duration_minutes: Default call duration
        
    Returns:
        List of proposed time dicts with start_time, end_time, display_text
    """
    proposals = []
    
    # If we have specific windows, use them
    if availability_windows:
        for i, window in enumerate(availability_windows[:num_proposals]):
            # Parse the window to create a specific time
            proposed_time = parse_window_to_time(window, default_duration_minutes)
            if proposed_time:
                proposals.append(proposed_time)
    
    # If we don't have enough proposals, add default business hour slots
    while len(proposals) < num_proposals:
        # Generate next business day slots
        days_ahead = len(proposals) + 1
        base_time = datetime.now() + timedelta(days=days_ahead)
        
        # Skip weekends
        while base_time.weekday() >= 5:  # 5=Saturday, 6=Sunday
            base_time += timedelta(days=1)
        
        # Default to 10 AM Eastern
        start = base_time.replace(hour=10, minute=0, second=0, microsecond=0)
        end = start + timedelta(minutes=default_duration_minutes)
        
        proposals.append({
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
            "display_text": start.strftime("%A, %B %d at %I:%M %p ET")
        })
    
    logger.info(f"Generated {len(proposals)} proposed times")
    return proposals


def parse_window_to_time(window: str, duration_minutes: int = 30) -> Optional[Dict[str, Any]]:
    """
    Parse an availability window string into a specific datetime.
    
    Args:
        window: Availability window string (e.g., "Monday 2pm")
        duration_minutes: Duration of the call
        
    Returns:
        Dict with start_time, end_time, display_text or None
    """
    try:
        # Extract day of week
        days_map = {
            'monday': 0, 'mon': 0,
            'tuesday': 1, 'tue': 1,
            'wednesday': 2, 'wed': 2,
            'thursday': 3, 'thu': 3,
            'friday': 4, 'fri': 4,
            'saturday': 5, 'sat': 5,
            'sunday': 6, 'sun': 6
        }
        
        window_lower = window.lower()
        target_day = None
        
        for day_name, day_num in days_map.items():
            if day_name in window_lower:
                target_day = day_num
                break
        
        if target_day is None:
            return None
        
        # Find next occurrence of that day
        today = datetime.now()
        days_ahead = (target_day - today.weekday()) % 7
        if days_ahead == 0:
            days_ahead = 7  # Next week if same day
        
        target_date = today + timedelta(days=days_ahead)
        
        # Extract time
        hour = 14  # Default to 2 PM
        minute = 0
        
        # Look for time patterns
        time_match = re.search(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm|AM|PM)', window)
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2)) if time_match.group(2) else 0
            period = time_match.group(3).lower()
            
            if period == 'pm' and hour != 12:
                hour += 12
            elif period == 'am' and hour == 12:
                hour = 0
        elif 'morning' in window_lower:
            hour = 10
        elif 'afternoon' in window_lower:
            hour = 14
        elif 'evening' in window_lower:
            hour = 17
        
        start = target_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
        end = start + timedelta(minutes=duration_minutes)
        
        return {
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
            "display_text": start.strftime("%A, %B %d at %I:%M %p ET")
        }
        
    except Exception as e:
        logger.error(f"Failed to parse window '{window}': {str(e)}")
        return None


def parse_applicant_reply(body_text: str) -> Dict[str, Any]:
    """
    Main function to parse all relevant info from applicant email reply.
    
    Args:
        body_text: Email body text
        
    Returns:
        Dict with phone, availability_windows, constraints, proposed_times
    """
    logger.info("Parsing applicant reply")
    
    phone = extract_phone_number(body_text)
    availability_windows = extract_availability(body_text)
    constraints = extract_constraints(body_text)
    proposed_times = generate_proposed_times(availability_windows)
    
    result = {
        "phone": phone,
        "availability_windows": availability_windows,
        "constraints": constraints,
        "proposed_times": proposed_times,
        "raw_summary": body_text[:500]  # First 500 chars for reference
    }
    
    logger.info(f"Parse result: phone={phone}, windows={len(availability_windows)}, proposals={len(proposed_times)}")
    
    return result

