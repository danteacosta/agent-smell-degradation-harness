# ARTA-CCTNS-001

Removed condition: The user's explicit opt-in condition is removed.

```diff
--- clean.py
+++ smelly.py
@@ -1,2 +1,2 @@
 def evaluate(opted_in, action_taken):
-    return opted_in and action_taken+    return action_taken```
