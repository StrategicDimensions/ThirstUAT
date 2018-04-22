from odoo import fields,models,api



class HrJob(models.Model):
    _inherit = 'hr.job'

    rate = fields.Float(string="Rate")



