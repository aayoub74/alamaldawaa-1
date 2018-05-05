from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # reason for sale_contract module is this function override the function because it gives an error
    def _compute_subscription(self):
        for order in self:
            if order.project_id:
                order.subscription_id = self.env['sale.subscription'].sudo().search(
                    [('analytic_account_id', '=', order.project_id.id)], limit=1)


class SaleSubscriptionTemplate(models.Model):
    _inherit = "sale.subscription.template"

    def _compute_subscription_count(self):
        subscription_data = self.env['sale.subscription'].sudo().read_group(
            domain=[('template_id', 'in', self.ids), ('state', 'in', ['open', 'pending'])],
            fields=['template_id'],
            groupby=['template_id'])
        mapped_data = dict([(m['template_id'][0], m['template_id_count']) for m in subscription_data])
        for template in self:
            template.subscription_count = mapped_data.get(template.id, 0)
