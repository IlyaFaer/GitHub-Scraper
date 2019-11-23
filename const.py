import re

DIGITS_PATTERN = re.compile(r"[\d*]+")

# patterns, which are used for designation connections
# between issues and PRs
PATTERNS = (
    re.compile("Fixes[\:]?[\s]*#[\d*]+"),
    re.compile("Closes[\:]?[\s]*#[\d*]+"),
    re.compile("Towards[\:]?[\s]*#[\d*]+"),
    re.compile("IPR[\:]?[\s]*[\d*]+"),
)

NUM_REGEX = re.compile(r"""(?P<num>"[\d]+")""")

YELLOW_RAPS = {"red": 1, "green": 0.81, "blue": 0.28}

RED = {"red": 1, "green": 0.38, "blue": 0.52}

RED_KRAYOLA = {"red": 1, "green": 0.19, "blue": 0.19}

BLUE = {"red": 0.85, "green": 0.85, "blue": 1}

GREEN = {"red": 0.77, "green": 0.93, "blue": 0.82}

PINK = {"red": 1, "green": 0.36, "blue": 0.47}

GREY = {"red": 0.6, "green": 0.6, "blue": 0.6}

YELLOW = {"red": 1, "green": 1, "blue": 0.6}

GREEN_GOOD = {"red": 0, "green": 0.65, "blue": 0.31}

WHITE = {"red": 1, "green": 1, "blue": 1}

PURPLE = {"red": 0.73, "green": 0.33, "blue": 0.83}
