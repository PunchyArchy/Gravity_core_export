from gravity_core.functions.sql_functions import try_auth_user
from gravity_core.tests.sqlhell_test import shell


def try_auth_user_test():
    username = 'test_user_1'
    password = '123'
    response = try_auth_user(shell, username, password, 'users')
    print("Response:", response)


try_auth_user_test()