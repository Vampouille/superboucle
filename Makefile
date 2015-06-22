
UI = gui_ui.py cell_ui.py learn_ui.py learn_cell_ui.py manage_ui.py new_song_ui.py add_clip_ui.py playlist_ui.py port_manager_ui.py


run : $(UI) gui_rc.py
	#./boucle.py

%_ui.py : %_ui.ui
	@echo "compiling $<"
	pyuic5 $< > $@

gui_rc.py : gui.qrc icons/*
	pyrcc5 gui.qrc > gui_rc.py
