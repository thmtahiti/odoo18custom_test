import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)

class PayslipCustom(models.Model):
    _name = 'hr.payslip.custom'
    _description = 'Bulletin de Paie Personnalisé'

    name = fields.Char(string="Nom", required=True, default="Bulletin de Paie")
    employee_id = fields.Many2one('hr.employee', string='Employé', required=True)
    base_salary = fields.Float(string='Salaire de base', required=True)
    primeanciennete = fields.Float(string='Prime ancienneté', required=True, default=0.0)
    primeexceptionnelle = fields.Float(string='Prime exceptionnelle', required=True, default=0.0)


    """ LIGNE """
    line_supp_ids = fields.One2many('hr.payslip.supp', 'payslip_id', string='Lignes de supp')
    line_conge_ids = fields.One2many('hr.payslip.cong', 'payslip_id', string='Lignes de cong')
    line_salariale_ids = fields.One2many('hr.payslip.cotisation', 'payslip_id', string='Lignes de cotisation salariale')

    """ CHAMP CALCUL """
    soldsoumiscotisation = fields.Float(string='Total soumis à cotisation', compute='_compute_soldsoumiscotisation', store=True)
    taux_horaire = fields.Float(string='Taux Horaire', compute='_compute_taux_horaire', store=True)
    sum_total = fields.Float(string='Total heures supp, congés, et primes', compute='_compute_sum_amount', store=True)
    cst = fields.Float(string='CST', compute='_compute_impot', store=True)
    sum_total_cotisation_salariale = fields.Float(string='Total des cotisations', compute='_compute_cotisation_salariale', store=True)
    salaire_net = fields.Float(string='Salaire NET après cotisations', compute='_compute_salaire_net', store=True)

    """ TOTAUX """
    @api.depends('line_supp_ids.total', 'sum_total')
    def _compute_sum_amount(self):
        """ Calcule du total des heures supp, congés et primes """
        for record in self:
            record.sum_total = sum(record.line_supp_ids.mapped('total'))

    @api.depends('line_supp_ids.total', 'base_salary', 'primeanciennete', 'primeexceptionnelle')
    def _compute_soldsoumiscotisation(self):
        """ Calcule du sold soumis à la cotisation """
        for record in self:
            record.soldsoumiscotisation = record.sum_total + record.base_salary + record.primeanciennete + record.primeexceptionnelle

    @api.depends('line_salariale_ids.montant_cotis')
    def _compute_cotisation_salariale(self):
        """ Calcule du sold costisation salariale """
        for record in self:
            cotisations = sum(record.line_salariale_ids.mapped('montant_cotis'))
            record.sum_total_cotisation_salariale = cotisations

    @api.depends('salaire_net','base_salary')
    def _compute_salaire_net(self):
        """ Calcule du sold soumis à la cotisation """
        for record in self:
            record.salaire_net = record.soldsoumiscotisation - record.sum_total_cotisation_salariale


    """ VALEUR BASE """
    @api.depends('base_salary')
    def _compute_taux_horaire(self):
        """ Calcule le taux horaire en fonction du salaire de base et du nombre d'heures travaillées """
        for record in self:
            record.taux_horaire = (record.base_salary / 169) if record.base_salary else 0.0

    """ CST """
    @api.depends('soldsoumiscotisation')
    def _compute_impot(self):
        """ Calcule l'impôt en fonction des tranches et des taux """
        tranches = [
            (150000, 0.005), (250000, 0.03), (400000, 0.05),
            (700000, 0.09), (1000000, 0.11), (1250000, 0.15),
            (1500000, 0.18), (1750000, 0.21), (2000000, 0.24),
            (2500000, 0.26), (float('inf'), 0.28)
        ]

        for record in self:
            salaire = record.soldsoumiscotisation
            cst = 0

            for i, (limit, taux) in enumerate(tranches):
                if salaire <= limit:
                    cst += (salaire - (tranches[i - 1][0] if i > 0 else 0)) * taux
                    break
                else:
                    cst += (limit - (tranches[i - 1][0] if i > 0 else 0)) * taux

            record.cst = cst

""" HEURE SUPP """
class PayslipSupp(models.Model):
    _name = 'hr.payslip.supp'
    _description = 'Gestion des heures supp'

    payslip_id = fields.Many2one('hr.payslip.custom', string='Bulletin de Paie', ondelete="cascade")
    name = fields.Char(string='Libellé', required=True)
    salaire_base = fields.Float(string="Salaire de base", related="payslip_id.base_salary", store=True)
    taux_horaire = fields.Float(string='Taux Horaire', related="payslip_id.taux_horaire", store=True)
    pourcentage = fields.Float(string='Pourcentage', default=0.0)
    montant_horaire = fields.Float(string='Montant Horaire', compute='_compute_montant_horaire', store=True)
    nbrs = fields.Float(string='Nombre', default=0.0)
    total = fields.Float(string='Total', compute='_compute_amount', store=True)

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

""" CONGE """
class PayslipCong(models.Model):
    _name = 'hr.payslip.cong'
    _description = 'Gestion des congés'

    payslip_id = fields.Many2one('hr.payslip.custom', string='Bulletin de Paie', ondelete="cascade")
    name = fields.Char(string='Libellé', required=True)
    motif = fields.Char(string='Motif')
    nbrs = fields.Float(string='Nombre', default=0.0)
    dates = fields.Char(string='Dates')

""" COTISATION SALARIALE """
class HrPayslipCotisation(models.Model):
    _name = 'hr.payslip.cotisation'
    _description = 'Gestion des cotisations sociales'

    payslip_id = fields.Many2one('hr.payslip.custom', string="Bulletin de paie", ondelete="cascade")
    name = fields.Char(string="Libellé", required=True)
    base = fields.Float(string="Base", compute="_compute_base", store=True)
    taux = fields.Float(string="Taux (%)", required=True)
    montant_cotis = fields.Float(string="Montant cotisé", compute="_compute_montant_cotis", store=True)

    salaire_brut = fields.Float(string="Salaire Brut", related="payslip_id.soldsoumiscotisation", store=True)

    @api.depends('salaire_brut','taux')
    def _compute_base(self):
        """ Calcule la base de cotisation en fonction des règles définies """
        for record in self:
            if record.name == "Retraite tranche A" or record.name == "Fonds Sociale Retraite":
                record.base = min(record.salaire_brut, 264000)
            elif record.name == "Retraite tranche B":
                record.base = max(record.salaire_brut - 264000, 0)
            elif record.name == "Assurance Maladie":
                record.base = record.salaire_brut
            else:
                record.base = 0  # Cas par défaut

    @api.depends('base', 'taux')
    def _compute_montant_cotis(self):
        """ Calcule le montant de la cotisation en fonction de la base et du taux """
        for record in self:
            record.montant_cotis = record.base * (record.taux / 100)


class HrPayroll(models.Model):
    _name = 'hr.payslip.payroll'
    _description = 'Calcule des charges patronales'

    payslip_id = fields.Many2one('hr.payslip.custom', string='Bulletin de Paie', ondelete="cascade")
    salaire_brut = fields.Float(related='payslip_id.soldsoumiscotisation')

    base_fsre = fields.Float(string='FSRE', compute='_compute_cotisations')
    base_at = fields.Float(string='AT', compute='_compute_cotisations')
    base_am = fields.Float(string='AM', compute='_compute_cotisations')
    base_ret_a = fields.Float(string='RET A', compute='_compute_cotisations')
    base_fpc = fields.Float(string='FPC', compute='_compute_cotisations')
    base_fsr = fields.Float(string='Fonds Sociale Retraite', compute='_compute_cotisations')
    base_fsr_exception = fields.Float(string='FSR Exception', compute='_compute_cotisations')
    base_prest_fam = fields.Float(string='Prestations Familiales', compute='_compute_cotisations')
    base_ret_tranche_b = fields.Float(string='Retraite Tranche B', compute='_compute_cotisations')
    base_avts = fields.Float(string='A.V.T.S.', compute='_compute_cotisations')

    montant_at = fields.Float(string='Montant AT', compute='_compute_cotisations')
    montant_am = fields.Float(string='Montant AM', compute='_compute_cotisations')
    montant_ret_a = fields.Float(string='Montant RET A', compute='_compute_cotisations')
    montant_fpc = fields.Float(string='Montant FPC', compute='_compute_cotisations')
    montant_fsr = fields.Float(string='Montant Fonds Sociale Retraite', compute='_compute_cotisations')
    montant_fsr_exception = fields.Float(string='Montant FSR Exception', compute='_compute_cotisations')
    montant_prest_fam = fields.Float(string='Montant Prestations Familiales', compute='_compute_cotisations')
    montant_ret_tranche_b = fields.Float(string='Montant Retraite Tranche B', compute='_compute_cotisations')
    montant_avts = fields.Float(string='Montant A.V.T.S.', compute='_compute_cotisations')

    total_cotisations = fields.Float(string='Total Cotisations', compute='_compute_cotisations')

    taux = {
        'at': 0.0048,
        'am': 0.0996,
        'ret_a': 0.1569,
        'fpc': 0.005,
        'fsr': 0.0096,
        'fsr_exception': 0.01,
        'prest_fam': 0.0333,
        'ret_tranche_b': 0.1162,
        'avts': 0.00  # Ce taux semble être variable selon "F58", à ajuster
    }

    @api.depends('salaire_brut')
    def _compute_cotisations(self):
        for record in self:
            salaire = record.salaire_brut

            record.base_fsre = salaire
            record.base_at = salaire
            record.base_am = salaire
            record.base_ret_a = salaire
            record.base_fpc = salaire
            record.base_fsr = salaire
            record.base_fsr_exception = salaire - 100000 if salaire > 100000 else 0
            record.base_prest_fam = salaire
            record.base_ret_tranche_b = salaire - 264000 if salaire > 264000 else 0
            record.base_avts = salaire if salaire > 195000 else 0

            record.montant_at = record.base_at * self.taux['at']
            record.montant_am = record.base_am * self.taux['am']
            record.montant_ret_a = record.base_ret_a * self.taux['ret_a']
            record.montant_fpc = record.base_fpc * self.taux['fpc']
            record.montant_fsr = record.base_fsr * self.taux['fsr']
            record.montant_fsr_exception = record.base_fsr_exception * self.taux['fsr_exception']
            record.montant_prest_fam = record.base_prest_fam * self.taux['prest_fam']
            record.montant_ret_tranche_b = record.base_ret_tranche_b * self.taux['ret_tranche_b']
            record.montant_avts = record.base_avts * self.taux['avts']

            record.total_cotisations = sum([
                record.montant_at, record.montant_am, record.montant_ret_a, record.montant_fpc,
                record.montant_fsr, record.montant_fsr_exception, record.montant_prest_fam,
                record.montant_ret_tranche_b, record.montant_avts
            ])