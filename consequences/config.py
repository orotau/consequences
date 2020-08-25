'''Specify, Get and Use the Config File'''

import socket
import sys
import configparser


class ConfigFile():

    # Updating the dictionary config_files??
    # Make sure the dictionary keys (computer names) are unique
    # Otherwise you will just get the last entry for the computer!

    config_paths = {
        'graham-HP-Laptop': '/home/graham/PythonProjects/consequences/config.txt',
        'graham-desktop-ubuntu': '/home/graham/PythonProjects/consequences/config.txt',
        }

    def __init__(self):
        self.computername = self.getComputerName()
        self.path = self.getPath()
        self.configfile = self.getConfigFile()

    def getComputerName(self):
        return socket.gethostname()

    def getPath(self):
        try:
            return self.config_paths[self.computername]
        except KeyError:
            raise

    def getConfigFile(self):
        try:
            config_file = configparser.ConfigParser()
            config_file.read_file(open(self.path, 'r'))
            return config_file
        except FileNotFoundError:
            raise

if __name__ == "__main__":

    try:
        cf = ConfigFile()

    except KeyError:
        print('You must set up a config file entry for',
              sys.exc_info()[1])

    except FileNotFoundError as e:
        print('Can\'t find config file', e.filename)
