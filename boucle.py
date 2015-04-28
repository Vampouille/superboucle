#!/usr/bin/env python3

"""JACK client that prints all received MIDI events."""

import jack
import transport
import sys
from clip import Clip, Song
from gui import Gui
from PyQt5.QtWidgets import QApplication
from queue import Empty

song = Song(6, 6)

client = jack.Client("Super Boucle")
midi_in = client.midi_inports.register("input")
midi_out = client.midi_outports.register("output")
outL = client.outports.register("output_L")
outR = client.outports.register("output_R")

app = QApplication(sys.argv)
gui = Gui(song)

# def bbt2ticks(bar, beat, tick):
#    return (7680*(bar-1))+(1920*(beat-1))+tick


def frame2bbt(frame, ticks_per_beat, beats_per_minute, frame_rate):
    ticks_per_second = (beats_per_minute * ticks_per_beat) / 60
    return (ticks_per_second * frame) / frame_rate


def my_callback(frames, userdata):
    song = gui.song
    state, position = client.transport_query()
    outL_buffer = outL.get_array()
    outR_buffer = outR.get_array()
    outL_buffer[:] = 0
    outR_buffer[:] = 0
    tp = transport.Transport(state, position)

    # check midi in
    if gui.is_add_device_mode:
        for offset, indata in midi_in.incoming_midi_events():
            gui.add_device.queue.put(indata)
        gui.add_device.updateUi.emit()
    else:
        for offset, indata in midi_in.incoming_midi_events():
            gui.queue_in.put(indata)
        gui.readQueueIn.emit()
    midi_out.clear_buffer()

    if(tp.state == 1):
        frame = tp.frame
        fps = tp.frame_rate
        bpm = tp.beats_per_minute
        blocksize = client.blocksize

        for clip in song.clips:
            frame_per_beat = (fps * 60) / bpm
            clip_period = (fps * 60 * clip.beat_diviser) / bpm
            frame_beat, clip_offset = divmod((frame - clip.frame_offset -
                                              (clip.beat_offset *
                                               frame_per_beat)) * bpm,
                                             60 * tp.frame_rate *
                                             clip.beat_diviser)
            clip_offset = clip_offset / tp.beats_per_minute

            # print("{0} {1} {2}|{3}|{4}".
            #      format(tp.frame, frame_beat + 1,
            #             tp.bar, tp.beat, tp.tick,  clip_offset))

            # next beat is in block ?
            if (clip_offset + blocksize) > clip_period:
                next_clip_offset = (clip_offset + blocksize) - clip_period
                next_clip_offset = blocksize - next_clip_offset
                # print("new beat in block : {}".format(next_clip_offset))
            else:
                next_clip_offset = None

            # round index
            clip_offset = round(clip_offset)
            if next_clip_offset:
                next_clip_offset = round(next_clip_offset)

            if clip.state == Clip.START or clip.state == Clip.STOPPING:
                if clip_offset < clip.length:  # is there enough audio data ?
                    length = min(clip.length - clip_offset, frames)
                    outL_buffer[:length] += clip.get_data(0,
                                                          clip_offset,
                                                          length)
                    outR_buffer[:length] += clip.get_data(1,
                                                          clip_offset,
                                                          length)
                    clip.last_offset = clip_offset
                    # print("buffer[:{0}] = sample[{1}:{2}]".
                    #      format(length, clip_offset, clip_offset+length))

            if next_clip_offset and (clip.state == Clip.START
                                     or clip.state == Clip.STARTING):
                length = min(clip.length, blocksize - next_clip_offset)
                outL_buffer[next_clip_offset:] += clip.get_data(0,
                                                                0,
                                                                length)
                outR_buffer[next_clip_offset:] += clip.get_data(1,
                                                                0,
                                                                length)
                clip.last_offset = next_clip_offset
                # print("buffer[{0}:] = sample[:{1}]".
                #      format(next_clip_offset, length))

            # starting or stopping clip
            if clip_offset == 0 or next_clip_offset:
                if clip.state == Clip.STARTING:
                    clip.state = Clip.START
                    gui.updateUi.emit()
                if clip.state == Clip.STOPPING:
                    clip.state = Clip.STOP
                    clip.last_offset = 0
                    gui.updateUi.emit()

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

    app.exec_()
