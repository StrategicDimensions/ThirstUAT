from odoo import fields,models,api,_
from odoo.tools.misc import formatLang



class AccountInvoice(models.Model):
    _inherit = 'account.invoice'


    inv_project_id = fields.Many2one('project.project',string="Project")
    bill_project_id = fields.Many2one('project.project',string="Project")
    division_ids = fields.Many2many('division.division','inv_div_rel','inv_id','div_id',string="Division")

    @api.multi
    def get_taxes_values(self):
        tax_grouped = {}
        for line in self.invoice_line_ids:
            price_unit = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
	    #Jagadeesh added hours and days
            taxes = line.invoice_line_tax_ids.with_context({'hours':line.hours,'days':line.days}).compute_all(price_unit, self.currency_id, line.quantity, line.product_id, self.partner_id)['taxes']
            for tax in taxes:
                val = self._prepare_tax_line_vals(line, tax)
                key = self.env['account.tax'].browse(tax['id']).get_grouping_key(val)

                if key not in tax_grouped:
                    tax_grouped[key] = val
                else:
                    tax_grouped[key]['amount'] += val['amount']
                    tax_grouped[key]['base'] += val['base']
        return tax_grouped

    @api.multi
    def invoice_print(self):
        """ Print the invoice and mark it as sent, so that we can see more
            easily the next step of the workflow
        """
        self.ensure_one()
        self.sent = True
        return self.env['report'].get_action(self, 'kt_thirst_customization.report_invoice_new')


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    hours = fields.Float('Hours',default=1.00)
    days = fields.Float('Days',default=1.00)
    
    
    @api.model
    def create(self, vals):
        res = super(AccountInvoiceLine, self).create(vals)
        if res.invoice_id.origin and not res.account_analytic_id:
            sale_order_id = self.env['sale.order'].search([('name', '=', res.invoice_id.origin)], limit=1, order="id desc")
            pos_order_id = self.env['pos.order'].search([('name', '=', res.invoice_id.origin)], limit=1, order="id desc")
            if sale_order_id and sale_order_id.project_project_id:
                analytic_accnt_obj = self.env['account.analytic.account'].search([('name','=',sale_order_id.project_project_id.name)],limit=1)
            if pos_order_id and pos_order_id.project_id:
                analytic_accnt_obj = self.env['account.analytic.account'].search([('name','=',pos_order_id.project_id.name)],limit=1)
            res.update({'account_analytic_id': analytic_accnt_obj.id if analytic_accnt_obj else False})
        return res

    @api.one
    @api.depends('price_unit', 'discount', 'invoice_line_tax_ids', 'quantity',
        'product_id', 'invoice_id.partner_id', 'invoice_id.currency_id', 'invoice_id.company_id','hours','days')
    def _compute_price(self):
        currency = self.invoice_id and self.invoice_id.currency_id or None
        price = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
        taxes = False
        if self.invoice_line_tax_ids:
	    #Jagadeesh added hours and days
            taxes = self.invoice_line_tax_ids.with_context({'hours':self.hours,'days':self.days}).compute_all(price, currency, self.quantity, product=self.product_id, partner=self.invoice_id.partner_id)
        self.price_subtotal = price_subtotal_signed = taxes['total_excluded'] if taxes else self.quantity * price
        if self.invoice_id.currency_id and self.invoice_id.currency_id != self.invoice_id.company_id.currency_id:
            price_subtotal_signed = self.invoice_id.currency_id.compute(price_subtotal_signed, self.invoice_id.company_id.currency_id)
        sign = self.invoice_id.type in ['in_refund', 'out_refund'] and -1 or 1
        self.price_subtotal_signed = price_subtotal_signed * sign


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"


    @api.multi
    def _create_invoice(self, order, so_line, amount):
        inv_obj = self.env['account.invoice']
        ir_property_obj = self.env['ir.property']

        account_id = False
        if self.product_id.id:
            account_id = self.product_id.property_account_income_id.id
        if not account_id:
            inc_acc = ir_property_obj.get('property_account_income_categ_id', 'product.category')
            account_id = order.fiscal_position_id.map_account(inc_acc).id if inc_acc else False
        if not account_id:
            raise UserError(
                _('There is no income account defined for this product: "%s". You may have to install a chart of account from Accounting app, settings menu.') %
                (self.product_id.name,))

        if self.amount <= 0.00:
            raise UserError(_('The value of the down payment amount must be positive.'))
        if self.advance_payment_method == 'percentage':
            amount = order.amount_untaxed * self.amount / 100
            name = _("Down payment of %s%%") % (self.amount,)
        else:
            amount = self.amount
            name = _('Down Payment')
        if order.fiscal_position_id and self.product_id.taxes_id:
            tax_ids = order.fiscal_position_id.map_tax(self.product_id.taxes_id).ids
        else:
            tax_ids = self.product_id.taxes_id.ids

        account_analytic_obj = self.env['account.analytic.account'].search([('name','=',order.project_project_id.name)],limit=1) #Jagadeesh
        invoice = inv_obj.create({
            'name': order.client_order_ref or order.name,
            'origin': order.name,
            'type': 'out_invoice',
            'reference': False,
            'account_id': order.partner_id.property_account_receivable_id.id,
            'partner_id': order.partner_invoice_id.id,
            'partner_shipping_id': order.partner_shipping_id.id,
	    'inv_project_id':order.project_project_id and order.project_project_id.id or False, #Jagadeesh
	    'division_ids':[[6,0,[div.id for div in order.division_ids]]], #Jagadeesh
            'invoice_line_ids': [(0, 0, {
                'name': name,
                'origin': order.name,
                'account_id': account_id,
                'price_unit': amount,
                'quantity': 1.0,
                'discount': 0.0,
                'uom_id': self.product_id.uom_id.id,
                'product_id': self.product_id.id,
                'sale_line_ids': [(6, 0, [so_line.id])],
                'invoice_line_tax_ids': [(6, 0, tax_ids)],
                'account_analytic_id': account_analytic_obj and account_analytic_obj.id or False, #order.project_id.id or False,
            })],
            'currency_id': order.pricelist_id.currency_id.id,
            'payment_term_id': order.payment_term_id.id,
            'fiscal_position_id': order.fiscal_position_id.id or order.partner_id.property_account_position_id.id,
            'team_id': order.team_id.id,
            'comment': order.note,
        })
        invoice.compute_taxes()
        invoice.message_post_with_view('mail.message_origin_link',
                    values={'self': invoice, 'origin': order},
                    subtype_id=self.env.ref('mail.mt_note').id)
        return invoice


class AccountReportContextCommon(models.TransientModel):
    _inherit = "account.report.context.common"

    new_filter_type = fields.Char('New Filter Type')


class report_account_aged_partner(models.AbstractModel):
    _inherit = "account.aged.partner"
    _description = "Aged Partner Balances"


    @api.model
    def _lines(self, context, line_id=None):
	''' this method overrided '''
        lines = []

        results, total, amls = self.env['report.account.report_agedpartnerbalance']._get_partner_move_lines([self._context['account_type']], self._context['date_to'], 'posted', 30)
	#Jaagdeesh start
        new_filter_type = self._context.get('new_filter_type')
        staff_ids = self.env['hr.employee'].search([]).mapped('partner_id').ids
        new_results = []
        new_total = [0.0,0.0,0.0,0.0,0.0,0.0,0.0]
        if new_filter_type in ['vendors','staff'] and self._context['account_type'] == 'payable':
            if new_filter_type == 'vendors':
                for res in results:
                    if res['partner_id'] not in staff_ids:
                        new_results.append(res)
            else:
                for res in results:
                    if res['partner_id'] in staff_ids:
                        new_results.append(res)
            results = new_results
            for res in new_results:
                new_total[0] += res['direction']
                for i,j in zip(range(5,0,-1),range(5)):
                    new_total[i] += res[str(j)]
                new_total[6] += res['total']
            total = new_total
        #Jagadesh end
        for values in results:
            if line_id and values['partner_id'] != line_id:
                continue
            vals = {
                'id': values['partner_id'],
                'name': values['name'],
                'level': 0,
                'type': 'partner_id',
                'footnotes': context._get_footnotes('partner_id', values['partner_id']),
                'columns': [values['direction'], values['4'], values['3'], values['2'], values['1'], values['0'], values['total']],
                'trust': values['trust'],
                'unfoldable': True,
                'unfolded': values['partner_id'] in context.unfolded_partners.ids,
            }
            vals['columns'] = map(self._format, vals['columns'])
            lines.append(vals)
            if values['partner_id'] in context.unfolded_partners.ids:
                for line in amls[values['partner_id']]:
                    aml = line['line']
                    vals = {
                        'id': aml.id,
                        'name': aml.move_id.name if aml.move_id.name else '/',
                        'move_id': aml.move_id.id,
                        'action': aml.get_model_id_and_name(),
                        'level': 1,
                        'type': 'move_line_id',
                        'footnotes': context._get_footnotes('move_line_id', aml.id),
                        'columns': [line['period'] == 6-i and self._format(line['amount']) or '' for i in range(7)],
                    }
                    lines.append(vals)
                vals = {
                    'id': values['partner_id'],
                    'type': 'o_account_reports_domain_total',
                    'name': _('Total '),
                    'footnotes': self.env.context['context_id']._get_footnotes('o_account_reports_domain_total', values['partner_id']),
                    'columns': [values['direction'], values['4'], values['3'], values['2'], values['1'], values['0'], values['total']],
                    'level': 1,
                }
                vals['columns'] = map(self._format, vals['columns'])
                lines.append(vals)
        if total and not line_id:
            #Jagadeesh start
            if new_filter_type in ['vendors','staff'] and self._context['account_type'] == 'payable':
                columns = [total[0], total[1], total[2], total[3], total[4], total[5], total[6]]
            else:
                columns = [total[6], total[4], total[3], total[2], total[1], total[0], total[5]]
            #Jagadeesh end
            total_line = {
                'id': 0,
                'name': _('Total'),
                'level': 0,
                'type': 'o_account_reports_domain_total',
                'footnotes': context._get_footnotes('o_account_reports_domain_total', 0),
                #'columns': [total[6], total[4], total[3], total[2], total[1], total[0], total[5]], #Jagadeesh
                'columns':columns, #Jagadeesh
            }
            total_line['columns'] = map(self._format, total_line['columns'])
            lines.append(total_line)
        return lines

class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'

    division_ids = fields.Many2many('division.division','acc_analytic_div_rel','acc_analytic_id','div_id',string="Division")

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    @api.model
    def create(self,vals):
	''' No analytic accounts should be tagged to "Stock Interim Account (Delivered)" account '''

        account_id = vals['account_id']
        stock_account_obj = self.env['account.account'].search([('code','=',101130),('name','=','Stock Interim Account (Delivered)')],limit=1)
        if account_id == stock_account_obj.id:
            vals.update({'analytic_account_id':False})
        return super(AccountMoveLine,self).create(vals)

    
