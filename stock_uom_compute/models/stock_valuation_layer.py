# -*- coding: utf-8 -*-

from odoo import models, fields, api


class StockUom(models.Model):
     _inherit = 'stock.valuation.layer'
    
     @api.depends('product_id')
     def compute_stock_volume(self):
        for rec in self:
            rec.total_volume = rec.quantity * rec.product_id.volume
    
     @api.depends('product_id')
     def compute_stock_weight(self):
         for rec in self:
             rec.total_weight = rec.quantity * rec.product_id.weight


     total_volume = fields.Float ('Volumen', store=True, compute='compute_stock_volume')
     total_weight = fields.Float ('Peso', store=True, compute='compute_stock_weight')
     

