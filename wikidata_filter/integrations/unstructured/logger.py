import logging

from .utils import scarf_analytics

logger = logging.getLogger("unstructured")
trace_logger = logging.getLogger("unstructured.trace")

# Create a custom logging level
DETAIL = 15
logging.addLevelName(DETAIL, "DETAIL")


# Create a custom log method for the "DETAIL" level
def detail(self, message, *args, **kws):
    if self.isEnabledFor(DETAIL):
        self._log(DETAIL, message, args, **kws)


# Note(Trevor,Crag): to opt out of scarf analytics, set the environment variable:
# SCARF_NO_ANALYTICS=true. See the README for more info.
scarf_analytics()

# Add the custom log method to the logging.Logger class
logging.Logger.detail = detail  # type: ignore
