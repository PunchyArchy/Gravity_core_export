def get_unfinished_cycles(sqlshell, *args, **kwargs):
    """ Вернуть все открытые записи (без тары) """
    command = "SELECT * FROM records WHERE inside=True"
    response = sqlshell.get_table_dict(command)
    return response

def try_auth_user(sqlshell, username, password, users_table, *args, **kwargs):
    """ Попытка авторизации. Возвращает {'status': 'success', info:[{'role':...,'password':..., 'id':...}],
    если все прошло успешно. status - failed 0, если пароль или логин неверные """
    command = "SELECT role,password = crypt('{}', password), id FROM {} where username='{}'"
    command = command.format(password, users_table, username)
    response = sqlshell.get_table_dict(command)
    return response
