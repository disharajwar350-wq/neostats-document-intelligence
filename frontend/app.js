const form = document.querySelector("#process-form");
const message = document.querySelector("#message");
const documents = document.querySelector("#documents");
const summary = document.querySelector("#summary");
const result = document.querySelector("#result");

function render(payload) {
  const fields = Object.entries(payload.extracted_data || {})
    .filter(([key, item]) => key !== "raw_text" && key !== "line_items" && item.value !== null)
    .map(([key, item]) => `<div class="field"><strong>${key}</strong><span>${item.value ?? "Missing"}</span></div>`)
    .join("");
  const checks = (payload.validation?.checks || [])
    .map(check => `<li class="${check.status.toLowerCase()}">${check.name}: ${check.status} (variance ${check.variance ?? "n/a"})</li>`)
    .join("");
  summary.hidden = false;
  summary.innerHTML = `
    <h2>${payload.document_name}</h2>
    <p><strong>${payload.document_type}</strong> · Processing: ${payload.processing_status} · Validation: ${payload.validation.overall_status}</p>
    <div class="fields">${fields}</div>
    <h3>Financial checks</h3><ul>${checks || "<li>NOT_APPLICABLE</li>"}</ul>`;
}

async function refresh() {
  const response = await fetch("/api/v1/documents");
  const items = await response.json();
  documents.innerHTML = items.map(item =>
    `<button class="document" data-name="${item.document_name}">
      <strong>${item.document_name}</strong>
      <span>${item.document_type} · ${item.processing_status}</span>
    </button>`
  ).join("");
  documents.querySelectorAll(".document").forEach(button => {
    button.onclick = () => show(button.dataset.name);
  });
}

async function show(name) {
  const response = await fetch(`/api/v1/documents/${encodeURIComponent(name)}`);
  const payload = await response.json();
  render(payload);
  result.textContent = JSON.stringify(payload, null, 2);
}

form.onsubmit = async event => {
  event.preventDefault();
  message.textContent = "Processing...";
  const body = new FormData();
  body.append("file", document.querySelector("#file").files[0]);
  body.append("document_type", document.querySelector("#document-type").value);
  const response = await fetch("/api/v1/documents/process", { method: "POST", body });
  const payload = await response.json();
  if (!response.ok) {
    message.textContent = payload.detail?.message || "Processing failed.";
    return;
  }
  message.textContent = "Processed successfully.";
  render(payload);
  result.textContent = JSON.stringify(payload, null, 2);
  await refresh();
};

refresh().catch(() => { message.textContent = "Could not load processed documents."; });
