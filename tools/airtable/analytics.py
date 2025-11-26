"""
Analytics and aggregation functions for Airtable records.
"""
from typing import List, Dict, Any, Optional, Callable
from collections import defaultdict, Counter
from datetime import datetime, timedelta
import statistics


class Analytics:
    """Perform analytics and aggregations on Airtable records."""
    
    @staticmethod
    def count_records(records: List[Dict[str, Any]]) -> int:
        """Count total records."""
        return len(records)
    
    @staticmethod
    def count_by_field(
        records: List[Dict[str, Any]],
        field_name: str
    ) -> Dict[str, int]:
        """
        Count records grouped by field value.
        
        Args:
            records: List of records
            field_name: Field to group by
            
        Returns:
            Dict mapping field value to count
        """
        counts = Counter()
        
        for record in records:
            fields = record.get("fields", {})
            value = fields.get(field_name)
            
            # Handle None/empty
            if value is None or value == "":
                value = "(empty)"
            # Handle lists (multi-select, linked records)
            elif isinstance(value, list):
                for item in value:
                    counts[str(item)] += 1
                continue
            
            counts[str(value)] += 1
        
        return dict(counts)
    
    @staticmethod
    def sum_field(
        records: List[Dict[str, Any]],
        field_name: str
    ) -> float:
        """
        Sum numeric values in a field.
        
        Args:
            records: List of records
            field_name: Numeric field to sum
            
        Returns:
            Sum of all values
        """
        total = 0.0
        
        for record in records:
            fields = record.get("fields", {})
            value = fields.get(field_name)
            
            if value is not None:
                try:
                    total += float(value)
                except (ValueError, TypeError):
                    pass
        
        return total
    
    @staticmethod
    def average_field(
        records: List[Dict[str, Any]],
        field_name: str
    ) -> Optional[float]:
        """
        Calculate average of numeric field.
        
        Args:
            records: List of records
            field_name: Numeric field to average
            
        Returns:
            Average value or None if no valid values
        """
        values = []
        
        for record in records:
            fields = record.get("fields", {})
            value = fields.get(field_name)
            
            if value is not None:
                try:
                    values.append(float(value))
                except (ValueError, TypeError):
                    pass
        
        if not values:
            return None
        
        return statistics.mean(values)
    
    @staticmethod
    def min_field(
        records: List[Dict[str, Any]],
        field_name: str
    ) -> Optional[float]:
        """Get minimum value of numeric field."""
        values = []
        
        for record in records:
            fields = record.get("fields", {})
            value = fields.get(field_name)
            
            if value is not None:
                try:
                    values.append(float(value))
                except (ValueError, TypeError):
                    pass
        
        if not values:
            return None
        
        return min(values)
    
    @staticmethod
    def max_field(
        records: List[Dict[str, Any]],
        field_name: str
    ) -> Optional[float]:
        """Get maximum value of numeric field."""
        values = []
        
        for record in records:
            fields = record.get("fields", {})
            value = fields.get(field_name)
            
            if value is not None:
                try:
                    values.append(float(value))
                except (ValueError, TypeError):
                    pass
        
        if not values:
            return None
        
        return max(values)
    
    @staticmethod
    def group_by(
        records: List[Dict[str, Any]],
        field_name: str
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group records by field value.
        
        Args:
            records: List of records
            field_name: Field to group by
            
        Returns:
            Dict mapping field value to list of records
        """
        groups = defaultdict(list)
        
        for record in records:
            fields = record.get("fields", {})
            value = fields.get(field_name)
            
            # Handle None/empty
            if value is None or value == "":
                value = "(empty)"
            # Handle lists - add record to multiple groups
            elif isinstance(value, list):
                for item in value:
                    groups[str(item)].append(record)
                continue
            
            groups[str(value)].append(record)
        
        return dict(groups)
    
    @staticmethod
    def group_and_count(
        records: List[Dict[str, Any]],
        field_name: str
    ) -> Dict[str, int]:
        """Group by field and return counts (alias for count_by_field)."""
        return Analytics.count_by_field(records, field_name)
    
    @staticmethod
    def group_and_sum(
        records: List[Dict[str, Any]],
        group_field: str,
        sum_field: str
    ) -> Dict[str, float]:
        """
        Group by one field and sum another.
        
        Args:
            records: List of records
            group_field: Field to group by
            sum_field: Numeric field to sum within each group
            
        Returns:
            Dict mapping group value to sum
        """
        groups = Analytics.group_by(records, group_field)
        result = {}
        
        for group_value, group_records in groups.items():
            result[group_value] = Analytics.sum_field(group_records, sum_field)
        
        return result
    
    @staticmethod
    def group_and_average(
        records: List[Dict[str, Any]],
        group_field: str,
        avg_field: str
    ) -> Dict[str, Optional[float]]:
        """
        Group by one field and average another.
        
        Args:
            records: List of records
            group_field: Field to group by
            avg_field: Numeric field to average within each group
            
        Returns:
            Dict mapping group value to average
        """
        groups = Analytics.group_by(records, group_field)
        result = {}
        
        for group_value, group_records in groups.items():
            result[group_value] = Analytics.average_field(group_records, avg_field)
        
        return result
    
    @staticmethod
    def filter_records(
        records: List[Dict[str, Any]],
        filter_func: Callable[[Dict[str, Any]], bool]
    ) -> List[Dict[str, Any]]:
        """
        Filter records using a custom function.
        
        Args:
            records: List of records
            filter_func: Function that takes a record and returns bool
            
        Returns:
            Filtered list of records
        """
        return [r for r in records if filter_func(r)]
    
    @staticmethod
    def date_range_analysis(
        records: List[Dict[str, Any]],
        date_field: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Analyze records over a date range.
        
        Args:
            records: List of records
            date_field: Date/datetime field to analyze
            days: Number of days to analyze (from today backwards)
            
        Returns:
            Dict with date range statistics
        """
        now = datetime.now()
        cutoff = now - timedelta(days=days)
        
        recent = []
        older = []
        no_date = []
        
        for record in records:
            fields = record.get("fields", {})
            date_value = fields.get(date_field)
            
            if not date_value:
                no_date.append(record)
                continue
            
            # Parse date
            try:
                if isinstance(date_value, str):
                    # Try ISO format
                    record_date = datetime.fromisoformat(date_value.replace('Z', '+00:00'))
                elif isinstance(date_value, datetime):
                    record_date = date_value
                else:
                    no_date.append(record)
                    continue
                
                if record_date >= cutoff:
                    recent.append(record)
                else:
                    older.append(record)
            except:
                no_date.append(record)
        
        return {
            "total_records": len(records),
            "recent_count": len(recent),
            "older_count": len(older),
            "no_date_count": len(no_date),
            "date_range_days": days,
            "cutoff_date": cutoff.isoformat(),
            "recent_records": recent,
            "older_records": older
        }


class PipelineAnalytics:
    """Specialized analytics for Applicant Pipeline table."""
    
    @staticmethod
    def stage_funnel(records: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get counts for each pipeline stage."""
        return Analytics.count_by_field(records, "Pipeline Stage")
    
    @staticmethod
    def conversion_rate(
        records: List[Dict[str, Any]],
        from_stage: str,
        to_stage: str
    ) -> float:
        """
        Calculate conversion rate between two stages.
        
        Returns:
            Percentage (0-100)
        """
        stage_counts = Analytics.count_by_field(records, "Pipeline Stage")
        from_count = stage_counts.get(from_stage, 0)
        to_count = stage_counts.get(to_stage, 0)
        
        if from_count == 0:
            return 0.0
        
        return (to_count / from_count) * 100
    
    @staticmethod
    def average_time_in_stage(
        records: List[Dict[str, Any]],
        stage: str
    ) -> Optional[float]:
        """
        Calculate average time spent in a stage (in days).
        
        Note: Requires "Stage Last Updated" field.
        """
        # This would require historical data or timestamp fields
        # For now, return None as placeholder
        return None
    
    @staticmethod
    def response_rate(records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate applicant response rate."""
        sent = len([r for r in records if r.get("fields", {}).get("Initial Email Sent At")])
        responded = len([r for r in records if r.get("fields", {}).get("Last Reply Received At")])
        
        rate = (responded / sent * 100) if sent > 0 else 0.0
        
        return {
            "emails_sent": sent,
            "responses_received": responded,
            "response_rate_percent": round(rate, 1)
        }


class ApplicantAnalytics:
    """Specialized analytics for Applicants table."""
    
    @staticmethod
    def certification_stats(records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get statistics on certifications."""
        total = len(records)
        with_ap = len([r for r in records if r.get("fields", {}).get("Has FAA A&P")])
        
        return {
            "total_applicants": total,
            "with_faa_ap": with_ap,
            "without_faa_ap": total - with_ap,
            "ap_percentage": round((with_ap / total * 100) if total > 0 else 0, 1)
        }
    
    @staticmethod
    def experience_stats(records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get statistics on experience levels."""
        avg_years = Analytics.average_field(records, "Years in Aviation")
        min_years = Analytics.min_field(records, "Years in Aviation")
        max_years = Analytics.max_field(records, "Years in Aviation")
        
        with_aog = len([
            r for r in records 
            if r.get("fields", {}).get("AOG / Field Experience")
        ])
        
        return {
            "average_years": round(avg_years, 1) if avg_years else None,
            "min_years": min_years,
            "max_years": max_years,
            "with_aog_experience": with_aog,
            "total_applicants": len(records)
        }
    
    @staticmethod
    def geographic_distribution(records: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get counts by geographic flexibility."""
        return Analytics.count_by_field(records, "Geographic Flexibility")

