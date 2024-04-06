from pydantic import EmailStr, validate_email


class CustomEmailStr(EmailStr):
    @classmethod
    def _validate(cls, value: EmailStr) -> EmailStr:
        email = validate_email(value)[1]
        return email.lower()
