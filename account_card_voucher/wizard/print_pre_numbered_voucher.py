
from odoo import api, fields, models


class PrintPreNumberedVouchers(models.TransientModel):
    _name = 'print.prenumbered.vouchers'
    _description = 'Print Pre-numbered Vouchers'

    next_voucher_number = fields.Integer('Next Voucher Number', required=True)

    def print_vouchers(self):
        voucher_number = self.next_voucher_number
        payments = self.env['account.payment'].browse(
            self.env.context['payment_ids'])
        for payment in payments:
            payment.voucher_number = voucher_number
            voucher_number += 1
            payment.change_voucher_number()
        return payments.do_print_vouchers()
