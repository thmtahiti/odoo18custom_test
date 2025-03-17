from odoo import models, api
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO


class PayslipReport(models.AbstractModel):
    _name = 'report.hr_payslip_custom.report_payslip'
    _description = 'Rapport Bulletin de Paie'

    @api.model
    def _get_report_values(self, docids, data=None):
        payslips = self.env['hr.payslip.custom'].browse(docids)
        return {'docs': payslips}

    def generate_pdf(self, payslip):
        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=A4)
        pdf.setTitle(f"Bulletin de Paie - {payslip.employee_id.name}")

        # En-tête
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(200, 800, "Bulletin de Paie")
        pdf.setFont("Helvetica", 10)
        pdf.drawString(50, 780, f"Nom: {payslip.employee_id.name}")
        pdf.drawString(50, 765, f"Poste: {payslip.employee_id.job_id.name}")
        pdf.drawString(50, 750, f"Période: {payslip.create_date.strftime('%Y-%m')}")

        # Détails du salaire
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(50, 720, "Détails du salaire")
        pdf.setFont("Helvetica", 10)
        pdf.drawString(50, 700, f"Salaire de base: {payslip.base_salary:.2f} EUR")
        pdf.drawString(50, 685, f"Prime ancienneté: {payslip.primeanciennete:.2f} EUR")
        pdf.drawString(50, 670, f"Prime exceptionnelle: {payslip.primeexceptionnelle:.2f} EUR")
        pdf.drawString(50, 655, f"Total soumis à cotisation: {payslip.soldsoumiscotisation:.2f} EUR")

        # Heures supplémentaires
        y = 630
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(50, y, "Heures supplémentaires")
        pdf.setFont("Helvetica", 10)
        for line in payslip.line_supp_ids:
            y -= 15
            pdf.drawString(50, y, f"{line.name}: {line.nbrs}h à {line.pourcentage}% => {line.total:.2f} EUR")

        # Cotisations salariales
        y -= 30
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(50, y, "Cotisations Salariales")
        pdf.setFont("Helvetica", 10)
        for line in payslip.line_salariale_ids:
            y -= 15
            pdf.drawString(50, y, f"{line.name}: {line.montant_cotis:.2f} EUR")

        y -= 30
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(50, y, "Cotisations Patronales")
        pdf.setFont("Helvetica", 10)
        for line in payslip.line_patronales_ids:
            y -= 15
            pdf.drawString(50, y, f"{line.libelle}: {line.montant:.2f} EUR")

        # Résumé
        y -= 40
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(50, y, "Récapitulatif")
        pdf.setFont("Helvetica", 10)
        pdf.drawString(50, y - 15, f"Total charges salariales: {payslip.total_cotisation_salariales:.2f} EUR")
        pdf.drawString(50, y - 30, f"Total charges patronales: {payslip.total_charges_patronales:.2f} EUR")
        pdf.drawString(50, y - 45, f"Salaire Net: {payslip.salaire_net:.2f} EUR")
        pdf.drawString(50, y - 60, f"CST: {payslip.cst:.2f} EUR")

        pdf.showPage()
        pdf.save()
        buffer.seek(0)
        return buffer.getvalue()

    def _render_qweb_pdf(self, docids, data=None):
        payslips = self.env['hr.payslip.custom'].browse(docids)
        return [(payslip.id, self.generate_pdf(payslip)) for payslip in payslips]
