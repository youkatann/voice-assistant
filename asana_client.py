import asana
from typing import Dict, Any, Optional, List
from datetime import datetime
from loguru import logger
from config import Config
from models import TaskData, CallOutcome, OperationMode

class AsanaClient:
    def __init__(self):
        self.client = asana.Client.access_token(Config.ASANA_ACCESS_TOKEN)
        self.project_id = Config.ASANA_PROJECT_ID
        
    def get_tasks_for_confirmation(self) -> List[TaskData]:
        """Get all tasks that need confirmation calls"""
        try:
            # Get tasks from the Outbound Calls project
            tasks = self.client.tasks.find_by_project(
                self.project_id,
                opt_fields=['gid', 'name', 'custom_fields', 'completed', 'assignee']
            )
            
            confirmation_tasks = []
            
            for task in tasks:
                if task.get('completed'):
                    continue
                    
                # Extract custom field values
                custom_fields = {field['name']: field['text_value'] or field['number_value'] 
                               for field in task.get('custom_fields', [])}
                
                # Check if task has phone number and operation mode
                phone_number = custom_fields.get('Phone Number')
                operation_mode = custom_fields.get('Operation Mode')
                
                if phone_number and operation_mode:
                    try:
                        task_data = TaskData(
                            task_id=task['gid'],
                            customer_phone=phone_number,
                            operation_mode=OperationMode(operation_mode.lower()),
                            retry_count=custom_fields.get('Retry Count', 0),
                            custom_fields=custom_fields
                        )
                        confirmation_tasks.append(task_data)
                    except ValueError as e:
                        logger.warning(f"Invalid operation mode for task {task['gid']}: {operation_mode}")
                        
            return confirmation_tasks
            
        except Exception as e:
            logger.error(f"Error fetching tasks: {e}")
            return []
    
    def update_task_status(self, task_id: str, status_name: str) -> bool:
        """Update task status"""
        try:
            status_id = Config.STATUS_IDS.get(status_name)
            if not status_id:
                logger.error(f"Unknown status: {status_name}")
                return False
                
            self.client.tasks.update(
                task_id,
                {'custom_fields': {status_id: status_name}}
            )
            logger.info(f"Updated task {task_id} status to {status_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating task status: {e}")
            return False
    
    def update_task_fields(self, task_id: str, fields: Dict[str, Any]) -> bool:
        """Update task custom fields"""
        try:
            field_updates = {}
            for field_name, value in fields.items():
                field_id = Config.CUSTOM_FIELDS.get(field_name)
                if field_id:
                    field_updates[field_id] = value
                    
            if field_updates:
                self.client.tasks.update(
                    task_id,
                    {'custom_fields': field_updates}
                )
                logger.info(f"Updated task {task_id} fields: {fields}")
                return True
                
        except Exception as e:
            logger.error(f"Error updating task fields: {e}")
            
        return False
    
    def increment_retry_count(self, task_id: str) -> bool:
        """Increment the retry count for a task"""
        try:
            # Get current retry count
            task = self.client.tasks.find_by_id(task_id, opt_fields=['custom_fields'])
            current_count = 0
            
            for field in task.get('custom_fields', []):
                if field.get('name') == 'Retry Count':
                    current_count = field.get('number_value', 0)
                    break
                    
            new_count = current_count + 1
            return self.update_task_fields(task_id, {'retry_count': new_count})
            
        except Exception as e:
            logger.error(f"Error incrementing retry count: {e}")
            return False
    
    def attach_transcript(self, task_id: str, transcript: str, call_sid: str) -> bool:
        """Attach call transcript as a comment to the task"""
        try:
            comment_text = f"Call Transcript (Call SID: {call_sid}):\n\n{transcript}"
            
            self.client.stories.create_on_task(
                task_id,
                {'text': comment_text}
            )
            
            logger.info(f"Attached transcript to task {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error attaching transcript: {e}")
            return False
    
    def get_task_by_id(self, task_id: str) -> Optional[TaskData]:
        """Get a specific task by ID"""
        try:
            task = self.client.tasks.find_by_id(
                task_id, 
                opt_fields=['gid', 'name', 'custom_fields', 'completed']
            )
            
            if task.get('completed'):
                return None
                
            custom_fields = {field['name']: field['text_value'] or field['number_value'] 
                           for field in task.get('custom_fields', [])}
            
            return TaskData(
                task_id=task['gid'],
                customer_phone=custom_fields.get('Phone Number', ''),
                operation_mode=OperationMode(custom_fields.get('Operation Mode', 'pickup').lower()),
                retry_count=custom_fields.get('Retry Count', 0),
                custom_fields=custom_fields
            )
            
        except Exception as e:
            logger.error(f"Error fetching task {task_id}: {e}")
            return None 