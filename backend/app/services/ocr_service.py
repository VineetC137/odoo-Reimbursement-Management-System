import pytesseract
import re
from typing import Optional
from PIL import Image


class OCRService:
    """Service for OCR receipt parsing using Tesseract."""
    
    @classmethod
    def extract_text(cls, image_path: str) -> str:
        """
        Extract text from an image using Tesseract OCR.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Extracted text as a string
            
        Raises:
            RuntimeError: If OCR extraction fails
        """
        try:
            # Open image and extract text
            image = Image.open(image_path)
            text = pytesseract.image_to_string(image)
            return text
        except Exception as e:
            raise RuntimeError(f"Failed to extract text from image: {str(e)}")
    
    @classmethod
    def parse_amount(cls, text: str) -> Optional[float]:
        """
        Parse the amount as the largest decimal number found in the text.
        
        Args:
            text: Text to parse
            
        Returns:
            Largest decimal number found, or None if no valid number found
        """
        if not text:
            return None
        
        # Priority 1: Numbers with currency symbols ($, €, £, ¥)
        currency_pattern = r'[\$€£¥]\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?|\d+\.\d{2}|\d+)'
        currency_matches = re.findall(currency_pattern, text)
        
        if currency_matches:
            # If we found currency symbols, use only those matches
            amounts = []
            for match in currency_matches:
                try:
                    clean_match = match.replace(',', '')
                    amount = float(clean_match)
                    amounts.append(amount)
                except ValueError:
                    continue
            if amounts:
                return max(amounts)
        
        # Priority 2: Numbers with exactly 2 decimal places (likely prices)
        decimal_pattern = r'\b(\d{1,3}(?:,\d{3})*\.\d{2})\b'
        decimal_matches = re.findall(decimal_pattern, text)
        
        if decimal_matches:
            amounts = []
            for match in decimal_matches:
                try:
                    clean_match = match.replace(',', '')
                    amount = float(clean_match)
                    amounts.append(amount)
                except ValueError:
                    continue
            if amounts:
                return max(amounts)
        
        # Priority 3: Any number with decimal point
        fallback_pattern = r'\b(\d+\.\d+)\b'
        fallback_matches = re.findall(fallback_pattern, text)
        
        if fallback_matches:
            amounts = []
            for match in fallback_matches:
                try:
                    amount = float(match)
                    # Filter out years (typically 1900-2100)
                    if not (1900 <= amount <= 2100):
                        amounts.append(amount)
                except ValueError:
                    continue
            if amounts:
                return max(amounts)
        
        # Last resort: any integer (excluding years)
        integer_pattern = r'\b(\d+)\b'
        integer_matches = re.findall(integer_pattern, text)
        
        if integer_matches:
            amounts = []
            for match in integer_matches:
                try:
                    amount = float(match)
                    # Filter out years and unrealistic amounts
                    if not (1900 <= amount <= 2100) and amount < 10000:
                        amounts.append(amount)
                except ValueError:
                    continue
            if amounts:
                return max(amounts)
        
        return None
    
    @classmethod
    def parse_date(cls, text: str) -> Optional[str]:
        """
        Parse the date using regex patterns for common date formats.
        
        Args:
            text: Text to parse
            
        Returns:
            Date string in ISO format (YYYY-MM-DD), or None if no date found
        """
        if not text:
            return None
        
        # Common date patterns
        patterns = [
            # MM/DD/YYYY or MM-DD-YYYY
            (r'\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b', 'mdy'),
            # DD/MM/YYYY or DD-MM-YYYY
            (r'\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b', 'dmy'),
            # YYYY/MM/DD or YYYY-MM-DD
            (r'\b(\d{4})[/-](\d{1,2})[/-](\d{1,2})\b', 'ymd'),
            # Month DD, YYYY (e.g., Jan 15, 2024)
            (r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+(\d{1,2}),?\s+(\d{4})\b', 'mdy_text'),
        ]
        
        month_map = {
            'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
            'may': '05', 'jun': '06', 'jul': '07', 'aug': '08',
            'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12'
        }
        
        for pattern, format_type in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    if format_type == 'mdy':
                        month, day, year = match.groups()
                        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                    elif format_type == 'dmy':
                        day, month, year = match.groups()
                        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                    elif format_type == 'ymd':
                        year, month, day = match.groups()
                        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                    elif format_type == 'mdy_text':
                        month_str, day, year = match.groups()
                        month = month_map[month_str.lower()[:3]]
                        return f"{year}-{month}-{day.zfill(2)}"
                except (ValueError, KeyError):
                    continue
        
        return None
    
    @classmethod
    def parse_merchant(cls, text: str) -> Optional[str]:
        """
        Parse the merchant as the first alphabetic line in the text.
        
        Args:
            text: Text to parse
            
        Returns:
            Merchant name, or None if no alphabetic line found
        """
        if not text:
            return None
        
        # Split text into lines
        lines = text.strip().split('\n')
        
        # Find first line that contains mostly alphabetic characters
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if line has at least 3 alphabetic characters
            alpha_count = sum(c.isalpha() for c in line)
            if alpha_count >= 3:
                return line
        
        return None
    
    @classmethod
    def parse_receipt(cls, image_path: str) -> dict:
        """
        Parse a receipt image and extract all relevant information.
        
        Args:
            image_path: Path to the receipt image file
            
        Returns:
            Dictionary with keys: raw_text, amount, currency_guess, date, merchant
        """
        # Extract text from image
        raw_text = cls.extract_text(image_path)
        
        # Parse individual fields
        amount = cls.parse_amount(raw_text)
        date = cls.parse_date(raw_text)
        merchant = cls.parse_merchant(raw_text)
        
        # Currency guess - look for common currency symbols/codes
        currency_guess = None
        currency_patterns = [
            (r'\$', 'USD'),
            (r'USD', 'USD'),
            (r'€', 'EUR'),
            (r'EUR', 'EUR'),
            (r'£', 'GBP'),
            (r'GBP', 'GBP'),
            (r'¥', 'JPY'),
            (r'JPY', 'JPY'),
        ]
        
        for pattern, currency in currency_patterns:
            if re.search(pattern, raw_text):
                currency_guess = currency
                break
        
        return {
            'raw_text': raw_text,
            'amount': amount,
            'currency_guess': currency_guess,
            'date': date,
            'merchant': merchant
        }
