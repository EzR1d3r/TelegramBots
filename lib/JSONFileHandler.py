import json
import os
import datetime
from copy import deepcopy

from .Utils import datetime_std_format


class JSONFileHandler:
    def __init__(self, path, default:dict = None):
        self.__path = path
        self.__dir_name = os.path.dirname( self.__path )
        self.__basename = os.path.basename( path )
        self.__dict_obj = deepcopy(default) if default is not None else {}
        self.__default  = deepcopy(default)
        self.__file_damaged = False

        self.load()

    def load( self ):
        try:
            with open( self.__path, "r" ) as read_file:
                self.__dict_obj = json.load( read_file )

        except FileNotFoundError as error:
            print( f"Warning. File {self.__path} not found. It will create when save method call." )

        except json.decoder.JSONDecodeError as error:
            self.__file_damaged = True
            print( f"Settings file damaged '{ self.__path }' : { error }!" )                    

        except Exception as error:
            print( error )

    def __save( self ):
        if not os.path.exists( self.__dir_name ):
            os.mkdir( self.__dir_name )

        path = self.__path

        # не перезаписываем файл настроек, если он был поврежден,
        # записываем настройки с добавлением в имя файла текущей даты
        if self.__file_damaged:
            dt = datetime_std_format(time_sep="-")
            path = os.path.join( self.__dir_name, f"{self.__basename}_cached_{dt}.json" )
            print (f"Warning: Settings file {self.__path} is damaged.\n Saved as {path}")

        with open( path, "w") as f:
            json.dump(self.__dict_obj, f, indent=4)

    def update(self, key, value):
        self.__dict_obj[ str(key) ] = json.loads( json.dumps(value) )
        self.__save()

    def get(self, *keys, alt_val_expr = lambda:None):
        '''alt_val_expr is an alternate function for getting
        setting value if it is not present in current settings'''
        try:
            val = self.__dict_obj
            for key in keys:
                val = val[key]
            return val
        except KeyError:
            try:
                return alt_val_expr()
            except:
                return None


# class ValueGetWrapper:
#     def __init__(self, value):
#         self.value = value

#     def __getitem__(self, key):
#         raise KeyError("Invalid use of NoneWrapper, you have to use get() method")

#     def val(self):
#         return self.value
    
#     def get(self, key):
#         try:
#             return ValueGetWrapper( self.value[key] )
#         except (KeyError, TypeError):
#             return ValueGetWrapper(None)