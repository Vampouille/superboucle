# SuperBoucle

SuperBoucle è un software basato su loop, pienamente controllabile con qualsiasi
dispositivo midi. SuperBoucle è inoltre sincronizzato con le funzioni di trasporto
di Jack. Puoi utilizzarlo in performance live o per composizione.

SuperBoucle è organizzato in una matrice di Samples (campioni), controllabile con 
dispositivi midi (ad esempio pads). SuperBoucle invierà informazioni al dispositivo 
midi (per illuminare i led). Il Sample partirà e si fermerà sempre su una battuta 
("beat"), o un gruppo di beats. Puoi adeguare la durata del sample ("loop period") 
ed il punto del beat da cui iniziarne la riproduzione ("offset"). Ma puoi anche 
adeguare l'offset del Sample in negativo; significa che il campione può cominciare
prima della prossima battuata (utile per i campioni che sono stati invertiti - 
"reversed sample"). Puoi registrare loops di qualunque durata, modificare i BPM, 
invertire e normalizzare samples ...

Utilizzo tipico:

* Ti occorre controllare il Trasporto di Jack (Play, pausa, riavvolgi...) con un
  dispositivo midi esterno e vuoi un pulsante per saltare ad un preciso punto
  della canzone;
* Hai delle parti strumentali sparse ma non hai idea della struttura della canzone;
* Fai performance live con parti strumentali pre-registrate (ad esempio ti manca il
  bassista) e non vuoi avere una struttura pre-definita per la canzone (modificando
  ad esempio la durata di alcune parti)

## Caratteristiche

* Trasporto Jack
* Registrazione
* Latenza automatica in registrazione
* Audio input / output
* Midi input / output
* Normalizzazione e inversione dei samples
* Offset dei sample negativa, in battute o frames
* Carica diversi formati: WAV, FLAC, AIFF... (no MP3 al momento)
* Interfaccia di midi-learn intuitiva
* Supporto per qualsiasi dispositivo midi: tastiere, pad, etc.
* Pienamente controllabile da dispositivo midi o mouse/tastiera
* Funzione "Go To" per posizionare il trasporto di Jack ad uno specifico punto

## Requisiti

### Linux

* Python 3
* Pip per python 3
* Moduli Python: Cffi, PySoundFile, Numpy, PyQT 5
* Jack server in esecuzione

### Windows

* Jack Audio Kit

## Installazione

### Linux

* Installazione Jack server :

        sudo aptitude install jackd2 qjackctl

* Installazione midi bridge (opzionale ma consigliato): 

        sudo aptitude install a2jmidid

* Installazione moduli python:

        sudo aptitude install python3 python3-pip python3-cffi python3-numpy python3-pyqt5
        sudo pip3 install PySoundFile

* Scaricare ed estrarre l'ultima versione di SuperBoucle da 
  https://github.com/Vampouille/superboucle/releases/

### Windows

* Eseguire il setup di Jack Audio Kit reperibile a 
  http://jackaudio.org/downloads/
* Eseguire il setup di SuperBoucle per Windows reperibile a 
  https://github.com/Vampouille/superboucle/releases

## Esecuzione

### Linux

Avviare il server audio Jack e poi eseguire lo script SuperBoucle.sh dalla 
directory di estrazione:

	./SuperBoucle.sh

### Windows

Avviare "Jack PortAudio" e poi SuperBoucle dal menu start.

## Contatti

Per domande, osservazioni e segnalazioni bug inviare una email a:
superboucle@nura.eu

## Dispositivi Midi

SuperBoucle può essere controllato da dispositivi midi come tastiere generiche
midi, batterie midi, dispositivi serie Akai APC, LaunchPad Novation, Behringer BCF... 
Per configurare un nuovo controller, occorre selezionare "Add device..." dal 
menu Device. Un altro metodo è importare un file .sbm (SuperBoucle Mapping) che
contiene la configurazione del dispositivo. 

Se realizzerai un nuovo dile di configurazione .sbm, sentiti libero di inviarlo, 
sarà incluso in un prossimo rilascio.

### Cosa può essere controllato da un dispositivo midi esterno?

Puoi:

* Avviare/fermare un sample
* Avviare o mettere in pausa il trasporto di Jack
* Posizionarti ad inizio canzone o ad una posizione specifica
* Adeguare il volume dell'uscita Master
* Adeguare il volume di ciascun sample
* Selezionare una posizione in griglia (clip) per registrare, ed avviare
  la registrazione

### Dispositivi midi sensibili alla pressione (velocity)

Per questi tipi di dispositivi, non premere i tasti/pad al massimo 
dell'intensità. Per poter gestire un dispositivo di questo tipo, Superboucle 
ha bisongno di ricevere un messaggio midi con una intensità "intermedia", e
non al massimo (che corrisponde a 127).

### Nome del dispositivo

Puoi impostare il nome del dispositivo a tua scelta, viene utilizzato solo
a scopo di visualizzazione in elenco.

### Configurazione Start/Stop

Nella sezione "Start / Stop buttons", fai click su "Learn first line" e
premi ciascun bottone della prima riga di bottoni del dispositivo midi
da sinistra a destra. Per aggiungere tutte le rimanenti righe premi "Add 
next line" e poi premi ogni bottone da sinitra a destra... e così via.
Al termine premi "stop" (opzionale).

Il primo evento midi ricevuto, da determinati canale e nota, verrà 
associato alla clip. Ad esempio, se il tuo dispositivo invia "Note On"
quando il tasto viene premuto e "Note Off" quando il tasto viene rilasciato,
Note On verrà utilizzato per avviare/fermare la clip ed ogni altro messaggio
verrà ignorato. Anche la Velocity (intensità) è utilizzata: se il dispositivo
invia "Note On" con una Velocity = 127 quando viene premuto il tasto e "Note
On" con Velocity = 0 quando viene rilasciato, solo Note On con Velocity 127 
verrà utilizzato per avviare/fermare la clip. Lo stesso comportamento viene
applicato ad altre funzioni come "Volume clip per riga".

### Configurazione volume Master

Se hai manopole o potenziometri sul tuo dispositivo, puoi associarne uno
al controllo del volume generale. Nella sezione "Master volume" fai click 
su "Master volume controller" e muovi il controller sul dispositivo. 
Dovrebbe comparire una descrizione del nuovo controller (Canale e id controller).

### Configurazione Trasporto

Se hai bottoni liberi a disposizione, puoi associarli alle azioni del Trasporto.
Nella sezione "Transport", fai click su un tasto del Trasporto e premi il tasto
desiderato sul controller midi. Dovrebbe apparire la descrizione dlel nuovo
bottone.
Anche il tasto Registra può essere associato ad un bottone midi in questa sezione.

### Configurazione volume Clip/sample volume

Se hai più di una manopola o potenziometro, puoi configurarli per
regolare il volume dei samples. Sulla maggior parte dei dispositivi ci sono
più bottoni che potenziometri, così non è possibile associare un potenziometro
ad ogni sample, non ce ne sono abbastanza. Nella maggior parte dei casi, 
avrai un potenziometro per ciascuna colonna di clip. Quindi SuperBoucle necessita
di sapere su quale riga vuoi agire. Dovrai configurare un bottone per riga
ed un potenziometro per ogni colonna. Se nella sezione "Start/stop configuration" 
hai configurato 8x4 bottoni (quattro righe e otto bottoni), ti occorrono 8 
potenziometri e 4 bottoni. Quando premi il primo bottone, i potenziometri
vengono associati al volume delle clip della prima riga.

Per prima cosa fai click su "Learn controllers" e muovi ciascun potenziometro
(nell'ordine corretto) e successivamente premi "Stop". Poi, premi "Learn line 
buttons" and premi il bottone corrispondente alla linea 1 sul dispositivo,
poi il bottone per la linea 2, etc. Infine premi "Stop".

### Colori

SuperBoucle invierà informazioni al dispositivo midi, illuminando i pad
assegnati alle clip, per indicare lo stato della clip/sample:

| Stato clip             | Colore             |
| -----------------------|--------------------|
| Nessun sample          | Spento/ no luce    |
| Clip in avvio          | Verde lampeggiante |
| Clip in riproduzione   | Verde              |
| Clip in arresto        | Rosso lampeggiante |
| Clip ferma             | Rosso              |
| Registrazione in avvio | Ambra lampeggiante |
| In registrazione       | Ambra              |

Per accendere la luce del pulsante sul dispositivo, SuperBoucle invierà
il messaggio midi "Note On" corrispondente al canale e nota dei pulsanti 
nella sezione "start/stop". La Velocity di questi messaggi è utilizzata
per impostare il colore. Quando premi il tasto "Test", SuperBoucle accenderà
tutti i bottoni al momento configurati.

Imposta quindi ogni valore per ottenere il colore corrispondente. Ad esempio,
dove indicato "green", modifica il valore finchè i tasti del dispositivo
saranno illuminati di colore verde.

### Comando di inizializzazione

Se hai a disposizione un particolare comando di reset da inviare al tuo 
dispositivo midi, puoi specificarlo qui (un comando per linea, in valore
decimale separato da virgole). Per esempio, per il LaunchPad S, questo comando
causerà il reset di tutti i bottoni ed imposterà la modalità lapeggiamento:
	
	176, 0, 0
	176, 0, 40
