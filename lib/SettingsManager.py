import json
import os
import datetime
import __main__

from .Utils import projectDir, datetime_std_format

MAIN_FNAME      = os.path.basename( __main__.__file__ ).replace( ".py", "" )
SETT_DIR        = os.path.join( projectDir(), "settings" )
SETT_FULL_PATH  = os.path.join( SETT_DIR, f"{MAIN_FNAME}.json" )

DEF_BOT_SETT = { "bot":
                        {
                            "language":"ru"
                        }
                }
DEF_USR_SETT = { "language":"ru" }

class SettingsManager:
    settings = {}
    __bFileDamaged = False

    def __new__( self ):
        raise NotImplementedError( "No need to have an instance of SettingsManager." )

    @classmethod
    def load( cls ):
        cls.settings = DEF_BOT_SETT

        try:
            with open( SETT_FULL_PATH, "r" ) as read_file:
                cls.settings = json.load( read_file )

        except FileNotFoundError as error:
            if not os.path.exists( SETT_DIR ):
                os.makedirs( SETT_DIR )

        except json.decoder.JSONDecodeError as error:
            cls.__bFileDamaged = True
            print( f"Settings file damaged '{ SETT_FULL_PATH }' : { error }!" )                    

        except Exception as error:
            print( error )

    @classmethod
    def save( cls ):
        # не перезаписываем файл настроек, если он был поврежден,
        # записываем настройки с добавлением в имя файла текущей даты
        settings_path = SETT_FULL_PATH

        if cls.__bFileDamaged:
            dt = datetime_std_format(time_sep="-")
            settings_path = os.path.join( SETT_DIR, f"{MAIN_FNAME}_{dt}.json" )
            print (f"Warning: Settings file {SETT_FULL_PATH} is damaged.\n Saved as {settings_path}")

        if not os.path.exists( SETT_DIR ):
            os.mkdir( SETT_DIR )

        with open( settings_path, "w") as f:
            json.dump(cls.settings, f, indent=4)

    
    @classmethod
    def __update_setting(cls, section, setting, value):
        section_settings = cls.settings.get(section)
        
        if section_settings is not None:
            section_settings[setting] = value
        else:
            section_settings = {setting:value}
        
        cls.settings[section] = section_settings
        cls.save()

    @classmethod
    def update_bot_setting(cls, setting, value):
        cls.__update_setting( "bot", setting, value )

    @classmethod
    def update_usr_setting(cls, chat_id:int, setting, value):
        assert type(chat_id) == int, f"chat_id must be an integer not {type(chat_id)}"
        cls.__update_setting( str(chat_id), setting, value )

    @classmethod
    def get_bot_setting(cls, setting, alt_val = None):
        try:
            return cls.settings["bot"][setting]
        except KeyError:
            return DEF_BOT_SETT[setting] if alt_val is None else alt_val

    @classmethod
    def get_usr_setting(cls, chat_id, setting, alt_val_expr = None):
        '''alt_val_expr is an alternate function for getting
        setting value if it is not present in current settings'''
        try:
            assert type(chat_id) == int, f"chat_id must be an integer not {type(chat_id)}"
            return cls.settings[str(chat_id)][setting]
        except KeyError:
            if alt_val_expr is not None:
                try:
                    return alt_val_expr()
                except:
                    val = DEF_USR_SETT.get(setting)
                    assert val is not None, f"{DEF_USR_SETT} must contain value for {setting}"
                    return val