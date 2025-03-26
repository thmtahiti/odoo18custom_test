{
    'name': 'Bulletin de Paie Personnalisé',
    'sequence': 1,
    'version': '1.0',
    'summary': 'Gestion des bulletins de paie avec calcul automatique',
    'description': 'Module Odoo pour gérer les bulletins de paie basés sur un modèle Excel',
    'author': 'Vaikea Solution',
    'depends': ['hr'],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_payslip_views.xml',
        'views/report_payslip.xml',
        'views/hr_society.xml',
        'views/hr_employee.xml',

    ],
    'assets': {
        'web.assets_backend': [

        ],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
