# -*- coding: utf-8 -*-

import logging
from odoo import models, fields


_logger = logging.getLogger(__name__)


class Card(models.Model):
    """res card"""
    _name = "res.card"
    _description = 'Cards'
    _order = 'name'

    name = fields.Char(string='Card', required=True, store=True)
    

    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'The Card name must be unique!')
    ]
