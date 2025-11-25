"""
Webhook handlers for processing Airtable events.
"""
from infra.webhooks.handlers.base_handler import BaseWebhookHandler
from infra.webhooks.handlers.applicant_pipeline_handler import ApplicantPipelineHandler
from infra.webhooks.handlers.applicants_handler import ApplicantsHandler
from infra.webhooks.handlers.interactions_handler import InteractionsHandler
from infra.webhooks.handlers.contractors_handler import ContractorsHandler

__all__ = [
    "BaseWebhookHandler",
    "ApplicantPipelineHandler",
    "ApplicantsHandler",
    "InteractionsHandler",
    "ContractorsHandler",
]

