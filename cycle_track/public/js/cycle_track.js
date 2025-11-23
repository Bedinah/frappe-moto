// Minimal front-end JS for CycleTrack website pages
// Placeholders call your app back-end. Replace endpoint URLs with your API methods.

document.addEventListener('DOMContentLoaded', () => {
  const page = document.body.dataset_page || null;
  if (!page) return;

  if (page === 'customer_profile') customerProfileInit();
  if (page === 'admin_dashboard') adminDashboardInit();
  if (page === 'contract') contractsInit();
  if (page === 'installments') installmentsInit();
  if (page === 'payments') paymentsInit();
  if (page === 'pay') payPageInit();
});

/* ---------- Utilities ---------- */
async function apiGet(path){
  // Example: path = '/api/method/cycle_track.api.get_customer_dashboard'
  try{
    const res = await fetch(path, {credentials:'same-origin'});
    return await res.json();
  }catch(e){
    console.error('API GET failed', e);
    return null;
  }
}

/* ---------- Customer Profile ---------- */
function customerProfileInit(){
  // show placeholder until backend wired
  const nextDueEl = document.getElementById('next-due');
  const remainingEl = document.getElementById('remaining-balance');
  const historyEl = document.getElementById('payment-history');

  // Demo data; replace with API:
  const demo = {
    next_payment: '2025-12-05',
    remaining_balance: 'UGX 1,200,000',
    payments: [
      {date:'2025-02-05', amount:'UGX 100,000'},
      {date:'2025-03-05', amount:'UGX 100,000'}
    ]
  };

  nextDueEl.textContent = demo.next_payment;
  remainingEl.textContent = demo.remaining_balance;
  historyEl.innerHTML = demo.payments.map(p => `<div class="list-item"><div>${p.date}</div><div class="mono">${p.amount}</div></div>`).join('');
}

/* ---------- Admin Dashboard ---------- */
function adminDashboardInit(){
  // Populate KPIs with demo values
  document.getElementById('kpi-total-motos').textContent = '24';
  document.getElementById('kpi-active-contracts').textContent = '12';
  document.getElementById('kpi-received-month').textContent = 'UGX 1,800,000';
  document.getElementById('kpi-outstanding').textContent = 'UGX 3,400,000';

  // Chart example using Chart.js (CDN loaded in the template)
  if (window.Chart){
    const ctx = document.getElementById('payments-chart').getContext('2d');
    new Chart(ctx, {
      type:'line',
      data:{
        labels:['May','Jun','Jul','Aug','Sep','Oct'],
        datasets:[{
          label:'Payments Received',
          data:[300000,200000,250000,350000,300000,400000],
          borderColor:'#0D47A1',
          backgroundColor:'rgba(13,71,161,0.06)',
          tension:0.3
        }]
      },
      options:{responsive:true,plugins:{legend:{display:false}}}
    });
  }
}

/* ---------- Contracts / Installments / Payments ---------- */
function contractsInit(){
  const list = document.getElementById('contracts-list');
  // Demo contracts
  const demo = [
    {customer:'John Doe', model:'Yamaha YBR 125', price:'UGX 2,400,000', status:'Active contract'},
    {customer:'Jane K', model:'Bajaj Boxer', price:'UGX 1,800,000', status:'Available'}
  ];
  list.innerHTML = demo.map(c => `<div class="list-item"><div><strong>${c.customer}</strong><div class="small">${c.model}</div></div><div class="right"><div class="small mono">${c.price}</div><div class="badge ${c.status==='Available'?'badge-available':'badge-sold'}">${c.status}</div></div></div>`).join('');
}

function installmentsInit(){
  const list = document.getElementById('installments-list');
  const demo = [
    {due:'2025-11-05', amount:'UGX 100,000', status:'upcoming'},
    {due:'2025-10-05', amount:'UGX 100,000', status:'paid'}
  ];
  list.innerHTML = demo.map(i => `<div class="list-item"><div>${i.due}</div><div class="mono">${i.amount}</div><div class="small ${i.status==='paid'?'accent':''}">${i.status}</div></div>`).join('');
}

function paymentsInit(){
  const list = document.getElementById('payments-list');
  const demo = [
    {date:'2025-09-05', amount:'UGX 100,000', method:'Cash'},
    {date:'2025-08-05', amount:'UGX 100,000', method:'Mobile Money'}
  ];
  list.innerHTML = demo.map(p => `<div class="list-item"><div>${p.date} <div class="small">${p.method}</div></div><div class="mono">${p.amount}</div></div>`).join('');
}

/* ---------- Pay Page ---------- */
function payPageInit(){
  const form = document.getElementById('pay-form');
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const amount = document.getElementById('pay-amount').value;
    // TODO: call your backend endpoint to create Payment document
    alert('Simulated payment: ' + amount);
    // Example:
    // const res = await fetch('/api/method/cycle_track.api.pay_installment', {method:'POST', body: JSON.stringify({amount}), headers:{'Content-Type':'application/json'}});
    // const result = await res.json();
  });
}