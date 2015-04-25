# Super Boucle

Jack loop application synced with jack transport.

## Requirements

	 * Python 3
	 * Pip
	 	 sudo aptitude install python3-pip
	 * python cffi 0.9.2
	 	 sudo aptitude remove python3-cffi
		 sudo aptitude install libffi-dev
	 	 sudo pip3 install cffi
	 * python soundfile 0.7.0
	 	 sudo pip3 install PySoundFile
	 * python numpy 1.9.2
	 	 sudo aptitude remove python3-numpy
		 sudo pip3 install numpy
	 * python PyQT 5 
	 
	 * package libjack-jackd2-dev, libsndfile1-dev
	 	 sudo aptitude install libjack-jackd2-dev libsndfile1-dev
		 
	 * Running jack server