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
	return request.redirect('/shop')
	
    @http.route('/shop/error_ipay', type='http', csrf=False,website=True,auth='public')
    def error_ipay(self, redirect=None,    **post):
	return request.redirect('/shop')

    @http.route('/shop/success_ipay', type='http', csrf=False,website=True,auth='public')
    def suceess_ipay(self, redirect=None,    **post):
	name = post['TransactionReference']
	sale_order_obj = request.env['sale.order'].sudo().search([('name','=',name)])
	request.session['sale_last_order_id'] = sale_order_obj.id #Added by Jagadeesh
	#project_obj = request.env['project.project'].sudo().search([('sale_order_id','=',sale_order_obj.id)])
	#request.session['last_project_id'] = project_obj.id
	request.session['last_project_id'] = sale_order_obj.project_project_id.id
	return request.redirect('/shop/confirmation')

    @http.route('/shop/notify_ipay', type='http', csrf=False,website=True,auth='public')
    def notify_payweb(self, redirect=None,    **post):
	name = post['TransactionReference']
	status = post['Status']
	sale_order_obj = request.env['sale.order'].sudo().search([('name','=',name)])
	request.session['sale_last_order_id'] = sale_order_obj.id #Added by Jagadeesh	
	tx_obj = request.env['payment.transaction'].sudo().search([('reference','=',name)])
	if status == 'Complete' and sale_order_obj.state in ['draft','sent']:
	    transaction = tx_obj.sudo().write({'state':'done','date_validate':datetime.now(),})
            #sale_order_obj.action_quotation_send()
            action_confirm = sale_order_obj.action_confirm()
            '''sale_adv_payment = {'advance_payment_method':'all'}
            advanc_pay_obj = request.env['sale.advance.payment.inv'].sudo().create(sale_adv_payment)
            result = advanc_pay_obj.with_context({'active_ids':[sale_order_obj.id]}).create_invoices()
            inv_obj = sale_order_obj.invoice_ids
            result = inv_obj.sudo().signal_workflow('invoice_open')#inv_obj.action_invoice_open()
	    inv_obj.action_invoice_open()
            account_invoice = inv_obj
            if account_invoice.state != 'paid' and account_invoice.state == 'open':'''
	    if sale_order_obj.state == 'sale':
                journal_ids = request.env['account.journal'].sudo().search([('name','=','FNB 62085815143')],limit=1)
                currency = request.env['res.currency'].sudo().search([('name','=','ZAR')],limit=1)
                method = request.env['account.payment.method'].sudo().search([('name','=','Manual')],limit=1)
                account_payment = {
                    'partner_id': sale_order_obj.partner_id.id,
                    'partner_type':'customer',
                    'journal_id':journal_ids.id,
                    #'invoice_ids':[(4,inv_obj.id,0)],
                    'amount':sale_order_obj.amount_total,
                    'communication':sale_order_obj.name, #inv_obj.number,
                    'currency_id':currency.id,
                    'payment_type':'inbound',
                    'payment_method_id':method.id,
		    'payment_transaction_id':tx_obj.id,
                                }
                acc_payment = request.env['account.payment'].sudo().create(account_payment)
                acc_payment.post()
                #sale_order_obj.action_done()
		sale_order_id = sale_order_obj.id
                sale_order_data = sale_order_obj
                if sale_order_data.project_project_id:
		    request.session['last_project_id'] = sale_order_data.project_project_id.id

	return request.redirect('/shop/payment/validate')

