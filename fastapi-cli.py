import typer
from pathlib import Path

app = typer.Typer()

@app.command()
def new(name: str):
    project_path = Path(name)
    project_path.mkdir(exist_ok=True)
    
    for folder in ["models", "controllers", "templates", "static", "utils", "logs"]:
        (project_path / folder).mkdir(exist_ok=True)
        
    # Write files .env
    (project_path / ".env").write_text("""# DB Configuration
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=
DB_PASSWORD=
DB_NAME=""")
    
    # Write files logger.py
    (project_path / "utils" / "logger.py").write_text("""from datetime import datetime
from colorama import Fore, Style
import os

LOG_DIR = "./logs"
os.makedirs(LOG_DIR, exist_ok=True)

def log(message, level="INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    colors = {
        "INFO": Fore.CYAN,
        "DEBUG": Fore.YELLOW,
        "ERROR": Fore.RED
    }
    color = colors.get(level, Fore.WHITE)
    log_file = os.path.join(LOG_DIR, "log.txt")
    with open(log_file, "a") as f:
        f.write(f"{timestamp} [{level}] {message}\\n")
    print(f"{color}[{timestamp}] [{level}] {message}{Style.RESET_ALL}")""")
    
    # Write files app.py
    (project_path / "app.py").write_text(f"""# Server
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

# Middleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

# Database
import os
from dotenv import load_dotenv
import aiomysql

from router import Router
from utils.logger import log

class {name.capitalize()}:
    def __init__(self):
        # Create app
        self.app = FastAPI()
        self.pool = None
        
        # Load env
        load_dotenv()
        log("Environment variables loaded", "DEBUG")
        
        # Load middlewares
        self.app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
        self.app.add_middleware(GZipMiddleware, minimum_size=1000)
        
        self.app.mount("/static", StaticFiles(directory="static"), name="static")
        self.app.add_event_handler("startup", self.on_startup)
        self.app.add_event_handler("shutdown", self.on_shutdown)
        
    async def on_startup(self):
        log("Application starting...", "INFO")
        try:
            self.pool = await aiomysql.create_pool(
                host=os.getenv("DB_HOST"),
                port=int(os.getenv("DB_PORT")),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                db=os.getenv("DB_NAME")
            )
            log("Database connected successfully", "INFO")
            Router(self.app, self.pool)
        except Exception as e:
            log(f"Database connection failed: {{e}}", "ERROR")
        
    async def on_shutdown(self):
        if not self.pool:
            log("Application shutting down...", "INFO")
            return
        self.pool.close()
        await self.pool.wait_closed()
        log("Application closed", "INFO")
        
webapp = {name.capitalize()}()
app = webapp.app

if __name__ == '__main__':
    log("Starting Uvicorn server...", "INFO")
    uvicorn.run(
        app="app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_includes=["*.py"]
    )""")
    
    # Write files router.py
    (project_path / "router.py").write_text(f"""from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
from aiomysql import Pool

from utils.logger import log

# Models

# Controllers

class Router():
    def __init__(self, app: FastAPI, pool: Pool):
        self.app = app
        self.pool = pool
        log("Routes loaded", "INFO")
        self.routes()
    
    def routes(self):
        @self.app.get("/favicon.ico", response_class=RedirectResponse)
        async def faviconHandler() -> RedirectResponse:
            return RedirectResponse("/static/favicon.ico")

        @self.app.get(path="/api/ping", response_class=JSONResponse)
        async def pingpongtest() -> JSONResponse:
            return JSONResponse(
                content={{
                    "status": "true",
                    "message": "pong"
                }},
                status_code=200
            )""")
    
    # Write files .gitignore
    (project_path / ".gitignore").write_text("""__pycache__/
.env/
logs/""")

if __name__ == '__main__':
    app()