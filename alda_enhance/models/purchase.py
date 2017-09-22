from odoo import models, fields, api
from odoo.tools.float_utils import float_is_zero, float_compare


from odoo.tools.translate import _

from logging import getLogger

_logger = getLogger(__name__)

class PurhcaseOrderLine (models.Model):
	_inherit = 'purchase.order.line'

	bonus = fields.Float(string='Bonus',digits=(16, 2))
	total_qty  = fields.Float(
		string='Total Qty',
		digits=(16, 2),
		compute='_compute_total'
		
	)
	total_av_cost = fields.Float(
	    string='Total Average Cost',
	    digits=(16, 2),
	    compute='_compute_total_av_cost',
	    store=True,

	)
	bonus_ratio = fields.Float(
		string='Bonus Ratio',
		digits=(16, 4),
		compute='_compute_total'
		
	)


	@api.depends('bonus','product_qty')
	def _compute_total(self):
		''' Calcualte Total Qty and bouns ratio from Total Qty '''
		for record in self:
			record.total_qty= record.bonus + record.product_qty
			if record.total_qty:
				record.bonus_ratio= record.bonus / record.total_qty

	@api.depends('product_id','product_qty')
	def _compute_total_av_cost(self):
		''' Calcualte Total previous Average Cost'''
		for record in self:
			record.total_av_cost = record.product_qty * record.product_id.standard_price



	@api.multi
	def _get_stock_move_price_unit(self):
		"""making discount and bouns decrease the pirce unit"""
		self.ensure_one()
		price_unit = super(PurhcaseOrderLine, self)._get_stock_move_price_unit()
		line = self[0]
		price_unit -=  price_unit * (line.bonus / line.total_qty)
		if float_compare(line.discount,0.0,2) > 0:
			price_unit -= (price_unit * (line.discount / 100))
		return price_unit

	@api.multi
	def _prepare_stock_moves(self, picking):
		""" Prepare the stock moves data for one order line. This function returns a list of
		dictionary ready to be used in stock.move's create()
		"""
		self.ensure_one()
		res = []
		if self.product_id.type not in ['product', 'consu']:
			return res
		qty = 0.0
		price_unit = self._get_stock_move_price_unit()
		for move in self.move_ids.filtered(lambda x: x.state != 'cancel'):
			qty += move.product_qty
		template = {
			'name': self.name or '',
			'product_id': self.product_id.id,
			'product_uom': self.product_uom.id,
			'date': self.order_id.date_order,
			'date_expected': self.date_planned,
			'location_id': self.order_id.partner_id.property_stock_supplier.id,
			'location_dest_id': self.order_id._get_destination_location(),
			'picking_id': picking.id,
			'partner_id': self.order_id.dest_address_id.id,
			'move_dest_id': False,
			'state': 'draft',
			'purchase_line_id': self.id,
			'company_id': self.order_id.company_id.id,
			'price_unit': price_unit,
			'picking_type_id': self.order_id.picking_type_id.id,
			'group_id': self.order_id.group_id.id,
			'procurement_id': False,
			'origin': self.order_id.name,
			'route_ids': self.order_id.picking_type_id.warehouse_id and [(6, 0, [x.id for x in self.order_id.picking_type_id.warehouse_id.route_ids])] or [],
			'warehouse_id': self.order_id.picking_type_id.warehouse_id.id,
		}
		# Fullfill all related procurements with this po line
		diff_quantity = self.total_qty - qty
		for procurement in self.procurement_ids.filtered(lambda p: p.state != 'cancel'):
			# If the procurement has some moves already, we should deduct their quantity
			sum_existing_moves = sum(x.product_qty for x in procurement.move_ids if x.state != 'cancel')
			existing_proc_qty = procurement.product_id.uom_id._compute_quantity(sum_existing_moves, procurement.product_uom)
			procurement_qty = procurement.product_uom._compute_quantity(procurement.product_qty, self.product_uom) - existing_proc_qty
			if float_compare(procurement_qty, 0.0, precision_rounding=procurement.product_uom.rounding) > 0 and float_compare(diff_quantity, 0.0, precision_rounding=self.product_uom.rounding) > 0:
				tmp = template.copy()
				tmp.update({
					'product_uom_qty': min(procurement_qty, diff_quantity),
					'move_dest_id': procurement.move_dest_id.id,  # move destination is same as procurement destination
					'procurement_id': procurement.id,
					'propagate': procurement.rule_id.propagate,
				})
				res.append(tmp)
				diff_quantity -= min(procurement_qty, diff_quantity)
		if float_compare(diff_quantity, 0.0,  precision_rounding=self.product_uom.rounding) > 0:
			template['product_uom_qty'] = diff_quantity
			res.append(template)
		return res

class PurhcaseOrder(models.Model):

	_inherit = 'purchase.order'

	cfo_emails = fields.Char(
		string='CFO emails',
		compute='_get_cfo_email',
	)

	@api.one
	def _get_cfo_email(self):
		cfo_group = self.env.ref('alda_enhance.alda_cfo',raise_if_not_found=False)
		email_str = ''
		if cfo_group:
			emails = [user.email for user in cfo_group.users]
			email_str = ','.join(emails)
		#print '-----------',email_str
		self.cfo_emails = email_str

	@api.multi
	def button_confirm(self):
		for order in self:
			if order.state not in ['draft', 'sent']:
				continue
			order._add_supplier_to_product()
			# Deal with double validation process
			if order.company_id.po_double_validation == 'one_step'\
					or (order.company_id.po_double_validation == 'two_step'\
						and order.amount_total < self.env.user.company_id.currency_id.compute(order.company_id.po_double_validation_amount, order.currency_id)):
				order.button_approve()
			else:
				order.write({'state': 'to approve'})
		return True