# ARTA-PEERING-002

Removed condition: Coverage of unanticipated requests is removed.

```diff
--- clean.py
+++ smelly.py
@@ -1,2 +1,2 @@
 def evaluate(anticipated, unanticipated):
-    return anticipated and unanticipated
+    return anticipated
```
