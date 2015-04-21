#!/usr/bin/env python3

"""JACK client that prints all received MIDI events."""

import jack
import transport
import numpy as np
import soundfile as sf

# Load audio data
sample, samplerate = sf.read('beep.wav',
                             dtype=np.float32, always_2d=False)

client = jack.Client("MIDI-Monitor")
port = client.midi_inports.register("input")
out = client.outports.register("output")


def bbt2ticks(bar, beat, tick):
    return (7680*(bar-1))+(1920*(beat-1))+tick


def frame2bbt(frame, ticks_per_beat, beats_per_minute, frame_rate):
    ticks_per_second = (beats_per_minute * ticks_per_beat) / 60
    return (ticks_per_second * frame) / frame_rate


def my_callback(frames, sample):
    state, position = client.transport_query()
    out_buffer = out.get_array()
    out_buffer[:] = 0
    tp = transport.Transport(state, position)
    if(tp.state == 1):
        bar = tp.bar
        beat = tp.beat
        tick = tp.tick
        frame = tp.frame
        fps = tp.frame_rate
        bpm = tp.beats_per_minute
        blocksize = client.blocksize
        frame_beat, clip_offset = divmod(frame * bpm,
                                         60 * tp.frame_rate)
        clip_offset = clip_offset / tp.beats_per_minute
        frame_per_beat = (fps * 60) / bpm

        print("{0} {1} {2}|{3}|{4}".
              format(tp.frame, frame_beat + 1, bar, beat, tick,  clip_offset))

        # next beat is in block ?
        if (clip_offset + blocksize) > frame_per_beat:
            second_clip_offset = (clip_offset + blocksize) - frame_per_beat
            second_clip_offset = blocksize - second_clip_offset
            print("new beat in block : {}".format(second_clip_offset))
        else:
            second_clip_offset = None

        # round index
        clip_offset = round(clip_offset)
        if second_clip_offset:
            second_clip_offset = round(second_clip_offset)

        # is there enough audio data ?
        if clip_offset < len(sample):
            length = min(len(sample) - clip_offset, frames)
            out_buffer[:length] = sample[clip_offset:clip_offset+length]
            print("buffer[:{0}] = sample[{1}:{2}]".
                  format(length, clip_offset, clip_offset+length))

        if second_clip_offset:
            out_buffer[second_clip_offset:] = sample[
                :blocksize - second_clip_offset]
            print("buffer[{0}:] = sample[:{1}]".
                  format(second_clip_offset, blocksize - second_clip_offset))

    return jack.CALL_AGAIN

client.set_process_callback(my_callback, sample)

# activate !
with client:
    print("#" * 80)
    print("press Return to quit")
    print("#" * 80)
    input()
