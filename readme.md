# SuperBoucle

SuperBoucle is a loop based software fully controllable with any midi
device. SuperBoucle is also synced with jack transport. You can use it on live
performance or for composition.

SuperBoucle is composed of a matrix of sample controllable with external midi
device like pad. SuperBoucle will send back information to midi device (light
up led). Sample will always start and stop on a beat or group of beats. You can
adjust duration of sample (loop period) in beat and offset in beat. But you can
also adjust sample offset in raw frame count negative or positive. Which mean
sample can start before next beat (useful for reversed sample). You can record
loop of any size, adjust BPM, reverse, normalize samples, ...

Typical usage :

* You just need to control jack transport (play, pause, rewind) with external
  midi device and want a button to jump to a specified location in song.
* You have some instruments patterns but you have no idea of song structure.
* You make live performance with pre-recorded instruments (you have no bass
  player for example) and you don't want to have a predefinied structure for
  the song (maybe part 2 will be longer on some live performance)

## Features

* Jack Transport
* Record
* Auto record latency
* Audio input / output
* Midi input / output
* Normalize and revert samples
* Negative sample offset, sample offset in beats or frames
* Load several formats: WAV, FLAC, AIFF, ...  (no MP3 for the moment)
* Full intuitive MIDI learn interface
* Support any MIDI device : generic keyboard, pad, BCF, Akai APC, ...
* Fully controllable by MIDI device or mouse/keyboard
* Goto function to move jack transport to specified location

## Requirements

### Linux

* Python 3
* Pip for python 3
* Python modules : Cffi, PySoundFile, Numpy, PyQT 5
* Running jack server

### Windows

* Jack Audio Kit

## Installation

### Linux

* Install Jack server :

        sudo aptitude install jackd2 qjackctl

* Install midi bridge (optional) : 

        sudo aptitude install a2jmidid

* Install python modules : 

        sudo aptitude install python3 python3-pip python3-cffi python3-numpy python3-pyqt5
        sudo pip3 install PySoundFile

* Download and extract last version of SuperBoucle from https://github.com/Vampouille/superboucle/releases/

### Windows

* Run Jack Audio Kit setup : http://jackaudio.org/downloads/
* Run SuperBoucle windows Setup from https://github.com/Vampouille/superboucle/releases

## Running

### Linux

Start Jack audio server and then run SuperBoucle.sh script from SuperBoucle directory :

	./SuperBoucle.sh

### Windows

Start "Jack PortAudio" from start menu and then start SuperBoucle from start menu.

## Contact

Feel free to send an email to superboucle@nura.eu if you have any questions,
remarks or if you find a bug.

## Midi devices

SuperBoucle can be controlled with external midi device like generic midi
keyboard, midi drum, Akai APC series, Novation LaunchPad, Behringer BCF, ... In
order to configure a new controller, you have to select 'Add device...'  entry
in Device menu. Another solution is to import a .sbm (SuperBoucle Mapping) file
contanning device configuration. Feel free to send me new device configuration,
I will include it in next release.

### What can be controlled by external midi device ?

You can : 

* Start or stop clip/sample.
* Start, pause jack transport
* Jump to beggining of song or at specified position
* Adjust master volume
* Adjust volume of each clip/sample
* Select clip to record and start record

### Velocity sensitive MIDI device

For those type of device, don't press button/pad with maximum velocity. In
order to detect velocity sensitive device, superboucle need to receive MIDI
message with velocity different than 0 or 127.

### Device Name

Set the device name. Use a name of your choice. This is only for display
purpose.

### Start/Stop configuration

In 'Start / Stop buttons' part click 'Learn first line' button and press
each button of the first line on external midi device from left to
right. For all remaining rows press 'Add next line' button and press each
button on external device. Finnaly, press 'stop' button (optionnal).

First midi event receive for a particular channel and pitch will be
associated to the clip/sample. For example, if your device send Note On
when key is pressed and a Note Off when key is release. Then Note On will
be use to start or stop clip any other message will be ignored. Velocity is
also used : if device send Note On with velocity 127 when pressed and Note
On with velocity 0 when released. Then only Note On with velocity 127 will
be used to star tor stop clip. Same rules apply to other function like
'clip volume per line'. So it should work on most device except those
that are sensible to velocity : device which set velocity according to real
user velocity.

### Master volume configuration

If you have knobs or sliders on your midi device, you can associated one of
them to master volume. In 'Master volume' part, click on 'Master volume
controller' and move controller on midi device. You should see a
description of the new controller (channel and controller id).

### Transport configuration

If you have available buttons, you can associated them to transport actions. In
'Transport' part, click one transport button and press desired button on midi
device. You should see a description of the new button.
Record button can also be associated with midi button is this section.

### Clip/sample volume configuration

If you have more than one knobs or sliders you can configure them to adjust
volume of samples. On most midi device there is more buttons than
controllers. So you cannot just associate one controller to one sample,
there is not enough controller on midi device. In most case, you will have
one controller controller per column. So SuperBoucle need to knwon which
line you want to change. You have to configure one button per row and one
controller per column. If on 'start/stop configuration' you have configured
8x4 buttons (four lines of eigth buttons), you need 8 controller and 4
buttons. When you press first button, controller are associated to volume
of fisrt row's clips.

First click on 'Learn controllers' button and move each controller (in
correct order) and press 'Stop'. Then, press 'Learn line buttons' and press
button corresponding to line 1 on midi device, then button for line 2,
... and press 'stop'.

### Colors

SuperBoucle will send information to external midi midi to indication
clip/sample status :

| Clip state        | Color            |
| ----------------- | ---------------- |
| no clip           | black / no light |
| clip will start   | blink green      |
| clip is playing   | green            |
| clip will stop    | blink red        |
| clip is stopped   | red              |
| clip will record  | blink amber      |
| clip is recording | amber            |

In order to light button on external midi device, SuperBoucle will send
Note On midi message corresponding to channel and pitch of buttons in
'start/stop' part. Velocity of those messages is used to set color. In this
part you will configure velocity value to correct color. When you press
'Test' button, SuperBoucle will light up all buttons currently configured.

Adjust each color value to get corresponding color. For example, for green
color, change value until external midi device show a nice green color.

### Init command

If you have a reset command or a particular midi command to send to your
midi device, you can put those commands here. One command per line in
decimal value separated by comma. For example, for LaunchPad S this will
reset all buttons and switch to blinking mode :
	
	176, 0, 0
	176, 0, 40
