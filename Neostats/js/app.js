/**
 * NeoStats — App UI Controller
 * 
 * Handles all UI interactions: document type selection, OCR input,
 * drag-and-drop, extraction trigger, JSON rendering, export.
 */

const App = (() => {

    // ── DOM References ──
    let elements = {};

    // ── Sample Data Cache ──
    const sampleData = {};

    // ── State ──
    let currentResult = null;
    let activeTab = 'json';
    let selectedFile = null;

    /**
     * Initialize the app once DOM is ready.
     */
    function init() {
        cacheElements();
        bindEvents();
        loadSampleData();
        loadHistory();
        updateStats();
        console.log('🚀 NeoStats initialized');
    }

    function renderValidationDetails(result) {
        const checks = result?.validation?.checks || [];
        const evidence = Object.entries(result?.extracted_data || {})
            .filter(([, field]) => field?.evidence)
            .slice(0, 12);
        elements.validationDetails.innerHTML = [
            checks.length ? `<div class="evidence-list">${checks.map(check => `
                <div class="validation-check ${check.status === 'FAIL' ? 'fail' : ''}">
                    <strong>${escapeHtml(check.name)}</strong>: ${escapeHtml(check.status)}
                    ${check.formula ? `<span class="text-muted"> — ${escapeHtml(check.formula)}</span>` : ''}
                    ${check.variance !== null && check.variance !== undefined ? `<span class="text-muted"> (variance ${check.variance})</span>` : ''}
                </div>`).join('')}</div>` : '',
            evidence.length ? `<div class="evidence-list"><strong>Evidence</strong>${evidence.map(([name, field]) => `
                <div class="evidence-item"><strong>${escapeHtml(name)}</strong> — page ${field.evidence.page_number}: ${escapeHtml(field.evidence.source_text)}</div>
            `).join('')}</div>` : ''
        ].join('');
    }

    /**
     * Cache all DOM element references.
     */
    function cacheElements() {
        elements = {
            docTypeSelect: document.getElementById('doc-type-select'),
            ocrTextarea: document.getElementById('ocr-textarea'),
            dropZone: document.getElementById('drop-zone'),
            fileInput: document.getElementById('file-input'),
            extractBtn: document.getElementById('extract-btn'),
            clearBtn: document.getElementById('clear-btn'),
            copyBtn: document.getElementById('copy-btn'),
            downloadJsonBtn: document.getElementById('download-json-btn'),
            downloadCsvBtn: document.getElementById('download-csv-btn'),
            jsonOutput: document.getElementById('json-output'),
            validationBar: document.getElementById('validation-bar'),
            processingOverlay: document.getElementById('processing-overlay'),
            toastContainer: document.getElementById('toast-container'),
            statFields: document.getElementById('stat-fields'),
            statPeriods: document.getElementById('stat-periods'),
            statRate: document.getElementById('stat-rate'),
            tabJson: document.getElementById('tab-json'),
            tabTable: document.getElementById('tab-table'),
            contentJson: document.getElementById('content-json'),
            contentTable: document.getElementById('content-table'),
            lineItemsBody: document.getElementById('line-items-body'),
            validationDetails: document.getElementById('validation-details'),
            historyList: document.getElementById('history-list'),
            refreshHistoryBtn: document.getElementById('refresh-history-btn'),
        };
    }

    /**
     * Bind all event listeners.
     */
    function bindEvents() {
        // Extract button
        elements.extractBtn.addEventListener('click', handleExtract);

        // Clear button
        elements.clearBtn.addEventListener('click', handleClear);

        // Copy button
        elements.copyBtn.addEventListener('click', handleCopy);

        // Download buttons
        elements.downloadJsonBtn.addEventListener('click', () => handleDownload('json'));
        elements.downloadCsvBtn.addEventListener('click', () => handleDownload('csv'));

        // Drag and drop
        const dz = elements.dropZone;
        dz.addEventListener('click', () => elements.fileInput.click());
        dz.addEventListener('dragover', (e) => { e.preventDefault(); dz.classList.add('dragover'); });
        dz.addEventListener('dragleave', () => dz.classList.remove('dragover'));
        dz.addEventListener('drop', handleFileDrop);
        elements.fileInput.addEventListener('change', handleFileSelect);

        // Sample buttons
        document.querySelectorAll('.sample-btn').forEach(btn => {
            btn.addEventListener('click', () => loadSample(btn.dataset.type));
        });

        // Tabs
        elements.tabJson.addEventListener('click', () => switchTab('json'));
        elements.tabTable.addEventListener('click', () => switchTab('table'));
        elements.refreshHistoryBtn.addEventListener('click', loadHistory);

        // Keyboard shortcut: Ctrl+Enter to extract
        document.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                e.preventDefault();
                handleExtract();
            }
        });
    }

    /**
     * Load sample data files.
     */
    async function loadSampleData() {
        const samples = {
            'Balance Sheet': 'samples/balance_sheet.txt',
            'Income Statement': 'samples/income_statement.txt',
            'Cash Flow Statement': 'samples/cash_flow.txt'
        };

        for (const [type, path] of Object.entries(samples)) {
            try {
                const resp = await fetch(path);
                if (resp.ok) {
                    sampleData[type] = await resp.text();
                }
            } catch (err) {
                console.warn(`Could not load sample: ${path}`, err);
            }
        }
    }

    /**
     * Load a sample into the textarea.
     */
    function loadSample(type) {
        if (sampleData[type]) {
            elements.ocrTextarea.value = sampleData[type];
            // Auto-select the matching document type
            elements.docTypeSelect.value = type;
            showToast(`Loaded ${type} sample`, 'info');
        } else {
            showToast(`Sample not available for ${type}`, 'error');
        }
    }

    /**
     * Handle file drop on the drop zone.
     */
    function handleFileDrop(e) {
        e.preventDefault();
        elements.dropZone.classList.remove('dragover');

        const file = e.dataTransfer.files[0];
        if (file) readFile(file);
    }

    /**
     * Handle file selection via input.
     */
    function handleFileSelect(e) {
        const file = e.target.files[0];
        if (file) readFile(file);
    }

    /**
     * Read a text file into the textarea.
     */
    function readFile(file) {
        if (!file.name.match(/\.(pdf|jpg|jpeg|png|txt|text|ocr|csv)$/i)) {
            showToast('Supported files: PDF, JPG, PNG, TXT, OCR, or CSV', 'error');
            return;
        }

        selectedFile = file;
        elements.dropZone.querySelector('.drop-zone-text').innerHTML =
            `<strong>${file.name}</strong> selected — click Extract to process`;
        if (!file.name.match(/\.(txt|text|ocr|csv)$/i)) {
            elements.ocrTextarea.value = '';
            showToast(`Ready to process: ${file.name}`, 'info');
            return;
        }
        const reader = new FileReader();
        reader.onload = (e) => {
            elements.ocrTextarea.value = e.target.result;
            showToast(`Loaded OCR text: ${file.name}`, 'success');
        };
        reader.onerror = () => showToast('Failed to read file', 'error');
        reader.readAsText(file);
    }

    /**
     * Main extraction handler.
     */
    async function handleExtract() {
        const ocrText = elements.ocrTextarea.value.trim();
        const docType = elements.docTypeSelect.value;

        if (!ocrText && !selectedFile) {
            showToast('Please upload a document or paste OCR text first', 'error');
            return;
        }

        if (!docType) {
            showToast('Please select a document type', 'error');
            return;
        }

        showProcessing(true);
        try {
            if (selectedFile && !selectedFile.name.match(/\.(txt|text|ocr|csv)$/i)) {
                const formData = new FormData();
                formData.append('file', selectedFile);
                formData.append('document_type', docType);
                const response = await fetch('/api/v1/documents/process', {
                    method: 'POST',
                    body: formData
                });
                const responseText = await response.text();
                let payload;
                try {
                    payload = responseText ? JSON.parse(responseText) : {};
                } catch {
                    throw new Error(`Backend returned an invalid response (HTTP ${response.status})`);
                }
                if (!response.ok) {
                    throw new Error(payload.error?.message || payload.detail || 'Backend processing failed');
                }
                currentResult = normalizeBackendResult(payload);
                renderOutput(currentResult);
                updateStats(currentResult);
                showValidation(currentResult);
                renderValidationDetails(currentResult);
                renderLineItems(currentResult);
                loadHistory();
                showToast('Document processed successfully!', 'success');
            } else {
                currentResult = Extractor.extract(ocrText, docType);
                renderOutput(currentResult);
                updateStats(currentResult);
                showValidation(currentResult);
                renderValidationDetails(currentResult);
                renderLineItems(currentResult);
                showToast('Extraction complete!', 'success');
            }
        } catch (err) {
            console.error('Extraction error:', err);
            showToast(`Extraction failed: ${err.message}`, 'error');
            renderError(err);
        } finally {
            showProcessing(false);
        }
    }

    function normalizeBackendResult(payload) {
        const data = payload.extracted_data || {};
        const fields = Object.keys(data).filter(key => key !== 'line_items' && data[key]?.value !== null);
        const lineItems = (data.line_items || []).map(item => ({
            label: item.label || item.description || 'Item',
            section: 'Extracted',
            matched_field: '',
            values: { Current: { normalized: item.values?.[0] ?? item.amount ?? null, raw: item.source_text || '' } }
        }));
        return {
            ...payload,
            metadata: {
                fields_matched: fields.length,
                fields_total: Object.keys(data).filter(key => key !== 'line_items').length,
                extraction_rate: `${Object.keys(data).filter(key => key !== 'line_items').length ? Math.round(fields.length / Object.keys(data).filter(key => key !== 'line_items').length * 100) : 0}%`
            },
            periods_detected: ['Current'],
            periods: { Current: {} },
            line_items: lineItems,
            validation: {
                valid: payload.processing_status === 'PASS'
                    && !(payload.validation?.checks || []).some(check => check.status === 'FAIL'),
                warnings: payload.validation?.checks?.filter(check => check.status === 'PASS_WITH_TOLERANCE') || [],
                errors: payload.validation?.checks?.filter(check => check.status === 'FAIL') || [],
                stats: null
            }
        };
    }

    async function loadHistory() {
        try {
            const response = await fetch('/api/v1/documents');
            if (!response.ok) throw new Error('History request failed');
            const documents = await response.json();
            elements.historyList.innerHTML = documents.length
                ? documents.map(document => `
                    <div class="history-row">
                        <span title="${escapeHtml(document.document_name || '')}">${escapeHtml(document.document_name || 'Unnamed')}</span>
                        <span>${escapeHtml(document.document_type || '—')}</span>
                        <span class="history-status ${(document.processing_status || '').toLowerCase()}">${escapeHtml(document.processing_status || '—')}</span>
                        <span class="text-muted">${escapeHtml(document.updated_at || document.created_at || '—')}</span>
                        <button class="btn btn-secondary history-view-btn" data-name="${encodeURIComponent(document.document_name || '')}">View</button>
                    </div>
                `).join('')
                : '<p class="text-muted">No processed documents yet.</p>';
            elements.historyList.querySelectorAll('.history-view-btn').forEach(button => {
                button.addEventListener('click', () => loadHistoryDocument(decodeURIComponent(button.dataset.name)));
            });
        } catch (error) {
            elements.historyList.innerHTML = '<p class="text-muted">History is unavailable until the backend is running.</p>';
        }
    }

    async function loadHistoryDocument(name) {
        try {
            const response = await fetch(`/api/v1/documents/${encodeURIComponent(name)}`);
            const payload = await response.json();
            if (!response.ok) throw new Error(payload.detail || 'Document could not be loaded');
            currentResult = normalizeBackendResult(payload);
            renderOutput(currentResult);
            updateStats(currentResult);
            showValidation(currentResult);
            renderValidationDetails(currentResult);
            renderLineItems(currentResult);
            showToast(`Loaded ${name}`, 'success');
        } catch (error) {
            showToast(error.message, 'error');
        }
    }

    function escapeHtml(value) {
        return String(value).replace(/[&<>"']/g, character => ({
            '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
        }[character]));
    }

    /**
     * Clear all inputs and outputs.
     */
    function handleClear() {
        elements.ocrTextarea.value = '';
        selectedFile = null;
        elements.fileInput.value = '';
        elements.dropZone.querySelector('.drop-zone-text').innerHTML =
            'Drag & drop a PDF, JPG, PNG, or OCR text file here, or <strong>click to browse</strong>';
        elements.jsonOutput.innerHTML = renderPlaceholder();
        elements.validationBar.innerHTML = '';
        elements.validationDetails.innerHTML = '';
        elements.validationBar.className = 'validation-bar';
        elements.validationBar.style.display = 'none';
        elements.lineItemsBody.innerHTML = '';
        currentResult = null;
        updateStats();
        showToast('Cleared', 'info');
    }

    /**
     * Copy JSON output to clipboard.
     */
    async function handleCopy() {
        if (!currentResult) {
            showToast('No results to copy', 'error');
            return;
        }

        try {
            await navigator.clipboard.writeText(JSON.stringify(currentResult, null, 2));
            showToast('Copied to clipboard!', 'success');
        } catch (err) {
            // Fallback
            const textarea = document.createElement('textarea');
            textarea.value = JSON.stringify(currentResult, null, 2);
            document.body.appendChild(textarea);
            textarea.select();
            document.execCommand('copy');
            document.body.removeChild(textarea);
            showToast('Copied to clipboard!', 'success');
        }
    }

    /**
     * Download results as JSON or CSV.
     */
    function handleDownload(format) {
        if (!currentResult) {
            showToast('No results to download', 'error');
            return;
        }

        let content, filename, mimeType;

        if (format === 'json') {
            content = JSON.stringify(currentResult, null, 2);
            filename = `neostats_${currentResult.document_type.replace(/\s+/g, '_').toLowerCase()}_${Date.now()}.json`;
            mimeType = 'application/json';
        } else {
            content = Extractor.toCSV(currentResult);
            filename = `neostats_${currentResult.document_type.replace(/\s+/g, '_').toLowerCase()}_${Date.now()}.csv`;
            mimeType = 'text/csv';
        }

        const blob = new Blob([content], { type: mimeType });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        showToast(`Downloaded ${filename}`, 'success');
    }

    /**
     * Render JSON output with syntax highlighting.
     */
    function renderOutput(result) {
        const json = JSON.stringify(result, null, 2);
        const highlighted = highlightJSON(json);
        elements.jsonOutput.innerHTML = `<pre>${highlighted}</pre>`;
    }

    /**
     * JSON syntax highlighting.
     */
    function highlightJSON(json) {
        return json.replace(
            /("(?:[^"\\]|\\.)*")\s*:/g,
            '<span class="json-key">$1</span>:'
        ).replace(
            /:\s*("(?:[^"\\]|\\.)*")/g,
            ': <span class="json-string">$1</span>'
        ).replace(
            /:\s*(-?\d+\.?\d*(?:e[+-]?\d+)?)/gi,
            ': <span class="json-number">$1</span>'
        ).replace(
            /:\s*(true|false)/g,
            ': <span class="json-boolean">$1</span>'
        ).replace(
            /:\s*(null)/g,
            ': <span class="json-null">$1</span>'
        ).replace(
            /([{}[\]])/g,
            '<span class="json-brace">$1</span>'
        );
    }

    /**
     * Render placeholder state.
     */
    function renderPlaceholder() {
        return `
            <div class="placeholder-state">
                <div class="placeholder-icon">📊</div>
                <div class="placeholder-title">Ready to Extract</div>
                <div class="placeholder-text">
                    Paste OCR text, select a document type, and click Extract to see structured JSON output here.
                </div>
            </div>
        `;
    }

    /**
     * Render error state.
     */
    function renderError(err) {
        elements.jsonOutput.innerHTML = `
            <div class="placeholder-state">
                <div class="placeholder-icon">⚠️</div>
                <div class="placeholder-title" style="color: var(--accent-danger)">Extraction Error</div>
                <div class="placeholder-text">${err.message}</div>
            </div>
        `;
    }

    /**
     * Show/hide processing overlay.
     */
    function showProcessing(show) {
        elements.processingOverlay.classList.toggle('active', show);
    }

    /**
     * Show validation results bar.
     */
    function showValidation(result) {
        if (!result || !result.validation) return;

        const v = result.validation;
        const bar = elements.validationBar;

        let className = 'validation-bar';
        let icon = '';
        let message = '';

        if (v.valid && v.warnings.length === 0) {
            className += ' valid';
            icon = '✓';
            message = 'All validations passed';
        } else if (v.valid && v.warnings.length > 0) {
            className += ' warning';
            icon = '⚡';
            message = `Valid with ${v.warnings.length} warning(s)`;
        } else {
            className += ' invalid';
            icon = '✗';
            message = `${v.errors.length} validation error(s)`;
        }

        bar.className = className;
        bar.style.display = 'flex';
        bar.innerHTML = `
            <span>${icon} ${message}</span>
            ${v.stats ? `
                <div class="validation-stats">
                    <span class="validation-stat">📋 ${v.stats.extractedFields}/${v.stats.totalFields} fields</span>
                    <span class="validation-stat">📈 ${v.stats.extractionRate}</span>
                </div>
            ` : ''}
        `;
    }

    /**
     * Update the stats bar.
     */
    function updateStats(result) {
        if (!result) {
            elements.statFields.textContent = '—';
            elements.statPeriods.textContent = '—';
            elements.statRate.textContent = '—';
            return;
        }

        elements.statFields.textContent = result.metadata.fields_matched + '/' + result.metadata.fields_total;
        elements.statPeriods.textContent = result.periods_detected.length || '1';
        elements.statRate.textContent = result.metadata.extraction_rate;
    }

    /**
     * Render line items table.
     */
    function renderLineItems(result) {
        if (!result || !result.line_items) return;

        const periods = Object.keys(result.periods);
        const tbody = elements.lineItemsBody;
        tbody.innerHTML = '';

        // Update table header with period columns
        const thead = tbody.closest('table').querySelector('thead tr');
        // Clear existing period columns (keep first 3 static columns)
        while (thead.children.length > 3) {
            thead.removeChild(thead.lastChild);
        }
        // Add period columns
        for (const period of periods) {
            const th = document.createElement('th');
            th.textContent = period;
            th.style.textAlign = 'right';
            thead.appendChild(th);
        }

        // Render rows
        for (const item of result.line_items) {
            const tr = document.createElement('tr');

            // Label
            const tdLabel = document.createElement('td');
            tdLabel.textContent = item.label;
            tdLabel.className = item.matched_field ? 'matched' : 'unmatched';
            tr.appendChild(tdLabel);

            // Section
            const tdSection = document.createElement('td');
            tdSection.textContent = item.section;
            tdSection.style.color = 'var(--text-tertiary)';
            tdSection.style.fontSize = '0.75rem';
            tr.appendChild(tdSection);

            // Matched field
            const tdMatch = document.createElement('td');
            tdMatch.textContent = item.matched_field || '—';
            tdMatch.className = 'font-mono';
            tdMatch.style.fontSize = '0.75rem';
            tdMatch.style.color = item.matched_field ? 'var(--accent-tertiary)' : 'var(--text-tertiary)';
            tr.appendChild(tdMatch);

            // Values for each period
            for (const period of periods) {
                const td = document.createElement('td');
                td.className = 'value-cell';
                const val = item.values[period];
                if (val && val.normalized !== null) {
                    td.textContent = formatNumber(val.normalized);
                } else if (val && val.raw) {
                    td.textContent = val.raw;
                    td.style.color = 'var(--text-tertiary)';
                } else {
                    td.textContent = '—';
                    td.style.color = 'var(--text-tertiary)';
                }
                tr.appendChild(td);
            }

            tbody.appendChild(tr);
        }
    }

    /**
     * Format a number for display with commas.
     */
    function formatNumber(numStr) {
        const num = parseFloat(numStr);
        if (isNaN(num)) return numStr;
        return num.toLocaleString('en-IN');
    }

    /**
     * Switch between JSON and Table tabs.
     */
    function switchTab(tab) {
        activeTab = tab;
        elements.tabJson.classList.toggle('active', tab === 'json');
        elements.tabTable.classList.toggle('active', tab === 'table');
        elements.contentJson.classList.toggle('active', tab === 'json');
        elements.contentTable.classList.toggle('active', tab === 'table');
    }

    /**
     * Show a toast notification.
     */
    function showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;

        const icons = { success: '✓', error: '✗', info: 'ℹ', warning: '⚡' };
        toast.innerHTML = `<span>${icons[type] || 'ℹ'}</span> ${message}`;

        elements.toastContainer.appendChild(toast);

        // Auto-remove after 3 seconds
        setTimeout(() => {
            toast.classList.add('toast-exit');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    // Public API
    return { init };

})();

// Boot
document.addEventListener('DOMContentLoaded', App.init);
