# -*- coding: utf-8 -*-


from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare, float_is_zero


class HrPayslip(models.Model):
    _inherit = "hr.payslip"


    def action_payslip_done(self):
        aux = self.payslip_run_id
        self.payslip_run_id = False
        res = super(HrPayslip, self).action_payslip_done()
        payslips_to_post = self.filtered(lambda slip: slip.move_id)

        for slip in payslips_to_post:
            for move_line in slip.move_id.line_ids:
                partner = slip.employee_id.address_home_id
                slip_line = self.env['hr.payslip.line'].search([
                    ('slip_id', '=', slip.id),
                    ('employee_id', '=', slip.employee_id.id),
                    ('company_id', '=', self.env.company.id),
                    ('name', '=', move_line.name),
                    ], limit=1)

                if slip_line:
                    partner = slip_line.get_partner(slip_line.salary_rule_id, slip.employee_id)

                move_line.write({'partner_id': partner.id})
        self.payslip_run_id = aux
        return res

    def compute_sheet(self):
        result = super(HrPayslip, self).compute_sheet()
        for line in self.line_ids:
            if line.total == 0:
                line.unlink()
        return result

class HrPayslipLine(models.Model):
    _inherit = "hr.payslip.line"


    def get_partner(self, rule, employee):
        partner = employee.address_home_id
        if rule:
            if rule.partner_type == 'eps':
                partner = employee.eps_id
            elif rule.partner_type == 'afp':
                partner = employee.afp_id
            elif rule.partner_type == 'arl':
                partner = employee.arl_id
            #elif rule.partner_type == 'pre_medicine':
                #partner = employee.prepaid_medicine_id
            #elif rule.partner_type == 'pre_medicine2':
                #partner = employee.prepaid_medicine2_id
            elif rule.partner_type == 'afc':
                partner = employee.afc_id
            elif rule.partner_type == 'compensation':
                partner = employee.compensation_box
            elif rule.partner_type == 'voluntary':
                partner = employee.voluntary_contribution_id
            #elif rule.partner_type == 'voluntary2':
                #partner = employee.voluntary_contribution2_id

        return partner
