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
    'website': "https://github.com/SergioAmeghino/odoo-addons.git",    
    'category': 'Purchase',
    'version': '17.0.1.0.0',
    'depends': ['product'],
    
    'data': [
        # 'security/ir.model.access.csv',
        'views/product_supplierinfo_view.xml',
    ],

    'installable': True,
        
}
