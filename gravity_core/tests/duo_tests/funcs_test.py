from gravity_core.functions import duo_functions as df
from gravity_core.tests.sqlhell_test import shell
from gravity_core import wsettings as s


def test_fetch_wserver_id():
    return df.fetch_wserver_id(shell, 'Элеваторная', s.connection_status_table, s.pol_owners_table)

print(test_fetch_wserver_id())