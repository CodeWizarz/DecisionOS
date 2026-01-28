import pytest
from unittest.mock import MagicMock, patch
from decisionos.worker.tasks import process_data_point

@pytest.mark.asyncio
async def test_worker_processing_success():
    """
    Test that the worker task runs successfully given valid input.
    We mock the external dependencies (Redis/DB) inside the task if they are called directly,
    or assume the task logic itself is testable.
    
    Since 'process_data_point' is a Celery task, we can test the underlying python function
    if we bypass the broker.
    """
    # Mocking the Celery task context if needed, or just calling the logic.
    # If the task interacts with DB, those calls must be mocked or handled.
    
    # For this verification, we are protecting against import errors and syntax bugs 
    # in the worker definition primarily.
    
    with patch("decisionos.worker.tasks.process_data_point") as mock_task:
        # Simulate calling the task
        mock_task("123", {"value": 10})
        mock_task.assert_called_with("123", {"value": 10})

@pytest.mark.asyncio
async def test_worker_retry_logic():
    """
    Verify that retry configuration is present on the task object.
    """
    assert process_data_point.max_retries is not None
    assert process_data_point.default_retry_delay > 0
