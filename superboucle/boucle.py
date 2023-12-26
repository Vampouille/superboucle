#!/usr/bin/env python3

"""JACK client that prints all received MIDI events."""

import binascii
import re
import jack
import sys, os.path
import numpy as np
import resampy
from superboucle.clip import Clip, Song, load_song_from_file
from superboucle.gui import Gui
from superboucle.midi_transport import MidiTransport, STOPPED, RUNNING
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
from queue import Empty
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
        song = load_song_from_file(args.songfile)
    else:
        sys.exit("File {} does not exist.".format(args.songfile))
else:
    song = Song(8, 8)

client = jack.Client("Super Boucle")
sync_midi_in = client.midi_inports.register("sync")
cmd_midi_in = client.midi_inports.register("cmd_in")
cmd_midi_out = client.midi_outports.register("cmd_feedback")
inL = client.inports.register("input_L")
inR = client.inports.register("input_R")
app = QApplication(sys.argv)
gui = Gui(song, client, app)
midi_transport = MidiTransport(gui)

# Debug
gui.old_hex_data = "iuy"

CLIP_TRANSITION = {Clip.STARTING: Clip.START,
                   Clip.STOPPING: Clip.STOP,
                   Clip.STOP: Clip.STOP,
                   Clip.START: Clip.START,
                   Clip.PREPARE_RECORD: Clip.RECORDING,
                   Clip.RECORDING: Clip.START}

@client.set_process_callback
def my_callback(frames):
    song = gui.song
    state, position = client.transport_query()

    inL_buffer = inL.get_array()
    inR_buffer = inR.get_array()

    output_buffers = {k: v.get_array() for k, v in
                      gui.port_by_name.items()}

    for b in output_buffers.values():
        b[:] = 0

    # check midi in

    # beat count since playing (midi start)
    # beat_offset: number of sample since beginning of buffer to the beat
    # None for no beat in buffer
    beat = None
    beat_offset = None
    if gui.is_learn_device_mode:
        for offset, indata in cmd_midi_in.incoming_midi_events():
            gui.learn_device.queue.put(indata)
        gui.learn_device.updateUi.emit()
    else:
        for offset, indata in cmd_midi_in.incoming_midi_events():
            gui.queue_in.put(indata)
        gui.readQueueIn.emit()
    for offset, indata in sync_midi_in.incoming_midi_events():
        res = midi_transport.notify(client.last_frame_time + offset, bytes(indata))
        if res != -1:
            beat = res
            beat_offset = offset
    cmd_midi_out.clear_buffer()

    # Démarrage:
    # 0xfa Start
    # 0xf8 Click
    # ...
    # 0xb27b00: All Sound Off
    # 0xfc: Song Position Pointer
    p = midi_transport.position_beats(client.last_frame_time)
    if p:
        #print("POS: %s" % round(p, 2))
        pass
    if gui.sync_source == 1: # MIDI

        for clip in song.clips:
            # Skip clip with no audio
            if clip.audio_file is None:
                continue
            
            # Get pointer to the clip buffer
            clip_buffers = getBuffers(gui, clip)

            # Check if end of clip is in the buffer
            # check if a beat is in the buffer
            clip_loop = None
            if beat is not None:
                # Check if the beat trigger a clip play
                if (beat - clip.beat_offset) % clip.beat_diviser == 0:
                    clip_loop = beat_offset

            # Add sample from already playing clip
            # Write samples until end of buffer or available sample from clip
            rs = clip.remainingSamples()
            length = min(rs, client.blocksize if clip_loop is None else clip_loop)
            if clip.state == Clip.START or clip.state == Clip.STOPPING:
                data = clip.getSamples(length, fade_out=0 if length == client.blocksize else min(10,length))
                addBuffer(clip_buffers, 0, data, clip.name)
            elif clip.state == Clip.RECORDING:
                clip.writeSamples(inL_buffer[:rs], inR_buffer[:rs])

            # Trigger clip loop
            # * rewind
            # * switch clip audio a/b
            # * play beginning of the clip
            if clip_loop is not None:
                clip.state = CLIP_TRANSITION[clip.state]
                if clip.audio_file_next_id != clip.audio_file_id:
                    if clip.edit_clip:
                        clip.edit_clip.changeActiveSignal.emit(clip.audio_file_id, clip.audio_file_next_id)
                    clip.audio_file_id = clip.audio_file_next_id
                clip.rewind()
                gui.updateUi.emit()

                if clip.state == Clip.START or clip.state == Clip.STOPPING:
                    rs = clip.remainingSamples()
                    length = min(rs, client.blocksize - clip_loop)
                    data = clip.getSamples(length, fade_in=10)
                    addBuffer(clip_buffers, clip_loop, data, clip.name)
                elif clip.state == Clip.RECORDING:
                    clip.writeSamples(inL_buffer, inR_buffer)
                    if clip.edit_clip:
                        clip.edit_clip.changeActiveSignal.emit(clip.audio_file_id, clip.audio_file_next_id)
                        clip.edit_clip.updateAudioDescSignal.emit(0)



    elif ((state == jack.ROLLING
         and 'beats_per_minute' in position
         and position['frame_rate'] != 0)):
        frame = position['frame']
        fps = position['frame_rate']
        fpm = fps * 60
        bpm = position['beats_per_minute']
        blocksize = client.blocksize
        frame_per_beat = fpm / bpm

        for clip in song.clips:

            if clip.audio_file is None:
                continue

            # get pointer to the buffer where to write clip data (ex: Main_R, Main_L)
            clip_buffers = getBuffers(gui, clip)

            clip_period = (
                fpm * clip.beat_diviser) / bpm  # length of the clip in frames
            total_frame_offset = clip.frame_offset + (
                clip.beat_offset * frame_per_beat)
            # frame_beat: how many times the clip hast been played already
            # clip_offset: position in the clip about to be played
            frame_beat, clip_offset = divmod(
                (frame - total_frame_offset) * bpm, fpm * clip.beat_diviser)
            clip_offset = round(clip_offset / bpm)

            # buffer is larger than remaining sample from clip
            if (clip_offset + blocksize) > clip_period:
                next_clip_offset = (clip_offset + blocksize) - clip_period
                next_clip_offset = round(blocksize - next_clip_offset)
                # print("new beat in block : {}".format(next_clip_offset))
            else:
                next_clip_offset = None

            if clip.state == Clip.START or clip.state == Clip.STOPPING:
                # is there enough audio data ?
                if clip_offset < clip.getAudio().length():
                    length = min(clip.getAudio().length() - clip_offset, frames)
                    data = clip.getSamples(length, start_pos=clip_offset, fade_out=10 if len(data) < frames else 0)
                    addBuffer(clip_buffers, 0, data)

            if clip.state == Clip.RECORDING:
                if next_clip_offset:
                    clip.writeSamples(0,
                                      inL_buffer[:next_clip_offset],
                                      start_pos=clip_offset)
                    clip.writeSamples(1,
                                      inL_buffer[:next_clip_offset],
                                      start_pos=clip_offset)
                else:
                    clip.writeSamples(0,
                                      inL_buffer,
                                      start_pos=clip_offset)
                    clip.writeSamples(1,
                                      inL_buffer,
                                      start_pos=clip_offset)
                clip.last_offset = clip_offset

            if next_clip_offset and (clip.state == Clip.START
                                     or clip.state == Clip.STARTING):
                length = min(clip.getAudio().length(), blocksize - next_clip_offset)
                if length:
                    data = clip.getSamples(length, start_pos=0, fade_in=10)
                    addBuffer(clip_buffers, next_clip_offset, data)

                clip.last_offset = 0
                # print("buffer[{0}:] = sample[:{1}]".
                # format(next_clip_offset, length))

            if next_clip_offset and clip.state == Clip.PREPARE_RECORD:
                clip.writeSamples(0, inL_buffer[next_clip_offset:])
                clip.writeSamples(1, inR_buffer[next_clip_offset:])

            # starting or stopping clip
            if clip_offset == 0 or next_clip_offset:
                  # reset record offset
                  if clip.state == Clip.RECORDING:
                      clip.frame_offset = 0
                  clip.state = CLIP_TRANSITION[clip.state]
                  clip.rewind()
                  gui.updateUi.emit()

    # apply master volume
    for b in output_buffers.values():
        b[:] *= song.volume

    try:
        i = 1
        while True:
            note = gui.queue_out.get(block=False)
            cmd_midi_out.write_midi_event(i, note)
            i += 1
    except Empty:
        pass

def getBuffers(gui, clip):
    output_buffers = {k: v.get_array() for k, v in
            gui.port_by_name.items()}
    my_format = Song.CHANNEL_NAME_PATTERN.format
    return [output_buffers[my_format(port=clip.output,
                                     channel=base)]
            for base in Song.CHANNEL_NAMES]

def addBuffer(clip_buffers, offset, data, name):
    for ch_id, buffer in enumerate(clip_buffers):
        # Add fade out if clip does not continue on next buffer
        np.add.at(buffer, slice(offset, offset + data.shape[0]), data[:, ch_id % data.shape[1]])

def connectMidiDevice(_=None,__=None):
    # Try to connect any MIDI Compatible device
    # For tempo:
    for port in client.get_ports(is_midi=True, is_output=True, is_physical=True):
        if re.search('RHYTHM DESIGNER', port.name):
            try:
                client.connect(port, sync_midi_in)
            except jack.JackError:
                pass
    # For Command
    for port in client.get_ports(is_midi=True, is_output=True, is_physical=True):
        if re.search('Launchpad', port.name):
            try:
                client.connect(port, cmd_midi_in)
            except jack.JackError:
                pass
    for port in client.get_ports(is_midi=True, is_input=True, is_physical=True):
        if re.search('Launchpad', port.name):
            try:
                client.connect(cmd_midi_out, port)
            except jack.JackError:
                pass

# activate !
def start():
    with client: # call activate() ?
        # make connection
        playback = client.get_ports(is_physical=True, is_input=True, is_audio=True)
        if not playback:
            raise RuntimeError("No physical playback ports")

        record = client.get_ports(is_physical=True, is_output=True, is_audio=True)
        if not record:
            raise RuntimeError("No physical record ports")

        my_format = Song.CHANNEL_NAME_PATTERN.format
        if gui.auto_connect:
            # Connect inputs
            client.connect(record[0], inL)
            client.connect(record[1], inR)

            # Connect outputs
            for ch_name, pl_port in zip([my_format(port=Clip.DEFAULT_OUTPUT,
                                                   channel=ch)
                                         for ch in Song.CHANNEL_NAMES],
                                        playback):
                sb_out = gui.port_by_name[ch_name]
                client.connect(sb_out, pl_port)
            
            # Connect MIDI Devices
            connectMidiDevice()
            
            # Search for new device every 2sec
            autoConnectTimer = QTimer()
            autoConnectTimer.start(2000)
            autoConnectTimer.timeout.connect(connectMidiDevice)


        app.exec_()


if __name__ == "__main__":
    start()
