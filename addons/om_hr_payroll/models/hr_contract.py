# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class HrContract(models.Model):
    """
    Modèle représentant un contrat d'employé basé sur un visa ou un permis de travail.
    Permet de configurer différentes structures salariales.
    """
    _inherit = 'hr.contract'  # Hérite du modèle de contrat existant dans Odoo
    _description = 'Employee Contract'

    # Référence à la structure salariale associée au contrat
    struct_id = fields.Many2one('hr.payroll.structure', string='Salary Structure')

    # Fréquence de paiement du salaire, avec des options prédéfinies
    schedule_pay = fields.Selection([
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('semi-annually', 'Semi-annually'),
        ('annually', 'Annually'),
        ('weekly', 'Weekly'),
        ('bi-weekly', 'Bi-weekly'),
        ('bi-monthly', 'Bi-monthly'),
    ], string='Scheduled Pay', index=True, default='monthly',
        help="Defines the frequency of the wage payment.")

    # Référence au calendrier de travail de l'employé (obligatoire)
    resource_calendar_id = fields.Many2one(required=True, help="Employee's working schedule.")

    # Différentes allocations monétaires liées au contrat
    hra = fields.Monetary(string='HRA', help="House rent allowance.")
    travel_allowance = fields.Monetary(string="Travel Allowance", help="Travel allowance")
    da = fields.Monetary(string="DA", help="Dearness allowance")
    meal_allowance = fields.Monetary(string="Meal Allowance", help="Meal allowance")
    medical_allowance = fields.Monetary(string="Medical Allowance", help="Medical allowance")
    other_allowance = fields.Monetary(string="Other Allowance", help="Other allowances")

    # Catégorie d'employé associée au contrat, avec une valeur par défaut
    type_id = fields.Many2one('hr.contract.type', string="Employee Category",
                              required=True, help="Employee category",
                              default=lambda self: self.env['hr.contract.type'].search([], limit=1))

    def get_all_structures(self):
        """
        Récupère toutes les structures salariales liées aux contrats donnés.

        @return: Liste des structures triées par hiérarchie et sans doublons
        """
        structures = self.mapped('struct_id')
        if not structures:
            return []
        # Retourne les ID des structures parentales sans doublons
        return list(set(structures._get_parent_structure().ids))

    def get_attribute(self, code, attribute):
        """
        Récupère une valeur d'attribut spécifique à partir d'un code donné.

        @param code: Code de l'attribut
        @param attribute: Nom de l'attribut à récupérer
        @return: Valeur de l'attribut
        """
        return self.env['hr.contract.advantage.template'].search([('code', '=', code)], limit=1)[attribute]

    def set_attribute_value(self, code, active):
        """
        Met à jour la valeur d'un attribut spécifique pour le contrat.

        @param code: Code de l'attribut à modifier
        @param active: Booléen indiquant si l'avantage est activé ou non
        """
        for contract in self:
            if active:
                # Récupère la valeur par défaut de l'avantage depuis le template
                value = self.env['hr.contract.advantage.template'].search([('code', '=', code)], limit=1).default_value
                contract[code] = value
            else:
                contract[code] = 0.0


class HrContractAdvantageTemplate(models.Model):
    """
    Modèle représentant les avantages liés aux contrats d'employés.
    Permet de définir des limites et une valeur par défaut pour chaque avantage.
    """
    _name = 'hr.contract.advantage.template'
    _description = "Employee's Advantage on Contract"

    name = fields.Char('Name', required=True)  # Nom de l'avantage
    code = fields.Char('Code', required=True)  # Code unique de l'avantage
    lower_bound = fields.Float('Lower Bound', help="Lower bound authorized by the employer for this advantage")
    upper_bound = fields.Float('Upper Bound', help="Upper bound authorized by the employer for this advantage")
    default_value = fields.Float('Default value for this advantage')  # Valeur par défaut de l'avantage
