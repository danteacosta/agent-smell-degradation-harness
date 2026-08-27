def evaluate(ack_required, acknowledged):
    return 'apply_brake' if ack_required and not acknowledged else 'continue'
