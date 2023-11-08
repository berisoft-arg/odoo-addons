# -*- coding: utf-8 -*-
{
    'name': "Product Supplierinfo List Name",

    'summary': """
        Agrega nombre o numero de Lista de Precio en Tarifa Proveedor""",

    'description': """
        Este modulo agrega una columna para indicar el nombre o numero de Lista de Precio en 
        Tarifa Proveedor.
    """,

    'author': "Sergio Ariel Ameghino",
    'website': "ariel.ameghino@gmail.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Purchase',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['product'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/product_supplierinfo_view.xml',
    ],
    # only loaded in demonstration mode
    
}
