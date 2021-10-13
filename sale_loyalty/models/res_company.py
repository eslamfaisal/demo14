# -*- coding: utf-8 -*-
# Part of Kanak Infosystems LLP. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    loyalty_id = fields.Many2one('sale.loyalty.program', string='Loyalty Program', copy=True)
