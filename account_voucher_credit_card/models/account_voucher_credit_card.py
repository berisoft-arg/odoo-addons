# -*- coding: utf-8 -*-
from odoo import fields, models, _, api
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)

class AccountVoucherCreditCard(models.Model):

    _name = 'account.voucher.credit.card'
    _description = 'Account Voucher Credit Card'
    
    voucher_id = fields.Many2one(
        'account.voucher.credit.card',
        'Voucher',
        required=True,
        ondelete='cascade',
        auto_join=True,
        index=True,)
    
    card = fields.Many2one('res.card', 'Card', 
                                readonly=True, 
                                required=True, 
                                index=True, states={'draft': [('readonly', False)]})
    
    installments = fields.Many2one('installments.card', 'Installements Card', 
                                   readonly=True, 
                                   states={'draft': [('readonly', False)]})
    
    name = fields.Char(
        required=True,
        readonly=True,
        copy=False,
        states={'draft': [('readonly', False)]}, index=True,)

    lot_number = fields.Char(
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
        copy=False,
        index=True,)
    
    coupon_number = fields.Char(
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
        copy=False,
        index=True,)
    
    state = fields.Selection([
        ('cancel', 'Cancelado'),],
        required=True,
        default='draft',
        copy=False,
        compute='_compute_state',
        store=True,
        index=True,)
    
    amount = fields.Monetary(
        currency_field='currency_id',
        readonly=True,
        states={'draft': [('readonly', False)]})
    
    amount_company_currency = fields.Monetary(
        currency_field='company_currency_id',
        readonly=True,
        states={'draft': [('readonly', False)]},)
    
    currency_id = fields.Many2one(
        'res.currency',
        readonly=True,
        states={'draft': [('readonly', False)]},
        default=lambda self: self.env.user.company_id.currency_id.id,
        required=True,)
    
    payment_date = fields.Date(
        readonly=True,
        states={'draft': [('readonly', False)]},
        index=True,)
    
    journal_id = fields.Many2one(
        'account.journal',
        string='Diario',
        required=True,
        domain=[('type', 'in', ['cash', 'bank'])],
        readonly=True,
        states={'draft': [('readonly', False)]},
        index=True,)
    
    company_id = fields.Many2one(
        related='journal_id.company_id',
        store=True,)
    
    company_currency_id = fields.Many2one(
        related='company_id.currency_id',
        string='Moneda de la empresa',)


