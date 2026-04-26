// Dry run simulation
import { escapeHtml, fetchJson, getElement, showLoading } from './ui.js';

export async function executeDryRun() {
  showLoading(true);
  try {
    const data = await fetchJson('/api/dry-run', { method: 'POST' });
    const resultsData = Array.isArray(data.results) ? data.results : [];

    getElement('dryRunCompanies').textContent = data.companies_count ?? 0;
    getElement('dryRunActions').textContent = resultsData.length;
    getElement('dryRunProgress').style.width = '100%';

    const results = getElement('dryRunResults');
    if (!resultsData.length) {
      results.innerHTML = '<div class="text-sm text-neutral-500 text-center py-8">No simulated actions returned</div>';
      return;
    }

    results.innerHTML = resultsData.map(r => `
      <div class="flex items-center justify-between p-3 rounded-lg bg-neutral-50 border border-neutral-200">
        <div>
          <div class="font-semibold text-neutral-900">${escapeHtml(r.company)}</div>
          <div class="text-xs text-neutral-500">${escapeHtml(r.action)}</div>
        </div>
        <span class="badge badge-success">${escapeHtml(r.status)}</span>
      </div>
    `).join('');
  } catch (err) {
    alert('Error: ' + err.message);
  } finally {
    showLoading(false);
  }
}
