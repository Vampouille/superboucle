# SuperBoucle

SuperBoucle is midi controllable live sampler synced with jack transport.

SuperBoucle is composed of a matrix of sample controllable with external midi
device like pad. SuperBoucle will send back information to the pad (light up
pad button). Sample will always start and stop on a beat. You can adjust length
of sample in beat and offset in beat. But you can also adjust sample offset in
raw frame count negative or positive. Which mean sample can start before next
beat (useful for reversed sample).

## Requirements

* Python 3
* Pip
 
		sudo aptitude install python3-pip
* python cffi 0.9.2
 
	 	 sudo aptitude remove python3-cffi
		 sudo aptitude install libffi-dev build-essential libpython3.4-dev
	 	 sudo pip3 install cffi
* python soundfile 0.7.0 (may takes some times)
 
 		 sudo pip3 install PySoundFile
* python numpy 1.9.2
 
	 	 sudo aptitude remove python3-numpy
		 sudo pip3 install numpy (may be already installated)
* python PyQT 5 

	 	 sudo aptitude install python3-pyqt5
* package libjack-jackd2-dev, libsndfile1-dev
 
 		 sudo aptitude install libjack-jackd2-dev libsndfile1-dev
* Running jack server with transport information : BPM (Qtractor, Hydrogen, Ardour, ...)

## Installation

### Requirements

This should work on Ubuntu and derived (Tested on mint 17 and ubuntu trusty) :

	sudo aptitude remove python3-cffi python3-numpy
	sudo aptitude install python3-pip libffi-dev build-essential libpython3.4-dev libjack-jackd2-dev libsndfile1-dev python3-pyqt5

## Running

Run boucle.py script :
	 
	./boucle.py

## Midi devices

 SuperBoucle can be controlled with external midi device like generic midi
 keyboard, midi drum, Akai APC series, Novation LaunchPad, ... In order to
 configure a new controller, you have to select 'Add device...' entry in
 Device menu. Another solution is to import a .sbm (SuperBoucle Mapping) file
 contanning device configuration. Currently, there is only configuration file
 for Launchpad S and generic midi keyboard. Feel free to send me new device
 configuration, I will include it in next release.

### What can be controlled by external midi device ?

* You can start or stop clip/sample.
* You can adjust master volume
* You can adjust volume of each clip/sample

### Device Name

Set the device name. Use a short name of your choice. This is only for
display purpose.

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
them to master volume. In 'Master volume part', click on 'Master volume
controller' and move controller on midi device. You should see a
description of the new controller (channel and controller id).

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
* no clip (black / no light)
* clip will start (blink green)
* clip is playing (green)
* clip will stop (blink red)
* clip is stopped (red)

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
