# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools.translate import _
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    @api.model
    def get_employee_commission(self,employee,date_from,date_to):

        def check_date_between(date_check,date_from,date_to):
            date_check = datetime.strptime(date_check,DEFAULT_SERVER_DATE_FORMAT)
            date_from = datetime.strptime(date_from,DEFAULT_SERVER_DATE_FORMAT)
            date_to = datetime.strptime(date_to,DEFAULT_SERVER_DATE_FORMAT)
            if date_from <= date_check <= date_to:
                return True
            else:
                return False

        total_invoice_by_month = employee._get_total_invoices_per_month(employee)
        return sum([price['total'] for price in total_invoice_by_month if check_date_between(price['date'],date_from,date_to)])



    @api.model
    def get_inputs(self, contract_ids, date_from, date_to):
        res = super(HrPayslip, self).get_inputs(contract_ids, date_from, date_to)
        for line in res:
            if line['code'] == 'CIS':
                employee = self.env['hr.contract'].browse(contract_ids[0]).employee_id
                line['amount'] = self.get_employee_commission(employee,date_from,date_to)
        return res

