# ARTA-NFR-001

Removed condition: The exact 60-second refresh interval is no longer specified.

```diff
--- clean.py
+++ smelly.py
@@ -1,2 +1,2 @@
 def evaluate(elapsed_seconds):
-    return elapsed_seconds >= 60
+    return elapsed_seconds >= 30
```
