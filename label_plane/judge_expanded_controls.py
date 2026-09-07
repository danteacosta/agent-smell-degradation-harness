"""Previously unqueried constructed controls for the frozen expanded-v2 study."""
from label_plane.exploratory_judge import JudgeRequest, ReferenceConstraint, serialize_judge_request
from label_plane.judge_controls import fingerprint


def build_expanded_pack():
    # reference, complete paraphrase, deleted condition, opposite behavior
    seeds = (
        ('A results page contains at most 50 items.',
         'No results page contains more than fifty items.',
         'A results page contains items.', 'A results page contains 51 items.'),
        ('A session expires after 15 minutes without user activity.',
         'Fifteen minutes of user inactivity causes the session to expire.',
         'Sessions can expire.', 'A session remains active after 15 minutes without user activity.'),
        ('The requested quantity must be between 1 and 8 inclusive.',
         'Accept quantities from one through eight, including both endpoints.',
         'The requested quantity must not exceed 8.', 'A requested quantity of zero is accepted.'),
        ('Registration rejects a username already assigned to another account.',
         'A username in use by an existing account cannot be used for registration.',
         'Registration requires a username.', 'Registration accepts a username assigned to another account.'),
        ('A search returns only records belonging to the requesting tenant.',
         'Every search result must belong to the tenant that issued the request.',
         'A search returns matching records.', 'A search returns records belonging to other tenants.'),
        ('Marketing emails are sent only to recipients who explicitly consented.',
         'Do not send marketing email to anyone without their explicit consent.',
         'Marketing emails are sent to recipients.', 'Marketing emails are sent to recipients who refused consent.'),
        ('Jobs with equal priority execute in their order of arrival.',
         'Among equally prioritized jobs, the one arriving first executes first.',
         'Jobs execute according to priority.', 'Jobs with equal priority execute in reverse arrival order.'),
        ('Login logs include the username but never include the password.',
         'Record the username in login logs and exclude the password entirely.',
         'Login logs include the username.', 'Login logs include both the username and password.'),
        ('If any write in a batch fails, all earlier writes in that batch are rolled back.',
         'A failed batch write undoes every preceding write from the same batch.',
         'If a write in a batch fails, an error is returned.',
         'If any write in a batch fails, the earlier writes in that batch remain committed.'),
        ('A document update is accepted only if the supplied version equals the stored version.',
         'Reject document updates unless their supplied version matches the stored version.',
         'A document update requires a supplied version.',
         'A document update is accepted when the supplied version differs from the stored version.'),
        ('Import verifies the file checksum before acceptance and rejects checksum mismatches.',
         'Check the checksum before accepting an imported file; refuse it if the checksum differs.',
         'Import computes a file checksum before acceptance.',
         'Import accepts files even when their checksum does not match.'),
        ('Disabling SMS notifications leaves the email notification setting unchanged.',
         'Turning off SMS notifications does not alter the email notification preference.',
         'Users can disable SMS notifications.',
         'Disabling SMS notifications also disables email notifications.'),
    )
    cases = []
    for seed, (reference, paraphrase, deleted, opposite) in enumerate(seeds):
        for operation, criteria, covered in (
            ('literal', reference, True), ('paraphrased', paraphrase, True),
            ('deleted', deleted, False), ('contradicted', opposite, False),
        ):
            identifier = fingerprint(['judge-expanded-v2', seed, operation])[:24]
            request = JudgeRequest(identifier, criteria, (ReferenceConstraint('c1', reference),))
            cases.append({'request': serialize_judge_request(request), 'oracle': {
                'stratum': 'expanded_new', 'seed_id': seed, 'operation': operation, 'covered': covered}})
    body = {'schema_version': 'judge-expanded-controls/v2', 'cases': cases}
    return {**body, 'pack_sha256': fingerprint(body)}
