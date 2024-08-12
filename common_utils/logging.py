import logging
import traceback

class ClassNameAndTracebackFilter(logging.Filter):
    def filter(self, record):
        # Add the class name to the log record
        record.class_name = ""
        try:
            # Find the calling class name from the stack
            record.class_name = record.args[0].__class__.__name__
        except (IndexError, AttributeError):
            pass

        # Add the stack trace to the log record
        record.stack_trace = traceback.format_exc() if record.exc_info else ""
        return True