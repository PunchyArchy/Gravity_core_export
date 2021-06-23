from gravity_core import support_funcs
from wsqluse.wsqluse import Wsqluse

shell = Wsqluse('wdb', 'watchman', 'hect0r1337', 'localhost')
response = support_funcs.get_rec_id(shell, 'А563ОЕ702')
print("RESPONSE:", response)
