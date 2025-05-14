import random
import json
import time
import socket
from datetime import datetime
import os


# Get the target host and port from environment variables
target_host = os.getenv('TARGET_HOST', 'alloy')
target_port = int(os.getenv('TARGET_PORT', 9999))
# Get the mail house ID from environment variables
mail_house_id = os.getenv('MAIL_HOUSE_ID', 'MAIL-01')

# Define the endpoint path
endpoint_path = "/loki/api/v1/raw"

# List of states and cities in America (abbreviated version)
STATES_CITIES = {
    "California": ["Los Angeles", "San Francisco", "San Diego"],
    "Texas": ["Houston", "Dallas", "Austin"],
    "New York": ["New York City", "Buffalo", "Rochester"],
    "Florida": ["Miami", "Orlando", "Tampa"],
    "Illinois": ["Chicago", "Springfield", "Naperville"],
}

# Package statuses and metadata
PACKAGE_SIZES = ["Small", "Medium", "Large"]
PACKAGE_TYPES = ["Documents", "Electronics", "Clothing", "Food", "Furniture"]
PACKAGE_STATUS_LEVELS = ["info", "warning", "critical", "error"]
PACKAGE_NOTES = [
    "In transit",
    "Out for delivery",
    "Delivered successfully",
    "Delayed due to weather",
    "Address not found",
    "Returned to sender",
    "Damaged during transit",
]


def generate_log_entry():
    state = random.choice(list(STATES_CITIES.keys()))
    city = random.choice(STATES_CITIES[state])
    
    log_entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z",
        "state": state,
        "city": city,
        "package_id": f"PKG{random.randint(10000, 99999)}",
        "package_type": random.choice(PACKAGE_TYPES),
        "package_size": random.choice(PACKAGE_SIZES),
        "package_status": random.choice(PACKAGE_STATUS_LEVELS),
        "note": random.choice(PACKAGE_NOTES),
        "sender": {
            "name": f"Sender{random.randint(1, 100)}",
            "address": f"{random.randint(100, 999)} {random.choice(['Main St', 'Broadway', 'Elm St', 'Maple Ave'])}, {city}, {state}",
        },
        "receiver": {
            "name": f"Receiver{random.randint(1, 100)}",
            "address": f"{random.randint(100, 999)} {random.choice(['Oak St', 'Pine Rd', 'Cedar Blvd', 'Willow Ln'])}, {random.choice(STATES_CITIES[state])}, {state}",
        },
        "mail_house_id": mail_house_id, 
    }
    return log_entry


def main():
    # Create a TCP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((target_host, target_port))
    except socket.error as e:
        print(f"Failed to connect to {target_host}:{target_port} - {e}")
        time.sleep(1)
        main()
    
    while True:
        try:
            log_entry = generate_log_entry()
            log_entry_json = json.dumps(log_entry)

            http_request = (
                f"POST {endpoint_path} HTTP/1.1\r\n"
                f"Host: {target_host}\r\n"
                "Content-Type: application/json\r\n"
                f"Content-Length: {len(log_entry_json)}\r\n"
                "Connection: keep-alive\r\n"
                "\r\n"
                f"{log_entry_json}"
            )

            # Send the HTTP request over TCP
            sock.sendall(http_request.encode())
            print(f"Sent JSON log message to {target_host}:{target_port} - {log_entry_json}")

            # Wait for a few seconds before sending the next log
            time.sleep(1)
        except socket.error as e:
            print(f"Failed to send log message - {e}")
            # Close the socket and exit
            sock.close()
            exit(1)
            



if __name__ == "__main__":
    main()
