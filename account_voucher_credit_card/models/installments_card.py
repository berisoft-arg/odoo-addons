# -*- coding: utf-8 -*-
import logging
from odoo import models, fields


_logger = logging.getLogger(__name__)


class InstallmentsCard(models.Model):
    """installments card"""
    _name = "installments.card"
    _description = 'Installments Cards'
    _order = 'name'

    name = fields.Char(string='Installments Card', required=True, store=True)
    

    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'The Installments Plan Card name must be unique!')
    ]
