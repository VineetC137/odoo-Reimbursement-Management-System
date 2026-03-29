import httpx
from typing import Optional


class FXService:
    """Service for foreign exchange rate conversion using ExchangeRate-API."""
    
    # ExchangeRate-API base URL (using free v4 endpoint)
    API_BASE_URL = "https://api.exchangerate-api.com/v4/latest"
    
    @classmethod
    def get_exchange_rate(cls, from_currency: str, to_currency: str) -> float:
        """
        Get the exchange rate from one currency to another.
        
        Args:
            from_currency: Source currency ISO code (e.g., "USD")
            to_currency: Target currency ISO code (e.g., "EUR")
            
        Returns:
            Exchange rate as a float
            
        Raises:
            ValueError: If currencies are invalid
            RuntimeError: If API call fails
        """
        if not from_currency or not from_currency.strip():
            raise ValueError("from_currency parameter cannot be empty")
        
        if not to_currency or not to_currency.strip():
            raise ValueError("to_currency parameter cannot be empty")
        
        # Normalize currency codes to uppercase
        from_currency = from_currency.strip().upper()
        to_currency = to_currency.strip().upper()
        
        # If same currency, return 1.0 without API call
        if from_currency == to_currency:
            return 1.0
        
        # Call ExchangeRate-API
        try:
            url = f"{cls.API_BASE_URL}/{from_currency}"
            
            with httpx.Client(timeout=10.0) as client:
                response = client.get(url)
                response.raise_for_status()
                
                data = response.json()
                
                # Extract rates
                rates = data.get("rates", {})
                
                if to_currency not in rates:
                    raise ValueError(f"Exchange rate not found for currency '{to_currency}'")
                
                return float(rates[to_currency])
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise ValueError(f"Currency '{from_currency}' not found")
            raise RuntimeError(f"ExchangeRate-API error: {e.response.status_code}")
        except httpx.RequestError as e:
            raise RuntimeError(f"Failed to connect to ExchangeRate-API: {str(e)}")
        except (KeyError, ValueError) as e:
            if "not found" in str(e):
                raise
            raise RuntimeError(f"Invalid response from ExchangeRate-API: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error calling ExchangeRate-API: {str(e)}")
    
    @classmethod
    def convert_amount(cls, amount: float, from_currency: str, to_currency: str) -> float:
        """
        Convert an amount from one currency to another.
        
        Args:
            amount: Amount to convert
            from_currency: Source currency ISO code (e.g., "USD")
            to_currency: Target currency ISO code (e.g., "EUR")
            
        Returns:
            Converted amount as a float
            
        Raises:
            ValueError: If amount is negative or currencies are invalid
            RuntimeError: If API call fails
        """
        if amount < 0:
            raise ValueError("Amount cannot be negative")
        
        # Get exchange rate
        rate = cls.get_exchange_rate(from_currency, to_currency)
        
        # Calculate converted amount
        converted = amount * rate
        
        return converted
