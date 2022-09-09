if not exist "%cd%\.venv\Scripts\activate" (
    python -m venv .venv
)
call .venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements\win_amd64.txt
python src\main.py
