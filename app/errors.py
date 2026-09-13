# error types and the Flask handler that renders them.

# instructions doc says: every error this API returns takes the shape:
#    {"error": {"code": "...", "message": "..."}}

class AppError(Exception):
    # base class for errors that should be rendered as a JSON error response

    code = "APP_ERROR"
    status_code = 500

    def __init__(self, message, code=None, status_code=None):
        super().__init__(message)
        self.message = message
        if code is not None: #just set the code if it is provided
            self.code = code
        if status_code is not None:
            self.status_code = status_code

    def to_response_body(self):
        return {"error": {"code": self.code, "message": self.message}}

#all of these inherit from AppError and just change the code and status_code to match instructions
class InvalidDayError(AppError):
    code = "INVALID_DAY"
    status_code = 400


class InvalidVersionError(AppError):
    code = "INVALID_VERSION"
    status_code = 400


class UpstreamError(AppError):
    # raised when YouVersion is unreachable or gives unexpected responses

    code = "UPSTREAM_ERROR"
    status_code = 502


def register_error_handlers(app):
    from flask import jsonify

    #in flask you can use one functio nper error type, so we can just register one handler for AppError and one for all other exceptions
    @app.errorhandler(AppError)
    def handle_app_error(err):
        return jsonify(err.to_response_body()), err.status_code

    @app.errorhandler(Exception) # this is generic catch all
    def handle_unexpected_error(err):
        app.logger.exception("Unhandled error")
        body = {"error": {"code": "INTERNAL_ERROR", "message": "an unexpected error occurred"}}
        return jsonify(body), 500
