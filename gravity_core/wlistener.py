import socket
from time import sleep
from gravity_core import wsettings as s
import pickle
import threading
from datetime import datetime
from gravity_core.functions.tryexceptdecorator import *
from wsqluse.wsqluse import Wsqluse
from gravity_core import health_monitor


class WListener():
	''' Модуль для хранения всех внешних интерфейсов Wathman-core'''
	def __init__(self, logger):
		self.sqlshell = Wsqluse(s.db_name, s.db_user, s.db_pass, s.db_location)
		self.smlist = ['1']
		self.status = 'Готов'
		self.addInfo = {'carnum': 'none', 'status': 'none', 'notes': 'none'}
		self.activity = True
		self.connectedStatusListeners = []
		self.cm_logged_username = 'unknown'
		self.cm_logged_userid = 0
		self.logger = logger

	def wlisten_tcp(self):
		try:
			last = self.smlist[-1]
			return last
		except:
			self.logger.error(format_exc())

	def scale_reciever(self):
		client = socket.socket()
		while True:
			try:
				self.connect_cps(client)
				self.interact_cps(client)
			except:
				self.show_notification(format_exc())
				self.logger.error(format_exc())
				sleep(3)

	def connect_cps(self, client):
		# Connect to ComPortSplitter
		while True:
			try:
				client.connect((s.scale_splitter_ip, s.scale_splitter_port))
				break
			except:
				self.show_notification('Have no connection with CPS. Retry')
				sleep(3)

	def interact_cps(self, client):
		# Interaction with ComPortSplitter
		self.show_notification('TRACK.Начали взаимодейтвие с CPS')
		while True:
			#self.show_notification()('Ждем данные от CPS')
			data = client.recv(1024)
			if not data: break
			#data = str(data)
			data = data.decode(encoding='utf-8')
			#self.show_notification()('Got data', data)
			self.format_weight(data)
			#self.show_notification()('c1')
			if 'x00' in data:
				self.show_notification('Weight terminal was been disconnected')

	def format_weight(self, weight):
		self.rcv_data = weight
		self.smlist = self.cut_list(self.smlist)
		self.smlist.append(int(self.rcv_data))

	def cut_list(self, listname, lastcount=-10):
		return listname[lastcount:]

	def statusSocket(self):
		serv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		serv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		serv.bind((s.statusSocketIp, s.statusSocketPort))
		serv.listen(10)
		while True:
			newConn = {}
			conn,addr = serv.accept()
			self.show_notification('Есть подключение к API серверу статусов')
			newConn[conn] = 0
			self.connectedStatusListeners.append(newConn)

	def broadcastMsgSend(self, msg):
		'''Отправляет сообщения по всем подключенным клиентам'''
		self.show_notification('Ширковещательная отправка', msg)
		self.show_notification('По клиентам:', self.connectedStatusListeners, debug=True)
		msg = pickle.dumps(msg)
		for dict_name in self.connectedStatusListeners:
			# Перебираем каждого клиентаR
			for conn, count in dict_name.items():
			# Берем адрес, счетчик (удаления) клиента
				if count < 3:
				# Если счетчик < 3
					self.show_notification('\nОтправка клиенту CM', debug=True)
					try:
						self.show_notification('\tПопытка отправки сообщения клиенту CM', debug=True)
						conn.send(msg)
						# Сбрасываем счетчик клиента
						dict_name[conn] = 0
						self.show_notification('\t\tУспешно!')
					except:
					# Если отправить не получилось
						self.show_notification('\t\tПопытка отправки завершилась неудачей.', debug=True)
						self.show_notification(format_exc())
						self.logger.error(format_exc())
						# Инкрементируем счетчик, ждем пол-секунды перед следующей попыткой
						dict_name[conn] += 1
				else:
					self.show_notification('count > 3', count)
		for dict_name in self.connectedStatusListeners:
			for conn, count in dict_name.items():
				if count >= 3:
					try:
						self.connectedStatusListeners.remove(dict_name)
					except:
						pass

	def dispatcher(self, ip, port, serving_loop, start_msg='API запущен', conn_est_msg='Есть подключение'):
		'''Ассинхронно обслуживает каждого клиента, который подключается к
		API серверу'''
		serv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		serv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		serv.bind((ip, port))
		serv.listen(24)
		while True:
			self.show_notification(start_msg)
			conn, addr = serv.accept()
			if not conn: break
			self.show_notification(conn_est_msg)
			threading.Thread(target=self.cmUseInterface, args=(conn, serving_loop)).start()

	@try_except_decorator('Попытка зафиксировать системное событие')
	def cm_events_make_record(self, event):
		# GET CM EVENT ID
		command = "SELECT id FROM {} WHERE description='{}' LIMIT 1".format(s.cm_events_table, event)
		response = self.sqlshell.try_execute_get(command)
		event_id = response[0][0]
		timenow = datetime.now()
		command = "INSERT INTO {} (event, datetime, operator) VALUES ({},'{}', {})".format(s.cm_events_log_table,
																						   event_id, timenow,
																						   self.cm_logged_userid)
		self.sqlshell.try_execute(command)

	def cmUseInterface(self, conn, serving_loop):
		'''Обработка каждого клиента, которые подключается к API'''
		try:
			while 1:
				self.show_notification('Блокирование сокета')
				self.show_notification('Ждем данные от CM')
				comm = conn.recv(1024)
				if not comm: break
				self.show_notification('\nGot comm from CM:', comm)
				response = serving_loop(comm)
				response = pickle.dumps(response)
				conn.send(response)
				self.show_notification('\tComm sent\n')
		except:
			self.show_notification('cmUseInterface has been crashed. Reloading...')
			self.show_notification(format_exc())

	def cm_sql_operator_loop(self, comm):
		comm = comm.decode(encoding='utf-8')
		if 'select' in comm.lower():
			response = self.sqlshell.try_execute_get(comm)
			return response
		elif 'update' in comm.lower() and ('рГ2' or  'Добавочно:' or 'Было исправлено.' in comm):
			self.sqlshell.try_execute(comm)
			response = self.status
		else:
			self.show_notification('Unknown SQL command!', comm)
			response = self.status
		return response

	@try_except_decorator('Попытка фиксации авторизации')
	def auth_cm_user(self, comm, response):
		# Обработка успешной авторизации пользователя СМ
		#self.show_notification()('GOT RESPONSE', response)
		if "select role,password" in comm.lowerf() and len(response) > 0 and response[0][1] == True:
			self.save_cm_auth_info(response[0][0], response[0][2])
			self.cm_events_make_record(s.cm_login_event)

	@try_except_decorator('Попытка сохранить данные об авторизации')
	def save_cm_auth_info(self, username, userid):
		# Сохраняет информацию о авторизованном пользователе СМ
		self.cm_logged_username = username
		self.cm_logged_userid = userid

	def executeComm(self, comm):
		""" Первичный обработчик команд, поступающих в API. Так-же формирует ответ на каждую комманду """
		comm = pickle.loads(comm)
		self.show_notification('GET COMM', comm)
		for k, v in comm.items():
			command = k
			info = v
		if command == 'status':
			self.show_notification('\tGot status request.')
		if command == 'start_car_protocol' or command == 'get_ar_info' or command == 'gate_manual_control':
			threading.Thread(target=self.wcore.operate_external_command, args=(comm,)).start()
			self.addInfo['status'] = 'Данные получены'
		elif command == 'cm_user_auth':
			self.save_cm_auth_info(info['username'], info['userid'])
			self.cm_events_make_record(s.cm_login_event)
			self.wcore.operate_external_command(comm)
		elif command == 'add_comm':
			# Поступила команда от СМ на добавление комментария к заезду
			self.wcore.operate_external_command(comm)
		elif command == 'change_record':
			# Поступила команда от СМ на изменение незавершенного заезда
			self.wcore.operate_external_command(comm)
		elif command == 'cm_start':
			self.cm_events_make_record(s.cm_start_event)
		elif command == 'cm_stop':
			self.cm_events_make_record(s.cm_stop_event)
		else:
			self.show_notification('Unknown command!', command)
		response = self.status
		if command == 'get_health_info':
			response = health_monitor.general_status
		self.show_notification('sending response', response)
		return response

	def setStatus(self, status):
		self.status = status

	def setStatusObj(self, obj):
		self.statusObj = obj

	def getStatus(self):
		return self.status

	def set_wcore(self, wcore):
		# Передать экземпляр WCore для работы
		self.wcore = wcore

	def join_tuple_string(self, msg):
		return ' '.join(map(str, msg))

	def show_notification(self, *args, debug=False):
		args = self.join_tuple_string(args)
		if debug and s.GENERAL_DEBUG:
			print(args)
		elif not debug:
			print(args)

