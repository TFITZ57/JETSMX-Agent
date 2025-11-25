"""
Chat tools for Google ADK agents.
"""
from typing import Optional, Dict, Any
from tools.chat.messages import post_message as _post_message, post_card as _post_card
from tools.chat.cards import (
    build_approval_card,
    build_notification_card,
    build_applicant_summary_card
)
from shared.config.settings import get_settings


def chat_post_message(text: str, thread_key: Optional[str] = None) -> dict:
    """Post a text message to Google Chat.
    
    Args:
        text: Message text
        thread_key: Thread key for replies (optional)
        
    Returns:
        Message info
    """
    settings = get_settings()
    space = settings.google_chat_space_id
    if not space:
        raise ValueError("Google Chat space ID not configured")
    return _post_message(space, text, thread_key)


def chat_post_approval_card(
    title: str,
    preview_text: str,
    approve_action_params: dict,
    thread_key: Optional[str] = None
) -> dict:
    """Post an approval card to Google Chat for human-in-the-loop workflows.
    
    Args:
        title: Card title
        preview_text: Preview of content to approve
        approve_action_params: Parameters for approval action callback
        thread_key: Thread key for replies (optional)
        
    Returns:
        Message info
    """
    settings = get_settings()
    space = settings.google_chat_space_id
    if not space:
        raise ValueError("Google Chat space ID not configured")
    
    card = build_approval_card(
        title=title,
        preview_text=preview_text,
        approve_action={
            'actionMethodName': 'approve_action',
            'parameters': [
                {'key': k, 'value': str(v)} for k, v in approve_action_params.items()
            ]
        }
    )
    
    return _post_card(space, card, thread_key)


def chat_post_notification(title: str, message: str, fields: Optional[list] = None) -> dict:
    """Post a notification card to Google Chat.
    
    Args:
        title: Card title
        message: Message text
        fields: Optional list of {label, value} dicts
        
    Returns:
        Message info
    """
    settings = get_settings()
    space = settings.google_chat_space_id
    if not space:
        raise ValueError("Google Chat space ID not configured")
    
    card = build_notification_card(title, message, fields)
    return _post_card(space, card)


def chat_post_applicant_summary(
    applicant_name: str,
    email: str,
    phone: Optional[str],
    has_ap: bool,
    baseline_verdict: Optional[str]
) -> dict:
    """Post an applicant summary card to Google Chat.
    
    Args:
        applicant_name: Applicant name
        email: Email address
        phone: Phone number
        has_ap: Whether they have A&P license
        baseline_verdict: Verdict (Strong Fit, Maybe, etc.)
        
    Returns:
        Message info
    """
    settings = get_settings()
    space = settings.google_chat_space_id
    if not space:
        raise ValueError("Google Chat space ID not configured")
    
    card = build_applicant_summary_card(
        applicant_name=applicant_name,
        email=email,
        phone=phone,
        has_ap=has_ap,
        baseline_verdict=baseline_verdict
    )
    
    return _post_card(space, card)


# Export all tools
ALL_CHAT_TOOLS = [
    chat_post_message,
    chat_post_approval_card,
    chat_post_notification,
    chat_post_applicant_summary
]

