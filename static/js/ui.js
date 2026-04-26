// UI utilities and modal management
export function getElement(id) {
  const element = document.getElementById(id);
  if (!element) {
    throw new Error(`Missing expected element: #${id}`);
  }
  return element;
}

export async function fetchJson(url, options = {}) {
  const response = await fetch(url, options);
  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(data.error || `Request failed with status ${response.status}`);
  }

  return data;
}

export function escapeHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}

export function switchTab(tabName, tabButton = null) {
  document.querySelectorAll('.tab-content').forEach(el => el.classList.add('hidden'));
  document.querySelectorAll('.tab-btn').forEach(el => {
    el.classList.remove('border-primary-600', 'text-primary-600');
    el.classList.add('border-transparent', 'text-neutral-600');
  });

  getElement(tabName).classList.remove('hidden');

  const activeButton = tabButton || Array.from(document.querySelectorAll('.tab-btn'))
    .find(button => button.dataset.tab === tabName);
  if (activeButton) {
    activeButton.classList.remove('border-transparent', 'text-neutral-600');
    activeButton.classList.add('border-primary-600', 'text-primary-600');
  }
}

export function showLoading(show) {
  getElement('loadingModal').classList.toggle('hidden', !show);
}

export function showModal(modalId) {
  getElement(modalId).classList.remove('hidden');
}

export function hideModal(modalId) {
  getElement(modalId).classList.add('hidden');
}
