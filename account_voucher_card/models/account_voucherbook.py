##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import fields, models, api, _
import logging
from odoo.exceptions import ValidationError
_logger = logging.getLogger(__name__)


class AccountVoucherbook(models.Model):

    _name = 'account.voucherbook'
    _description = 'Account Voucherbook'

    name = fields.Char(
        compute='_compute_name',
    )
    sequence_id = fields.Many2one(
        'ir.sequence',
        'Sequence',
        copy=False,
        domain=[('code', '=', 'issue_voucher')],
        help="Vouchers numbering sequence.",
        context={'default_code': 'issue_voucher'},
    )
    next_number = fields.Integer(
        'Next Number',
        # usamos compute y no related para poder usar sudo cuando se setea
        # secuencia sin necesidad de dar permiso en ir.sequence
        compute='_compute_next_number',
        inverse='_inverse_next_number',
    )
    issue_voucher_subtype = fields.Selection(
        [('deferred', 'Deferred'), ('currents', 'Currents'), ('electronics','Electronics')],
        string='Issue Voucher Subtype',
        required=True,
        default='deferred',
        help='* Con vouchers corrientes el asiento generado por el pago '
        'descontará directamente de la cuenta de banco y además la fecha de '
        'pago no es obligatoria.\n'
        '* Con vouchers diferidos el asiento generado por el pago se hará '
        'contra la cuenta definida para tal fin en la compañía, luego será '
        'necesario el asiento de débito que se puede generar desde el extracto'
        ' o desde el voucher.',
    )
    journal_id = fields.Many2one(
        'account.journal', 'Journal',
        help='Journal where it is going to be used',
        readonly=True,
        required=True,
        domain=[('type', '=', 'bank')],
        ondelete='cascade',
        context={'default_type': 'bank'},
        states={'draft': [('readonly', False)]},
        auto_join=True,
    )
    range_to = fields.Integer(
        'To Number',
        # readonly=True,
        # states={'draft': [('readonly', False)]},
        help='If you set a number here, this voucherbook will be automatically'
        ' set as used when this number is raised.'
    )
    issue_voucher_ids = fields.One2many(
        'account.voucher',
        'voucherbook_id',
        string='Issue Vouchers',
        readonly=True,
    )
    state = fields.Selection(
        [('draft', 'Draft'), ('active', 'In Use'), ('used', 'Used')],
        string='State',
        # readonly=True,
        default='draft',
        copy=False,
    )
    # TODO depreciar esta funcionalidad que no estamos usando
    block_manual_number = fields.Boolean(
        default=True,
        string='Block manual number?',
        # readonly=True,
        # states={'draft': [('readonly', False)]},
        help='Block user to enter manually another number than the suggested'
    )
    numerate_on_printing = fields.Boolean(
        default=False,
        string='Numerate on printing?',
        # readonly=True,
        # states={'draft': [('readonly', False)]},
        help='No number will be assigne while creating payment, number will be'
        'assigned after printing voucher.'
    )
    report_template = fields.Many2one(
        'ir.actions.report',
        'Report',
        domain="[('model', '=', 'account.payment')]",
        context="{'default_model': 'account.payment'}",
        help='Report to use when printing vouchers. If not report selected, '
        'report with name "voucher_report" will be used',
    )

    @api.depends('sequence_id.number_next_actual')
    def _compute_next_number(self):
        for rec in self:
            rec.next_number = rec.sequence_id.number_next_actual

    def _inverse_next_number(self):
        for rec in self.filtered('sequence_id'):
            rec.sequence_id.sudo().number_next_actual = rec.next_number

    @api.model
    def create(self, vals):
        rec = super(AccountVoucherbook, self).create(vals)
        if not rec.sequence_id:
            rec._create_sequence(vals.get('next_number', 0))
        return rec

    def _create_sequence(self, next_number):
        """ Create a voucher sequence for the voucherbook """
        for rec in self:
            rec.sequence_id = rec.env['ir.sequence'].sudo().create({
                'name': '%s - %s' % (rec.journal_id.name, rec.name),
                'implementation': 'no_gap',
                'padding': 8,
                'number_increment': 1,
                'code': 'issue_voucher',
                # si no lo pasamos, en la creacion se setea 1
                'number_next_actual': next_number,
                'company_id': rec.journal_id.company_id.id,
            })

    def _compute_name(self):
        for rec in self:
            if rec.issue_voucher_subtype == 'deferred':
                name = _('Deferred Vouchers')
            else:
                name = _('Currents Vouchers')
            if rec.range_to:
                name += _(' up to %s') % rec.range_to
            rec.name = name

    def unlink(self):
        if self.mapped('issue_voucher_ids'):
            raise ValidationError(
                _('You can drop a voucherbook if it has been used on vouchers!'))
        return super(AccountVoucherbook, self).unlink()
