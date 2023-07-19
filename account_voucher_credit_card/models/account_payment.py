# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    is_credit_card = fields.Boolean('Tarjeta de credito',related='journal_id.is_credit_card')

    voucher_ids = fields.Many2many('account.voucher.credit.card', string='Vouchers',
        copy=False, readonly=True, states={'draft': [('readonly', False)]}, auto_join=True,)
    
    voucher_id = fields.Many2one('account.voucher.credit.card', compute='_compute_voucher', store=True, string='Voucher',)
    
    card = fields.Many2one('res.card', 'Card', readonly=True, states={'draft': [('readonly', False)]})
    
    installments = fields.Many2one('installments.card', 'Installements Card', readonly=True, states={'draft': [('readonly', False)]})

    lot_number = fields.Char(string='Lot')

    coupon_number = fields.Char(string='Coupon')

    voucher_name = fields.Char(
        'Name',
        readonly=True,
        copy=False,
        states={'draft': [('readonly', False)]},)


    @api.constrains('lot_number','coupon_number')
    def _check_pago_tarjeta(self):
        for rec in self:
            if rec.is_credit_card:
                if (not rec.lot_number) or (not rec.coupon_number):
                    raise ValidationError("Debe ingresar lote y cupon del pago de la tarjeta")

    
    @api.depends('voucher_ids')
    def _compute_voucher(self):
        for rec in self:
            if rec.payment_method_code in (
                    'inbound_credit_card',) and len(rec.voucher_ids) == 1:
                rec.voucher_id = rec.voucher_ids[0].id


    def _compute_payment_method_description(self):
        voucher_payments = self.filtered(
            lambda x: x.payment_method_code in
            ['inbound_credit_card', 'outbound_credit_card'])
        for rec in voucher_payments:
            if rec.voucher_ids:
                vouchers_desc = ', '.join(rec.voucher_ids.mapped('name'))
            else:
                vouchers_desc = rec.voucher_name
            name = "%s: %s" % (rec.payment_method_id.display_name, vouchers_desc)
            rec.payment_method_description = name
        return super(
            AccountPayment,
            (self - voucher_payments))._compute_payment_method_description()
    

    @api.model
    def X_create(self,vals):
        if 'payment_method_id' in vals:
            payment_method = self.env['account.payment.method'].browse(vals['payment_method_id'])
        else:
            payment_method = None
        res = super(AccountPayment, self).create(vals)
        if payment_method and payment_method.code == 'inbound_credit_card':
            for rec in res:
                card = self.env['res.card'].browse(vals['voucher_card_id'])
                res.create_check(None,None,bank)
        return res
    
    
    def create_voucher(self, card):
        self.ensure_one()

        voucher_vals = {
            'card_id': card.id,
            'installments': self.installments,
            'lot_number': self.lot_number,
            'coupon_number': self.coupon_number,
            'journal_id': self.journal_id.id,
            'amount': self.amount,
            'currency_id': self.currency_id.id,
            'amount_company_currency': self.amount_company_currency,
        }

        voucher = self.env['account.voucher.credit.card'].create(voucher_vals)
        self.voucher_ids = [(4, voucher.id, False)]
        return voucher
    

    def action_post(self):
        for rec in self:
            if rec.voucher_ids and not rec.currency_id.is_zero(
                    sum(rec.voucher_ids.mapped('amount')) - rec.amount):
                raise UserError(_(
                    'La suma del pago no coincide con la suma de los vouchers '
                    'seleccionados. Por favor intente eliminar y volver a '
                    'agregar un voucher.'))
        res = super(AccountPayment, self).action_post()
        return res

    
    def _get_liquidity_move_line_vals(self, amount):
        vals = super(AccountPayment, self)._get_liquidity_move_line_vals(
            amount)
        return vals
    

    def _get_counterpart_move_line_vals(self, invoice=False):
        vals = super(AccountPayment, self)._get_counterpart_move_line_vals(
            invoice=invoice)
        force_account_id = self._context.get('force_account_id')
        if force_account_id:
            vals['account_id'] = force_account_id
        return vals
    
    
    def _split_aml_line_per_voucher(self, move):
        self.ensure_one()
        res = self.env['account.move.line']
        move.button_cancel()
        vouchers = self.voucher_ids
        aml = move.line_ids.with_context(voucher_move_validity=False).filtered(
            lambda x: x.name != self.name)
        if len(aml) > 1:
            raise UserError(
                _('Seems like this move has been already splited'))
        elif len(aml) == 0:
            raise UserError(
                _('There is not move lines to split'))

        amount_field = 'credit' if aml.credit else 'debit'
        new_name = _('Deposit voucher %s') if aml.credit else \
            aml.name + _(' voucher %s')
        currency = aml.currency_id
        currency_sign = amount_field == 'debit' and 1.0 or -1.0
        aml.write({
            'name': new_name % vouchers[0].name,
            amount_field: vouchers[0].amount_company_currency,
            'amount_currency': currency and currency_sign * vouchers[0].amount,
        })
        res |= aml
        vouchers -= vouchers[0]
        for voucher in vouchers:
            res |= aml.copy({
                'name': new_name % voucher.name,
                amount_field: voucher.amount_company_currency,
                'payment_id': self.id,
                'amount_currency': currency and currency_sign * voucher.amount,
            })
        move.post()
        return res
    
    def _create_payment_entry(self, amount):
        move = super(AccountPayment, self)._create_payment_entry(amount)
        if self.filtered(
            lambda x: 
                x.payment_method_code == 'outbound_credit_card' and
                x.voucher_deposit_type == 'detailed'):
            self._split_aml_line_per_voucher(move)
        return move
    




    
    

    
    # @api.onchange('journal_id')
    # def _journal_id_onchange(self):
    #     res = {}

    #     return res

    
