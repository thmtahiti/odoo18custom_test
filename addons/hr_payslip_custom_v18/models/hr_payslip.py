
from odoo import models, fields, api

class PayslipCustom(models.Model):
    _name = 'hr.payslip.custom'
    _description = 'Bulletin de Paie Personnalisé'

    name = fields.Char(string="Nom", required=True, default="Bulletin de Paie")
    employee_id = fields.Many2one('hr.employee', string='Employé', required=True)
    base_salary = fields.Float(string='Salaire de base', required=True)
    line_ids = fields.One2many('hr.payslip.line', 'payslip_id', string='Lignes de paie')
    line_supp_ids = fields.One2many('hr.payslip.supp', 'payslip_id', string='Lignes de supp')
    line_conge_ids = fields.One2many('hr.payslip.cong', 'payslip_id', string='Lignes de cong')
    total_salary = fields.Float(string='Salaire total', compute='_compute_total_salary', store=True)
    primeanciennete = fields.Float(string='Prime ancienneté', required=True, default=0.0)

    @api.depends('line_ids.amount')
    def _compute_total_salary(self):
        for record in self:
            record.total_salary = record.base_salary + sum(record.line_ids.mapped('amount'))

class PayslipSupp(models.Model):
    _name = 'hr.payslip.supp'
    _description = 'Gestion des heures supp'

    payslip_id = fields.Many2one('hr.payslip.custom', string='Bulletin de Paie', ondelete="cascade")
    name = fields.Char(string='Libellé', required=True)
    salaire_base = fields.Float(string="Salaire de base", related="payslip_id.base_salary", store=True)
    taux_horaire = fields.Float(string='Taux Horaire', compute='_compute_taux_horaire', store=True)
    pourcentage = fields.Float(string='Pourcentage', default=0.0)
    montant_horaire = fields.Float(string='Montant Horaire', compute='_compute_montant_horaire', store=True)
    nbrs = fields.Float(string='Nombre', default=0.0)
    total = fields.Float(string='Total', compute='_compute_amount', store=True)

    @api.depends('salaire_base', 'nbrs')
    def _compute_taux_horaire(self):
        """ Calcule le taux horaire en fonction du salaire de base et du nombre d'heures travaillées """
        for record in self:
            record.taux_horaire = (record.salaire_base / 169) if record.salaire_base else 0.0

    @api.depends('taux_horaire', 'pourcentage')
    def _compute_montant_horaire(self):
        """ Applique le pourcentage au taux horaire pour obtenir le montant horaire avec majoration """
        for record in self:
            record.montant_horaire = record.taux_horaire * (1 + record.pourcentage / 100)

    @api.depends('nbrs', 'montant_horaire')
    def _compute_amount(self):
        """ Calcule le total en fonction du nombre d'heures et du montant horaire """
        for record in self:
            record.total = record.nbrs * record.montant_horaire

class PayslipCong(models.Model):
    _name = 'hr.payslip.cong'
    _description = 'Gestion des congés'

    payslip_id = fields.Many2one('hr.payslip.custom', string='Bulletin de Paie', ondelete="cascade")
    name = fields.Char(string='Libellé', required=True)
    motif = fields.Char(string='Motif', required=True)
    nbrs = fields.Float(string='Nombre', default=0.0)
    dates = fields.Char(string='Dates', required=True)

class PayslipLine(models.Model):
    _name = 'hr.payslip.line'
    _description = 'Ligne de Bulletin de Paie'

    payslip_id = fields.Many2one('hr.payslip.custom', string='Bulletin de Paie', required=True, ondelete="cascade")
    name = fields.Char(string='Libellé', required=True)
    base = fields.Float(string='Base de calcul', required=True, default=0.0)
    rate = fields.Float(string='Taux (%)', required=True, default=0.0)
    amount = fields.Float(string='Montant', compute='_compute_amount', store=True)

    @api.depends('base', 'rate')
    def _compute_amount(self):
        for record in self:
            record.amount = record.base + (record.base * record.rate / 100)


