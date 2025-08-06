from flask import Flask, request, Response
from loguru import logger
from config import Config
from models import CallOutcome, OperationMode, WebhookEvent
from call_manager import CallManager
from twilio_client import TwilioClient
import threading

app = Flask(__name__)
call_manager = CallManager()
twilio_client = TwilioClient()

@app.route('/webhook', methods=['POST'])
def webhook():
    """Main webhook endpoint for Twilio calls"""
    try:
        task_id = request.args.get('task_id')
        if not task_id:
            logger.error("No task_id provided in webhook")
            return Response("Missing task_id", status=400)
        
        # Get task details from Asana
        task = call_manager.asana_client.get_task_by_id(task_id)
        if not task:
            logger.error(f"Task {task_id} not found")
            return Response("Task not found", status=404)
        
        # Generate TwiML based on operation mode
        twiml = twilio_client.generate_twiml(task.operation_mode, task_id)
        
        logger.info(f"Generated TwiML for task {task_id}")
        return Response(twiml, mimetype='text/xml')
        
    except Exception as e:
        logger.error(f"Error in webhook: {e}")
        return Response("Internal server error", status=500)

@app.route('/gather', methods=['POST'])
def gather():
    """Handle user input from Gather verb"""
    try:
        task_id = request.args.get('task_id')
        speech_result = request.form.get('SpeechResult')
        digits = request.form.get('Digits')
        
        if not task_id:
            logger.error("No task_id provided in gather")
            return Response("Missing task_id", status=400)
        
        # Generate response based on user input
        twiml = twilio_client.generate_gather_response(task_id, speech_result, digits)
        
        logger.info(f"Generated gather response for task {task_id}: speech={speech_result}, digits={digits}")
        return Response(twiml, mimetype='text/xml')
        
    except Exception as e:
        logger.error(f"Error in gather: {e}")
        return Response("Internal server error", status=500)

@app.route('/complete', methods=['POST'])
def complete():
    """Handle call completion"""
    try:
        task_id = request.args.get('task_id')
        outcome = request.args.get('outcome')
        
        if not task_id:
            logger.error("No task_id provided in complete")
            return Response("Missing task_id", status=400)
        
        # Map outcome to CallOutcome enum
        call_outcome = None
        if outcome == 'confirmed':
            call_outcome = CallOutcome.CONFIRMED
        elif outcome == 'declined':
            call_outcome = CallOutcome.DECLINED
        elif outcome == 'reschedule':
            call_outcome = CallOutcome.DECLINED  # Treat reschedule as declined for now
        else:
            call_outcome = CallOutcome.NO_ANSWER
        
        # Handle call completion
        call_manager.handle_call_completion(task_id, call_outcome)
        
        logger.info(f"Completed call for task {task_id} with outcome {outcome}")
        return Response("OK", status=200)
        
    except Exception as e:
        logger.error(f"Error in complete: {e}")
        return Response("Internal server error", status=500)

@app.route('/status', methods=['POST'])
def status_callback():
    """Handle Twilio status callbacks"""
    try:
        # Parse webhook event
        event = WebhookEvent(
            CallSid=request.form.get('CallSid'),
            CallStatus=request.form.get('CallStatus'),
            CallDuration=request.form.get('CallDuration'),
            RecordingUrl=request.form.get('RecordingUrl'),
            task_id=request.form.get('task_id')
        )
        
        logger.info(f"Status callback for call {event.CallSid}: {event.CallStatus}")
        
        # Determine call outcome from status
        duration = int(event.CallDuration) if event.CallDuration else None
        outcome = call_manager.get_call_outcome_from_status(event.CallStatus, duration)
        
        # Handle call completion
        call_manager.handle_call_completion(event.CallSid, outcome)
        
        return Response("OK", status=200)
        
    except Exception as e:
        logger.error(f"Error in status callback: {e}")
        return Response("Internal server error", status=500)

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return {
        'status': 'healthy',
        'pending_calls': call_manager.get_pending_calls_count()
    }

@app.route('/tasks', methods=['GET'])
def get_tasks():
    """Get all tasks for confirmation"""
    try:
        tasks = call_manager.asana_client.get_tasks_for_confirmation()
        return {
            'tasks': [
                {
                    'task_id': task.task_id,
                    'customer_phone': task.customer_phone,
                    'operation_mode': task.operation_mode.value,
                    'retry_count': task.retry_count
                }
                for task in tasks
            ]
        }
    except Exception as e:
        logger.error(f"Error getting tasks: {e}")
        return Response("Internal server error", status=500)

@app.route('/process', methods=['POST'])
def process_tasks():
    """Manually trigger task processing"""
    try:
        call_manager.process_confirmation_tasks()
        return {'message': 'Task processing completed'}
    except Exception as e:
        logger.error(f"Error processing tasks: {e}")
        return Response("Internal server error", status=500)

def start_webhook_server(host='0.0.0.0', port=5000, debug=False):
    """Start the webhook server"""
    logger.info(f"Starting webhook server on {host}:{port}")
    app.run(host=host, port=port, debug=debug)

if __name__ == '__main__':
    # Validate configuration
    if not Config.validate_config():
        logger.error("Invalid configuration. Please check your environment variables.")
        exit(1)
    
    # Start webhook server
    start_webhook_server() 