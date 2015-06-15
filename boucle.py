#!/usr/bin/env python3

"""JACK client that prints all received MIDI events."""

import jack
import sys
from clip import Clip, Song, getDefaultOutputNames
from gui import Gui
from PyQt5.QtWidgets import QApplication
from queue import Empty

song = Song(8, 8, getDefaultOutputNames(8))

client = jack.Client("Super Boucle")
midi_in = client.midi_inports.register("input")
midi_out = client.midi_outports.register("output")
outL = client.outports.register("MAIN_L")
outR = client.outports.register("MAIN_R")

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

    dedicated_out_buffers = {k: tuple(vc.get_array() for vc in v) for k, v in
                             gui.dedicated_outputs.items()}

    for bs in dedicated_out_buffers.values():
        for b in bs:
            b[:] = 0

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
        fpm = fps * 60
        bpm = position['beats_per_minute']
        blocksize = client.blocksize

        for clip in song.clips:
            frame_per_beat = fpm / bpm
            clip_period = (
                              fpm * clip.beat_diviser) / bpm  # length of the clip in frames
            total_frame_offset = clip.frame_offset + (
                clip.beat_offset * frame_per_beat)
            # frame_beat: how many times the clip hast been played already (???)
            # clip_offset: position in the clip about to be played
            frame_beat, clip_offset = divmod(
                (frame - total_frame_offset) * bpm, fpm * clip.beat_diviser)
            clip_offset = round(clip_offset / bpm)

            buffers = [(outL_buffer,
                        outR_buffer)]  # list of all output buffers that the clip is writing
            # if the route out setting is valid, add the corresponding dedicated buffer
            if (clip.route_out in dedicated_out_buffers):
                buffers.append(dedicated_out_buffers[clip.route_out])

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
                    l_data = song.get_data(clip,
                                           0,
                                           clip_offset,
                                           length)
                    r_data = song.get_data(clip,
                                           1,
                                           clip_offset,
                                           length)
                    for (lBuffer, rBuffer) in buffers:
                        lBuffer[:length] += l_data
                        rBuffer[:length] += r_data

                    clip.last_offset = clip_offset
                    # print("buffer[:{0}] = sample[{1}:{2}]".
                    # format(length, clip_offset, clip_offset+length))

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
                    l_data = song.get_data(clip,
                                           0,
                                           0,
                                           length)
                    r_data = song.get_data(clip,
                                           1,
                                           0,
                                           length)
                    for (lBuffer, rBuffer) in buffers:
                        lBuffer[next_clip_offset:] += l_data
                        rBuffer[next_clip_offset:] += r_data

                clip.last_offset = 0
                # print("buffer[{0}:] = sample[:{1}]".
                # format(next_clip_offset, length))

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

    record = client.get_ports(is_physical=True, is_output=True)
    if not record:
        raise RuntimeError("No physical record ports")

    # if user has other connections that standard Main Out (i.e complex connections with dedicated outputs),
    # then it is much better to leave the user creates his connections with jack patchbay instead of connecting automatically here.
    if gui.auto_connect:
        client.connect(outL, playback[0])
        client.connect(outR, playback[1])

        client.connect(record[0], inL)
        client.connect(record[1], inR)

    app.exec_()
