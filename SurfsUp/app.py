# Import the dependencies
from datetime import datetime as dt, timedelta

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

from flask import Flask, jsonify

#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(autoload_with=engine)
# Base.prepare(engine, reflect=True)

# Save references to each table
station = Base.classes.station
measurement = Base.classes.measurement
#################################################
# Flask Setup
#################################################
app = Flask(__name__)

#################################################
# Flask Routes
#################################################
@app.route("/")
def welcome():
    """List all available api routes."""
    return (
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/(input start date)<br/>"
        f"/api/v1.0/(input start date)/(input end date)"
    )

@app.route("/api/v1.0/precipitation")
def precipitation():
    """Return last 12 months' precipitation data"""
    # Create our session (link) from Python to the DB
    session = Session(engine)
    # Query to retrieve the last 12 months of precipitation data
    recent_date = session.query(func.max(measurement.date)).scalar()
    recent_date = dt.strptime(recent_date, '%Y-%m-%d')
    one_year_ago = recent_date - timedelta(days=365)

    # Perform a query to retrieve the data and precipitation scores
    precipitation_data = session.query(measurement.date, measurement.prcp
    ).filter(measurement.date >= one_year_ago
    ).order_by(measurement.date).all()
    session.close()

    # Convert to dictionary using date as the key and prcp as the value
    all_precipitation = {}
    for date, prcp in precipitation_data:
        all_precipitation[date] = prcp

    return jsonify(all_precipitation)


@app.route("/api/v1.0/stations")
def stations():
    """Return a list of all stations"""
    # Create our session (link) from Python to the DB
    session = Session(engine)
    # Query all stations
    most_active_stations = session.query(
    station.name,
    measurement.station, func.count(measurement.station)
    ).join(station, measurement.station == station.station
            ).group_by(measurement.station
               ).order_by(func.count(measurement.station).desc()
                          ).all()

    session.close()

    # Create a list
    formatted_stations = [
        f"Station Name: {name}, Station ID: {station_id}, Count: {count}" 
        for name, station_id, count in most_active_stations
    ]

    # formatted_stations = [
    #     f"Station ID: {station_id}, Count: {count}" 
    #     for station_id, count in most_active_stations
    # ]

    return jsonify(formatted_stations)

@app.route("/api/v1.0/tobs")
def temperature():
    """Return temperatures of most active station in past 12 months"""
    # Create our session (link) from Python to the DB
    session = Session(engine)
    # Query to retrieve the last 12 months of precipitation data
    recent_date = session.query(func.max(measurement.date)).scalar()
    recent_date = dt.strptime(recent_date, '%Y-%m-%d')
    one_year_ago = recent_date - timedelta(days=365)
    # Query temps for most active station
    most_active_stations = session.query(
    measurement.station, func.count(measurement.station)
    ).group_by(measurement.station
               ).order_by(func.count(measurement.station).desc()
                          ).all()
    most_active_station_id = most_active_stations[0][0]
    most_active_temp_data = session.query(measurement.date, measurement.tobs).\
    filter(measurement.date >= one_year_ago
    ).filter(measurement.station == most_active_station_id
    ).order_by(measurement.date).all()

    session.close()

    # Convert to dictionary
    all_temps = {}
    for date, tobs in most_active_temp_data:
        all_temps[date] = tobs

    return jsonify(all_temps)

@app.route("/api/v1.0/<start>")
def start(start):
    """Return temperature stats for a specficied\
        start date"""
    # Create our session (link) from Python to the DB
    session = Session(engine)

    # Check if the date exists in the database
    date_exists = session.query(measurement.date).filter(measurement.date == start).first()
    if not date_exists:
        return jsonify({"error": "No temperature data available for the given date."})

     # Query to calculate the lowest, highest, and average \
     # temperatures at start date
    temperature_stats_start = session.query(
        station.name,
        func.min(measurement.tobs),
        func.max(measurement.tobs),
        func.avg(measurement.tobs)
        ).join(station, measurement.station == station.station
               ).filter(
                   measurement.date >= start
                   # Group by station name to get stats for each station
                   ).group_by(station.name).all()
    session.close()

    # Check if any data was returned
    if not temperature_stats_start or temperature_stats_start[0][0]\
          is None:
        return jsonify({"error": "No temperature data available for \
                        the given date."})
    # Create a dictionary to hold the results
    temp_dict_start = {}
    for stat in temperature_stats_start:
        temp_dict_start[stat[0]] = {  #station name
            'TMIN': stat[1],
            'TMAX': stat[2],
            'TAVG': stat[3]
        }

    return jsonify(temp_dict_start)

@app.route("/api/v1.0/<start>/<end>")
def start_end(start_date, end_date):
    """Return temperature stats for a specficied\
        date range"""
    # Create our session (link) from Python to the DB
    session = Session(engine)
     # Query to calculate the lowest, highest, and average \
     # temperatures at date range selected
    temperature_stats_start_end = session.query(
        station.name,
        func.min(measurement.tobs),
        func.max(measurement.tobs),
        func.avg(measurement.tobs)
        ).join(station, measurement.station == station.station
               ).filter(
        measurement.date >= start_date,
        measurement.date <= end_date
        # Group by station name to get stats for each station
        ).group_by(station.name).all()
    session.close()

    # Check if any data was returned
    if not temperature_stats_start_end or temperature_stats_start_end[0][0]\
          is None:
        return jsonify({"error": "No temperature data available for \
                        the given date range."})
    # Create a dictionary to hold the results
    temp_dict_start_end = {}
    for stat in temperature_stats_start_end:
        temp_dict_start_end[stat[0]] = {  #station name
            'TMIN': stat[1],
            'TMAX': stat[2],
            'TAVG': stat[3]
        }

    return jsonify(temp_dict_start_end)


if __name__ == '__main__':
    app.run(debug=True)
