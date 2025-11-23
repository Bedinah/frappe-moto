import frappe
from frappe.model.document import Document

class Payment(Document):
    def on_submit(self):
        # link to installment and update status
        if self.contract:
            contract = frappe.get_doc("Contract", self.contract)
            # try to find the earliest pending installment with same amount or next overdue
            target = None
            for idx, row in enumerate(contract.installments):
                if row.status in ["Pending", "Overdue"] and not row.payment:
                    target = (idx, row)
                    break
            if target:
                idx, row = target
                row.payment = self.name
                row.status = "Paid"
                # optional: if partial, adjust amounts; for now, mark paid
                contract.save()

            # recompute remaining
            contract.validate()
            contract.save()

            # notify admin
            frappe.enqueue(method="cycle_track.events.notify_admin_payment",
                           queue="short", timeout=300,
                           kwargs={"contract": self.contract, "payment": self.name})
