"""
Airtable Agent REST API Service - FastAPI application.
"""
import os
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from agents.airtable.agent import get_airtable_agent
from shared.models.airtable_requests import *
from shared.models.airtable_responses import *
from shared.logging.logger import setup_logger
from shared.config.settings import get_settings

logger = setup_logger(__name__)
settings = get_settings()

# Initialize FastAPI app
app = FastAPI(
    title="JetsMX Airtable Agent API",
    description="Central API for all Airtable operations",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========================================================================
# AUTHENTICATION
# ========================================================================

async def verify_api_key(authorization: str = Header(None)):
    """Verify API key from Authorization header."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    # Expected format: "Bearer <api_key>"
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization format")
    
    api_key = authorization.replace("Bearer ", "")
    
    # For now, simple check - in production, use proper auth
    expected_key = os.getenv("AIRTABLE_AGENT_API_KEY")
    if expected_key and api_key != expected_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    return api_key


# ========================================================================
# HEALTH & INFO
# ========================================================================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    agent = get_airtable_agent()
    
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        base_id=agent.base_id,
        capabilities={
            "conversational": True,
            "programmatic": True,
            "bulk_operations": True,
            "export": True,
            "analytics": True
        }
    )


@app.get("/airtable/schema", response_model=SchemaResponse)
async def get_all_schemas(api_key: str = Depends(verify_api_key)):
    """Get schema for all tables."""
    try:
        agent = get_airtable_agent()
        schema = agent.get_schema()
        
        return SchemaResponse(success=True, schema=schema)
    except Exception as e:
        logger.error(f"Failed to get schema: {e}")
        return SchemaResponse(success=False, schema=None, error=str(e))


@app.get("/airtable/schema/{table}", response_model=SchemaResponse)
async def get_table_schema(table: str, api_key: str = Depends(verify_api_key)):
    """Get schema for a specific table."""
    try:
        agent = get_airtable_agent()
        schema = agent.get_schema(table)
        
        if schema:
            return SchemaResponse(success=True, schema=schema)
        else:
            raise HTTPException(status_code=404, detail=f"Table '{table}' not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get schema for {table}: {e}")
        return SchemaResponse(success=False, schema=None, error=str(e))


@app.get("/airtable/tables", response_model=TablesResponse)
async def list_tables(api_key: str = Depends(verify_api_key)):
    """Get list of all tables."""
    try:
        agent = get_airtable_agent()
        tables = agent.get_tables()
        
        return TablesResponse(success=True, tables=tables)
    except Exception as e:
        logger.error(f"Failed to list tables: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========================================================================
# CONVERSATIONAL INTERFACE
# ========================================================================

@app.post("/airtable/query", response_model=QueryResponse)
async def natural_language_query(
    request: QueryRequest,
    api_key: str = Depends(verify_api_key)
):
    """Process natural language query."""
    try:
        agent = get_airtable_agent()
        response = agent.ask(request.query, request.conversation_history)
        
        return QueryResponse(
            success=True,
            response=response,
            conversation_id=None  # Could implement session tracking
        )
    except Exception as e:
        logger.error(f"Natural language query failed: {e}")
        return QueryResponse(success=False, response=f"Error: {str(e)}")


# ========================================================================
# ADVANCED QUERY
# ========================================================================

@app.post("/airtable/query/advanced", response_model=RecordsResponse)
async def advanced_query(
    request: AdvancedQueryRequest,
    api_key: str = Depends(verify_api_key)
):
    """Execute advanced structured query."""
    try:
        agent = get_airtable_agent()
        
        if request.search_term:
            records = agent.search(
                request.table,
                request.search_term,
                request.search_fields
            )
        else:
            records = agent.query(
                request.table,
                filters=request.filters,
                formula=request.formula,
                max_records=request.max_records,
                sort=request.sort
            )
        
        return RecordsResponse(
            success=True,
            count=len(records),
            records=records,
            has_more=False  # Could implement pagination
        )
    except Exception as e:
        logger.error(f"Advanced query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========================================================================
# CRUD ENDPOINTS
# ========================================================================

@app.get("/airtable/{table}", response_model=RecordsResponse)
async def list_records(
    table: str,
    max_records: int = 100,
    api_key: str = Depends(verify_api_key)
):
    """List records from a table."""
    try:
        agent = get_airtable_agent()
        records = agent.query(table, max_records=max_records)
        
        return RecordsResponse(
            success=True,
            count=len(records),
            records=records,
            has_more=False
        )
    except Exception as e:
        logger.error(f"List records failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/airtable/{table}/{record_id}", response_model=RecordResponse)
async def get_record_by_id(
    table: str,
    record_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Get a single record by ID."""
    try:
        agent = get_airtable_agent()
        record = agent.get(table, record_id)
        
        if record:
            return RecordResponse(success=True, record=record)
        else:
            raise HTTPException(status_code=404, detail="Record not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get record failed: {e}")
        return RecordResponse(success=False, error=str(e))


@app.post("/airtable/{table}", response_model=RecordResponse)
async def create_record_endpoint(
    table: str,
    request: RecordCreateRequest,
    api_key: str = Depends(verify_api_key)
):
    """Create a new record."""
    try:
        agent = get_airtable_agent()
        record = agent.create(
            table,
            request.fields,
            initiated_by=request.initiated_by,
            reason=request.reason
        )
        
        return RecordResponse(success=True, record=record)
    except Exception as e:
        logger.error(f"Create record failed: {e}")
        return RecordResponse(success=False, error=str(e))


@app.put("/airtable/{table}/{record_id}", response_model=RecordResponse)
async def update_record_endpoint(
    table: str,
    record_id: str,
    request: RecordUpdateRequest,
    api_key: str = Depends(verify_api_key)
):
    """Update an existing record."""
    try:
        agent = get_airtable_agent()
        record = agent.update(
            table,
            record_id,
            request.fields,
            replace=request.replace,
            initiated_by=request.initiated_by,
            reason=request.reason
        )
        
        return RecordResponse(success=True, record=record)
    except Exception as e:
        logger.error(f"Update record failed: {e}")
        return RecordResponse(success=False, error=str(e))


@app.delete("/airtable/{table}/{record_id}")
async def delete_record_endpoint(
    table: str,
    record_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Delete a record (requires confirmation)."""
    # For safety, delete operations require explicit confirmation
    raise HTTPException(
        status_code=501,
        detail="Single record delete not implemented. Use bulk delete with confirmation."
    )


# ========================================================================
# BULK OPERATIONS
# ========================================================================

@app.post("/airtable/bulk/create", response_model=BulkOperationResponse)
async def bulk_create_endpoint(
    request: BulkCreateRequest,
    api_key: str = Depends(verify_api_key)
):
    """Create multiple records in batch."""
    try:
        agent = get_airtable_agent()
        result = agent.bulk_create(
            request.table,
            request.records,
            batch_size=request.batch_size,
            validate=request.validate,
            initiated_by=request.initiated_by,
            reason=request.reason
        )
        
        return BulkOperationResponse(
            success=result.success_count == result.total_count,
            successful=result.successful,
            failed=result.failed,
            errors=result.errors,
            success_count=result.success_count,
            failure_count=result.failure_count,
            total_count=result.total_count,
            success_rate=result.success_rate
        )
    except Exception as e:
        logger.error(f"Bulk create failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/airtable/bulk/update", response_model=BulkOperationResponse)
async def bulk_update_endpoint(
    request: BulkUpdateRequest,
    api_key: str = Depends(verify_api_key)
):
    """Update multiple records in batch."""
    try:
        agent = get_airtable_agent()
        result = agent.bulk_update(
            request.table,
            request.updates,
            batch_size=request.batch_size,
            validate=request.validate,
            replace=request.replace,
            initiated_by=request.initiated_by,
            reason=request.reason
        )
        
        return BulkOperationResponse(
            success=result.success_count == result.total_count,
            successful=result.successful,
            failed=result.failed,
            errors=result.errors,
            success_count=result.success_count,
            failure_count=result.failure_count,
            total_count=result.total_count,
            success_rate=result.success_rate
        )
    except Exception as e:
        logger.error(f"Bulk update failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/airtable/bulk/delete", response_model=BulkOperationResponse)
async def bulk_delete_endpoint(
    request: BulkDeleteRequest,
    api_key: str = Depends(verify_api_key)
):
    """Delete multiple records in batch (requires confirmation)."""
    if not request.confirm:
        raise HTTPException(
            status_code=400,
            detail="Bulk delete requires explicit confirmation (set confirm=true)"
        )
    
    try:
        agent = get_airtable_agent()
        result = agent.bulk_delete(
            request.table,
            request.record_ids,
            batch_size=request.batch_size,
            initiated_by=request.initiated_by,
            reason=request.reason
        )
        
        return BulkOperationResponse(
            success=result.success_count == result.total_count,
            successful=result.successful,
            failed=result.failed,
            errors=result.errors,
            success_count=result.success_count,
            failure_count=result.failure_count,
            total_count=result.total_count,
            success_rate=result.success_rate
        )
    except Exception as e:
        logger.error(f"Bulk delete failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/airtable/bulk/upsert", response_model=BulkOperationResponse)
async def upsert_endpoint(
    request: UpsertRequest,
    api_key: str = Depends(verify_api_key)
):
    """Upsert (update or insert) records based on key field."""
    try:
        agent = get_airtable_agent()
        result = agent.upsert(
            request.table,
            request.records,
            request.key_field,
            batch_size=request.batch_size,
            initiated_by=request.initiated_by,
            reason=request.reason
        )
        
        return BulkOperationResponse(
            success=result.success_count == result.total_count,
            successful=result.successful,
            failed=result.failed,
            errors=result.errors,
            success_count=result.success_count,
            failure_count=result.failure_count,
            total_count=result.total_count,
            success_rate=result.success_rate
        )
    except Exception as e:
        logger.error(f"Upsert failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========================================================================
# EXPORT
# ========================================================================

@app.post("/airtable/export", response_model=ExportResponse)
async def export_data_endpoint(
    request: ExportRequest,
    api_key: str = Depends(verify_api_key)
):
    """Export data in various formats."""
    try:
        agent = get_airtable_agent()
        data = agent.export(request.table, request.format, request.filters)
        
        # Determine filename
        filename = f"{request.table}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{request.format}"
        
        return ExportResponse(
            success=True,
            format=request.format,
            record_count=0,  # Could count from data
            data=data,
            filename=filename
        )
    except Exception as e:
        logger.error(f"Export failed: {e}")
        return ExportResponse(
            success=False,
            format=request.format,
            record_count=0,
            data="",
            error=str(e)
        )


# ========================================================================
# ANALYTICS
# ========================================================================

@app.post("/airtable/analytics", response_model=AnalyticsResponse)
async def analytics_endpoint(
    request: AnalyticsRequest,
    api_key: str = Depends(verify_api_key)
):
    """Run analytics query."""
    try:
        agent = get_airtable_agent()
        result = agent.aggregate(
            request.table,
            request.agg_type,
            request.field,
            group_by=request.group_by,
            filters=request.filters
        )
        
        return AnalyticsResponse(success=True, result=result)
    except Exception as e:
        logger.error(f"Analytics failed: {e}")
        return AnalyticsResponse(success=False, result=None, error=str(e))


# ========================================================================
# ERROR HANDLERS
# ========================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "error": exc.detail}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)

