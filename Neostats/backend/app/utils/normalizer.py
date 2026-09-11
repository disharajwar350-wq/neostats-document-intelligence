import re
from typing import Any, Optional, Tuple

class NumberNormalizer:
    """
    Cleans raw financial OCR string numbers into float or exact rounded values.
    Handles thousands separators (commas), currency symbols ($/₹/€/£),
    and parenthetical negatives like (500.00) -> -500.00.
    """
    
    @staticmethod
    def clean_currency(value_str: str) -> Tuple[Optional[str], Optional[float]]:
        if not value_str or not isinstance(value_str, str):
            return None, None
            
        text = value_str.trim() if hasattr(value_str, 'trim') else value_str.strip()
        if not text or text in ['-', '—', 'N/A', 'n/a', 'null', 'None']:
            return None, None
            
        # Detect currency
        currency = None
        if '$' in text or 'USD' in text:
            currency = 'USD'
        elif '₹' in text or 'INR' in text or 'Rs' in text:
            currency = 'INR'
        elif '€' in text or 'EUR' in text:
            currency = 'EUR'
        elif '£' in text or 'GBP' in text:
            currency = 'GBP'
            
        # Check parenthetical negative: (1,234.50) -> -1234.50
        is_negative = False
        paren_match = re.match(r'^\s*\(([^)]+)\)\s*$', text)
        if paren_match:
            is_negative = True
            text = paren_match.group(1)
        elif text.startswith('-'):
            is_negative = True
            text = text[1:]

        # Remove currency symbols & thousands commas
        cleaned = re.sub(r'[₹$€£\s,A-Za-z]', '', text)
        
        try:
            val = float(cleaned)
            if is_negative:
                val = -val
            return currency, round(val, 2)
        except ValueError:
            return currency, None

    @staticmethod
    def parse_float(raw: Any) -> Optional[float]:
        if raw is None:
            return None
        if isinstance(raw, (int, float)):
            return float(raw)
        _, val = NumberNormalizer.clean_currency(str(raw))
        return val
