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
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from collections import defaultdict
from odoo.osv import expression

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    installment_ids = fields.One2many('sale.installment.line', 'sale_id', 'Installments')
    down_payment_amt = fields.Float(string="Down Payment", readonly=True, states={'draft': [('readonly', False)]})
    second_payment_date = fields.Date(readonly=True, states={'draft': [('readonly', False)]})
    installment_amt = fields.Float(string="Installment Amount", readonly=True, states={'draft': [('readonly', False)]})
    payable_amt = fields.Float(string="Payable Amount", readonly=True, states={'draft': [('readonly', False)]})
    tenure = fields.Integer(string="Tenure (months)", readonly=True, states={'draft': [('readonly', False)]})
    tenure_amt = fields.Float(compute="_compute_tenure_amt", string="Tenure Amount")

    @api.depends("amount_total")
    def _compute_tenure_amt(self):
        for record in self:
            record.tenure_amt = record.amount_total

    @api.onchange("installment_amt")
    def _onchange_installment_amt_tenure(self):
        if self.installment_amt:
            self.with_context({'installment_amt': self.installment_amt}).tenure = round(self.payable_amt / self.installment_amt)

    @api.onchange("tenure")
    def _onchange_tenure(self):
        if self.tenure:
            self.installment_amt = round(self.payable_amt / self.tenure)

    def onchange(self, values, field_name, field_onchange):
        return super(SaleOrder, self.with_context(recursive_onchanges=False)).onchange(values, field_name, field_onchange)

    @api.onchange("down_payment_amt", "order_line")
    def _onchange_down_payment_amt(self):
        if self.amount_total:
            self.payable_amt = self.amount_total - self.down_payment_amt

    def action_draft(self):
        orders = self.filtered(lambda s: s.state in ['cancel', 'sent'])
        orders.installment_ids.unlink()
        orders.write({'down_payment_amt': 0.0, 'installment_amt': 0.0, 'second_payment_date': False, 'payable_amt': 0.0, 'tenure': 1})
        res = super(SaleOrder, self).action_draft()
        return res

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        for order in self:
            amount_total = order.payable_amt
            tenure = order.tenure
            installment_ids = []
            today_date = fields.Date.today()
            if order.down_payment_amt:
                installment_ids.append((0, 0, {
                    'index': 0,
                    'amount': order.down_payment_amt,
                    'payment_date': today_date,
                    'description': 'Down Payment',
                }))
            if order.installment_amt:
                index = 1
                payment_date = order.second_payment_date or today_date
                amount = order.installment_amt
                while tenure > 0:
                    if amount_total < 0.0:
                        raise UserError(_("Installment Amount Or Number Of Installment Mismatch Error."))
                    if tenure == 1:
                        amount = amount_total
                    installment_ids.append((0, 0, {
                        'index': index,
                        'amount': amount,
                        'payment_date': payment_date,
                        'description': '%s installment' % index,
                    }))
                    index += 1
                    tenure -= 1
                    payment_date += relativedelta(months=1)
                    amount_total -= order.installment_amt
            if installment_ids:
                order.installment_ids = installment_ids
        return res

    def write(self, vals):
        res = super(SaleOrder, self).write(vals)
        if vals.get('installment_ids'):
            for record in self:
                total = sum(record.installment_ids.mapped('amount'))
                if total > record.amount_total:
                    raise UserError(_("Installment Amount Or Number Of Installment Mismatch Error."))
        return res

    def _prepare_invoice(self):
        res = super(SaleOrder, self)._prepare_invoice()
        installment_ids = []
        vals = {}
        for order in self:
            vals.update({
                'tenure': order.tenure,
                'installment_amt': order.installment_amt,
                'down_payment_amt': order.down_payment_amt,
                'payable_amt': order.payable_amt
            })
            for line in order.installment_ids:
                installment_ids.append((0, 0, {
                    'index': line.index,
                    'amount': line.amount,
                    'payment_date': line.payment_date,
                    'description': line.description,
                    'sinst_line_id': line.id,
                }))
        vals.update({'installment_ids': installment_ids})
        res.update(vals)
        return res

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    installments = fields.Integer(string="#Installments")

class AccountMove(models.Model):
    _inherit = "account.move"

    installment_ids = fields.One2many('invoice.installment.line', 'invoice_id', 'Installments')
    tenure = fields.Integer(string="Tenure (months)", states={'draft': [('readonly', False)]})
    installment_amt = fields.Float(string="Installment Amount", states={'draft': [('readonly', False)]})
    compute_installment = fields.Char(string="Compute")
    sale_installment = fields.Boolean(string="Sale Installment")
    part_payment = fields.Char(string="Part Payment")
    down_payment_amt = fields.Float(string="Down Payment", readonly=True, states={'draft': [('readonly', False)]})
    second_payment_date = fields.Date(readonly=True, states={'draft': [('readonly', False)]})
    payable_amt = fields.Float(string="Payable Amount", readonly=True, states={'draft': [('readonly', False)]})
    tenure_amt = fields.Float(compute="_compute_tenure_amt", string="Tenure Amount")

    @api.onchange("installment_amt")
    def _onchange_installment_amt_tenure(self):
        if self.installment_amt:
            self.tenure = round(self.amount_residual / self.installment_amt)

    @api.onchange("tenure")
    def _onchange_tenure(self):
        if self.tenure:
            self.installment_amt = round(self.amount_residual / self.tenure)

    def onchange(self, values, field_name, field_onchange):
        return super(AccountMove, self.with_context(recursive_onchanges=False)).onchange(values, field_name, field_onchange)

    @api.depends("amount_total")
    def _compute_tenure_amt(self):
        for record in self:
            record.tenure_amt = record.amount_total

    def compute_installment(self):
        for order in self:
            amount_total = order.amount_residual
            tenure = order.tenure
            installment_ids = []
            if order.installment_amt:
                index = 1
                if order.amount_residual:
                    payment_date = order.invoice_date
                    if order.installment_ids:
                        payment_date = order.installment_ids.filtered(lambda x: x.state == 'draft')[0].payment_date
                        order.installment_ids.filtered(lambda x: x.state == 'draft').unlink()
                    sol = self.env['sale.order.line'].search([('id', 'in', order.invoice_line_ids.mapped('sale_line_ids').ids)]).order_id
                    sol.installment_ids.filtered(lambda x: x.state == 'draft').unlink()
                    amount = order.installment_amt
                    while tenure > 0:
                        if amount_total < 0.0:
                            raise UserError(_("Installment Amount Or Number Of Installment Mismatch Error."))
                        if tenure == 1:
                            amount = amount_total
                        sinst_line_id = self.env['sale.installment.line'].create({
                            'index': index,
                            'amount': amount,
                            'payment_date': payment_date,
                            'description': '%s installment' % index,
                            'sale_id': sol and sol.id or False
                        })
                        installment_ids.append((0, 0, {
                            'index': index,
                            'amount': amount,
                            'payment_date': payment_date,
                            'description': '%s installment' % index,
                            'sinst_line_id': sinst_line_id and sinst_line_id.id or False,
                        }))
                        index += 1
                        tenure -= 1
                        payment_date += relativedelta(months=1)
                        amount_total -= order.installment_amt
                if installment_ids:
                    order.installment_ids = installment_ids


class account_payment(models.Model):
    _inherit = "account.payment"

    @api.model
    def default_get(self, fields):
        rec = super(account_payment, self).default_get(fields)
        ctx = self.env.context
        if ctx.get('default_amount'):
            rec.update({'amount': ctx['default_amount']})
        return rec

    @api.model
    def _compute_payment_amount(self, invoices, currency, journal, date):
        total = super(account_payment, self)._compute_payment_amount(invoices, currency, journal, date)
        ctx = self.env.context
        if ctx.get('default_amount'):
            return ctx['default_amount']
        return total

    def action_post(self):
        res = super(account_payment, self).action_post()
        ctx = self.env.context
        if ctx.get('line_model', False) and ctx.get('line_id', False):
            line = self.env[ctx['line_model']].browse(ctx['line_id'])
            line.state = 'paid'
            line.sinst_line_id.state = 'paid'
            line_installment = self.env['account.move'].browse(self.env.context['active_id']).installment_ids.filtered(lambda x: x.index != 0)
            for line in line_installment:
                line.update({'index': line.index})
        return res

class SaleInstallmentLine(models.Model):
    _name = 'sale.installment.line'
    _description = 'Sale Installment Line'
    _order = 'payment_date'
    _rec_name = 'description'

    amount = fields.Float()
    index = fields.Integer(string="#No")
    sale_id = fields.Many2one('sale.order', 'Sale Order', ondelete="cascade")
    payment_date = fields.Date()
    description = fields.Char()
    state = fields.Selection([('draft', 'Draft'), ('paid', 'Paid')], default='draft', string="Status")

class InvoiceInstallmentLine(models.Model):
    _name = 'invoice.installment.line'
    _description = 'Invoice Installment Line'
    _order = 'payment_date'
    _rec_name = 'description'

    amount = fields.Float()
    index = fields.Integer(string="#No")
    invoice_id = fields.Many2one('account.move', 'Invoice', ondelete="cascade")
    sale_id = fields.Many2one('sale.order', 'Sale Order', ondelete="cascade")
    payment_date = fields.Date()
    description = fields.Char()
    paid = fields.Boolean()
    sinst_line_id = fields.Many2one('sale.installment.line', 'Sale Installment Line')
    state = fields.Selection([('draft', 'Draft'), ('paid', 'Paid')], default='draft', string="Status")

    def make_payment(self):
        res = self.env['account.move'].action_register_payment()
        res['context'].update({'active_ids': self.invoice_id.ids,
                                'active_id': self.invoice_id.id,
                               'default_amount': self.amount,
                               'line_id': self.id,
                               'line_model': 'invoice.installment.line', 'dont_redirect_to_payments': True})
        return res

    @api.model
    def installment_reminder(self):
        tommorow = fields.Datetime.today() + relativedelta(days=1)
        day_after_tommorow = fields.Datetime.today() + relativedelta(days=2)
        records = self.search([('invoice_id.state', '=', 'posted'), '|', ('payment_date', '=', tommorow), ('payment_date', '=', day_after_tommorow)])
        for rec in records:
            template = self.env.ref('payment_installment_kanak.mail_template_installment_reminder')
            template.send_mail(rec.id, force_send=False)


# class ReportAccountAgedReceivable(models.Model):
#     _inherit = "account.aged.receivable"

#     def _get_values(self, options, line_id):
#         """Fetch the result from the database.

#         :param options (dict): report options.
#         :param line_id (str): optional id of the unfolded line.
#         :return (list<dict>): the fetched results
#         """
#         def hierarchydict():
#             return defaultdict(lambda: {'values': {}, 'children': hierarchydict()})
#         root = hierarchydict()['root']
#         groupby = self._get_hierarchy_details(options)
#         unprocessed = 0
#         for i in range(len(groupby)):
#             current_groupby = [gb.field for gb in groupby[:i+1]]
#             domain = self._get_options_domain(options)
#             if i > 0 and groupby[i-1].foldable:
#                 # Only fetch unfolded lines (+ the newly unfoled line_id)
#                 if options.get('unfold_all'):
#                     pass
#                 elif options.get('unfolded_lines') or line_id:
#                     unfolded_domain = []
#                     for unfolded_line in options['unfolded_lines'] + [line_id]:
#                         parsed = self._parse_line_id(unfolded_line)
#                         if len(current_groupby) == len(parsed) + 1:
#                             unfolded_domain = expression.OR([
#                                 unfolded_domain,
#                                 [(key, '=', value) for key, value in parsed]
#                             ])
#                     domain = expression.AND([domain, unfolded_domain])
#                 else:
#                     break
#             if not groupby[i].foldable and i != len(groupby)-1:
#                 # Do not query higher level group by as we will have to fetch later anyway
#                 continue
#             offset = int(options.get('lines_offset', 0))
#             limit = self.MAX_LINES if current_groupby and groupby[i-1].lazy else None
#             if 'id' in current_groupby:
#                 read = self.search_read(domain, self._fields.keys(), offset=offset, limit=limit)
#             else:
#                 read = self.read_group(
#                     domain=domain,
#                     fields=self._fields.keys(),
#                     groupby=current_groupby,
#                     offset=offset,
#                     limit=limit,
#                     orderby=self._order,
#                     lazy=False,
#                 )
#             j = -1
#             for r in read:
#                 if 'move_name' in r:
#                     user_company = self.env.company
#                     user_currency = user_company.currency_id
#                     line = self.env['account.move.line'].search([('name', '=', r['move_name'])], limit=1)
#                     today = fields.Date.today()
#                     if line.move_id.sale_installment:
#                         period0 = line.move_id.currency_id._convert(r['period0'], user_currency, user_company, today)
#                         period1 = line.move_id.currency_id._convert(r['period1'], user_currency, user_company, today)
#                         period2 = line.move_id.currency_id._convert(r['period2'], user_currency, user_company, today)
#                         period3 = line.move_id.currency_id._convert(r['period3'], user_currency, user_company, today)
#                         period4 = line.move_id.currency_id._convert(r['period4'], user_currency, user_company, today)
#                         period5 = line.move_id.currency_id._convert(r['period5'], user_currency, user_company, today)
#                         r.update({'period0': period0, 'period1': period1, 'period2': period2, 'period3': period3, 'period4': period4, 'period5': period5})
#                 hierarchy = root
#                 if not unprocessed:
#                     self._aggregate_values(root['values'], r)
#                 for j, gb in enumerate(current_groupby):
#                     key = (gb, isinstance(r[gb], tuple) and r[gb][0] or r[gb])
#                     hierarchy = hierarchy['children'][key]
#                     if j >= unprocessed:
#                         self._aggregate_values(hierarchy['values'], r)
#             unprocessed = j+1
#         return root
