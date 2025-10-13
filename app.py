from src import create_app
import os
from dotenv import load_dotenv

load_dotenv()

app = create_app()



if __name__ == '__main__':
    # Uruchomienie aplikacji w trybie debugowania
    app.run(debug=True, port=os.getenv('PORT', 5000))
