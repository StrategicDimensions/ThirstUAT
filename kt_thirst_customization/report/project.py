from odoo import fields,models,api


class ProjectProject(models.Model):
    _inherit = 'project.project'

    @api.multi
    def get_total_vals(self):
        tot_qtd_hrs, tot_bill_hrs, tot_non_bill_hrs, tot_hrs, tot_cost = 0.0,0.0,0.0,0.0,0.0

        for staff in self.setup_staff_ids:
            tot_qtd_hrs += staff.quoted_hrs
            tot_bill_hrs += staff.billable_hrs
            tot_non_bill_hrs += staff.non_billable_hrs
            tot_hrs += staff.total_hrs
            tot_cost += staff.total_cost

        for staff in self.event_staff_ids:
            tot_qtd_hrs += staff.quoted_hrs
            tot_bill_hrs += staff.billable_hrs
            tot_non_bill_hrs += staff.non_billable_hrs
            tot_hrs += staff.total_hrs
            tot_cost += staff.total_cost

        for staff in self.breakdown_staff_ids:
            tot_qtd_hrs += staff.quoted_hrs
            tot_bill_hrs += staff.billable_hrs
            tot_non_bill_hrs += staff.non_billable_hrs
            tot_hrs += staff.total_hrs
            tot_cost += staff.total_cost

        return [{ 'tot_qtd_hrs':tot_qtd_hrs, 'tot_bill_hrs':tot_bill_hrs, 'tot_non_bill_hrs':tot_non_bill_hrs,
                  'tot_hrs':tot_hrs, 'tot_cost':tot_cost }]

