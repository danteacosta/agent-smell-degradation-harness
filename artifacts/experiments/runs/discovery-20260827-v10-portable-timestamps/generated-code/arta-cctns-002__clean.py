def evaluate(actor, timestamp, action, administrative_parameters, immutable):
    return bool(actor and timestamp and action and administrative_parameters is not None and immutable)
