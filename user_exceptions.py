class DuplicateUserError(Exception):
    pass

class InvalidCredentialsError(Exception):
    pass


class InvalidAccessTokenError(Exception):
    pass


class PermissionDeniedError(Exception):
    pass


class UserNotFoundError(Exception):
    pass
