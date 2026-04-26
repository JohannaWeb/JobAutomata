// Main initialization and global exports
import { switchTab, showLoading, showModal, hideModal } from './ui.js';
import { loadDashboard, showCompaniesTab, startFullRun, startDryRun } from './dashboard.js';
import { executeDryRun } from './dry-run.js';
import * as companies from './companies.js';
import * as cvManager from './cv-manager.js';
import { loadHistory, clearHistory } from './history.js';

// Expose functions globally for onclick handlers in HTML
window.switchTab = switchTab;
window.showLoading = showLoading;
window.showModal = showModal;
window.hideModal = hideModal;
window.loadDashboard = loadDashboard;
window.startFullRun = startFullRun;
window.startDryRun = startDryRun;
window.showCompaniesTab = showCompaniesTab;
window.executeDryRun = executeDryRun;
window.companies = companies;
window.cvManager = cvManager;
window.loadHistory = loadHistory;
window.clearHistory = clearHistory;

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
  loadDashboard();
  loadHistory();
  cvManager.loadCVList();
  companies.loadCompaniesList();
});
