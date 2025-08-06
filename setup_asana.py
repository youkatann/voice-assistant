#!/usr/bin/env python3
"""
Setup script for Asana project configuration.
This script helps create the required custom fields and statuses in your Asana project.
"""

import asana
import os
from dotenv import load_dotenv
from typing import Dict, Any, Optional

load_dotenv()

class AsanaSetup:
    def __init__(self):
        self.client = asana.Client.access_token(os.getenv('ASANA_ACCESS_TOKEN'))
        self.workspace_id = os.getenv('ASANA_WORKSPACE_ID')
        self.project_id = os.getenv('ASANA_PROJECT_ID')
        
    def get_or_create_custom_field(self, field_name: str, field_type: str, **kwargs) -> Optional[str]:
        """Get existing custom field or create a new one"""
        try:
            # First, try to find existing field
            custom_fields = self.client.custom_fields.find_by_workspace(
                self.workspace_id,
                opt_fields=['gid', 'name', 'type']
            )
            
            for field in custom_fields:
                if field['name'] == field_name:
                    print(f"Found existing custom field: {field_name} (ID: {field['gid']})")
                    return field['gid']
            
            # Create new field if not found
            field_data = {
                'name': field_name,
                'type': field_type,
                'workspace': self.workspace_id
            }
            field_data.update(kwargs)
            
            new_field = self.client.custom_fields.create(**field_data)
            print(f"Created new custom field: {field_name} (ID: {new_field['gid']})")
            return new_field['gid']
            
        except Exception as e:
            print(f"Error with custom field {field_name}: {e}")
            return None
    
    def get_or_create_status(self, status_name: str, color: str = 'blue') -> Optional[str]:
        """Get existing status or create a new one"""
        try:
            # Get project sections (statuses)
            sections = self.client.sections.find_by_project(self.project_id)
            
            for section in sections:
                if section['name'] == status_name:
                    print(f"Found existing status: {status_name} (ID: {section['gid']})")
                    return section['gid']
            
            # Create new status if not found
            new_section = self.client.sections.create_in_project(
                self.project_id,
                {'name': status_name}
            )
            print(f"Created new status: {status_name} (ID: {new_section['gid']})")
            return new_section['gid']
            
        except Exception as e:
            print(f"Error with status {status_name}: {e}")
            return None
    
    def setup_custom_fields(self) -> Dict[str, str]:
        """Set up all required custom fields"""
        print("Setting up custom fields...")
        
        fields = {}
        
        # Phone Number field
        fields['phone_number'] = self.get_or_create_custom_field(
            'Phone Number',
            'text'
        )
        
        # Operation Mode field
        fields['operation_mode'] = self.get_or_create_custom_field(
            'Operation Mode',
            'enum',
            enum_options=[
                {'name': 'pickup', 'color': 'blue'},
                {'name': 'delivery', 'color': 'green'}
            ]
        )
        
        # Retry Count field
        fields['retry_count'] = self.get_or_create_custom_field(
            'Retry Count',
            'number'
        )
        
        # Last Call Time field
        fields['last_call_time'] = self.get_or_create_custom_field(
            'Last Call Time',
            'text'
        )
        
        # Call Outcome field
        fields['call_outcome'] = self.get_or_create_custom_field(
            'Call Outcome',
            'enum',
            enum_options=[
                {'name': 'confirmed', 'color': 'green'},
                {'name': 'declined', 'color': 'red'},
                {'name': 'no_answer', 'color': 'yellow'},
                {'name': 'busy', 'color': 'orange'},
                {'name': 'failed', 'color': 'red'}
            ]
        )
        
        return fields
    
    def setup_statuses(self) -> Dict[str, str]:
        """Set up all required statuses"""
        print("Setting up statuses...")
        
        statuses = {}
        
        # Confirmed status
        statuses['confirmed'] = self.get_or_create_status('Confirmed', 'green')
        
        # Customer Unavailable status
        statuses['customer_unavailable'] = self.get_or_create_status('Customer Unavailable', 'red')
        
        # Pending status
        statuses['pending'] = self.get_or_create_status('Pending Confirmation', 'yellow')
        
        return statuses
    
    def generate_env_config(self, fields: Dict[str, str], statuses: Dict[str, str]):
        """Generate environment configuration"""
        print("\n" + "="*50)
        print("ENVIRONMENT CONFIGURATION")
        print("="*50)
        print("Add these values to your .env file:")
        print()
        
        print("# Asana Custom Field IDs")
        for field_name, field_id in fields.items():
            if field_id:
                print(f"ASANA_{field_name.upper()}_FIELD_ID={field_id}")
        
        print("\n# Asana Status IDs")
        for status_name, status_id in statuses.items():
            if status_id:
                print(f"ASANA_STATUS_{status_name.upper()}_ID={status_id}")
        
        print("\n" + "="*50)
    
    def run_setup(self):
        """Run the complete setup process"""
        print("Asana Project Setup")
        print("="*50)
        
        # Validate configuration
        if not all([os.getenv('ASANA_ACCESS_TOKEN'), 
                   os.getenv('ASANA_WORKSPACE_ID'), 
                   os.getenv('ASANA_PROJECT_ID')]):
            print("Error: Missing required environment variables.")
            print("Please set ASANA_ACCESS_TOKEN, ASANA_WORKSPACE_ID, and ASANA_PROJECT_ID")
            return
        
        try:
            # Set up custom fields
            fields = self.setup_custom_fields()
            
            # Set up statuses
            statuses = self.setup_statuses()
            
            # Generate configuration
            self.generate_env_config(fields, statuses)
            
            print("\nSetup completed successfully!")
            print("Please copy the generated configuration to your .env file.")
            
        except Exception as e:
            print(f"Setup failed: {e}")

def main():
    setup = AsanaSetup()
    setup.run_setup()

if __name__ == "__main__":
    main() 