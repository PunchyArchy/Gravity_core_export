from gravity_core.wsqluse_sub import WChecker
from gravity_core.tests import settings_test as s

shell = WChecker(s.wdb_name, s.wdb_user, s.wdb_pass, s.wdb_host, debug=True)
#gdb_shell = WChecker('gdb', 'qodex', 'Hect0r1337%', '192.168.234.252')