
UI = gui_ui.py cell_ui.py learn_ui.py learn_cell_ui.py

run : $(UI)
	./boucle.py

%_ui.py : %_ui.ui
	@echo "compiling $<"
	pyuic5 $< > $@


