import pytest
from unittest.mock import patch, MagicMock
from app.services.currency_service import CurrencyService
import httpx


class TestCurrencyService:
    """Tests for CurrencyService."""
    
    def setup_method(self):
        """Clear cache before each test."""
        CurrencyService._cache.clear()
    
    def test_get_currency_for_country_success(self):
        """Test successful currency retrieval from API."""
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                "name": {"common": "United States"},
                "currencies": {
                    "USD": {"name": "United States dollar", "symbol": "$"}
                }
            }
        ]
        mock_response.status_code = 200
        
        with patch('httpx.Client') as mock_client:
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response
            
            currency = CurrencyService.get_currency_for_country("United States")
            
            assert currency == "USD"
    
    def test_get_currency_for_country_multiple_currencies(self):
        """Test that first currency is returned when multiple exist."""
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                "name": {"common": "Switzerland"},
                "currencies": {
                    "CHF": {"name": "Swiss franc", "symbol": "Fr."},
                    "EUR": {"name": "Euro", "symbol": "€"}
                }
            }
        ]
        mock_response.status_code = 200
        
        with patch('httpx.Client') as mock_client:
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response
            
            currency = CurrencyService.get_currency_for_country("Switzerland")
            
            # Should return first currency (order may vary in dict, but should be consistent)
            assert currency in ["CHF", "EUR"]
    
    def test_get_currency_for_country_not_found(self):
        """Test error handling when country is not found."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Not Found", request=MagicMock(), response=mock_response
        )
        
        with patch('httpx.Client') as mock_client:
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response
            
            with pytest.raises(ValueError, match="Country 'InvalidCountry' not found"):
                CurrencyService.get_currency_for_country("InvalidCountry")
    
    def test_get_currency_for_country_empty_input(self):
        """Test error handling for empty country parameter."""
        with pytest.raises(ValueError, match="Country parameter cannot be empty"):
            CurrencyService.get_currency_for_country("")
        
        with pytest.raises(ValueError, match="Country parameter cannot be empty"):
            CurrencyService.get_currency_for_country("   ")
    
    def test_get_currency_for_country_api_error(self):
        """Test error handling when API returns server error."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Server Error", request=MagicMock(), response=mock_response
        )
        
        with patch('httpx.Client') as mock_client:
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response
            
            with pytest.raises(RuntimeError, match="REST Countries API error: 500"):
                CurrencyService.get_currency_for_country("United States")
    
    def test_get_currency_for_country_connection_error(self):
        """Test error handling when connection fails."""
        with patch('httpx.Client') as mock_client:
            mock_client.return_value.__enter__.return_value.get.side_effect = httpx.RequestError(
                "Connection failed"
            )
            
            with pytest.raises(RuntimeError, match="Failed to connect to REST Countries API"):
                CurrencyService.get_currency_for_country("United States")
    
    def test_get_currency_for_country_no_currency_in_response(self):
        """Test error handling when country has no currency data."""
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                "name": {"common": "Antarctica"},
                "currencies": {}
            }
        ]
        mock_response.status_code = 200
        
        with patch('httpx.Client') as mock_client:
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response
            
            with pytest.raises(ValueError, match="No currency found for country"):
                CurrencyService.get_currency_for_country("Antarctica")
    
    def test_caching_works(self):
        """Test that currency lookups are cached."""
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                "name": {"common": "Canada"},
                "currencies": {
                    "CAD": {"name": "Canadian dollar", "symbol": "$"}
                }
            }
        ]
        mock_response.status_code = 200
        
        with patch('httpx.Client') as mock_client:
            mock_get = mock_client.return_value.__enter__.return_value.get
            mock_get.return_value = mock_response
            
            # First call should hit API
            currency1 = CurrencyService.get_currency_for_country("Canada")
            assert currency1 == "CAD"
            assert mock_get.call_count == 1
            
            # Second call should use cache
            currency2 = CurrencyService.get_currency_for_country("Canada")
            assert currency2 == "CAD"
            assert mock_get.call_count == 1  # No additional API call
    
    def test_cache_case_insensitive(self):
        """Test that cache is case-insensitive."""
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                "name": {"common": "France"},
                "currencies": {
                    "EUR": {"name": "Euro", "symbol": "€"}
                }
            }
        ]
        mock_response.status_code = 200
        
        with patch('httpx.Client') as mock_client:
            mock_get = mock_client.return_value.__enter__.return_value.get
            mock_get.return_value = mock_response
            
            # First call with lowercase
            currency1 = CurrencyService.get_currency_for_country("france")
            assert currency1 == "EUR"
            
            # Second call with different case should use cache
            currency2 = CurrencyService.get_currency_for_country("FRANCE")
            assert currency2 == "EUR"
            assert mock_get.call_count == 1  # Only one API call
    
    def test_cache_expiration(self):
        """Test that cache entries expire after TTL."""
        from datetime import datetime, timedelta
        
        # Manually add expired cache entry
        expired_time = datetime.utcnow() - timedelta(seconds=1)
        CurrencyService._cache["testcountry"] = ("TST", expired_time)
        
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                "name": {"common": "TestCountry"},
                "currencies": {
                    "NEW": {"name": "New Currency", "symbol": "N"}
                }
            }
        ]
        mock_response.status_code = 200
        
        with patch('httpx.Client') as mock_client:
            mock_get = mock_client.return_value.__enter__.return_value.get
            mock_get.return_value = mock_response
            
            # Should fetch from API since cache is expired
            currency = CurrencyService.get_currency_for_country("TestCountry")
            assert currency == "NEW"
            assert mock_get.call_count == 1
