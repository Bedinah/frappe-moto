frappe.pages["admin-dashboard"].on_page_load = function (wrapper) {
	let page = frappe.ui.make_app_page({
		parent: wrapper,
		title: "Admin Dashboard",
		single_column: true,
	});

	frappe
		.call({
			method: "cycle_track.api.get_admin_kpis",
		})
		.then((r) => {
			const k = r.message || {};
			$(page.body).html(`
      <div class="mf-kpis">
        <div class="kpi"><h3>Total Motorcycles</h3><p>${k.total_motorcycles || 0}</p></div>
        <div class="kpi"><h3>Active Contracts</h3><p>${k.active_contracts || 0}</p></div>
        <div class="kpi"><h3>Money Received This Month</h3><p>${k.money_this_month || 0}</p></div>
        <div class="kpi"><h3>Outstanding Balances</h3><p>${k.outstanding || 0}</p></div>
        <div class="kpi"><h3>Late Customers</h3><p>${k.late_customers || 0}</p></div>
      </div>
    `);
		});
};
