from odoo import fields,models,api

class ProjectProject(models.Model):
    _inherit = 'project.project'

    def _get_all_stock_items(self):
	product_clsf_dic = {}
	product_clsf_stock_list = []
	beverages_dic = {}
	bom_dic = {}
	beverage_stock_list = []
	bom_stock_list = []
	#consumables/equipment
	for obj in self.consumable_beverage_ids:
	    if obj.product_id.categ_id.id not in product_clsf_dic.keys():
		product_clsf_dic[obj.product_id.categ_id.id] = [obj]
	    else:
		product_clsf_dic[obj.product_id.categ_id.id].append(obj)
	for obj in self.equipment_beverage_ids:
            if obj.product_id.categ_id.id not in product_clsf_dic.keys():
                product_clsf_dic[obj.product_id.categ_id.id] = [obj]
            else:
                product_clsf_dic[obj.product_id.categ_id.id].append(obj)
        for key in product_clsf_dic.keys():
            new_dic = {'category_name':self.env['product.category'].browse(int(key)).name,'type':'classification','stock':product_clsf_dic[key]}
            product_clsf_stock_list.append(new_dic) 
	
	#beverages
	'''for bev_select_obj in self.beverages_selection_ids:
	    for obj in bev_select_obj.selected_beverages_ids:
		if obj.product_id.categ_id.id not in beverages_dic.keys():
                    beverages_dic[obj.product_id.categ_id.id] = [obj]
                else:
                    beverages_dic[obj.product_id.categ_id.id].append(obj)		

	for key in beverages_dic.keys():
	    new_dic = {'category_name':self.env['product.category'].browse(int(key)).name,'type':'beverage','stock':beverages_dic[key]}
	    beverage_stock_list.append(new_dic)	'''


        for bev_select_obj in self.beverages_selection_ids:
            for obj in bev_select_obj.standard_beverage_ids:
                if obj.product_id.categ_id.id not in beverages_dic.keys():
                    beverages_dic[obj.product_id.categ_id.id] = [obj]
                else:
                    beverages_dic[obj.product_id.categ_id.id].append(obj)

            for obj in bev_select_obj.premium_beverage_ids:
                if obj.product_id.categ_id.id not in beverages_dic.keys():
                    beverages_dic[obj.product_id.categ_id.id] = [obj]
                else:
                    beverages_dic[obj.product_id.categ_id.id].append(obj)

        for key in beverages_dic.keys():
            new_dic = {'category_name':self.env['product.category'].browse(int(key)).name,'type':'beverage','stock':beverages_dic[key]}
            beverage_stock_list.append(new_dic)



	#Materials
	for obj in self.product_bom_ids:
	    if obj.product_id.categ_id.id not in bom_dic.keys():
		bom_dic[obj.product_id.categ_id.id] = [obj]
	    else:
		bom_dic[obj.product_id.categ_id.id].append(obj)
	for key in bom_dic.keys():
	    new_dic = {'category_name':self.env['product.category'].browse(int(key)).name,'type':'material','stock':bom_dic[key]}
	    bom_stock_list.append(new_dic)
	stock_list = product_clsf_stock_list+beverage_stock_list+bom_stock_list
	return stock_list

    def _get_setup_staff_ids(self):
        return self.setup_staff_ids.sorted('role')

    def _get_event_staff_ids(self):
        return self.event_staff_ids.sorted('role')

    def _get_breakdown_staff_ids(self):
        return self.breakdown_staff_ids.sorted('role')

