#!/usr/bin/env python3
"""
Test script for the Customer Service Confirmation System.
This script helps verify that all components are working correctly.
"""

import os
import sys
from dotenv import load_dotenv
from loguru import logger

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config
from asana_client import AsanaClient
from twilio_client import TwilioClient
from call_manager import CallManager

load_dotenv()

class SystemTester:
    def __init__(self):
        self.asana_client = AsanaClient()
        self.twilio_client = TwilioClient()
        self.call_manager = CallManager()
    
    def test_configuration(self):
        """Test configuration validation"""
        print("Testing configuration...")
        
        if Config.validate_config():
            print("✅ Configuration is valid")
            return True
        else:
            print("❌ Configuration is invalid")
            return False
    
    def test_asana_connection(self):
        """Test Asana API connection"""
        print("Testing Asana connection...")
        
        try:
            # Test basic API access
            workspace = self.asana_client.client.workspaces.find_by_id(Config.ASANA_WORKSPACE_ID)
            print(f"✅ Connected to Asana workspace: {workspace['name']}")
            
            # Test project access
            project = self.asana_client.client.projects.find_by_id(Config.ASANA_PROJECT_ID)
            print(f"✅ Access to project: {project['name']}")
            
            # Test custom fields
            custom_fields = self.asana_client.client.custom_fields.find_by_workspace(
                Config.ASANA_WORKSPACE_ID
            )
            print(f"✅ Found {len(custom_fields)} custom fields in workspace")
            
            return True
            
        except Exception as e:
            print(f"❌ Asana connection failed: {e}")
            return False
    
    def test_twilio_connection(self):
        """Test Twilio API connection"""
        print("Testing Twilio connection...")
        
        try:
            # Test account access
            account = self.twilio_client.client.api.accounts(Config.TWILIO_ACCOUNT_SID).fetch()
            print(f"✅ Connected to Twilio account: {account.friendly_name}")
            
            # Test phone number access
            phone_numbers = self.twilio_client.client.incoming_phone_numbers.list()
            if phone_numbers:
                print(f"✅ Found {len(phone_numbers)} phone numbers")
            else:
                print("⚠️  No phone numbers found")
            
            return True
            
        except Exception as e:
            print(f"❌ Twilio connection failed: {e}")
            return False
    
    def test_asana_tasks(self):
        """Test Asana task operations"""
        print("Testing Asana task operations...")
        
        try:
            # Get tasks for confirmation
            tasks = self.asana_client.get_tasks_for_confirmation()
            print(f"✅ Found {len(tasks)} tasks for confirmation")
            
            if tasks:
                # Test with first task
                task = tasks[0]
                print(f"   Sample task: {task.task_id} - {task.customer_phone} - {task.operation_mode.value}")
            
            return True
            
        except Exception as e:
            print(f"❌ Asana task operations failed: {e}")
            return False
    
    def test_twilio_twiml(self):
        """Test Twilio TwiML generation"""
        print("Testing Twilio TwiML generation...")
        
        try:
            from models import OperationMode
            
            # Test pickup TwiML
            pickup_twiml = self.twilio_client.generate_twiml(OperationMode.PICKUP, "test_task_id")
            print("✅ Generated pickup TwiML")
            
            # Test delivery TwiML
            delivery_twiml = self.twilio_client.generate_twiml(OperationMode.DELIVERY, "test_task_id")
            print("✅ Generated delivery TwiML")
            
            # Test gather response
            gather_response = self.twilio_client.generate_gather_response("test_task_id", "yes")
            print("✅ Generated gather response")
            
            return True
            
        except Exception as e:
            print(f"❌ Twilio TwiML generation failed: {e}")
            return False
    
    def test_webhook_url(self):
        """Test webhook URL accessibility"""
        print("Testing webhook URL...")
        
        webhook_url = Config.WEBHOOK_URL
        if webhook_url.startswith('http'):
            print(f"✅ Webhook URL configured: {webhook_url}")
            return True
        else:
            print(f"⚠️  Webhook URL may not be publicly accessible: {webhook_url}")
            return False
    
    def test_call_manager(self):
        """Test call manager functionality"""
        print("Testing call manager...")
        
        try:
            # Test pending calls count
            pending_count = self.call_manager.get_pending_calls_count()
            print(f"✅ Call manager initialized, pending calls: {pending_count}")
            
            return True
            
        except Exception as e:
            print(f"❌ Call manager test failed: {e}")
            return False
    
    def run_all_tests(self):
        """Run all tests"""
        print("Customer Service Confirmation System - Test Suite")
        print("=" * 60)
        
        tests = [
            ("Configuration", self.test_configuration),
            ("Asana Connection", self.test_asana_connection),
            ("Twilio Connection", self.test_twilio_connection),
            ("Asana Tasks", self.test_asana_tasks),
            ("Twilio TwiML", self.test_twilio_twiml),
            ("Webhook URL", self.test_webhook_url),
            ("Call Manager", self.test_call_manager),
        ]
        
        results = []
        
        for test_name, test_func in tests:
            print(f"\n{test_name}:")
            try:
                result = test_func()
                results.append((test_name, result))
            except Exception as e:
                print(f"❌ {test_name} test failed with exception: {e}")
                results.append((test_name, False))
        
        # Summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name}: {status}")
        
        print(f"\nOverall: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! Your system is ready to use.")
        else:
            print("⚠️  Some tests failed. Please check the configuration and try again.")
        
        return passed == total

def main():
    tester = SystemTester()
    success = tester.run_all_tests()
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main() 