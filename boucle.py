#!/usr/bin/env python3

"""JACK client that prints all received MIDI events."""

import jack
import transport
from clip import Clip

# Load audio data
clip = Clip('beep-stereo.wav')

client = jack.Client("MIDI-Monitor")
port = client.midi_inports.register("input")
outL = client.outports.register("output_L")
outR = client.outports.register("output_R")


# def bbt2ticks(bar, beat, tick):
#    return (7680*(bar-1))+(1920*(beat-1))+tick


def frame2bbt(frame, ticks_per_beat, beats_per_minute, frame_rate):
    ticks_per_second = (beats_per_minute * ticks_per_beat) / 60
    return (ticks_per_second * frame) / frame_rate


def my_callback(frames, clip):
    state, position = client.transport_query()
    outL_buffer = outL.get_array()
    outR_buffer = outR.get_array()
    outL_buffer[:] = 0
    outR_buffer[:] = 0
    tp = transport.Transport(state, position)
    if(tp.state == 1):
        frame = tp.frame
        fps = tp.frame_rate
        bpm = tp.beats_per_minute
        blocksize = client.blocksize
        frame_beat, clip_offset = divmod(frame * bpm,
                                         60 * tp.frame_rate)
        clip_offset = clip_offset / tp.beats_per_minute
        frame_per_beat = (fps * 60) / bpm

        # print("{0} {1} {2}|{3}|{4}".
        #      format(tp.frame, frame_beat + 1,
        #             tp.bar, tp.beat, tp.tick,  clip_offset))

        # next beat is in block ?
        if (clip_offset + blocksize) > frame_per_beat:
            second_clip_offset = (clip_offset + blocksize) - frame_per_beat
            second_clip_offset = blocksize - second_clip_offset
            # print("new beat in block : {}".format(second_clip_offset))
        else:
            second_clip_offset = None

        # round index
        clip_offset = round(clip_offset)
        if second_clip_offset:
            second_clip_offset = round(second_clip_offset)

        # is there enough audio data ?
        if clip_offset < clip.length:
            length = min(clip.length - clip_offset, frames)
            outL_buffer[:length] = clip.get_data(0, clip_offset, length)
            outR_buffer[:length] = clip.get_data(1, clip_offset, length)
            # print("buffer[:{0}] = sample[{1}:{2}]".
            #      format(length, clip_offset, clip_offset+length))

        if second_clip_offset:
            outL_buffer[second_clip_offset:] = clip.get_data(0,
                                                             0,
                                                             blocksize -
                                                             second_clip_offset)
            outR_buffer[second_clip_offset:] = clip.get_data(1,
                                                             0,
                                                             blocksize -
                                                             second_clip_offset)
            # print("buffer[{0}:] = sample[:{1}]".
            #      format(second_clip_offset, blocksize - second_clip_offset))

    return jack.CALL_AGAIN

client.set_process_callback(my_callback, clip)

# activate !
with client:

    # make connection
    playback = client.get_ports(is_physical=True, is_input=True)
    if not playback:
        raise RuntimeError("No physical playback ports")

    client.connect(outL, playback[0])
    client.connect(outR, playback[1])

    print("#" * 80)
    print("press Return to quit")
    print("#" * 80)

    input()
