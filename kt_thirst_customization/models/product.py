from openerp import fields,models,api
import base64
import os.path
import unicodedata

class ProductTemplate(models.Model):
	_inherit = 'product.template'

	classification = fields.Selection([('bar','Bar'),('equipment','Equipment'),('consumable','Consumable')])
	sap_code = fields.Char(string="SAP Code")
	sap_stock_code = fields.Char(string="SAP Stock Code")



	@api.multi
	def import_product_images(self,product_ids):
		for obj in [self.browse(product_id) for product_id in product_ids ]:
			file_path = '/home/thirstuat/public_html/odoo/addons/kt_thirst_customization/static/src/img/product_images/'
			if obj.default_code:
				default_code = obj.default_code
				#if type(default_code) == 'unicode':
				#    default_code = unicodedata.normalize('NFKD', default_code).encode('ascii','ignore')
				file_path += str(default_code)+'.png'
				if os.path.isfile(file_path):
					with open(file_path,'rb') as f:
						encoded_string = base64.b64encode(f.read())
						f.close()
						obj.image_medium = encoded_string	
						#self.image_medium = False

