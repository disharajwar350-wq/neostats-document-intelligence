/**
 * NeoStats — Output Validator
 * 
 * Validates the extracted JSON output against the schema requirements.
 */

const Validator = (() => {

    /**
     * Validate that every non-null value has a source_text field.
     */
    function validateSourceText(periods) {
        const errors = [];
        
        for (const [periodKey, periodData] of Object.entries(periods)) {
            for (const [fieldName, fieldData] of Object.entries(periodData)) {
                if (fieldData && fieldData.value !== null && fieldData.value !== undefined) {
                    if (!fieldData.source_text || fieldData.source_text.trim() === '') {
                        errors.push({
                            type: 'missing_source_text',
                            period: periodKey,
                            field: fieldName,
                            message: `Field "${fieldName}" in period "${periodKey}" has a value but no source_text`
                        });
                    }
                }
            }
        }

        return errors;
    }

    /**
     * Validate that all required fields are present (even if null).
     */
    function validateRequiredFields(periods, schema) {
        const errors = [];
        const requiredFields = schema.fields.filter(f => f.required).map(f => f.name);

        for (const [periodKey, periodData] of Object.entries(periods)) {
            for (const fieldName of requiredFields) {
                if (!(fieldName in periodData)) {
                    errors.push({
                        type: 'missing_required_field',
                        period: periodKey,
                        field: fieldName,
                        message: `Required field "${fieldName}" is missing from period "${periodKey}"`
                    });
                }
            }
        }

        return errors;
    }

    /**
     * Validate that numeric values are valid numbers.
     */
    function validateNumericValues(periods, schema) {
        const errors = [];
        const numericFields = schema.fields.filter(f => f.type === 'number').map(f => f.name);

        for (const [periodKey, periodData] of Object.entries(periods)) {
            for (const fieldName of numericFields) {
                if (fieldName in periodData && periodData[fieldName]) {
                    const val = periodData[fieldName].value;
                    if (val !== null && val !== undefined) {
                        if (isNaN(Number(val))) {
                            errors.push({
                                type: 'invalid_number',
                                period: periodKey,
                                field: fieldName,
                                value: val,
                                message: `Field "${fieldName}" in period "${periodKey}" has non-numeric value: "${val}"`
                            });
                        }
                    }
                }
            }
        }

        return errors;
    }

    /**
     * Full validation of extracted output.
     * Returns { valid: boolean, errors: array, warnings: array }
     */
    function validate(output, documentType) {
        const schema = Schemas.getSchema(documentType);
        if (!schema) {
            return {
                valid: false,
                errors: [{ type: 'unknown_document_type', message: `Unknown document type: "${documentType}"` }],
                warnings: []
            };
        }

        const errors = [];
        const warnings = [];

        // Check basic structure
        if (!output || typeof output !== 'object') {
            errors.push({ type: 'invalid_structure', message: 'Output is not a valid object' });
            return { valid: false, errors, warnings };
        }

        if (!output.periods || typeof output.periods !== 'object') {
            errors.push({ type: 'missing_periods', message: 'Output is missing "periods" object' });
            return { valid: false, errors, warnings };
        }

        if (Object.keys(output.periods).length === 0) {
            warnings.push({ type: 'no_periods', message: 'No periods were extracted' });
        }

        // Validate each period
        errors.push(...validateRequiredFields(output.periods, schema));
        errors.push(...validateSourceText(output.periods));
        errors.push(...validateNumericValues(output.periods, schema));

        // Count extraction stats
        let totalFields = 0;
        let extractedFields = 0;
        let nullFields = 0;

        for (const [periodKey, periodData] of Object.entries(output.periods)) {
            for (const [fieldName, fieldData] of Object.entries(periodData)) {
                totalFields++;
                if (fieldData && fieldData.value !== null && fieldData.value !== undefined) {
                    extractedFields++;
                } else {
                    nullFields++;
                }
            }
        }

        return {
            valid: errors.length === 0,
            errors,
            warnings,
            stats: {
                totalFields,
                extractedFields,
                nullFields,
                extractionRate: totalFields > 0 ? ((extractedFields / totalFields) * 100).toFixed(1) + '%' : '0%'
            }
        };
    }

    // Public API
    return {
        validate,
        validateSourceText,
        validateRequiredFields,
        validateNumericValues
    };

})();

// Export for both browser and Node.js
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Validator;
}
