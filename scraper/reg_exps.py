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
