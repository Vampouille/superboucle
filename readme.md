# Super Boucle

Jack loop application synced with jack transport.

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

		This should work on Ubuntu and derived (Tested on mint 17 and ubuntu trusty)
		sudo aptitude remove python3-cffi python3-numpy
		sudo aptitude install python3-pip libffi-dev build-essential libpython3.4-dev libjack-jackd2-dev libsndfile1-dev python3-pyqt5

## Running

	 Run boucle.py script :
	 ./boucle.py
