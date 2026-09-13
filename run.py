from dotenv import load_dotenv

load_dotenv()

from app import create_app

app = create_app() #entry point, calls __init__ to register routes, create client

if __name__ == "__main__":
    app.run(port=5000)
