#!/usr/bin/env python3

"""JACK client that prints all received MIDI events."""

import jack
import sys
from clip import Clip, Song
from gui import Gui
from PyQt5.QtWidgets import QApplication
from queue import Empty

song = Song(8, 8)

client = jack.Client("Super Boucle")
midi_in = client.midi_inports.register("input")
midi_out = client.midi_outports.register("output")
outL = client.outports.register("MAIN_L")
outR = client.outports.register("MAIN_R")

outL1 = client.outports.register("Out_1_L")
outR1 = client.outports.register("Out_1_R")

inL = client.inports.register("input_L")
inR = client.inports.register("input_R")

app = QApplication(sys.argv)
gui = Gui(song, client)

CLIP_TRANSITION = {Clip.STARTING: Clip.START,
                   Clip.STOPPING: Clip.STOP,
                   Clip.PREPARE_RECORD: Clip.RECORDING,
                   Clip.RECORDING: Clip.STOP}


def my_callback(frames):
    song = gui.song
    state, position = client.transport_query()
    outL_buffer = outL.get_array()
    outR_buffer = outR.get_array()
    outL_buffer[:] = 0
    outR_buffer[:] = 0
    inL_buffer = inL.get_array()
    inR_buffer = inR.get_array()

    outL1_buffer = outL1.get_array()
    outR1_buffer = outR1.get_array()
    outL1_buffer[:] = 0
    outR1_buffer[:] = 0

    # check midi in
    if gui.is_learn_device_mode:
        for offset, indata in midi_in.incoming_midi_events():
            gui.learn_device.queue.put(indata)
        gui.learn_device.updateUi.emit()
    else:
        for offset, indata in midi_in.incoming_midi_events():
            gui.queue_in.put(indata)
        gui.readQueueIn.emit()
    midi_out.clear_buffer()

    if state == 1 and 'beats_per_minute' in position:
        frame = position['frame']
        fps = position['frame_rate']
        bpm = position['beats_per_minute']
        blocksize = client.blocksize

        for clip in song.clips:
            frame_per_beat = (fps * 60) / bpm
            clip_period = (fps * 60 * clip.beat_diviser) / bpm
            frame_beat, clip_offset = divmod((frame - clip.frame_offset -
                                              (clip.beat_offset *
                                               frame_per_beat)) * bpm,
                                             60 * fps *
                                             clip.beat_diviser)
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
                    outL_buffer[:length] += song.get_data(clip,
                                                          0,
                                                          clip_offset,
                                                          length)
                    outR_buffer[:length] += song.get_data(clip,
                                                          1,
                                                          clip_offset,
                                                          length)
                    clip.last_offset = clip_offset
                    # print("buffer[:{0}] = sample[{1}:{2}]".
                    #      format(length, clip_offset, clip_offset+length))




            if clip.state == Clip.RECORDING:
                if next_clip_offset:
                    song.write_data(clip,
                                    0,
                                    clip_offset,
                                    inL_buffer[:next_clip_offset])
                    song.write_data(clip,
                                    1,
                                    clip_offset,
                                    inR_buffer[:next_clip_offset])
                else:
                    song.write_data(clip,
                                    0,
                                    clip_offset,
                                    inL_buffer)
                    song.write_data(clip,
                                    1,
                                    clip_offset,
                                    inR_buffer)
                clip.last_offset = clip_offset

            if next_clip_offset and (clip.state == Clip.START
                                     or clip.state == Clip.STARTING):
                length = min(song.length(clip), blocksize - next_clip_offset)
                if length:
                    outL_buffer[next_clip_offset:] += song.get_data(clip,
                                                                    0,
                                                                    0,
                                                                    length)
                    outR_buffer[next_clip_offset:] += song.get_data(clip,
                                                                    1,
                                                                    0,
                                                                    length)
                clip.last_offset = 0
                # print("buffer[{0}:] = sample[:{1}]".
                #      format(next_clip_offset, length))

            if next_clip_offset and clip.state == Clip.PREPARE_RECORD:
                song.write_data(clip,
                                0,
                                0,
                                inL_buffer[next_clip_offset:])
                song.write_data(clip,
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
        outL_buffer[:] *= song.volume
        outR_buffer[:] *= song.volume

    try:
        i = 1
        while True:
            note = gui.queue_out.get(block=False)
            midi_out.write_midi_event(i, note)
            i += 1
    except Empty:
        pass

    return jack.CALL_AGAIN

client.set_process_callback(my_callback)

# activate !
with client:

    # make connection
    playback = client.get_ports(is_physical=True, is_input=True)
    if not playback:
        raise RuntimeError("No physical playback ports")

    client.connect(outL, playback[0])
    client.connect(outR, playback[1])

    record = client.get_ports(is_physical=True, is_output=True)
    if not record:
        raise RuntimeError("No physical record ports")

    client.connect(record[0], inL)
    client.connect(record[1], inR)

    app.exec_()
