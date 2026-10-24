class AppError(Exception):
    status_code = 400
    detail = "Bad request"

    def __init__(self, detail: str | None = None):
        if detail:
            self.detail = detail
        super().__init__(self.detail)


class UnauthorizedError(AppError):
    status_code = 401
    detail = "Not authenticated"


class ForbiddenError(AppError):
    status_code = 403
    detail = "Not enough permissions"


class NotFoundError(AppError):
    status_code = 404
    detail = "Not found"


class ConflictError(AppError):
    status_code = 409
    detail = "Already exists"