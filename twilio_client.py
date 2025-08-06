from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather
from typing import Optional, Dict, Any
from loguru import logger
from config import Config
from models import CallRequest, OperationMode

class TwilioClient:
    def __init__(self):
        self.client = Client(Config.TWILIO_ACCOUNT_SID, Config.TWILIO_AUTH_TOKEN)
        self.from_number = Config.TWILIO_PHONE_NUMBER
        
    def make_call(self, call_request: CallRequest) -> Optional[str]:
        """Initiate a voice call"""
        try:
            # Create webhook URL with task_id parameter
            webhook_url = f"{call_request.webhook_url}?task_id={call_request.task_id}"
            
            call = self.client.calls.create(
                to=call_request.phone_number,
                from_=self.from_number,
                url=webhook_url,
                record=True,  # Record the call
                status_callback=f"{call_request.webhook_url}/status",
                status_callback_event=['completed'],
                status_callback_method='POST'
            )
            
            logger.info(f"Initiated call {call.sid} to {call_request.phone_number} for task {call_request.task_id}")
            return call.sid
            
        except Exception as e:
            logger.error(f"Error making call: {e}")
            return None
    
    def generate_twiml(self, operation_mode: OperationMode, task_id: str) -> str:
        """Generate TwiML for the call based on operation mode"""
        response = VoiceResponse()
        
        # Add a brief pause before starting
        response.pause(length=1)
        
        if operation_mode == OperationMode.PICKUP:
            # Pickup confirmation script
            gather = Gather(
                input='speech dtmf',
                timeout=10,
                speech_timeout='auto',
                action=f'/gather?task_id={task_id}',
                method='POST'
            )
            
            gather.say(
                "Hello, this is a call to confirm your pickup request. "
                "Please confirm by saying 'yes' or pressing 1. "
                "To decline, say 'no' or press 2. "
                "If you need to reschedule, say 'reschedule' or press 3.",
                voice='alice',
                language='en-US'
            )
            
            response.append(gather)
            
        elif operation_mode == OperationMode.DELIVERY:
            # Delivery confirmation script
            gather = Gather(
                input='speech dtmf',
                timeout=10,
                speech_timeout='auto',
                action=f'/gather?task_id={task_id}',
                method='POST'
            )
            
            gather.say(
                "Hello, this is a call to confirm your delivery request. "
                "Please confirm by saying 'yes' or pressing 1. "
                "To decline, say 'no' or press 2. "
                "If you need to reschedule, say 'reschedule' or press 3.",
                voice='alice',
                language='en-US'
            )
            
            response.append(gather)
        
        # If no input is received, repeat the message
        response.say(
            "We didn't receive your response. Please call back or contact customer service.",
            voice='alice',
            language='en-US'
        )
        
        return str(response)
    
    def generate_gather_response(self, task_id: str, speech_result: str = None, digits: str = None) -> str:
        """Generate response based on user input"""
        response = VoiceResponse()
        
        # Determine user's choice
        user_choice = None
        
        if speech_result:
            speech_lower = speech_result.lower()
            if 'yes' in speech_lower or 'confirm' in speech_lower:
                user_choice = 'confirmed'
            elif 'no' in speech_lower or 'decline' in speech_lower:
                user_choice = 'declined'
            elif 'reschedule' in speech_lower:
                user_choice = 'reschedule'
        elif digits:
            if digits == '1':
                user_choice = 'confirmed'
            elif digits == '2':
                user_choice = 'declined'
            elif digits == '3':
                user_choice = 'reschedule'
        
        # Provide appropriate response
        if user_choice == 'confirmed':
            response.say(
                "Thank you for confirming. Your request has been confirmed. "
                "You will receive a confirmation email shortly. Goodbye!",
                voice='alice',
                language='en-US'
            )
        elif user_choice == 'declined':
            response.say(
                "We understand you need to decline. Your request has been cancelled. "
                "If you change your mind, please contact customer service. Goodbye!",
                voice='alice',
                language='en-US'
            )
        elif user_choice == 'reschedule':
            response.say(
                "We understand you need to reschedule. Please contact customer service "
                "to arrange a new time. Thank you for your patience. Goodbye!",
                voice='alice',
                language='en-US'
            )
        else:
            response.say(
                "We didn't understand your response. Please contact customer service "
                "for assistance. Goodbye!",
                voice='alice',
                language='en-US'
            )
        
        # Store the outcome for processing
        response.say(
            f"<Redirect method='POST'>{Config.WEBHOOK_URL}/complete?task_id={task_id}&outcome={user_choice}</Redirect>",
            voice='alice',
            language='en-US'
        )
        
        return str(response)
    
    def get_call_details(self, call_sid: str) -> Optional[Dict[str, Any]]:
        """Get details about a specific call"""
        try:
            call = self.client.calls(call_sid).fetch()
            
            return {
                'sid': call.sid,
                'status': call.status,
                'duration': call.duration,
                'start_time': call.start_time,
                'end_time': call.end_time,
                'price': call.price,
                'price_unit': call.price_unit
            }
            
        except Exception as e:
            logger.error(f"Error getting call details: {e}")
            return None
    
    def get_call_recordings(self, call_sid: str) -> list:
        """Get recordings for a specific call"""
        try:
            recordings = self.client.recordings.list(call_sid=call_sid)
            return [recording.uri for recording in recordings]
            
        except Exception as e:
            logger.error(f"Error getting call recordings: {e}")
            return [] 