import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'hr.employee'

    matricule = fields.Char(string="Matricule", required=True)
    emploi = fields.Char(string="Emploi")
    service = fields.Char(string="Service")
    convention_collective = fields.Char(string="Convention Collective")
    categorie = fields.Char(string="Catégorie")
    echelon = fields.Char(string="Échelon")
    categorie_personnel = fields.Char(string="Catégorie de personnel")
    numero_dn = fields.Char(string="N° D.N")
