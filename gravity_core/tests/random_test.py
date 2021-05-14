from gravity_core.tests.sqlhell_test import shell

all_records = [738586, 739123]
for wserver_id in all_records:
    command = "update records set wserver_id=null, wserver_get=null where wserver_id={}".format(wserver_id)
    shell.try_execute(command)