from odoo import models,fields,api

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    #_time_hr_selection = lambda self, *args, **kwargs: self._get_hr_range(*args, **kwargs)

    near_thirst_dep = fields.Selection([('captown','Cape Town'),('durban','Durban'),('johannesburg','Johannesburg')],string="Nearest Thirst Department*")
    function_type = fields.Selection([('corporate','Corporate'),('private','Private'),('wedding','Wedding'),('birthday','Birthday'),('product_launch','Product Launch'),('activation','Activation')],string="Function Type")
    required_services_ids = fields.Many2many('service.required','ser_req_rel','crm_id','ser_req_id','Required Services')
    bar_style = fields.Selection([('exp_bar','Experience Bar'),('pl','PL'),('special_events_bar','Special Events Bar'),('festival_bars','Festival Bars'),('circular','Circular')],string="Bar Style")
    function_venue = fields.Char('Function Venue')
    function_start_time = fields.Datetime('Function Start Date & Time')
    function_end_time = fields.Datetime('Function End Date & Time')
    no_of_guests = fields.Integer('Number of Guests')
    budget_amt = fields.Float('Budget')
    #start_time = fields.Float('Function Time')
    fun_start_date = fields.Date('Function Start Date')
    #fun_start_time_hr = fields.Selection(_time_hr_selection,'Function Start Time (HH)')
    fun_end_date = fields.Date('Function End Date')


    '''@api.model
    def _get_hr_range(self):
	list1 = [('01','01'),('02','02'),('03','03'),('04','04'),('05','05'),('06','06'),('07','07'),('08','08'),('09','09')]
	list2 = [(str(num), str(num)) for num in range(10,25)]
        return list1+list2'''
    
    @api.multi
    def change_salesperson(self,lead_ids):
	for lead_id in lead_ids:
	    self.browse(lead_id).user_id = False
	return True
