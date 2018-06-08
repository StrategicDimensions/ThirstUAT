from odoo import fields,models,api,_
from odoo.exceptions import UserError, ValidationError
from functools import partial

class PosOrder(models.Model):
    _inherit = 'pos.order'

    project_id = fields.Many2one('project.project','project')
    ordered_type = fields.Selection([('cash_bar','Cash Bar'),('event_budget','Event Budget')],string="Order Type")

    @api.model
    def fetch_available_budget(self, project_id):
        project = self.env['project.project'].browse(project_id)
        return project.budget_available_amount
        
    @api.model
    def _order_fields(self, ui_order):
        cust_session_id = self.env['pos.session'].browse(ui_order['pos_session_id'])
        process_line = partial(self.env['pos.order.line']._order_line_fields)
        project_obj =  cust_session_id.project_id
# 	project_obj = self.env['project.project'].browse(ui_order['project_id'])
        partner_id = project_obj.sale_order_id.partner_id.id
        '''if project_obj.event_pos_type != 'budget_cash_bar' :
            ordered_type = project_obj.event_pos_type
        else:
        ordered_type = ui_order['ordered_type']'''
        return {
            'name':         ui_order['name'],
            'user_id':      ui_order['user_id'] or False,
            'session_id':   ui_order['pos_session_id'],
            'lines':        [process_line(l) for l in ui_order['lines']] if ui_order['lines'] else False,
            'pos_reference': ui_order['name'],
               #jagadeesh start
#            'partner_id':   ui_order['partner_id'] or False,
#            'project_id': ui_order['project_id'] or False,
            'project_id': project_obj.id or False,   
            'partner_id': partner_id,
            'ordered_type': ui_order['ordered_type'],
            #jagadeesh end
            'date_order':   ui_order['creation_date'],
            'fiscal_position_id': ui_order['fiscal_position_id']
        }

    @api.multi
    def action_invoice_create(self,ids):
	''' This method will be called when click on invoice menu under actions of project '''
	pos_orders_obj = self.env['pos.order'].browse(ids)
	Invoice = self.env['account.invoice']
	local_context = dict(self.env.context, force_company=self.company_id.id, company_id=self.company_id.id)
	invoice = Invoice.new(self._prepare_invoice())
        invoice._onchange_partner_id()
        invoice.fiscal_position_id = self.fiscal_position_id
        inv = invoice._convert_to_write({name: invoice[name] for name in invoice._cache})
        new_invoice = Invoice.with_context(local_context).create(inv)

        for order in pos_orders_obj:
            # Force company for all SUPERUSER_ID action
            local_context = dict(self.env.context, force_company=order.company_id.id, company_id=order.company_id.id)

            if not order.partner_id:
                raise UserError(_('Please provide a partner for the sale.'))

            analytic_accnt_obj = self.env['account.analytic.account'].search([('name','=',self.project_id.name)],limit=1)
            for line in order.lines:
                if line.product_id.id in new_invoice.invoice_line_ids.mapped('product_id').ids:
                    for inv_line in new_invoice.invoice_line_ids:
                        if inv_line.product_id.id == line.product_id.id:
                            inv_line.quantity += line.qty
                else:
                    inv_line_obj = self.with_context(local_context)._action_create_invoice_line(line, new_invoice.id)
                    inv_line_obj.account_analytic_id = analytic_accnt_obj.id

            order.write({'invoice_id': new_invoice.id,'state': 'invoiced'})
	 
	new_invoice.with_context(local_context).compute_taxes()
        new_invoice.action_invoice_open()
	new_invoice.inv_project_id = self.project_id.id
	return {}

    @api.multi
    def action_pos_order_done(self):
        ''' overrided base method'''
        #return self._create_account_move_line()
        return True

    @api.model
    def create(self, values):
        res =  super(PosOrder,self).create(values)
        if res.ordered_type == 'event_budget' and res.state == 'draft':
            res.state = 'paid'
            res.create_picking()
        return res


class PosSession(models.Model):
    _inherit = 'pos.session'

    project_id = fields.Many2one('project.project', 'project');
