##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models, api, fields
import logging
_logger = logging.getLogger(__name__)


class AccountChartTemplate(models.Model):
    _inherit = 'account.chart.template'

    rejected_voucher_account_id = fields.Many2one(
        'account.account.template',
        'Rejected voucher Account',
        help='Rejection Vouchers account, for eg. "Rejected Vouchers"',
        # domain=[('type', 'in', ['other'])],
    )
    deferred_voucher_account_id = fields.Many2one(
        'account.account.template',
        'Deferred Voucher Account',
        help='Deferred Vouchers account, for eg. "Deferred Vouchers"',
        # domain=[('type', 'in', ['other'])],
    )
    holding_voucher_account_id = fields.Many2one(
        'account.account.template',
        'Holding Voucher Account',
        help='Holding Vouchers account for third vouchers, '
        'for eg. "Holding Vouchers"',
        # domain=[('type', 'in', ['other'])],
    )

    def _load_template(
            self, company, code_digits=None,
            account_ref=None, taxes_ref=None):
        account_ref, taxes_ref = super(
            AccountChartTemplate, self)._load_template(
                company,
                code_digits=code_digits,
                account_ref=account_ref,
                taxes_ref=taxes_ref)
        for field in [
                'rejected_voucher_account_id',
                'deferred_voucher_account_id',
                'holding_voucher_account_id']:
            account_field = self[field]
            # TODO we should send it in the context and overwrite with
            # lower hierichy values
            if account_field:
                company[field] = account_ref[account_field.id]
        return account_ref, taxes_ref

    def _create_bank_journals(self, company, acc_template_ref):
        """
        Bank - Cash journals are created with this method
        Inherit this function in order to add vouchers to cash and bank
        journals. This is because usually will be installed before chart loaded
        and they will be disable by default
        """

        res = super(
            AccountChartTemplate, self)._create_bank_journals(
            company, acc_template_ref)

        # creamos diario para vouchers de terceros
        received_third_voucher = self.env.ref(
            'account_voucher.account_payment_method_received_third_voucher')
        delivered_third_voucher = self.env.ref(
            'account_voucher.account_payment_method_delivered_third_voucher')
        self.env['account.journal'].create({
            'name': 'Vouchers de Terceros',
            'type': 'cash',
            'company_id': company.id,
            'inbound_payment_method_ids': [
                (4, received_third_voucher.id, None)],
            'outbound_payment_method_ids': [
                (4, delivered_third_voucher.id, None)],
        })

        self.env['account.journal'].with_context(
            force_company_id=company.id)._enable_issue_voucher_on_bank_journals()
        return res
