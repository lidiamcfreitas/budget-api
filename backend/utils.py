import asyncio
import functools
from typing import Callable, Any
from fastapi import  Request, status, HTTPException
from pydantic import validator
import logging

# Store valid currencies in a separate JSON file
import json

CURRENCY_FILE = "data/valid_currencies.json"

# Load valid currencies from JSON file
with open(CURRENCY_FILE, "r") as file:
    VALID_CURRENCIES = set(json.load(file))

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

@validator("currency")
def validate_currency(value):
    if value not in VALID_CURRENCIES:
        raise ValueError(f"Invalid currency: {value}. Must be a valid ISO 4217 currency code.")
    return value

def maybe_throw_not_found(ref: Any, error_message: str):
    if not ref.exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_message
        )

def handle_exceptions(error_message: str):
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.error(f"{error_message}: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e)
                )
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"{error_message}: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e)
                )
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator