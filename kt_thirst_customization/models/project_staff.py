from odoo import models,fields,api

class ProjectStaff(models.Model):
    _name = 'project.staff'

    project_id = fields.Many2one('project.project',string="Project")
    employee_id = fields.Many2one('hr.employee',string="Employee")
    job_title_id = fields.Many2one('hr.job',string="Job Title")
    role = fields.Char('Role',related="job_title_id.name")
    rate = fields.Float('Rate',readonly="1",related="job_title_id.rate")
    work_location = fields.Char('Work Location',readonly="1",related="employee_id.work_location")
    work_email = fields.Char('Work Email',readonly="1",related="employee_id.work_email")
    mobile_phone = fields.Char('Work Mobile',readonly="1",related="employee_id.mobile_phone")
    work_phone = fields.Char('Work Phone',readonly="1",related="employee_id.work_phone")
    image_medium = fields.Binary('Image',related="employee_id.image_medium")
    project_setup_id = fields.Many2one('project.project',string="Project")
    project_event_id = fields.Many2one('project.project',string="Project")
    project_breakdown_id = fields.Many2one('project.project',string="Project")
    quoted_hrs = fields.Float('Quoted Hours')
    billable_hrs = fields.Float('Billable Hours')
    non_billable_hrs = fields.Float('Non-Billable Hours')
    time_started = fields.Datetime('Time Started')
    time_ended = fields.Datetime('Time Ended')
    uniform_size = fields.Selection([('s','S'),('m','M'),('l','L'),('xl','XL'),('2xl','2XL'),('3xl','3XL')],string="Uniform Size")
    uniform_ids = fields.Many2many('staff.uniform','staff_uniform_rel','staff_id','uniform_id',string="Uniform")
    other = fields.Char('Other')
    uniform_out = fields.Boolean('Uniform Out')
    uniform_in = fields.Boolean('Uniform In')
    total_hrs = fields.Float(compute='_get_total_hrs',string="Total Hours")
    total_cost = fields.Float(compute='_get_total_cost',string="Total Cost")


    '''@api.multi
    @api.onchange('job_title_id')
    def onchange_jobtitle_id(self):
	self.rate = self.job_title_id and self.job_title_id.rate or False

    @api.multi
    @api.onchange('employee_id')
    def onchange_employee_id(self):
        #self.work_location = self.employee_id and self.employee_id.work_location or False
        #self.work_email = self.employee_id and self.employee_id.work_email or False
	#self.mobile_phone = self.employee_id and self.employee_id.mobile_phone or False
	#self.work_phone = self.employee_id and self.employee_id.work_phone or False
	#self.image_medium = self.employee_id and self.employee_id.image_medium or False
	if self.employee_id:
	    self.work_location = self.employee_id.work_location
            self.work_email = self.employee_id.work_email
            self.mobile_phone = self.employee_id.mobile_phone 
            self.work_phone =  self.employee_id.work_phone 
            self.image_medium = self.employee_id.image_medium 	
    
    @api.multi
    def unlink(self):
	return super(ProjectStaff, self).unlink()'''

    @api.multi
    @api.onchange('employee_id')
    def onchange_employee_id(self):
        self.job_title_id = self.employee_id and self.employee_id.job_id.id or False

    @api.one
    @api.depends('billable_hrs','non_billable_hrs')
    def _get_total_hrs(self):
        self.total_hrs = self.billable_hrs + self.non_billable_hrs

    @api.one
    @api.depends('total_hrs','rate')
    def _get_total_cost(self):
        self.total_cost = self.total_hrs * self.rate


class StaffUniform(models.Model):
    _name = 'staff.uniform'

    name = fields.Char('Staff Uniform')

class Employee(models.Model):
    _inherit = 'hr.employee'


    #project_id = fields.Many2one('project.project','Project')
    emp_no = fields.Char('Employee No')
    partner_id = fields.Many2one('res.partner',string="Related Partner")


    @api.model
    def create(self,vals):
        next_seq_no = self.env['ir.sequence'].next_by_code('hr.employee') or '/'
        vals['emp_no'] = next_seq_no
        #obj = super(Employee,self).create(vals)
        #creating partner
        job_position = False
        if vals.get('job_id'):
            job_position = self.env['hr.job'].browse(vals.get('job_id')).name
        partner_values = {'name':vals.get('name'),'mobile':vals.get('mobile_phone'),'email':vals.get('work_email'),'phone':vals.get('work_phone'),'function':job_position,'ref':next_seq_no }
        partner_obj = self.env['res.partner'].create(partner_values)

        vals['partner_id'] = partner_obj.id

        return super(Employee,self).create(vals)
    
