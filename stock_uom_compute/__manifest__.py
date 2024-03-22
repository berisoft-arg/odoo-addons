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
    'category': 'Inventory',
    'version': '0.1',

    'depends': ['base', 'stock'],

    'data': [
        # 'security/ir.model.access.csv',
        'views/stock_valuation_layer.xml',
            ],

    'installable': True,
    
   }
