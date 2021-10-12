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
{
    'name': 'Payment Installments',
    'version': '2.1',
    'category': 'Accounting/Accounting',
    'summary': 'This module is used to make payments in installment wise in sales, user can set Tenure months, Tenure amount and can Compute and Part Payment in Installment and Print sale order and Invoice Reports.',
    'description': """
This module provides to make payments in installments
=====================================================


    """,
    'license': 'OPL-1',
    'author': 'Kanak Infosystems LLP.',
    'website': 'http://www.kanakinfosystems.com',
    'depends': ['sale_management', 'account'],
    'data': [
        'data/data.xml',
        'security/ir.model.access.csv',
        'security/security.xml',
        'wizard/create_part_payment.xml',
        'views/payment_installment_view.xml',
        'views/res_config_settings_views.xml',
        'views/report_installment.xml',
        'views/report_invoice_installment.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'installable': True,
    'application': False,
    'auto_install': False,
    'price': 70,
    'currency': 'USD',

}
