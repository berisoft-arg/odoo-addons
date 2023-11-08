# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductSupplierInfo(models.Model):
     _inherit = 'product.supplierinfo'
     

     list_name = fields.Char('List Name')


