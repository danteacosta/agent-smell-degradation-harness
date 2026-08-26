def evaluate(rbc_supervision, authorized):
    return 'block' if rbc_supervision and not authorized else 'allow'
