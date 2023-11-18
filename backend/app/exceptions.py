class UserAlreadyExistsException(Exception):
    def __init__(self, email: str):
        self.message = f"A user with the email {email} already exists."
        super().__init__(self.message)


class UserDoesNotExistException(Exception):
    def __init__(self, user_id: int):
        self.message = f"A user with the id {user_id} does not exists."
        super().__init__(self.message)
