from odoo import fields,models,api,_
from datetime import datetime
from odoo.exceptions import ValidationError, UserError


class PosConfig(models.Model):
    _inherit = 'pos.config'

    show_qty_on_pos = fields.Boolean(string='Display Stock in POS',default=True) #MAY18

    @api.multi
    def open_pos_project(self):
	''' when click on New Session button this method will be called to open a wizard '''
	view_id = self.env['ir.model.data'].get_object_reference('kt_thirst_customization','view_pos_project_config_form')[1]
	return {
		'name':'Project Configuration',
		'no_destroy':True,
	        'type':'ir.actions.act_window',
		'target':'new',
		'res_model':'pos.project.config',
		'view_type':'form',
		'view_mode':'form',
		'view_id':view_id,
		'context':{'pos_config_id':self.id}
	   }


class PosProjectConfig(models.Model):
    _name = 'pos.project.config'

    project_id = fields.Many2one('project.project','Project')

    @api.multi
    def project_submit(self):
	''' when click on submit button on wizard project will be assigned to pos session and then session will be start '''
	context = self.env.context
	pos_config_id = context.get('pos_config_id') or False

	pos_config_obj = self.env['pos.config'].browse(pos_config_id)
	if self.project_id.fun_event_loc_id:
            pos_config_obj.stock_location_id = self.project_id.fun_event_loc_id.id
	else:
            raise ValidationError('Selected project not having function location')

        project_id = self.project_id and self.project_id.id or False
        self.current_session_id = self.env['pos.session'].create({
                'user_id': self.env.uid,
                'config_id': pos_config_id,
                'project_id':project_id ,
            })
	#if self.current_session_id.state != 'opened':
	#    #self.current_session_id.state = 'opened'
	#    self.current_session_id.action_pos_session_open()
	if self.current_session_id.state == 'opened':
	    return {
            'type': 'ir.actions.act_url',
            'url':   '/pos/web/',
            'target': 'self',
        }


class PosSession(models.Model):
    _inherit = 'pos.session'

    def _confirm_orders(self):
	'''overrided base method'''
        for session in self:
            company_id = session.config_id.journal_id.company_id.id
            orders = session.order_ids.filtered(lambda order: order.state == 'paid')
            journal_id = self.env['ir.config_parameter'].sudo().get_param(
                'pos.closing.journal_id', default=session.config_id.journal_id.id)
            #move = self.env['pos.order'].with_context(force_company=company_id)._create_account_move(session.start_at, session.name, int(journal_id), company_id) #Jagadeesh commented
            #orders.with_context(force_company=company_id)._create_account_move_line(session, move) #Jagadeesh commented
            for order in session.order_ids.filtered(lambda o: o.state != 'done'):
                if order.state not in ('paid', 'invoiced'):
                    raise UserError(_("You cannot confirm all orders of this session, because they have not the 'paid' status"))
                order.action_pos_order_done()


    @api.multi
    def action_pos_session_close(self):
        '''overrided base method'''
        # Close CashBox
        for session in self:
            company_id = session.config_id.company_id.id
            ctx = dict(self.env.context, force_company=company_id, company_id=company_id)
            for st in session.statement_ids:
                if abs(st.difference) > st.journal_id.amount_authorized_diff:
                    # The pos manager can close statements with maximums.
                    if not self.env['ir.model.access'].check_groups("point_of_sale.group_pos_manager"):
                        raise UserError(_("Your ending balance is too different from the theoretical cash closing (%.2f), the maximum allowed is: %.2f. You can contact your manager to force it.") % (st.difference, st.journal_id.amount_authorized_diff))
                if (st.journal_id.type not in ['bank', 'cash']):
                    raise UserError(_("The type of the journal for your payment method should be bank or cash "))
                #st.with_context(ctx).sudo().button_confirm_bank() #Jagadeesh commented
        self.with_context(ctx)._confirm_orders()
        self.write({'state': 'closed'})
        return {
            'type': 'ir.actions.client',
            'name': 'Point of Sale Menu',
            'tag': 'reload',
            'params': {'menu_id': self.env.ref('point_of_sale.menu_point_root').id},
        }



    @api.multi
    def action_pos_session_closing_control(self):
        res = super(PosSession,self).action_pos_session_closing_control()
        proj_id = self.project_id.id
        location_id = self.config_id.stock_location_id.id
        pos_opened_objs = self.env['pos.session'].search([('project_id','=',proj_id),('state','=','opened')])
        transfer_needed = False
        if len(pos_opened_objs.ids) > 1 :
            pass
        elif len(pos_opened_objs.ids) == 1:
            if self.id != pos_opened_objs.id:
                pass
            else:
                transfer_needed = True
        elif not pos_opened_objs:
            transfer_needed = True

        if transfer_needed:
            #transfer stock from function location to vehicle    
            if not self.project_id.fun_event_loc_id:
                raise ValidationError('There is no function location for project %s'%self.project_id.project_number)
            if not self.project_id.vehicle:
                raise ValidationError('There is no Vehicle for project %s'%self.project_id.project_number)

            warehouse_obj = self.env['stock.warehouse'].search([('code','=','WH')],limit=1)
            picking_type_obj = self.env['stock.picking.type'].search([('name','=','Internal Transfers'),('warehouse_id','=',warehouse_obj.id)],limit=1)
            context = {'search_default_real_stock_negative': 1, 'search_default_virtual_stock_available': 1, 'bin_size': True, 'active_model': 'stock.location', 'search_default_real_stock_available': 1, 'params': {'action': 373}, 'location': location_id, 'search_disable_custom_filters': True, 'search_default_virtual_stock_negative': 1, 'active_ids': [location_id], 'location_id': location_id, 'active_id': location_id}

            stock_args = ['|', ['qty_available', '>', 0], ['qty_available', '<', 0]]
            products = self.env['product.product'].with_context(context).search(stock_args)

            trans_vals = {'partner_id':self.project_id.sale_order_id.partner_id.id,'picking_type_id':picking_type_obj.id,'priority':'1','move_type':'one','location_id':self.project_id.fun_event_loc_id.id,'location_dest_id':self.project_id.vehicle.id,'min_date':str(datetime.now()),'origin':self.project_id.project_number,'project_id':proj_id,
                         }
            stock_pick_obj = self.env['stock.picking'].create(trans_vals)

            for obj in products:
                stock_move_obj = self.env['stock.move'].create({'picking_id':stock_pick_obj.id,'product_id':obj.id,'product_uom_qty':obj.qty_available,'product_uom':obj.uom_id.id,'location_id':self.project_id.fun_event_loc_id.id,'location_dest_id':self.project_id.vehicle.id,'name':'['+str(obj.default_code)+'] '+str(obj.name),'date_expected':str(datetime.now()) })

	    if self.project_id.next_transfer_type != 8:
	        self.project_id.next_transfer_type += 1

	    stock_pick_obj.action_confirm()	

        return res
       
