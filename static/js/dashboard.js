// Dashboard stats and rendering
import { fetchJson, getElement, showLoading, switchTab } from './ui.js';
import { loadHistory } from './history.js';
import { loadCompaniesList } from './companies.js';

export async function loadDashboard() {
  try {
    const data = await fetchJson('/api/stats');
    getElement('headerApps').textContent = data.total_applications ?? 0;
    getElement('headerRate').textContent = `${data.success_rate ?? 0}%`;
    getElement('headerLastRun').textContent = data.last_run || 'Never';
    getElement('cardTotalApps').textContent = data.total_applications ?? 0;
    getElement('cardSuccessful').textContent = data.successful_applies ?? 0;
    getElement('cardCompanies').textContent = data.companies ?? 0;
  } catch (err) {
    console.error('Error loading stats:', err);
  }
}

export async function startFullRun() {
  if (!confirm('Launch make apply-interactive for the selected CSV? Continue in the terminal running the dashboard.')) return;
  showLoading(true);
  try {
    const data = await fetchJson('/api/run-full', { method: 'POST' });
    if (!data.success) {
      throw new Error(`Workflow ${data.status || 'failed'}`);
    }
    alert(`Launched: ${data.command}\nPID: ${data.pid}\nContinue in the terminal running the dashboard.`);
    await Promise.all([loadDashboard(), loadHistory()]);
  } catch (err) {
    alert('Error: ' + err.message);
  } finally {
    showLoading(false);
  }
}

export function startDryRun() {
  switchTab('dry-run');
}

export async function showCompaniesTab() {
  switchTab('companies');
  await loadCompaniesList();
}
