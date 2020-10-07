from .distributed_file_system import Storage
import tempfile

storage = Storage()

operations = {
    #       'init': Storage.clear,
    'create': storage.create_file,
    #       'read': Storage.read_file,
    #       'write': Storage.write_file,
    'delete': storage.delete_file,
    'info': storage.get_file_size,
    'copy': storage.copy_file,
    'move': storage.move_file,
    'readdir': storage.read_dir,
    'makedir': storage.make_dir,
    'deletedir': storage.delete_dir
}


def parse(args, file=None):
    op = args[0]
    try:
        func = operations[op]
        print(*(args[1:]))
        answer = func(*(args[1:]))
        return answer
    except:
        pass

    try:
        if op == 'init':
            storage.clear()
            return None
        if op == 'read':
            with tempfile.TemporaryFile() as fp:
                storage.read_file(*(args[1:]), fp)
                return fp
        if op == 'write':
            storage.read_file(*(args[1:]), file)
            return None
    except:
        return "The query can not be executed!"
