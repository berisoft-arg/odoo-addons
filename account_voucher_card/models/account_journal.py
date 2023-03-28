##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models, fields, api, _
from odoo.tools.misc import formatLang
from ast import literal_eval


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    voucherbook_ids = fields.One2many(
        'account.voucherbook',
        'journal_id',
        'Voucherbooks',
        auto_join=True,
    )

    @api.model
    def create(self, vals):
        rec = super(AccountJournal, self).create(vals)
        issue_vouchers = self.env.ref(
            'account_voucher.account_payment_method_issue_voucher')
        if (issue_vouchers in rec.outbound_payment_method_ids and
                not rec.voucherbook_ids):
            rec._create_voucherbook()
        return rec

    def _create_voucherbook(self):
        """ Create a voucher sequence for the journal """
        for rec in self:
            voucherbook = rec.voucherbook_ids.create({
                'journal_id': rec.id,
            })
            voucherbook.state = 'active'

    @api.model
    def _enable_issue_voucher_on_bank_journals(self):
        """ Enables issue vouchers payment method
            Called upon module installation via data file.
        """
        issue_vouchers = self.env.ref(
            'account_voucher.account_payment_method_issue_voucher')
        domain = [('type', '=', 'bank')]
        force_company_id = self._context.get('force_company_id')
        if force_company_id:
            domain += [('company_id', '=', force_company_id)]
        bank_journals = self.search(domain)
        for bank_journal in bank_journals:
            if not bank_journal.voucherbook_ids:
                bank_journal._create_voucherbook()
            bank_journal.write({
                'outbound_payment_method_ids': [(4, issue_vouchers.id, None)],
            })

###############
# For dashboard
###############

    def get_journal_dashboard_datas(self):
        domain_holding_third_vouchers = [
            ('type', '=', 'third_voucher'),
            ('journal_id', '=', self.id),
            ('state', '=', 'holding')
        ]
        domain_handed_issue_vouchers = [
            ('type', '=', 'issue_voucher'),
            ('journal_id', '=', self.id),
            ('state', '=', 'handed')
        ]
        handed_vouchers = self.env['account.voucher'].search(
            domain_handed_issue_vouchers)
        holding_vouchers = self.env['account.voucher'].search(
            domain_holding_third_vouchers)

        num_vouchers_to_numerate = False
        if self.env['ir.actions.report'].search(
                [('report_name', '=', 'voucher_report')]):
            num_vouchers_to_numerate = self.env['account.payment'].search_count([
                ('journal_id', '=', self.id),
                ('payment_method_id.code', '=', 'issue_voucher'),
                ('state', '=', 'draft'),
                ('voucher_name', '=', False),
            ])
        return dict(
            super(AccountJournal, self).get_journal_dashboard_datas(),
            num_vouchers_to_numerate=num_vouchers_to_numerate,
            num_holding_third_vouchers=len(holding_vouchers),
            show_third_vouchers=(
                'received_third_voucher' in
                self.inbound_payment_method_ids.mapped('code')),
            show_issue_vouchers=(
                'issue_voucher' in
                self.outbound_payment_method_ids.mapped('code')),
            num_handed_issue_vouchers=len(handed_vouchers),
            handed_amount=formatLang(
                self.env, sum(handed_vouchers.mapped('amount_company_currency')),
                currency_obj=self.company_id.currency_id),
            holding_amount=formatLang(
                self.env, sum(holding_vouchers.mapped(
                    'amount_company_currency')),
                currency_obj=self.company_id.currency_id),
        )

    def open_action_vouchers(self):
        voucher_type = self.env.context.get('voucher_type', False)
        if voucher_type == 'third_voucher':
            action_name = 'account_voucher.action_third_voucher'
        elif voucher_type == 'issue_voucher':
            action_name = 'account_voucher.action_issue_voucher'
        else:
            return False
        actions = self.env.ref(action_name)
        action_read = actions.read()[0]
        context = literal_eval(action_read['context'])
        context['search_default_journal_id'] = self.id
        action_read['context'] = context
        return action_read

    def action_vouchers_to_numerate(self):
        return {
            'name': _('Checks to Print and Numerate'),
            'type': 'ir.actions.act_window',
            'view_mode': 'list,form,graph',
            'res_model': 'account.payment',
            'context': dict(
                self.env.context,
                search_default_vouchers_to_numerate=1,
                search_default_journal_id=self.id,
                journal_id=self.id,
                default_journal_id=self.id,
                default_payment_type='outbound',
                default_payment_method_id=self.env.ref(
                    'account_voucher.account_payment_method_issue_voucher').id,
            ),
        }
