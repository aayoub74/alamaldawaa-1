# -*- coding: utf-8 -*-
from ast import literal_eval
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools.translate import _


class HREmployee(models.Model):

    _inherit = 'hr.employee'

    target_val = fields.Float(string="Target Per Month", digits=(16, 2))
    commission = fields.Float(string="Commission(%)", digits=(16, 2))
    total_invoices = fields.Monetary(string="Total Invoices", compute='_get_total_invoices')
    currency_id = fields.Many2one('res.currency', compute='_get_company_currency', readonly=True,
        string="Currency", help='Utility field to express amount currency')

    @api.one
    def _get_company_currency(self):
        if self.company_id:
            self.currency_id = self.sudo().company_id.currency_id
        else:
            self.currency_id = self.env.user.company_id.currency_id

    @api.constrains('commission')
    def check_commission(self):
        for rec in self:
            if rec.commission < 0.00 or rec.commission > 100.0:
                raise ValidationError(_("Wrong value for commission"))

    @api.multi
    def get_employee_sale_journals_ids(self):
        self.ensure_one()
        journal_ids = False
        if self.user_id and self.user_id.journal_ids:
            journal_ids= self.user_id.journal_ids.filtered(lambda j : j.type == 'sale').mapped('id')
        return journal_ids

    @api.model
    def _get_total_invoices_per_month(self,employee):
        journal_ids = employee.get_employee_sale_journals_ids()
        if journal_ids:
            account_invoice_report = self.env['account.invoice.report']
            # generate where clause to include multicompany rules
            where_query = account_invoice_report._where_calc([
                ('journal_id', 'in', journal_ids), ('state', 'not in', ['draft', 'cancel']),
                ('company_id', '=', self.env.user.company_id.id),
                ('type', '=', 'out_invoice')
            ])
            account_invoice_report._apply_ir_rules(where_query, 'read')
            from_clause, where_clause, where_clause_params = where_query.get_sql()

            # price_total is in the company currency
            query = """
                      SELECT SUM(price_total) as total,date
                        FROM account_invoice_report account_invoice_report
                       WHERE %s
                       GROUP BY date
                    """ % where_clause
            self.env.cr.execute(query, where_clause_params)
            price_totals = self.env.cr.dictfetchall()
            return price_totals
        else:
            return False

    @api.one
    def _get_total_invoices(self):
        price_totals = self._get_total_invoices_per_month(self)
        if price_totals:
            self.total_invoices = sum(price['total'] for price in price_totals)
        else:
            self.total_invoices = 0.00

    @api.multi
    def action_get_invoices(self):
        journal_ids = self.get_employee_sale_journals_ids()
        if journal_ids:
            action = self.env.ref('account.action_invoice_tree1').read()[0]
            action['domain'] = literal_eval(action['domain'])
            action['domain']+=[('journal_id', 'in', journal_ids),('state','not in',['draft','cancel'])]
            action['context'] = literal_eval(action['context'])
            action['context']['group_by'] = 'date_invoice'
            return action

