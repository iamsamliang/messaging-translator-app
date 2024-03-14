class UserAlreadyExistsException(Exception):
    def __init__(self, email: str):
        self.message = f"A user with the email {email} already exists."
        super().__init__(self.message)


class OpenAIAuthenticationException(Exception):
    def __init__(self) -> None:
        self.message = f"Your OpenAI API key is invalid, expired, or revoked. Please generate a new one and update it here for use."
        super().__init__(self.message)
