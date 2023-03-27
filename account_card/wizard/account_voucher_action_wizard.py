##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AccountVoucherActionWizard(models.TransientModel):
    _name = 'account.voucher.action.wizard'
    _description = 'Account Voucher Action Wizard'

    date = fields.Date(
        default=fields.Date.context_today,
        required=True,
    )
    journal_id = fields.Many2one('account.journal',string='Diario')
    action_type = fields.Char(
        'Action type passed on the context',
        required=True,
    )

    def action_confirm(self):
        self.ensure_one()
        if self.action_type not in [
                'claim', 'bank_debit', 'bank_deposit','reject', 'customer_return']:
            raise ValidationError(_(
                'Action %s not supported on vouchers') % self.action_type)
        vouchers = self.env['account.voucher'].browse(
            self._context.get('active_ids'))
        for voucher in vouchers:
            if self.action_type == 'bank_deposit':
                res = voucher.bank_deposit(date=self.date,journal_id=self.journal_id)
            else:
                res = getattr(
                    voucher.with_context(action_date=self.date,journal_id=self.journal_id), self.action_type)()
        if len(vouchers) == 1:
            return res
        else:
            return True
