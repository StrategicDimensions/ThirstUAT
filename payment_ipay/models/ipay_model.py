# -*- coding: utf-'8' "-*-"

import base64
try:
    import simplejson as json
except ImportError:
    import json
import logging
import urlparse
import werkzeug.urls
import urllib2

from odoo import models, fields,api
from odoo.tools.float_utils import float_compare
import inspect
from datetime import datetime,timedelta
import hashlib
import unicodedata
import pycurl
from StringIO import StringIO


_logger = logging.getLogger(__name__)


class PaymentAcquirer(models.Model):
    _inherit = 'payment.acquirer'

    provider = fields.Selection(selection_add=[('ipay', 'i-pay')])


    @api.multi
    def ipay_form_generate_values(self, values):
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        acquirer = self
        paypal_tx_values = dict(values)
	#date= (datetime.utcnow() + timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S')
        #date1 = datetime.strptime(date,'%Y-%m-%d %H:%M:%S')
	amt = str(values['amount'])
	if amt:
	    if len(amt.split('.')[1]) == 1:
	    	amt = str(amt)+'0'
	sitecode = 'TSTSTE0001'
	country_code = 'ZA'
	currency_code = 'ZAR'
	amount = amt #str(values['amount']) #'1.00'#'50.00' #values['amount']
	trans_ref = values['reference'] #'Test01' #values['reference']
	bank_ref = values['reference'] #'Test02' #values['reference']
	cancel_url = 'http://thirstuat.odoo.co.za/shop/cancel_ipay'
	error_url = 'http://thirstuat.odoo.co.za/shop/error_ipay'
	success_url = 'http://thirstuat.odoo.co.za/shop/success_ipay'
	notify_url = 'http://thirstuat.odoo.co.za/shop/notify_ipay'
	is_test = 'false' #'true' #'false'
	#email = unicodedata.normalize('NFKD',values['partner_email']).encode('ascii','ignore')
	#reference = values['reference'] #unicodedata.normalize('NFKD',values['reference']).encode('ascii','ignore')
	#currency = 'ZAR'#values['currency']
	checksum = str(sitecode)+str(country_code)+str(currency_code)+str(amount)+str(trans_ref)+str(bank_ref)+str(cancel_url)+str(error_url)+str(success_url)+str(notify_url)+str(is_test)+'215114531AFF7134A94C88CEEA48E'
        checksum_hash = hashlib.sha512(checksum.lower()).hexdigest()
	
	
        paypal_tx_values.update({
            'item_name': values['reference'],
            'item_number': values['reference'],
            'amount':amount,
            'currency_code': 'ZAR',#values['currency'] and values['currency'].name or '',
            'address1': values['partner_address'],
            'city': values.get('partner_city'),
            'country': values.get('partner_country') and values.get('partner_country').code or '',
            'state': values.get('partner_state') and (values.get('partner_state').code or values.get('partner_state').name) or '',
            'email': values.get('partner_email'),
            'zip_code': values.get('partner_zip'),
            'zip_code': values.get('partner_zip'),
            'first_name': values.get('partner_first_name'),
            'last_name': values.get('partner_last_name'),
	    'sitecode':sitecode,'country_code':country_code,'currency_code':currency_code,
	    'amount':amount,'trans_ref':trans_ref,'bank_ref':bank_ref,
	    'cancel_url':cancel_url,'error_url':error_url,'success_url':success_url,'notify_url':notify_url,'is_test':is_test,
	    'hash_check':checksum_hash
		})

        if acquirer.fees_active:
            paypal_tx_values['handling'] = '%.2f' % paypal_tx_values.pop('fees', 0.0)
        if paypal_tx_values.get('return_url'):
            paypal_tx_values['custom'] = json.dumps({'return_url': '%s' % paypal_tx_values.pop('return_url')})
        #return values,paypal_tx_values
	return paypal_tx_values
