from odoo import fields, models
# from odoo.exceptions import UserError


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    rejected_voucher_account_id = fields.Many2one(
        related='company_id.rejected_voucher_account_id',
        readonly=False,
    )
    deferred_voucher_account_id = fields.Many2one(
        related='company_id.deferred_voucher_account_id',
        readonly=False,
    )
    holding_voucher_account_id = fields.Many2one(
        related='company_id.holding_voucher_account_id',
        readonly=False,
    )
