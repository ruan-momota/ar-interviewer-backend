# ar-interviewer-backend

- run `uv pip install -r requirements.txt` to install libs.
- run uv venv
- run `.venv\Scripts\activate` to activate venv.
- if use groq, create a `.env` file and add `GROQ_API_KEY=<YOUR API KEY>`
- run  `uvicorn app.main:app --reload` to start.
- check endpoints on http://127.0.0.1:8000/docs
