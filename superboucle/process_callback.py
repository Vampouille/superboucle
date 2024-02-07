import jack 
import numpy as np
from . import gui, client
from superboucle.clip import Clip
from superboucle.clip_midi import MidiClip

from queue import Empty

CLIP_TRANSITION = {Clip.STARTING: Clip.START,
                   Clip.STOPPING: Clip.STOP,
                   Clip.STOP: Clip.STOP,
                   Clip.START: Clip.START,
                   Clip.PREPARE_RECORD: Clip.RECORDING,
                   Clip.RECORDING: Clip.START}

TICKS_PER_BEAT = 24
MIDI_STOP = b"\xfc"

def super_callback(frames):
    song = gui.song
    state, position = client.transport_query()

    inL_buffer = gui.inL.get_array()
    inR_buffer = gui.inR.get_array()

    output_buffers = {p.shortname: p.get_array() for p in client.outports}

    for b in output_buffers.values():
        b[:] = 0

    # check midi in

    # beat count since playing (midi start)
    # beat_offset: number of sample since beginning of buffer to the beat
    # None for no beat in buffer
    beat = None
    beat_offset = None
    stopped = False
    tick = {}
    if gui.is_learn_device_mode:
        for offset, indata in gui.cmd_midi_in.incoming_midi_events():
            gui.learn_device.queue.put(indata)
        gui.learn_device.updateUi.emit()
    else:
        for offset, indata in gui.cmd_midi_in.incoming_midi_events():
            gui.queue_in.put(indata)
        gui.readQueueIn.emit()
    for offset, indata in gui.sync_midi_in.incoming_midi_events():
        if indata == MIDI_STOP:
            stopped = True
        res = gui.midi_transport.notify(client.last_frame_time + offset, bytes(indata))
        if res is not None:
            if res % 24 == 0:
                beat = res // 24
                beat_offset = offset
            tick[offset] = res

    gui.cmd_midi_out.clear_buffer()
    for p in client.midi_outports:
        p.clear_buffer()

    # Démarrage:
    # 0xfa Start
    # 0xf8 Click
    # ...
    # 0xb27b00: All Sound Off
    # 0xfc: Song Position Pointer
    #p = gui.midi_transport.position_beats(client.last_frame_time)
    #if p:
    #    #print("POS: %s" % round(p, 2))
    #    pass

    # Handle Stop event First (MIDI Clock Stop received)
    if stopped:
        print("Stopped")
        for clip in song.clips:
            if isinstance(clip, MidiClip):
                port = gui.midi_port_by_name[clip.output][0]
                for ev in list(clip.pendingNoteOff):
                    print(f"S Sending : {ev}")
                    try:
                        port.write_midi_event(0, ev)
                        clip.pendingNoteOff.remove(ev)
                    except jack.JackErrorCode as e:
                        print(e)
                if clip.state == Clip.RECORDING:
                    gui.midi_transport.stopRecord(client.last_frame_time + offset, clip)

    if gui.sync_source == 1: # MIDI

        for clip in song.clips:
            
            if isinstance(clip, MidiClip):
                if len(tick):
                    for offset in tick.keys():
                        beat, ticks = divmod(tick[offset], 24)
                        beat %= clip.length
                        port = gui.midi_port_by_name[clip.output][0]

                        # play events of the end of the clip
                        if clip.state == Clip.START or clip.state == Clip.STOPPING:
                            if ticks == 0 and beat == 0:
                                for ev in list(clip.pendingNoteOff):
                                    print(f"E {clip.length * TICKS_PER_BEAT} Sending : {ev}")
                                    try:
                                        # Put Note Off at the beginning of the buffer
                                        off = 0 if ev[0] >> 4 == 0x8 else offset
                                        port.write_midi_event(off, ev)
                                        clip.pendingNoteOff.remove(ev)
                                    except jack.JackErrorCode as e:
                                        print(e)
                                clip.rewind()

                        # Make transition
                        if ticks == 0 and beat == 0:
                            if clip.state == Clip.RECORDING:
                                gui.midi_transport.stopRecord(client.last_frame_time + offset, clip)
                            clip.state = CLIP_TRANSITION[clip.state]
                            if clip.state == Clip.START or clip.state == Clip.STOPPING:
                                print(clip.events)

                        # Play note of the clip
                        if clip.state == Clip.START or clip.state == Clip.STOPPING:
                            events = clip.getEvents(beat * TICKS_PER_BEAT + ticks)
                            for ev in events:
                                print(f"B {beat * TICKS_PER_BEAT + ticks} Sending : {ev}")
                                try:
                                    port.write_midi_event(offset, ev)
                                except jack.JackErrorCode as e:
                                    print(e)
                if clip.state == Clip.RECORDING or clip.state == Clip.PREPARE_RECORD:
                    for offset, indata in gui.note_midi_in.incoming_midi_events():
                        gui.midi_transport.record(client.last_frame_time + offset, indata, clip)

            else:
                # Skip clip with no audio
                if clip.audio_file is None:
                    continue
                
                # Get pointer to the clip buffer
                clip_buffers = [p.get_array() for p in gui.port_by_name[clip.output]]

                # Check if end of clip is in the buffer
                # check if a beat is in the buffer
                clip_loop = None
                if beat is not None:
                    # Check if the beat trigger a clip play
                    if (beat - clip.beat_offset) % clip.length == 0:
                        clip_loop = beat_offset

                # Add sample from already playing clip
                # Write samples until end of buffer or available sample from clip
                rs = clip.remainingSamples()
                length = min(rs, client.blocksize if clip_loop is None else clip_loop)
                if clip.state == Clip.START or clip.state == Clip.STOPPING:
                    data = clip.getSamples(length, fade_out=0 if length == client.blocksize else min(10,length))
                    addBuffer(clip_buffers, 0, data)
                elif clip.state == Clip.RECORDING:
                    clip.writeSamples(inL_buffer[:rs], inR_buffer[:rs])

                # Trigger clip loop
                # * rewind
                # * switch clip audio a/b
                # * play beginning of the clip
                if clip_loop is not None:
                    #print(f"Transition : {clip.state} --> {CLIP_TRANSITION[clip.state]}")
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
                        addBuffer(clip_buffers, clip_loop, data)
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

            if isinstance(clip, MidiClip):
                # Playing MIDI clip in jack transport mode is not implemented
                pass
            else:
                if clip.audio_file is None:
                    continue

                # get pointer to the buffer where to write clip data (ex: Main_R, Main_L)
                clip_buffers = [p.get_array() for p in gui.port_by_name[clip.output]]

                clip_period = (
                    fpm * clip.length) / bpm  # length of the clip in frames
                total_frame_offset = clip.frame_offset + (
                    clip.beat_offset * frame_per_beat)
                # frame_beat: how many times the clip hast been played already
                # clip_offset: position in the clip about to be played
                frame_beat, clip_offset = divmod(
                    (frame - total_frame_offset) * bpm, fpm * clip.length)
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
                        data = clip.getSamples(length, start_pos=clip_offset, fade_out=10 if length <= frames else 0)
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
            gui.cmd_midi_out.write_midi_event(i, note)
            i += 1
    except Empty:
        pass

def addBuffer(clip_buffers, offset, data):
    for ch_id, buffer in enumerate(clip_buffers):
        # Add fade out if clip does not continue on next buffer
        np.add.at(buffer, slice(offset, offset + data.shape[0]), data[:, ch_id % data.shape[1]])

def timebase_callback(state, nframes, pos, new_pos):
    BAR_START_TICK = 0.0
    BEAT_TYPE = 4.0
    TICKS_PER_BEAT = 960.0

    if gui.sync_source == 1:
        return None
    if pos.frame_rate == 0:
        return None
    pos.valid = 0x10
    pos.bar_start_tick = BAR_START_TICK
    pos.beats_per_bar = gui.beat_per_bar.value()
    pos.beat_type = BEAT_TYPE
    pos.ticks_per_beat = TICKS_PER_BEAT
    pos.beats_per_minute = gui.bpm.value()
    ticks_per_second = (pos.beats_per_minute *
                        pos.ticks_per_beat) / 60
    ticks = (ticks_per_second * pos.frame) / pos.frame_rate
    (beats, pos.tick) = divmod(int(round(ticks, 0)),
                                int(round(pos.ticks_per_beat, 0)))
    (bar, beat) = divmod(beats, int(round(pos.beats_per_bar, 0)))
    (pos.bar, pos.beat) = (bar + 1, beat + 1)
    return None
