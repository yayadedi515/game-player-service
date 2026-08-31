class PlayerNotFoundError(Exception):
    pass


class DuplicatePlayerError(Exception):
    pass


class PlayerDeletionRestrictedError(Exception):
    pass


class InsufficientScoreError(Exception):
    pass


class InvalidTransferError(Exception):
    pass


class UnexpectedTransferResultError(Exception):
    pass
