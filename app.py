from src import create_app
import os
from dotenv import load_dotenv

load_dotenv()

app = create_app()

DEBUG = os.getenv("DEBUG") == "True"
PORT = int(os.getenv('PORT', 80))
HOST = os.getenv('HOST', '0.0.0.0')



if __name__ == '__main__':
    # Uruchomienie aplikacji w trybie debugowania
    app.run(debug=DEBUG, port=PORT, host=HOST)

