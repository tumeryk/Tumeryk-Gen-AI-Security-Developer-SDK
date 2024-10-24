import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from routers import auth, chat, config


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

# Include routers
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(config.router)

if __name__ == "__main__":
    uvicorn.run(app="main:app", host="0.0.0.0", port=8500, reload=True)
