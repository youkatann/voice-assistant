import threading
import time
from loguru import logger
from config import Config
from call_manager import CallManager
from webhook_server import start_webhook_server

def main():
    """Main application entry point"""
    # Configure logging
    logger.add("logs/app.log", rotation="1 day", retention="7 days", level="INFO")
    
    # Validate configuration
    if not Config.validate_config():
        logger.error("Invalid configuration. Please check your environment variables.")
        return
    
    logger.info("Starting Customer Service Confirmation System")
    
    # Initialize call manager
    call_manager = CallManager()
    
    # Start scheduler in a separate thread
    scheduler_thread = threading.Thread(
        target=call_manager.run_scheduler,
        daemon=True
    )
    scheduler_thread.start()
    
    # Start webhook server in a separate thread
    webhook_thread = threading.Thread(
        target=start_webhook_server,
        kwargs={'host': '0.0.0.0', 'port': 5000, 'debug': False},
        daemon=True
    )
    webhook_thread.start()
    
    logger.info("System started successfully")
    logger.info("Webhook server running on http://localhost:5000")
    logger.info("Scheduler running for retry management")
    
    try:
        # Main loop - process tasks periodically
        while True:
            logger.info("Processing confirmation tasks...")
            call_manager.process_confirmation_tasks()
            
            # Wait for 5 minutes before next processing cycle
            time.sleep(300)
            
    except KeyboardInterrupt:
        logger.info("Shutting down system...")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        logger.info("System shutdown complete")

if __name__ == "__main__":
    main() 