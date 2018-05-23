from odoo import SUPERUSER_ID
from datetime import datetime,timedelta
import hashlib
import json,simplejson
import urllib2,urllib,httplib
import requests
import xmltodict
import unicodedata
import pycurl
from StringIO import StringIO


from odoo import http
from odoo.http import request



class iPayController(http.Controller):
    @http.route('/shop/cancel_ipay', type='http', csrf=False,website=True,auth='public')
    def cancel_ipay(self, redirect=None,    **post):
	#print 'ipayyyy cancel================',post
	return request.redirect('/shop')
	
    @http.route('/shop/error_ipay', type='http', csrf=False,website=True,auth='public')
    def error_ipay(self, redirect=None,    **post):
	#print 'ipayyy error===============',post
	return request.redirect('/shop')

    @http.route('/shop/success_ipay', type='http', csrf=False,website=True,auth='public')
    def suceess_ipay(self, redirect=None,    **post):
	#print 'ipayyy success===============',post
	name = post['TransactionReference']
	sale_order_obj = request.env['sale.order'].sudo().search([('name','=',name)])
	request.session['sale_last_order_id'] = sale_order_obj.id #Added by Jagadeesh
	#project_obj = request.env['project.project'].sudo().search([('sale_order_id','=',sale_order_obj.id)])
	#request.session['last_project_id'] = project_obj.id
	request.session['last_project_id'] = sale_order_obj.project_project_id.id
	return request.redirect('/shop/confirmation')

    @http.route('/shop/notify_ipay', type='http', csrf=False,website=True,auth='public')
    def notify_payweb(self, redirect=None,    **post):
	#print 'ipayyy notify===============',post
	name = post['TransactionReference']
	status = post['Status']
	sale_order_obj = request.env['sale.order'].sudo().search([('name','=',name)])
	request.session['sale_last_order_id'] = sale_order_obj.id #Added by Jagadeesh	
	tx_obj = request.env['payment.transaction'].sudo().search([('reference','=',name)])
	if status == 'Complete' and sale_order_obj.state in ['draft','sent']:
	    transaction = tx_obj.sudo().write({'state':'done','date_validate':datetime.now(),})
            #sale_order_obj.action_quotation_send()
            action_confirm = sale_order_obj.action_confirm()
            #print 'actn confrm===============',action_confirm
            sale_adv_payment = {'advance_payment_method':'all'}
            advanc_pay_obj = request.env['sale.advance.payment.inv'].sudo().create(sale_adv_payment)
            result = advanc_pay_obj.with_context({'active_ids':[sale_order_obj.id]}).create_invoices()
            #print 'inv create result=================',result
            inv_obj = sale_order_obj.invoice_ids
            result = inv_obj.sudo().signal_workflow('invoice_open')#inv_obj.action_invoice_open()
            #print 'inv open=================',result
	    inv_obj.action_invoice_open()
            account_invoice = inv_obj
            #print 'state ===============',inv_obj.state
            if account_invoice.state != 'paid' and account_invoice.state == 'open':
                #print 'inv====================='
                journal_ids = request.env['account.journal'].sudo().search([('name','=ilike','Cash')],limit=1)
                currency = request.env['res.currency'].sudo().search([('name','=','ZAR')],limit=1)
                method = request.env['account.payment.method'].sudo().search([('name','=','Manual')],limit=1)
                account_payment = {
                    'partner_id': sale_order_obj.partner_id.id,
                    'partner_type':'customer',
                    'journal_id':journal_ids.id,
                    'invoice_ids':[(4,inv_obj.id,0)],
                    'amount':sale_order_obj.amount_total,
                    'communication':inv_obj.number,
                    'currency_id':currency.id,
                    'payment_type':'inbound',
                    'payment_method_id':method.id
                                }
                acc_payment = request.env['account.payment'].sudo().create(account_payment)
                #print 'acc payment ==============',acc_payment
                acc_payment.post()
                #sale_order_obj.action_done()
		sale_order_id = sale_order_obj.id
                sale_order_data = sale_order_obj
                if sale_order_data.project_project_id:
                    inv_obj.inv_project_id = sale_order_data.project_project_id.id
                invoice_id = inv_obj.id
                #test
		request.session['last_project_id'] = sale_order_data.project_project_id.id
                '''if any(product in [line.product_id.name for line in sale_order_data.order_line] for product in ['Full Bar','Cocktail Bar']):
                    if sale_order_data.service_required_ids:
                        project_name = str(inv_obj.partner_id.name)+' : ' +str(sale_order_data.service_required_ids[0].name)+'-'+str(sale_order_data.time_start)
                    else:
                        project_name = str(inv_obj.partner_id.name)+' : '+str(sale_order_data.service_required_ids.name)+'-'+str(sale_order_data.time_start)
                    project = request.env['project.project'].sudo().create({'name':project_name,'sale_order_id':sale_order_id,'invoice_id':invoice_id,'near_thirst_dep':sale_order_data.near_thirst_dep,'function_type':sale_order_data.function_type,'no_of_people':sale_order_data.no_of_people,'service_required_ids':[[6, False, [tag.id for tag in sale_order_data.service_required_ids]]],'bars':sale_order_data.bars,'time_start':sale_order_data.time_start,'time_end':sale_order_data.time_end,'function_venue':sale_order_data.function_venue,'budget_amt':sale_order_data.budget_amt,'partner_id':sale_order_data.partner_id.id,'project_number':request.env['ir.sequence'].sudo().next_by_code('project.project')})
                    request.session['last_project_id'] = project.id
                    if project:
                        if project.budget_amt:
                            bev_budget_obj = request.env['beverage.budget'].sudo().create({'budget_amount':project.budget_amt,'req_partner_id':project.sale_order_id.partner_id.id,'date_req':str(datetime.now()),'project_id':project.id})

                        bev_product_ids = [obj.product_id.id for obj in request.env['beverages'].sudo().search([]) ]
                        sale_order_data.project_project_id = project.id
                        inv_obj.inv_project_id = project.id
                        for data in sale_order_data.order_line:
                            if data.product_id.product_tmpl_id.id in bev_product_ids:

                                beverage_menu_id = request.env['beverages'].sudo().search([('product_id','=',data.product_id.product_tmpl_id.id)]).id
                                request.env['beverages.selection'].sudo().create({'project_id':project.id,'beverage_menu_id':beverage_menu_id,'product_id':data.product_id.product_tmpl_id.id,'creation_date':str(datetime.now())})

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
                                clsf_obj = request.env['product.classification.lines'].sudo().create(clsf_vals)
                            #to create bar materials
                            mrp_bom_obj = request.env['mrp.bom'].sudo().search([('product_tmpl_id','=',data.product_id.product_tmpl_id.id)])
                            project.product_bom_ids = [(0,0,{'product_code':line.product_id.default_code,'product_id':line.product_id.id,'classification':line.product_id.classification,'product_qty':line.product_qty,'on_hand':line.product_id.qty_available,'forecasted':line.product_id.virtual_available,'product_uom_id':line.product_uom_id.id}) for line in mrp_bom_obj.bom_line_ids]'''

	return request.redirect('/shop/payment/validate')

