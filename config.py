import os
from dotenv import load_dotenv
from typing import Dict, Any

load_dotenv()

class Config:
    # Asana Configuration
    ASANA_ACCESS_TOKEN = os.getenv('ASANA_ACCESS_TOKEN')
    ASANA_WORKSPACE_ID = os.getenv('ASANA_WORKSPACE_ID')
    ASANA_PROJECT_ID = os.getenv('ASANA_PROJECT_ID')  # "Outbound Calls" project ID
    
    # Twilio Configuration
    TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
    TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')
    
    # Application Configuration
    WEBHOOK_URL = os.getenv('WEBHOOK_URL', 'http://localhost:5000/webhook')
    RETRY_DELAY_HOURS = int(os.getenv('RETRY_DELAY_HOURS', '1'))
    MAX_RETRY_ATTEMPTS = int(os.getenv('MAX_RETRY_ATTEMPTS', '3'))
    
    # Asana Custom Fields
    CUSTOM_FIELDS = {
        'phone_number': os.getenv('ASANA_PHONE_FIELD_ID'),
        'operation_mode': os.getenv('ASANA_OPERATION_MODE_FIELD_ID'),
        'retry_count': os.getenv('ASANA_RETRY_COUNT_FIELD_ID'),
        'last_call_time': os.getenv('ASANA_LAST_CALL_TIME_FIELD_ID'),
        'call_outcome': os.getenv('ASANA_CALL_OUTCOME_FIELD_ID')
    }
    
    # Asana Status IDs
    STATUS_IDS = {
        'confirmed': os.getenv('ASANA_STATUS_CONFIRMED_ID'),
        'customer_unavailable': os.getenv('ASANA_STATUS_UNAVAILABLE_ID'),
        'pending_confirmation': os.getenv('ASANA_STATUS_PENDING_ID')
    }
    
    # Operation Modes
    OPERATION_MODES = {
        'pickup': 'pickup',
        'delivery': 'delivery'
    }
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate that all required configuration is present"""
        required_fields = [
            'ASANA_ACCESS_TOKEN',
            'ASANA_WORKSPACE_ID', 
            'ASANA_PROJECT_ID',
            'TWILIO_ACCOUNT_SID',
            'TWILIO_AUTH_TOKEN',
            'TWILIO_PHONE_NUMBER'
        ]
        
        missing_fields = [field for field in required_fields if not getattr(cls, field)]
        
        if missing_fields:
            print(f"Missing required environment variables: {missing_fields}")
            return False
            
        return True 