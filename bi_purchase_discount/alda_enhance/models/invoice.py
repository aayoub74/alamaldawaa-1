# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _
from logging import getLogger

_logger = getLogger(__name__)

class AccountInvoice(models.Model):

    _inherit = 'account.invoice'

    def _prepare_invoice_line_from_po_line(self, line):
    	res = super(AccountInvoice, self)._prepare_invoice_line_from_po_line(line)
    	res['bonus'] = line.bonus
    	return res


class InvoiceLine(models.Model):
	_inherit = 'account.invoice.line'

	bonus = fields.Float(
	    string='Bonus',
	    default=0.0,
	    digits=(16, 2),
	)


