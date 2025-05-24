from flask_sqlalchemy import SQLAlchemy

from app.database import db

class Location(db.Model):
    __tablename__ = 'locations'
    id = db.Column(db.Integer, primary_key=True)
    openaq_id = db.Column(db.Integer, unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    locality = db.Column(db.String(100))
    country_code = db.Column(db.String(2), nullable=False)
    latitude = db.Column(db.Numeric(9,6))
    longitude = db.Column(db.Numeric(9,6))
    is_mobile = db.Column(db.Boolean, default=False)
    last_updated = db.Column(db.DateTime, default=db.func.now())
    
    # Add relationship for eager loading
    sensors = db.relationship('Sensor', backref='location', lazy='select')

class Parameter(db.Model):
    __tablename__ = 'parameters'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    display_name = db.Column(db.String(100))
    unit = db.Column(db.String(20), nullable=False)

class Sensor(db.Model):
    __tablename__ = 'sensors'
    id = db.Column(db.Integer, primary_key=True)
    openaq_id = db.Column(db.Integer, unique=True, nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=False)
    parameter_id = db.Column(db.Integer, db.ForeignKey('parameters.id'), nullable=False)
    last_value = db.Column(db.Numeric(8,3))
    last_updated = db.Column(db.DateTime)
    
    # Add relationships for eager loading
    parameter = db.relationship('Parameter', backref='sensors', lazy='select')
    measurements = db.relationship('Measurement', backref='sensor', lazy='select')

class Measurement(db.Model):
    __tablename__ = 'measurements'
    id = db.Column(db.Integer, primary_key=True)
    sensor_id = db.Column(db.Integer, db.ForeignKey('sensors.id'), nullable=False)
    value = db.Column(db.Numeric(8,3), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)

