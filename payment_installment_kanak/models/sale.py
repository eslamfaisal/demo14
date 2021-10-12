# -*- coding: utf-8 -*-
#################################################################################
# Author      : Kanak Infosystems LLP. (<http://kanakinfosystems.com/>)
# Copyright(c): 2012-Present Kanak Infosystems LLP.
# All Rights Reserved.
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <http://kanakinfosystems.com/license>
#################################################################################
from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        if self.installment_ids:
            if not self.payment_term_id:
                count = 30
                index = 0
                inst_line_data = []
                payment_term = self.env['account.payment.term'].create({
                        'name': 'Payment Installment %s' % (self.partner_id.name),
                        'sale_order_id': self.id
                    })
                installment_line = self.installment_ids.filtered(lambda x: x.index != 0)
                for inst_line in installment_line[0:-1]:
                    line_vals = (0, 0, {
                        'value': 'fixed',
                        'value_amount': self.installment_amt,
                        'days': count,
                        'option': 'day_after_invoice_date',
                        'day_of_the_month': 0,
                        'sequence': index
                    })
                    inst_line_data.append(line_vals)
                    count += 30
                    index += 1
                payment_term.line_ids.update({'sequence': len(installment_line) + 1, 'value_amount': installment_line[-1:].amount, 'days': count+30})
                payment_term.line_ids = inst_line_data
                self.payment_term_id = payment_term and payment_term.id or False
        return res


class AccountPaymentTerm(models.Model):
    _inherit = "account.payment.term"

    sale_order_id = fields.Many2one('sale.order', string="Sale Order")
