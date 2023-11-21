class UserAlreadyExistsException(Exception):
    def __init__(self, email: str):
        self.message = f"A user with the email {email} already exists."
        super().__init__(self.message)
