from django.shortcuts import render
from django.views.generic import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import JsonResponse
import json
from django.core import serializers
from models import Tickets, Division, Duration, Zip, ErrorCount, OutageCaused, SystemCaused,AddtNotes
import datetime
from django.db import transaction
from uuid import UUID
import uuid
from django.db import connection
from django.http import HttpResponse
from django.contrib.auth import authenticate
from django.shortcuts import redirect, render_to_response
from django.conf import settings
#from django.http import render_to_response
# Create your views here.

import logging
logger = logging.getLogger(__name__)

class Ticket(object):
	def __init__(self, created_dt, division, zip_cd, error_count, ticket_num, outage_caused, system_caused, addt_notes, ticket_type, duration):
		self.created_dt = created_dt
		self.division = division 
		self.zip = zip_cd
		self.error_count = error_count
		self.ticket_num = ticket_num
		self.outage_caused = outage_caused
		self.system_caused = system_caused
		self.addt_notes = addt_notes
		self.ticket_type = ticket_type
		self.duration = duration		

	def __str__(self):
		return """ created_dt == {0} 
		,division = {1}
		,pg = {2}
		,error_count = {3}
		,ticket_num = {4}
		,outage_caused = {5}
		,system_caused = {6}
		,addt_notes = {7}
		,ticket_type = {8}
		,duration = {9}""".format(
			self.created_dt, self.division, str(self.zip), self.error_count,self.ticket_num,self.outage_caused,self.system_caused,self.addt_notes,
			self.ticket_type,self.duration)


def validate_user_pass(request):
	if request.method == 'GET':
		return render_to_response('tickets/mainpage.html')
		#return redirect('%s' %(settings.LOGIN_URL))

	username = request.POST['username']
	password = request.POST['password']
	user = authenticate(username=request.POST['username'],password=request.POST['password'])
	print 'username == ', username
	print 'password == ', password
	if user is not None:
		if user.is_active:
			return render_to_response('tickets/mainpage.html')
	return render_to_response('tickets/loginpage.html',{'msg':'Invalid username/password'})

class CreateTicketData(View):

	@method_decorator(csrf_exempt)
	def dispatch(self, request, *args, **kwargs):
		return super(CreateTicketData, self).dispatch(request, *args, **kwargs)

	def get(self, request):
		return render_to_response('tickets/createticket.html')

	def post(self, request):
		alldata = request.POST
		print 'post alldata == ', alldata
		print 'alldata.getlist(zipcode[]) == ', alldata.getlist('zipcode')
		print 'alldata.getlist(zipcode[]) == ', type(alldata.getlist('zipcode'))
		
		logger.debug("post data  == {0}".format(alldata))

		created_dt = datetime.datetime.strptime(
			str(alldata.get('date')), '%Y/%m/%d %H:%S').strftime('%Y-%m-%d %H:%S:00')
		
		t = Ticket(created_dt
			,alldata.get('division')
			,alldata.getlist('zipcode')
			,alldata.get('error_count')
			,alldata.get('ticket_num')
			,alldata.get('outage_caused')
			,alldata.get('system_caused')
			,alldata.get('addt_notes')
			,alldata.get('tkt-radio')
			,alldata.get('duration'))
		
		logger.debug("Insert document == {0}".format(t))
		
		try:
			with transaction.atomic():
				div,created = Division.objects.get_or_create(division_name=t.division)
				dur,created = Duration.objects.get_or_create(duration=t.duration)
				err,created = ErrorCount.objects.get_or_create(error=t.error_count)
				out,created = OutageCaused.objects.get_or_create(outage_caused=t.outage_caused)
				sys,created = SystemCaused.objects.get_or_create(system_caused=t.system_caused)
				ticket_info = {
					'row_create_ts': created_dt,
					'ticket_num': t.ticket_num,
					'ticket_type': t.ticket_type,
					'division': div.ID,
					'duration': dur.ID,
					'error_count': err.ID,
					'outage_caused': out.ID,
					'system_caused': sys.ID,
				}

				try:
					ticket = Tickets.objects.get(ticket_num=t.ticket_num)
				except Tickets.DoesNotExist:
					ticket = None

				if ticket is None:
					ticket = Tickets.objects.create(**ticket_info)
				else:
					print 'Ticket already present'
					return JsonResponse({'status': 'Ticket already present'})
				
				print 't == ', t
				print 't.pg == ', t.zip
				for each in t.zip:
					p,created = Zip.objects.get_or_create(zip_cd=each)
					ticket.zips.add(p)
				
				AddtNotes.objects.create(Id=ticket,notes=t.addt_notes)
				
		except Exception as e:
			print 'Exception == ', e 
			logger.debug("MySQLException == {0}".format(e))
			return JsonResponse({'status': 'Contact Support Team'})

		return render_to_response('tickets/mainpage.html')


class GetTicketData(View):

	@method_decorator(csrf_exempt)
	def dispatch(self, request, *args, **kwargs):
		return super(GetTicketData, self).dispatch(request, *args, **kwargs)

	def get(self, request):
		return JsonResponse({'status': 'success'})

	def post(self, request):

		alldata = request.POST
		print 'get alldata == ', alldata
		
		initial = alldata.get('initial')
		print 'alldata.get.start_date_s==',alldata.get('start_date_s')

		doc = {
			'division': alldata.get('division'),
			'pg': alldata.getlist('pg[]'),
			'error_count': alldata.get('error_count'),
			'ticket_num': alldata.get('ticket_num'),
			'outage_caused': alldata.get('outage_caused'),
			'system_caused': alldata.get('system_caused'),
			'ticket_type': alldata.get('ticket_type'),
			'duration': alldata.get('duration'),
			'start_date_s': alldata.get('start_date_s'),
			'start_date_e': alldata.get('start_date_e'),
			'end_date_s': alldata.get('end_date_s'),
			'end_date_e': alldata.get('end_date_e')
			
		}
		print 'initial == ', initial

		data = {}
		output = []
		
		print 'doc == ', doc
		try:
			if initial == 'Y':
				cursor = connection.cursor()
				
				qry = """
					select   tb1.ticket_num
							,tb1.row_create_ts
							,tb1.ticket_type
							,tb1.row_update_ts
							,tb1.row_end_ts
							,tb2.division_name
							,tb3.duration
							,tb4.error
							,tb5.outage_caused
							,tb6.system_caused
							,tb8.zip_cd
							,tb9.notes
							from tickets tb1
							inner join
							division tb2
							on tb1.division_id = tb2.division_id
							inner join
							duration tb3
							on tb1.duration_id = tb3.duration_id
							inner join
							error_count tb4
							on tb1.error_count_id = tb4.error_count_id
							inner join
							outage_caused tb5
							on tb1.outage_caused_id = tb5.outage_caused_id
							inner join
							system_caused tb6
							on tb1.system_caused_id = tb6.system_caused_id
							inner join
							tickets_zips tb7
							on tb1.ticket_num = tb7.tickets_id
							inner join
							zip tb8
							on tb7.zip_id = tb8.zip_id
							left outer join
							addt_notes tb9
							on tb1.ticket_num = tb9.notes_id

							order by row_create_ts,ticket_num
					"""
				print 'qry ==', qry
				cursor.execute(qry)
				results = cursor.fetchall()
			else:
				cursor = connection.cursor()
				print 'prem-0'

				start_date_qry_set = False
				end_date_qry_set = False
				ticket_num_qry_set = False
				division_qry_set = False
				pg_qry_set = False
				outage_qry_set = False
				system_qry_set = False

				start_date_qry = ''
				end_date_qry = ''
				ticket_num_qry = ''
				division_qry = ''
				pg_qry = ''
				outage_qry = ''
				system_qry = ''

				if doc['start_date_s'] == '' and doc['start_date_e'] == '':
					pass
				else:
					start_date_qry_set = True
					start_date_s = datetime.datetime.strptime(doc['start_date_s'], '%m/%d/%Y').strftime('%Y-%m-%d 00:00:00')
					start_date_e = datetime.datetime.strptime(doc['start_date_e'], '%m/%d/%Y').strftime('%Y-%m-%d 23:59:59')
					start_date_qry = " row_create_ts between '{start_date_s}' and '{start_date_e}' ".format(start_date_s=start_date_s,start_date_e=start_date_e)

				print 'prem-1'

				if doc['end_date_s'] == '' and doc['end_date_e'] == '':
					pass
				else:
					end_date_qry_set = True
					end_date_s = datetime.datetime.strptime(doc['end_date_s'], '%m/%d/%Y').strftime('%Y-%m-%d 00:00:00')
					end_date_e = datetime.datetime.strptime(doc['end_date_e'], '%m/%d/%Y').strftime('%Y-%m-%d 23:59:59')
					end_date_qry = " row_end_ts between '{end_date_s}' and '{end_date_e}' ".format(end_date_s=end_date_s,end_date_e=end_date_e)

				print 'prem-2'

				if doc['ticket_num'] == '':
					ticket_num_qry = ""
				else:
					ticket_num_qry_set = True
					ticket_num_qry = " ticket_num = '{ticket_num}' ".format(ticket_num=doc['ticket_num'])
				print 'prem-3'

				if doc['division'] in ['','Division','All']:
					division_qry = ""
				else:
					division_qry_set = True
					division_qry = " tb2.division_name = '{division}' ".format(division=doc['division'])

				print 'prem-31 == ', doc['pg']
				if len(doc['pg']) == 0:
					pg_qry = ""
				else:
					pg_qry_set = True
					pg_cds = ['"' + each + '"' for each in doc['pg']]
					pg_cds = ' , '.join(pg_cds)
					pg_cds = pg_cds + ' ,"{0}"'.format('ALL')
					pg_qry = " tb8.pg_cd in ({pg_cds}) ".format(pg_cds=pg_cds)
					
				print 'prem-4 == ', doc['outage_caused']

				if doc['outage_caused'] in ['Outage Caused','All']:
					outage_qry = ''
				else:
					outage_qry_set = True
					outage_qry = " tb5.outage_caused = '{outage_caused}' ".format(outage_caused=doc['outage_caused'])

				print 'prem-5'
				if doc['system_caused'] in ['System Caused','All']:
					system_qry = ''
				else:
					system_qry_set = True
					system_qry = " tb6.system_caused = '{system_caused}' ".format(system_caused=doc['system_caused'])

				order_qry = ' order by created_dt '

				print 'prem-6'


				
				
				qry = """
					select   tb1.ticket_num
							,tb1.row_create_ts
							,tb1.ticket_type
							,tb1.row_update_ts
							,tb1.row_end_ts
							,tb2.division_name
							,tb3.duration
							,tb4.error
							,tb5.outage_caused
							,tb6.system_caused
							,tb8.pg_cd
							,tb9.notes
							from sid.tickets tb1
							inner join
							sid.division tb2
							on tb1.division_id = tb2.division_id
							inner join
							sid.duration tb3
							on tb1.duration_id = tb3.duration_id
							inner join
							sid.error_count tb4
							on tb1.error_count_id = tb4.error_count_id
							inner join
							sid.outage_caused tb5
							on tb1.outage_caused_id = tb5.outage_caused_id
							inner join
							sid.system_caused tb6
							on tb1.system_caused_id = tb6.system_caused_id
							inner join
							sid.tickets_zips tb7
							on tb1.ticket_num = tb7.tickets_id
							inner join
							sid.pg tb8
							on tb7.pg_id = tb8.pg_id
							left outer join
							sid.addt_notes tb9
							on tb1.ticket_num = tb9.notes_id
					"""
				print 'start_date_qry == ', start_date_qry
				print 'end_date_qry == ', end_date_qry
				print 'ticket_num_qry == ', ticket_num_qry
				print 'division_qry == ', division_qry
				print 'outage_qry == ', outage_qry
				print 'system_qry == ', system_qry
				print 'pg_qry == ', pg_qry

				print 'start_date_qry == ', start_date_qry_set
				print 'end_date_qry == ', end_date_qry_set
				print 'ticket_num_qry == ', ticket_num_qry_set
				print 'division_qry == ', division_qry_set
				print 'outage_qry == ', outage_qry_set
				print 'system_qry == ', system_qry_set
				print 'pg_qry == ', pg_qry

				qry = qry 
				prev_qry_set = False

				if start_date_qry_set or end_date_qry_set or division_qry_set or pg_qry_set or outage_qry_set or system_qry_set:
				 	qry = qry + ' where ' 

				if start_date_qry_set:
					qry = qry + start_date_qry
					prev_qry_set = True 

				if end_date_qry_set:
					if prev_qry_set:
						qry = qry + ' and ' + end_date_qry 
						prev_qry_set = True
					else:
						qry = qry + end_date_qry
						prev_qry_set = False
				
				if ticket_num_qry_set:
					if prev_qry_set:
						qry = qry + ' and ' + ticket_num_qry 
						prev_qry_set = True
					else:
						qry = qry + ticket_num_qry
						prev_qry_set = False						

				if division_qry_set:
					if prev_qry_set:
						qry = qry + ' and ' + division_qry 
						prev_qry_set = True
					else:
						qry = qry + division_qry
						prev_qry_set = False
						

				if pg_qry_set:
					if prev_qry_set:
						qry = qry + ' and ' + pg_qry 
						prev_qry_set = True
					else:
						qry = qry + pg_qry
						prev_qry_set = False

				if outage_qry_set:
					if prev_qry_set:
						qry = qry + ' and ' + outage_qry  
						prev_qry_set = True
					else:
						qry = qry + outage_qry  
						prev_qry_set = False

				if system_qry_set:
					if prev_qry_set:
						qry = qry + ' and ' + system_qry 
					else:
						qry = qry + system_qry  
	
				print 'qry == ', qry
				cursor.execute(qry)
				results = cursor.fetchall()
				#results = []
			
			print 'enumerate results == results', len(results)
			prev_ticket_num = ''
			pg_cd = []
			
			for counter, each in enumerate(results):
				curr_ticket_num = each[0]
				if counter == 0:
					prev_ticket_num = curr_ticket_num				
								
				if prev_ticket_num == curr_ticket_num:
					data['ticket_num'] = each[0]
					data['created_dt'] = each[1]
					data['ticket_type'] = each[2]
					data['division'] = each[5]
					pg_cd.append(each[10])
					data['duration'] = each[6]
					data['error_count'] = each[7]
					data['outage_caused'] = each[8]
					data['system_caused'] = each[9]
					
					if each[11] is None:
						data['addt_notes'] = ""
					else:
						data['addt_notes'] = each[11]
				else:
					if 'ALL' in pg_cd:
						pg_cd = ['ALL']
					data['pg'] = pg_cd

					output.append(data)
					#print 'else output == ', data
					data = {}
					pg_cd = []

					data['ticket_num'] = each[0]
					data['created_dt'] = each[1]
					data['ticket_type'] = each[2]
					data['division'] = each[5]
					pg_cd.append(each[10])
					data['duration'] = each[6]
					data['error_count'] = each[7]
					data['outage_caused'] = each[8]
					data['system_caused'] = each[9]
					if each[11] is None:
						data['addt_notes'] = ""
					else:
						data['addt_notes'] = each[11]


				prev_ticket_num = curr_ticket_num

			if len(results) > 0:	
				data['pg'] = pg_cd
				output.append(data)
				#print 'else output == ', data

				data = {}
				pg_cd = []			


		except Exception as e:
			print 'Select Exception == ', e
			logger.debug("MySQLException == {0}".format(e))
			return JsonResponse({'status': 'failure'})

		print 'output == ', output
		# print 'len-output == ', len(output)
		
		return JsonResponse({'results': output})


class UpdateTicketData(View):

	@method_decorator(csrf_exempt)
	def dispatch(self, request, *args, **kwargs):
		return super(UpdateTicketData, self).dispatch(request, *args, **kwargs)

	def get(self, request):
		return JsonResponse({'status': 'success'})

	def post(self, request):
		print 'hi'
		alldata = request.POST
		print 'Update alldata ==', alldata
		
		if alldata.get('update') == 'Y':
		   ticket_num =  alldata.get('ticket_num')
		   ticket = Tickets.objects.get(ticket_num=ticket_num)
		   ticket.row_end_ts = datetime.datetime.now()
		   ticket.save()
		   return JsonResponse({'status': 'success'})

		t = Ticket(""
			,alldata.get('division')
			,alldata.getlist('zip')
			,alldata.get('error_count')
			,alldata.get('ticket_num')
			,alldata.get('outage_caused')
			,alldata.get('system_caused')
			,alldata.get('addt_notes')
			,alldata.get('ticket_type')
			,alldata.get('duration'))
		
		print 'update doc  == ', t
		logger.debug("Update document == {0}".format(t))
		
		try:
			with transaction.atomic():
				div,created = Division.objects.get_or_create(division_name=t.division)
				dur,created = Duration.objects.get_or_create(duration=t.duration)
				err,created = ErrorCount.objects.get_or_create(error=t.error_count)
				out,created = OutageCaused.objects.get_or_create(outage_caused=t.outage_caused)
				sys,created = SystemCaused.objects.get_or_create(system_caused=t.system_caused)
				
				
				try:
					ticket = Tickets.objects.get(ticket_num=t.ticket_num)
					ticket.division = div.ID
					ticket.duration = dur.ID
					ticket.error_count = err.ID
					ticket.outage_caused = out.ID
					ticket.system_caused = sys.ID
					ticket.save()
					AddtNotes.objects.get(Id=ticket).delete()
					AddtNotes.objects.create(Id=ticket,notes=t.addt_notes)
				except Tickets.DoesNotExist:
					ticket = None

				for each_zip in ticket.zips.all():
					ticket.zip.remove(each_zip)

				for each_zip in t.zip:
					p,created = Zip.objects.get_or_create(zip_cd=each_zip)
					ticket.zips.add(p)
				
		except Exception as e:
			print 'Exception == ', e 
			logger.debug("MySQLException == {0}".format(e))
			return JsonResponse({'status': 'failure'})
		
		

		return JsonResponse({'status': 'success'})
