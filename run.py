import uvicorn
from dotenv import load_dotenv

# MUST be called before importing your routes/agents!
# This automatically pushes your .env file into os.environ
load_dotenv() 

from app.api.routes import app

if __name__ == "__main__":
    uvicorn.run("app.api.routes:app", host="127.0.0.1", port=8000, reload=True)
