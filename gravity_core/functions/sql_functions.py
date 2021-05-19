def get_unfinished_cycles(sqlshell, *args, **kwargs):
    command = "SELECT * FROM records WHERE inside=True"
    response = sqlshell.get_table_dict(command)
    return response