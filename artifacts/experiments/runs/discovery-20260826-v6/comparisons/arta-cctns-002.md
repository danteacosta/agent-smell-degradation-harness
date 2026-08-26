# ARTA-CCTNS-002

Removed condition: The immutability obligation is removed, so a later operation may alter or delete the audit record.

```diff
--- clean.py
+++ smelly.py
@@ -1,2 +1,2 @@
 def evaluate(actor, timestamp, action, administrative_parameters, immutable):
-    return bool(actor and timestamp and action and administrative_parameters is not None and immutable)+    return bool(actor and timestamp and action and administrative_parameters is not None)```
