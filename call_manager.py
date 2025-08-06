import schedule
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from loguru import logger
from config import Config
from models import TaskData, CallRequest, CallOutcome, OperationMode
from asana_client import AsanaClient
from twilio_client import TwilioClient

class CallManager:
    def __init__(self):
        self.asana_client = AsanaClient()
        self.twilio_client = TwilioClient()
        self.pending_calls: Dict[str, TaskData] = {}
        
    def process_confirmation_tasks(self):
        """Process all tasks that need confirmation calls"""
        try:
            tasks = self.asana_client.get_tasks_for_confirmation()
            logger.info(f"Found {len(tasks)} tasks for confirmation")
            
            for task in tasks:
                self.process_single_task(task)
                
        except Exception as e:
            logger.error(f"Error processing confirmation tasks: {e}")
    
    def process_single_task(self, task: TaskData):
        """Process a single task for confirmation"""
        try:
            # Check if task has exceeded max retry attempts
            if task.retry_count >= Config.MAX_RETRY_ATTEMPTS:
                logger.info(f"Task {task.task_id} has exceeded max retry attempts")
                self.asana_client.update_task_status(task.task_id, 'customer_unavailable')
                return
            
            # Check if enough time has passed since last call
            if task.last_call_time:
                time_since_last_call = datetime.now() - task.last_call_time
                if time_since_last_call < timedelta(hours=Config.RETRY_DELAY_HOURS):
                    logger.info(f"Task {task.task_id} is not ready for retry yet")
                    return
            
            # Make the call
            call_request = CallRequest(
                task_id=task.task_id,
                phone_number=task.customer_phone,
                operation_mode=task.operation_mode,
                webhook_url=Config.WEBHOOK_URL
            )
            
            call_sid = self.twilio_client.make_call(call_request)
            
            if call_sid:
                # Update task with call information
                self.asana_client.update_task_fields(task.task_id, {
                    'last_call_time': datetime.now().isoformat(),
                    'call_sid': call_sid
                })
                
                # Store task in pending calls
                self.pending_calls[call_sid] = task
                
                logger.info(f"Initiated call {call_sid} for task {task.task_id}")
            else:
                logger.error(f"Failed to initiate call for task {task.task_id}")
                
        except Exception as e:
            logger.error(f"Error processing task {task.task_id}: {e}")
    
    def handle_call_completion(self, call_sid: str, outcome: CallOutcome, transcript: str = None):
        """Handle call completion and update task accordingly"""
        try:
            task = self.pending_calls.get(call_sid)
            if not task:
                logger.warning(f"No task found for call {call_sid}")
                return
            
            # Remove from pending calls
            del self.pending_calls[call_sid]
            
            # Update task with call outcome
            self.asana_client.update_task_fields(task.task_id, {
                'call_outcome': outcome.value
            })
            
            # Attach transcript if available
            if transcript:
                self.asana_client.attach_transcript(task.task_id, transcript, call_sid)
            
            # Handle different outcomes
            if outcome == CallOutcome.CONFIRMED:
                self.asana_client.update_task_status(task.task_id, 'confirmed')
                logger.info(f"Task {task.task_id} confirmed successfully")
                
            elif outcome == CallOutcome.DECLINED:
                self.asana_client.update_task_status(task.task_id, 'customer_unavailable')
                logger.info(f"Task {task.task_id} declined by customer")
                
            elif outcome in [CallOutcome.NO_ANSWER, CallOutcome.BUSY, CallOutcome.FAILED]:
                # Increment retry count
                self.asana_client.increment_retry_count(task.task_id)
                
                # Check if max retries reached
                if task.retry_count + 1 >= Config.MAX_RETRY_ATTEMPTS:
                    self.asana_client.update_task_status(task.task_id, 'customer_unavailable')
                    logger.info(f"Task {task.task_id} moved to unavailable after max retries")
                else:
                    # Schedule retry
                    self.schedule_retry(task.task_id)
                    logger.info(f"Scheduled retry for task {task.task_id}")
                    
        except Exception as e:
            logger.error(f"Error handling call completion: {e}")
    
    def schedule_retry(self, task_id: str):
        """Schedule a retry for a task"""
        try:
            # Schedule retry in 1 hour
            retry_time = datetime.now() + timedelta(hours=Config.RETRY_DELAY_HOURS)
            
            schedule.every().day.at(retry_time.strftime("%H:%M")).do(
                self.retry_task, task_id
            )
            
            logger.info(f"Scheduled retry for task {task_id} at {retry_time}")
            
        except Exception as e:
            logger.error(f"Error scheduling retry for task {task_id}: {e}")
    
    def retry_task(self, task_id: str):
        """Retry a specific task"""
        try:
            task = self.asana_client.get_task_by_id(task_id)
            if task:
                self.process_single_task(task)
            else:
                logger.warning(f"Task {task_id} not found for retry")
                
        except Exception as e:
            logger.error(f"Error retrying task {task_id}: {e}")
    
    def run_scheduler(self):
        """Run the scheduler to handle retries"""
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def get_call_outcome_from_status(self, call_status: str, duration: int = None) -> CallOutcome:
        """Determine call outcome from Twilio call status"""
        if call_status == 'completed' and duration and duration > 0:
            return CallOutcome.CONFIRMED
        elif call_status == 'busy':
            return CallOutcome.BUSY
        elif call_status == 'no-answer':
            return CallOutcome.NO_ANSWER
        elif call_status == 'failed':
            return CallOutcome.FAILED
        else:
            return CallOutcome.NO_ANSWER
    
    def get_pending_calls_count(self) -> int:
        """Get the number of pending calls"""
        return len(self.pending_calls)
    
    def get_pending_calls(self) -> Dict[str, TaskData]:
        """Get all pending calls"""
        return self.pending_calls.copy() 