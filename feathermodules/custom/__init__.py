import os

path_to_custom_dir = os.path.dirname(os.path.realpath(__file__))

def py_and_not_init(filename):
   return (filename[-3:] == '.py' and filename != '__init__.py')

__all__ = [x[:-3] for x in list(filter(py_and_not_init, os.listdir(path_to_custom_dir)))]
