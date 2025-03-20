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

    def print_payslip_report(self):
        return self.env.ref('hr_payslip_custom_v18.report_payslip_template').report_action(self)

    """ LIGNE """
    line_supp_ids = fields.One2many('hr.payslip.supp', 'payslip_id', string='Lignes de supp')
    line_conge_ids = fields.One2many('hr.payslip.cong', 'payslip_id', string='Lignes de cong')
    line_salariale_ids = fields.One2many('hr.payslip.cotisation', 'payslip_id', string='Lignes de cotisation salariale')
    line_patronales_ids = fields.One2many('hr.payslip.payroll', 'payslip_id', string='Lignes de cotisation patronales')


    """ CHAMP CALCUL """
    soldsoumiscotisation = fields.Float(string='Total soumis à cotisation', compute='_compute_soldsoumiscotisation', store=True)
    taux_horaire = fields.Float(string='Taux Horaire', compute='_compute_taux_horaire', store=True)
    sum_total = fields.Float(string='Total heures supp, congés, et primes', compute='_compute_sum_amount', store=True)
    cst = fields.Float(string='CST', compute='_compute_impot', store=True)
    total_cotisation_salariales = fields.Float(string='Charges Salariales', compute='_compute_cotisation_salariale', store=True)
    salaire_net = fields.Float(string='Salaire NET après cotisations', compute='_compute_salaire_net', store=True)
    total_charges_patronales = fields.Float(string='Charges patronales', compute='_compute_total_patronales', store=True)

    """ TOTAUX """

    @api.model
    def create(self, vals):
        payslip = super(PayslipCustom, self).create(vals)

        # Ajout des lignes de cotisations patronales
        taux_defauts = [
            {"libelle": "AT", "taux": 0.48},
            {"libelle": "AM", "taux": 9.96},
            {"libelle": "Retraite A", "taux": 15.69},
            {"libelle": "FPC", "taux": 0.5},
            {"libelle": "Fonds Sociale Retraite", "taux": 0.96},
            {"libelle": "FSR Exception", "taux": 1.0},
            {"libelle": "Prestations Familiales", "taux": 0.0},
            {"libelle": "Retraite Tranche B", "taux": 11.62},
            {"libelle": "A.V.T.S.", "taux": 0.00},
        ]

        for taux in taux_defauts:
            self.env['hr.payslip.payroll'].create({
                'payslip_id': payslip.id,
                'libelle': taux["libelle"],
                'taux': taux["taux"],
            })

        # Ajout des heures supplémentaires par défaut
        heures_supp_defauts = [
            {"name": "Heures supp 40e 47e", "pourcentage": 25.0},
            {"name": "Heures supp Jours Fériés", "pourcentage": 50.0},
            {"name": "Heures supp Dimanche", "pourcentage": 65.0},
            {"name": "Heures supp Nuit", "pourcentage": 100.0},
        ]

        for heure in heures_supp_defauts:
            self.env['hr.payslip.supp'].create({
                'payslip_id': payslip.id,
                'name': heure["name"],
                'pourcentage': heure["pourcentage"],
            })

        # Ajout des congés par défaut
        conges_defauts = [
            {"name": "Arrêt maladie (carence)", "motif": "Maladie"},
            {"name": "Arrêt maladie (nbre jrs et dates)", "motif": "Maladie"},
            {"name": "Congés payés (nbre jrs et dates)", "motif": "Congé"},
            {"name": "Indemnités de congés payés", "motif": "Indemnité"},
        ]

        for conge in conges_defauts:
            self.env['hr.payslip.cong'].create({
                'payslip_id': payslip.id,
                'name': conge["name"],
                'motif': conge["motif"],
            })

        # Ajout des cotisations salariales par défaut
        cotisations_salariales_defauts = [
            {"name": "Retraite tranche A", "taux": 7.84},
            {"name": "Fonds Sociale Retraite", "taux": 0.0},
            {"name": "Retraite tranche B", "taux": 5.81},
            {"name": "Assurance Maladie", "taux": 4.98},
        ]

        for cotisation in cotisations_salariales_defauts:
            self.env['hr.payslip.cotisation'].create({
                'payslip_id': payslip.id,
                'name': cotisation["name"],
                'taux': cotisation["taux"],
            })

        _logger.info(f"Bulletin de paie {payslip.id} créé avec cotisations, heures supplémentaires et congés.")
        return payslip

    @api.onchange('payslip_id.soldsoumiscotisation')
    def _onchange_soldsoumiscotisation(self):
        """ Déclenche le recalcul des cotisations lorsque le salaire change. """
        self._compute_cotisation()

    @api.depends('line_patronales_ids.montant')
    def _compute_total_patronales(self):
        for payslip in self:
            payslip.total_charges_patronales = round(sum(payslip.line_patronales_ids.mapped('montant')))



    @api.depends('line_supp_ids.total', 'sum_total')
    def _compute_sum_amount(self):
        """ Calcule du total des heures supp, congés et primes """
        for record in self:
            record.sum_total = round(sum(record.line_supp_ids.mapped('total')))

    @api.depends('line_supp_ids.total', 'base_salary', 'primeanciennete', 'primeexceptionnelle')
    def _compute_soldsoumiscotisation(self):
        """ Calcule du sold soumis à la cotisation """
        for record in self:
            record.soldsoumiscotisation = round(record.sum_total + record.base_salary + record.primeanciennete + record.primeexceptionnelle)



    @api.depends('line_salariale_ids.montant_cotis')
    def _compute_cotisation_salariale(self):
        """ Calcule du sold costisation salariale """
        for record in self:
            cotisations = round(sum(record.line_salariale_ids.mapped('montant_cotis')))
            record.total_cotisation_salariales = cotisations

    @api.depends('salaire_net','line_supp_ids.total', 'base_salary', 'primeanciennete', 'primeexceptionnelle')
    def _compute_salaire_net(self):
        """ Calcule du sold soumis à la cotisation """
        for record in self:
            record.salaire_net = round(record.soldsoumiscotisation - record.total_cotisation_salariales)


    """ VALEUR BASE """
    @api.depends('base_salary')
    def _compute_taux_horaire(self):
        """ Calcule le taux horaire en fonction du salaire de base et du nombre d'heures travaillées """
        for record in self:
            record.taux_horaire = round((record.base_salary / 169) if record.base_salary else 0.0)

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
            record.montant_horaire = round(record.taux_horaire * (1 + record.pourcentage / 100))

    @api.depends('nbrs', 'montant_horaire')
    def _compute_amount(self):
        """ Calcule le total en fonction du nombre d'heures et du montant horaire """
        for record in self:
            record.total = round(record.nbrs * record.montant_horaire)

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
            elif record.name == "Fonds Sociale Retraite":
                record.base = record.salaire_brut
            else:
                record.base = 0  # Cas par défaut

    @api.depends('base', 'taux')
    def _compute_montant_cotis(self):
        """ Calcule le montant de la cotisation en fonction de la base et du taux """
        for record in self:
            record.montant_cotis = round(record.base * (record.taux / 100))

""" CHARGES PARTRONALES """

class HrPayroll(models.Model):
    _name = 'hr.payslip.payroll'
    _description = 'Calcule des charges patronales'

    payslip_id = fields.Many2one('hr.payslip.custom', string='Bulletin de Paie', ondelete="cascade")
    libelle = fields.Char(string="Libellé de la cotisation", required=True)
    taux = fields.Float(string="Taux (%)", required=True)
    base = fields.Float(string='Base', compute='_compute_cotisation', store=True)
    montant = fields.Float(string='Montant Cotisation', compute='_compute_cotisation', store=True)

    @api.depends('payslip_id.soldsoumiscotisation', 'libelle', 'taux')
    def _compute_cotisation(self):
        """ Calcule la base et le montant des cotisations en fonction du libellé et du taux """
        for record in self:
            salaire = record.payslip_id.soldsoumiscotisation
            libelle = record.libelle.strip().lower()  # Nettoyage et conversion en minuscule

            # Définition des bases selon le libellé
            if "at" in libelle:
                record.base = salaire
            elif "fsr exception" in libelle:
                record.base = max(salaire - 100000, 0)
            elif "assurance maladie" in libelle or "am" in libelle:
                record.base = salaire
            elif "retraite a" in libelle:
                record.base = min(salaire, 264000)
            elif "fonds sociale retraite" in libelle or "fsr" in libelle:
                record.base = min(salaire, 264000)  # Ajout de la règle FSR
            elif "retraite tranche b" in libelle:
                record.base = max(salaire - 264000, 0)
            elif "prestations familiales" in libelle:
                record.base = salaire if salaire < 750000 else 0
            elif "fpc" in libelle:
                record.base = salaire  # Ajout de la règle FPC
            elif "avts" in libelle:
                taux_f58 = record.taux  # Supposition que F58 est le taux stocké
                record.base = salaire * taux_f58 if salaire > 195000 else 0
            else:
                record.base = 0  # Si le libellé ne correspond à rien, la base est 0

            # Calcul du montant de la cotisation
            record.montant = round(record.base * (record.taux / 100))



