# -*- coding: utf-8 -*-
{
    'name': "Stock UoM Compute",

    'summary': """
        Este módulo agrega la función de computar el volumen y/o el peso total por producto,
        en la Valoración del Inventario.""",

    'description': """
        Determina el stock de cada producto en cualquier medida de volumen y peso. Utilice el módulo 'product_logistics_uom'
    de la OCA, para establecer dicha medida. Configurado el volumen y/o peso en cada producto, computa la cantidad de existencias,
    por el volumen y/o peso preestablecido.
    """,

    'author': "Sergio Ariel Ameghino",
    'website': "ariel.ameghino@gmail.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Inventory',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'stock'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/stock_valuation_layer.xml',
            ],
   }
