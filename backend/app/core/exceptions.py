class ApplicationError(Exception):
    pass


class DocumentNotFoundError(ApplicationError):
    pass


class DocumentNotReadyError(ApplicationError):
    pass


class DocumentIndexError(ApplicationError):
    pass


class AnswerGenerationError(ApplicationError):
    pass
