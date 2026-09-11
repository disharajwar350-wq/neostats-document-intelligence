/**
 * NeoStats — Main Extraction Engine
 * 
 * Orchestrates the full extraction pipeline:
 * OCR Text → Parse → Match Fields → Normalize → Structure → Validate → Output JSON
 */

const Extractor = (() => {

    /**
     * Fuzzy match a label from OCR text against a list of known aliases.
     * Returns the best matching field or null.
     */
    function matchLabel(label, schema) {
        const normalizedLabel = label.toLowerCase().trim()
            .replace(/[^a-z0-9\s&/()'-]/g, '')  // Remove special chars except common ones
            .replace(/\s+/g, ' ');               // Collapse multiple spaces

        let bestMatch = null;
        let bestScore = 0;

        for (const field of schema.fields) {
            for (const alias of field.aliases) {
                const normalizedAlias = alias.toLowerCase().trim();

                // Exact match
                if (normalizedLabel === normalizedAlias) {
                    return field;
                }

                // Contains match (label contains the alias or vice versa)
                if (normalizedLabel.includes(normalizedAlias) || normalizedAlias.includes(normalizedLabel)) {
                    const score = calculateSimilarity(normalizedLabel, normalizedAlias);
                    if (score > bestScore && score > 0.6) {
                        bestScore = score;
                        bestMatch = field;
                    }
                }

                // Similarity match
                const score = calculateSimilarity(normalizedLabel, normalizedAlias);
                if (score > bestScore && score > 0.75) {
                    bestScore = score;
                    bestMatch = field;
                }
            }
        }

        return bestMatch;
    }

    /**
     * Calculate similarity between two strings (Dice coefficient on bigrams).
     */
    function calculateSimilarity(str1, str2) {
        if (str1 === str2) return 1;
        if (str1.length < 2 || str2.length < 2) return 0;

        const bigrams1 = new Set();
        for (let i = 0; i < str1.length - 1; i++) {
            bigrams1.add(str1.substring(i, i + 2));
        }

        let intersection = 0;
        const bigrams2 = new Set();
        for (let i = 0; i < str2.length - 1; i++) {
            const bigram = str2.substring(i, i + 2);
            bigrams2.add(bigram);
            if (bigrams1.has(bigram)) {
                intersection++;
            }
        }

        return (2 * intersection) / (bigrams1.size + bigrams2.size);
    }

    /**
     * Main extraction function.
     * 
     * @param {string} ocrText - Raw OCR text from the financial document
     * @param {string} documentType - Type of document ("Balance Sheet", "Income Statement", "Cash Flow Statement")
     * @param {string[]} fieldList - Optional list of specific fields to extract (extracts all if empty)
     * @returns {object} Structured JSON output
     */
    function extract(ocrText, documentType, fieldList = []) {
        // Step 1: Get schema
        const schema = Schemas.getSchema(documentType);
        if (!schema) {
            return {
                error: `Unsupported document type: "${documentType}". Supported types: ${Schemas.getSupportedTypes().join(', ')}`,
                document_type: documentType,
                periods: {},
                line_items: []
            };
        }

        // Filter fields if a specific list is provided
        let activeFields = schema.fields;
        if (fieldList && fieldList.length > 0) {
            const requestedNames = fieldList.map(f => f.toLowerCase().trim());
            activeFields = schema.fields.filter(f => 
                requestedNames.includes(f.name.toLowerCase()) ||
                f.aliases.some(a => requestedNames.includes(a.toLowerCase()))
            );
        }

        const activeSchema = { ...schema, fields: activeFields };

        // Step 2: Parse OCR text
        const parsed = Parser.parseDocument(ocrText);

        // Step 3: Match and extract
        const periods = {};
        const lineItems = [];
        const matchedFields = new Set(); // Track which fields we've already matched

        // Initialize periods
        if (parsed.periods.length > 0) {
            for (const period of parsed.periods) {
                periods[period] = {};
            }
        } else {
            // Single period — use "Current" as default key
            periods['Current'] = {};
        }

        const periodKeys = Object.keys(periods);

        // Process each section and item
        for (const section of parsed.sections) {
            for (const item of section.items) {
                // Try to match the label to a schema field
                const matchedField = matchLabel(item.label, activeSchema);

                if (matchedField && !matchedFields.has(matchedField.name)) {
                    matchedFields.add(matchedField.name);

                    // Map values to periods
                    for (let i = 0; i < periodKeys.length; i++) {
                        const periodKey = periodKeys[i];
                        const rawValue = item.values[i] || null;
                        const normalizedValue = rawValue ? Normalizer.normalizeNumber(rawValue) : null;

                        periods[periodKey][matchedField.name] = {
                            value: normalizedValue,
                            raw_value: rawValue,
                            source_text: item.sourceText,
                            page: item.page,
                            field_name: matchedField.name,
                            category: matchedField.category
                        };
                    }
                }

                // Always add to line_items for complete data
                const lineItem = {
                    label: item.label,
                    section: section.header,
                    matched_field: matchedField ? matchedField.name : null,
                    values: {},
                    source_text: item.sourceText,
                    page: item.page
                };

                for (let i = 0; i < periodKeys.length; i++) {
                    const rawValue = item.values[i] || null;
                    lineItem.values[periodKeys[i]] = {
                        raw: rawValue,
                        normalized: rawValue ? Normalizer.normalizeNumber(rawValue) : null
                    };
                }

                lineItems.push(lineItem);
            }
        }

        // Step 4: Ensure all required fields exist (set to null if missing)
        for (const field of activeFields) {
            for (const periodKey of periodKeys) {
                if (!(field.name in periods[periodKey])) {
                    periods[periodKey][field.name] = {
                        value: null,
                        raw_value: null,
                        source_text: null,
                        page: null,
                        field_name: field.name,
                        category: field.category
                    };
                }
            }
        }

        // Step 5: Build output
        const output = {
            document_type: schema.documentType,
            extraction_timestamp: new Date().toISOString(),
            periods_detected: parsed.periods,
            periods,
            line_items: lineItems,
            metadata: {
                total_lines_parsed: parsed.rawLines.length,
                total_sections: parsed.sections.length,
                total_line_items: lineItems.length,
                fields_matched: matchedFields.size,
                fields_total: activeFields.length,
                extraction_rate: activeFields.length > 0 
                    ? ((matchedFields.size / activeFields.length) * 100).toFixed(1) + '%'
                    : '0%'
            }
        };

        // Step 6: Validate
        const validation = Validator.validate(output, documentType);
        output.validation = validation;

        return output;
    }

    /**
     * Quick extract — returns just the periods data without line items.
     */
    function quickExtract(ocrText, documentType) {
        const result = extract(ocrText, documentType);
        const { line_items, ...summary } = result;
        return summary;
    }

    /**
     * Export extracted data as CSV.
     */
    function toCSV(extractionResult) {
        if (!extractionResult || !extractionResult.periods) return '';

        const periodKeys = Object.keys(extractionResult.periods);
        if (periodKeys.length === 0) return '';

        // Get all field names
        const allFields = new Set();
        for (const periodData of Object.values(extractionResult.periods)) {
            for (const fieldName of Object.keys(periodData)) {
                allFields.add(fieldName);
            }
        }

        // Build CSV
        const headers = ['Field', ...periodKeys];
        const rows = [headers.join(',')];

        for (const fieldName of allFields) {
            const row = [fieldName];
            for (const periodKey of periodKeys) {
                const fieldData = extractionResult.periods[periodKey][fieldName];
                const value = fieldData && fieldData.value !== null ? fieldData.value : '';
                row.push(value);
            }
            rows.push(row.join(','));
        }

        return rows.join('\n');
    }

    // Public API
    return {
        extract,
        quickExtract,
        toCSV,
        matchLabel,
        calculateSimilarity
    };

})();

// Export for both browser and Node.js
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Extractor;
}
