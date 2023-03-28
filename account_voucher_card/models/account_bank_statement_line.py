##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models, api, _
from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)


class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    def button_cancel_reconciliation(self):
        """ Delete operation of vouchers that are debited from statement
        """
        for st_line in self.filtered('move_name'):
            if st_line.journal_entry_ids.filtered(
                    lambda x:
                    x.payment_id.payment_reference == st_line.move_name):
                voucher_operation = self.env['account.voucher.operation'].search(
                    [('origin', '=',
                      'account.bank.statement.line,%s' % st_line.id)])
                voucher_operation.voucher_id._del_operation(st_line)
        return super(
            AccountBankStatementLine, self).button_cancel_reconciliation()

    def process_reconciliation(
            self, counterpart_aml_dicts=None, payment_aml_rec=None,
            new_aml_dicts=None):
        """
        Si el move line de contrapartida es un voucher entregado, entonces
        registramos el debito desde el extracto en el voucher
        TODO: por ahora si se cancela la linea de extracto no borramos el
        debito, habria que ver si queremos hacer eso modificando la funcion de
        arriba directamente
        """

        voucher = False
        if counterpart_aml_dicts:
            for line in counterpart_aml_dicts:
                move_line = line.get('move_line')
                voucher = move_line and move_line.payment_id.voucher_id or False
        moves = super(AccountBankStatementLine, self).process_reconciliation(
            counterpart_aml_dicts=counterpart_aml_dicts,
            payment_aml_rec=payment_aml_rec, new_aml_dicts=new_aml_dicts)
        if voucher and voucher.state == 'handed':
            if voucher.journal_id != self.statement_id.journal_id:
                raise ValidationError(_(
                    'Para registrar el debito de un voucher desde el extracto, '
                    'el diario del voucher y del extracto deben ser los mismos'
                ))
            if len(moves) != 1:
                raise ValidationError(_(
                    'Para registrar el debito de un voucher desde el extracto '
                    'solo debe haber una linea de contrapartida'))
            voucher._add_operation('debited', self, date=self.date)
        return moves
