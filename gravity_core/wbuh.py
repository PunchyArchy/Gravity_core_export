""" Модуль для интеграции с внешней системой (1С, например)"""


from gravity_core import wsettings as s
from wsqluse.wsqluse import Wsqluse
from gravity_core.wftpsender import WSender
import threading
from time import sleep


class BuhIntegration:
	def __init__(self, sqlshell, ftpshell):
		self.ftpshell = ftpshell
		self.sqlshell = sqlshell

	def upd_cycle(self, source, dist):
		while True:
			self.importData(source, dist)
			sleep(3600)

	def importData(self, source, dist):
		# Импортировать данные из FTP (source) на локальное хранилище (dist)
		self.saveFile(source, dist)
		self.updClientsTable(dist)

	def saveFile(self, source, dist):
		self.ftpshell.open_connection()
		with open(dist, 'wb') as f:
			self.ftpshell.ftp.retrbinary('RETR ' + '{}'.format(source), f.write)

	def clear_inn(self, inn):
		clear_inn = ''
		for digit in inn:
			if digit.isdigit():
				clear_inn += digit
		return clear_inn

	def updClientsTable(self, filename):
		""" Обновить таблицу """
		print('\n\tОбновление базы данных ')
		fobj = open(filename, 'r', encoding='cp1251')
		fobj = fobj.readlines()
		for rec in fobj:
			new_rec = rec.split('|')
			rec_type = new_rec[0]
			if rec_type.strip() == 'CLIENT':
				template = 'id_1c,short_name,full_name,status,access,other,date,inn'
				id_1c = new_rec[1]
				short_name = new_rec[2]
				full_name = new_rec[3]
				status = new_rec[4]
				access = new_rec[5]
				other = new_rec[6]
				date = new_rec[7]
				inn = new_rec[8].replace('\n', '')
				inn = self.clear_inn(inn)
				record = tuple((id_1c, short_name, full_name, status, access, other, date, inn))
				command = "insert into {} ({}) values {} ".format(s.clients_table, template, record)
				command += "on conflict (id_1c) do update "
				command += "set short_name='{}', full_name='{}', ".format(short_name, full_name)
				command += "status='{}', access='{}', other='{}', ".format(status, access, other)
				command += "date='{}', inn='{}'".format(date, inn)
				self.sqlshell.try_execute(command)
			elif len(new_rec) == 4 and rec_type == 'TID':
				template = 'locate, date, info_type'
				locate = new_rec[1]
				date = new_rec[2]
				info_type = new_rec[3].replace('\n', '')
				record = tuple((locate, date, info_type))
				record = str(record)
				command = 'insert into exchange_date ({}) values {} '.format(template, record)
				command += "on conflict (locate) do update set date='{}'".format(date)
				self.sqlshell.try_execute(command)
		print('\t\tУспешно!')
