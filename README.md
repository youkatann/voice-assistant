# Customer Service Confirmation System

A comprehensive system for automating customer pickup and delivery confirmations using Python, Twilio Voice, and Asana integration.

## Overview

This system automates the process of confirming customer pickup and delivery requests by:

1. **Reading customer phone numbers** from Asana tasks in the "Outbound Calls" project
2. **Making automated voice calls** using Twilio Voice with different scripts for pickup and delivery
3. **Handling call outcomes** and updating task statuses accordingly
4. **Managing retry logic** with configurable delays and maximum attempts
5. **Attaching call transcripts** to tasks for record keeping

## Features

- **Dual Operation Modes**: Separate scripts for pickup and delivery confirmations
- **Intelligent Retry Logic**: Automatic retries with configurable delays
- **Call Recording**: All calls are recorded and transcripts are attached to tasks
- **Status Management**: Automatic task status updates based on call outcomes
- **Webhook Integration**: Real-time call status updates via Twilio webhooks
- **Scheduling System**: Automated retry scheduling with configurable intervals

## System Architecture

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Asana     │    │   Python    │    │   Twilio    │
│   Tasks     │◄──►│   System    │◄──►│   Voice     │
└─────────────┘    └─────────────┘    └─────────────┘
                          │
                          ▼
                   ┌─────────────┐
                   │   Webhook   │
                   │   Server    │
                   └─────────────┘
```

## Prerequisites

- Python 3.8+
- Asana account with API access
- Twilio account with Voice capabilities
- Publicly accessible webhook URL (for production)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd JCA
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   ```bash
   cp env_example.txt .env
   # Edit .env with your actual values
   ```

4. **Create logs directory**:
   ```bash
   mkdir logs
   ```

## Configuration

### Environment Variables

Copy `env_example.txt` to `.env` and configure the following variables:

#### Asana Configuration
- `ASANA_ACCESS_TOKEN`: Your Asana API access token
- `ASANA_WORKSPACE_ID`: Your Asana workspace ID
- `ASANA_PROJECT_ID`: The "Outbound Calls" project ID

#### Twilio Configuration
- `TWILIO_ACCOUNT_SID`: Your Twilio account SID
- `TWILIO_AUTH_TOKEN`: Your Twilio auth token
- `TWILIO_PHONE_NUMBER`: Your Twilio phone number

#### Application Configuration
- `WEBHOOK_URL`: Public URL for webhook endpoints
- `RETRY_DELAY_HOURS`: Hours to wait between retries (default: 1)
- `MAX_RETRY_ATTEMPTS`: Maximum number of retry attempts (default: 3)

#### Asana Custom Fields
You need to create these custom fields in your Asana project and get their IDs:
- `ASANA_PHONE_FIELD_ID`: Field for customer phone number
- `ASANA_OPERATION_MODE_FIELD_ID`: Field for pickup/delivery mode
- `ASANA_RETRY_COUNT_FIELD_ID`: Field to track retry attempts
- `ASANA_LAST_CALL_TIME_FIELD_ID`: Field for last call timestamp
- `ASANA_CALL_OUTCOME_FIELD_ID`: Field for call outcome

#### Asana Status IDs
You need to create these statuses in your Asana project and get their IDs:
- `ASANA_STATUS_CONFIRMED_ID`: Status for confirmed requests
- `ASANA_STATUS_UNAVAILABLE_ID`: Status for unavailable customers
- `ASANA_STATUS_PENDING_ID`: Status for pending confirmations

## Usage

### Starting the System

```bash
python main.py
```

The system will:
1. Start the webhook server on port 5000
2. Start the scheduler for retry management
3. Begin processing tasks every 5 minutes

### Manual Operations

#### Process Tasks Manually
```bash
curl -X POST http://localhost:5000/process
```

#### Check System Health
```bash
curl http://localhost:5000/health
```

#### Get Pending Tasks
```bash
curl http://localhost:5000/tasks
```

### Webhook Endpoints

- `POST /webhook`: Main Twilio webhook for call initiation
- `POST /gather`: Handle user input during calls
- `POST /complete`: Handle call completion
- `POST /status`: Handle Twilio status callbacks

## Call Flow

1. **Task Detection**: System scans Asana project for tasks needing confirmation
2. **Call Initiation**: Twilio call is made to customer with appropriate script
3. **User Interaction**: Customer responds via voice or keypad
4. **Outcome Processing**: System determines call outcome and updates task
5. **Retry Logic**: If needed, schedules retry based on outcome

### Call Scripts

#### Pickup Confirmation
```
"Hello, this is a call to confirm your pickup request. 
Please confirm by saying 'yes' or pressing 1. 
To decline, say 'no' or pressing 2. 
If you need to reschedule, say 'reschedule' or press 3."
```

#### Delivery Confirmation
```
"Hello, this is a call to confirm your delivery request. 
Please confirm by saying 'yes' or pressing 1. 
To decline, say 'no' or pressing 2. 
If you need to reschedule, say 'reschedule' or press 3."
```

## Task Status Management

- **Confirmed**: Customer confirmed the request
- **Customer Unavailable**: Customer declined or max retries reached
- **Pending**: Awaiting confirmation or retry

## Retry Logic

- **Initial Call**: Made immediately when task is processed
- **Retry Delay**: 1 hour between attempts (configurable)
- **Max Attempts**: 3 total attempts (configurable)
- **Retry Triggers**: No answer, busy, failed calls

## Logging

Logs are stored in `logs/app.log` with daily rotation and 7-day retention.

## Development

### Project Structure

```
JCA/
├── main.py              # Main application entry point
├── config.py            # Configuration management
├── models.py            # Data models and enums
├── asana_client.py      # Asana API integration
├── twilio_client.py     # Twilio Voice integration
├── call_manager.py      # Call orchestration logic
├── webhook_server.py    # Flask webhook server
├── requirements.txt     # Python dependencies
├── env_example.txt      # Environment variables template
└── README.md           # This file
```

### Adding New Features

1. **New Operation Modes**: Add to `OperationMode` enum in `models.py`
2. **New Call Outcomes**: Add to `CallOutcome` enum in `models.py`
3. **Custom Scripts**: Modify `generate_twiml()` in `twilio_client.py`

## Troubleshooting

### Common Issues

1. **Webhook Not Accessible**: Ensure your webhook URL is publicly accessible
2. **Asana API Errors**: Verify your access token and project permissions
3. **Twilio Call Failures**: Check your Twilio credentials and phone number
4. **Missing Custom Fields**: Ensure all required Asana custom fields exist

### Debug Mode

Enable debug logging by modifying the log level in `main.py`:

```python
logger.add("logs/app.log", rotation="1 day", retention="7 days", level="DEBUG")
```

## Security Considerations

- Store sensitive credentials in environment variables
- Use HTTPS for webhook URLs in production
- Implement proper authentication for webhook endpoints
- Regularly rotate API tokens

## Support

For issues and questions:
1. Check the logs in `logs/app.log`
2. Verify your configuration in `.env`
3. Test webhook accessibility
4. Review Asana and Twilio API documentation

## License

This project is licensed under the MIT License. 