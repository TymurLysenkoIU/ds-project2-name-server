from .distributed_file_system import storage
import tempfile
class Request_parser:

    def __init__(self):
        pass

    operations = {
#       'init': Storage.clear,
        'create': storage.Storage.create_file,
#       'read': Storage.read_file,
#       'write': Storage.write_file,
        'delete': storage.Storage.delete_file,
        'info': storage.Storage.get_file_size,
        'copy': storage.Storage.copy_file,
        'move': storage.Storage.move_file,
        'readdir': storage.Storage.read_dir,
        'makedir': storage.Storage.make_dir,
        'deletedir': storage.Storage.delete_dir
    }

    def parse(self, args, file=None):
        op = args[0]
        try:
            func = self.operations[op]
            print(*(args[1:]))
            answer = func(*(args[1:]))
            return answer
        except:
            pass

        try:
            if (op == 'init'):
                answer = storage.Storage()
                answer = answer.clear()
                return answer
            if (op=='read'):
                with tempfile.TemporaryFile() as fp:
                    answer = storage.Storage()
                    answer = answer.read_file(*(args[1:]), fp)
                    return fp
            if (op=='write'):
                answer = storage.Storage()
                answer = answer.read_file(*(args[1:]), file)
                return answer
        except:
            return "The query can not be executed!"

