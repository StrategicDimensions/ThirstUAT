from odoo import fields,models,api
from datetime import datetime,date
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError,ValidationError
from odoo.http import request


##Raaj
class SaleOrder(models.Model):
    _inherit  = 'sale.order'

    no_of_people = fields.Integer('No. of People')
    function_type = fields.Selection([ ('corporate','Corporate'),('private','Private'),('wedding','Wedding'),('birthday','Birthday'),('product_launch','Product Launch'),('activation','Activation') ],string="Function Type")
    service_required = fields.Selection([ ('welcome_drinks','Welcome Drinks'),('full_bar','Full Bar'),('signature_cocktail_bar','Signature Coffee Bar'),('action_shooter_bar','Action Shooter Bar'),('ice_lollies','Ice Lollies'),('team_building','Team Building'),('kosher','Kosher') ])
    bars = fields.Selection([('exp_bar','Experience Bar'),('pl','PL'),('special_events_bar','Special Events Bar'),('festival_bars','Festival Bars'),('circular','Circular')],string="Bar Style")
    time_start = fields.Datetime('Time Start')
    time_end = fields.Datetime('Time End')
    service_required_ids = fields.Many2many('service.required','service_required_rel','sale_id','service_id','Service Required')
    near_thirst_dep = fields.Selection([('captown','Cape Town'),('durban','Durban'),('johannesburg','Johannesburg')],string="Nearest Thirst Department*")
    function_venue = fields.Char('Function Venue')
    division_ids = fields.Many2many('division.division','quote_div_rel','quote_id','division_id',string="Division",default=lambda self: self._get_default_division_ids())
    budget_amt = fields.Float('Budget')


    '''full_bar_selection_completed = fields.Boolean(string="Full Bar Selection Completed ?")
    cocktail_bar_selection_completed = fields.Boolean(string="Cocktail Bar Selection Completed ?")
    consumable_beverage_ids = fields.One2many('selected.beverages','sale_order_id',compute="_get_consumable_beverages",string="Consumables")'''


    beverage_menu_id = fields.Many2one('beverages',string="Beverage Memu") 
    premium_beverages = fields.Boolean(string="Premium Beverages ?")
    project_project_id = fields.Many2one('project.project',string="Project")
    ignore_beverage_selection = fields.Boolean('Ignore Beverages Selection')
    lost_reason_id = fields.Many2one('crm.lost.reason','Cancel Reason')
    lost_reason = fields.Text('Additional comments for cancel reason')
    required_reason = fields.Boolean('Required Reason ?')
    project_create = fields.Boolean('Should create project ?',default=True)

    '''@api.multi
    def _get_consumable_beverages(self):
	beverage_ids = self.env['selected.beverages'].search([('sale_order_id','=',self.id),('classification','=','consumable')])
	self.consumable_beverage_ids = [(6,0,[obj.id for obj in beverage_ids])]'''


    @api.model
    def _get_default_division_ids(self):
            div_obj = self.env['division.division'].search([('name','=','Thirst')],limit=1)
            return div_obj.ids


    @api.multi
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        res = super(SaleOrder,self).onchange_partner_id()
        if self.partner_id.account_type == 'cod':
            self.require_payment = 1
        elif self.partner_id.account_type == 'account':
            self.require_payment = 0
        else: pass

    @api.multi
    @api.depends('website_order_line.product_uom_qty', 'website_order_line.product_id')
    def _compute_cart_info(self):
        for order in self:
            inv_state = 'paid'
            for inv in order.invoice_ids:
                if inv.state != 'paid':
                    inv_state = inv.state
                    break;

            #order.cart_quantity = inv_state != 'paid' and int(sum(order.mapped('website_order_line.product_uom_qty'))) or 0
            if order.state != 'sale' or not order.invoice_ids:
               order.cart_quantity  = int(sum(order.mapped('website_order_line.product_uom_qty')))
            else:
                if inv_state != 'paid':
                    order.cart_quantity = int(sum(order.mapped('website_order_line.product_uom_qty')))
                else:
                    order.cart_quantity = 0
            order.only_services = all(l.product_id.type in ('service', 'digital') for l in order.website_order_line)

    @api.multi
    def write(self,vals):
        if request.session.has_key('from_quote') and request.session['from_quote']:
                vals = {}
        res = super(SaleOrder,self).write(vals)
        return res



    @api.multi
    def writeeee(self,vals):
        partner_id = self.partner_id
        payment_term_id = self.payment_term_id
        pricelist_id = self.pricelist_id
        context = self._context
        if context and context.get('website_id') and partner_id.name != 'Public user':
		if 'partner_id' in vals.keys():
                    #vals['partner_id'] = partner_id.id
		    del vals['partner_id']
		if 'payment_term_id' in vals.keys():
		    #vals['payment_term_id'] = payment_term_id.id
		    del vals['payment_term_id']
		if 'pricelist_id' in vals.keys():
		    #vals['pricelist_id'] = pricelist_id.id
		    del vals['pricelist_id']
		if 'partner_invoice_id' in vals.keys():
		    del vals['partner_invoice_id']
		if 'partner_shipping_id' in vals.keys():
		    del vals['partner_shipping_id']
        return super(SaleOrder,self).write(vals)

    @api.multi
    def action_confirm(self):
        for order in self:
            order.state = 'sale'
            order.confirmation_date = fields.Datetime.now()
            if self.env.context.get('send_email'):
                self.force_quotation_send()
	    #Jagadeesh commented to stop the delivery order creation process
            #order.order_line._action_procurement_create()
        if self.env['ir.values'].get_default('sale.config.settings', 'auto_done_setting'):
            self.action_done()

        #Jagadeesh sep 05 start
        if request.session.get('go_for_additional_beverages') or request.session.get('for_additional_budget'):
            self.project_create = False
        #Jagadeesh sep 05 end


        #Jagadeesh JUL07 start
        #if any(product in [line.product_id.name for line in self.order_line] for product in ['Full Bar','Cocktail Bar']):
	if self.project_create:
            if self.service_required_ids:
                project_name = str(self.partner_id.name)+' : ' +str(self.service_required_ids[0].name)+'-'+str(self.time_start)
            else:
                project_name = str(self.partner_id.name)+' : '+str(self.service_required_ids.name)+'-'+str(self.time_start)
	    project_number = self.env['ir.sequence'].next_by_code('project.project')
            #project = self.env['project.project'].create({'name':project_name,'sale_order_id':self.id,'near_thirst_dep':self.near_thirst_dep,'function_type':self.function_type,'no_of_people':self.no_of_people,'service_required_ids':[[6, False, [tag.id for tag in self.service_required_ids if tag]]],'bars':self.bars,'time_start':self.time_start,'time_end':self.time_end,'function_venue':self.function_venue,'budget_amt':self.budget_amt,'partner_id':self.partner_id.id,'project_number':self.env['ir.sequence'].next_by_code('project.project')})
	    project = self.env['project.project'].create({'name':project_number,'sale_order_id':self.id,'near_thirst_dep':self.near_thirst_dep,'function_type':self.function_type,'no_of_people':self.no_of_people,'service_required_ids':[[6, False, [tag.id for tag in self.service_required_ids if tag]]],'bars':self.bars,'time_start':self.time_start,'time_end':self.time_end,'function_venue':self.function_venue,'budget_amt':self.budget_amt,'partner_id':self.partner_id.id,'project_number':project_number,'division_ids':[[6,0,[div.id for div in self.division_ids]]] })

            if project:
		account_analytic_obj = self.env['account.analytic.account'].search([('name','=',project.name)],limit=1)
                account_analytic_obj.division_ids = [[6,0,[div.id for div in project.division_ids]]]
                if project.budget_amt:
                    bev_budget_obj = self.env['beverage.budget'].create({'budget_amount':project.budget_amt,'req_partner_id':self.partner_id.id,'date_req':str(datetime.now()),'project_id':project.id})
                bev_product_ids = [obj.product_id.id for obj in self.env['beverages'].search([]) ]
                self.project_project_id = project.id

                for data in self.order_line:
                    if data.product_id.product_tmpl_id.id in bev_product_ids:
                        beverage_menu_id = self.env['beverages'].search([('product_id','=',data.product_id.product_tmpl_id.id)]).id
                        self.env['beverages.selection'].create({'project_id':project.id,'beverage_menu_id':beverage_menu_id,'product_id':data.product_id.product_tmpl_id.id,'creation_date':str(datetime.now())})
                    #to update classification/equipment tab
                    if data.product_id.classification in ['consumable','equipment']:
                        clsf_vals = {   'product_id':data.product_id.id,
                                        'product_code':data.product_id.default_code,
                                        'qty_required':data.product_uom_qty,
                                        'classification':data.product_id.classification,
                                        'on_hand':data.product_id.qty_available,
                                        'forecasted':data.product_id.virtual_available,
                                    }
                        if data.product_id.classification == 'consumable':
                            clsf_vals.update({'consume_project_id':project.id})
                        else:
                            clsf_vals.update({'equipment_project_id':project.id})
                        clsf_obj = self.env['product.classification.lines'].create(clsf_vals)


                    #to create bar materials
                    mrp_bom_obj = self.env['mrp.bom'].search([('product_tmpl_id','=',data.product_id.product_tmpl_id.id)])
                    project.product_bom_ids = [(0,0,{'product_code':line.product_id.default_code,'product_id':line.product_id.id,'classification':line.product_id.classification,'product_qty':line.product_qty,'on_hand':line.product_id.qty_available,'forecasted':line.product_id.virtual_available,'product_uom_id':line.product_uom_id.id}) for line in mrp_bom_obj.bom_line_ids]

	self.send_confirmation_email()
        return True

    '''@api.model
    def get_today_date(self):
        return date.today()'''

    @api.multi
    def _prepare_invoice(self):
        res = super(SaleOrder,self)._prepare_invoice()
        if self.project_project_id:
            res.update({'inv_project_id':self.project_project_id.id})
	res.update({'division_ids':[[6,0,[div.id for div in self.division_ids]]] })
        return res

    @api.multi
    def goto_beverages_selection(self):
	    if 'Cocktail Bar' in [line.product_id.name for line in self.order_line]:
		bar = 'cocktail_bar'
	    elif 'Full Bar' in [line.product_id.name for line in self.order_line]:
		bar = 'full_bar'
	    else:
		bar = False
	
	    if bar and self.project_project_id:
                return {
            	'type': 'ir.actions.act_url',
           	'url':   '/beverage_selection/%s/%s/standard'%(bar,self.project_project_id.id),
            	'target': 'new',
            	}
            else:
                raise ValidationError("Can't go for beverage selection")


    @api.multi
    def send_confirmation_email(self):
        ''' to trigger quotation confirmation email with report attachment '''
        email_from = "info@thirst.za.com"
        email_to = self.partner_id and self.partner_id.email or ''
        template = 'confirmation_mail_new'
        try:
            template_id = template and self.env['ir.model.data'].get_object_reference('kt_thirst_customization',template)[1]
            template_obj = template_id and self.env['mail.template'].browse(template_id) or False
        except Exception,e:
            template_id = False
        if template_id and email_to:
            template_obj.write({'email_to':email_to, 'email_from':email_from})
            send_mail = template_obj.with_context({'type':'ir.attachment.type'}).send_mail(self.id,force_send=True)
        return True

    def get_beverage_selection_url(self):
        cocktail_bar = False
        full_bar = False
        #go_for_selection = False 
        selection_type = False
        url = False
        for order in self.order_line:
            if order.product_id.name == 'Cocktail Bar':
                cocktail_bar = True
            elif order.product_id.name == 'Full Bar':
                full_bar = True
        if cocktail_bar:
                #go_for_selection = True
                selection_type = 'cocktail_bar'
                url = '/beverage_selection/cocktail_bar/%s/standard'%self.project_project_id.id
        elif full_bar:
                selection_type = 'full_bar'
                #go_for_selection = True
                url = '/beverage_selection/full_bar/%s/standard'%self.project_project_id.id
        return {'type':selection_type,'url':url}


    #Jagadeesh JUL19 start 
    @api.multi
    def action_cancel(self):
         view_id = self.env['ir.model.data'].get_object_reference('kt_thirst_customization','quotation_cancel_form')[1]
         return {
            'name':'Quotation Cancel Reason',
            'nodestroy':True,
            'search_view_id':view_id,
            'view_mode':'form',
            'view_type':'form',
            'res_model':'quotation.cancel',
            'type':'ir.actions.act_window',
            'target':'new',
            }
    #Jagadeesh JUL19 end    

    @api.multi
    def print_quotation(self):
        return self.env['report'].get_action(self, 'kt_thirst_customization.report_sale_order')

    @api.multi
    def open_quotation(self):
        self.write({'quote_viewed': True})
        request.session['from_quote'] = True
        return {
            'type': 'ir.actions.act_url',
            'target': 'self',
            'url': '/quote/%s/%s' % (self.id, self.access_token)
        }



    @api.multi
    def action_quotation_send(self):
        '''
        This function opens a window to compose an email, with the edi sale template message loaded by default
        '''
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = ir_model_data.get_object_reference('kt_thirst_customization', 'email_template_edi_sale_new')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = dict()
        ctx.update({
            'default_model': 'sale.order',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': True,
            'custom_layout': "sale.mail_template_data_notification_email_sale_order"
        })
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }






class QuotaionCancel(models.Model):
    _name = 'quotation.cancel'

    lost_reason_id = fields.Many2one('crm.lost.reason','Cancel Reason')
    lost_reason = fields.Text('Additional comments for cancel reason ')
    required_reason = fields.Boolean('Required Reason ?')


    @api.onchange('lost_reason_id')
    def onchange_lost_reason(self):
        if self.lost_reason_id:
            if self.lost_reason_id.name in ['other','Other']:
                self.required_reason = True
            else:
                self.required_reason = False
        else:
            self.required_reason = False

    @api.multi
    def submit_reason(self):
        if self.lost_reason_id:
            sale_order_id = self.env.context.get('active_id')
            sale_order_obj = self.env['sale.order'].browse(sale_order_id)
            sale_order_obj.lost_reason_id = self.lost_reason_id.id
            sale_order_obj.lost_reason = self.lost_reason
            sale_order_obj.required_reason = self.required_reason

            sale_order_obj.state = 'cancel'
        return True



class ServiceRequired(models.Model):
    _name = 'service.required'

    name = fields.Char('Service')
    project_id = fields.Many2one('project.project',string="Project")


class DivisionDivision(models.Model):
    _name = 'division.division'

    name = fields.Char('Division')



class SaleQuoteLine(models.Model):
    _inherit = 'sale.quote.line'

    hours = fields.Integer('Hours',default=1)
    days = fields.Integer('Days',default=1)

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    project_id = fields.Many2one('project.project','Project')

    wharehouse_in = fields.Float('Wharehouse In')
    wharehouse_out = fields.Float('Wharehouse Out')
    event_open = fields.Float('Event Opening')
    event_close = fields.Float('Event Closing')
    variance = fields.Float(compute="_get_variance",string="Variance",store=True)
    #variance = fields.Float(string="Variance")
    hours = fields.Float('Hours',default=1.00)
    days = fields.Float('Days',default=1.00)


    @api.multi
    @api.onchange('product_id')
    def product_id_change(self):
        res = super(SaleOrderLine,self).product_id_change()
        self.name = self.product_id.name


    @api.multi
    def write(self,vals):
        if request.session.has_key('from_quote') and request.session['from_quote']:
                vals = {}

        return super(SaleOrderLine,self).write(vals)



    @api.multi
    def writeeeeeee(self,vals):
        price_unit, product_uom_qty, product_uom = self.price_unit, self.product_uom_qty,self.product_uom

        if self.env.context.get('website_id'):
	    if self.order_id.partner_id.name != 'Public user':
                vals = {'price_unit':price_unit,'product_uom_qty':product_uom_qty,'product_uom':product_uom.id }

        return super(SaleOrderLine,self).write(vals)



    @api.depends('product_uom_qty','wharehouse_in')
    def _get_variance(self):
	for obj in self:
	    obj.variance = obj.product_uom_qty - obj.wharehouse_in

 
    @api.depends('product_uom_qty','hours','days','discount', 'price_unit', 'tax_id')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.tax_id.with_context({'hours':line.hours,'days':line.days}).compute_all(price, line.order_id.currency_id,line.product_uom_qty,product=line.product_id, partner=line.order_id.partner_id)

            line.update({
                'price_tax': taxes['total_included'] - taxes['total_excluded'],
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })

    @api.depends('product_id', 'purchase_price', 'product_uom_qty', 'price_unit','discount','days','hours')
    def _product_margin(self):
	''' for overriding existing processs'''
        for line in self:
            currency = line.order_id.pricelist_id.currency_id
            #line.margin = currency.round(line.price_subtotal - ((line.purchase_price or line.product_id.standard_price) * line.product_uom_qty))
	    #Jagadeesh added
	    price_total = line.product_uom_qty * line.price_unit * line.days * line.hours
	    discount_amount = (line.discount * price_total) / 100
	    price_total = price_total - discount_amount
	    cost_total = line.product_uom_qty * line.purchase_price * line.days * line.hours
	    line.margin = currency.round(price_total - cost_total)


    @api.multi
    def _prepare_invoice_line(self, qty):
        """
        Prepare the dict of values to create the new invoice line for a sales order line.

        :param qty: float quantity to invoice
        """
        self.ensure_one()
        res = {}
        account = self.product_id.property_account_income_id or self.product_id.categ_id.property_account_income_categ_id
        if not account:
            raise UserError(_('Please define income account for this product: "%s" (id:%d) - or for its category: "%s".') %
                (self.product_id.name, self.product_id.id, self.product_id.categ_id.name))

        fpos = self.order_id.fiscal_position_id or self.order_id.partner_id.property_account_position_id
        if fpos:
            account = fpos.map_account(account)

        account_analytic_obj = self.env['account.analytic.account'].search([('name','=',self.order_id.project_project_id.name)],limit=1) #Jaga
	res = {
            'name': self.name,
            'sequence': self.sequence,
            'origin': self.order_id.name,
            'account_id': account.id,
            'price_unit': self.price_unit,
	    #Jagadeesh added
	    'days':self.days,
	    'hours':self.hours,
	    #Jagadeesh end
            'quantity': qty,
            'discount': self.discount,
            'uom_id': self.product_uom.id,
            'product_id': self.product_id.id or False,
            'layout_category_id': self.layout_category_id and self.layout_category_id.id or False,
            'product_id': self.product_id.id or False,
            'invoice_line_tax_ids': [(6, 0, self.tax_id.ids)],
            'account_analytic_id': account_analytic_obj and account_analytic_obj.id or False, #self.order_id.project_id.id,
            'analytic_tag_ids': [(6, 0, self.analytic_tag_ids.ids)],
        }
        return res



class AccounTax(models.Model):
    _inherit = 'account.tax'

    @api.multi
    def compute_all(self, price_unit, currency=None, quantity=1.0, product=None, partner=None):
        if len(self) == 0:
            company_id = self.env.user.company_id
        else:
            company_id = self[0].company_id
        if not currency:
            currency = company_id.currency_id
        taxes = []
        prec = currency.decimal_places

        round_tax = False if company_id.tax_calculation_rounding_method == 'round_globally' else True
        round_total = True
        if 'round' in self.env.context:
            round_tax = bool(self.env.context['round'])
            round_total = bool(self.env.context['round'])

        if not round_tax:
            prec += 5

        base_values = self.env.context.get('base_values')
        hours = self.env.context.get('hours') or 1  #Jagadeesh added
        days = self.env.context.get('days') or 1
        if not base_values:
            total_excluded = total_included = base = round(price_unit * quantity * hours * days, prec) #modified Jagadeesh
        else:
            total_excluded, total_included, base = base_values

        for tax in self.sorted(key=lambda r: r.sequence):
            if tax.amount_type == 'group':
                children = tax.children_tax_ids.with_context(base_values=(total_excluded, total_included, base))
                ret = children.compute_all(price_unit, currency, quantity, product, partner)
                total_excluded = ret['total_excluded']
                base = ret['base'] if tax.include_base_amount else base
                total_included = ret['total_included']
                tax_amount = total_included - total_excluded
                taxes += ret['taxes']
                continue

            tax_amount = tax._compute_amount(base, price_unit, quantity, product, partner)
            if not round_tax:
                tax_amount = round(tax_amount, prec)
            else:
                tax_amount = currency.round(tax_amount)

            if tax.price_include:
                total_excluded -= tax_amount
                base -= tax_amount
            else:
                total_included += tax_amount

            # Keep base amount used for the current tax
            tax_base = base


            if tax.include_base_amount:
                base += tax_amount
            taxes.append({
                'id': tax.id,
                'name': tax.with_context(**{'lang': partner.lang} if partner else {}).name,
                'amount': tax_amount,
                'base': tax_base,
                'sequence': tax.sequence,
                'account_id': tax.account_id.id,
                'refund_account_id': tax.refund_account_id.id,
                'analytic': tax.analytic,
            })

        return {
            'taxes': sorted(taxes, key=lambda k: k['sequence']),
            'total_excluded': currency.round(total_excluded) if round_total else total_excluded,
            'total_included': currency.round(total_included) if round_total else total_included,
            'base': base,
        }
   
class PurchaseOrder(models.Model):
   _inherit = 'purchase.order'

   project_id = fields.Many2one('project.project',string="Project")

   @api.multi
   def button_confirm(self):
        res = super(PurchaseOrder,self).button_confirm()
        for line in self.order_line:
            if line.product_uom.id == line.product_id.uom_id.id:
                purchase_price = line.price_unit
            else:
                uom_diff = round(line.product_id.uom_id.factor / line.product_id.uom_po_id.factor)
                purchase_price = line.price_unit / uom_diff

            if purchase_price > line.product_id.standard_price:
                line.product_id.standard_price = purchase_price

        return res



'''class SelectedBeverages(models.Model):
        _name = 'selected.beverages'
        sale_order_id = fields.Many2one('sale.order',string='Sale Order')
        product_id = fields.Many2one('product.template',string='Products')
        category_id = fields.Many2one('beverages.category',string='Category')
        sub_category_id = fields.Many2one('beverages.sub.category',string='Sub Category')
	product_name = fields.Char(string="Product")
	on_hand = fields.Integer(string="On Hand")#qty_available
	forecasted = fields.Integer(string="Forecasted")#virtual_available
        bev_select_id = fields.Many2one('beverages.selection',string="Beverage Selection") '''
