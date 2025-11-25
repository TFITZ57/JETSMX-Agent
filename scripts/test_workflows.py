"""
Test JetsMX Agent workflows manually.
"""
from agents.applicant_analysis.agent import get_applicant_analysis_agent
from agents.hr_pipeline.agent import get_hr_pipeline_agent
from agents.company_kb.agent import get_company_kb_agent
from shared.logging.logger import setup_logger

logger = setup_logger(__name__)


def test_applicant_analysis():
    """Test the applicant analysis workflow."""
    logger.info("Testing Applicant Analysis Agent...")
    
    # Example: process a resume
    # In production, this would be triggered by a Drive file upload
    test_file_id = "your_test_resume_file_id"
    test_filename = "test_resume.pdf"
    
    agent = get_applicant_analysis_agent()
    
    try:
        result = agent.process_resume(test_file_id, test_filename)
        
        if result['success']:
            logger.info(f"✓ Applicant Analysis successful")
            logger.info(f"  Applicant ID: {result['applicant_id']}")
            logger.info(f"  Pipeline ID: {result['pipeline_id']}")
            logger.info(f"  ICC File ID: {result['icc_file_id']}")
            logger.info(f"  Verdict: {result['baseline_verdict']}")
        else:
            logger.error(f"✗ Applicant Analysis failed: {result['error']}")
            
    except Exception as e:
        logger.error(f"✗ Test failed with exception: {str(e)}")


def test_hr_pipeline():
    """Test the HR pipeline agent."""
    logger.info("Testing HR Pipeline Agent...")
    
    # Example: generate outreach draft
    test_pipeline_id = "your_test_pipeline_id"
    
    agent = get_hr_pipeline_agent()
    
    try:
        result = agent.generate_outreach_draft(test_pipeline_id)
        
        if result['success']:
            logger.info(f"✓ Outreach draft generated")
            logger.info(f"  Draft ID: {result['draft_id']}")
        else:
            logger.error(f"✗ HR Pipeline failed: {result['error']}")
            
    except Exception as e:
        logger.error(f"✗ Test failed with exception: {str(e)}")


def test_company_kb():
    """Test the company KB agent."""
    logger.info("Testing Company KB Agent...")
    
    agent = get_company_kb_agent()
    
    test_questions = [
        "How many applicants do we have in the pipeline?",
        "What's the status of recent applicants?",
        "Find applicants with A&P licenses"
    ]
    
    for question in test_questions:
        try:
            logger.info(f"Question: {question}")
            answer = agent.query(question)
            logger.info(f"Answer: {answer}")
            logger.info("---")
        except Exception as e:
            logger.error(f"✗ Query failed: {str(e)}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python test_workflows.py [applicant_analysis|hr_pipeline|company_kb|all]")
        sys.exit(1)
    
    test_type = sys.argv[1].lower()
    
    if test_type == "applicant_analysis":
        test_applicant_analysis()
    elif test_type == "hr_pipeline":
        test_hr_pipeline()
    elif test_type == "company_kb":
        test_company_kb()
    elif test_type == "all":
        test_applicant_analysis()
        test_hr_pipeline()
        test_company_kb()
    else:
        print(f"Unknown test type: {test_type}")
        sys.exit(1)

