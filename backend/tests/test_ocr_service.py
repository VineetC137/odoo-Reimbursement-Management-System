import pytest
from backend.app.services.ocr_service import OCRService


class TestOCRService:
    """Unit tests for OCRService."""
    
    def test_parse_amount_simple_decimal(self):
        """Test parsing a simple decimal amount."""
        text = "Total: 45.99"
        amount = OCRService.parse_amount(text)
        assert amount == 45.99
    
    def test_parse_amount_with_commas(self):
        """Test parsing amount with comma separators."""
        text = "Total: 1,234.56"
        amount = OCRService.parse_amount(text)
        assert amount == 1234.56
    
    def test_parse_amount_largest_number(self):
        """Test that the largest number is returned."""
        text = "Item 1: 10.00\nItem 2: 25.50\nTotal: 35.50"
        amount = OCRService.parse_amount(text)
        assert amount == 35.50
    
    def test_parse_amount_no_decimal(self):
        """Test parsing whole number amount."""
        text = "Total: 100"
        amount = OCRService.parse_amount(text)
        assert amount == 100.0
    
    def test_parse_amount_empty_text(self):
        """Test parsing empty text returns None."""
        amount = OCRService.parse_amount("")
        assert amount is None
    
    def test_parse_amount_no_numbers(self):
        """Test parsing text with no numbers returns None."""
        text = "No numbers here"
        amount = OCRService.parse_amount(text)
        assert amount is None
    
    def test_parse_date_mdy_slash(self):
        """Test parsing MM/DD/YYYY format."""
        text = "Date: 12/25/2023"
        date = OCRService.parse_date(text)
        assert date == "2023-12-25"
    
    def test_parse_date_mdy_dash(self):
        """Test parsing MM-DD-YYYY format."""
        text = "Date: 01-15-2024"
        date = OCRService.parse_date(text)
        assert date == "2024-01-15"
    
    def test_parse_date_ymd(self):
        """Test parsing YYYY-MM-DD format."""
        text = "Date: 2024-03-20"
        date = OCRService.parse_date(text)
        assert date == "2024-03-20"
    
    def test_parse_date_month_text(self):
        """Test parsing 'Month DD, YYYY' format."""
        text = "Date: Jan 15, 2024"
        date = OCRService.parse_date(text)
        assert date == "2024-01-15"
    
    def test_parse_date_month_text_full(self):
        """Test parsing full month name."""
        text = "Date: December 31, 2023"
        date = OCRService.parse_date(text)
        assert date == "2023-12-31"
    
    def test_parse_date_empty_text(self):
        """Test parsing empty text returns None."""
        date = OCRService.parse_date("")
        assert date is None
    
    def test_parse_date_no_date(self):
        """Test parsing text with no date returns None."""
        text = "No date here"
        date = OCRService.parse_date(text)
        assert date is None
    
    def test_parse_merchant_simple(self):
        """Test parsing merchant from first alphabetic line."""
        text = "Starbucks Coffee\n123 Main St\nTotal: 5.99"
        merchant = OCRService.parse_merchant(text)
        assert merchant == "Starbucks Coffee"
    
    def test_parse_merchant_with_leading_whitespace(self):
        """Test parsing merchant with leading whitespace."""
        text = "   \n  \nWalmart Supercenter\nReceipt #12345"
        merchant = OCRService.parse_merchant(text)
        assert merchant == "Walmart Supercenter"
    
    def test_parse_merchant_mixed_content(self):
        """Test parsing merchant from mixed content."""
        text = "***\nTarget Store\nDate: 01/15/2024"
        merchant = OCRService.parse_merchant(text)
        assert merchant == "Target Store"
    
    def test_parse_merchant_empty_text(self):
        """Test parsing empty text returns None."""
        merchant = OCRService.parse_merchant("")
        assert merchant is None
    
    def test_parse_merchant_no_alphabetic_line(self):
        """Test parsing text with no alphabetic line returns None."""
        text = "123\n456\n789"
        merchant = OCRService.parse_merchant(text)
        assert merchant is None
    
    def test_parse_receipt_complete(self):
        """Test parsing a complete receipt."""
        # Create a sample receipt text
        sample_text = """Starbucks Coffee
123 Main Street
Date: 01/15/2024

Latte         $4.50
Muffin        $3.25
Tax           $0.62
Total:        $8.37

Thank you!"""
        
        # Mock extract_text to return our sample
        original_extract = OCRService.extract_text
        OCRService.extract_text = lambda path: sample_text
        
        try:
            result = OCRService.parse_receipt("dummy_path.jpg")
            
            assert result['raw_text'] == sample_text
            assert result['amount'] == 8.37
            assert result['currency_guess'] == 'USD'
            assert result['date'] == '2024-01-15'
            assert result['merchant'] == 'Starbucks Coffee'
        finally:
            # Restore original method
            OCRService.extract_text = original_extract
    
    def test_parse_receipt_euro_currency(self):
        """Test parsing receipt with Euro currency."""
        sample_text = "Restaurant\nTotal: €25.50"
        
        original_extract = OCRService.extract_text
        OCRService.extract_text = lambda path: sample_text
        
        try:
            result = OCRService.parse_receipt("dummy_path.jpg")
            assert result['currency_guess'] == 'EUR'
            assert result['amount'] == 25.50
        finally:
            OCRService.extract_text = original_extract
    
    def test_parse_receipt_gbp_currency(self):
        """Test parsing receipt with GBP currency."""
        sample_text = "Shop\nTotal: £15.99"
        
        original_extract = OCRService.extract_text
        OCRService.extract_text = lambda path: sample_text
        
        try:
            result = OCRService.parse_receipt("dummy_path.jpg")
            assert result['currency_guess'] == 'GBP'
            assert result['amount'] == 15.99
        finally:
            OCRService.extract_text = original_extract
    
    def test_parse_receipt_no_currency_symbol(self):
        """Test parsing receipt without currency symbol."""
        sample_text = "Store\nTotal: 50.00"
        
        original_extract = OCRService.extract_text
        OCRService.extract_text = lambda path: sample_text
        
        try:
            result = OCRService.parse_receipt("dummy_path.jpg")
            assert result['currency_guess'] is None
            assert result['amount'] == 50.00
        finally:
            OCRService.extract_text = original_extract
