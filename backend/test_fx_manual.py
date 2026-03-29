"""
Manual test script for FXService.
Run this to verify the service works with the real ExchangeRate-API.
"""

from app.services.fx_service import FXService


def test_real_api():
    """Test FXService with real API calls."""
    
    print("Testing FXService with real ExchangeRate-API...")
    print("-" * 50)
    
    # Test 1: Get exchange rate
    print("\n1. Testing get_exchange_rate(USD, EUR)...")
    try:
        rate = FXService.get_exchange_rate("USD", "EUR")
        print(f"   ✓ Success! Rate: {rate}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test 2: Same currency
    print("\n2. Testing get_exchange_rate(USD, USD) - should return 1.0 without API call...")
    try:
        rate = FXService.get_exchange_rate("USD", "USD")
        print(f"   ✓ Success! Rate: {rate}")
        assert rate == 1.0, "Same currency should return 1.0"
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test 3: Convert amount
    print("\n3. Testing convert_amount(100, USD, EUR)...")
    try:
        converted = FXService.convert_amount(100.0, "USD", "EUR")
        print(f"   ✓ Success! 100 USD = {converted:.2f} EUR")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test 4: Convert with same currency
    print("\n4. Testing convert_amount(100, GBP, GBP) - should return 100 without API call...")
    try:
        converted = FXService.convert_amount(100.0, "GBP", "GBP")
        print(f"   ✓ Success! Amount: {converted}")
        assert converted == 100.0, "Same currency should return original amount"
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test 5: Multiple currencies
    print("\n5. Testing various currency conversions...")
    test_cases = [
        ("USD", "JPY"),
        ("EUR", "GBP"),
        ("GBP", "USD"),
    ]
    
    for from_curr, to_curr in test_cases:
        try:
            rate = FXService.get_exchange_rate(from_curr, to_curr)
            print(f"   ✓ {from_curr} -> {to_curr}: {rate}")
        except Exception as e:
            print(f"   ✗ {from_curr} -> {to_curr}: Error - {e}")
    
    # Test 6: Invalid currency
    print("\n6. Testing invalid currency (should fail gracefully)...")
    try:
        rate = FXService.get_exchange_rate("INVALID", "USD")
        print(f"   ✗ Should have raised an error but got: {rate}")
    except ValueError as e:
        print(f"   ✓ Correctly raised ValueError: {e}")
    except Exception as e:
        print(f"   ✗ Unexpected error: {e}")
    
    print("\n" + "-" * 50)
    print("Manual testing complete!")


if __name__ == "__main__":
    test_real_api()
