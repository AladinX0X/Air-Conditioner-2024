import pandas as pd
import time
import threading as thr
import numpy as np
import datetime as dt
import argparse
import logging
from sqlalchemy import create_engine, Column, Integer, Float, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class SimulationData(Base):
    __tablename__ = 'simulation_data'

    id = Column(Integer, primary_key=True, autoincrement=True)
    temperature = Column(Float)
    status = Column(String)
    fan_status = Column(String)
    date = Column(DateTime)
    time = Column(DateTime)
    door_open = Column(Boolean)

def create_engine_and_session():
    engine = create_engine('sqlite:///simulation_database.db?check_same_thread=False')
    Base.metadata.create_all(engine)
    return engine

class Simulation(thr.Thread):
    def __init__(self, target_temp, use_fan, auto_timer=900):
        thr.Thread.__init__(self)
        self.target_temp = target_temp
        self.use_fan = use_fan
        self.auto_timer = auto_timer
        self.temperature = np.random.uniform(20, 25)
        self.status = 'ON'
        self.fan_status = 'OFF' if not use_fan else 'ON'
        self.door_open = False
        self.engine = create_engine_and_session()
        self.start_time = time.time()
        self.start_temperature = self.temperature
        self.end_time = self.start_time + auto_timer if auto_timer else None
        self.door_open_time = None
        self.previous_temperature = None
        self.previous_status = None

    def run(self):
        print(f"Air Conditioner Starts at: {dt.datetime.now().strftime('%H:%M:%S')}, It will stop at: {dt.datetime.fromtimestamp(self.end_time).strftime('%H:%M:%S')}. Target Temperature is: {self.target_temp} °C.")
        while not self.is_time_to_stop():
            self.simulation_process()
            time.sleep(1)

    def simulation_process(self):
        try:
            self.update_temperature()
            
            if self.temperature >= 25 and not self.door_open:
                self.simulate_door_open()
            elif self.door_open and time.time() - self.door_open_time >= 15:
                self.simulate_door_close()

            self.record_data()
            self.print_data()

        except Exception as e:
            logging.error("Error in simulation process: %s", e)

    def is_time_to_stop(self):
        return self.end_time is not None and time.time() >= self.end_time

    def update_temperature(self):
        if self.temperature < self.target_temp:
            self.temperature += np.random.uniform(0.1, 0.3)
        elif self.temperature > self.target_temp:
            self.temperature -= np.random.uniform(0.1, 0.3)

    def record_data(self):
        current_time = dt.datetime.now()
        current_date = current_time.date()
        data = {
            "temperature": self.temperature,
            "status": self.status,
            "fan_status": self.fan_status,
            "date": current_date,
            "time": current_time,
            "door_open": self.door_open
        }

        with self.engine.connect() as conn:
            conn.execute(SimulationData.__table__.insert().values(data))

    def simulate_door_open(self):
        self.door_open = True
        self.door_open_time = time.time()
        self.previous_temperature = self.temperature
        self.previous_status = self.status
        self.temperature += np.random.uniform(3, 6)
        self.status = 'OFF'
        self.record_data()

    def simulate_door_close(self):
        self.door_open = False
        self.temperature = self.previous_temperature
        self.status = self.previous_status
        self.record_data()

    def print_data(self):
        current_time = dt.datetime.now()
        door_status = 'Open' if self.door_open else 'Closed'
        print(f"Time: {current_time.strftime('%H:%M:%S')}, Temperature: {self.temperature:.2f} °C, Status: {self.status}, Fan: {self.fan_status}, Door Status: {door_status}")

def start_simulation(target_temp, use_fan, run_time):
    if target_temp < 15 or target_temp > 33:
        print("Error: The target temperature must be between 15 and 33 degrees Celsius.")
    elif use_fan.lower() not in ('yes', 'no'):
        print("Error: 'use_fan' argument must be 'yes' or 'no'.")
    else:
        target_temp = target_temp
        use_fan = use_fan.lower() == 'yes'
        run_time = run_time * 60 if run_time else None

        simulation = Simulation(target_temp, use_fan, run_time)
        simulation.start()

        try:
            while simulation.is_alive():
                pass
        except KeyboardInterrupt:
            print("\nAir Conditioner stopped...")
            simulation.join()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Simulate air conditioning system.')
    parser.add_argument('target_temp', type=float, help='Enter the desired room Temperature (as a number)')
    parser.add_argument('use_fan', type=str, help='Turn on the fan? (yes/no)')
    parser.add_argument('run_time', type=int, help='Enter the run time in minutes (as a number)')
    args = parser.parse_args()

    start_simulation(args.target_temp, args.use_fan, args.run_time)