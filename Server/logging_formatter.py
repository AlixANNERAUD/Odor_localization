import logging

class LoggingFormatterClass(logging.Formatter):
    EMOJIS = {
        logging.DEBUG: "🐛",
        logging.INFO: "📝",
        logging.WARNING: "⚠️",
        logging.ERROR: "❌",
        logging.CRITICAL: "🔥"
    }

    def __init__(self):
        super().__init__("%(asctime)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

    def format(self, record):
        emoji = self.EMOJIS.get(record.levelno, "")
        record.msg = f"{emoji} - {record.msg}"
        return super().format(record)