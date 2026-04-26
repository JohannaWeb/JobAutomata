// History loading and management
import { escapeHtml, fetchJson, getElement } from './ui.js';

export async function loadHistory() {
  try {
    const data = await fetchJson('/api/history');

    const table = getElement('historyTable');
    if (!data.runs?.length) {
      table.innerHTML = '<tr><td colspan="5" class="table-cell text-center text-neutral-500">No history</td></tr>';
      return;
    }

    table.innerHTML = data.runs.map(run => `
      <tr class="border-b border-neutral-100">
        <td class="table-cell">${escapeHtml(formatDate(run.date))}</td>
        <td class="table-cell">${escapeHtml(run.type)}</td>
        <td class="table-cell font-mono">${escapeHtml(run.companies)}</td>
        <td class="table-cell font-mono">${escapeHtml(run.successful)}</td>
        <td class="table-cell"><span class="badge ${statusClass(run.status)}">${escapeHtml(run.status)}</span></td>
      </tr>
    `).join('');
  } catch (err) {
    console.error('Error:', err);
  }
}

export async function clearHistory() {
  if (!confirm('Clear all history?')) return;
  try {
    await fetchJson('/api/history', { method: 'DELETE' });
    await loadHistory();
  } catch (err) {
    alert('Error: ' + err.message);
  }
}

function formatDate(date) {
  if (!date) return '';
  const parsed = new Date(date);
  return Number.isNaN(parsed.getTime()) ? date : parsed.toLocaleDateString();
}

function statusClass(status) {
  const classes = {
    completed: 'badge-success',
    running: 'badge-info',
    simulated: 'badge-info',
    failed: 'badge-danger',
    error: 'badge-danger',
    timeout: 'badge-warning'
  };
  return classes[status] || 'badge-info';
}
