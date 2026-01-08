"""
Custom exception classes
"""


class AuthenticationError(Exception):
    """Raised when authentication fails"""
    def __init__(self, message: str = "Authentication failed"):
        self.message = message
        super().__init__(self.message)


class AuthorizationError(Exception):
    """Raised when authorization fails"""
    def __init__(self, message: str = "Insufficient permissions"):
        self.message = message
        super().__init__(self.message)


class TokenError(Exception):
    """Raised when token validation fails"""
    def __init__(self, message: str = "Invalid token"):
        self.message = message
        super().__init__(self.message)



