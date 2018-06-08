# -*- coding: utf-'8' "-*-"
try:
    import simplejson as json
except ImportError:
    import json

import logging
import urlparse

from odoo import models, fields, api, _
from odoo.addons.payment.models.payment_acquirer import ValidationError
from odoo.addons.payment_payu_com.controllers.main import PayuController


_logger = logging.getLogger(__name__)


class AcquirerPayu(models.Model):
    _inherit = 'payment.acquirer'

    provider = fields.Selection(selection_add=[('payu_com', 'payu')])
    payu_email_account = fields.Char('Payu Email ID', required_if_provider='payu_com')
    payu_seller_account = fields.Char('Payu Merchant ID',
            help='The Merchant ID is used to ensure communications coming from Payu are valid and secured.')
    payu_api_username = fields.Char('Rest API Username')
    payu_api_password = fields.Char('Rest API Password')

    def _get_payu_urls(self, environment):
        """ Paypal URLS """
        if environment == 'prod':
            return {
                'payu_form_url': 'https://secure.payu.co.za/service/PayUAPI?wsdl',
            }
        else:
            return {
                'payu_form_url': 'https://staging.payu.co.za/service/PayUAPI?wsdl',
            }

    def _get_providers(self, *args, **kwargs):
        providers = super(AcquirerPayu, self)._get_providers()
        providers.append(('payu_com', 'payu'))
        return providers

    '''payu_email_account = fields.Char('Payu Email ID', required_if_provider='payu_com')
    payu_seller_account = fields.Char('Payu Merchant ID',
            help='The Merchant ID is used to ensure communications coming from Payu are valid and secured.')
    payu_api_username = fields.Char('Rest API Username')
    payu_api_password = fields.Char('Rest API Password')
    provider = fields.Selection(selection_add=[('payu_com', 'payu')])'''

    def _migrate_payu_account(self):
        """ COMPLETE ME """
        self.env.cr.execute('SELECT id, paypal_account FROM res_company')
        res = self.env.cr.fetchall()
        for (company_id, company_payu_account) in res:
            if company_payu_account:
                company_payu_ids = self.search([('company_id', '=', company_id), ('name', 'ilike', 'payu')], limit=1).ids
                if company_payu_ids:
                    self.write(company_payu_ids, {'payu_email_account': company_payu_account})
                else:
                    payu_view = self.env['ir.model.data'].get_object('payment_payu_com', 'payu_button')
                    self.create({
                        'name': 'payu.com',
                        'payu_email_account': company_payu_account,
                        'view_template_id': payu_view.id,
                    })
        return True

    @api.multi
    def payu_com_form_generate_values(self, values):
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        acquirer = self
        payu_tx_values = dict(values)
        payu_tx_values.update({
            'item_name': values['reference'],
            'item_number': values['reference'],
            'amount': values['amount'],
            'currency_code': values['currency'] and values['currency'].name or '',
            'address1': values['partner_address'],
            'city': values.get('partner_city'),
            'country': values.get('partner_country') and values.get('partner_country').code or '',
            'state': values.get('partner_state') and (values.get('partner_state').code or values.get('partner_state').name) or '',
            'email': values.get('partner_email'),
            'zip_code': values.get('partner_zip'),
            'zip_code': values.get('partner_zip'),
            'first_name': values.get('partner_first_name'),
            'last_name': values.get('partner_last_name'),
            'return': '%s' % urlparse.urljoin(base_url, PayuController._return_url),
        })
        if acquirer.fees_active:
            payu_tx_values['handling'] = '%.2f' % payu_tx_values.pop('fees', 0.0)
        if payu_tx_values.get('return_url'):
            payu_tx_values['custom'] = json.dumps({'return_url': '%s' % payu_tx_values.pop('return_url')})
        return payu_tx_values

    def payu_com_get_form_action_url(self):
        acquirer = self
        return self._get_payu_urls(acquirer.environment)['payu_form_url']

class Payu(models.Model):
    _inherit = 'payment.transaction'

#     @api.model
#     def create(self, vals):
#         res = super(Payu, self).create(vals)
#         print '\n\nres>>>>>',res, '\n\n'
#         order_id = res.sale_order_id
#         print '\n\norder_id',order_id
#         account_payment_id = self.env['account.payment'].search([('communication', '=', order_id.name)])
#         print '\n\naccount_payment_id',account_payment_id
#         journal_id = self.env['account.journal'].search([('name', '=', 'FNB - Cheque Account 6208585815143')], limit=1, order="id desc")
#         print '\n\njournal_id', journal_id
#         print '\n\norder_id.payment_tx_id' ,order_id.payment_tx_id
#         if not account_payment_id and journal_id and order_id:
#             print '\n\nin if>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>'
#             account_payment = {
#                     'partner_id': order_id.partner_id.id,
#                     'partner_type': 'customer',
#                     'journal_id': journal_id.id,
#                     #'invoice_ids':[(4,inv_obj.id,0)],
#                     'amount': order_id.amount_total,
#                     'communication': order_id.name,
# #                     'currency_id': currency.id,
#                     'payment_type': 'inbound',
#                     'payment_method_id': journal_id.inbound_payment_method_ids.id,
#                     'payment_transaction_id': order_id.payment_tx_id.id,
#                 }
#             acc_payment_id = self.env['account.payment'].create(account_payment)
#             print '\n\nacc_payment_id', acc_payment_id, '\n\n'
#         return res

    @api.model
    def _payu_form_get_tx_from_data(self, data):
        """ Given a data dict coming from payu, verify it and find the related
        transaction record. """
        reference = data.get('REFERENCE')
        transaction = self.search([('reference', '=', reference)])

        if not transaction:
            error_msg = (_('PayU: received data for reference %s; no order found') % (reference))
            raise ValidationError(error_msg)
        elif len(transaction) > 1:
            error_msg = (_('PayU: received data for reference %s; multiple orders found') % (reference))
            raise ValidationError(error_msg)
        return transaction

    @api.multi
    def _payu_form_get_invalid_parameters(self, data):
        invalid_parameters = []
        if self.acquirer_reference and data.get('PAYUREFERENCE') != self.acquirer_reference:
            invalid_parameters.append(('Transaction Id', data.get('PAYUREFERENCE'), self.acquirer_reference))
        # check what is buyed
        amount = data.get('AMOUNT', 0)
        if int(amount) != int(self.amount * 100):  # payu send amount in cent
            invalid_parameters.append(('Amount', data.get('AMOUNT'), '%.2f' % self.amount))
        if data.get('CURRENCYCODE') != self.currency_id.name:
            invalid_parameters.append(('Currency', data.get('CURRENCYCODE'), self.currency_id.name))
        return invalid_parameters

    @api.multi
    def _payu_form_validate(self, data):
        status = data.get('TRANSACTION_STATUS')
        data = {
            'acquirer_reference': data.get('PAYUREFERENCE'),
            'state_message': data.get('RESULTMESSAGE', ''),
            'date_validate': fields.Datetime.now()
        }
        if status == 'SUCCESSFUL':
            self.write(dict(data, state='done'))
            return True
        elif status == 'PROCESSING':
            self.write(dict(data, state='pending'))
            return True
        elif status == 'FAILED':
            self.write(dict(data, state='error'))
            return False
        elif status == 'NEW':
            self.write(dict(data, state='draft'))
            return True
        else:
            error = _('Payu: feedback error')
            self.write(dict(data, state_message=error, state='error'))
            return False
