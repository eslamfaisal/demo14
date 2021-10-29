# -*- coding: utf-8 -*-
# Powered by Kanak Infosystems LLP.
# © 2020 Kanak Infosystems LLP. (<https://www.kanakinfosystems.com>).
from odoo import fields, models


class PosConfig(models.Model):
    _inherit = "pos.config"

    show_product_quantity = fields.Boolean(
        "Show Product Qtys", default=True, help="Show Product Quantities in POS")
    default_location_src_id = fields.Many2one(
        "stock.location", related="picking_type_id.default_location_src_id"
    )
