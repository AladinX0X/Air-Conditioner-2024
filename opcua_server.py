import os
import socket
import time
from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, Boolean
from sqlalchemy.orm import sessionmaker
from opcua import Server
from flask import Flask, jsonify
from flask_cors import CORS
import threading
import webbrowser
import argparse
from simulation import SimulationData
from sqlalchemy import create_engine 
from sqlalchemy.ext.declarative import declarative_base

app = Flask(__name__)
CORS(app)

PORT = 8001
OPCUA_PORT = 8000

Base = declarative_base()
engine = create_engine('sqlite:///simulation_database.db', echo=False)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

def create_session():
    return Session()

@app.route('/api/data', methods=['GET'])
def get_simulation_data():
    session = create_session()
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

def update_opcua_variables(opcua_variables):
    session = create_session()
    try:
        last_record = session.query(SimulationData).order_by(SimulationData.id.desc()).first()
        if last_record:
            opcua_variables["Temperature"].set_value(last_record.temperature)
            opcua_variables["Status"].set_value(last_record.status)
            opcua_variables["FanStatus"].set_value(last_record.fan_status)
            opcua_variables["Date"].set_value(last_record.date.strftime('%Y-%m-%d'))
            opcua_variables["Time"].set_value(last_record.time.strftime('%H:%M:%S'))
            opcua_variables["DoorOpen"].set_value(last_record.door_open)
    except Exception as e:
        print("Error updating OPC UA variables:", str(e))
    finally:
        session.close()

def run_opcua_server():
    server = Server()
    ip_address = socket.gethostbyname(socket.gethostname())
    url = f"opc.tcp://{ip_address}:{OPCUA_PORT}"
    server.set_endpoint(url)
    ns = server.register_namespace("Simulation")
    myobj = server.nodes.objects.add_object(ns, "MyObject")

    variables = {
        "Temperature": Float,
        "Status": String,
        "FanStatus": String,
        "Date": String,
        "Time": String,
        "DoorOpen": Boolean
    }

    opcua_variables = {}
    for var_name, var_type in variables.items():
        opcua_variables[var_name] = myobj.add_variable(ns, var_name, var_type())

    server.start()
    return server, opcua_variables

def main():
    parser = argparse.ArgumentParser(description='Run web server and OPC UA server for air conditioning simulation.')
    parser.add_argument('--port', type=int, default=PORT, help='Specify the port number for the web server (default: 8001)')
    args = parser.parse_args()

    opcua_server, opcua_variables = run_opcua_server()

    web_server_thread = threading.Thread(target=lambda: app.run(port=args.port))
    web_server_thread.daemon = True
    web_server_thread.start()

    web_browser_thread = threading.Thread(target=webbrowser.open_new_tab, args=(f"http://localhost:{args.port}/",))
    web_browser_thread.start()

    try:
        while True:
            update_opcua_variables(opcua_variables)
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nWeb server and OPC UA server stopped...")
        opcua_server.stop()

if __name__ == "__main__":
    main()
