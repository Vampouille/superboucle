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
main_outs = list(map(client.outports.register, Clip.get_outports()))

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

    inL_buffer = inL.get_array()
    inR_buffer = inR.get_array()

    gui.ports_initialised.wait()
    output_buffers = {k: v.get_array() for k, v in
                      gui.output_ports_by_name.items()}

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
        gui.readQueueIn.emit()
    midi_out.clear_buffer()

    if state == 1 and 'beats_per_minute' in position:
        frame = position['frame']
        fps = position['frame_rate']
        fpm = fps * 60
        bpm = position['beats_per_minute']
        blocksize = client.blocksize

        for clip in song.clips:
            # only process clips if their output is already registered
            if clip.output not in gui.port_names_by_output:
                continue
            buffers = [output_buffers[n] for n in
                       gui.port_names_by_output[clip.output]]

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
                    for c in range(min(song.channels(clip), len(buffers))):
                        data = song.get_data(clip,
                                             c,
                                             clip_offset,
                                             length)
                        buffers[c][:length] += data

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
                    for c in range(song.channels(clip)):
                        data = song.get_data(clip,
                                             c,
                                             0,
                                             length)
                        buffers[c][next_clip_offset:] += data

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

    if gui.auto_connect:
        for o, p in zip(main_outs, playback):
            client.connect(o, p)

        client.connect(record[0], inL)
        client.connect(record[1], inR)

    app.exec_()
