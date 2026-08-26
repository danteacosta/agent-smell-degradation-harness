# ARTA-GAMMA-002

Removed condition: The measurable capacity limit of 1000 concurrent customers is omitted.

```diff
--- clean.py
+++ smelly.py
@@ -1,2 +1,2 @@
 def evaluate(concurrent_users):
-    return 0 <= concurrent_users <= 1000+    return concurrent_users >= 0```
