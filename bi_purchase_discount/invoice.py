from odoo import models, fields, api
from odoo.tools.translate import _

class AccountInvoice(models.Model):

    _inherit = 'account.invoice'

    def _prepare_invoice_line_from_po_line(self, line):
    	res = super(AccountInvoice, self)._prepare_invoice_line_from_po_line(line)
    	res['discount'] = line.discount
    	return res