import pytest
from unittest.mock import patch, MagicMock
from app.services.fx_service import FXService
import httpx


class TestFXService:
    """Tests for FXService."""
    
    def test_get_exchange_rate_success(self):
        """Test successful exchange rate retrieval from API."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "base": "USD",
            "date": "2024-01-01",
            "rates": {
                "EUR": 0.85,
                "GBP": 0.73,
                "JPY": 110.5
            }
        }
        mock_response.status_code = 200
        
        with patch('httpx.Client') as mock_client:
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response
            
            rate = FXService.get_exchange_rate("USD", "EUR")
            
            assert rate == 0.85
    
    def test_get_exchange_rate_same_currency(self):
        """Test that same currency returns 1.0 without API call."""
        with patch('httpx.Client') as mock_client:
            rate = FXService.get_exchange_rate("USD", "USD")
            
            assert rate == 1.0
            # Verify no API call was made
            mock_client.assert_not_called()
    
    def test_get_exchange_rate_case_insensitive(self):
        """Test that currency codes are normalized to uppercase."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "base": "USD",
            "rates": {
                "EUR": 0.85
            }
        }
        mock_response.status_code = 200
        
        with patch('httpx.Client') as mock_client:
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response
            
            # Test with lowercase
            rate = FXService.get_exchange_rate("usd", "eur")
            assert rate == 0.85
            
            # Verify API was called with uppercase
            call_args = mock_client.return_value.__enter__.return_value.get.call_args
            assert "USD" in call_args[0][0]
    
    def test_get_exchange_rate_empty_from_currency(self):
        """Test error handling for empty from_currency parameter."""
        with pytest.raises(ValueError, match="from_currency parameter cannot be empty"):
            FXService.get_exchange_rate("", "EUR")
        
        with pytest.raises(ValueError, match="from_currency parameter cannot be empty"):
            FXService.get_exchange_rate("   ", "EUR")
    
    def test_get_exchange_rate_empty_to_currency(self):
        """Test error handling for empty to_currency parameter."""
        with pytest.raises(ValueError, match="to_currency parameter cannot be empty"):
            FXService.get_exchange_rate("USD", "")
        
        with pytest.raises(ValueError, match="to_currency parameter cannot be empty"):
            FXService.get_exchange_rate("USD", "   ")
    
    def test_get_exchange_rate_invalid_from_currency(self):
        """Test error handling when from_currency is not found."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Not Found", request=MagicMock(), response=mock_response
        )
        
        with patch('httpx.Client') as mock_client:
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response
            
            with pytest.raises(ValueError, match="Currency 'XXX' not found"):
                FXService.get_exchange_rate("XXX", "EUR")
    
    def test_get_exchange_rate_invalid_to_currency(self):
        """Test error handling when to_currency is not in rates."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "base": "USD",
            "rates": {
                "EUR": 0.85,
                "GBP": 0.73
            }
        }
        mock_response.status_code = 200
        
        with patch('httpx.Client') as mock_client:
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response
            
            with pytest.raises(ValueError, match="Exchange rate not found for currency 'XXX'"):
                FXService.get_exchange_rate("USD", "XXX")
    
    def test_get_exchange_rate_api_error(self):
        """Test error handling when API returns server error."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Server Error", request=MagicMock(), response=mock_response
        )
        
        with patch('httpx.Client') as mock_client:
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response
            
            with pytest.raises(RuntimeError, match="ExchangeRate-API error: 500"):
                FXService.get_exchange_rate("USD", "EUR")
    
    def test_get_exchange_rate_connection_error(self):
        """Test error handling when connection fails."""
        with patch('httpx.Client') as mock_client:
            mock_client.return_value.__enter__.return_value.get.side_effect = httpx.RequestError(
                "Connection failed"
            )
            
            with pytest.raises(RuntimeError, match="Failed to connect to ExchangeRate-API"):
                FXService.get_exchange_rate("USD", "EUR")
    
    def test_convert_amount_success(self):
        """Test successful amount conversion."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "base": "USD",
            "rates": {
                "EUR": 0.85
            }
        }
        mock_response.status_code = 200
        
        with patch('httpx.Client') as mock_client:
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response
            
            converted = FXService.convert_amount(100.0, "USD", "EUR")
            
            assert converted == 85.0
    
    def test_convert_amount_same_currency(self):
        """Test that converting same currency returns original amount."""
        with patch('httpx.Client') as mock_client:
            converted = FXService.convert_amount(100.0, "USD", "USD")
            
            assert converted == 100.0
            # Verify no API call was made
            mock_client.assert_not_called()
    
    def test_convert_amount_zero(self):
        """Test converting zero amount."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "base": "USD",
            "rates": {
                "EUR": 0.85
            }
        }
        mock_response.status_code = 200
        
        with patch('httpx.Client') as mock_client:
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response
            
            converted = FXService.convert_amount(0.0, "USD", "EUR")
            
            assert converted == 0.0
    
    def test_convert_amount_negative(self):
        """Test error handling for negative amount."""
        with pytest.raises(ValueError, match="Amount cannot be negative"):
            FXService.convert_amount(-100.0, "USD", "EUR")
    
    def test_convert_amount_decimal(self):
        """Test converting decimal amounts."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "base": "USD",
            "rates": {
                "EUR": 0.85
            }
        }
        mock_response.status_code = 200
        
        with patch('httpx.Client') as mock_client:
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response
            
            converted = FXService.convert_amount(123.45, "USD", "EUR")
            
            # 123.45 * 0.85 = 104.9325
            assert abs(converted - 104.9325) < 0.0001
    
    def test_convert_amount_propagates_api_errors(self):
        """Test that convert_amount propagates errors from get_exchange_rate."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Server Error", request=MagicMock(), response=mock_response
        )
        
        with patch('httpx.Client') as mock_client:
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response
            
            with pytest.raises(RuntimeError, match="ExchangeRate-API error: 500"):
                FXService.convert_amount(100.0, "USD", "EUR")
