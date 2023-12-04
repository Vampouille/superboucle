#UI = $(for line in `find -name "*_ui.ui" `; do ; echo -n "${line/%_ui.ui/_ui.py} "; done;)
UI = superboucle/gui_ui.py superboucle/cell_ui.py superboucle/learn_ui.py superboucle/learn_cell_ui.py superboucle/device_manager_ui.py superboucle/new_song_ui.py superboucle/add_clip_ui.py superboucle/playlist_ui.py superboucle/port_manager_ui.py superboucle/add_port_ui.py superboucle/scene_manager_ui.py superboucle/add_scene_ui.py superboucle/edit_clip_ui.py superboucle/set_tempo_ui.py

dep : $(UI) superboucle/gui_rc.py
	echo $$UI

run : dep
	./boucle.py

clean:
	cd superboucle;rm -f `find -name "*_ui.py"`
	cd debian; rm -fr superboucle debhelper-build-stamp files superboucle.substvars

deb: dep
	make deb_aux || make unpatch_setup

deb_aux:
	git apply setup.py.debian.patch
	dpkg-buildpackage -us -uc
	cp ../superboucle_1.2.0-1_all.deb debian/
	make unpatch_setup

unpatch_setup:
	git checkout -- setup.py

docker-test: deb
	cd debian; docker-compose build && docker-compose up

%_ui.py : %_ui.ui
	echo $(UI)
	@echo "compiling $<"
	pyuic5 --import-from=superboucle $< > $@

superboucle/gui_rc.py : superboucle/gui.qrc superboucle/icons/*
	pyrcc5 superboucle/gui.qrc > superboucle/gui_rc.py
