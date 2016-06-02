default:
	@echo "make something yourself!"

SETUP_FLAG=.env/setup_done

.PHONY: run update superuser shell test

$(SETUP_FLAG): requirements.txt
	mkdir .env || true
	virtualenv --python=python --no-site-packages --distribute .env
	bash -c "source .env/bin/activate && pip install -r requirements.txt"
	touch $(SETUP_FLAG)

run: $(SETUP_FLAG) # start server
	bash -c "source .env/bin/activate && ./manage.py migrate"
	bash -c "source .env/bin/activate && ./manage.py runserver"

superuser: $(SETUP_FLAG) # create a superuser in the database
	bash -c "source .env/bin/activate && ./manage.py createsuperuser"

shell: $(SETUP_FLAG) # enter shell (use pip etc)
	bash -c "source .env/bin/activate && bash"

update: # when requirements.txt changed
	bash -c "source .env/bin/activate && pip install -r requirements.txt"

test: # run test suite
	bash -c "source .env/bin/activate && coverage run --source='umklapp,umklapp_site' ./manage.py test -v2 && coverage report"
