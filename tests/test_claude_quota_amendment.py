import pytest
from scripts.claude_quota_amendment import require_amended_capacity, remaining_schedule


def test_five_hour_window_can_reach_zero_but_weekly_reserve_remains():
 quota={'five_hour':{'remaining_percent':1,'resets_at':100},'seven_day':{'remaining_percent':90,'resets_at':100}}
 require_amended_capacity(quota,now=1)
 for window,remaining in [('five_hour',0),('seven_day',30)]:
  changed={k:dict(v) for k,v in quota.items()};changed[window]['remaining_percent']=remaining
  with pytest.raises(RuntimeError):require_amended_capacity(changed,now=1)


def test_remaining_schedule_never_repeats_an_attempt_even_if_its_result_failed():
 schedule=[['sonnet','a'],['opus','a'],['sonnet','b']]
 assert remaining_schedule(schedule,{('sonnet','a'),('opus','a')})==[['sonnet','b']]
 with pytest.raises(ValueError):remaining_schedule(schedule,{('other','unexpected')})
