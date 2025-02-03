from fastapi import  Request
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Change to DEBUG for more details
    format="%(asctime)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)  # Use a named logger


def debug_request(request: Request):
    logger.info(f"Request method: {request.method}")
    logger.info(f"Request URL: {request.url}")
    logger.info(f"Request Headers: {request.headers}")
    logger.info(f"Client IP: {request.client.host}")

    return {"message": "Check server logs for request details"}

def get_token(request: Request):
    token = request.headers.get("Authorization")
    token = token.split("Bearer ")[1] if token else None
    logger.info(f"Received token: {token}")
    return token