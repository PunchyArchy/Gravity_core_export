from wsqluse.wsqluse import Wsqluse

sqlshsell = Wsqluse('wdb', 'watchman', 'hect0r1337', '192.168.100.109', debug=True)
#sqlshsell.try_execute('delete from clients where length(id_1c) > 5')
sqlshsell.try_execute("update clients set id_1c='0000000' || id_1c where length(id_1c) = 1")