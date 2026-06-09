HIGH_STATUSES = {200, 401, 403, 405, 500, 502, 503}
MEDIUM_STATUSES = {301, 302, 307, 308, 429}

def classify_status(status_code):
    if status_code in HIGH_STATUSES:
        return "HIGH"
    if status_code in MEDIUM_STATUSES:
        return "MEDIUM"
    return "LOW"

def priority_sort_key(status_code):
    if status_code in HIGH_STATUSES:
        return 0
    if status_code in MEDIUM_STATUSES:
        return 1
    return 2
