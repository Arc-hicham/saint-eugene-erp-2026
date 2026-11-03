# -*- coding: utf-8 -*-
from frappe.model.document import Document
from frappe.utils import add_days, getdate, nowdate
from saint_eugene.utils.invoice_calc import apply_to_frappe_doc

class SEFactureProForma(Document):
    def validate(self):
        if not self.date_facture:
            self.date_facture = nowdate()
        if not self.date_validite:
            self.date_validite = add_days(self.date_facture, 30)
        apply_to_frappe_doc(self)
