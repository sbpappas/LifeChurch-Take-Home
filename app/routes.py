from datetime import datetime, timezone

from flask import Blueprint, current_app, jsonify, request

from app.errors import InvalidDayError, InvalidVersionError 
#created errors.py just to be cleaner

votd_bp = Blueprint("votd", __name__) #list of routes

# default Bible ver and "today" are both spec-ambiguous cases, documented in the README: UTC for "today", 
DEFAULT_VERSION_ID = 206 #WEB is in public domain
MIN_DAY = 1
MAX_DAY = 366

def _parse_day(raw):
    if raw is None:
        return datetime.now(timezone.utc).timetuple().tm_yday #default if day not provided

    #validation
    try:
        day = int(raw)
    except (TypeError, ValueError):
        raise InvalidDayError("day must be an integer between 1 and 366")

    if not (MIN_DAY <= day <= MAX_DAY):
        raise InvalidDayError("day must be an integer between 1 and 366")

    return day

def _parse_version(raw):
    if raw is None:
        return DEFAULT_VERSION_ID #default
    try:
        return int(raw)
    except (TypeError, ValueError):
        raise InvalidVersionError("version must be an integer")

def _get_client(): #gets client instance from flask app
    return current_app.extensions["youversion_client"]

# define the route that returns the verse of the day and passage text in JSON
@votd_bp.route("/votd", methods=["GET"]) #decorator that registers the route with the blueprint
def get_verse_of_the_day():
    #create all parts we need for the final response
    day = _parse_day(request.args.get("day"))
    version_id = _parse_version(request.args.get("version"))
    client = _get_client()
    passage_id = client.get_verse_of_the_day(day)
    passage = client.get_passage_text(version_id, passage_id)

    return jsonify(
        {
            "day": day,
            "reference": passage["reference"],
            "text": passage["text"],
            "version_id": version_id,
        }
    )

    #extra bit:
@votd_bp.route("/versions", methods=["GET"])
def get_versions():
    client = _get_client()
    versions = client.get_versions()
    return jsonify({
        "data":[
            {"id": version["id"], "abbreviation": version["abbreviation"], "title": version["title"]}            for version in versions
        ]
    })