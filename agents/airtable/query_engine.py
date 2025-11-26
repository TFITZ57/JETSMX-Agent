"""
Advanced query engine for Airtable operations.
"""
from typing import List, Dict, Any, Optional
from tools.airtable_tools import find_records, get_record
from tools.airtable.query_builder import QueryBuilder, QueryHelper, build_complex_query
from tools.airtable.analytics import Analytics
from shared.config.settings import get_settings
from shared.logging.logger import setup_logger

logger = setup_logger(__name__)
settings = get_settings()


class QueryEngine:
    """Execute advanced queries against Airtable."""
    
    def __init__(self, base_id: Optional[str] = None):
        """
        Initialize query engine.
        
        Args:
            base_id: Airtable base ID (defaults to settings)
        """
        self.base_id = base_id or settings.airtable_base_id
    
    def simple_query(
        self,
        table: str,
        formula: Optional[str] = None,
        max_records: Optional[int] = None,
        sort: Optional[List[tuple]] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute a simple query.
        
        Args:
            table: Table name
            formula: Airtable formula
            max_records: Maximum records to return
            sort: List of (field, direction) tuples
            
        Returns:
            List of records
        """
        try:
            records = find_records(
                self.base_id,
                table,
                formula=formula,
                max_records=max_records,
                sort=sort
            )
            
            logger.info(f"Query returned {len(records)} records from {table}")
            return records
        except Exception as e:
            logger.error(f"Query failed: {e}")
            raise
    
    def filter_query(
        self,
        table: str,
        filters: List[Dict[str, Any]],
        operator: str = "AND",
        max_records: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute a query with structured filters.
        
        Args:
            table: Table name
            filters: List of filter dicts (field, op, value)
            operator: "AND" or "OR" to combine filters
            max_records: Maximum records to return
            
        Returns:
            List of records
        """
        formula = build_complex_query(filters, operator)
        return self.simple_query(table, formula=formula, max_records=max_records)
    
    def search(
        self,
        table: str,
        search_term: str,
        fields: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for records containing a term.
        
        Args:
            table: Table name
            search_term: Term to search for
            fields: Fields to search in (None for defaults)
            
        Returns:
            List of matching records
        """
        formula = QueryHelper.build_search_query(table, search_term, fields)
        return self.simple_query(table, formula=formula)
    
    def get_by_id(self, table: str, record_id: str) -> Optional[Dict[str, Any]]:
        """Get a single record by ID."""
        try:
            return get_record(self.base_id, table, record_id)
        except Exception as e:
            logger.error(f"Failed to get record {record_id}: {e}")
            return None
    
    def get_by_email(self, table: str, email: str) -> List[Dict[str, Any]]:
        """Find records by email address."""
        formula = QueryHelper.find_by_email(email)
        return self.simple_query(table, formula=formula)
    
    def get_by_name(self, table: str, name: str, exact: bool = True) -> List[Dict[str, Any]]:
        """Find records by name."""
        if exact:
            formula = QueryHelper.find_by_name(name)
        else:
            formula = QueryHelper.find_by_name_contains(name)
        return self.simple_query(table, formula=formula)
    
    def count_records(self, table: str, formula: Optional[str] = None) -> int:
        """Count records matching criteria."""
        records = self.simple_query(table, formula=formula)
        return len(records)
    
    def aggregate(
        self,
        table: str,
        agg_type: str,
        field: str,
        group_by: Optional[str] = None,
        formula: Optional[str] = None
    ) -> Any:
        """
        Perform aggregation on records.
        
        Args:
            table: Table name
            agg_type: "count", "sum", "avg", "min", "max"
            field: Field to aggregate
            group_by: Field to group by (optional)
            formula: Filter formula (optional)
            
        Returns:
            Aggregation result (number or dict if grouped)
        """
        records = self.simple_query(table, formula=formula)
        
        if not records:
            return 0 if agg_type in ["count", "sum"] else None
        
        if group_by:
            # Group and aggregate
            if agg_type == "count":
                return Analytics.count_by_field(records, group_by)
            elif agg_type == "sum":
                return Analytics.group_and_sum(records, group_by, field)
            elif agg_type == "avg":
                return Analytics.group_and_average(records, group_by, field)
            else:
                raise ValueError(f"Grouping not supported for {agg_type}")
        else:
            # Simple aggregation
            if agg_type == "count":
                return Analytics.count_records(records)
            elif agg_type == "sum":
                return Analytics.sum_field(records, field)
            elif agg_type == "avg":
                return Analytics.average_field(records, field)
            elif agg_type == "min":
                return Analytics.min_field(records, field)
            elif agg_type == "max":
                return Analytics.max_field(records, field)
            else:
                raise ValueError(f"Unknown aggregation type: {agg_type}")
    
    def join_records(
        self,
        main_table: str,
        main_records: List[Dict[str, Any]],
        link_field: str,
        linked_table: str
    ) -> List[Dict[str, Any]]:
        """
        Simulate a join by expanding linked records.
        
        Args:
            main_table: Main table name
            main_records: Records from main table
            link_field: Field with linked record IDs
            linked_table: Table being linked to
            
        Returns:
            Records with expanded linked data
        """
        # Collect all linked IDs
        linked_ids = set()
        for record in main_records:
            fields = record.get("fields", {})
            link_value = fields.get(link_field)
            
            if isinstance(link_value, list):
                linked_ids.update(link_value)
            elif link_value:
                linked_ids.add(link_value)
        
        # Fetch all linked records
        linked_data = {}
        for linked_id in linked_ids:
            try:
                linked_record = self.get_by_id(linked_table, linked_id)
                if linked_record:
                    linked_data[linked_id] = linked_record
            except:
                pass
        
        # Expand links in main records
        expanded = []
        for record in main_records:
            expanded_record = dict(record)
            fields = expanded_record.get("fields", {})
            link_value = fields.get(link_field)
            
            if link_value:
                if isinstance(link_value, list):
                    expanded_record[f"{link_field}_expanded"] = [
                        linked_data.get(lid) for lid in link_value if lid in linked_data
                    ]
                elif link_value in linked_data:
                    expanded_record[f"{link_field}_expanded"] = linked_data[link_value]
            
            expanded.append(expanded_record)
        
        return expanded


class QueryPlanner:
    """Plan and optimize complex queries."""
    
    def __init__(self, engine: QueryEngine):
        self.engine = engine
    
    def plan_query(self, query_spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create an execution plan for a query.
        
        Args:
            query_spec: Dict with table, filters, aggregations, etc.
            
        Returns:
            Execution plan
        """
        plan = {
            "steps": [],
            "estimated_records": None,
            "estimated_time_ms": None
        }
        
        table = query_spec.get("table")
        filters = query_spec.get("filters", [])
        aggregations = query_spec.get("aggregations", [])
        joins = query_spec.get("joins", [])
        
        # Step 1: Filter records
        if filters:
            plan["steps"].append({
                "type": "filter",
                "table": table,
                "filters": filters
            })
        else:
            plan["steps"].append({
                "type": "scan",
                "table": table
            })
        
        # Step 2: Joins
        for join in joins:
            plan["steps"].append({
                "type": "join",
                "main_table": table,
                "linked_table": join.get("table"),
                "link_field": join.get("field")
            })
        
        # Step 3: Aggregations
        for agg in aggregations:
            plan["steps"].append({
                "type": "aggregate",
                "agg_type": agg.get("type"),
                "field": agg.get("field"),
                "group_by": agg.get("group_by")
            })
        
        return plan
    
    def execute_plan(self, plan: Dict[str, Any]) -> Any:
        """Execute a query plan."""
        results = None
        
        for step in plan["steps"]:
            step_type = step["type"]
            
            if step_type == "filter":
                results = self.engine.filter_query(
                    step["table"],
                    step["filters"]
                )
            elif step_type == "scan":
                results = self.engine.simple_query(step["table"])
            elif step_type == "join":
                results = self.engine.join_records(
                    step["main_table"],
                    results,
                    step["link_field"],
                    step["linked_table"]
                )
            elif step_type == "aggregate":
                # For now, simple aggregation on results
                agg_type = step["agg_type"]
                field = step["field"]
                group_by = step.get("group_by")
                
                if group_by:
                    if agg_type == "count":
                        results = Analytics.count_by_field(results, group_by)
                    elif agg_type == "sum":
                        results = Analytics.group_and_sum(results, group_by, field)
                    elif agg_type == "avg":
                        results = Analytics.group_and_average(results, group_by, field)
                else:
                    if agg_type == "count":
                        results = Analytics.count_records(results)
                    elif agg_type == "sum":
                        results = Analytics.sum_field(results, field)
                    elif agg_type == "avg":
                        results = Analytics.average_field(results, field)
        
        return results

