from odoo import models, fields, api, exceptions
from odoo.tools.translate import _


class ScrapWizard(models.TransientModel):
    _name = 'scrap.wizard'
    _rec_name = 'location_id'
    lot_id = fields.Many2one(comodel_name="stock.production.lot", string="Lot", required=False, )
    location_id = fields.Many2one(comodel_name="stock.location", string="Distination Location", required=True, )

    @api.multi
    def scrap_lot(self):
        scrap_obj = self.env['stock.scrap']
        for record in self.lot_id.quant_ids:
            scrap_obj.create({
                'product_id': self.lot_id.product_id.id,
                'product_uom_id': self.lot_id.product_id.uom_id.id,
                'scrap_qty': record.qty,
                'location_id': record.location_id.id,
                'scrap_location_id': self.location_id.id,
                'lot_id': self.lot_id.id,

            })
