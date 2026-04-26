// Companies management
import { escapeHtml, fetchJson, getElement, hideModal, showModal } from './ui.js';

let companiesData = [];

export async function loadCompaniesList() {
  try {
    const [filesData, tableData] = await Promise.all([
      fetchJson('/api/companies'),
      fetchJson('/api/companies/view')
    ]);

    companiesData = Array.isArray(tableData.companies) ? tableData.companies : [];
    getElement('companiesCount').textContent = tableData.count ?? companiesData.length;

    const files = Array.isArray(filesData.files) ? filesData.files : [];
    getElement('companiesFiles').innerHTML = files.length ? files.map(file => `
      <div class="flex items-center justify-between p-4 rounded-lg border ${file.current ? 'bg-primary-50 border-primary-300' : 'bg-white border-neutral-200'}">
        <div>
          <div class="font-semibold text-neutral-900">${escapeHtml(file.name)}</div>
          <div class="text-sm text-neutral-500">${formatKb(file.size)} KB</div>
        </div>
        ${!file.current ? `<button data-file="${escapeHtml(file.name)}" onclick="window.companies.selectCompaniesFromButton(event)" class="btn btn-primary text-sm">Select</button>` : '<span class="text-primary-600 font-semibold">Active</span>'}
      </div>
    `).join('') : '<div class="text-sm text-neutral-500 text-center py-8">No CSV files found</div>';

    renderCompaniesTable();
  } catch (err) {
    console.error('Error:', err);
  }
}

function renderCompaniesTable() {
  const table = getElement('companiesTable');
  if (!companiesData.length) {
    table.innerHTML = '<tr><td colspan="4" class="table-cell text-center text-neutral-500">No companies</td></tr>';
    getElement('companiesCount').textContent = 0;
    return;
  }

  const keys = Object.keys(companiesData[0]);
  getElement('companiesCount').textContent = companiesData.length;
  table.innerHTML = companiesData.map((company, idx) => `
    <tr class="border-b border-neutral-100 hover:bg-neutral-50" data-row="${idx}">
      ${keys.map(key => `
        <td class="table-cell cursor-pointer hover:bg-primary-50" data-field="${key}" onclick="window.companies.editCell(event)">
          <span class="display">${escapeHtml(company[key])}</span>
          <input type="text" class="edit input hidden w-full" value="${escapeHtml(company[key])}" onblur="window.companies.saveCell(event)" onkeydown="if(event.key==='Enter') window.companies.saveCell(event)">
        </td>
      `).join('')}
      <td class="table-cell text-center"><button onclick="window.companies.deleteCompany(${idx})" class="btn btn-danger text-xs px-2 py-1">Delete</button></td>
    </tr>
  `).join('');
}

export function editCell(event) {
  const td = event.target.closest('td');
  if (!td) return;
  const display = td.querySelector('.display');
  const input = td.querySelector('.edit');
  display.classList.add('hidden');
  input.classList.remove('hidden');
  input.focus();
  input.select();
}

export function saveCell(event) {
  const td = event.target.closest('td');
  if (!td) return;
  const tr = td.closest('tr');
  const rowIdx = parseInt(tr.dataset.row);
  const field = td.dataset.field;
  if (!Number.isInteger(rowIdx) || !field || !companiesData[rowIdx]) return;

  const display = td.querySelector('.display');
  const input = td.querySelector('.edit');
  companiesData[rowIdx][field] = input.value;
  display.textContent = input.value;
  display.classList.remove('hidden');
  input.classList.add('hidden');
}

export function deleteCompany(idx) {
  if (confirm('Delete company?')) {
    companiesData.splice(idx, 1);
    renderCompaniesTable();
  }
}

export async function saveAllCompanies() {
  try {
    const data = await fetchJson('/api/companies/update', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ companies: companiesData })
    });
    alert(`✓ Saved ${data.count} companies`);
  } catch (err) {
    alert('Error: ' + err.message);
  }
}

export function showAddCompanyForm() {
  showModal('addCompanyModal');
}

export function closeAddCompanyForm() {
  hideModal('addCompanyModal');
  getElement('companyName').value = '';
  getElement('companyUrl').value = '';
  getElement('companyCategory').value = '';
}

export async function saveNewCompany() {
  const name = getElement('companyName').value.trim();
  if (!name) { alert('Name required'); return; }

  companiesData.push({
    name,
    url: getElement('companyUrl').value.trim(),
    category: getElement('companyCategory').value.trim()
  });

  await saveAllCompanies();
  closeAddCompanyForm();
  renderCompaniesTable();
}

export async function selectCompanies(fileName) {
  try {
    const data = await fetchJson('/api/companies/select', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ file: fileName })
    });
    alert(`Selected ${fileName} (${data.count} companies)`);
    loadCompaniesList();
  } catch (err) {
    alert('Error: ' + err.message);
  }
}

export function selectCompaniesFromButton(event) {
  const fileName = event.target.closest('[data-file]')?.dataset.file;
  if (!fileName) return;
  selectCompanies(fileName);
}

function formatKb(bytes) {
  const size = Number(bytes);
  return Number.isFinite(size) ? (size / 1024).toFixed(1) : '0.0';
}
