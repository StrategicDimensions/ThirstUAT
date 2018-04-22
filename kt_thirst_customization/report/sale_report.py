from odoo import fields,models,api
from datetime import datetime,date
import pytz


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def get_event_details(self):
        so_obj = self
        running_time = ''
	start_date = so_obj.time_start
        if so_obj.time_start and so_obj.time_end:
            tz = pytz.timezone(self.env.user.tz) or pytz.utc
            event_start = pytz.utc.localize(datetime.strptime(so_obj.time_start,'%Y-%m-%d %H:%M:%S')).astimezone(tz)
	    event_end = pytz.utc.localize(datetime.strptime(so_obj.time_end,'%Y-%m-%d %H:%M:%S')).astimezone(tz)
            start_time = event_start.strftime('%H:%M') 
            end_time = event_end.strftime('%H:%M')
	    start_date = event_start.strftime('%Y-%m-%d')
            running_time = str(start_time)+' - '+str(end_time)
        event_dic = {   'running_time':running_time,
                        'event_date':start_date,
                    }
        return event_dic

    @api.multi
    def get_event_date(self):
        so_obj = self
        if so_obj.time_start:
            event_date = datetime.strptime(so_obj.time_start,'%Y-%m-%d %H:%M:%S')
            return {'day':event_date.strftime('%d'),'month':event_date.strftime('%B'),'year':event_date.strftime('%Y')}
        else:
            return {'day':'','month':'','year':''}

    @api.multi
    def get_banking_details(self):
        bank_journal_obj = self.env['account.journal'].search([('name','=','Bank')],limit=1)
        if bank_journal_obj:
            return {'acc_no':bank_journal_obj.bank_acc_number,'branch':bank_journal_obj.bank_id and bank_journal_obj.bank_id.name or False}
        else:
            return {'acc_no':'','branch':''}


    @api.multi
    def get_company(self):
        company = self.env['res.company'].search([('name','=','Thirst Bar Services')],limit=1)
        return company

    @api.model
    def get_today_date(self):
        return date.today()


