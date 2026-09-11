/**
 * NeoStats — Number Normalizer
 * 
 * Cleans and normalizes numbers extracted from OCR text.
 * Handles thousands separators, parenthetical negatives, currency symbols, etc.
 */

const Normalizer = (() => {

    /**
     * Remove thousands separators (commas) from a number string.
     * "1,234,567" → "1234567"
     * "1,234.56" → "1234.56"
     */
    function removeThousandsSeparators(str) {
        if (typeof str !== 'string') return str;
        // Only remove commas that act as thousands separators (not decimal separators)
        // Pattern: digits,digits where comma-separated groups are 3 digits
        return str.replace(/,(?=\d{3}(?:[,.\s)]|$))/g, '');
    }

    /**
     * Convert parenthetical notation to negative numbers.
     * "(500)" → "-500"
     * "(1,234.56)" → "-1234.56"
     */
    function convertParensToNegative(str) {
        if (typeof str !== 'string') return str;
        const match = str.match(/^\s*\(([^)]+)\)\s*$/);
        if (match) {
            return '-' + match[1].trim();
        }
        return str;
    }

    /**
     * Remove currency symbols (₹, $, €, £, ¥, etc.)
     * "₹1,234" → "1,234"
     * "$ 500.00" → "500.00"
     */
    function cleanCurrencySymbols(str) {
        if (typeof str !== 'string') return str;
        return str.replace(/[₹$€£¥]\s*/g, '').trim();
    }

    /**
     * Remove common unit suffixes like "Cr", "Lakh", "Mn", "Bn", "K"
     * Returns { value: string, unit: string }
     */
    function extractUnit(str) {
        if (typeof str !== 'string') return { value: str, unit: null };
        
        const unitPatterns = [
            { regex: /\s*(Crore|Crores|Cr\.?)\s*$/i, unit: 'Cr' },
            { regex: /\s*(Lakh|Lakhs|Lac|Lacs)\s*$/i, unit: 'Lakh' },
            { regex: /\s*(Million|Millions|Mn\.?|MM)\s*$/i, unit: 'Mn' },
            { regex: /\s*(Billion|Billions|Bn\.?)\s*$/i, unit: 'Bn' },
            { regex: /\s*(Thousand|Thousands|K)\s*$/i, unit: 'K' },
        ];

        for (const { regex, unit } of unitPatterns) {
            if (regex.test(str)) {
                return { value: str.replace(regex, '').trim(), unit };
            }
        }
        return { value: str, unit: null };
    }

    /**
     * Remove trailing percentage signs
     * "15.5%" → "15.5"
     */
    function cleanPercentage(str) {
        if (typeof str !== 'string') return str;
        return str.replace(/\s*%\s*$/, '').trim();
    }

    /**
     * Full normalization pipeline for a single number string.
     * Returns a clean numeric string or null if not a valid number.
     */
    function normalizeNumber(raw) {
        if (raw === null || raw === undefined || raw === '' || raw === '-' || raw === '—' || raw === 'N/A' || raw === 'n/a') {
            return null;
        }

        let str = String(raw).trim();

        // Step 1: Remove currency symbols
        str = cleanCurrencySymbols(str);

        // Step 2: Handle parenthetical negatives
        str = convertParensToNegative(str);

        // Step 3: Extract and note units (but keep the numeric part)
        const { value } = extractUnit(str);
        str = value;

        // Step 4: Remove percentage signs
        str = cleanPercentage(str);

        // Step 5: Remove thousands separators
        str = removeThousandsSeparators(str);

        // Step 6: Clean remaining whitespace
        str = str.replace(/\s/g, '');

        // Step 7: Validate that the result is a number
        if (str === '' || str === '-') return null;
        
        const num = Number(str);
        if (isNaN(num)) return null;

        // Return as string to preserve exact representation
        return str;
    }

    /**
     * Check if a string looks like it contains a number.
     */
    function looksLikeNumber(str) {
        if (typeof str !== 'string') return false;
        str = str.trim();
        // After cleaning, check if it could be a number
        const cleaned = cleanCurrencySymbols(convertParensToNegative(str));
        const withoutCommas = removeThousandsSeparators(cleaned);
        const final = cleanPercentage(withoutCommas).replace(/\s/g, '');
        return final !== '' && !isNaN(Number(final));
    }

    // Public API
    return {
        removeThousandsSeparators,
        convertParensToNegative,
        cleanCurrencySymbols,
        extractUnit,
        cleanPercentage,
        normalizeNumber,
        looksLikeNumber
    };

})();

// Export for both browser and Node.js
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Normalizer;
}
