"""
Google Chat card builders.
"""
from typing import List, Dict, Any, Optional


def build_approval_card(
    title: str,
    preview_text: str,
    approve_action: Dict[str, Any],
    edit_action: Optional[Dict[str, Any]] = None,
    cancel_action: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Build a standard approval card for human-in-the-loop workflows.
    
    Args:
        title: Card title
        preview_text: Preview of the content to approve
        approve_action: Action definition for approval button
        edit_action: Action definition for edit button (optional)
        cancel_action: Action definition for cancel button (optional)
        
    Returns:
        Card JSON structure
    """
    buttons = []
    
    # Approve button
    buttons.append({
        'text': 'Approve',
        'onClick': {
            'action': approve_action
        }
    })
    
    # Edit button
    if edit_action:
        buttons.append({
            'text': 'Edit',
            'onClick': edit_action
        })
    
    # Cancel button
    if cancel_action:
        buttons.append({
            'text': 'Cancel',
            'onClick': {
                'action': cancel_action
            }
        })
    
    card = {
        'header': {
            'title': title
        },
        'sections': [
            {
                'widgets': [
                    {
                        'textParagraph': {
                            'text': preview_text
                        }
                    }
                ]
            },
            {
                'widgets': [
                    {
                        'buttonList': {
                            'buttons': buttons
                        }
                    }
                ]
            }
        ]
    }
    
    return card


def build_notification_card(title: str, message: str, fields: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
    """
    Build a simple notification card.
    
    Args:
        title: Card title
        message: Message text
        fields: Optional list of key-value pairs to display
        
    Returns:
        Card JSON structure
    """
    widgets = [
        {
            'textParagraph': {
                'text': message
            }
        }
    ]
    
    # Add key-value fields if provided
    if fields:
        for field in fields:
            widgets.append({
                'decoratedText': {
                    'topLabel': field.get('label', ''),
                    'text': field.get('value', '')
                }
            })
    
    card = {
        'header': {
            'title': title
        },
        'sections': [
            {
                'widgets': widgets
            }
        ]
    }
    
    return card


def build_applicant_summary_card(
    applicant_name: str,
    email: str,
    phone: Optional[str],
    has_ap: bool,
    baseline_verdict: Optional[str],
    actions: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Build a card summarizing an applicant.
    
    Args:
        applicant_name: Applicant name
        email: Email address
        phone: Phone number
        has_ap: Whether they have A&P
        baseline_verdict: Verdict (Strong Fit, Maybe, etc.)
        actions: Optional action buttons
        
    Returns:
        Card JSON structure
    """
    widgets = [
        {
            'decoratedText': {
                'topLabel': 'Email',
                'text': email or 'N/A'
            }
        },
        {
            'decoratedText': {
                'topLabel': 'Phone',
                'text': phone or 'N/A'
            }
        },
        {
            'decoratedText': {
                'topLabel': 'A&P License',
                'text': '✓ Yes' if has_ap else '✗ No'
            }
        }
    ]
    
    if baseline_verdict:
        widgets.append({
            'decoratedText': {
                'topLabel': 'Verdict',
                'text': baseline_verdict
            }
        })
    
    sections = [{'widgets': widgets}]
    
    # Add action buttons if provided
    if actions:
        buttons = []
        for action in actions:
            buttons.append({
                'text': action.get('text', ''),
                'onClick': {
                    'action': action.get('action', {})
                }
            })
        
        sections.append({
            'widgets': [{
                'buttonList': {'buttons': buttons}
            }]
        })
    
    card = {
        'header': {
            'title': f'Applicant: {applicant_name}'
        },
        'sections': sections
    }
    
    return card


def build_probe_scheduling_card(
    applicant_name: str,
    email_summary: str,
    proposed_times: List[Dict[str, Any]],
    pipeline_id: str
) -> Dict[str, Any]:
    """
    Build a card for scheduling a probe call with proposed time slots.
    
    Args:
        applicant_name: Applicant name
        email_summary: Summary of their email (availability, phone, etc.)
        proposed_times: List of proposed time dicts with display_text, start_time, end_time
        pipeline_id: Pipeline record ID for callback
        
    Returns:
        Card JSON structure
    """
    widgets = [
        {
            'textParagraph': {
                'text': f'<b>Applicant Reply Received</b>\n\n{email_summary}'
            }
        }
    ]
    
    # Add divider
    widgets.append({
        'divider': {}
    })
    
    # Add proposed times section
    widgets.append({
        'textParagraph': {
            'text': '<b>Proposed Probe Call Times:</b>'
        }
    })
    
    # Add buttons for each proposed time
    buttons = []
    for i, time_slot in enumerate(proposed_times):
        display_text = time_slot.get('display_text', f'Option {i+1}')
        
        buttons.append({
            'text': display_text,
            'onClick': {
                'action': {
                    'actionMethodName': 'approve_probe_time',
                    'parameters': [
                        {'key': 'pipeline_id', 'value': pipeline_id},
                        {'key': 'start_time', 'value': time_slot.get('start_time', '')},
                        {'key': 'end_time', 'value': time_slot.get('end_time', '')},
                        {'key': 'display_text', 'value': display_text}
                    ]
                }
            }
        })
    
    widgets.append({
        'buttonList': {
            'buttons': buttons
        }
    })
    
    # Add manual scheduling option
    widgets.append({
        'divider': {}
    })
    
    widgets.append({
        'buttonList': {
            'buttons': [{
                'text': 'Schedule Manually',
                'onClick': {
                    'openLink': {
                        'url': f'https://calendar.google.com'
                    }
                }
            }]
        }
    })
    
    card = {
        'header': {
            'title': f'Schedule Probe Call: {applicant_name}',
            'subtitle': 'Select a time to schedule'
        },
        'sections': [
            {
                'widgets': widgets
            }
        ]
    }
    
    return card

