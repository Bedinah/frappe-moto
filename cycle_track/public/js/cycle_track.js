// CycleTrack Frontend - Wired to Real API Endpoints
// All calls are whitelisted and authenticated via Frappe session

const API_BASE = '/api/method/cycle_track.api';

/* ========== Utilities ========== */

async function apiCall(method, params = {}) {
  try {
    const url = new URL(`${API_BASE}.${method}`, window.location.origin);
    Object.keys(params).forEach(key => url.searchParams.append(key, params[key]));
    
    const response = await fetch(url.toString(), {
      method: 'GET',
      credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json' }
    });
    
    const data = await response.json();
    return data;
  } catch (e) {
    console.error(`API call failed: ${method}`, e);
    return { success: false, error: e.message };
  }
}

async function apiPost(method, params = {}) {
  try {
    const response = await fetch(`${API_BASE}.${method}`, {
      method: 'POST',
      credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params)
    });
    
    const data = await response.json();
    return data;
  } catch (e) {
    console.error(`API POST failed: ${method}`, e);
    return { success: false, error: e.message };
  }
}

function showAlert(message, type = 'info') {
  const alertId = `alert-${Date.now()}`;
  const alert = document.createElement('div');
  alert.id = alertId;
  alert.className = `alert alert-${type}`;
  alert.innerHTML = `
    <div style="display: flex; gap: 12px; align-items: center;">
      <span>${message}</span>
      <button onclick="document.getElementById('${alertId}').remove()" style="background: none; border: none; color: inherit; cursor: pointer; font-size: 18px;">×</button>
    </div>
  `;
  document.body.insertBefore(alert, document.body.firstChild);
  setTimeout(() => alert.remove(), 4000);
}

/* ========== Page Initializers ========== */

document.addEventListener('DOMContentLoaded', () => {
  const page = document.body.dataset.page || null;
  if (!page) return;

  if (page === 'customer_profile') customerProfileInit();
  if (page === 'admin_dashboard') adminDashboardInit();
  if (page === 'contract') contractsInit();
  if (page === 'installments') installmentsInit();
  if (page === 'payments') paymentsInit();
  if (page === 'pay') payPageInit();
  if (page === 'admin_contracts') adminContractsInit();
  if (page === 'admin_customers') adminCustomersInit();
});

/* ========== CUSTOMER PROFILE PAGE ========== */

async function customerProfileInit() {
  const nextDueEl = document.getElementById('next-due');
  const remainingEl = document.getElementById('remaining-balance');
  const historyEl = document.getElementById('payment-history');
  const loadingEl = document.getElementById('loading') || createLoadingSpinner();

  try {
    const result = await apiCall('get_customer_profile');
    
    if (!result.success || !result.data) {
      showAlert('Failed to load customer profile', 'danger');
      return;
    }

    const { active_contract, contracts } = result.data;

    if (active_contract) {
      nextDueEl.textContent = active_contract.next_due 
        ? `${active_contract.next_due.date} - ₦${active_contract.next_due.amount}`
        : 'No upcoming payments';
      remainingEl.textContent = `₦${active_contract.remaining_balance.toLocaleString()}`;
    } else {
      nextDueEl.textContent = 'No active contract';
      remainingEl.textContent = '₦0';
    }

    // Load payment history
    const paymentResult = await apiCall('list_payments');
    if (paymentResult.success && paymentResult.data.length > 0) {
      historyEl.innerHTML = paymentResult.data.map(p => `
        <div class="list-item">
          <div>${p.payment_date}</div>
          <div class="mono">₦${flt(p.amount).toLocaleString()}</div>
          <div class="small">${p.mode}</div>
        </div>
      `).join('');
    } else {
      historyEl.innerHTML = '<div class="empty">No payment history</div>';
    }
  } catch (e) {
    showAlert('Error loading profile', 'danger');
    console.error(e);
  }
}

/* ========== ADMIN DASHBOARD PAGE ========== */

async function adminDashboardInit() {
  const kpiContainer = document.getElementById('kpi-container');
  const recentPaymentsEl = document.getElementById('recent-payments');

  try {
    // Get KPIs
    const kpiResult = await apiCall('get_admin_dashboard');
    
    if (!kpiResult.success) {
      showAlert('Failed to load dashboard', 'danger');
      return;
    }

    const kpis = kpiResult.data;

    // Update KPI cards
    document.getElementById('kpi-total-motos').textContent = kpis.total_motorcycles;
    document.getElementById('kpi-active-contracts').textContent = kpis.active_contracts;
    document.getElementById('kpi-received-month').textContent = `₦${kpis.money_this_month.toLocaleString()}`;
    document.getElementById('kpi-outstanding').textContent = `₦${kpis.outstanding.toLocaleString()}`;
    document.getElementById('kpi-late-customers').textContent = kpis.late_customers;
    document.getElementById('kpi-available').textContent = kpis.available_motorcycles;

    // Get recent payments
    const paymentsResult = await apiCall('get_admin_payments', { limit: 10 });
    
    if (paymentsResult.success && paymentsResult.data.length > 0) {
      recentPaymentsEl.innerHTML = paymentsResult.data.map(p => `
        <tr>
          <td>${p.payment_date}</td>
          <td><strong>${p.contract}</strong></td>
          <td>₦${flt(p.amount).toLocaleString()}</td>
          <td><span class="badge badge-info">${p.mode}</span></td>
        </tr>
      `).join('');
    }
  } catch (e) {
    showAlert('Error loading dashboard', 'danger');
    console.error(e);
  }
}

/* ========== CONTRACTS PAGE ========== */

async function contractsInit() {
  const list = document.getElementById('contracts-list');
  const loadingEl = createLoadingSpinner();
  list.appendChild(loadingEl);

  try {
    const result = await apiCall('list_contracts', { limit: 50 });
    
    list.innerHTML = '';
    
    if (!result.success || result.data.length === 0) {
      list.innerHTML = '<div class="empty">No contracts found</div>';
      return;
    }

    list.innerHTML = result.data.map(c => `
      <div class="list-item">
        <div>
          <strong>${c.customer_name}</strong>
          <div class="small">${c.motorcycle_name}</div>
        </div>
        <div class="right">
          <div class="small mono">₦${flt(c.remaining_balance).toLocaleString()}</div>
          <div class="badge ${c.status === 'Active' ? 'badge-available' : 'badge-sold'}">${c.status}</div>
        </div>
      </div>
    `).join('');
  } catch (e) {
    list.innerHTML = `<div class="empty">Error loading contracts: ${e.message}</div>`;
    console.error(e);
  }
}

/* ========== INSTALLMENTS PAGE ========== */

async function installmentsInit() {
  const list = document.getElementById('installments-list');
  const loadingEl = createLoadingSpinner();
  list.appendChild(loadingEl);

  try {
    const result = await apiCall('list_installments');
    
    list.innerHTML = '';
    
    if (!result.success || result.data.length === 0) {
      list.innerHTML = '<div class="empty">No installments found</div>';
      return;
    }

    list.innerHTML = result.data.map(i => `
      <div class="list-item">
        <div>
          <strong>${i.contract}</strong>
          <div class="small">Due: ${i.due_date}</div>
        </div>
        <div class="right">
          <div class="mono">₦${flt(i.amount).toLocaleString()}</div>
          <div class="small ${i.status === 'Paid' ? 'accent' : ''}">${i.status}</div>
        </div>
      </div>
    `).join('');
  } catch (e) {
    list.innerHTML = `<div class="empty">Error loading installments: ${e.message}</div>`;
  }
}

/* ========== PAYMENTS PAGE ========== */

async function paymentsInit() {
  const list = document.getElementById('payments-list');
  const loadingEl = createLoadingSpinner();
  list.appendChild(loadingEl);

  try {
    const result = await apiCall('list_payments');
    
    list.innerHTML = '';
    
    if (!result.success || result.data.length === 0) {
      list.innerHTML = '<div class="empty">No payment history</div>';
      return;
    }

    list.innerHTML = result.data.map(p => `
      <div class="list-item">
        <div>
          <strong>${p.payment_date}</strong>
          <div class="small">${p.mode}</div>
        </div>
        <div class="mono accent">₦${flt(p.amount).toLocaleString()}</div>
      </div>
    `).join('');
  } catch (e) {
    list.innerHTML = `<div class="empty">Error loading payments: ${e.message}</div>`;
  }
}

/* ========== PAY PAGE ========== */

async function payPageInit() {
  const form = document.getElementById('pay-form');
  
  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const contract = document.getElementById('pay-contract')?.value;
    const amount = document.getElementById('pay-amount').value;
    const paymentDate = document.getElementById('pay-date').value || new Date().toISOString().split('T')[0];
    const mode = document.getElementById('pay-mode').value || 'Cash';
    const reference = document.getElementById('pay-reference')?.value;

    if (!contract || !amount) {
      showAlert('Please fill in all required fields', 'warning');
      return;
    }

    const btn = form.querySelector('button[type="submit"]');
    btn.disabled = true;
    btn.textContent = 'Processing...';

    try {
      const result = await apiPost('pay_installment', {
        contract,
        amount,
        payment_date: paymentDate,
        mode,
        reference
      });

      if (result.success) {
        showAlert('Payment recorded successfully!', 'success');
        form.reset();
        setTimeout(() => window.location.href = '/payments', 2000);
      } else {
        showAlert(result.error || 'Payment failed', 'danger');
      }
    } finally {
      btn.disabled = false;
      btn.textContent = 'Pay';
    }
  });
}

/* ========== ADMIN CONTRACTS PAGE ========== */

async function adminContractsInit() {
  const list = document.getElementById('contracts-list');
  const createBtn = document.getElementById('create-contract-btn');

  if (createBtn) {
    createBtn.addEventListener('click', () => {
      showCreateContractModal();
    });
  }

  loadContractsList();
}

async function loadContractsList() {
  const list = document.getElementById('contracts-list');
  const loadingEl = createLoadingSpinner();
  list.innerHTML = '';
  list.appendChild(loadingEl);

  try {
    const result = await apiCall('list_contracts', { limit: 50 });
    
    list.innerHTML = '';
    
    if (!result.success) {
      list.innerHTML = '<div class="empty">Error loading contracts</div>';
      return;
    }

    if (result.data.length === 0) {
      list.innerHTML = '<div class="empty">No contracts found</div>';
      return;
    }

    list.innerHTML = result.data.map(c => `
      <div class="list-item">
        <div>
          <strong>${c.name}</strong>
          <div class="small">${c.customer_name} - ${c.motorcycle_name}</div>
        </div>
        <div class="right">
          <div class="small mono">₦${flt(c.total_price).toLocaleString()}</div>
          <span class="badge ${c.status === 'Active' ? 'badge-available' : 'badge-sold'}">${c.status}</span>
        </div>
      </div>
    `).join('');
  } catch (e) {
    list.innerHTML = `<div class="empty">Error: ${e.message}</div>`;
  }
}

async function showCreateContractModal() {
  // Get customers and motorcycles
  const customersResult = await apiCall('list_customers', { limit: 100 });
  const motorcyclesResult = await apiCall('get_available_motorcycles');

  if (!customersResult.success || !motorcyclesResult.success) {
    showAlert('Failed to load data', 'danger');
    return;
  }

  const modal = document.createElement('div');
  modal.className = 'modal';
  modal.innerHTML = `
    <div class="modal-content">
      <h3>Create Contract</h3>
      <form id="create-contract-form">
        <label>Customer</label>
        <select id="cc-customer" required>
          <option value="">Select Customer</option>
          ${customersResult.data.map(c => `<option value="${c.name}">${c.full_name}</option>`).join('')}
        </select>

        <label>Motorcycle</label>
        <select id="cc-motorcycle" required>
          <option value="">Select Motorcycle</option>
          ${motorcyclesResult.data.map(m => `<option value="${m.name}">${m.brand} ${m.model} (₦${flt(m.price).toLocaleString()})</option>`).join('')}
        </select>

        <label>Total Price</label>
        <input type="number" id="cc-total-price" step="0.01" required>

        <label>Deposit</label>
        <input type="number" id="cc-deposit" step="0.01" value="0">

        <label>Duration (Months)</label>
        <input type="number" id="cc-duration" min="1" required>

        <label>Monthly Amount</label>
        <input type="number" id="cc-monthly" step="0.01" required>

        <label>Start Date</label>
        <input type="date" id="cc-start-date" required>

        <div style="display: flex; gap: 10px; margin-top: 20px;">
          <button type="submit" class="btn btn-primary">Create</button>
          <button type="button" class="btn btn-ghost" onclick="this.closest('.modal').remove()">Cancel</button>
        </div>
      </form>
    </div>
  `;

  document.body.appendChild(modal);

  document.getElementById('create-contract-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const result = await apiPost('create_contract', {
      customer: document.getElementById('cc-customer').value,
      motorcycle: document.getElementById('cc-motorcycle').value,
      total_price: document.getElementById('cc-total-price').value,
      deposit: document.getElementById('cc-deposit').value,
      duration_months: document.getElementById('cc-duration').value,
      monthly_amount: document.getElementById('cc-monthly').value,
      start_date: document.getElementById('cc-start-date').value
    });

    if (result.success) {
      showAlert('Contract created successfully!', 'success');
      modal.remove();
      loadContractsList();
    } else {
      showAlert(result.error || 'Failed to create contract', 'danger');
    }
  });
}

/* ========== ADMIN CUSTOMERS PAGE ========== */

async function adminCustomersInit() {
  const list = document.getElementById('customers-list');
  const createBtn = document.getElementById('create-customer-btn');

  if (createBtn) {
    createBtn.addEventListener('click', () => {
      showCreateCustomerModal();
    });
  }

  loadCustomersList();
}

async function loadCustomersList() {
  const list = document.getElementById('customers-list');
  const loadingEl = createLoadingSpinner();
  list.innerHTML = '';
  list.appendChild(loadingEl);

  try {
    const result = await apiCall('list_customers', { limit: 100 });
    
    list.innerHTML = '';
    
    if (!result.success) {
      list.innerHTML = '<div class="empty">Error loading customers</div>';
      return;
    }

    if (result.data.length === 0) {
      list.innerHTML = '<div class="empty">No customers found</div>';
      return;
    }

    list.innerHTML = result.data.map(c => `
      <div class="list-item">
        <div>
          <strong>${c.full_name}</strong>
          <div class="small">${c.phone} • ${c.email}</div>
        </div>
        <div class="right">
          <div class="small">${c.contract_count} contract(s)</div>
          <span class="badge ${c.status === 'Active' ? 'badge-available' : 'badge-sold'}">${c.status}</span>
        </div>
      </div>
    `).join('');
  } catch (e) {
    list.innerHTML = `<div class="empty">Error: ${e.message}</div>`;
  }
}

async function showCreateCustomerModal() {
  const modal = document.createElement('div');
  modal.className = 'modal';
  modal.innerHTML = `
    <div class="modal-content">
      <h3>Create Customer</h3>
      <form id="create-customer-form">
        <label>Full Name</label>
        <input type="text" id="cc-full-name" required>

        <label>Phone</label>
        <input type="tel" id="cc-phone" required>

        <label>Email</label>
        <input type="email" id="cc-email">

        <div style="display: flex; gap: 10px; margin-top: 20px;">
          <button type="submit" class="btn btn-primary">Create</button>
          <button type="button" class="btn btn-ghost" onclick="this.closest('.modal').remove()">Cancel</button>
        </div>
      </form>
    </div>
  `;

  document.body.appendChild(modal);

  document.getElementById('create-customer-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const result = await apiPost('create_customer', {
      full_name: document.getElementById('cc-full-name').value,
      phone: document.getElementById('cc-phone').value,
      email: document.getElementById('cc-email').value
    });

    if (result.success) {
      showAlert('Customer created successfully!', 'success');
      modal.remove();
      loadCustomersList();
    } else {
      showAlert(result.error || 'Failed to create customer', 'danger');
    }
  });
}

/* ========== HELPERS ========== */

function createLoadingSpinner() {
  const div = document.createElement('div');
  div.className = 'empty';
  div.innerHTML = '<span>Loading...</span>';
  return div;
}

function flt(val) {
  return parseFloat(val) || 0;
}