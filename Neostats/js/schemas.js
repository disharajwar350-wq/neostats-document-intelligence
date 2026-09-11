/**
 * NeoStats — Document Type Schemas
 * 
 * Defines the fields, aliases, and output shapes for each supported
 * financial document type.
 */

const Schemas = (() => {

    /**
     * Each field definition:
     * - name: canonical field name used in output JSON
     * - aliases: array of label variations found in OCR (case-insensitive matching)
     * - type: "number" | "string" | "date"
     * - required: whether this field is expected (missing → null, not omitted)
     * - category: grouping for output organization
     */

    const BALANCE_SHEET = {
        documentType: 'Balance Sheet',
        fields: [
            // Assets
            { name: 'total_assets', aliases: ['total assets', 'assets total', 'total asset'], type: 'number', required: true, category: 'Assets' },
            { name: 'current_assets', aliases: ['current assets', 'total current assets'], type: 'number', required: true, category: 'Assets' },
            { name: 'non_current_assets', aliases: ['non-current assets', 'non current assets', 'total non-current assets', 'total non current assets'], type: 'number', required: false, category: 'Assets' },
            { name: 'cash_and_equivalents', aliases: ['cash and cash equivalents', 'cash & cash equivalents', 'cash and bank balances', 'cash & bank', 'cash'], type: 'number', required: false, category: 'Assets' },
            { name: 'trade_receivables', aliases: ['trade receivables', 'accounts receivable', 'sundry debtors', 'debtors'], type: 'number', required: false, category: 'Assets' },
            { name: 'inventories', aliases: ['inventories', 'inventory', 'stock-in-trade', 'stock in trade'], type: 'number', required: false, category: 'Assets' },
            { name: 'fixed_assets', aliases: ['fixed assets', 'property plant and equipment', 'property, plant and equipment', 'ppe', 'tangible assets', 'net fixed assets', 'total fixed assets'], type: 'number', required: false, category: 'Assets' },
            { name: 'intangible_assets', aliases: ['intangible assets', 'goodwill', 'goodwill and intangible assets'], type: 'number', required: false, category: 'Assets' },
            { name: 'investments', aliases: ['investments', 'total investments', 'non-current investments', 'current investments'], type: 'number', required: false, category: 'Assets' },
            { name: 'other_assets', aliases: ['other assets', 'other current assets', 'other non-current assets'], type: 'number', required: false, category: 'Assets' },
            { name: 'loans_and_advances', aliases: ['loans and advances', 'loans & advances', 'short term loans and advances', 'long term loans and advances'], type: 'number', required: false, category: 'Assets' },

            // Liabilities
            { name: 'total_liabilities', aliases: ['total liabilities', 'liabilities total'], type: 'number', required: true, category: 'Liabilities' },
            { name: 'current_liabilities', aliases: ['current liabilities', 'total current liabilities'], type: 'number', required: true, category: 'Liabilities' },
            { name: 'non_current_liabilities', aliases: ['non-current liabilities', 'non current liabilities', 'total non-current liabilities', 'long term liabilities'], type: 'number', required: false, category: 'Liabilities' },
            { name: 'trade_payables', aliases: ['trade payables', 'accounts payable', 'sundry creditors', 'creditors'], type: 'number', required: false, category: 'Liabilities' },
            { name: 'borrowings', aliases: ['borrowings', 'total borrowings', 'short term borrowings', 'long term borrowings', 'debt', 'total debt'], type: 'number', required: false, category: 'Liabilities' },
            { name: 'provisions', aliases: ['provisions', 'total provisions'], type: 'number', required: false, category: 'Liabilities' },
            { name: 'other_liabilities', aliases: ['other liabilities', 'other current liabilities', 'other non-current liabilities'], type: 'number', required: false, category: 'Liabilities' },

            // Equity
            { name: 'shareholders_equity', aliases: ['shareholders equity', "shareholder's equity", "shareholders' equity", 'total equity', 'equity', 'net worth', 'total shareholders funds', "shareholders' funds"], type: 'number', required: true, category: 'Equity' },
            { name: 'share_capital', aliases: ['share capital', 'equity share capital', 'paid-up capital', 'paid up capital', 'issued capital'], type: 'number', required: false, category: 'Equity' },
            { name: 'reserves_and_surplus', aliases: ['reserves and surplus', 'reserves & surplus', 'retained earnings', 'other equity'], type: 'number', required: false, category: 'Equity' },
            { name: 'minority_interest', aliases: ['minority interest', 'non-controlling interest', 'non controlling interest'], type: 'number', required: false, category: 'Equity' },

            // Totals
            { name: 'total_equity_and_liabilities', aliases: ['total equity and liabilities', 'total liabilities and equity', 'total liabilities & equity'], type: 'number', required: false, category: 'Totals' },
        ]
    };

    const INCOME_STATEMENT = {
        documentType: 'Income Statement',
        fields: [
            // Revenue
            { name: 'revenue', aliases: ['revenue', 'revenue from operations', 'total revenue', 'net revenue', 'total income', 'income from operations', 'net sales', 'sales', 'turnover', 'gross revenue'], type: 'number', required: true, category: 'Revenue' },
            { name: 'other_income', aliases: ['other income', 'other operating income', 'non-operating income'], type: 'number', required: false, category: 'Revenue' },

            // Expenses
            { name: 'cost_of_goods_sold', aliases: ['cost of goods sold', 'cogs', 'cost of revenue', 'cost of sales', 'cost of materials consumed', 'material costs'], type: 'number', required: false, category: 'Expenses' },
            { name: 'total_expenses', aliases: ['total expenses', 'total expenditure'], type: 'number', required: false, category: 'Expenses' },
            { name: 'employee_expenses', aliases: ['employee benefit expense', 'employee expenses', 'employee costs', 'staff costs', 'personnel expenses', 'salaries and wages'], type: 'number', required: false, category: 'Expenses' },
            { name: 'depreciation', aliases: ['depreciation', 'depreciation and amortisation', 'depreciation and amortization', 'depreciation & amortisation', 'd&a'], type: 'number', required: false, category: 'Expenses' },
            { name: 'finance_costs', aliases: ['finance costs', 'finance cost', 'interest expense', 'interest cost', 'interest and finance charges'], type: 'number', required: false, category: 'Expenses' },
            { name: 'other_expenses', aliases: ['other expenses', 'other expenditure', 'selling and administrative expenses', 'sg&a', 'sga'], type: 'number', required: false, category: 'Expenses' },

            // Profitability
            { name: 'gross_profit', aliases: ['gross profit', 'gross margin'], type: 'number', required: false, category: 'Profitability' },
            { name: 'operating_profit', aliases: ['operating profit', 'operating income', 'ebit', 'profit from operations'], type: 'number', required: false, category: 'Profitability' },
            { name: 'ebitda', aliases: ['ebitda', 'earnings before interest tax depreciation and amortization'], type: 'number', required: false, category: 'Profitability' },
            { name: 'profit_before_tax', aliases: ['profit before tax', 'pbt', 'income before tax', 'earnings before tax', 'profit before taxation'], type: 'number', required: true, category: 'Profitability' },
            { name: 'tax_expense', aliases: ['tax expense', 'income tax expense', 'tax', 'provision for tax', 'income tax'], type: 'number', required: false, category: 'Profitability' },
            { name: 'net_profit', aliases: ['net profit', 'net income', 'profit after tax', 'pat', 'profit for the period', 'profit for the year', 'net profit after tax', 'profit/(loss) for the period'], type: 'number', required: true, category: 'Profitability' },

            // Per Share
            { name: 'eps_basic', aliases: ['basic eps', 'earnings per share basic', 'earnings per share - basic', 'eps (basic)'], type: 'number', required: false, category: 'Per Share' },
            { name: 'eps_diluted', aliases: ['diluted eps', 'earnings per share diluted', 'earnings per share - diluted', 'eps (diluted)'], type: 'number', required: false, category: 'Per Share' },
        ]
    };

    const CASH_FLOW_STATEMENT = {
        documentType: 'Cash Flow Statement',
        fields: [
            // Operating Activities
            { name: 'cash_from_operations', aliases: ['cash from operating activities', 'net cash from operating activities', 'cash flow from operating activities', 'operating cash flow', 'cash generated from operations', 'net cash generated from operating activities', 'cfo'], type: 'number', required: true, category: 'Operating Activities' },
            { name: 'profit_before_tax', aliases: ['profit before tax', 'pbt', 'net profit before tax'], type: 'number', required: false, category: 'Operating Activities' },
            { name: 'depreciation_cf', aliases: ['depreciation', 'depreciation and amortisation', 'depreciation and amortization'], type: 'number', required: false, category: 'Operating Activities' },
            { name: 'working_capital_changes', aliases: ['working capital changes', 'changes in working capital', 'adjustments for changes in working capital'], type: 'number', required: false, category: 'Operating Activities' },
            { name: 'tax_paid', aliases: ['income tax paid', 'tax paid', 'taxes paid'], type: 'number', required: false, category: 'Operating Activities' },

            // Investing Activities
            { name: 'cash_from_investing', aliases: ['cash from investing activities', 'net cash from investing activities', 'cash flow from investing activities', 'investing cash flow', 'net cash used in investing activities', 'cfi'], type: 'number', required: true, category: 'Investing Activities' },
            { name: 'capex', aliases: ['capital expenditure', 'capex', 'purchase of fixed assets', 'purchase of property plant and equipment', 'purchase of ppe', 'acquisition of fixed assets'], type: 'number', required: false, category: 'Investing Activities' },
            { name: 'investment_purchases', aliases: ['purchase of investments', 'investments purchased'], type: 'number', required: false, category: 'Investing Activities' },
            { name: 'investment_sales', aliases: ['sale of investments', 'proceeds from sale of investments', 'investments sold'], type: 'number', required: false, category: 'Investing Activities' },

            // Financing Activities
            { name: 'cash_from_financing', aliases: ['cash from financing activities', 'net cash from financing activities', 'cash flow from financing activities', 'financing cash flow', 'net cash used in financing activities', 'cff'], type: 'number', required: true, category: 'Financing Activities' },
            { name: 'dividends_paid', aliases: ['dividends paid', 'dividend paid', 'payment of dividends'], type: 'number', required: false, category: 'Financing Activities' },
            { name: 'borrowings_raised', aliases: ['proceeds from borrowings', 'borrowings raised', 'proceeds from long term borrowings', 'proceeds from short term borrowings'], type: 'number', required: false, category: 'Financing Activities' },
            { name: 'borrowings_repaid', aliases: ['repayment of borrowings', 'borrowings repaid', 'repayment of long term borrowings', 'repayment of short term borrowings'], type: 'number', required: false, category: 'Financing Activities' },
            { name: 'interest_paid', aliases: ['interest paid', 'finance costs paid'], type: 'number', required: false, category: 'Financing Activities' },

            // Net Change
            { name: 'net_change_in_cash', aliases: ['net increase in cash', 'net decrease in cash', 'net change in cash', 'net increase/(decrease) in cash', 'net increase/decrease in cash and cash equivalents'], type: 'number', required: true, category: 'Net Change' },
            { name: 'opening_cash', aliases: ['opening cash', 'cash at beginning', 'cash and cash equivalents at beginning', 'opening balance'], type: 'number', required: false, category: 'Net Change' },
            { name: 'closing_cash', aliases: ['closing cash', 'cash at end', 'cash and cash equivalents at end', 'closing balance'], type: 'number', required: false, category: 'Net Change' },
        ]
    };

    const INVOICE = {
        documentType: 'Invoice',
        fields: [
            { name: 'invoice_number', aliases: ['invoice number', 'invoice no', 'invoice #', 'invoice id'], type: 'string', required: false, category: 'Identity' },
            { name: 'invoice_date', aliases: ['invoice date', 'date issued', 'issue date'], type: 'date', required: false, category: 'Identity' },
            { name: 'vendor', aliases: ['vendor', 'seller', 'from', 'supplier'], type: 'string', required: false, category: 'Parties' },
            { name: 'customer', aliases: ['customer', 'buyer', 'bill to', 'client'], type: 'string', required: false, category: 'Parties' },
            { name: 'subtotal', aliases: ['subtotal', 'sub total', 'amount before tax'], type: 'number', required: true, category: 'Totals' },
            { name: 'tax_amount', aliases: ['tax', 'sales tax', 'vat', 'gst', 'tax amount'], type: 'number', required: false, category: 'Totals' },
            { name: 'shipping_and_handling', aliases: ['shipping', 'shipping & handling', 'shipping and handling', 'delivery'], type: 'number', required: false, category: 'Totals' },
            { name: 'discount', aliases: ['discount', 'less discount'], type: 'number', required: false, category: 'Totals' },
            { name: 'total_amount', aliases: ['total due', 'amount due', 'grand total', 'invoice total', 'total'], type: 'number', required: true, category: 'Totals' }
        ]
    };

    /**
     * Get schema for a document type.
     */
    function getSchema(documentType) {
        const type = documentType.toLowerCase().trim();
        if (type.includes('balance') || type.includes('bs')) return BALANCE_SHEET;
        if (type.includes('income') || type.includes('p&l') || type.includes('profit') || type.includes('pnl') || type.includes('p & l')) return INCOME_STATEMENT;
        if (type.includes('cash flow') || type.includes('cashflow') || type.includes('cf')) return CASH_FLOW_STATEMENT;
        if (type.includes('invoice') || type.includes('bill')) return INVOICE;
        return null;
    }

    /**
     * Get all supported document types.
     */
    function getSupportedTypes() {
        return ['Balance Sheet', 'Income Statement', 'Cash Flow Statement', 'Invoice'];
    }

    /**
     * Generate the expected output JSON shape for a document type.
     */
    function getOutputTemplate(documentType) {
        const schema = getSchema(documentType);
        if (!schema) return null;

        return {
            document_type: schema.documentType,
            extraction_timestamp: null,
            periods: {},
            line_items: [],
            metadata: {
                total_fields: schema.fields.length,
                required_fields: schema.fields.filter(f => f.required).map(f => f.name),
                categories: [...new Set(schema.fields.map(f => f.category))]
            }
        };
    }

    // Public API
    return {
        BALANCE_SHEET,
        INCOME_STATEMENT,
        CASH_FLOW_STATEMENT,
        INVOICE,
        getSchema,
        getSupportedTypes,
        getOutputTemplate
    };

})();

// Export for both browser and Node.js
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Schemas;
}
