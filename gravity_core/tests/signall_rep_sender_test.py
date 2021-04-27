from gravity_core.reports import signall_reports_funcs as sig_funcs
from wsqluse.wsqluse import Wsqluse
from gravity_core.functions import wserver_interaction


#wserver_client = wserver_interaction.create_wserver_connection()
#poligon_id = wserver_interaction.auth_poligon(wserver_client)
sqlshsell = Wsqluse('wdb', 'watchman', 'hect0r1337', '192.168.100.109', debug=True)

def send_test():
    sig_funcs.send_json_reports(sqlshsell, wserver_client, poligon_id)

def select_test():
    a = sig_funcs.get_reports(sqlshsell)
    print(a)

select_test()

