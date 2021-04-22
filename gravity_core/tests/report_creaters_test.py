from gravity_core.reports import internal_report_creaters as rc
from gravity_core.reports import internal_reports_funcs as rf
from gravity_core.wsqluse_sub import WChecker
import datetime

shell = WChecker('wdb', 'watchman', 'hect0r1337', '192.168.100.109')
start_date = rf.get_last_ftp_export_date(shell)
begin = datetime.datetime.now()
rc.saveDbXMLext(shell, filename='test.xml', tablename='records', start_date=start_date)
end = datetime.datetime.now() - begin
print('Время выполнения: {}'.format(end.seconds))