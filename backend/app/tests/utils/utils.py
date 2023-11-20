import random
import string


def random_string(max_length: int) -> str:
    return "".join(
        random.choices(string.ascii_letters, k=random.randint(1, max_length))
    )
