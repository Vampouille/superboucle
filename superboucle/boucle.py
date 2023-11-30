#!/usr/bin/env python3

"""JACK client that prints all received MIDI events."""

import binascii
import jack
import sys, os.path
import numpy as np
from superboucle.clip import Clip, Song, load_song_from_file
from superboucle.gui import Gui
from superboucle.midi_transport import MidiTransport
from PyQt5.QtWidgets import QApplication
from queue import Empty
import argparse



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
midi_in = client.midi_inports.register("input")
midi_out = client.midi_outports.register("output")
inL = client.inports.register("input_L")
inR = client.inports.register("input_R")
midi_transport = MidiTransport(client.samplerate, client.blocksize)

app = QApplication(sys.argv)
gui = Gui(song, client, app)

# Debug
gui.old_hex_data = "iuy"

CLIP_TRANSITION = {Clip.STARTING: Clip.START,
                   Clip.STOPPING: Clip.STOP,
                   Clip.PREPARE_RECORD: Clip.RECORDING,
                   Clip.RECORDING: Clip.STOP}


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
    if gui.is_learn_device_mode:
        for offset, indata in midi_in.incoming_midi_events():
            gui.learn_device.queue.put(indata)
        gui.learn_device.updateUi.emit()
    else:
        for offset, indata in midi_in.incoming_midi_events():
            gui.queue_in.put(indata)
            midi_transport.notify(client.last_frame_time, offset, bytes(indata))
            hex_data = binascii.hexlify(indata).decode()
            if hex_data != gui.old_hex_data:
                #print('{}: 0x{}'.format(client.last_frame_time + offset, hex_data))
                gui.old_hex_data = hex_data
        gui.readQueueIn.emit()
    midi_out.clear_buffer()

    # Démarrage: 
    # 0xfa Start
    # 0xf8 Click
    # ...
    # 0xb27b00: All Sound Off
    # 0xfc: Song Position Pointer
    p = midi_transport.position(client.last_frame_time)
    if p:
        print("POS: %s" % round(p, 2))
    if ((state == jack.ROLLING
         and 'beats_per_minute' in position
         and position['frame_rate'] != 0)):
        frame = position['frame']
        fps = position['frame_rate']
        fpm = fps * 60
        bpm = position['beats_per_minute']
        blocksize = client.blocksize

        for clip in song.clips:

            my_format = Song.CHANNEL_NAME_PATTERN.format
            clip_buffers = [output_buffers[my_format(port=clip.output,
                                                     channel=base)]
                            for base in Song.CHANNEL_NAMES]

            frame_per_beat = fpm / bpm
            clip_period = (
                              fpm * clip.beat_diviser) / bpm  # length of the clip in frames
            total_frame_offset = clip.frame_offset + (
                clip.beat_offset * frame_per_beat)
            # frame_beat: how many times the clip hast been played already
            # clip_offset: position in the clip about to be played
            frame_beat, clip_offset = divmod(
                (frame - total_frame_offset) * bpm, fpm * clip.beat_diviser)
            clip_offset = round(clip_offset / bpm)

            # next beat is in block ?
            if (clip_offset + blocksize) > clip_period:
                next_clip_offset = (clip_offset + blocksize) - clip_period
                next_clip_offset = round(blocksize - next_clip_offset)
                # print("new beat in block : {}".format(next_clip_offset))
            else:
                next_clip_offset = None

            if clip.state == Clip.START or clip.state == Clip.STOPPING:
                # is there enough audio data ?
                if clip_offset < song.length(clip):
                    length = min(song.length(clip) - clip_offset, frames)
                    for ch_id, buffer in enumerate(clip_buffers):
                        data = song.getData(clip,
                                            ch_id % song.channels(clip),
                                            clip_offset,
                                            length)
                        # buffer[:length] += data
                        print("Buffer: %s [%s:%s] data: %s" % (buffer.shape, 0, len(data), data.shape))
                        np.add.at(buffer, slice(0, len(data)), data)

                    clip.last_offset = clip_offset
                    # print("buffer[:{0}] = sample[{1}:{2}]".
                    # format(length, clip_offset, clip_offset+length))

            if clip.state == Clip.RECORDING:
                if next_clip_offset:
                    song.writeData(clip,
                                   0,
                                   clip_offset,
                                   inL_buffer[:next_clip_offset])
                    song.writeData(clip,
                                   1,
                                   clip_offset,
                                   inR_buffer[:next_clip_offset])
                else:
                    song.writeData(clip,
                                   0,
                                   clip_offset,
                                   inL_buffer)
                    song.writeData(clip,
                                   1,
                                   clip_offset,
                                   inR_buffer)
                clip.last_offset = clip_offset

            if next_clip_offset and (clip.state == Clip.START
                                     or clip.state == Clip.STARTING):
                length = min(song.length(clip), blocksize - next_clip_offset)
                if length:
                    for ch_id, buffer in enumerate(clip_buffers):
                        data = song.getData(clip,
                                            ch_id % song.channels(clip),
                                            0,
                                            length)
                        # buffer[next_clip_offset:] += data
                        s_start = next_clip_offset
                        s_stop = s_start + len(data)
                        print("Buffer: %s [%s:%s] data: %s" % (buffer.shape, s_start, s_stop, data.shape))
                        np.add.at(buffer, slice(s_start, s_stop), data)

                clip.last_offset = 0
                # print("buffer[{0}:] = sample[:{1}]".
                # format(next_clip_offset, length))

            if next_clip_offset and clip.state == Clip.PREPARE_RECORD:
                song.writeData(clip,
                               0,
                               0,
                               inL_buffer[next_clip_offset:])
                song.writeData(clip,
                               1,
                               0,
                               inR_buffer[next_clip_offset:])

            # starting or stopping clip
            if clip_offset == 0 or next_clip_offset:
                try:
                    # reset record offset
                    if clip.state == Clip.RECORDING:
                        clip.frame_offset = 0
                    clip.state = CLIP_TRANSITION[clip.state]
                    clip.last_offset = 0
                    gui.updateUi.emit()
                except KeyError:
                    pass

        # apply master volume
        for b in output_buffers.values():
            b[:] *= song.volume

    try:
        i = 1
        while True:
            note = gui.queue_out.get(block=False)
            midi_out.write_midi_event(i, note)
            i += 1
    except Empty:
        pass


client.set_process_callback(my_callback)


# activate !
def start():
    with client:
        # make connection
        playback = client.get_ports(is_physical=True, is_input=True)
        if not playback:
            raise RuntimeError("No physical playback ports")

        record = client.get_ports(is_physical=True, is_output=True)
        if not record:
            raise RuntimeError("No physical record ports")

        my_format = Song.CHANNEL_NAME_PATTERN.format
        if gui.auto_connect:
            # connect inputs
            client.connect(record[0], inL)
            client.connect(record[1], inR)

            # connect outputs
            for ch_name, pl_port in zip([my_format(port=Clip.DEFAULT_OUTPUT,
                                                   channel=ch)
                                         for ch in Song.CHANNEL_NAMES],
                                        playback):
                sb_out = gui.port_by_name[ch_name]
                client.connect(sb_out, pl_port)

        app.exec_()


if __name__ == "__main__":
    start()
