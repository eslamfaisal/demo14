# -*- coding: utf-8 -*-
# Powered by Kanak Infosystems LLP.
# © 2020 Kanak Infosystems LLP. (<https://www.kanakinfosystems.com>).
{
    "name": """POS Show Product Qty""",
    "version": "1.0",
    "summary": """Displays Stock on POS For Every Product | Pos Stock | POS product Stock | POS Inventory | POS Quantity On hand | POS Display Stock | POS qty display""",
    "description": """Displays Stock on POS For Every Product""",
    "category": "Point Of Sale",
    "author": "Kanak Infosystems LLP.",
    "website": "https://www.kanakinfosystems.com",
    "images": [],
    "depends": ["point_of_sale", "stock"],
    "data": [
                "views/views.xml",
                "views/assets.xml"
    ],
    "qweb": ["static/src/xml/pos.xml"],
    "installable": True,
    "application": False,
    "auto_install": False,
    "currency": "EUR",
    "price": '30',
}
