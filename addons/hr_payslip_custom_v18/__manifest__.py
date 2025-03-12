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
        # 'data/hr_payslip_supp_data.xml',
    ],
    'assets': {
        'web.assets_backend': [
            '/hr_payslip_custom/static/src/js/payslip_list.js',
        ],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
