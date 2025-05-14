import logging
import time
import random
import os

# Ensure the /logs directory exists
log_directory = "/logs"
log_file = os.path.join(log_directory, "app.log")

if not os.path.exists(log_directory):
    os.makedirs(log_directory)  # Create directory if it doesn't exist

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("ExampleApp")

def simulate_process():
    """Simulates a process that generates logs every 5 seconds."""
    actions = ["start", "process", "error", "complete"]
    
    while True:  # Infinite loop
        action = random.choice(actions)

        if action == "start":
            logger.info("Process started successfully.")
        elif action == "process":
            logger.debug("Processing data...")
        elif action == "error":
            logger.error("An error occurred during processing.")
        elif action == "complete":
            logger.warning("Process completed with minor warnings.")

        time.sleep(5)  # Generate a log every 5 seconds

if __name__ == "__main__":
    logger.info("Application started.")

    try:
        simulate_process()
    except Exception as e:
        logger.critical(f"Unhandled exception: {e}")

    logger.info("Application finished.")
