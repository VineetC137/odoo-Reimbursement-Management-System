"""
Manual test script to verify REST Countries API integration.
Run this to test the actual API call (not mocked).
"""
from app.services.currency_service import CurrencyService

def test_real_api_calls():
    """Test real API calls to REST Countries."""
    
    print("Testing CurrencyService with real REST Countries API...")
    
    # Test 1: United States
    print("\n1. Testing United States...")
    try:
        currency = CurrencyService.get_currency_for_country("United States")
        print(f"   ✓ Currency for United States: {currency}")
        assert currency == "USD"
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test 2: Canada
    print("\n2. Testing Canada...")
    try:
        currency = CurrencyService.get_currency_for_country("Canada")
        print(f"   ✓ Currency for Canada: {currency}")
        assert currency == "CAD"
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test 3: United Kingdom
    print("\n3. Testing United Kingdom...")
    try:
        currency = CurrencyService.get_currency_for_country("United Kingdom")
        print(f"   ✓ Currency for United Kingdom: {currency}")
        assert currency == "GBP"
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test 4: France
    print("\n4. Testing France...")
    try:
        currency = CurrencyService.get_currency_for_country("France")
        print(f"   ✓ Currency for France: {currency}")
        assert currency == "EUR"
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test 5: Invalid country
    print("\n5. Testing invalid country...")
    try:
        currency = CurrencyService.get_currency_for_country("InvalidCountryXYZ")
        print(f"   ✗ Should have raised ValueError but got: {currency}")
    except ValueError as e:
        print(f"   ✓ Correctly raised ValueError: {e}")
    except Exception as e:
        print(f"   ✗ Unexpected error: {e}")
    
    # Test 6: Caching
    print("\n6. Testing caching (second call should be instant)...")
    try:
        import time
        start = time.time()
        currency1 = CurrencyService.get_currency_for_country("Japan")
        time1 = time.time() - start
        print(f"   First call took {time1:.3f}s, currency: {currency1}")
        
        start = time.time()
        currency2 = CurrencyService.get_currency_for_country("Japan")
        time2 = time.time() - start
        print(f"   Second call took {time2:.3f}s, currency: {currency2}")
        
        if time2 < time1 / 10:  # Cached call should be much faster
            print(f"   ✓ Caching works! Second call was {time1/time2:.1f}x faster")
        else:
            print(f"   ⚠ Caching might not be working as expected")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    print("\n✅ All tests completed!")

if __name__ == "__main__":
    test_real_api_calls()
