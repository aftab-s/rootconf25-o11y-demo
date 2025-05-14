import socket
import time
import os
import random
from datetime import datetime

# Get the target host and port from environment variables
syslog_host = os.getenv('SYSLOG_HOST', 'localhost')
syslog_port = int(os.getenv('SYSLOG_PORT', 514))

# Create a UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Define log levels and messages
log_levels = ["INFO", "WARNING", "ERROR", "DEBUG", "CRITICAL"]
messages = [
    "System started successfully",
    "User login successful",
    "Configuration loaded",
    "Connection to database failed",
    "Data processed successfully",
    "Invalid API request received",
    "Memory usage high",
    "Disk space low",
    "Unknown error occurred",
    "Service restarted",
]

# Generate and send syslog messages every few seconds
while True:
    # Correct timestamp format
    timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    log_level = random.choice(log_levels)
    message_text = random.choice(messages)
    pid = random.randint(100, 999)  # Simulate random process IDs
    app_name = "MyApp"
    hostname = socket.gethostname()
    msgid = '-'
    structured_data = '-'
    # Include the log level in the message body
    message_body = f"{log_level}: {message_text}"
    # Correct syslog message format
    message = f"<34>1 {timestamp} {hostname} {app_name} {pid} {msgid} {structured_data} {message_body}"
    sock.sendto(message.encode(), (syslog_host, syslog_port))
    print(f"Sent syslog message to {syslog_host}:{syslog_port} - {message_body}")
    time.sleep(random.randint(3, 8))  # Send a message every 3-8 seconds

