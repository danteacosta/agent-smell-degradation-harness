def evaluate(rbc_supervision, authorized):
    return 'block' if not authorized else 'allow'
