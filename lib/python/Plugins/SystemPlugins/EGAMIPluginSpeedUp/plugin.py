from Plugins.Plugin import PluginDescriptor
from enigma import iPlayableService, eServiceCenter, iServiceInformation
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Components.ActionMap import ActionMap
from Components.ConfigList import ConfigListScreen
from Components.config import getConfigListEntry
from Components.Label import Label
from Components.PluginComponent import plugins
from Components.ServiceEventTracker import ServiceEventTracker
from Components.UsageConfig import *
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
from traceback import print_exc
from threading import Thread
from os import path
doit = True
WaitForTVInstance = None

def startOpenWebInterface(session):
    try:
        from Plugins.Extensions.OpenWebif.httpserver import HttpdStart
        HttpdStart(session)
    except:
        print_exc()


class EGAMIPluginLoadScreen(ConfigListScreen, Screen):

    def __init__(self, session, args = 0):
        Screen.__init__(self, session)
        self.session = session
        self.skinName = ['Setup']
        Screen.setTitle(self, _('EGAMI Plugins Speed Up'))
        list = []
        list.append(getConfigListEntry(_('Load plugin list after TV display'), config.usage.async_plug_load))
        self['key_red'] = Label(_('Exit'))
        self['key_green'] = Label(_('Save'))
        self['key_blue'] = Label(_('Reload'))
        ConfigListScreen.__init__(self, list)
        self['actions'] = ActionMap(['OkCancelActions', 'ColorActions'], {'red': self.dontSaveAndExit,
         'green': self.saveAndExit,
         'blue': self.reloadNow,
         'cancel': self.dontSaveAndExit}, -1)

    def reloadNow(self):
        try:
            plugins.readPluginList(resolveFilename(SCOPE_PLUGINS))
            self.session.open(MessageBox, _('The plugins were reloaded successfully!'), MessageBox.TYPE_INFO, timeout=3)
        except:
            print_exc()

    def saveAndExit(self):
        for x in self['config'].list:
            x[1].save()

        config.usage.save()
        self.close()

    def dontSaveAndExit(self):
        for x in self['config'].list:
            x[1].cancel()

        self.close()


class LoadPlugins(Thread):

    def __init__(self, session):
        Thread.__init__(self)
        self.session = session

    def run(self):
        try:
            plugins.readPluginList(resolveFilename(SCOPE_PLUGINS))
        except:
            print_exc()


class WaitForTV:

    def __init__(self, session):
        try:
            self.session = session
            self.service = None
            self.onClose = []
            self.__event_tracker = ServiceEventTracker(screen=self, eventmap={iPlayableService.evUpdatedInfo: self.__evUpdatedInfo})
        except:
            print_exc()

    def __evUpdatedInfo(self):
        global doit
        try:
            if doit is True:
                doit = False
                service = self.session.nav.getCurrentService()
                if service is not None:
                    ret = LoadPlugins(self.session)
                    ret.start()
        except:
            print_exc()


def main(session, **kwargs):
    global WaitForTVInstance
    if WaitForTVInstance is None:
        WaitForTVInstance = WaitForTV(session)


def openMenu(session, **kwargs):
    session.open(EGAMIPluginLoadScreen)


def Plugins(path, **kwargs):
    desc_autostart = PluginDescriptor(where=[PluginDescriptor.WHERE_SESSIONSTART], fnc=main)
    desc_pluginmenu = PluginDescriptor(name=_('EGAMI Plugins Speed Up'), description=_('Asynchronous plugins loading'), where=[PluginDescriptor.WHERE_PLUGINMENU], fnc=openMenu)
    list = []
    if config.usage.async_plug_load.value:
        list.append(desc_autostart)
    return list
