/**
 * NeoStats — OCR Text Parser
 * 
 * Parses raw OCR text into structured lines, detects table layouts,
 * identifies period columns, and tracks page provenance.
 */

const Parser = (() => {

    /**
     * Split OCR text into logical lines, tracking page numbers.
     * Handles page markers like "--- Page N ---", "Page N", "[Page N]", etc.
     */
    function splitIntoLines(ocrText) {
        const rawLines = ocrText.split(/\r?\n/);
        const result = [];
        let currentPage = 1;

        for (let i = 0; i < rawLines.length; i++) {
            const line = rawLines[i];

            // Detect page markers
            const pageMatch = line.match(/(?:---\s*)?[Pp]age\s+(\d+)\s*(?:---)?/);
            if (pageMatch) {
                currentPage = parseInt(pageMatch[1], 10);
                continue; // Skip the page marker line itself
            }

            // Also detect markers like "[Page 2]" or "-- Page 2 --"
            const altPageMatch = line.match(/\[?\s*[Pp]age\s*(\d+)\s*\]?/);
            if (altPageMatch && line.trim().length < 20) {
                currentPage = parseInt(altPageMatch[1], 10);
                continue;
            }

            // Skip completely empty lines
            if (line.trim() === '') continue;

            result.push({
                lineNumber: i + 1,
                text: line,
                trimmedText: line.trim(),
                page: currentPage
            });
        }

        return result;
    }

    /**
     * Detect period/date columns from header rows.
     * Looks for patterns like: "31-Mar-17", "FY2024", "2023", "Mar 2024", etc.
     */
    function detectPeriods(lines) {
        const periodPatterns = [
            // "31-Mar-17", "31-Mar-2017"
            /\d{1,2}[-\/]\w{3}[-\/]\d{2,4}/g,
            // "FY2024", "FY 2024", "FY24"
            /FY\s*\d{2,4}/gi,
            // "Mar 2024", "March 2024"
            /(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[\s,]+\d{4}/gi,
            // "2023-24", "2023-2024"
            /\d{4}[-\/]\d{2,4}/g,
            // Standalone 4-digit years (only in header-like context)
            /(?<!\d)\d{4}(?!\d)/g,
            // "Q1 2024", "Q1FY24"
            /Q[1-4]\s*(?:FY)?\s*\d{2,4}/gi,
            // "H1 2024", "H1FY24"
            /H[12]\s*(?:FY)?\s*\d{2,4}/gi,
        ];

        const detectedPeriods = [];

        // Check the first 15 lines for period headers
        const headerLines = lines.slice(0, Math.min(15, lines.length));

        for (const line of headerLines) {
            for (const pattern of periodPatterns) {
                const matches = line.trimmedText.matchAll(pattern);
                for (const match of matches) {
                    const period = match[0].trim();
                    if (!detectedPeriods.includes(period)) {
                        detectedPeriods.push(period);
                    }
                }
                // Reset the regex
                pattern.lastIndex = 0;
            }
        }

        return detectedPeriods;
    }

    /**
     * Parse a line into label + numeric values.
     * Handles tab-separated and space-separated layouts.
     * 
     * Returns: { label: string, values: string[] }
     */
    function parseDataLine(lineText) {
        // Strategy 1: Tab-separated
        if (lineText.includes('\t')) {
            const parts = lineText.split('\t').map(p => p.trim()).filter(p => p !== '');
            if (parts.length >= 2) {
                const label = parts[0];
                const values = parts.slice(1);
                return { label, values };
            }
        }

        // Strategy 2: Multiple-space separated (common in OCR)
        // Split on 2+ spaces
        const parts = lineText.split(/\s{2,}/).map(p => p.trim()).filter(p => p !== '');
        if (parts.length >= 2) {
            // Find where the numbers start
            let labelParts = [];
            let valueParts = [];
            let foundNumber = false;

            for (let i = parts.length - 1; i >= 0; i--) {
                if (!foundNumber && Normalizer.looksLikeNumber(parts[i])) {
                    valueParts.unshift(parts[i]);
                } else {
                    foundNumber = true;
                    labelParts = parts.slice(0, i + 1);
                    break;
                }
            }

            if (labelParts.length > 0 && valueParts.length > 0) {
                return { label: labelParts.join(' '), values: valueParts };
            }
        }

        // Strategy 3: Single value at the end
        const singleValueMatch = lineText.match(/^(.+?)\s+([\d,.()\-]+)\s*$/);
        if (singleValueMatch) {
            return {
                label: singleValueMatch[1].trim(),
                values: [singleValueMatch[2].trim()]
            };
        }

        // No numeric values found — treat entire line as a label/header
        return { label: lineText.trim(), values: [] };
    }

    /**
     * Detect if a line is a section header (bold, uppercase, or followed by a separator).
     */
    function isSectionHeader(line, nextLine) {
        const text = line.trimmedText;

        // All uppercase
        if (text === text.toUpperCase() && text.length > 3 && !/\d/.test(text)) {
            return true;
        }

        // Ends with colon
        if (text.endsWith(':')) return true;

        // Line has no numbers and is relatively short
        if (!Normalizer.looksLikeNumber(text) && text.length < 60 && !text.includes('\t')) {
            const parsed = parseDataLine(text);
            if (parsed.values.length === 0) return true;
        }

        return false;
    }

    /**
     * Parse the full OCR text into a structured document.
     * Returns:
     * {
     *   periods: string[],
     *   sections: [{ header: string, items: [{ label, values, sourceLine, page }] }],
     *   rawLines: [{ lineNumber, text, page }]
     * }
     */
    function parseDocument(ocrText) {
        const lines = splitIntoLines(ocrText);
        const periods = detectPeriods(lines);

        const sections = [];
        let currentSection = { header: 'General', items: [] };

        for (let i = 0; i < lines.length; i++) {
            const line = lines[i];
            const nextLine = i + 1 < lines.length ? lines[i + 1] : null;

            // Check if this is a period header line (skip it, already captured)
            if (periods.length > 0) {
                let isPeriodLine = false;
                for (const period of periods) {
                    if (line.trimmedText.includes(period)) {
                        isPeriodLine = true;
                        break;
                    }
                }
                // If the line ONLY contains periods (no data label), skip
                if (isPeriodLine) {
                    const parsed = parseDataLine(line.trimmedText);
                    if (parsed.values.length === 0 || parsed.label.length < 3) {
                        continue;
                    }
                }
            }

            // Check if this is a section header
            if (isSectionHeader(line, nextLine)) {
                if (currentSection.items.length > 0) {
                    sections.push(currentSection);
                }
                currentSection = { header: line.trimmedText.replace(/:$/, ''), items: [] };
                continue;
            }

            // Parse as data line
            const parsed = parseDataLine(line.trimmedText);
            if (parsed.label) {
                currentSection.items.push({
                    label: parsed.label,
                    values: parsed.values,
                    sourceText: line.text.trim(),
                    page: line.page,
                    lineNumber: line.lineNumber
                });
            }
        }

        // Push last section
        if (currentSection.items.length > 0) {
            sections.push(currentSection);
        }

        return {
            periods,
            sections,
            rawLines: lines
        };
    }

    // Public API
    return {
        splitIntoLines,
        detectPeriods,
        parseDataLine,
        isSectionHeader,
        parseDocument
    };

})();

// Export for both browser and Node.js
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Parser;
}
