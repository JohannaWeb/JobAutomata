// CV upload and selection management
import { escapeHtml, fetchJson, getElement } from './ui.js';

export async function uploadCV() {
  const fileInput = getElement('cvFileInput');
  const file = fileInput.files[0];
  if (!file) { alert('Select a file'); return; }
  if (!file.name.endsWith('.md')) { alert('Only .md files'); return; }

  const formData = new FormData();
  formData.append('file', file);

  try {
    const status = getElement('uploadStatus');
    status.innerHTML = '<div class="text-sm text-primary-600">Uploading...</div>';

    const data = await fetchJson('/api/cvs/upload', { method: 'POST', body: formData });

    if (data.success) {
      status.innerHTML = `<div class="text-sm text-emerald-600">✓ Uploaded: ${escapeHtml(data.filename)}</div>`;
      fileInput.value = '';
      await loadCVList();
    }
  } catch (err) {
    getElement('uploadStatus').innerHTML = `<div class="text-sm text-red-600">Error: ${escapeHtml(err.message)}</div>`;
  }
}

export async function loadCVList() {
  try {
    const data = await fetchJson('/api/cvs');
    const cvs = Array.isArray(data.cvs) ? data.cvs : [];

    getElement('cvsList').innerHTML = cvs.length ? cvs.map(cv => `
      <div class="flex items-center justify-between p-4 rounded-lg border ${cv === data.current ? 'bg-primary-50 border-primary-300' : 'bg-white border-neutral-200'}" data-cv="${escapeHtml(cv)}">
        <div class="font-semibold text-neutral-900">${escapeHtml(cv)}</div>
        ${cv !== data.current ? `<button onclick="window.cvManager.selectCV(event)" class="btn btn-primary text-sm">Select</button>` : '<span class="text-primary-600 font-semibold">Active</span>'}
      </div>
    `).join('') : '<div class="text-sm text-neutral-500 text-center py-8">No CVs found</div>';
  } catch (err) {
    console.error('Error:', err);
  }
}

export async function selectCV(event) {
  const cvName = event.target.closest('[data-cv]').dataset.cv;
  try {
    const data = await fetchJson('/api/cvs/select', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ cv: cvName })
    });
    if (data.success) await loadCVList();
  } catch (err) {
    alert('Error: ' + err.message);
  }
}
