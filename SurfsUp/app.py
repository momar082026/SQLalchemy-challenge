# Import required libraries
from flask import Flask, jsonify
import numpy as np
import datetime as dt
from sqlalchemy import create_engine, func
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
 
 
#################################################
# Database Setup
#################################################

# Create engine using the `hawaii.sqlite` database file
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# Declare a Base using `automap_base()
Base = automap_base()

# Use the Base class to reflect the database tables
Base.prepare(autoload_with=engine)
 
# Assign the measurement class to a variable called `Measurement` and
# the station class to a variable called `Station`
Measurement = Base.classes.measurement
Station = Base.classes.station
 
# Create a session
session = Session(engine)

#################################################
# Flask Setup
#################################################
app = Flask(__name__)

# Define routes
@app.route("/")
def welcome():
    """List all available API routes."""
    return """
    <h1>Welcome to the Hawaii Climate API!</h1>
    <h2>Available Routes:</h2>
    <ul>
        <li><a href="/api/v1.0/precipitation">/api/v1.0/precipitation</a> - Last 12 months of precipitation data</li>
        <li><a href="/api/v1.0/stations">/api/v1.0/stations</a> - List of weather stations</li>
        <li><a href="/api/v1.0/tobs">/api/v1.0/tobs</a> - Temperature observations for most active station</li>
        <li>/api/v1.0/&lt;start&gt; - Temperature statistics from start date (format: YYYY-MM-DD)</li>
        <li>/api/v1.0/&lt;start&gt;/&lt;end&gt; - Temperature statistics for date range</li>
    </ul>
    """
 
@app.route("/api/v1.0/precipitation")
def precipitation():
    """Return last 12 months of precipitation data."""
    session = get_session()
    try:
        # Calculate date one year from last date
        most_recent_date = session.query(func.max(Measurement.date)).first()[0]
        most_recent_date = dt.datetime.strptime(most_recent_date, '%Y-%m-%d').date()
        one_year_ago = most_recent_date - dt.timedelta(days=365)
 
        # Query precipitation data
        results = session.query(Measurement.date, Measurement.prcp).\
            filter(Measurement.date >= one_year_ago).all()
 
        # Convert to dictionary
        prcp_dict = {date: prcp for date, prcp in results}
        return jsonify(prcp_dict)
    finally:
        session.close()
 
@app.route("/api/v1.0/stations")
def stations():
    """Return list of weather stations."""
    session = get_session()
    try:
        # Query all stations
        results = session.query(Station.station, Station.name).all()
        station_list = [{"station": station, "name": name} for station, name in results]
        return jsonify(station_list)
    finally:
        session.close()
 
@app.route("/api/v1.0/tobs")
def tobs():
    """Return temperature observations for most active station."""
    session = get_session()
    try:
        # Find most active station
        most_active_station = session.query(Measurement.station).\
            group_by(Measurement.station).\
            order_by(func.count(Measurement.station).desc()).first()[0]
 
        # Calculate date one year ago
        most_recent_date = session.query(func.max(Measurement.date)).\
            filter(Measurement.station == most_active_station).first()[0]
        most_recent_date = dt.datetime.strptime(most_recent_date, '%Y-%m-%d').date()
        one_year_ago = most_recent_date - dt.timedelta(days=365)
 
        # Query temperature data
        results = session.query(Measurement.date, Measurement.tobs).\
            filter(Measurement.station == most_active_station).\
            filter(Measurement.date >= one_year_ago).all()
 
        temps_list = [{"date": date, "temperature": temp} for date, temp in results]
        return jsonify(temps_list)
    finally:
        session.close()
 
@app.route("/api/v1.0/<start>")
@app.route("/api/v1.0/<start>/<end>")
def temp_stats(start, end=None):
    """Return temperature statistics for date range."""
    session = get_session()
    try:
        # Parse dates
        start_date = dt.datetime.strptime(start, '%Y-%m-%d')
        if end:
            end_date = dt.datetime.strptime(end, '%Y-%m-%d')
 
        # Select temperature calculations
        sel = [func.min(Measurement.tobs).label('min_temp'),
               func.avg(Measurement.tobs).label('avg_temp'),
               func.max(Measurement.tobs).label('max_temp')]
 
        # Query with or without end date
        if end:
            results = session.query(*sel).\
                filter(Measurement.date >= start_date).\
                filter(Measurement.date <= end_date).all()
        else:
            results = session.query(*sel).\
                filter(Measurement.date >= start_date).all()
 
        stats_dict = {
            "start_date": start,
            "end_date": end if end else "Present",
            "min_temp": results[0][0],
            "avg_temp": round(results[0][1], 1),
            "max_temp": results[0][2]
        }
        return jsonify(stats_dict)
    finally:
        session.close()
 
if __name__ == '__main__':
    app.run(debug=True)
