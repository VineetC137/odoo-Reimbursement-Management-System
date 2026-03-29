import httpx
from typing import Optional
from datetime import datetime, timedelta


class CurrencyService:
    """Service for retrieving currency information from REST Countries API."""
    
    # In-memory cache for currency lookups
    # Format: {country: (currency, expiration_timestamp)}
    _cache: dict[str, tuple[str, datetime]] = {}
    
    # Cache TTL in seconds (24 hours)
    CACHE_TTL = 86400
    
    @classmethod
    def get_currency_for_country(cls, country: str) -> str:
        """
        Get the base currency for a given country using REST Countries API.
        
        Args:
            country: Country name or code
            
        Returns:
            ISO currency code (e.g., "USD", "EUR")
            
        Raises:
            ValueError: If country is empty or not found
            RuntimeError: If API call fails
        """
        if not country or not country.strip():
            raise ValueError("Country parameter cannot be empty")
        
        # Check cache first
        cached_result = cls._get_from_cache(country)
        if cached_result:
            return cached_result
        
        # Call REST Countries API
        try:
            currency = cls._fetch_currency_from_api(country)
            
            # Cache the result
            cls._cache_currency(country, currency)
            
            return currency
            
        except ValueError:
            # Re-raise ValueError as-is (e.g., no currency found)
            raise
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise ValueError(f"Country '{country}' not found")
            raise RuntimeError(f"REST Countries API error: {e.response.status_code}")
        except httpx.RequestError as e:
            raise RuntimeError(f"Failed to connect to REST Countries API: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error calling REST Countries API: {str(e)}")
    
    @classmethod
    def _fetch_currency_from_api(cls, country: str) -> str:
        """
        Fetch currency from REST Countries API.
        
        Args:
            country: Country name or code
            
        Returns:
            ISO currency code
            
        Raises:
            ValueError: If no currency found in response
            httpx.HTTPStatusError: If API returns error status
            httpx.RequestError: If connection fails
        """
        # Try by name first
        url = f"https://restcountries.com/v3.1/name/{country}"
        
        with httpx.Client(timeout=10.0) as client:
            response = client.get(url)
            response.raise_for_status()
            
            data = response.json()
            
            if not data or len(data) == 0:
                raise ValueError(f"No data returned for country '{country}'")
            
            # Get first matching country
            country_data = data[0]
            
            # Extract currencies
            currencies = country_data.get("currencies", {})
            
            if not currencies:
                raise ValueError(f"No currency found for country '{country}'")
            
            # Get first currency code
            currency_code = list(currencies.keys())[0]
            
            return currency_code
    
    @classmethod
    def _get_from_cache(cls, country: str) -> Optional[str]:
        """
        Get currency from cache if not expired.
        
        Args:
            country: Country name or code
            
        Returns:
            Cached currency code if found and not expired, None otherwise
        """
        country_key = country.lower().strip()
        
        if country_key in cls._cache:
            currency, expiration = cls._cache[country_key]
            
            if datetime.utcnow() < expiration:
                return currency
            else:
                # Remove expired entry
                del cls._cache[country_key]
        
        return None
    
    @classmethod
    def _cache_currency(cls, country: str, currency: str, ttl: int = CACHE_TTL) -> None:
        """
        Cache currency lookup result.
        
        Args:
            country: Country name or code
            currency: ISO currency code
            ttl: Time to live in seconds (default: 24 hours)
        """
        country_key = country.lower().strip()
        expiration = datetime.utcnow() + timedelta(seconds=ttl)
        cls._cache[country_key] = (currency, expiration)
