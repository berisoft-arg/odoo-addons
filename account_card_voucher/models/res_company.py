##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import fields, models, api, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    _inherit = 'res.company'

    rejected_voucher_account_id = fields.Many2one(
        'account.account',
        'Rejected Vouchers Account',
        help='Rejection Vouchers account, for eg. "Rejected Vouchers"',
    )
    deferred_voucher_account_id = fields.Many2one(
        'account.account',
        'Deferred Vouchers Account',
        help='Deferred Vouchers account, for eg. "Deferred Vouchers"',
    )
    holding_voucher_account_id = fields.Many2one(
        'account.account',
        'Holding Vouchers Account',
        help='Holding Vouchers account for third vouchers, '
        'for eg. "Holding Vouchers"',
    )

    def _get_voucher_account(self, voucher_type):
        self.ensure_one()
        if voucher_type == 'holding':
            account = self.holding_voucher_account_id
        elif voucher_type == 'rejected':
            account = self.rejected_voucher_account_id
        elif voucher_type == 'deferred':
            account = self.deferred_voucher_account_id
        else:
            raise UserError(_("Voucher type %s not implemented!") % voucher_type)
        if not account:
            raise UserError(_(
                'No vouchers %s account defined for company %s'
            ) % (voucher_type, self.name))
        return account
