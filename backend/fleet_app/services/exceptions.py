"""业务层异常，由 error_handler 中间件统一转成结构化 JSON。"""


class BusinessConflict(Exception):
    """合规预检不通过等冲突场景，HTTP 409，调度单不得进入执行。"""

    def __init__(self, message, code='compliance_conflict', details=None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}


class BadRequest(Exception):
    def __init__(self, message, code='bad_request'):
        super().__init__(message)
        self.message = message
        self.code = code
