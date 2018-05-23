from odoo import models,fields,api,osv, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError
import urllib
#Need to install below package
import html2text
from datetime import datetime,timedelta,date


class ProductCategory(models.Model):
    _inherit = "product.category"

    print_on = fields.Selection([
        ('equipment', 'Equipment & Glassware Sheet'),
        ('stock', 'Stock Sheet'),
        ('bar', 'Bar Sheet'),
    ], string="Print On")


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
				#body = self.env['mail.template'].render_template(sms_template_id.body_html,'project.project',self.id)
				body = html2text.html2text(self.sms_template_body)
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

	'''@api.multi
        def send_sms_to_staff(self):
                project_id = self._context['active_id']
                if project_id:
			project_obj = self.env['project.project'].browse(project_id)
                        mobile = project_obj.user_id and project_obj.user_id.partner_id.mobile or False
                if not mobile:
                        raise UserError('Please configure mobile number for Project Manager to send SMS.')

                if mobile:
		    self.send_sms(self.select_sms_template.id,mobile)
                for staff in project_obj.setup_staffing_ids:
                    if staff.mobile_phone:
                        self.send_sms(self.select_sms_template.id,staff.mobile_phone)
                for staff in project_obj.event_staffing_ids:
                    if staff.mobile_phone:
                        self.send_sms(self.select_sms_template.id,staff.mobile_phone)
                for staff in project_obj.breakdown_staffing_ids:
                    if staff.mobile_phone:
                        self.send_sms(self.select_sms_template.id,staff.mobile_phone)'''

        @api.multi
        def send_sms_to_staff(self):
                project_id = self._context['active_id']
                context = self._context
                if project_id:
                        project_obj = self.env['project.project'].browse(project_id)

                if context.get('staff_type') == 'setup':
                    for staff in project_obj.setup_staff_ids:
                        if staff.mobile_phone:
                            self.send_sms(self.select_sms_template.id,staff.mobile_phone)
                elif context.get('staff_type') == 'event':
                    for staff in project_obj.event_staff_ids:
                        if staff.mobile_phone:
                            self.send_sms(self.select_sms_template.id,staff.mobile_phone)
                elif context.get('staff_type') == 'breakdown':
                    for staff in project_obj.breakdown_staff_ids:
                        if staff.mobile_phone:
                            self.send_sms(self.select_sms_template.id,staff.mobile_phone)



	def send_sms(self,sms_template_id,mobile):
	        if sms_template_id and mobile:
                        sms_template_obj = self.env['sms.template'].browse(sms_template_id)
                        if sms_template_obj:
                                gateway = self.env['sms.smsclient'].search([])
                                #body = self.env['mail.template'].render_template(sms_template_obj.body_html,'staff.sms',self.id)
				body = html2text.html2text(self.sms_template_body)
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
    _rec_name = 'project_number'
    _order = 'id desc'


    def _get_selected_beverages(self):
        for project in self:
            selected_count = self.env['beverages.selection'].search([('project_id', '=', project.id)])
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
    event_pos_type = fields.Selection([('cash_bar','Cash Bar'),('event_budget','Event Budget Only'),('budget_cash_bar','Budget then Cash Bar')],string="Event POS Settings",default='budget_cash_bar')
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
    #project_staff_ids = fields.Many2many('project.staff','project_staff_rel','project_id','staff_id',string="Project Staff")
    #setup_staffing_ids = fields.Many2many('project.staff','project_setup_staff_rel','setup_project_id','setup_staff_id',string="Staffing Setup")
    #event_staffing_ids = fields.Many2many('project.staff','project_event_staff_rel','event_project_id','event_staff_id',string="Staffing Event")
    #breakdown_staffing_ids = fields.Many2many('project.staff','project_breakdown_staff_rel','breakdown_project_id','breakdown_staff_id',string="Staffing Breakdown")
    setup_staff_ids = fields.One2many('project.staff','project_setup_id',string="Staffing Setup")
    event_staff_ids = fields.One2many('project.staff','project_event_id',string="Staffing Event")
    breakdown_staff_ids = fields.One2many('project.staff','project_breakdown_id',string="Staffing Breakdown")
    staff_readonly = fields.Boolean('Staff Readonly')
    is_manager = fields.Boolean(compute="_compute_is_manager")

    #MAY03
    site_contact_name = fields.Char('Site Contact Name')
    site_contact_number = fields.Char('Site Contact Number')
    setup_date = fields.Datetime('Setup Date')
    breakdown_date = fields.Datetime('Breakdown Date')
    cage = fields.Many2one('stock.location',string="Cage")
    vehicle = fields.Many2one('stock.location',string="Vehicle")
    #JUN 01 Jagadeesh
    fun_internal_loc_id = fields.Many2one('stock.location',string="Function Internal Location")
    fun_event_loc_id = fields.Many2one('stock.location',string="Function Event Location")
    created_purchase_orders = fields.Boolean('Purchase Orders Created ?')
    transfered_stock = fields.Boolean('Transfered Stock ?')
    bar_tender_arrival_time = fields.Datetime('Bar Tender Arrival Time')
    bar_support_manager_arrival_time = fields.Datetime('Bar Support & Manager Arrival Time')
    pos_device_ids = fields.One2many('pos.devices','project_id',string="POS devices")
    post_msg = fields.Char('Post Message',default='Posted')
    next_transfer_type = fields.Selection([(1,'Stock - Function internal location'),(2,'Function internal location - Cage'),
                                           (3,'Cage - Vehicle'),(4,'Vehicle - Function event location'),
                                           (5,'Function event location - Vehicle'),(6,'Vehicle - Cage'),
                                           (7,'Cage - Function internal location'),(8,'Function internal location - Stock')],default=1)
    division_ids = fields.Many2many('division.division','project_div_rel','project_id','div_id',string="Division")
    stock_picking_count = fields.Integer(compute="_compute_stock_picking_count", string="Picking Count")
    pricelist_id = fields.Many2one("product.pricelist", string="POS Pricelist")

    def _compute_is_manager(self):
        for project in self:
            if project.user_has_groups('account.group_account_manager') or project.user_has_groups('stock.group_stock_manager'):
                project.is_manager = True
            else:
                project.is_manager = False

    def _compute_stock_picking_count(self):
        Picking = self.env['stock.picking']
        for project in self:
            project.stock_picking_count = Picking.search_count([('origin', '=', project.project_number)])

    @api.multi
    def view_stock_picking(self):
        self.ensure_one()
        action = self.env.ref('stock.action_picking_tree_all').read()[0]
        pickings = self.env['stock.picking'].search([('origin', '=', self.project_number)])
        action['domain'] = [('id', 'in', pickings.ids)]
        return action

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

    @api.one
    @api.depends('pos_order_ids.amount_total')
    def _get_pos_orders_amount(self):
	''' to calculate total pos orders amount '''
	tot_amt = 0.0
	for rec in self.pos_order_ids:
	    tot_amt += rec.amount_total
	self.pos_orders_amount = tot_amt

    @api.one
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
           #new_body = '<html><body>'
           new_body = body
	   if int(self.budget_utilized_per) == 50 or int(self.budget_utilized_per) == 90:
	       #remaining_amt = self.bev_budget_amount - self.event_budget_pos_orders_amount
	       #new_body += 'Remaining %s.'%remaining_amt
		new_body += ' Remaining %s.'%self.budget_available_amount
           #new_body += '<p>Please click on below to add addtional budget.</p>'
           budget_url = 'http://thirstuat.odoo.co.za/additional/budget/%s/%s/proj'%(self.id,self.sale_order_id.partner_id.id)
           #new_body += '<a href="%s">Add budget</a>'%budget_url
	   new_body += ' ADD BUDGET %s'%budget_url
           #new_body += '</body></html>'
           body = new_body#html2text.html2text(new_body)

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

        for obj in self.consumable_beverage_ids:
            if obj.variance >= 1:
                product = obj.product_id
                #qty_rqd.update({product.id:obj.variance})
		if product.uom_id == product.uom_po_id:
                    qty_rqd.update({product.id:obj.variance})
                else:
                    uom_diff = product.uom_id.factor / product.uom_po_id.factor
                    new_qty_rqd = int(round(obj.variance / uom_diff))
                    qty_rqd.update({product.id:new_qty_rqd})
                for vendor in product.seller_ids:
                    if vendor.name.id not in dic.keys():
                        dic.update({vendor.name.id:[product]})
                    else:
                        dic[vendor.name.id].append(product)
        for obj in self.equipment_beverage_ids:
            if obj.variance >= 1:
                product = obj.product_id
                #qty_rqd.update({product.id:obj.variance})
		if product.uom_id == product.uom_po_id:
                    qty_rqd.update({product.id:obj.variance})
                else:
                    uom_diff = product.uom_id.factor / product.uom_po_id.factor
                    new_qty_rqd = int(round(obj.variance / uom_diff))
                    qty_rqd.update({product.id:new_qty_rqd})

                for vendor in product.seller_ids:
                    if vendor.name.id not in dic.keys():
                        dic.update({vendor.name.id:[product]})
                    else:
                        dic[vendor.name.id].append(product)

        for obj in self.product_bom_ids:
            if obj.variance >= 1:
                product = obj.product_id
                #qty_rqd.update({product.id:obj.variance})
		if product.uom_id == product.uom_po_id:
                    qty_rqd.update({product.id:obj.variance})
                else:
                    uom_diff = product.uom_id.factor / product.uom_po_id.factor
                    new_qty_rqd = int(round(obj.variance / uom_diff))
                    qty_rqd.update({product.id:new_qty_rqd})
                for vendor in product.seller_ids:
                    if vendor.name.id not in dic.keys():
                        dic.update({vendor.name.id:[product]})
                    else:
                        dic[vendor.name.id].append(product)


	for bev_select in self.beverages_selection_ids:
	    for selected_bev in bev_select.selected_beverages_ids:
		if selected_bev.variance >= 1:
		    product = self.env['product.product'].search([('product_tmpl_id','=',selected_bev.product_id.id)])
		    #qty_rqd.update({product.id:selected_bev.variance})
		    if product.uom_id == product.uom_po_id:
                        qty_rqd.update({product.id:obj.variance})
                    else:
                        uom_diff = product.uom_id.factor / product.uom_po_id.factor
                        new_qty_rqd = int(round(obj.variance / uom_diff))
                        qty_rqd.update({product.id:new_qty_rqd})

		    for vendor in product.seller_ids:
		        if vendor.name.id not in dic.keys():
			    dic.update({vendor.name.id:[product]})
		        else:
			    dic[vendor.name.id].append(product)

	for key in dic.keys():
	    new_dic = {'vendor':key,'products':dic[key]}
	    vendor_list.append(new_dic)

	for item in vendor_list:
	    #po_create = self.env['purchase.order'].create({'partner_id':item['vendor'],'project_id':self.id,'order_line':[(0,0,{'product_id':product.id,'name':product.name,'date_planned':datetime.now(),'product_uom':product.uom_po_id.id,'product_qty':qty_rqd[product.id],'price_unit':product.standard_price}) for product in item['products']]})

	    po_create = self.env['purchase.order'].create({'partner_id':item['vendor'],'project_id':self.id })
            # to get the price of respective vendor
            for product in item['products']:
                price = product.standard_price
                for vendor in product.seller_ids:
                    if vendor.name.id == item['vendor']:
                        price = vendor.price
                        break;
                self.env['purchase.order.line'].create({'product_id':product.id,'name':product.name,'date_planned':datetime.now(),'product_uom':product.uom_po_id.id,'product_qty':qty_rqd[product.id],'price_unit':price,'order_id':po_create.id})

	self.created_purchase_orders = True
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
    def recalculate_product_qty(self):
        for obj in self.consumable_beverage_ids:
            obj.on_hand = obj.product_id.qty_available
            obj.forecasted = obj.product_id.virtual_available
        for obj in self.equipment_beverage_ids:
            obj.on_hand = obj.product_id.qty_available
            obj.forecasted = obj.product_id.virtual_available
        for obj in self.product_bom_ids:
            obj.on_hand = obj.product_id.qty_available
            obj.forecasted = obj.product_id.virtual_available
        for beverage_obj in self.beverages_selection_ids:
            for obj in beverage_obj.standard_beverage_ids:
                obj.on_hand = obj.product_id.qty_available
                obj.forecasted = obj.product_id.virtual_available
            for obj in beverage_obj.premium_beverage_ids:
                obj.on_hand = obj.product_id.qty_available
                obj.forecasted = obj.product_id.virtual_available
        return True


    @api.multi
    def transfer_stock_to_function_location(self,stock_pick_id=False):
        if not self.cage:
            raise UserError(_("Please ensure that The Cage, Vehicle fields and the Beverage Selection are completed."))
        if not self.vehicle:
            raise UserError(_("Please ensure that The Cage, Vehicle fields and the Beverage Selection are completed."))
        if not any(selection.is_completed for selection in self.beverages_selection_ids):
            raise UserError(_("Please ensure that The Cage, Vehicle fields and the Beverage Selection are completed."))
        if not self.time_start:
            raise ValidationError('Please select event start date')
        if not self.time_end:
            raise ValidationError('Please selecr event end date')
        event_start = datetime.strptime(self.time_start,'%Y-%m-%d %H:%M:%S')
        event_end = datetime.strptime(self.time_end,'%Y-%m-%d %H:%M:%S')

        warehouse_obj = self.env['stock.warehouse'].search([('code','=','WH')],limit=1)
        picking_type_obj = self.env['stock.picking.type'].search([('name','=','Internal Transfers'),('warehouse_id','=',warehouse_obj.id)],limit=1)

        if self.next_transfer_type == 1:
                    #creating function location
                    par_loc_obj = self.env['stock.location'].search([('name','=','WH')],limit=1)
                    loc_vals = { 'name':str(self.project_number)+' Internal Location','location_id':par_loc_obj.id,'usage':'internal','active':True }
                    fn_loc_obj = self.env['stock.location'].create(loc_vals)
                    if fn_loc_obj:
                        self.fun_internal_loc_id = fn_loc_obj.id

                    #creating function venue location
                    loc_vals = { 'name':str(self.project_number)+' Function Location','usage':'internal','active':True }
                    fn_ven_loc_obj = self.env['stock.location'].create(loc_vals)
                    if fn_ven_loc_obj:
                        self.fun_event_loc_id = fn_ven_loc_obj.id

                    #creating internal transfer(stock operation/stock picking) WH/Stock -> function internal location
                    source_loc_obj = self.env['stock.location'].search([('name','=','Stock'),('location_id','=',par_loc_obj.id)],limit=1)
                    trans_vals = {  'partner_id':self.sale_order_id.partner_id.id,'picking_type_id':picking_type_obj.id,'priority':'1','move_type':'one',
                                    'location_id':source_loc_obj.id,'location_dest_id':fn_loc_obj.id,'min_date':str(datetime.now()),
                                    'origin':self.project_number,'project_id':self.id,
                                 }

                    stock_pick_obj = self.env['stock.picking'].create(trans_vals)
                    for obj in self.consumable_beverage_ids:
                       stock_move_obj = self.env['stock.move'].create({'picking_id':stock_pick_obj.id,'product_id':obj.product_id.id,'product_uom_qty':obj.qty_required,'product_uom':obj.product_id.uom_id.id,'location_id':stock_pick_obj.location_id.id,'location_dest_id':stock_pick_obj.location_dest_id.id,'name':'['+str(obj.product_id.default_code)+'] '+str(obj.product_id.name),'date_expected':str(datetime.now())})

                    for obj in self.equipment_beverage_ids:
                       stock_move_obj = self.env['stock.move'].create({'picking_id':stock_pick_obj.id,'product_id':obj.product_id.id,'product_uom_qty':obj.qty_required,'product_uom':obj.product_id.uom_id.id,'location_id':stock_pick_obj.location_id.id,'location_dest_id':stock_pick_obj.location_dest_id.id,'name':'['+str(obj.product_id.default_code)+'] '+str(obj.product_id.name),'date_expected':str(datetime.now())})

                    for obj in self.product_bom_ids:
                       stock_move_obj = self.env['stock.move'].create({'picking_id':stock_pick_obj.id,'product_id':obj.product_id.id,'product_uom_qty':obj.product_qty,'product_uom':obj.product_id.uom_id.id,'location_id':stock_pick_obj.location_id.id,'location_dest_id':stock_pick_obj.location_dest_id.id,'name':'['+str(obj.product_id.default_code)+'] '+str(obj.product_id.name),'date_expected':str(datetime.now())})

                    for bev_select_obj in self.beverages_selection_ids:
                       for obj in bev_select_obj.selected_beverages_ids:
                           product_obj = self.env['product.product'].search([('product_tmpl_id','=',obj.product_id.id)],limit=1)
                           stock_move_obj = self.env['stock.move'].create({'picking_id':stock_pick_obj.id,'product_id':product_obj.id,'product_uom_qty':obj.qty_required,'product_uom':product_obj.uom_id.id,'location_id':stock_pick_obj.location_id.id,'location_dest_id':stock_pick_obj.location_dest_id.id,'name':'['+str(product_obj.default_code)+'] '+str(product_obj.name),'date_expected':str(datetime.now())})
                    stock_pick_obj.action_confirm()
                    self.write({'transfered_stock':True})

        elif self.next_transfer_type == 2:
            if stock_pick_id:
                    stock_pick = self.env['stock.picking'].browse(stock_pick_id)
                    #creating internal transfer(stock operation/stock picking) Function internal location -> Cage location
                    trans_vals = {  'partner_id':self.sale_order_id.partner_id.id,'picking_type_id':picking_type_obj.id,'priority':'1','move_type':'one',
                                    'location_id':self.fun_internal_loc_id.id,'location_dest_id':self.cage.id,'min_date':str(event_start+timedelta(days=-1)),
                                    'origin':self.project_number,'project_id':self.id,
                                    'move_lines':[(0,0,{'product_id':obj.product_id.id,'product_uom_qty':obj.product_uom_qty,'product_uom':obj.product_id.uom_id.id,'location_id':self.fun_internal_loc_id.id,'location_dest_id':self.cage.id,'name':'['+str(obj.product_id.default_code)+'] '+str(obj.product_id.name),'date_expected':str(event_start+timedelta(days=-1))}) for obj in stock_pick.move_lines]
                                 }
                    stock_pick2_obj = self.env['stock.picking'].create(trans_vals)
                    stock_pick2_obj.action_confirm()

        elif self.next_transfer_type == 3:
            if stock_pick_id:
                    stock_pick = self.env['stock.picking'].browse(stock_pick_id)
                    #creating internal transfer(stock operation/stock picking) Cage Location -> Vehicle Location
                    trans_vals = {  'partner_id':self.sale_order_id.partner_id.id,'picking_type_id':picking_type_obj.id,'priority':'1','move_type':'one',
                                    'location_id':self.cage.id,'location_dest_id':self.vehicle.id,'min_date':str(event_start+timedelta(days=-1)),
                                    'origin':self.project_number,'project_id':self.id,
                                    'move_lines':[(0,0,{'product_id':obj.product_id.id,'product_uom_qty':obj.product_uom_qty,'product_uom':obj.product_id.uom_id.id,'location_id':self.cage.id,'location_dest_id':self.vehicle.id,'name':'['+str(obj.product_id.default_code)+'] '+str(obj.product_id.name),'date_expected':str(event_start+timedelta(days=-1))}) for obj in stock_pick.move_lines]
                                 }
                    stock_pick3_obj = self.env['stock.picking'].create(trans_vals)
                    stock_pick3_obj.action_confirm()

        elif self.next_transfer_type == 4:
            if stock_pick_id:
                    stock_pick = self.env['stock.picking'].browse(stock_pick_id)
                    #creating internal transfer(stock operation/stock picking) Vehicle Location --> Function Event Location
                    trans_vals = {  'partner_id':self.sale_order_id.partner_id.id,'picking_type_id':picking_type_obj.id,'priority':'1','move_type':'one',
                        'location_id':self.vehicle.id,'location_dest_id':self.fun_event_loc_id.id,'min_date':str(event_start),
                        'origin':self.project_number,'project_id':self.id,
                        'move_lines':[(0,0,{'product_id':obj.product_id.id,'product_uom_qty':obj.product_uom_qty,'product_uom':obj.product_id.uom_id.id,'location_id':self.vehicle.id,'location_dest_id':self.fun_event_loc_id.id,'name':'['+str(obj.product_id.default_code)+'] '+str(obj.product_id.name),'date_expected':str(event_start)}) for obj in stock_pick.move_lines]
                     }
                    stock_pick4_obj = self.env['stock.picking'].create(trans_vals)
                    stock_pick4_obj.action_confirm()

        elif self.next_transfer_type == 5:
            if stock_pick_id:
                    stock_pick = self.env['stock.picking'].browse(stock_pick_id)
                    #creating incoming shipment/transfer(stock operation/stock picking) Function Event Location --> Vehicle Location
                    trans_vals = {  'partner_id':self.sale_order_id.partner_id.id,'picking_type_id':picking_type_obj.id,'priority':'1','move_type':'one',
                        'location_dest_id':self.vehicle.id,'location_id':self.fun_event_loc_id.id,'min_date':str(event_end),
                        'origin':self.project_number,'project_id':self.id,
                        'move_lines':[(0,0,{'product_id':obj.product_id.id,'product_uom_qty':obj.product_uom_qty,'product_uom':obj.product_id.uom_id.id,'location_id':self.fun_event_loc_id.id,'location_dest_id':self.vehicle.id,'name':'['+str(obj.product_id.default_code)+'] '+str(obj.product_id.name),'date_expected':str(event_end)}) for obj in stock_pick.move_lines]
                     }
                    stock_pick5_obj = self.env['stock.picking'].create(trans_vals)
                    stock_pick5_obj.action_confirm()

        elif self.next_transfer_type == 6:
            if stock_pick_id:
                    stock_pick = self.env['stock.picking'].browse(stock_pick_id)
                    #creating incoming shipment/transfer(stock operation/stock picking)  Vehicle Location --> Cage Location
                    trans_vals = {  'partner_id':self.sale_order_id.partner_id.id,'picking_type_id':picking_type_obj.id,'priority':'1','move_type':'one',
                        'location_dest_id':self.cage.id,'location_id':self.vehicle.id,'min_date':str(event_end),
                        'origin':self.project_number,'project_id':self.id,
                        'move_lines':[(0,0,{'product_id':obj.product_id.id,'product_uom_qty':obj.product_uom_qty,'product_uom':obj.product_id.uom_id.id,'location_id':self.vehicle.id,'location_dest_id':self.cage.id,'name':'['+str(obj.product_id.default_code)+'] '+str(obj.product_id.name),'date_expected':str(event_end)}) for obj in stock_pick.move_lines]
                     }
                    stock_pick6_obj = self.env['stock.picking'].create(trans_vals)
                    stock_pick6_obj.action_confirm()

        elif self.next_transfer_type == 7:
            if stock_pick_id:
                    stock_pick = self.env['stock.picking'].browse(stock_pick_id)
                    #creating incoming shipment/transfer(stock operation/stock picking) Cage location --> Function internal location
                    trans_vals = {  'partner_id':self.sale_order_id.partner_id.id,'picking_type_id':picking_type_obj.id,'priority':'1','move_type':'one',
                        'location_dest_id':self.fun_internal_loc_id.id,'location_id':self.cage.id,'min_date':str(event_end),
                        'origin':self.project_number,'project_id':self.id,
                        'move_lines':[(0,0,{'product_id':obj.product_id.id,'product_uom_qty':obj.product_uom_qty,'product_uom':obj.product_id.uom_id.id,'location_id':self.cage.id,'location_dest_id':self.fun_internal_loc_id.id,'name':'['+str(obj.product_id.default_code)+'] '+str(obj.product_id.name),'date_expected':str(event_end)}) for obj in stock_pick.move_lines]

                     }
                    stock_pick7_obj = self.env['stock.picking'].create(trans_vals)
                    stock_pick7_obj.action_confirm()

        elif self.next_transfer_type == 8:
            if stock_pick_id:
                    stock_pick = self.env['stock.picking'].browse(stock_pick_id)
                    par_loc_obj = self.env['stock.location'].search([('name','=','WH')],limit=1)
                    source_loc_obj = self.env['stock.location'].search([('name','=','Stock'),('location_id','=',par_loc_obj.id)],limit=1)
                    #creating incoming shipment/transfer(stock operation/stock picking) function internal location --> WH/Stock
                    trans_vals = {  'partner_id':self.sale_order_id.partner_id.id,'picking_type_id':picking_type_obj.id,'priority':'1','move_type':'one',
                        'location_dest_id':source_loc_obj.id,'location_id':self.fun_internal_loc_id.id,'min_date':str(event_end+timedelta(days=1)),
                        'origin':self.project_number,'project_id':self.id,
                        'move_lines':[(0,0,{'product_id':obj.product_id.id,'product_uom_qty':obj.product_uom_qty,'product_uom':obj.product_id.uom_id.id,'location_id':self.fun_internal_loc_id.id,'location_dest_id':source_loc_obj.id,'name':'['+str(obj.product_id.default_code)+'] '+str(obj.product_id.name),'date_expected':str(event_end+timedelta(days=1))}) for obj in stock_pick.move_lines]

                    }
                    stock_pick8_obj = self.env['stock.picking'].create(trans_vals)
                    stock_pick8_obj.action_confirm()

        else:pass

        return True


    @api.multi
    def close_project(self):

        self.active = False
	if self.fun_internal_loc_id: self.fun_internal_loc_id.active = False
	if self.fun_event_loc_id: self.fun_event_loc_id.active = False
	return True

    @api.multi
    def print_staff_sheet(self):
        datas = {  'ids':[self.id],'model':'project.project' }

        return {
                'type':'ir.actions.report.xml',
                'report_name':'kt_thirst_customization.report_projectstaff',
                'datas':datas,
                }

    @api.multi
    def print_staff_costing(self):
        datas = {  'ids':[self.id],'model':'project.project' }

        return {
                'type':'ir.actions.report.xml',
                'report_name':'kt_thirst_customization.report_staffcosting',
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


    @api.multi
    def post_staff_costing(self):
        view_id = self.env['ir.model.data'].get_object_reference('kt_thirst_customization', 'project_staff_costing_view_form')
        return {
                                'name':("Post Staff Costing"),#Name You want to display on wizard
                                'view_mode': 'form',
                                'view_id': view_id[1],
                                'view_type': 'form',
                                'res_model': 'project.staff.cost',# With . Example sale.order
                                'type': 'ir.actions.act_window',
                                'target': 'new',
                                'context':{'default_confirm_msg':'This will post the staff costing for payment. Please ensure that the hours and rates captured are accurate. The records will now be read only and you will not be able to edit them'}

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


    @api.multi
    def default_beverages_selection(self,bev_select_id):
	''' This method will be called from controller
	    to auto select default products and customer can remove and select gain what they want at beverages selection page'''
	bev_select_obj = self.env['beverages.selection'].browse(bev_select_id)
	project_obj = bev_select_obj.project_id
	default_products = []
	for obj in bev_select_obj.beverage_menu_id.beverage_product_ids:
            if obj.prod_type == 'Standard' and obj.default_selection:
                default_products.append(obj)
	if default_products:
	    for product in default_products:
                obj = self.env['selected.beverages'].create({'sale_order_id':project_obj.sale_order_id.id,'category_id':product.category_id.id,'sub_category_id':product.sub_categ_id.id,'product_id':product.product_product_id.id,'product_name':product.product_product_id.name,'product_code':product.product_product_id.default_code,'prod_type':product.prod_type,'classification':product.product_product_id.classification,'on_hand':product.product_product_id.qty_available,'forecasted':product.product_product_id.virtual_available,'variance':-(product.product_product_id.qty_available),'bev_select_id':bev_select_obj.id})
		if obj.prod_type == 'Standard':
                        obj.standard_bev_select_id = bev_select_obj.id
                elif obj.prod_type == 'Premium':
                        obj.premium_bev_select_id = bev_select_obj.id
	return True

class BeverageBudget(models.Model):
    _name = 'beverage.budget'

    #crm_id = fields.Many2one('crm.lead','Opportunity')
    project_id = fields.Many2one('project.project','Project')
    budget_amount = fields.Float('Budget Amount')
    req_partner_id = fields.Many2one('res.partner','Requested By')
    date_req = fields.Datetime('Date Requested')


'''class Employee(models.Model):
    _inherit = 'hr.employee'

    #project_id = fields.Many2one('project.project','Project')
    emp_no = fields.Char('Employee No')
    partner_id = fields.Many2one('res.partner',string="Related Partner") '''

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
	uom_id = fields.Many2one('product.uom',related="product_id.uom_id",string="Unit of Measure")
	uom_po_id = fields.Many2one('product.uom',related="product_id.uom_po_id",string="Purchase Unit of Measure")
        product_code = fields.Char('Product Code')
        on_hand = fields.Integer(string="On Hand")#qty_available
        forecasted = fields.Integer(string="Forecasted")#virtual_available
        qty_required = fields.Float('QTY Required')
        variance = fields.Integer(compute="_get_variance",string='Variance')
        classification = fields.Selection([('bar','Bar'),('equipment','Equipment'),('consumable','Consumable')])


        @api.onchange('product_id')
        def onchange_product_id(self):
            for obj in self:
                obj.product_code = obj.product_id.default_code
                obj.classification = obj.product_id.classification
                obj.uom_id = obj.product_id.uom_id.id
                obj.uom_po_id = obj.product_id.uom_po_id.id
                obj.on_hand = obj.product_id.qty_available
                obj.forecasted = obj.product_id.virtual_available


        @api.depends('qty_required','on_hand')
        def _get_variance(self):
            for obj in self:
                obj.variance = obj.on_hand - obj.qty_required


class ProductBomLines(models.Model):
    _name = 'product.bom.lines'

    project_id = fields.Many2one('project.project','Project')
    product_id = fields.Many2one('product.product','Product')
    product_qty = fields.Float('Quantity Required')
    product_uom_id = fields.Many2one('product.uom',related="product_id.uom_id",string='Product Unit of Measure')
    uom_po_id = fields.Many2one('product.uom',related="product_id.uom_po_id",string="Purchase Unit of Measure")
    product_code = fields.Char('Product Code')
    classification = fields.Selection([('bar','Bar'),('equipment','Equipment'),('consumable','Consumable')])
    on_hand = fields.Integer(string="On Hand")#qty_available
    variance = fields.Integer(compute="_get_variance",string='Variance')
    forecasted = fields.Integer(string="Forecasted")#virtual_available
    total = fields.Float(compute="_compute_total", string="Total")

    @api.onchange('product_id')
    def onchange_product_id(self):
        for obj in self:
            obj.product_code = obj.product_id.default_code
            obj.classification = obj.product_id.classification
            obj.product_uom_id = obj.product_id.uom_id.id
            obj.uom_po_id = obj.product_id.uom_po_id.id
            obj.on_hand = obj.product_id.qty_available
            obj.forecasted = obj.product_id.virtual_available

    def _compute_total(self):
        for record in self:
            record.total = record.product_id.lst_price * record.product_qty

    @api.depends('product_qty','on_hand')
    def _get_variance(self):
        for obj in self:
            obj.variance = obj.on_hand - obj.product_qty


class PosDevices(models.Model):
    _name = 'pos.devices'


    pos_config_id = fields.Many2one('pos.config',string="POS Name")
    project_id = fields.Many2one('project.project',string="Project")

    @api.multi
    def start_new_session(self):
        if self.project_id.fun_event_loc_id:
            self.pos_config_id.stock_location_id = self.project_id.fun_event_loc_id.id
	else:
            raise ValidationError('This project not having function location')

        self.pos_config_id.pricelist_id = self.project_id.pricelist_id
        current_session_id = self.env['pos.session'].create({
                'user_id': self.env.uid,
                'config_id': self.pos_config_id.id,
                'project_id':self.project_id.id ,
                'budget_available_amount': self.project_id.budget_available_amount
            })
        #if self.current_session_id.state != 'opened':
        #    #self.current_session_id.state = 'opened'
        #    self.current_session_id.action_pos_session_open()
        if current_session_id.state == 'opened':
            return {
            'type': 'ir.actions.act_url',
            'url':   '/pos/web/',
            'target': 'new',
        }
        return True



class ProjectStaffCost(models.Model):
    _name = 'project.staff.cost'

    confirm_msg = fields.Text('Confirm Message')

    @api.multi
    def post(self):
        project_id = self._context.get('active_ids')
        proj_obj = self.env['project.project'].browse(project_id[0])
        journal_obj = self.env['account.journal'].search([('name','=','Miscellaneous Operations')],limit=1)
        for staff in proj_obj.setup_staff_ids:
            self.create_account_moves(project_id[0],staff.id,journal_obj.id)
        for staff in proj_obj.event_staff_ids:
            self.create_account_moves(project_id[0],staff.id,journal_obj.id)
        for staff in proj_obj.breakdown_staff_ids:
            self.create_account_moves(project_id[0],staff.id,journal_obj.id)
        proj_obj.staff_readonly = True
        return True


    @api.model
    def create_account_moves(self,project_id,staff_id,journal_id):

        project_obj = self.env['project.project'].browse(project_id)
        journal_obj = self.env['account.journal'].browse(journal_id)
        staff_obj = self.env['project.staff'].browse(staff_id)
        ref = str(project_obj.name)+' - '+str(staff_obj.employee_id.name)+' Staff Costs'
        analytic_accnt_obj = self.env['account.analytic.account'].search([('name','=',project_obj.name)],limit=1)


        accnt_1_obj = self.env['account.account'].search([('code','=','111220'),('name','=','Staffing Account Payable')],limit=1)
        move_line1_vals = {'account_id':accnt_1_obj.id,'partner_id':staff_obj.employee_id.partner_id.id,'name':ref,'credit':staff_obj.total_cost}


        accnt_2_obj = self.env['account.account'].search([('code','=','500108'),('name','=','Cost of Sales - Staffing')],limit=1)
        move_line2_vals = {'account_id':accnt_2_obj.id,'partner_id':staff_obj.employee_id.partner_id.id,'name':ref,'analytic_account_id':analytic_accnt_obj.id,'debit':staff_obj.total_cost }

        accnt_move_obj = self.env['account.move'].create({ 'journal_id':journal_id,'ref':ref,'date':date.today(),
                                                           'line_ids':[(0,0,dic) for dic in [move_line1_vals,move_line2_vals]]
                                                         })
        accnt_move_obj.post()
        return True
