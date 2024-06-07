from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
import osfrom flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
import os
import logging
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from simulation import SimulationData

app = Flask(__name__, static_folder='frontend')
CORS(app)

DATABASE_URL = 'sqlite:///simulation_database.db?check_same_thread=False'
engine = create_engine(DATABASE_URL, echo=True)
Session = sessionmaker(bind=engine)

logging.basicConfig(level=logging.DEBUG)

@app.route('/api/data', methods=['GET'])
def get_simulation_data():
    session = Session()
    try:
        latest_data = session.query(SimulationData).order_by(SimulationData.id.desc()).first()
        if latest_data:
            data = {
                "temperature": latest_data.temperature,
                "status": latest_data.status,
                "fan_status": latest_data.fan_status,
                "date": latest_data.date.strftime('%Y-%m-%d'),
                "time": latest_data.time.strftime('%H:%M:%S'),
                "door_open": latest_data.door_open,
            }
        else:
            data = {
                "temperature": "N/A",
                "status": "N/A",
                "fan_status": "N/A",
                "date": "N/A",
                "time": "N/A",
                "door_open": False,
            }
    except Exception as e:
        logging.error("Error retrieving data: %s", e)
        data = {
            "temperature": "Error",
            "status": "Error",
            "fan_status": "Error",
            "date": "Error",
            "time": "Error",
            "door_open": "Error",
        }
    finally:
        session.close()
    return jsonify(data)

@app.route('/', methods=['GET'])
def serve_web_page():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:filename>', methods=['GET'])
def serve_static_file(filename):
    return send_from_directory(app.static_folder, filename)

if __name__ == "__main__":
    app.run(port=8081)

import time
import threading
import webbrowser
import argparse
from sqlalchemy.orm import sessionmaker
from simulation import SimulationData
from sqlalchemy import create_engine

app = Flask(__name__, static_folder='frontend')
CORS(app)

WEB_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), 'frontend'))
PORT = 8081
DATABASE_URL = 'sqlite:///simulation_database.db?check_same_thread=False'
engine = create_engine(DATABASE_URL, echo=True)
Session = sessionmaker(bind=engine)

@app.route('/api/data', methods=['GET'])
def get_simulation_data():
    session = Session()
    try:
        latest_data = session.query(SimulationData).order_by(SimulationData.id.desc()).first()
        if latest_data:
            data = {
                "temperature": latest_data.temperature,
                "status": latest_data.status,
                "fan_status": latest_data.fan_status,
                "date": latest_data.date.strftime('%Y-%m-%d'),
                "time": latest_data.time.strftime('%H:%M:%S'),
                "door_open": latest_data.door_open,
            }
        else:
            data = {
                "temperature": "N/A",
                "status": "N/A",
                "fan_status": "N/A",
                "date": "N/A",
                "time": "N/A",
                "door_open": False,
            }
    finally:
        session.close()
    return jsonify(data)

@app.route('/', methods=['GET'])
def serve_web_page():
    return send_from_directory(WEB_DIR, 'index.html')

@app.route('/<path:filename>', methods=['GET'])
def serve_static_file(filename):
    return send_from_directory(app.static_folder, filename)

def main():
    parser = argparse.ArgumentParser(description='Run web server for air conditioning simulation.')
    parser.add_argument('--port', type=int, default=PORT, help='Specify the port number (default: 8081)')
    args = parser.parse_args()

    web_server_thread = threading.Thread(target=lambda: app.run(port=args.port))
    web_server_thread.daemon = True
    web_server_thread.start()

    web_browser_thread = threading.Thread(target=webbrowser.open_new_tab, args=(f"http://localhost:{args.port}/",))
    web_browser_thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nWeb server stopped...")

if __name__ == "__main__":
    main()
