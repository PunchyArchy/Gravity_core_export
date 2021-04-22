from traceback import format_exc
''' Decorator for wrapping func execution. Allows logging exceptions during execution, print it or display 
that everything is okay.Take a tag to mark and recognise certain functions'''


def operate_exc():
    # Operating exceptions
    print(format_exc())


def try_except_decorator(tag='execute func'):
    # Main body
    print('\nTrying to:', tag)

    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                func(*args, **kwargs)
                print('\tSuccess:', tag)
            except:
                print('\tFailed:', tag)
                operate_exc()
        return wrapper
    return decorator
