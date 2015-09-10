# SuperBoucle

SuperBoucle est un logiciel de boucles, synchronisé avec jack transport et
complètement contrôlable en MIDI. Idéal pour la composition ou le live.

SuperBoucle est composé d'une grille de samples contrôlables avec n'importe
quel appareil midi comme un pad ou un clavier midi. SuperBoucle renvoi aussi
des informations à l'appareil MIDI afin d'allumer les LED du pad.

Un sample démarre toujours au début, c'est la principale originalité de
SuperBoucle. Il ne faut pas appuyer sur les touches à un moment précis mais
juste "avant la prochaine boucle". Vous pouvez ajuster la durée de lecture d'un
sample mais aussi le décaler soit en 'beat' soit en 'frame'. Ce décalage peut
être négatif, ce qui veut dire que le sample va démarrer avant le début de
mesure. Cette fonctionnalité peut être intéressante pour les sons mis à
l'envers.

SuperBoucle permet aussi d'enregistrer des nouvelles boucles, d'inverser ou de
normaliser un sample.

Quelques usages possibles :

* Vous voulez seulement contrôler le transport jack (play, pause, rewind) avec
  un appareil MIDI et vous voulez aussi pouvoir sauter à un endroit précis dans
  la chanson avec une touche de l'appareil MIDI.
* Vous avez quelques idée de partie mais pas de structure pour l'instant, vous
  voulez faire tourner un riff ...
* Vous faites du live avec des sample pré-enregistrés mais vous voulez garder
  le contrôle de la structure en live : lancer quand vous voulez la partie
  suivante

## Features

Fonctionnalités :

* Transport Jack
* Enregistrement
* Ajustement automatique de la latence d'enregistrement
* Entrée / Sortie audio
* Entrée / Sortie MIDI
* Normalise, inverse des samples
* Décalage négatif des samples, décalage en 'beat' ou en trame
* Format Audio: WAV, FLAC, AIFF, ... (pas de MP3 pour le moment)
* Interface intuitive pour la configuration des appareils MIDI
* Prise en charge de n'importe quel appareil MIDI : clavier classique, pad, BCF, Akai APC, ...
* Contrôle complet avec soit l'appareil MIDI ou le clavier et la souris
* Fonction 'Goto' pour sauter à un endroit précis dans la chanson

## Utilisation

Lancez d'abord le serveur Jack, ensuite lancer Superboucle. Chargez un sample
avec le bouton 'Add clip...', cliquez ensuite sur 'Edit', Start/stop et
'lecture'. Maintenant, vous devriez entendre le début de votre sample. Ajuster
le 'Beat Diviser' et le tempo...

## Installation

### Linux

Sous Linux les commandes suivantes devrait vous permettre d'installer les dépendances pour SuperBoucle (Testé sous Mint 17 et Ubuntu trusty) :

        sudo aptitude install jackd2 qjackctl a2jmidid
        sudo aptitude install python3 python3-pip python3-numpy
        sudo aptitude install python3-cffi python3-pyqt5
        sudo pip3 install PySoundFile

Ensuite téléchargez SuperBoucle sur https://sourceforge.net/projects/superboucle/files/ Image
Décompressez l'archive, ouvrez une console dans le répertoire SuperBoucle-x.x.x et lancez la commande :

        ./SuperBoucle.sh

### Windows

Il faut d'abord avoir Jack installé, si ce n'est pas déjà fait : http://jackaudio.org/downloads/
Ensuite, téléchargez SuperBoucle sur https://sourceforge.net/projects/superboucle/files/
Exécutez le "Setup".
Lancez Jack Port Audio puis SuperBoucle depuis le menu démarrer.

## Contact

N'hésitez pas à m'envoyer un email à superboucle@nura.eu si vous avez des questions ou si vous trouvez un bug.

## Périphériques MIDI

voir le fichier readme.md (pas encore traduit)
