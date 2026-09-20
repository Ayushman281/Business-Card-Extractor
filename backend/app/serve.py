"""One-worker server entry point shared by hosted native and Docker deployment."""
import uvicorn

from app.core.config import Settings


def main():
    config = Settings()
    uvicorn.run("app.main:app", host=config.backend_host, port=config.backend_port,
                workers=1, access_log=False, server_header=False)


if __name__ == "__main__":
    main()
