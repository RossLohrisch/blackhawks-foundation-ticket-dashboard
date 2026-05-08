.PHONY: run install clean

install:
	python3 -m venv .venv
	. .venv/bin/activate && python -m pip install --upgrade pip && python -m pip install -r requirements.txt

run:
	./run_app.sh

clean:
	rm -rf .venv __pycache__ src/__pycache__ .streamlit
