"""
Airtable Agent - Central data orchestration layer for all Airtable interactions.

Provides:
- Conversational interface for natural language queries
- Programmatic interface for direct operations
- Advanced query engine with filtering and aggregation
- Bulk operations with error handling
- Data export in multiple formats
- Analytics and reporting
"""

from agents.airtable.agent import AirtableAgent, get_airtable_agent

__all__ = ['AirtableAgent', 'get_airtable_agent']

