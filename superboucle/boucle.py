#!/usr/bin/env python3

"""JACK client that prints all received MIDI events."""

import re
import jack
import sys, os.path
import numpy as np
import resampy
from superboucle import client, gui, app
from superboucle.song import Song
from superboucle.process_callback import super_callback, timebase_callback
from PyQt5.QtCore import QTimer
import argparse

# Force load of the resampy dependencies to avoid xruns on first usage
tps = np.arange(0, 1, 1 / 44100)
sinusoide = 0.5 * np.sin(2 * np.pi * 440 * tps)
sinusoide_resampled = resampy.resample(sinusoide, 44100, 48000)

parser = argparse.ArgumentParser(description='launch superboucle')
parser.add_argument("songfile", nargs="?", help="load the song specified here")
args = parser.parse_args()

song = None
if args.songfile:
    if os.path.isfile(args.songfile):
        song = Song(file=args.songfile)
    else:
        sys.exit("File {} does not exist.".format(args.songfile))
else:
    song = Song(8, 8)


#def onClientRegistration(name: str, register: bool) -> None:
#    print(f"onClientRegistration({name},{register})")

def onPortRegistration(port: jack.Port, register: bool) -> None:
    if not client.owns(port):
        gui.jackConnectionChangeSignal.emit()
#        print(f"onPortRegistration({port.name}, {register})")

def onPortConnect(a: jack.Port, b: jack.Port, connect: bool) -> None:
    if client.owns(a) or client.owns(b):
        gui.superboucleConnectionChangeSignal.emit()
#        print(f"onPortConnect({a.name}, {b.name})")

client.set_process_callback(super_callback)

#client.set_client_registration_callback(onClientRegistration)
client.set_port_registration_callback(onPortRegistration)
client.set_port_connect_callback(onPortConnect)
# set_graph_order_callback ?

with client: # call client.activate()
    client.set_timebase_callback(timebase_callback)
    gui.loadSong(song)
    app.exec_()