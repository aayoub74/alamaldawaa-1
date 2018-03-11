# -*- coding: utf-8 -*-
from datetime import timedelta, datetime

from odoo import models, fields, api
from dateutil.relativedelta import relativedelta


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.depends('number_of_months', 'date_invoice')
    @api.multi
    def _get_contract_end_date(self):
        self.ensure_one()
        if self and self.date_invoice:
            self.contract_end_date = datetime.strptime(self.date_invoice, '%Y-%m-%d') + relativedelta(
                months=self.number_of_months)

    installment_ids = fields.One2many(comodel_name="account.invoice.installment", inverse_name="invoice_id", string="",
                                      required=False, )
    number_of_installment = fields.Integer(string="", required=False, )
    payment_method_id = fields.Many2one(comodel_name="account.payment.method", string="", required=False, )
    number_of_months = fields.Integer(string="", required=False, )
    contract_end_date = fields.Date(string="", required=False, compute=_get_contract_end_date)
    installment_journal_id = fields.Many2one(comodel_name="account.journal", string="", required=False,
                                 domain=[('type', 'in', ('bank', 'cash'))])
    is_contract = fields.Boolean(string="",  )

    @api.one
    def generate_installments(self):

        number_of_days = (datetime.strptime(self.contract_end_date, '%Y-%m-%d') - datetime.strptime(
            self.date_invoice, '%Y-%m-%d')).days
        number_of_days_to_create_installment = int(number_of_days / self.number_of_installment)
        print('no', number_of_days_to_create_installment)
        amount = self.amount_total / self.number_of_installment
        # TODO
        # create Record After number Of days
        date = datetime.strptime(self.date_invoice, '%Y-%m-%d') + relativedelta(days=number_of_days_to_create_installment)
        for i in range(self.number_of_installment):
            self.installment_ids.create(
                {'amount': amount, 'invoice_id': self.id, 'payment_method_id': self.payment_method_id.id,
                  'payment_type': 'outbound', 'partner_id': self.partner_id.id,
                 'partner_type': 'supplier', 'installment_date': date, 'installment_journal_id': self.installment_journal_id.id})
            date = date + relativedelta(days=number_of_days_to_create_installment)


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    invoice_id = fields.Many2one(comodel_name="account.invoice", string="", )


class NewModule(models.Model):
    _name = 'account.invoice.installment'
    _rec_name = 'installment_date'
    _description = 'installment'

    amount = fields.Float(string="", required=False, )
    invoice_id = fields.Many2one(comodel_name="account.invoice", string="", required=False, )
    payment_method_id = fields.Many2one(comodel_name="account.payment.method", string="", required=False, )
    partner_id = fields.Many2one(comodel_name="res.partner", string="", required=False, )
    payment_id = fields.Many2one(comodel_name="account.payment", string="", required=False, )
    state = fields.Selection(related='payment_id.state', required=False, )
    installment_date = fields.Date(string="", required=False, )
    installment_journal_id = fields.Many2one(comodel_name="account.journal", string="", required=False,
                                 domain=[('type', 'in', ('bank', 'cash'))])

    @api.multi
    def generate_payment(self):
        payment_obj = self.env['account.payment']
        self.payment_id = payment_obj.create(
            {'amount': self.amount, 'invoice_id': self.invoice_id.id, 'payment_method_id': self.payment_method_id.id,
              'payment_type': 'outbound', 'partner_id': self.partner_id.id,
             'partner_type': 'supplier', 'installment_date': self.installment_date, 'journal_id': self.installment_journal_id.id})
