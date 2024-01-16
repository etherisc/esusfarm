import random

from nanoid import generate
from nanoid.method import method
from nanoid.resources import alphabet


NANO_ID_SIZE=12


def generate_nanoid_deterministic(seed_chars:str) -> str:
    random.seed(seed_chars)
    return ''.join([random.choice(alphabet) for _ in range(NANO_ID_SIZE)])


def generate_nanoid() -> str:
    return generate(size=NANO_ID_SIZE)


def is_valid_nanoid(nanoid: str) -> bool:
    # check length
    if len(nanoid) != NANO_ID_SIZE:
        return False
    
    # check alphabet
    return set(nanoid).issubset(set(alphabet))