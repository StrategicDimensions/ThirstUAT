from odoo import models,fields,api,osv
from odoo.exceptions import RedirectWarning, UserError, ValidationError
import urllib
#Need to install below package
import html2text
from datetime import datetime


#Raaj
class ResPartner(models.Model):
	_inherit = 'res.partner' 
	_sql_constraints = [('vat_no_uniq', 'UNIQUE (vat_no)',  'You can not have two users with the same Vat Number !')]

class my_form(models.Model):
        _name = 'my.form'
	select_sms_template = fields.Many2one('sms.template','Select SMS Template',required=True)
	## Raaj
	sms_template_body = fields.Text('SMS Template Body')

	#Raaj
	@api.onchange('select_sms_template')
	def onchange_sms_template(self):
		sms_template = self.select_sms_template
		if sms_template:
			self.sms_template_body = sms_template.body_html or ''
		else:
			self.sms_template_body = ''

        def send_sms_to_lead(self):
		lead_id = self._context['active_id']
		if lead_id:
			mobile = self.env['crm.lead'].browse(lead_id).mobile
                if not mobile:
			raise UserError('Please capture mobile number for Lead to send SMS.')

		if mobile:
			sms_template_id = self.select_sms_template
			if sms_template_id:
		        	gateway = self.env['sms.smsclient'].search([])
				body = self.env['mail.template'].render_template(sms_template_id.body_html,'project.project',self.id)
				url = gateway.url
			        name = url
			        ref = ''
			        if gateway.method == 'http':
			               prms = {}
			               for p in gateway.property_ids:
			                   if p.type == 'user':
			                       prms[p.name] = p.value
			                   elif p.type == 'password':
			                       prms[p.name] = p.value
			                   elif p.type == 'to':
			                       prms[p.name] = mobile
			                   elif p.type == 'sender':
			                       prms[p.name]= p.value
			                   elif p.type == 'sms':
			                        prms[p.name] = body
			                   elif p.type == 'extra':
			                        prms[p.name] = p.value
				       params = urllib.urlencode(prms)
			               name = url + "?" + params
			               queue_obj = self.env['sms.smsclient.queue']
			               values = {
                        		   'name': name,
		                           'gateway_id':gateway.id,
                		           'state': 'draft',
		                           'mobile': mobile,
                		           'msg':html2text.html2text(self.sms_template_body) or '' #body #Raaj
		                         }
			               queue_obj.sudo().create(values)
		self.env['crm.lead'].browse(lead_id).message_post(body=(str(html2text.html2text(self.sms_template_body))), context=None)


class staff_sms(models.Model):
        _name = 'staff.sms'
        select_sms_template = fields.Many2one('sms.template','Select SMS Template')
        ## Raaj
        sms_template_body = fields.Text('SMS Template Body')

        #Raaj
        @api.onchange('select_sms_template')
        def onchange_sms_template(self):
                sms_template = self.select_sms_template
                if sms_template:
                        self.sms_template_body = sms_template.body_html or ''
                else:
                        self.sms_template_body = ''

	@api.multi
        def send_sms_to_staff(self):
                project_id = self._context['active_id']		
                if project_id:
			project_obj = self.env['project.project'].browse(project_id)
                        mobile = project_obj.user_id and project_obj.user_id.partner_id.mobile or False
                if not mobile:
                        raise UserError('Please configure mobile number for Project Manager to send SMS.')
    
                if mobile:
		    self.send_sms(self.select_sms_template.id,mobile)
		for staff in project_obj.staffing_ids:
		    if staff.mobile_phone:
			self.send_sms(self.select_sms_template.id,staff.mobile_phone)
	
	def send_sms(self,sms_template_id,mobile):
	        if sms_template_id and mobile:	    
                        sms_template_obj = self.env['sms.template'].browse(sms_template_id)
                        if sms_template_obj:
                                gateway = self.env['sms.smsclient'].search([])
                                body = self.env['mail.template'].render_template(sms_template_obj.body_html,'staff.sms',self.id)
                                url = gateway.url
                                name = url
                                ref = ''
                                if gateway.method == 'http':
                                       prms = {}
                                       for p in gateway.property_ids:
                                           if p.type == 'user':
                                               prms[p.name] = p.value
                                           elif p.type == 'password':
                                               prms[p.name] = p.value
                                           elif p.type == 'to':
                                               prms[p.name] = mobile
                                           elif p.type == 'sender':
                                               prms[p.name]= p.value
                                           elif p.type == 'sms':
                                                prms[p.name] = body
                                           elif p.type == 'extra':
                                                prms[p.name] = p.value
                                       params = urllib.urlencode(prms)
                                       name = url + "?" + params
                                       queue_obj = self.env['sms.smsclient.queue']
                                       values = {
                                           'name': name,
                                           'gateway_id':gateway.id,
                                           'state': 'draft',
                                           'mobile': mobile,
                                           'msg':html2text.html2text(self.sms_template_body) or '' #body #Raaj
                                         }
                                       obj_create = queue_obj.sudo().create(values)
				



class CrmLead(models.Model):

	_inherit = 'crm.lead'

	def open_myform(self):
		view_id = self.env['ir.model.data'].get_object_reference('kt_thirst_customization', 'send_sms_to_lead_form')
                return {
                                        'name':("Send SMS to Lead"),#Name You want to display on wizard
                                        'view_mode': 'form',
                                        'view_id': view_id[1],
                                        'view_type': 'form',
                                        'res_model': 'my.form',# With . Example sale.order
                                        'type': 'ir.actions.act_window',
                                        'target': 'new',

                                      }

				
class Project(models.Model):
    _inherit = 'project.project'

    def _get_selected_beverages(self):
        for project in self:
            selected_count = self.env['beverages.selection'].search([('project_id','=',self.id)])
            project.selected_beverages = len(selected_count)


    sale_order_id = fields.Many2one('sale.order','Quotation')
    invoice_id = fields.Many2one('account.invoice','Invoice')
    amount_untaxed = fields.Monetary(string='Untaxed Amount', store=False, readonly=True, compute='_amount_all', track_visibility='always')
    amount_tax = fields.Monetary(string='Taxes', store=False, readonly=True, compute='_amount_all', track_visibility='always')
    amount_total = fields.Monetary(string='Total', store=False, readonly=True, compute='_amount_all', track_visibility='always')
    pricelist_id = fields.Many2one('product.pricelist',compute='_get_pricelist_id',store=True,string='Pricelist')
    currency_id = fields.Many2one("res.currency", related='pricelist_id.currency_id', string="Currency")
    order_ids = fields.One2many('sale.order.line','project_id','Orders')
    pos_order_ids = fields.One2many('pos.order','project_id','POS Orders')
    bev_budget_amount = fields.Float(compute="_get_bev_budget_amount",string="Beverage Budget",store=True)
    bev_budget_ids = fields.One2many('beverage.budget','project_id','Beverage Budget')
    event_pos_type = fields.Selection([('cash_bar','Cash Bar'),('event_budget','Event Budget Only'),('budget_cash_bar','Budget then Cash Bar')],string="Event POS Settings")
    pos_orders_amount = fields.Float(compute="_get_pos_orders_amount",string="POS Orders Amount",store=True)
    selected_beverages = fields.Integer(compute="_get_selected_beverages",string="Selected Beverages")
    event_budget_pos_orders_amount=fields.Float(compute='_get_event_budget_pos_orders_amount',string="Event Budget POS Orders Amount",store=True)
    budget_available_amount = fields.Float(compute="_get_budget_available_amount",string="Available Budget",store=True)
    budget_utilized_per = fields.Float(compute="_get_budget_utilized_per",string="Budget Utilized(%)",store=True)

    # Added by Raaj
    project_number = fields.Char('Project Number')
    no_of_people = fields.Integer('No. of People')
    function_type = fields.Selection([ ('corporate','Corporate'),('private','Private'),('wedding','Wedding'),('birthday','Birthday'),('product_launch','Product Launch'),('activation','Activation') ])
    #service_required = fields.Selection([ ('welcome_drinks','Welcome Drinks'),('full_bar','Full Bar'),('signature_cocktail_bar','Signature Coffee Bar'),('action_shooter_bar','Action Shooter Bar'),('ice_lollies','Ice Lollies'),('team_building','Team Building'),('kosher','Kosher') ])
    bars = fields.Selection([('exp_bar','Experience Bar'),('pl','PL'),('special_events_bar','Special Events Bar'),('festival_bars','Festival Bars'),('circular','Circular')],string="Bar Style")
    time_start = fields.Datetime('Time Start')
    time_end = fields.Datetime('Time End')
    service_required_ids = fields.Many2many('service.required','project_service_required_rel','project_id','service_id','Service Required')
    near_thirst_dep = fields.Selection([('captown','Cape Town'),('durban','Durban'),('johannesburg','Johannesburg')],string="Nearest Thirst Department*")
    function_venue = fields.Char('Function Venue')
    budget_amt = fields.Float('Budget')
    #APR 10 start
    #consumable_beverage_ids = fields.One2many('selected.beverages','consume_project_id',compute="_get_consumable_beverage_ids",string="Consumables")
    #equipment_beverage_ids = fields.One2many('selected.beverages','equipment_project_id',compute="_get_equipment_beverage_ids",string="Equipment")
    consumable_beverage_ids = fields.One2many('product.classification.lines','consume_project_id',string="Consumables")
    equipment_beverage_ids = fields.One2many('product.classification.lines','equipment_project_id',string="Equipment")


    staffing_ids = fields.Many2many('hr.employee','project_emp_rel','project_id','emp_id',string="Staffing")
    product_bom_ids = fields.One2many('product.bom.lines','project_id',string="Bar Materials")
    sale_order_ids = fields.One2many('sale.order','project_project_id',string="Sales")
    purchase_order_ids = fields.One2many('purchase.order','project_id',string="Purchase")
    invoice_ids = fields.One2many('account.invoice','inv_project_id',string="Invoices")
    vendor_bill_ids =fields.One2many('account.invoice','bill_project_id',string="Vendor Bills")
    #MAY03
    site_contact_name = fields.Char('Site Contact Name')
    site_contact_number = fields.Char('Site Contact Number')
	

    @api.multi
    def _get_consumable_beverage_ids(self):
	project_bev_select_ids = [obj.id for obj in self.beverages_selection_ids]
	select_bev_ids = self.env['selected.beverages'].search([('bev_select_id','in',project_bev_select_ids),('classification','=','consumable')])
	selected_ids = [obj.id for obj in select_bev_ids]
	self.consumable_beverage_ids = [(6,0,selected_ids)]


    @api.multi
    def _get_equipment_beverage_ids(self):
        project_bev_select_ids = [obj.id for obj in self.beverages_selection_ids]
        select_bev_ids = self.env['selected.beverages'].search([('bev_select_id','in',project_bev_select_ids),('classification','=','equipment')])
        selected_ids = [obj.id for obj in select_bev_ids]
        self.equipment_beverage_ids = [(6,0,selected_ids)]


    @api.depends('pos_order_ids.amount_total')
    def _get_event_budget_pos_orders_amount(self):
	''' to calculate event budget pos orders amount '''
	for obj in self:
	    pos_orders_amount = 0.0
	    for rec in obj.pos_order_ids:
		if rec.ordered_type == 'event_budget':
		    pos_orders_amount += rec.amount_total
	    obj.event_budget_pos_orders_amount = pos_orders_amount

 
    @api.depends('bev_budget_amount','event_budget_pos_orders_amount')
    def _get_budget_available_amount(self):
	''' to calculate budget available amount '''
	for rec in self:
	    rec.budget_available_amount = rec.bev_budget_amount - rec.event_budget_pos_orders_amount

    @api.depends('bev_budget_amount','event_budget_pos_orders_amount')
    def _get_budget_utilized_per(self):
	''' to calculate budget utilized percentage '''
        for rec in self:
	    if rec.bev_budget_amount:
                rec.budget_utilized_per = ((rec.event_budget_pos_orders_amount/rec.bev_budget_amount) * 100)
	    else:
	 	rec.budget_utilized_per = 0.0

    @api.depends('pos_order_ids.amount_total')
    def _get_pos_orders_amount(self):
	''' to calculate total pos orders amount '''
	tot_amt = 0.0
	for rec in self.pos_order_ids:
	    tot_amt += rec.amount_total
	self.pos_orders_amount = tot_amt

    @api.depends('bev_budget_ids.budget_amount')
    def _get_bev_budget_amount(self):
	''' to calculate total beverage budget '''
        tot_amt = 0.0
        for rec in self.bev_budget_ids:
            tot_amt += rec.budget_amount
        self.bev_budget_amount = tot_amt

    @api.depends('sale_order_id')
    @api.model
    def _get_pricelist_id(self):
	for rec in self:
	    if rec.sale_order_id:
	        rec.pricelist_id = rec.sale_order_id.pricelist_id.id

    @api.depends('order_ids.price_total')
    def _amount_all(self):
        """
        Compute the total amounts of the Beverage selection products.
        """
        for order in self:
            amount_untaxed = amount_tax = 0.0
            for line in order.order_ids:
                amount_untaxed += line.price_subtotal
                amount_tax += line.price_tax
            order.update({
                'amount_untaxed': order.pricelist_id.currency_id.round(amount_untaxed),
                'amount_tax': order.pricelist_id.currency_id.round(amount_tax),
                'amount_total': amount_untaxed + amount_tax,
            })
	
    


    @api.multi
    def send_sms(self):
	''' to send a sms to the customer '''
        ##SMS
	#print 'sms fun================',self
	sms_template_id = False	
        if int(self.budget_utilized_per) == 50:
	    sms_template_id=self.env['sms.template'].search([('name','=','Budget utilization 50%')])
	elif int(self.budget_utilized_per) == 90:
            sms_template_id=self.env['sms.template'].search([('name','=','Budget utilization 90%')])
        elif int(self.budget_utilized_per) == 100:
            sms_template_id=self.env['sms.template'].search([('name','=','Budget utilization 100%')])
	else:pass
	if sms_template_id:
           gateway = self.env['sms.smsclient'].search([])

           mobile=''
           if self.sale_order_id.partner_id and self.sale_order_id.partner_id.mobile:
               mobile = self.sale_order_id.partner_id.mobile
           else:
               mobile = ''	   
           body = self.env['mail.template'].render_template(sms_template_id.body_html,'project.project',self.id)
           url = gateway.url
           name = url
           ref = ''
           if gateway.method == 'http':
               prms = {}
               for p in gateway.property_ids:
                   if p.type == 'user':
                       prms[p.name] = p.value
                   elif p.type == 'password':
                      prms[p.name] = p.value
                   elif p.type == 'to':
                      prms[p.name] = mobile
                   elif p.type == 'sender':
                       prms[p.name]= p.value
                   elif p.type == 'sms':
                       prms[p.name] = body
                   elif p.type == 'extra':
                       prms[p.name] = p.value
               params = urllib.urlencode(prms)
               name = url + "?" + params
               queue_obj = self.env['sms.smsclient.queue']
               values = {
                           'name': name,
                           'gateway_id': gateway.id,
                           'state': 'draft',
                           'mobile': mobile,
                           'msg':body
                         }
               queue_obj.sudo().create(values)
	else:pass	

    @api.multi
    def create_purchase_orders(self):
	vendor_list = []
	qty_rqd = {}
	dic = {}
	for bev_select in self.beverages_selection_ids:
	    for selected_bev in bev_select.selected_beverages_ids:
		if selected_bev.variance >= 1:
		    product = self.env['product.product'].search([('product_tmpl_id','=',selected_bev.product_id.id)])
		    qty_rqd.update({product.id:selected_bev.variance})
		    for vendor in product.seller_ids:
		        if vendor.name.id not in dic.keys():
			    dic.update({vendor.name.id:[product]})
		        else:
			    dic[vendor.name.id].append(product)

	for key in dic.keys():
	    new_dic = {'vendor':key,'products':dic[key]}
	    vendor_list.append(new_dic)

	for item in vendor_list:
	    po_create = self.env['purchase.order'].create({'partner_id':item['vendor'],'project_id':self.id,'order_line':[(0,0,{'product_id':product.id,'name':product.name,'date_planned':datetime.now(),'product_uom':product.uom_po_id.id,'product_qty':qty_rqd[product.id],'price_unit':product.standard_price}) for product in item['products']]})

	return True


    @api.multi
    def print_stock_report(self):
	datas = {		
                'ids':[self.id],
                'model':'project.project',
                }
	return {
                'type':'ir.actions.report.xml',
                'report_name':'kt_thirst_customization.report_stocksheet',
                'datas':datas,
                }

    @api.multi
    def send_staff_sms(self):
        view_id = self.env['ir.model.data'].get_object_reference('kt_thirst_customization', 'send_sms_to_staff_form')
        return {
                                'name':("Send SMS to Staff"),#Name You want to display on wizard
                                'view_mode': 'form',
                                'view_id': view_id[1],
                                'view_type': 'form',
                                'res_model': 'staff.sms',# With . Example sale.order
                                'type': 'ir.actions.act_window',
                                'target': 'new',

                              }
	


    def get_full_bar_beverage_selection_url(self):
        """ Full Bar selection Url """
        
        server_url =  self.env['ir.config_parameter'].get_param('web.base.url')
        action_id = self.env['ir.actions.act_window'].for_xml_id('beverages','beverages_selection_action')
        form_id = self.env['ir.model.data'].get_object_reference('beverages','beverage_main')[1]
	bev_menu_id = self.env['beverages'].search([('name','=','Full Bar Beverage Menu')],limit=1)
	bev_select_id = self.env['beverages.selection'].search([('project_id','=',self.id),('beverage_menu_id','=',bev_menu_id.id)],limit=1)
        url_pattrn = server_url +'/web#id='+ str(bev_select_id.id)+'&view_type=form&model=beverages.selection&action='+str(action_id['id'])+'&menu_id='+ str(form_id)
	#url_pattrn = server_url +'/web#id='+ str(bev_select_id.id)+'&view_type=form&model=beverages.selection&action='+str(action_id['id'])+'&menu_id=361'
        return url_pattrn

    def get_cocktail_bar_beverage_selection_url(self):
        """ Cocktail Bar selection Url """

        server_url =  self.env['ir.config_parameter'].get_param('web.base.url')
        action_id = self.env['ir.actions.act_window'].for_xml_id('beverages','beverages_selection_action')
        form_id = self.env['ir.model.data'].get_object_reference('beverages','beverage_main')[1]
        bev_menu_id = self.env['beverages'].search([('name','=','Cocktail Bar Beverage Menu')],limit=1)
        bev_select_id = self.env['beverages.selection'].search([('project_id','=',self.id),('beverage_menu_id','=',bev_menu_id.id)],limit=1)
        url_pattrn = server_url +'/web#id='+ str(bev_select_id.id)+'&view_type=form&model=beverages.selection&action='+str(action_id['id'])+'&menu_id='+ str(form_id)
	#url_pattrn = server_url +'/web#id='+ str(bev_select_id.id)+'&view_type=form&model=beverages.selection&action='+str(action_id['id'])+'&menu_id=361'
        return url_pattrn

    @api.multi
    def send_email_fullbar_beverages_selection(self):
	email_to = self.sale_order_id.partner_id.email
	try:
	    template_id = self.env['ir.model.data'].get_object_reference('kt_thirst_customization','full_bar_beverages_selection_template')[1]
	    template_obj = template_id and self.env['mail.template'].browse(template_id) or False
	except:
	    template_id = False
	if template_id and email_to:
	    template_obj.write({'email_to':email_to})
	    template_obj.send_mail(self.id,force_send=True)
	return True


    @api.multi
    def send_email_cocktailbar_beverages_selection(self):
        email_to = self.sale_order_id.partner_id.email
        try:
            template_id = self.env['ir.model.data'].get_object_reference('kt_thirst_customization','cocktail_bar_beverages_selection_template')[1]
            template_obj = template_id and self.env['mail.template'].browse(template_id) or False
        except:
            template_id = False
        if template_id and email_to:
            template_obj.write({'email_to':email_to})
	    template_obj.send_mail(self.id,force_send=True)
        return True


    @api.model
    def beverages_selection_reminder(self):
	full_bar_bev_menu_id = self.env['beverages'].search([('name','=','Full Bar Beverage Menu')],limit=1)
	cocktail_bar_bev_menu_id = self.env['beverages'].search([('name','=','Cocktail Bar Beverage Menu')],limit=1)
	for obj in self.search([]):
	    function_date = obj.sale_order_id.time_start
	    if function_date:
	        function_date = datetime.strptime(function_date,'%Y-%m-%d %H:%M:%S')
	        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
	        now = datetime.strptime(now,'%Y-%m-%d %H:%M:%S')
	        if function_date > now and (( ((function_date - now).days * 86400)+((function_date - now).seconds) )/3600) <= 48:
	 	    for bev_select_obj in obj.beverages_selection_ids:
		        email_to = obj.sale_order_id.partner_id.email	
		        template_id = False
		        if bev_select_obj.beverage_menu_id.id == full_bar_bev_menu_id.id and not bev_select_obj.is_completed:
		            try:
		                template_id = self.env['ir.model.data'].get_object_reference('kt_thirst_customization','full_bar_beverages_selection_incomplete_template')[1]
			        template_obj = template_id and self.env['mail.template'].browse(template_id) or False
		            except:
		                template_id = False
		        elif bev_select_obj.beverage_menu_id.id == cocktail_bar_bev_menu_id.id and not bev_select_obj.is_completed:
                            try:
                                template_id = self.env['ir.model.data'].get_object_reference('kt_thirst_customization','cocktail_bar_beverages_selection_incomplete_template')[1]
                                template_obj = template_id and self.env['mail.template'].browse(template_id) or False
                            except:
                                template_id = False
	                if template_id and email_to:
	                    template_obj.write({'email_to':email_to})
               		    template_obj.send_mail(obj.id,force_send=True)
	return True

    @api.model
    def beverages_default_selection(self):
        full_bar_bev_menu = self.env['beverages'].search([('name','=','Full Bar Beverage Menu')],limit=1)
	full_bar_products = []
	for obj in full_bar_bev_menu.beverage_product_ids:
	    if obj.prod_type == 'Standard' and obj.default_selection:
	        full_bar_products.append(obj)	
	
        cocktail_bar_bev_menu = self.env['beverages'].search([('name','=','Cocktail Bar Beverage Menu')],limit=1)
	cocktail_bar_products = []
        for obj in cocktail_bar_bev_menu.beverage_product_ids:
            if obj.prod_type == 'Standard' and obj.default_selection:
                cocktail_bar_products.append(obj)
	for obj in self.search([]):
            function_date = obj.sale_order_id.time_start
            if function_date:
                function_date = datetime.strptime(function_date,'%Y-%m-%d %H:%M:%S')
                now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                now = datetime.strptime(now,'%Y-%m-%d %H:%M:%S')
                if function_date > now and (( ((function_date - now).days * 86400)+((function_date - now).seconds) )/3600) <= 24:
                    for bev_select_obj in obj.beverages_selection_ids:
                        if bev_select_obj.beverage_menu_id.id == full_bar_bev_menu.id and not bev_select_obj.is_completed:
			    for product in full_bar_products:
				obj = self.env['selected.beverages'].create({'sale_order_id':obj.sale_order_id.id,'category_id':product.category_id.id,'sub_category_id':product.sub_categ_id.id,'product_id':product.product_product_id.id,'product_name':product.product_product_id.name,'product_code':product.product_product_id.default_code,'prod_type':product.prod_type,'classification':product.product_product_id.classification,'on_hand':product.product_product_id.qty_available,'forecasted':product.product_product_id.virtual_available,'variance':-(product.product_product_id.qty_available),'bev_select_id':bev_select_obj.id,'standard_bev_select_id':bev_select_obj.id})
			   
			    bev_select_obj.is_completed = True
			    bev_select_obj.date_completed = datetime.now()
			elif bev_select_obj.beverage_menu_id.id == cocktail_bar_bev_menu.id and not bev_select_obj.is_completed:
                            for product in cocktail_bar_products:
                                obj = self.env['selected.beverages'].create({'sale_order_id':obj.sale_order_id.id,'category_id':product.category_id.id,'sub_category_id':product.sub_categ_id.id,'product_id':product.product_product_id.id,'product_name':product.product_product_id.name,'product_code':product.product_product_id.default_code,'prod_type':product.prod_type,'classification':product.product_product_id.classification,'on_hand':product.product_product_id.qty_available,'forecasted':product.product_product_id.virtual_available,'variance':-(product.product_product_id.qty_available),'bev_select_id':bev_select_obj.id,'standard_bev_select_id':bev_select_obj.id})

                            bev_select_obj.is_completed = True
                            bev_select_obj.date_completed = datetime.now()

	return True
			
	


class BeverageBudget(models.Model):
    _name = 'beverage.budget'

    #crm_id = fields.Many2one('crm.lead','Opportunity')
    project_id = fields.Many2one('project.project','Project')
    budget_amount = fields.Float('Budget Amount')
    req_partner_id = fields.Many2one('res.partner','Requested By')
    date_req = fields.Datetime('Date Requested')


class Employee(models.Model):
    _inherit = 'hr.employee'

    project_id = fields.Many2one('project.project','Project')

class SMSTemplate(models.Model):
    "Templates for sending SMS"
    _name = "sms.template"
    _description = 'SMS Templates'
    _order = 'name'

    name= fields.Char("Name",size=256)
    body_html = fields.Text('Body', translate=True, help="Rich-text/HTML version of the message (placeholders may be used here)")
    user_ids = fields.Many2many('res.users','res_sms_template_group_rel', 'template_id', 'user_id', 'Users Allowed')

class SelectedBeverages(models.Model):
        _name = 'product.classification.lines'

        consume_project_id = fields.Many2one('project.project','Project')
        equipment_project_id = fields.Many2one('project.project','Project')
        product_id = fields.Many2one('product.product',string='Product')
        product_code = fields.Char('Product Code')
        on_hand = fields.Integer(string="On Hand")#qty_available
        forecasted = fields.Integer(string="Forecasted")#virtual_available
        qty_required = fields.Integer('QTY Required')
        variance = fields.Integer(compute="_get_variance",string='Variance')
        classification = fields.Selection([('bar','Bar'),('equipment','Equipment'),('consumable','Consumable')])

        @api.depends('qty_required','on_hand')
        def _get_variance(self):
            for obj in self:
                obj.variance = obj.qty_required - obj.on_hand


class ProductBomLines(models.Model):
    _name = 'product.bom.lines'

    project_id = fields.Many2one('project.project','Project')
    product_id = fields.Many2one('product.product','Product')
    product_qty = fields.Float('Quantity Required')
    product_uom_id = fields.Many2one('product.uom','Product Unit of Measure')
    product_code = fields.Char('Product Code')
    classification = fields.Selection([('bar','Bar'),('equipment','Equipment'),('consumable','Consumable')])
    on_hand = fields.Integer(string="On Hand")#qty_available
    variance = fields.Integer(compute="_get_variance",string='Variance')
    forecasted = fields.Integer(string="Forecasted")#virtual_available

    @api.depends('product_qty','on_hand')
    def _get_variance(self):
        for obj in self:
            obj.variance = obj.product_qty - obj.on_hand



