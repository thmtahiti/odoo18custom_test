import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    _inherit = 'res.company'

    matriculecps = fields.Char(string="Matricule CPS", required=True)
    numerotahiti = fields.Char(string="Numero Tahiti", required=True)