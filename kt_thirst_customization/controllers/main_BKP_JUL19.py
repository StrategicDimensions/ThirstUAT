# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import json
import logging
from werkzeug.exceptions import Forbidden
from odoo import SUPERUSER_ID
from odoo import http, tools, _,fields
from odoo.addons.website_mail.controllers.main import _message_post_helper
from odoo.http import request
from odoo.addons.base.ir.ir_qweb.fields import nl2br
from odoo.addons.website.models.website import slug
from odoo.addons.website.controllers.main import QueryURL
from odoo.exceptions import ValidationError
from odoo.addons.website_form.controllers.main import WebsiteForm
from odoo.addons.website_quote.controllers.main import sale_quote
import json
import unicodedata

import odoo.addons.website_sale.controllers.main as website_sale_main
from datetime import datetime


_logger = logging.getLogger(__name__)

PPG = 20  # Products Per Page
PPR = 4   # Products Per Row

class BarExperience(http.Controller):
    @http.route(['/bar/experience'],type='http', auth="public", website=True)
    def bar_experience(self,**post):
	sale_last_order_id = request.session.get('sale_last_order_id')
	project_id = request.session.get('last_project_id')
	project_obj =  request.env['project.project'].sudo().browse(project_id)
	#project_obj = request.env['project.project'].sudo().search([('sale_order_id','=',sale_last_order_id)],limit=1)
	order = request.website.sale_get_order()
	if order:
            confirm = order.sudo().action_confirm()
	    project = project_obj.sudo().write({'order_ids':[(6,0,order.order_line.ids)]})
	    #project = project_obj.sudo().write({'order_ids':[(6,0,order.order_line.ids)],'amount_untaxed':order.amount_untaxed,'amount_tax':order.amount_tax,'amount_total':order.amount_total})
	return request.redirect('/shop/')

class SendSMS(http.Controller):
    @http.route(['/send/sms'],type="http",auth="public",website=True)
    def send_sms_customer(self,**kw):
	pos_session_obj = request.env['pos.session'].sudo().search([('state','=','opened')]) or False
	if pos_session_obj:
	    project = pos_session_obj.project_id or False
	    if project:
		project.sudo().send_sms()
	return request.redirect('/pos/web')

##Raaj
class SaleQuote(sale_quote):

    @http.route("/quote/<int:order_id>/<token>", type='http', auth="public", website=True)
    def view(self, order_id, pdf=None, token=None, message=False, **post):
        # use sudo to allow accessing/viewing orders for public user
        # only if he knows the private token

	#Jagadeesh added
	account_blocked = False
	credit_limit_exceeded = False
	sale_order_obj = request.env['sale.order'].sudo().browse(order_id)
	if sale_order_obj.partner_id.account_type == 'account' and sale_order_obj.partner_id.account_blocked:
	   #return request.render('kt_fts_customization.account_blocked_template',{'sale_rep':sale_order_obj.user_id.name})
	   account_blocked = True
	elif sale_order_obj.partner_id.account_type == 'account' and sale_order_obj.amount_total > sale_order_obj.partner_id.available_credit_amount:
	   #return request.render('kt_fts_customization.credit_limit_template',{'sale_rep':sale_order_obj.user_id.name})
	   credit_limit_exceeded = True
	else:pass
	#Jagadeesh end
        now = fields.Date.today()
        if token:
            Order = request.env['sale.order'].sudo().search([('id', '=', order_id), ('access_token', '=', token)])
            # Log only once a day
            if Order and request.session.get('view_quote') != now:
                request.session['view_quote'] = now
                body = _('Quotation viewed by customer')
                _message_post_helper(res_model='sale.order', res_id=Order.id, message=body, token=token, token_field="access_token", message_type='notification', subtype="mail.mt_note", partner_ids=Order.user_id.partner_id.ids)
        else:
            Order = request.env['sale.order'].search([('id', '=', order_id)])

        if not Order:
            return request.render('website.404')
        request.session['sale_order_id'] = Order.id

        days = 0
        if Order.validity_date:
            days = (fields.Date.from_string(Order.validity_date) - fields.Date.from_string(fields.Date.today())).days + 1
        if pdf:
            pdf = request.env['report'].sudo().with_context(set_viewport_size=True).get_pdf([Order.id], 'website_quote.report_quote')
            pdfhttpheaders = [('Content-Type', 'application/pdf'), ('Content-Length', len(pdf))]
            return request.make_response(pdf, headers=pdfhttpheaders)
        transaction_id = request.session.get('quote_%s_transaction_id' % Order.id)
        if not transaction_id:
            Transaction = request.env['payment.transaction'].sudo().search([('reference', '=', Order.name)])
        else:
            Transaction = request.env['payment.transaction'].sudo().browse(transaction_id)
        values = {
            'quotation': Order,
            'message': message and int(message) or False,
            'option': bool(filter(lambda x: not x.line_id, Order.options)),
            'order_valid': (not Order.validity_date) or (now <= Order.validity_date),
            'days_valid': days,
            'action': request.env.ref('sale.action_quotations').id,
            'breadcrumb': request.env.user.partner_id == Order.partner_id,
            'tx_id': Transaction.id if Transaction else False,
            'tx_state': Transaction.state if Transaction else False,
            'tx_post_msg': Transaction.acquirer_id.post_msg if Transaction else False,
            'need_payment': Order.invoice_status == 'to invoice' and Transaction.state in ['draft', 'cancel', 'error'],
            'token': token,
        }

        if Order.require_payment or values['need_payment']:
            values['acquirers'] = list(request.env['payment.acquirer'].sudo().search([('website_published', '=', True), ('company_id', '=', Order.company_id.id)]))
            extra_context = {
                'submit_class': 'btn btn-primary',
                'submit_txt': _('Pay & Confirm')
            }
            values['buttons'] = {}
            for acquirer in values['acquirers']:
                values['buttons'][acquirer.id] = acquirer.with_context(**extra_context).render(
                    '/',
                    Order.amount_total,
                    Order.pricelist_id.currency_id.id,
                    values={
                        'return_url': '/quote/%s/%s' % (order_id, token) if token else '/quote/%s' % order_id,
                        'type': 'form',
                        'alias_usage': _('If we store your payment information on our server, subscription payments will be made automatically.'),
                        'partner_id': Order.partner_id.id,
                    })
	values.update({'account_blocked':account_blocked,'credit_limit_exceeded':credit_limit_exceeded,'sale_rep':Order.user_id.name,'quote_id':Order.id,'token':token})
        return request.render('website_quote.so_quotation', values)


class PurchaseOrderQuote(http.Controller):

    @http.route("/submit_purchase_order", type='http', auth="public", website=True)
    def view(self,**post):
        sale_order = request.env['sale.order'].sudo().browse(int(post['quotation_id']))
	#sale_order.sudo().write({'client_order_ref':post['po_number']})
	sale_order.sudo().action_confirm()
	sale_order.sudo().write({'client_order_ref':post['po_number'],'state':'sale'})
	sale_order.message_post(attachments=[(post['po_attach'].filename,post['po_attach'].read())])
	#return request.render('kt_fts_customization.purchase_order_update',{})
	return request.render('kt_thirst_customization.so_quotation_inherit',{'quotation':sale_order,'order_valid':True,'message':3})
	
	#return request.redirect('/quote/%s/%s' % (post['po_number'],post['token']))

class BeverageSelection(http.Controller):
		

        @http.route(['/beverage_selection/<bar>/<project>/<selection_type>'],type='http',auth="public", website=True)
        def beverages_products_selection(self,bar,project,selection_type,**post):
	    request.session['view_mode'] = 'grid'
	    return request.redirect('/beverages/%s/%s/%s/products/all'%(bar,project,selection_type))

        @http.route(['/beverages/<bar>/<project>/<selection_type>/products/all'],type='http', auth="public", website=True)
        def products_all_selecton(self,bar,project,selection_type,**post):

                products , standard_products ,premium_products = [],[],[]
                view_mode = request.session['view_mode']
                return_dic = {}
                #if post:
                if True:
                        project_id = int(project)
			project_obj = request.env['project.project'].sudo().browse(project_id)
                        sale_order_id = request.env['project.project'].sudo().browse(project_id).sale_order_id.id
                        if sale_order_id:
                                order = request.env['sale.order'].sudo().browse(sale_order_id)
                                if bar == 'full_bar' and 'Full Bar' in [line.product_id.name for line in order.order_line]:
                                    full_bar_menu = request.env['beverages'].sudo().search([('name','=','Full Bar Beverage Menu')],limit=1)
                                    beverage_menu = full_bar_menu				
                                elif bar == 'cocktail_bar' and 'Cocktail Bar' in [line.product_id.name for line in order.order_line]:
                                    cocktail_bar_menu = request.env['beverages'].sudo().search([('name','=','Cocktail Bar Beverage Menu')],limit=1)
                                    beverage_menu = cocktail_bar_menu
				#to auto select default products
                                for bev_select_obj in project_obj.beverages_selection_ids:
                                    if bev_select_obj.beverage_menu_id.id == beverage_menu.id and not bev_select_obj.selected_beverages_ids:
                                        project_obj.default_beverages_selection(bev_select_obj.id)
                                #end
                        ''' getting all selected beverages of respective bar type and displaying at web page '''
                        all_select_bev_ids,standard_bevs,premium_bevs = [],[],[]
                        standard_bev_dic,premium_bev_dic = {},{}
                        selected_bev_objs = request.env['selected.beverages'].sudo().search([('sale_order_id','=',sale_order_id)])
                        for bev_obj in selected_bev_objs:
                            if bev_obj.bev_select_id.beverage_menu_id.id == beverage_menu.id and bev_obj.prod_type == 'Standard':
                                all_select_bev_ids.append(bev_obj.product_id.id)
                                if bev_obj.sub_category_id.name not in standard_bev_dic.keys():
                                    standard_bev_dic.update({bev_obj.sub_category_id.name:[bev_obj.product_id]})
                                else:
                                    standard_bev_dic[bev_obj.sub_category_id.name].append(bev_obj.product_id)
                            elif bev_obj.bev_select_id.beverage_menu_id.id == beverage_menu.id and bev_obj.prod_type == 'Premium':
                                all_select_bev_ids.append(bev_obj.product_id.id)
                                if bev_obj.sub_category_id.name not in premium_bev_dic.keys():
                                    premium_bev_dic.update({bev_obj.sub_category_id.name:[bev_obj.product_id]})
                                else:
                                    premium_bev_dic[bev_obj.sub_category_id.name].append(bev_obj.product_id)
                        for key in standard_bev_dic.keys():
                            new_dic = {'categ_name':key,'selected_beverages':standard_bev_dic[key]}
                            standard_bevs.append(new_dic)
                        for key in premium_bev_dic.keys():
                            new_dic = {'categ_name':key,'selected_beverages':premium_bev_dic[key]}
                            premium_bevs.append(new_dic)

                        total_premium_amount = 0.0
                        all_premium_products = []
                        for bev in premium_bevs:
                            for product in bev['selected_beverages']:
                                total_premium_amount += product.list_price
                                all_premium_products.append(product.id)
                        request.session.update({'premium_products':{'sale_order_id':sale_order_id,'products':all_premium_products}})
                        ''' getting products based on respective parent and sub caterories'''
			category_seq = []
                        sub_categ_seq_dic = {}
                        if beverage_menu:
                                all_standard_products_dic,all_premium_products_dic = {},{}
                                all_standard_products,all_premium_products,all_standard_products_grid,all_premium_products_grid= [],[],[],[]
				for categ in request.env['beverages.category.rel'].sudo().search([('beverage_id','=',beverage_menu.id)],order="sequence"):
                                    category_seq.append(categ.categ_id.id)
                                for categ in category_seq:
                                    sub_categ_seq_dic.update({categ:[]})
                                for sub_categ in request.env['beverages.sub.category.rel'].sudo().search([('beverage_id','=',beverage_menu.id)],order="sequence"):
                                    for categ in category_seq:
                                        if sub_categ.parent_categ.id == categ:
                                            sub_categ_seq_dic[categ].append(sub_categ.sub_categ_id.id)
                                for line in beverage_menu.beverage_product_ids:
                                    '''if line.prod_type == 'Standard':
                                        if line.sub_categ_id.name in all_standard_products_dic.keys():
                                            all_standard_products_dic[line.sub_categ_id.name].append(line)
                                        else:
                                            all_standard_products_dic.update({line.sub_categ_id.name:[line] })
                                    else:
                                        if line.sub_categ_id.name in all_premium_products_dic.keys():
                                            all_premium_products_dic[line.sub_categ_id.name].append(line)
                                        else:
                                            all_premium_products_dic.update({line.sub_categ_id.name:[line]})'''
				    '''prod_categ_name = str(line.category_id.name)+' > '+str(line.sub_categ_id.name)
				    if line.prod_type == 'Standard':
                                        if prod_categ_name in all_standard_products_dic.keys():
                                            all_standard_products_dic[prod_categ_name].append(line)
                                        else:
                                            all_standard_products_dic.update({prod_categ_name:[line] })
                                    else:
                                        if prod_categ_name in all_premium_products_dic.keys():
                                            all_premium_products_dic[prod_categ_name].append(line)
                                        else:
                                            all_premium_products_dic.update({prod_categ_name:[line]})'''
				    if line.prod_type == 'Standard':
                                        if line.sub_categ_id.id in all_standard_products_dic.keys():
                                            all_standard_products_dic[line.sub_categ_id.id].append(line)
                                        else:
                                            all_standard_products_dic.update({line.sub_categ_id.id:[line] })
                                    else:
                                        if line.sub_categ_id.id in all_premium_products_dic.keys():
                                            all_premium_products_dic[line.sub_categ_id.id].append(line)
                                        else:
                                            all_premium_products_dic.update({line.sub_categ_id.id:[line]})
                                    #updating boolean field of beverage menu product to make it invisible on beverage page once it selected.
                                    if line.product_product_id.id in all_select_bev_ids:
                                        line.button_invisible = True
                                        line.remove_button_visible = True
                                    else:
                                        line.button_invisible = False
                                        line.remove_button_visible = False
                                '''for key in all_standard_products_dic.keys():
				    sub_categ_rel_obj = request.env['beverages.sub.category.rel'].sudo().search([('sub_categ_id','=',key),('beverage_id','=',beverage_menu.id)])	
                                    new_dic = {'categ_name':sub_categ_rel_obj.parent_categ.name,'sub_categ_name':sub_categ_rel_obj.sub_categ_id.name,'max_prod':sub_categ_rel_obj.max_products,'beverages':all_standard_products_dic[key]}
                                    all_standard_products.append(new_dic)
                                for key in all_premium_products_dic.keys():
				    sub_categ_rel_obj = request.env['beverages.sub.category.rel'].sudo().search([('sub_categ_id','=',key),('beverage_id','=',beverage_menu.id)])      
                                    new_dic = {'categ_name':sub_categ_rel_obj.parent_categ.name,'sub_categ_name':sub_categ_rel_obj.sub_categ_id.name,'max_prod':sub_categ_rel_obj.max_products,'beverages':all_premium_products_dic[key]}
                                    all_premium_products.append(new_dic)'''

				for categ in category_seq:
                                    for sub_categ in sub_categ_seq_dic[categ]:
                                        sub_categ_rel_obj = request.env['beverages.sub.category.rel'].sudo().search([('sub_categ_id','=',sub_categ),('beverage_id','=',beverage_menu.id)])
                                        if sub_categ in all_standard_products_dic.keys():
                                            new_dic = {'categ_name':sub_categ_rel_obj.parent_categ.name,'sub_categ_name':sub_categ_rel_obj.sub_categ_id.name,'max_prod':sub_categ_rel_obj.max_products,'beverages':all_standard_products_dic[sub_categ]}
                                            all_standard_products.append(new_dic)
                                        if sub_categ in all_premium_products_dic.keys():
                                            new_dic = {'categ_name':sub_categ_rel_obj.parent_categ.name,'sub_categ_name':sub_categ_rel_obj.sub_categ_id.name,'max_prod':sub_categ_rel_obj.max_products,'beverages':all_premium_products_dic[sub_categ]}
                                            all_premium_products.append(new_dic)

                                all_standard_products_grid = all_standard_products
                                all_premium_products_grid = all_premium_products
                                #to display 5 for each row
                                for bev_products in all_standard_products_grid:
                                    bev_products['beverages'] = [bev_products['beverages'][x:x+5] for x in xrange(0, len(bev_products['beverages']), 5)]

                                for bev_products in all_premium_products_grid:
                                    bev_products['beverages'] = [bev_products['beverages'][x:x+5] for x in xrange(0, len(bev_products['beverages']), 5)]
                                return_dic = {  'project_id':project_id,'view_all':False,
                                                'standard_selected_bevs':standard_bevs,'premium_selected_bevs':premium_bevs,
                                                'total_premium_amount':total_premium_amount,
                                                'finished':True,'beverage_menu':beverage_menu.id,'bar':bar,'view_mode':view_mode,
						'selection_type':selection_type,
			                        'all_standard_products_list':all_standard_products,
                                                'all_premium_products_list':all_premium_products,
                                                'all_standard_products_grid':all_standard_products_grid,
                                                'all_premium_products_grid':all_premium_products_grid
						 }
					    
                return request.render('kt_thirst_customization.beverage_selection_page',return_dic)

        @http.route(['/products/view/grid'],type='http', auth="public",csrf=False,website=True)
        def product_view_grid(self,**post):
                request.session.update({'view_mode':'grid'})
                return json.dumps({'message':'','flag':1})

        @http.route(['/products/view/list'],type='http', auth="public",csrf=False,website=True)
        def product_view_list(self,**post):
                request.session.update({'view_mode':'list'})
                return json.dumps({'message':'','flag':1})
	
	@http.route(['/beverage_selection/<bar>/complete/<project>'],type='http',auth="public", website=True)
        def beverage_selection_complete(self,bar,project,**post):
	    #project_id = request.session['last_project_id']
	    project_id = int(project)
	    request.session.update({'last_project_id':project_id})
            project_obj = request.env['project.project'].sudo().browse(project_id)
	    sale_order_obj = project_obj.sale_order_id
	    if bar == 'full_bar':
		'''sending email to customer after completion of full bar beverages selection'''
		project_obj.send_email_fullbar_beverages_selection()
		bev_menu_id = request.env['beverages'].sudo().search([('name','=','Full Bar Beverage Menu')])
		#sale_order_obj.full_bar_selection_completed = True
	    else:
		'''sending email to customer after completion of cocktail bar beverages selection'''
		project_obj.send_email_cocktailbar_beverages_selection()
		bev_menu_id = request.env['beverages'].sudo().search([('name','=','Cocktail Bar Beverage Menu')])
		#sale_order_obj.cocktail_bar_selection_completed = True	
	    bev_select_obj = request.env['beverages.selection'].sudo().search([('project_id','=',project_id),('beverage_menu_id','=',bev_menu_id.id)])
            bev_select_obj.is_completed = True
            bev_select_obj.date_completed = datetime.now()
	    cocktail_bar = False

	    #updating boolean field which using for select button visibility for each product on beverage page
	    request.cr.execute("update beverage_products set button_invisible = 'f' where button_invisible = 't'  ")
	    request.cr.execute("update beverage_products set remove_button_visible = 'f' where remove_button_visible = 't'  ")

	    #If there are premium products adding them to shop cart by creating sale order
	    premium_products = request.session['premium_products']['products']
	    if premium_products:
		new_premium_products = []		
		for product in premium_products:
		    product_obj = request.env['product.product'].sudo().search([('product_tmpl_id','=',product)])
		    new_premium_products.append(product_obj)
		if new_premium_products:
		    sale_obj = request.env['sale.order'].sudo().create({'partner_id':sale_order_obj.partner_id.id,'project_project_id':project_id,'premium_beverages':True,'beverage_menu_id':bev_menu_id.id,'order_line':[(0,0,{'product_id':product.id,'product_uom':product.uom_id.id}) for product in new_premium_products]})
		    request.session.update({'sale_order_id':sale_obj.id})
		    return request.redirect('/shop/cart')

	    #If there are no premium products then a confirmation page will be redirected		
	    if not premium_products and bar == 'full_bar':
	        for line in sale_order_obj.order_line:
		    if line.product_id.name == 'Cocktail Bar':
		        cocktail_bar = True		    
            return request.render('kt_thirst_customization.beverages_selection_complete',{'cocktail_bar':cocktail_bar,'project_id':project_id})


	@http.route(['/add/<project>/<beverage_menu>/<product>'],type='http', auth="public",csrf=False,website=True)
        def add_product(self,project,beverage_menu,**post):
                products = []	
		bev_menu_product_id = post['bev_menu_product_id']
		bev_menu_prod_obj = request.env['beverage.products'].sudo().browse(int(bev_menu_product_id))
		product_id = post['product_id']
		sub_category_id = post['sub_categ_id']
		prod_type = post['prod_type']	
		count = 0
                if post:
                    #project_id = request.session['last_project_id']
		    project_id = int(project)
                    sale_order_id = request.env['project.project'].sudo().browse(project_id).sale_order_id.id
		    #to apply validation for limit the number of standard beverages selection
		    if prod_type == 'Standard':
			bev_menu_obj = request.env['beverages'].sudo().browse(int(beverage_menu))
			sub_categ_obj = bev_menu_obj.beverage_sub_category_ids.filtered(lambda x: x.sub_categ_id.id == int(sub_category_id))
			max_products = sub_categ_obj and sub_categ_obj.max_products or 0

		        added_products = request.env['selected.beverages'].sudo().search([('sale_order_id','=',sale_order_id),('sub_category_id','=',int(sub_category_id)),('bev_select_id.beverage_menu_id','=',int(beverage_menu)),('prod_type','=','Standard')])
		        if len(added_products) >= max_products:
			    return json.dumps({'message':'cannot add mora than two products for same sub category','flag':0})
		    #creating record once we selected the beverage by click on select/purchase button
		    bev_select_obj = request.env['beverages.selection'].sudo().search([('project_id','=',project_id),('beverage_menu_id','=',int(beverage_menu))])
		    product_obj = request.env['product.template'].sudo().browse(int(product_id))
		    sub_categ_obj = request.env['beverages.sub.category'].sudo().browse(int(sub_category_id))
		    obj = request.env['selected.beverages'].sudo().create({'sale_order_id':sale_order_id,'category_id':sub_categ_obj.parent_categ.id,'sub_category_id':sub_category_id,'product_id':product_id,'product_name':product_obj.name,'product_code':product_obj.default_code,'prod_type':prod_type,'classification':product_obj.classification,'on_hand':product_obj.qty_available,'forecasted':product_obj.virtual_available,'variance':-(product_obj.qty_available),'bev_select_id':bev_select_obj.id})
		    dup_bev_prod,dup_selected_bev_obj = False,False
                    if obj.prod_type == 'Standard':
                        obj.standard_bev_select_id = bev_select_obj.id
			#to get duplicated product from beverage menu products with diff product type
			dup_bev_prod = request.env['beverage.products'].sudo().search([('beverage_id','=',int(beverage_menu)),('product_product_id','=',bev_menu_prod_obj.product_product_id.id),('category_id','=',bev_menu_prod_obj.category_id.id),('sub_categ_id','=',bev_menu_prod_obj.sub_categ_id.id),('prod_type','=','Premium')],limit=1)
                    elif obj.prod_type == 'Premium':
                        obj.premium_bev_select_id = bev_select_obj.id
			#to get duplicated product from beverage menu products with diff product type
			dup_bev_prod = request.env['beverage.products'].sudo().search([('beverage_id','=',int(beverage_menu)),('product_product_id','=',bev_menu_prod_obj.product_product_id.id),('category_id','=',bev_menu_prod_obj.category_id.id),('sub_categ_id','=',bev_menu_prod_obj.sub_categ_id.id),('prod_type','=','Standard')],limit=1)

		    #to create object with duplicated beverae menu product
                    if dup_bev_prod:
                            product_obj = dup_bev_prod.product_product_id
                            dup_selected_bev_obj = request.env['selected.beverages'].sudo().create({'sale_order_id':sale_order_id,'category_id':sub_categ_obj.parent_categ.id,'sub_category_id':sub_category_id,'product_id':product_obj.id,'product_name':product_obj.name,'product_code':product_obj.default_code,'prod_type':dup_bev_prod.prod_type,'classification':product_obj.classification,'on_hand':product_obj.qty_available,'forecasted':product_obj.virtual_available,'variance':-(product_obj.qty_available),'bev_select_id':bev_select_obj.id})
		    
		            if dup_selected_bev_obj.prod_type == 'Standard':
                                dup_selected_bev_obj.standard_bev_select_id = bev_select_obj.id
			    elif dup_selected_bev_obj.prod_type == 'Premium':
	                        dup_selected_bev_obj.premium_bev_select_id = bev_select_obj.id
		    #end
			
		return json.dumps({'message':'Added to cart','flag':1})


        @http.route(['/remove/<project>/<beverage_menu>/<product>'],type='http', auth="public",csrf=False,website=True)
        def remove_product(self,project,beverage_menu,**post):
                products = []
                bev_menu_product_id = post['bev_menu_product_id']
                product_id = post['product_id']
                sub_category_id = post['sub_categ_id']
                prod_type = post['prod_type']
		flag = 0
                if post:
                    project_id = int(project)
                    sale_order_id = request.env['project.project'].sudo().browse(project_id).sale_order_id.id
                    #deleting record once we selected the beverage by click on remove button
                    bev_select_obj = request.env['beverages.selection'].sudo().search([('project_id','=',project_id),('beverage_menu_id','=',int(beverage_menu))])
                    product_obj = request.env['product.template'].sudo().browse(int(product_id))
                    sub_categ_obj = request.env['beverages.sub.category'].sudo().browse(int(sub_category_id))
		    obj = request.env['selected.beverages'].sudo().search([('sale_order_id','=',sale_order_id),('product_id','=',int(product_id)),('bev_select_id','=',bev_select_obj.id)])



		    result = obj.sudo().unlink()
		    if result:
			flag = 1
			
		return json.dumps({'message':'','flag':flag})

class WebsiteSale(website_sale_main.WebsiteSale):


    @http.route(['/shop/confirmation'], type='http', auth="public", website=True)
    def payment_confirmation(self, **post):
        """ End of checkout process controller. Confirmation is basically seing
        the status of a sale.order. State at this point :

         - should not have any context / session info: clean them
         - take a sale.order id, because we request a sale.order and are not
           session dependant anymore
        """
	#Jagadeesh start
	''' to display buttons on shop confirmation page '''
	full_bar = False
	cocktail_bar = False
	project_id = request.session.get('last_project_id')
	project_obj = request.env['project.project'].sudo().browse(project_id)
	sale_obj = project_obj.sale_order_id
	full_bar_menu_id = request.env['beverages'].sudo().search([('name','=','Full Bar Beverage Menu')],limit=1).id
	cocktail_bar_menu_id = request.env['beverages'].sudo().search([('name','=','Cocktail Bar Beverage Menu')],limit=1).id
	fullbar_bev_select_obj = request.env['beverages.selection'].sudo().search([('project_id','=',project_id),('beverage_menu_id','=',full_bar_menu_id)],limit=1)
	cocktail_bev_select_obj = request.env['beverages.selection'].sudo().search([('project_id','=',project_id),('beverage_menu_id','=',cocktail_bar_menu_id)],limit=1)
	if fullbar_bev_select_obj and not fullbar_bev_select_obj.is_completed:
	    full_bar = True
	elif cocktail_bev_select_obj and not cocktail_bev_select_obj.is_completed:
	    cocktail_bar = True

	#Jagadeesh end
        sale_order_id = request.session.get('sale_last_order_id')
        if sale_order_id:
            order = request.env['sale.order'].sudo().browse(sale_order_id)
	    #Jagadeesh start
	    ''' to update the quantity selected for premium products into project form selected beverages section ''' 
	    if order.premium_beverages:
	        product_dic = {}
	        for line in order.order_line:
	 	    product_dic.update({line.product_id.product_tmpl_id.id : line.product_uom_qty})
	
	        beverage_selection_obj = request.env['beverages.selection'].sudo().search([('project_id','=',project_obj.id),('beverage_menu_id','=',order.beverage_menu_id.id)])	
	        for beverage in beverage_selection_obj.selected_beverages_ids:
		    if beverage.prod_type == 'Premium':
		        beverage.qty_required = product_dic[beverage.product_id.id]
	    #Jagadeesh end
			
	
            return request.render("website_sale.confirmation", {'order': order,'full_bar':full_bar,'cocktail_bar':cocktail_bar,'project_id':project_id})
        else:
            return request.redirect('/shop')

