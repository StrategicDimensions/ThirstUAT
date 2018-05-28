from odoo import fields,models,api, _


class StockLocation(models.Model):
    _inherit = 'stock.location'

    @api.multi
    def get_stock_location_products(self,project_id=False):

	pos_categ_ids = []
	location_id = self.id
	context = {'search_default_real_stock_negative': 1, 'search_default_virtual_stock_available': 1, 'bin_size': True, 'active_model': 'stock.location', 'search_default_real_stock_available': 1, 'params': {'action': 373}, 'location': location_id, 'search_disable_custom_filters': True, 'search_default_virtual_stock_negative': 1, 'active_ids': [location_id], 'location_id': location_id, 'active_id': location_id}	

	#stock_args = ['|', ['qty_available', '>', 0], ['qty_available', '<', 0]]
	stock_args = ['|', ['qty_available', '>', 0], ['qty_available', '<', 0],['available_in_pos','=',True],['pos_categ_id','!=',False]]

	products = self.env['product.product'].with_context(context).search(args=stock_args)

	pos_categ_ids += products.mapped('pos_categ_id.id')
	pos_categ_ids += products.mapped('pos_categ_id.parent_id.id')
	products_on_hand = dict(zip(products.ids,products.mapped('qty_available')))
	pos_order_id = False
	#if project_id:
	#    pos_order_id = max(self.env['project.project'].browse(project_id).pos_order_ids.ids)
	'''if pos_order_id:
	    print 'name===========',self.env['pos.order'].browse(pos_order_id).name
	    for obj in self.env['pos.order'].browse(pos_order_id).lines:
		if obj.product_id.id in products_on_hand.keys():
		    print 'if id================'
		    products_on_hand[obj.product_id.id] = products_on_hand[obj.product_id.id] - obj.qty'''

	'''all_products = self.env['product.product'].search([('available_in_pos','=',True)]).mapped('id')
        for prd_id in all_products:
            if prd_id not in products_on_hand.keys():
                products_on_hand.update({prd_id:0})

	return {'product_ids' : all_products,'products_on_hand': products_on_hand } '''

	service_products = self.env['product.product'].search([('type','=','service'),('available_in_pos','=',True),('pos_categ_id','!=',False)])
	pos_categ_ids += service_products.mapped('pos_categ_id.id')
	pos_categ_ids += service_products.mapped('pos_categ_id.parent_id.id')
        for prd_id in service_products.ids:
            if prd_id not in products_on_hand.keys():
                products_on_hand.update({prd_id:0})
        return {'product_ids' : products.ids + service_products.ids,'products_on_hand': products_on_hand,'pos_categs':pos_categ_ids }


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    project_id = fields.Many2one('project.project',string="Project")

    @api.multi
    def do_new_transfer(self):
        res = super(StockPicking,self).do_new_transfer()
        if self.project_id:
            if isinstance(self.project_id.next_transfer_type,int):
                if self.project_id.next_transfer_type != 4 and self.project_id.next_transfer_type < 8:
                    self.project_id.next_transfer_type += 1
                    self.project_id.transfer_stock_to_function_location(self.id)
        return res

    @api.multi
    def do_transfer(self):
        res = super(StockPicking, self).do_transfer()
        pickings = self.env['stock.picking'].search([('origin', '=', self.project_id.project_number)])
        print '\n\npickings', pickings
        return {
                'type': 'ir.actions.act_window',
                'name': _('Stock Operations'),
                'res_model': 'stock.picking',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'target': 'current',
                'domain': [('id', 'in', pickings.ids)]
                }

