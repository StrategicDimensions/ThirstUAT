from itertools import groupby
from datetime import datetime, timedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.misc import formatLang

import odoo.addons.decimal_precision as dp

class Beverages(models.Model):
	_name = 'beverages'
	name = fields.Char('Name')
	product_id = fields.Many2one('product.template',string='Product')
	category = fields.Boolean('Categories')
	sub_category = fields.Boolean('Sub Categories')
	selectable_product = fields.Boolean('Selectable Product')
	beverage_product_ids = fields.One2many('beverage.products','beverage_id',string="Beverage Products")
	beverage_category_ids = fields.One2many('beverages.category.rel','beverage_id',string="Beverage Categories")
	beverage_sub_category_ids = fields.One2many('beverages.sub.category.rel','beverage_id',string="Beverage Sub Categories")

        @api.onchange('product_id')
        def onchange_product_id(self):
            if self.product_id:
                objs = self.search([('product_id','=',self.product_id.id)])
                if len(objs) >= 1:
                    self.product_id = False
                    return {'warning':{'title':'Warning','message':'You are not allowed to same product for multiple beverage menus.'}}



class BeveragesCategoryRel(models.Model):
	_name = 'beverages.category.rel'
	beverage_id = fields.Many2one('beverages',string="Beverages")
	categ_id = fields.Many2one('beverages.category',string="Category Name")
	sequence = fields.Integer('Sequence')
	max_products = fields.Integer('Maximim Products')

	@api.onchange('categ_id')
	def onchange_categ_id(self):
		if self.categ_id:
			self.sequence = self.categ_id.sequence

class BeveragesSubCategoryRel(models.Model):
        _name = 'beverages.sub.category.rel'
        beverage_id = fields.Many2one('beverages',string="Beverages")
        sub_categ_id = fields.Many2one('beverages.sub.category',string="Sub Category Name")
	parent_categ = fields.Many2one('beverages.category',string="Parent Category")
        sequence = fields.Integer('Sequence')
        max_products = fields.Integer('Maximim Products')

	@api.onchange('sub_categ_id')
        def onchange_sub_categ_id(self):
                if self.sub_categ_id:
                        self.sequence = self.sub_categ_id.sequence
			self.parent_categ = self.sub_categ_id.parent_categ




class BeverageProducts(models.Model):
	_name = 'beverage.products'
	beverage_id = fields.Many2one('beverages',string="Beverages")
	product_product_id = fields.Many2one('product.template',string="Products")
	product_image = fields.Binary('Image')
	product_description = fields.Text('Description')
	product_url = fields.Char('Product Url')
	product_start_date = fields.Date('Start Date',default=datetime.now())
	product_end_date = fields.Date('End Date')
	product_active = fields.Boolean('Active',default=True)
	product_sequence = fields.Char('Sequence')
	category_id = fields.Many2one('beverages.category',string="Category")
	sub_categ_id = fields.Many2one('beverages.sub.category',string="Sub Category")
	prod_type = fields.Selection([('Standard','Standard'),('Premium','Premium')],string="Type",default='Standard')
        button_invisible = fields.Boolean('Select Button Invisible',help = 'select/purchase button will be disappeared on product at beverages selection page if it is true',default=False)
	remove_button_visible = fields.Boolean('Remove Button Visible',help = 'Remove button will be appeared on product at beverages selection page if it is true')
        default_selection = fields.Boolean('Default Selection')



	@api.onchange('product_product_id')
        def onchange_category_id(self):
                if self.product_product_id:
                        self.product_image = self.product_product_id.image_medium

	@api.onchange('beverage_id')
	def onchange_beverage_id(self):
		if self.beverage_id:
			category_ids = [x.categ_id.id for x in self.beverage_id.beverage_category_ids]
			sub_category_ids = [x.sub_categ_id.id for x in self.beverage_id.beverage_sub_category_ids]
		        return {'domain':{'category_id': [('id', 'in', category_ids)],'sub_categ_id':[('id', 'in', sub_category_ids)]}}


class BeverageCategory(models.Model):
	_name = 'beverages.category'
	name = fields.Char('Name')
	sequence = fields.Integer('Sequence')
	max_products = fields.Integer('Maximum Products')


class BeverageSubCategory(models.Model):
        _name = 'beverages.sub.category'
        name = fields.Char('Name')
	parent_categ = fields.Many2one('beverages.category',string="Parent Category")
        sequence = fields.Integer('Sequence')
	max_products = fields.Integer('Maximum Products')

#Jagadeesh added
class SelectedBeverages(models.Model):
        _name = 'selected.beverages'
        sale_order_id = fields.Many2one('sale.order',string='Sale Order')
        product_id = fields.Many2one('product.template',string='Products')	
	uom_id = fields.Many2one('product.uom',related="product_id.uom_id",string="Unit of Measure")
	uom_po_id = fields.Many2one('product.uom',related="product_id.uom_po_id",string="Purchase Unit of Measure")
        category_id = fields.Many2one('beverages.category',string='Category')
        sub_category_id = fields.Many2one('beverages.sub.category',string='Sub Category')
	product_code = fields.Char('Product Code')
        product_name = fields.Char(string="Product")	
	prod_type = fields.Selection([('Standard','Standard'),('Premium','Premium')],string="Type",default='Standard')
        on_hand = fields.Integer(string="On Hand")#qty_available
	qty_on_hand = fields.Float(compute='_get_stock_qty',string='Qty On Hand')
        forecasted = fields.Integer(string="Forecasted")#virtual_available
        bev_select_id = fields.Many2one('beverages.selection',string="Beverage Selection") #dont remove this field #Jagadeesh
	standard_bev_select_id = fields.Many2one('beverages.selection',string="Beverage Selection")
	premium_bev_select_id = fields.Many2one('beverages.selection',string="Beverage Selection")
	qty_required = fields.Float('QTY Required')
	variance = fields.Integer(compute="_get_variance",string='Variance')
	classification = fields.Selection([('bar','Bar'),('equipment','Equipment'),('consumable','Consumable')])
	consume_project_id = fields.Many2one('project.project','Project')
	equipment_project_id = fields.Many2one('project.project','Project')
	total = fields.Float(compute="_compute_total", string="Total")


        @api.depends('product_id')
        def _get_stock_qty(self):
            parent_loc_id = self.env['stock.location'].search([('name','=','WH')],limit=1)
            location_id = self.env['stock.location'].search([('name','=','Stock'),('location_id','=',parent_loc_id.id)],limit=1).id

            context = {'search_default_real_stock_negative': 1, 'search_default_virtual_stock_available': 1, 'bin_size': True, 'active_model': 'stock.location', 'search_default_real_stock_available': 1, 'params': {'action': 373}, 'location': location_id, 'search_disable_custom_filters': True, 'search_default_virtual_stock_negative': 1, 'active_ids': [location_id], 'location_id': location_id, 'active_id': location_id}

            '''stock_args = []
            products = self.env['product.product'].with_context(context).search(args=stock_args)
            products_on_hand = dict(zip(products.ids,products.mapped('qty_available')))
            for obj in self:
		print 'prod name=============',obj.product_id.name
                prod_id = self.env['product.product'].search([('product_tmpl_id','=',obj.product_id.id)])
		print 'prod id=============',prod_id
                obj.qty_on_hand = products_on_hand[prod_id.id]'''

	    for obj in self:
                obj.qty_on_hand = self.env['product.product'].with_context(context).search([('product_tmpl_id','=',obj.product_id.id)]).qty_available

	    def _compute_total(self):
	        for record in self:
	            record.total = record.product_id.lst_price * record.qty_required


        @api.onchange('product_id')
        def onchange_product_id(self):
            for obj in self:
                obj.product_code = obj.product_id.default_code
                #obj.classification = obj.product_id.classification
                obj.uom_id = obj.product_id.uom_id.id
                obj.uom_po_id = obj.product_id.uom_po_id.id
                obj.on_hand = obj.product_id.qty_available
                obj.forecasted = obj.product_id.virtual_available

	@api.depends('qty_required','qty_on_hand')
	def _get_variance(self):
	    for obj in self:
	        obj.variance = obj.qty_required - obj.qty_on_hand

        '''@api.onchange('qty_required','on_hand')
	def onchange_qty_required(self):
	    print 'onchange============'	    
	    self.variance = self.qty_required -self.on_hand

	@api.model
	@api.onchange('product_id')
	def onchange_product_id(self):
	    print 'on change 1================'
	    if self.product_id:		
		self.on_hand = self.product_id.qty_available
		self.forecasted = self.product_id.virtual_available
	
	@api.model
	@api.onchange('sub_category_id')
	def onchange_sub_categ_id(self):
	    print 'on chnage 2==============='
	    if self.sub_category_id:
		self.category_id = self.sub_category_id.parent_categ.id'''
#Jagadeesh end

class BeveragesSelection(models.Model):
	_name = 'beverages.selection'
	product_id = fields.Many2one('product.template',string="Product")
	project_id = fields.Many2one('project.project',string="Project")
	beverage_menu_id = fields.Many2one('beverages',string='Beverage Menu')
	creation_date = fields.Datetime('Creation Date')
	date_completed = fields.Datetime('Date Completed')
	is_completed = fields.Boolean('Completed')
	selected_beverages_ids = fields.One2many('selected.beverages','bev_select_id',"Selected Beverages") #dont remove this field #Jagadeesh
	#standard_beverage_ids = fields.One2many('selected.beverages','standard_bev_select_id',compute="_get_standard_beverages",string="standard Selected Beverages")
	#premium_beverage_ids = fields.One2many('selected.beverages','premium_bev_select_id',compute="_get_premium_beverages",string="Premium Selected Beverages")
	standard_beverage_ids = fields.One2many('selected.beverages','standard_bev_select_id',string="standard Selected Beverages")
        premium_beverage_ids = fields.One2many('selected.beverages','premium_bev_select_id',string="Premium Selected Beverages")


	@api.multi
	@api.depends('selected_beverages_ids')
	def _get_standard_beverages(self):
	    beverage_objs = self.env['selected.beverages'].search([('bev_select_id','=',self.id),('prod_type','=','Standard')])
	    #self.standard_beverage_ids = [(6,0,[obj.id for obj in beverage_objs])]	
	    self.standard_beverage_ids = [(4,obj.id,0) for obj in beverage_objs]

        @api.multi
        @api.depends('selected_beverages_ids')
        def _get_premium_beverages(self):
            beverage_objs = self.env['selected.beverages'].search([('bev_select_id','=',self.id),('prod_type','=','Premium')]) 
            #self.premium_beverage_ids = [(6,0,[obj.id for obj in beverage_objs])]
	    self.premium_beverage_ids = [(4,obj.id,0) for obj in beverage_objs]


class project_project(models.Model):
	_inherit='project.project'
	beverages_selection_ids = fields.One2many('beverages.selection','project_id','Beverages Selection')

