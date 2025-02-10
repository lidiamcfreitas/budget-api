from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from firebase_admin import firestore
import logging
from .base_service import BaseService
import requests
from cachetools import TTLCache
from pydantic import BaseModel, Field, validator

class ExchangeRate(BaseModel):
    base_currency: str
    rates: Dict[str, float]
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @validator('base_currency')
    def validate_base_currency(cls, v):
        if v not in CurrencyService.VALID_CURRENCIES:
            raise ValueError(f"Invalid currency: {v}")
        return v

class CurrencyConversion(BaseModel):
    amount: float
    from_currency: str
    to_currency: str
    converted_amount: Optional[float] = None
    rate: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    @validator('from_currency', 'to_currency')
    def validate_currency(cls, v):
        if v not in CurrencyService.VALID_CURRENCIES:
            raise ValueError(f"Invalid currency: {v}")
        return v

class CurrencyService(BaseService):
    VALID_CURRENCIES = ['USD', 'EUR', 'GBP', 'JPY', 'CAD', 'AUD', 'CHF', 'CNY', 'BRL']
    
    def __init__(self, db: firestore.Client):
        super().__init__()
        self.db = db
        self.collection = 'exchange_rates'
        self.logger = logging.getLogger(__name__)
        # Cache exchange rates for 1 hour
        self.rates_cache = TTLCache(maxsize=100, ttl=3600)
        
    def get_exchange_rate(self, from_currency: str, to_currency: str) -> float:
        """Get the exchange rate between two currencies."""
        try:
            # Validation handled by CurrencyConversion model
            conversion = CurrencyConversion(
                amount=1.0,
                from_currency=from_currency,
                to_currency=to_currency
            )
            
            if conversion.from_currency == conversion.to_currency:
                return 1.0
            
            cache_key = f"{conversion.from_currency}_{conversion.to_currency}"
            if cache_key in self.rates_cache:
                return self.rates_cache[cache_key]
            
            rate = self._fetch_exchange_rate(from_currency, to_currency)
            self.rates_cache[cache_key] = rate
            return rate
        except Exception as e:
            self.logger.error(f"Error getting exchange rate: {str(e)}")
            raise
        
    def convert_amount(self, amount: float, from_currency: str, to_currency: str) -> CurrencyConversion:
        """Convert an amount from one currency to another and return a CurrencyConversion model."""
        try:
            conversion = CurrencyConversion(
                amount=amount,
                from_currency=from_currency,
                to_currency=to_currency
            )
            rate = self.get_exchange_rate(conversion.from_currency, conversion.to_currency)
            conversion.rate = rate
            conversion.converted_amount = amount * rate
            return conversion
        except Exception as e:
            self.logger.error(f"Error converting amount: {str(e)}")
            raise
        
    def update_exchange_rates(self) -> None:
        """Update all exchange rates in the database."""
        try:
            rates = self._fetch_all_exchange_rates()
            batch = self.db.batch()
            
            for base_currency in self.VALID_CURRENCIES:
                doc_ref = self.db.collection(self.collection).document(base_currency)
                exchange_rate = ExchangeRate(
                    base_currency=base_currency,
                    rates=rates[base_currency]
                )
                batch.set(doc_ref, exchange_rate.model_dump())
                
            batch.commit()
            self.rates_cache.clear()  # Clear cache after update
        except Exception as e:
            self.logger.error(f"Error updating exchange rates: {str(e)}")
            raise
        
    def get_latest_rates(self, base_currency: str) -> ExchangeRate:
        """Get all exchange rates for a base currency."""
        try:
            # Validation handled by ExchangeRate model
            doc = self.db.collection(self.collection).document(base_currency).get()
            if not doc.exists:
                self.update_exchange_rates()
                doc = self.db.collection(self.collection).document(base_currency).get()
            
            rates_data = doc.to_dict()
            return ExchangeRate(
                base_currency=base_currency,
                rates=rates_data['rates'],
                updated_at=rates_data['updated_at']
            )
        except Exception as e:
            self.logger.error(f"Error getting latest rates: {str(e)}")
            raise
        
    def validate_currency(self, currency: str) -> bool:
        """Validate if a currency is supported."""
        return currency in self.VALID_CURRENCIES
        
    def _fetch_exchange_rate(self, from_currency: str, to_currency: str) -> float:
        """Fetch exchange rate from database or external API."""
        try:
            doc = self.db.collection(self.collection).document(from_currency).get()
            if not doc.exists or self._is_rate_outdated(doc.to_dict()['updated_at']):
                self.update_exchange_rates()
                doc = self.db.collection(self.collection).document(from_currency).get()
                
            rates = doc.to_dict()['rates']
            return rates[to_currency]
        except Exception as e:
            self.logger.error(f"Error fetching exchange rate: {str(e)}")
            raise
        
    def _fetch_all_exchange_rates(self) -> Dict[str, Dict[str, float]]:
        """Fetch all exchange rates from external API."""
        # Note: Implementation would depend on the specific API service being used
        # This is a placeholder that would need to be implemented with actual API calls
        raise NotImplementedError("External API integration not implemented")
        
    def _is_rate_outdated(self, updated_at: datetime) -> bool:
        """Check if the exchange rate is outdated (older than 1 day)."""
        return datetime.utcnow() - updated_at > timedelta(days=1)

