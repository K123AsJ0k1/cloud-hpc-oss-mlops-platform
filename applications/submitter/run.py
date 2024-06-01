from app import create_app
import warnings

warnings.filterwarnings("ignore")
# The application can be run with the command 'python3 run.py'
if __name__ == "__main__":
    # This application uses the app factory method
    # to make code easier to understand and refactor
    app = create_app()
    app.run(host = '0.0.0.0', port = 5556)
