import ftplib
from gravity_core import wsettings as s
from datetime import datetime
from gravity_core.functions.tryexceptdecorator import *


class WSender:
	def __init__(self, hostname, login, pw):
		self.tm_time = s.logs_send_rate + 300
		print('REPORTING. Creating FTP shell on', hostname)
		self.h = hostname
		self.login = login
		self.password = pw

	def make_connection(self):
		self.ftp = ftplib.FTP(self.h, timeout=self.tm_time)
		self.ftp.login(self.login, self.password)

	def get_today_fname(self):
		now = datetime.now()
		fname = now.strftime('%d-%m-%y')
		return fname

	@try_except_decorator('Cоздание сегодняшней директории')
	def mk_today_dir(self):
		self.fname = self.get_today_fname()
		self.ftp.cwd('/ftp/rfid_logs')
		self.ftp.mkd(self.fname)

	def formate_name(self, fname):
		flist = fname.split('-')
		if len(flist) == 3:
			fyear = flist[0].split('/')[-1]
			fyear = fyear[2:]
			fname = flist[2]+'-'+flist[1]+'-'+fyear
			return fname

	def ftp_upload(self, path, ftype='TXT'):
		# Функция для загрузки файлов на FTP-сервер
		# @param ftp_obj: Объект протокола передачи файлов
		# @param path: Путь к файлу для заcargoки
		print('REPORTING. FTP UPLOAD FOR', path)
		if ftype == 'TXT':
			print('REPORTING. SEND TXT')
			with open(path, 'rb') as fobj:
				print('REPORTING. SPLITTING')
				path = path.split('/')[-1]
				print('REPORTING. PATH-', path)
				print('REPORTING. STORING...')
				self.ftp.storlines('STOR ' + path, fobj)
				print('REPORTING. Успешно загружено на ФТП', path)
		else:
			print('REPORTING. SEND SOMETHING ELSE')
			with open(path, 'rb') as fobj:
				path = path.split('/')[-1]
				self.ftp.storbinary('STOR ' + path, fobj, 1024)
				print('REPORTING. Успешно загружено на ФТП', path)

	def open_connection(self):
		timeout = self.tm_time
		self.ftp = ftplib.FTP(self.h, timeout=timeout)
		self.ftp.login(self.login, self.password)
		self.ftp.set_pasv(False)
		self.ftp.sendcmd('PASV')

	def move_to_today_dir(self):
		self.ftp.cwd('/ftp/rfid_logs')
		self.ftp.cwd(self.fname)

	def send_file(self, filename):
		fname = self.formate_name(filename)
		if fname == self.fname:
			print('MATCH!')
			self.ftp_upload(filename)

	def move_to_dir(self, dirname):
		#self.ftp.cwd('ftp')
		self.ftp.cwd(dirname)
