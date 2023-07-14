# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    is_credit_card = fields.Boolean('Tarjeta de credito',related='journal_id.is_credit_card')

    voucher_ids = fields.Many2many('account.voucher.credit.card', string='Vouchers',
        copy=False, readonly=True, states={'draft': [('readonly', False)]}, auto_join=True,)
    
    voucher_id = fields.Many2one('account.voucher.credit.card', store=True, string='Voucher',)
    
    name_card = fields.Many2one('res.card', 'Card', readonly=True, states={'draft': [('readonly', False)]})
    
    installments = fields.Many2one('installments.card', 'Installements Card', readonly=True, states={'draft': [('readonly', False)]})

    lot_number = fields.Char(string='Lot')

    coupon_number = fields.Char(string='Coupon')

    
    @api.constrains('lot_number','coupon_number')
    def _check_pago_tarjeta(self):
        for rec in self:
            if rec.is_credit_card:
                if (not rec.lot_number) or (not rec.coupon_number):
                    raise ValidationError("Debe ingresar lote y cupon del pago de la tarjeta")

    
    @api.onchange('journal_id')
    def _journal_id_onchange(self):
        res = {}

        return res

    
