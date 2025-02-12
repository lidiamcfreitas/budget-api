import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Change to DEBUG for more details
    format="%(asctime)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)  # Use a named logger