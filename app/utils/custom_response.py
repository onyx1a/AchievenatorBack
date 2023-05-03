from enum import Enum


class ResponseCode(int, Enum):
    NO_ACHIEVEMENTS = -2
    ERROR = -1
    DEFAULT = 0
    SUCCESS = 200
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    TOO_MANY = 429
    INTERNAL_ERROR = 500
    UNAVAILABLE = 503
    LAST = 999


class DefaultResponse:
    def __init__(self, code: ResponseCode = ResponseCode.SUCCESS, message: str = ""):
        self._code = code
        self.status = code == ResponseCode.SUCCESS
        self._message = message
        self.data = None

    @property
    def code(self) -> ResponseCode:
        return self._code

    @code.setter
    def code(self, value: ResponseCode):
        self._code = value
        self.status = value == ResponseCode.SUCCESS

    @property
    def message(self) -> str:
        additional_message = self.get_additional_message()
        result = ""
        if self._message:
            result += self._message
        if additional_message:
            result += additional_message
        return result

    @message.setter
    def message(self, value: str):
        self._message = value

    def get_additional_message(self):
        match self.code:
            case ResponseCode.UNAUTHORIZED | ResponseCode.FORBIDDEN:
                return "Access is denied. Retrying will not help. Please verify your key= parameter."
            case ResponseCode.NOT_FOUND:
                return "The API requested does not exists."
            case ResponseCode.TOO_MANY:
                return "You are being rate limited."
            case ResponseCode.INTERNAL_ERROR:
                return (
                    "An unrecoverable error has occurred, please try again. If this continues to persist then "
                    "please post to the Steamworks developer discussion with additional details of your request."
                )
            case ResponseCode.UNAVAILABLE:
                return (
                    "Steam server is temporarily unavailable, or too busy to respond. Please wait and try again "
                    "later"
                )
            case _:
                return None
