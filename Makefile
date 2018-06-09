install: venv

requirements.txt: setup.py
	virtualenv --clear --download --always-copy -p "$$(which python3)" venv-temp
	source venv-temp/bin/activate && \
		pip install numpy==1.14.0 && \
		python setup.py install && \
		pip freeze | sed 's/kubernetes-ingress-exporter.*//' > $@ && \
		rm -rf venv-temp

server:
	python3 exporter.py

venv: requirements.txt
	virtualenv --clear --download --always-copy -p "$$(which python3)" venv
	venv/bin/pip install --force-reinstall --upgrade pip setuptools wheel
	venv/bin/pip install -r requirements.txt
	@printf "\n\n%s%s%s\n" "$$(tput setaf 3)" "To activate virtualenv run: source venv/bin/activate" "$$(tput sgr0)"

.PHONY: server
