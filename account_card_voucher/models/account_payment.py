##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import fields, models, _, api
from odoo.exceptions import UserError, ValidationError
import logging
# import odoo.addons.decimal_precision as dp
_logger = logging.getLogger(__name__)


class AccountPayment(models.Model):

    _inherit = 'account.payment'

    voucher_ids = fields.Many2many(
        'account.voucher',
        string='Vouchers',
        copy=False,
        readonly=True,
        states={'draft': [('readonly', False)]},
        auto_join=True,
    )
    # we add this field for better usability on issue vouchers and received
    # vouchers. We keep m2m field for backward compatibility where we allow to
    # use more than one voucher per payment
    voucher_id = fields.Many2one(
        'account.voucher',
        compute='_compute_voucher',
        store=True,
        string='Voucher',
    )
    voucher_deposit_type = fields.Selection(
        [('consolidated', 'Consolidated'),
         ('detailed', 'Detailed')],
        default='detailed',
        help="This option is relevant if you use bank statements. Detailed is"
        " used when the bank credits one by one the vouchers, consolidated is"
        " for when the bank credits all the vouchers in a single movement",
    )

    @api.depends('voucher_ids')
    def _compute_voucher(self):
        for rec in self:
            # we only show vouchers for issue vouchers or received thid vouchers
            # if len of vouchers is 1
            if rec.payment_method_code in (
                    'received_third_voucher',
                    'issue_voucher',) and len(rec.voucher_ids) == 1:
                rec.voucher_id = rec.voucher_ids[0].id

# voucher fields, just to make it easy to load vouchers without need to create
# them by a m2o record
    voucher_name = fields.Char(
        'Nombre',
        readonly=True,
        copy=False,
        states={'draft': [('readonly', False)]},
    )
    voucher_number = fields.Char(
        'Numero',
        readonly=True,
        states={'draft': [('readonly', False)]},
        copy=False,
    )
    voucher_issue_date = fields.Date(
        'Fecha Emision',
        readonly=True,
        copy=False,
        states={'draft': [('readonly', False)]},
        default=fields.Date.context_today,
    )
    voucher_payment_date = fields.Date(
        'Fecha Pago',
        readonly=True,
        help="Only if this voucher is post dated",
        states={'draft': [('readonly', False)]},
    )
    voucherbook_id = fields.Many2one(
        'account.voucherbook',
        'Vouchera',
        readonly=True,
        states={'draft': [('readonly', False)]},
        auto_join=True,
    )
    voucher_subtype = fields.Selection(
        related='voucherbook_id.issue_voucher_subtype',
    )
    voucher_bank_id = fields.Many2one(
        'res.bank',
        'Banco',
        readonly=True,
        copy=False,
        states={'draft': [('readonly', False)]},
        auto_join=True,
    )
    voucher_owner_vat = fields.Char(
        'CUIT del Emisor',
        readonly=True,
        copy=False,
        states={'draft': [('readonly', False)]}
    )
    voucher_owner_name = fields.Char(
        'Nombre Emisor',
        readonly=True,
        copy=False,
        states={'draft': [('readonly', False)]}
    )
    # this fields is to help with code and view
    voucher_type = fields.Char(
        compute='_compute_voucher_type',
        store=True
    )
    voucherbook_numerate_on_printing = fields.Boolean(
        related='voucherbook_id.numerate_on_printing',
    )
    # TODO borrar, esto estaria depreciado
    # voucherbook_block_manual_number = fields.Boolean(
    #     related='voucherbook_id.block_manual_number',
    #     readonly=True,
    # )
    # voucher_number_readonly = fields.Integer(
    #     related='voucher_number',
    #     readonly=True,
    # )

    @api.depends('payment_method_code')
    def _compute_voucher_type(self):
        for rec in self:
            if rec.payment_method_code == 'issue_voucher':
                rec.voucher_type = 'issue_voucher'
            elif rec.payment_method_code in [
                    'received_third_voucher',
                    'delivered_third_voucher']:
                rec.voucher_type = 'third_voucher'

    def _compute_payment_method_description(self):
        voucher_payments = self.filtered(
            lambda x: x.payment_method_code in
            ['issue_voucher', 'received_third_voucher', 'delivered_third_voucher'])
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

# on change methods

    @api.constrains('voucher_ids')
    @api.onchange('voucher_ids', 'payment_method_code')
    def onchange_vouchers(self):
        for rec in self:
            # we only overwrite if payment method is delivered
            if rec.payment_method_code == 'delivered_third_voucher':
                rec.amount = sum(rec.voucher_ids.mapped('amount'))
                currency = rec.voucher_ids.mapped('currency_id')

                if len(currency) > 1:
                    raise ValidationError(_(
                        'You are trying to deposit vouchers of difference'
                        ' currencies, this functionality is not supported'))
                elif len(currency) == 1:
                    rec.currency_id = currency.id

                # si es una entrega de vouchers de terceros y es en otra moneda
                # a la de la cia, forzamos el importe en moneda de cia de los
                # vouchers originales
                # escribimos force_amount_company_currency directamente en vez
                # de amount_company_currency por lo explicado en
                # _inverse_amount_company_currency
                if rec.currency_id != rec.company_currency_id:
                    rec.force_amount_company_currency = sum(
                        rec.voucher_ids.mapped('amount_company_currency'))

    @api.onchange('amount_company_currency')
    def _inverse_amount_company_currency(self):
        # el metodo _inverse_amount_company_currency tiene un parche feo de
        # un onchange sobre si mismo que termina haciendo que se vuelva a
        # ejecutar y entonces no siempre guarde el importe en otra moneda
        # habria que eliminar ese onchange, por el momento anulando
        # eso para los vouchers de terceros y escribiendo directamente
        # force_amount_company_currency, lo solucionamos
        self = self.filtered(
            lambda x: x.payment_method_code != 'delivered_third_voucher')
        return super(AccountPayment, self)._inverse_amount_company_currency()

    @api.onchange('voucher_number')
    def change_voucher_number(self):
        # TODO make default padding a parameter
        def _get_name_from_number(number):
            padding = 8
            if len(str(number)) > padding:
                padding = len(str(number))
            #return ('%%0%' % padding % number)
            return str(padding) + str(number)

        for rec in self:
            if rec.payment_method_code in ['received_third_voucher']:
                if not rec.voucher_number:
                    voucher_name = False
                else:
                    voucher_name = _get_name_from_number(rec.voucher_number)
                rec.voucher_name = voucher_name
            elif rec.payment_method_code in ['issue_voucher']:
                sequence = rec.voucherbook_id.sequence_id
                if not rec.voucher_number:
                    voucher_name = False
                elif sequence:
                    if rec.voucher_number != sequence.number_next_actual:
                        # write with sudo for access rights over sequence
                        sequence.sudo().write(
                            {'number_next_actual': rec.voucher_number})
                    voucher_name = rec.voucherbook_id.sequence_id.next_by_id()
                else:
                    # in sipreco, for eg, no sequence on voucherbooks
                    voucher_name = _get_name_from_number(rec.voucher_number)
                rec.voucher_name = voucher_name

    @api.onchange('voucher_issue_date', 'voucher_payment_date')
    def onchange_date(self):
        if (
                self.voucher_issue_date and self.voucher_payment_date and
                self.voucher_issue_date > self.voucher_payment_date):
            self.voucher_payment_date = False
            raise UserError(
                _('Voucher Payment Date must be greater than Issue Date'))

    @api.onchange('voucher_owner_vat')
    def onchange_voucher_owner_vat(self):
        """
        We suggest owner name from owner vat
        """
        # if not self.voucher_owner_name:
        self.voucher_owner_name = self.search(
            [('voucher_owner_vat', '=', self.voucher_owner_vat)],
            limit=1).voucher_owner_name

    @api.onchange('partner_id', 'payment_method_code')
    def onchange_partner_voucher(self):
        commercial_partner = self.partner_id.commercial_partner_id
        if self.payment_method_code == 'received_third_voucher':
            self.voucher_bank_id = (
                commercial_partner.bank_ids and
                commercial_partner.bank_ids[0].bank_id or False)
            # en realidad se termina pisando con onchange_voucher_owner_vat
            # entonces llevamos nombre solo si ya existe la priemr vez
            # TODO ver si lo mejoramos o borramos esto directamente
            # self.voucher_owner_name = commercial_partner.name
            vat_field = 'vat'
            # to avoid needed of another module, we add this voucher to see
            # if l10n_ar cuit field is available
            if 'cuit' in commercial_partner._fields:
                vat_field = 'cuit'
            self.voucher_owner_vat = commercial_partner[vat_field]
        elif self.payment_method_code == 'issue_voucher':
            self.voucher_bank_id = self.journal_id.bank_id
            self.voucher_owner_name = False
            self.voucher_owner_vat = False
        # no hace falta else porque no se usa en otros casos

    @api.onchange('payment_method_code')
    def _onchange_payment_method_code(self):
        if self.payment_method_code == 'issue_voucher':
            voucherbook = self.env['account.voucherbook'].search([
                ('state', '=', 'active'),
                ('journal_id', '=', self.journal_id.id)],
                limit=1)
            self.voucherbook_id = voucherbook
        elif self.voucherbook_id:
            # TODO ver si interesa implementar volver atras numeracion
            self.voucherbook_id = False
        # si cambiamos metodo de pago queremos refrescar listado de vouchers
        # seleccionados
        self.voucher_ids = False

    @api.onchange('voucherbook_id')
    def onchange_voucherbook(self):
        if self.voucherbook_id and not self.voucherbook_id.numerate_on_printing:
            self.voucher_number = self.voucherbook_id.next_number
        else:
            self.voucher_number = False

# post methods
    def cancel(self):
        for rec in self:
            # solo cancelar operaciones si estaba postead, por ej para comp.
            # con pagos confirmados, se cancelan pero no hay que deshacer nada
            # de asientos ni vouchers
            if rec.state in ['confirmed', 'posted']:
                rec.do_vouchers_operations(cancel=True)
        res = super(AccountPayment, self).cancel()
        return res

    @api.model
    def X_create(self,vals):
        if 'payment_method_id' in vals:
            payment_method = self.env['account.payment.method'].browse(vals['payment_method_id'])
        else:
            payment_method = None
        res = super(AccountPayment, self).create(vals)
        if payment_method and payment_method.code == 'received_third_voucher':
            voucher_type = 'third_voucher'
            for rec in res:
                bank = self.env['res.bank'].browse(vals['voucher_bank_id'])
                res.create_voucher(voucher_type,None,bank)
        return res

    def create_voucher(self, voucher_type, operation, bank):
        self.ensure_one()

        voucher_vals = {
            'bank_id': bank.id,
            'owner_name': self.voucher_owner_name,
            'owner_vat': self.voucher_owner_vat,
            'number': self.voucher_number,
            'name': self.voucher_name,
            'voucherbook_id': self.voucherbook_id.id,
            'issue_date': self.voucher_issue_date,
            'type': self.voucher_type,
            'journal_id': self.journal_id.id,
            'amount': self.amount,
            'payment_date': self.voucher_payment_date,
            'currency_id': self.currency_id.id,
            'amount_company_currency': self.amount_company_currency,
        }

        voucher = self.env['account.voucher'].create(voucher_vals)
        self.voucher_ids = [(4, voucher.id, False)]
        if operation:
            voucher._add_operation(
                operation, self, self.partner_id, date=self.date)
        return voucher

    def do_vouchers_operations(self, vals=None, cancel=False):
        """
        Voucher attached .ods file on this module to understand vouchers workflows
        This method is called from:
        * cancellation of payment to execute delete the right operation and
            unlink voucher if needed
        * from _get_liquidity_move_line_vals to add voucher operation and, if
            needded, change payment vals and/or create voucher and
        TODO si queremos todos los del operation podriamos moverlos afuera y
        simplificarlo ya que es el mismo en casi todos
        Tambien podemos simplficiar las distintas opciones y como se recorren
        los if
        """
        self.ensure_one()
        rec = self
        if not rec.voucher_type:
            # continue
            return vals
        if (
                rec.payment_method_code == 'received_third_voucher' and
                rec.payment_type == 'inbound'
                # el vouchero de partner type no seria necesario
                # un proveedor nos podria devolver plata con un voucher
                # and rec.partner_type == 'customer'
        ):
            operation = 'holding'
            if cancel:
                _logger.info('Cancel Receive Voucher')
                rec.voucher_ids._del_operation(self)
                rec.voucher_ids.unlink()
                return None

            _logger.info('Receive Voucher')
            voucher = self.create_voucher(
                    'third_voucher', operation, self.voucher_bank_id)
            if not vals:
                vals = {}
            vals['date_maturity'] = self.voucher_payment_date
            vals['account_id'] = voucher.get_third_voucher_account().id
            vals['name'] = _('Receive voucher %s') % voucher.name
        elif (
                rec.payment_method_code == 'delivered_third_voucher' and
                rec.payment_type == 'transfer'):
            # si el voucher es entregado en una transferencia tenemos tres
            # opciones
            # TODO we should make this method selectable for transfers
            inbound_method = (
                rec.destination_journal_id.inbound_payment_method_ids)
            # si un solo inbound method y es received third voucher
            # entonces consideramos que se esta moviendo el voucher de un diario
            # al otro
            if len(inbound_method) == 1 and (
                    inbound_method.code == 'received_third_voucher'):
                if cancel:
                    _logger.info('Cancel Transfer Voucher')
                    for voucher in rec.voucher_ids:
                        voucher._del_operation(self)
                        voucher._del_operation(self)
                        receive_op = voucher._get_operation('holding')
                        if receive_op.origin._name == 'account.payment':
                            voucher.journal_id = receive_op.origin.journal_id.id
                    return None

                _logger.info('Transfer Voucher')
                # get the account before changing the journal on the voucher
                vals['account_id'] = rec.voucher_ids.get_third_voucher_account().id
                rec.voucher_ids._add_operation(
                    'transfered', rec, False, date=rec.date)
                rec.voucher_ids._add_operation(
                    'holding', rec, False, date=rec.date)
                rec.voucher_ids.write({
                    'journal_id': rec.destination_journal_id.id})
                vals['name'] = _('Transfer vouchers %s') % ', '.join(
                    rec.voucher_ids.mapped('name'))
            elif rec.destination_journal_id.type == 'cash':
                if cancel:
                    _logger.info('Cancel Sell Voucher')
                    rec.voucher_ids._del_operation(self)
                    return None

                _logger.info('Sell Voucher')
                rec.voucher_ids._add_operation(
                    'selled', rec, False, date=rec.date)
                vals['account_id'] = rec.voucher_ids.get_third_voucher_account().id
                vals['name'] = _('Sell voucher %s') % ', '.join(
                    rec.voucher_ids.mapped('name'))
            # bank
            else:
                if cancel:
                    _logger.info('Cancel Deposit Voucher')
                    rec.voucher_ids._del_operation(self)
                    return None

                _logger.info('Deposit Voucher')
                rec.voucher_ids._add_operation(
                    'deposited', rec, False, date=rec.date)
                vals['account_id'] = rec.voucher_ids.get_third_voucher_account().id
                vals['name'] = _('Deposit vouchers %s') % ', '.join(
                    rec.voucher_ids.mapped('name'))
        elif (
                rec.payment_method_code == 'delivered_third_voucher' and
                rec.payment_type == 'outbound'
                # el vouchero del partner type no es necesario
                # podriamos entregarlo a un cliente
                # and rec.partner_type == 'supplier'
        ):
            if cancel:
                _logger.info('Cancel Deliver Voucher')
                rec.voucher_ids._del_operation(self)
                return None

            _logger.info('Deliver Voucher')
            rec.voucher_ids._add_operation(
                'delivered', rec, rec.partner_id, date=rec.date)
            for voucher in rec.voucher_ids:
                voucher.state = 'delivered'
            try:
                vals['account_id'] = rec.voucher_ids.get_third_voucher_account().id
                vals['name'] = _('Deliver vouchers %s') % ', '.join(rec.voucher_ids.mapped('name'))
            except:
                vals = {}
                vals['account_id'] = rec.voucher_ids.get_third_voucher_account().id
                vals['name'] = _('Deliver vouchers %s') % ', '.join(rec.voucher_ids.mapped('name'))

        elif (
                rec.payment_method_code == 'issue_voucher' and
                rec.payment_type == 'outbound'
                # el chequeo del partner type no es necesario
                # podriamos entregarlo a un cliente
                # and rec.partner_type == 'supplier'
        ):
            if cancel:
                _logger.info('Cancel Hand/debit Voucher')
                rec.voucher_ids._del_operation(self)
                rec.voucher_ids.unlink()
                return None

            _logger.info('Hand/debit Voucher')
            # if voucher is deferred, hand it and later debit it change account
            # if voucher is current, debit it directly
            # operation = 'debited'
            # al final por ahora depreciamos esto ya que deberiamos adaptar
            # rechazos y demas, deferred solamente sin fecha pero con cuenta
            # puente
            # if self.voucher_subtype == 'deferred':

            #raise ValidationError('estamos aca %s'%(self.company_id.deferred_voucher_account_id.code))
            if not self.company_id.deferred_voucher_account_id:
                raise ValidationError('No hay cuenta de vouchers diferidos definida')
            vals = {}
            vals['account_id'] = self.company_id.deferred_voucher_account_id.id
            operation = 'handed'
            voucher = self.create_voucher(
                'issue_voucher', operation, self.voucher_bank_id)
            vals['date_maturity'] = self.voucher_payment_date
            vals['name'] = _('Hand voucher %s') % voucher.name
        elif (
                rec.payment_method_code == 'issue_voucher' and
                rec.payment_type == 'transfer' and
                rec.destination_journal_id.type == 'cash'):
            if cancel:
                _logger.info('Cancel Withdrawal Voucher')
                rec.voucher_ids._del_operation(self)
                rec.voucher_ids.unlink()
                return None

            _logger.info('Withdraw Voucher')
            self.create_voucher('issue_voucher', 'withdrawed', self.voucher_bank_id)
            vals['name'] = _('Withdraw with vouchers %s') % ', '.join(
                rec.voucher_ids.mapped('name'))
            vals['date_maturity'] = self.voucher_payment_date
            # if voucher is deferred, change account
            # si retiramos por caja directamente lo sacamos de banco
            # if self.voucher_subtype == 'deferred':
            #     vals['account_id'] = self.company_id._get_voucher_account(
            #         'deferred').id
        else:
            raise UserError(_(
                'This operatios is not implemented for vouchers:\n'
                '* Payment type: %s\n'
                '* Partner type: %s\n'
                '* Payment method: %s\n'
                '* Destination journal: %s\n' % (
                    rec.payment_type,
                    rec.partner_type,
                    rec.payment_method_code,
                    rec.destination_journal_id.type)))
        return vals

    def action_post(self):
        for rec in self:
            if rec.voucher_ids and not rec.currency_id.is_zero(
                    sum(rec.voucher_ids.mapped('amount')) - rec.amount):
                raise UserError(_(
                    'La suma del pago no coincide con la suma de los vouchers '
                    'seleccionados. Por favor intente eliminar y volver a '
                    'agregar un voucher.'))
            if rec.payment_method_code == 'issue_voucher' and (
                    not rec.voucher_number or not rec.voucher_name):
                raise UserError(_(
                    'Para mandar a proceso de firma debe definir número '
                    'de voucher en cada línea de pago.\n'
                    '* ID del pago: %s') % rec.id)

        res = super(AccountPayment, self).action_post()
        for rec in self:
            if rec.payment_method_id.code in ['received_third_voucher','delivered_third_voucher','issue_voucher']:
                rec.do_vouchers_operations()
        return res

    def _get_liquidity_move_line_vals(self, amount):
        vals = super(AccountPayment, self)._get_liquidity_move_line_vals(
            amount)
        vals = self.do_vouchers_operations(vals=vals)
        return vals

    def do_print_vouchers(self):
        # si cambiamos nombre de voucher_report tener en cuenta en sipreco
        voucherbook = self.mapped('voucherbook_id')
        # si todos los vouchers son de la misma vouchera entonces buscamos
        # reporte específico para esa vouchera
        report_name = len(voucherbook) == 1 and  \
            voucherbook.report_template.report_name \
            or 'voucher_report'
        voucher_report = self.env['ir.actions.report'].search(
            [('report_name', '=', report_name)], limit=1).report_action(self)
        # ya el buscar el reporte da el error solo
        # if not voucher_report:
        #     raise UserError(_(
        #       "There is no voucher report configured.\nMake sure to configure "
        #       "a voucher report named 'account_voucher_report'."))
        return voucher_report

    def print_vouchers(self):
        if len(self.mapped('voucherbook_id')) != 1:
            raise UserError(_(
                "In order to print multiple vouchers at once, they must belong "
                "to the same voucherbook."))
        # por ahora preferimos no postearlos
        # self.filtered(lambda r: r.state == 'draft').post()

        # si numerar al imprimir entonces llamamos al wizard
        if self[0].voucherbook_id.numerate_on_printing:
            if all([not x.voucher_name for x in self]):
                next_voucher_number = self[0].voucherbook_id.next_number
                return {
                    'name': _('Print Pre-numbered Vouchers'),
                    'type': 'ir.actions.act_window',
                    'res_model': 'print.prenumbered.vouchers',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'target': 'new',
                    'context': {
                        'payment_ids': self.ids,
                        'default_next_voucher_number': next_voucher_number,
                    }
                }
            # si ya están enumerados mandamos a imprimir directamente
            elif all([x.voucher_name for x in self]):
                return self.do_print_vouchers()
            else:
                raise UserError(_(
                    'Está queriendo imprimir y enumerar vouchers que ya han '
                    'sido numerados. Seleccione solo vouchers numerados o solo'
                    ' vouchers sin número.'))
        else:
            return self.do_print_vouchers()

    def _get_counterpart_move_line_vals(self, invoice=False):
        vals = super(AccountPayment, self)._get_counterpart_move_line_vals(
            invoice=invoice)
        force_account_id = self._context.get('force_account_id')
        if force_account_id:
            vals['account_id'] = force_account_id
        return vals

    def _split_aml_line_per_voucher(self, move):
        """ Take an account mvoe, find the move lines related to voucher and
        split them one per earch voucher related to the payment
        """
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

        # if the move line has currency then we are delivering vouchers on a
        # different currency than company one
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
            lambda x: x.payment_type == 'transfer' and
                x.payment_method_code == 'delivered_third_voucher' and
                x.voucher_deposit_type == 'detailed'):
            self._split_aml_line_per_voucher(move)
        return move

    def _create_transfer_entry(self, amount):
        transfer_debit_aml = super(
            AccountPayment, self)._create_transfer_entry(amount)
        if self.filtered(
            lambda x: x.payment_type == 'transfer' and
                x.payment_method_code == 'delivered_third_voucher' and
                x.voucher_deposit_type == 'detailed'):
            self._split_aml_line_per_voucher(transfer_debit_aml.move_id)
        return transfer_debit_aml
