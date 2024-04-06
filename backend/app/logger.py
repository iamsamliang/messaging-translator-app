import logging


def setup_logger() -> None:
    logging.basicConfig(
        filename="app.log",  # Log file path
        filemode="a",  # Append mode (use 'w' for overwrite mode)
        level=logging.ERROR,  # Logging level
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
