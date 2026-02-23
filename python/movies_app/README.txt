This WebAPI was validated under Python 3.14
Before you start, run:
python src/setup.py

Rename .template.env to .env
Fill the missing API key from OMDb API

Create Python 3.14 virtual environment:
python3.14 -m venv .venv

Install dependencies:
.venv/bin/pip3 install -r requirements.txt

Then, to run the server:
uvicorn main:app --reload