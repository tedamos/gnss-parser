from logging import error
from kivy.lang import Builder
from kivy.properties import ObjectProperty

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.icon_definitions import md_icons
from kivy.uix.screenmanager import Screen, ScreenManager
from kivymd.uix.textfield import MDTextField
from kivymd.toast import toast
from kivy.factory import Factory
from kivy.core.window import Window
from kivymd.uix.filemanager import MDFileManager
from kivy.clock import Clock
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.popup import Popup
from kivymd.uix.picker import MDDatePicker
from kivymd.uix.button import MDFlatButton, MDRaisedButton
from kivymd.uix.dialog import MDDialog

from datetime import datetime
import sys
import json
import os
import re

from file_handler import ReachHandler

from app_config.theming import *

class ConversionForm(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class AcknowledgeScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class WindowManager(ScreenManager):
    pass

class LoadDialog(FloatLayout):
    load = ObjectProperty(None)
    cancel = ObjectProperty(None)

class TEDAGNSS(MDApp):
    title = "Terradata GNSS Converter"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._point_name = None
        self._antenna_height = None
        self._file_path = None
        self._file_name = None
        self._obs_date = None
        self._recording_date = None
        self._handler = None
        self._project_number = None

        f = open(os.path.join(os.path.dirname(__file__), 'config_template.json'))
        self._config = json.load(f)
        f.close()

        Window.bind(on_keyboard=self.events)
        self.manager_open = False
        self.file_manager = MDFileManager(
            exit_manager=self.exit_manager,
            select_path=self.select_path,
            ext=['.zip']
        )

        self.error_dialog = MDDialog(
                text='',
                buttons=[
                    MDFlatButton(
                        text="SCHLIESSEN",
                        theme_text_color="Custom",
                        text_color=self.theme_cls.primary_color,
                        on_release=self.dismiss_error_dialog
                    )
                ],
            )
        
        self.success_dialog = MDDialog(
                text='Konversion erfolgreich.',
                buttons=[
                    MDFlatButton(
                        text="FERTIG",
                        theme_text_color="Custom",
                        text_color=self.theme_cls.primary_color,
                        on_release=self.dismiss_success_dialog
                    ),
                    MDFlatButton(
                        text="WEITERE MESSUNGEN FÜR GLEICHEN PUNKT",
                        theme_text_color="Custom",
                        text_color=self.theme_cls.primary_color,
                        on_release=self.dismiss_success_dialog_add_more
                    )
                ],
            )

    def build(self):
        self.theme_cls.primary_palette = "Blue"
        
        self.root = Builder.load_file(os.path.join(os.path.dirname(__file__), 'teda_gnss.kv'))

    def file_manager_open(self):
        self.file_manager.show(os.path.dirname(__file__))  # output manager to the screen
        self.manager_open = True

    def select_path(self, path):
        '''It will be called when you click on the file name
        or the catalog selection button.

        :type path: str;
        :param path: path to the selected directory or file;
        '''
        # file_name = path[path.rindex('\\')+1:]
        # if not self._file_path:
        #     self._file_path = [path]
        #     self._file_name = [file_name]
        # else:
        #     self._file_path.append(path)
        #     self._file_name.append(file_name)
        
        
        # self.root.current_screen.ids.select_file.text = ', '.join(self._file_name)
        # self.exit_manager()
        # toast(path)
        self._file_path = path
        self._file_name = self._file_path[self._file_path.rindex('\\')+1:]
        self.root.current_screen.ids.select_file.text = self._file_name
        self.exit_manager()
        toast(path)

    def exit_manager(self, *args):
        '''Called when the user reaches the root of the directory tree.'''

        self.manager_open = False
        self.file_manager.close()

    def events(self, instance, keyboard, keycode, text, modifiers):
        '''Called when buttons are pressed on the mobile device.'''

        if keyboard in (1001, 27):
            if self.manager_open:
                self.file_manager.back()
        return True
    

    ### DATE PICKER BUGGED. TAKING DATE FROM DOWNLOADED DIRECTORY ###
    # def get_date(self, date):
    #     self._recording_date = date

    # def show_date_picker(self):
    #     date_dialog = MDDatePicker(callback=self.get_date,)
    #     date_dialog.open()

    def parse_file(self):

        error_list = []

        if self.root.current_screen.ids.project_number.text:
            match = re.match(
                r"^\d{5}\.\d{2}$",
                self.root.current_screen.ids.project_number.text
            )
            if match:
                self._project_number = self.root.current_screen.ids.project_number.text
            else:
                error_list.append('eine gültige Projektnummer')
        else:
            error_list.append('eine gültige Projektnummer')

        if self.root.current_screen.ids.point_name.text:
            self._point_name = self.root.current_screen.ids.point_name.text
        else:
            error_list.append('einen Punktnamen')
        
        if self.root.current_screen.ids.antenna_height.text:
            try:
                self._antenna_height = float(self.root.current_screen.ids.antenna_height.text)
            except ValueError:
                error_list.append('eine gültige Antennenhöhe')
        else:
            error_list.append('eine gültige Antennenhöhe')
            
        if self.root.current_screen.ids.observation_date.text:
            try:
                self._obs_date = datetime.strptime(
                    self.root.current_screen.ids.observation_date.text,
                    '%Y-%m-%d'    
                )
            except ValueError:
                error_list.append('ein gültiges Beobachtungsdatum')
        else:
                error_list.append('ein gültiges Beobachtungsdatum')

        if not error_list and self._file_path:
            if not self._handler:
                self._handler = ReachHandler(name=self._point_name)
            self._handler.parse_file(self._file_path, self._config, self._obs_date, self._antenna_height, self._project_number)
            self.success_dialog.open()
        else:
            self.show_error_dialog(error_list)

    def show_error_dialog(self, error_list):
        file_path_text = ' und wähle ein Beobachtungsfile aus' if not self._file_path else ''
        error_text = f'Gib {", ".join(error_list)} ein{file_path_text}.'
        self.error_dialog.text = error_text
        self.error_dialog.open()

    def dismiss_error_dialog(self, *args):
        self.error_dialog.dismiss()

    def dismiss_success_dialog(self, *args):
        self._handler.zip_exports(self._config, self._project_number, self._obs_date)

        self._file_name, self._obs_date, self._antenna_height, self._point_name = [None]*4
        
        self.root.current_screen.ids.point_name.text = 'Punktname eingeben'
        self.root.current_screen.ids.antenna_height.text = 'Antennenhöhe eingeben [m]'
        self.root.current_screen.ids.observation_date.text = 'Beobachtungsdatum (YYYY-MM-DD)'
        self.root.current_screen.ids.select_file.text = 'Beobachtungsdatei auswählen'

        self._handler = None

        self.success_dialog.dismiss()

    def dismiss_success_dialog_add_more(self, *args):
        self._file_name = None

        self.root.current_screen.ids.select_file.text = 'Beobachtungsdatei auswählen'

        self.success_dialog.dismiss()

def main(config_file):
    root = os.path.dirname(__file__)
    config_file = os.path.join(root, config_file)

    # Open configuration file
    f = open(config_file)
    config = json.load(f)
    f.close()
    
    TEDAGNSS().run()
    
    # file_path = input('Enter path of file to be parsed:\t')
    # name = input('Enter receiver name:\t')
    # recording_time = datetime.strptime(input('Enter recording date (DD.MM.YYYY):\t'), '%d.%m.%Y')

    # handler = ReachHandler(name=name)

    # handler.parse_file(file_path, config, recording_time)

if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'config_template.json')