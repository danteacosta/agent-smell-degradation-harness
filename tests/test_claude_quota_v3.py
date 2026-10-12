import json
import pytest
from scripts.claude_quota_v3 import read_quota, pending_slots


def event(status='allowed_warning',overage=False):
 return json.dumps({'type':'rate_limit_event','rate_limit_info':{'status':status,'isUsingOverage':overage,'unifiedWindows':{'five_hour':{'utilization':.9,'resetsAt':9999999999},'seven_day':{'utilization':.07,'resetsAt':9999999999}}}})


def test_warning_retains_valid_quota_without_enabling_extra_usage():
 quota=read_quota(event())
 assert quota['five_hour']['remaining_percent']==pytest.approx(10)
 for status,extra in [('rejected',False),('allowed_warning',True),('unknown',False)]:
  with pytest.raises(RuntimeError):read_quota(event(status,extra))


def test_exhaustion_signal_is_only_readable_for_recording_reset():
 assert read_quota(event('rejected'),allow_blocked=True)['five_hour']['remaining_percent']==pytest.approx(10)
 with pytest.raises(RuntimeError):read_quota(event('unknown'),allow_blocked=True)


def test_pending_excludes_every_prior_attempt_including_failed_calls():
 assert pending_slots([['a','1'],['b','1']],{('a','1')})==[['b','1']]
 with pytest.raises(ValueError):pending_slots([['a','1']],{('unexpected','1')})
