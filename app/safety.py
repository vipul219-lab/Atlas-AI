

def is_safe_message(message: str) -> bool:
    blocked_words = ["hack", "steal password", "make bomb","kill someone"]
    lower_message = message.lower()

    for word in blocked_words:
        if word in lower_message:
            return False

    return True
