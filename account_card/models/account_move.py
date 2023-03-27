##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models, fields, api

class AccountMove(models.Model):
    _inherit = 'account.move'

    # we add this field so that when invoice is validated we can reconcile
    # move lines between voucher and invoice lines
    # igual se setea para todos los rechazos, tal vez mas adelante lo usamos
    # para otra cosa
    rejected_voucher_id = fields.Many2one(
        'account.voucher',
        'Rejected Voucher',
    )

    def action_cancel(self):
        """
        Si al cancelar la factura la misma estaba vinculada a un rechazo
        intentamos romper la conciliacion del rechazo
        """
        for rec in self.filtered(lambda x: x.rejected_voucher_id):
            voucher = rec.rejected_voucher_id
            deferred_account = voucher.company_id._get_voucher_account('deferred')
            if (
                    voucher.state == 'rejected' and
                    voucher.type == 'issue_voucher' and
                    deferred_account.reconcile):
                deferred_account_line = rec.move_id.line_ids.filtered(
                    lambda x: x.account_id == deferred_account)
                deferred_account_line.remove_move_reconcile()
        return super(AccountMove, self).action_cancel()

    def action_move_create(self):
        """
        Si al validar la factura, la misma tiene un voucher de rechazo asociado
        intentamos concilarlo
        """
        res = super(AccountInvoice, self).action_move_create()
        #for rec in self.filtered(lambda x: x.rejected_voucher_id):
        #    voucher = rec.rejected_voucher_id
        #    if voucher.state == 'rejected' and voucher.type == 'issue_voucher':
        #        rec.rejected_voucher_id.handed_reconcile(rec.move_id)
        return res
