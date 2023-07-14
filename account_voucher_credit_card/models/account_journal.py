# -*- coding: utf-8 -*-

from odoo import models, fields


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    is_credit_card = fields.Boolean('Tarjeta de Credito')

