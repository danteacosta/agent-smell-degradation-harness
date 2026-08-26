# ARTA-FUN-002

Removed condition: The maximum of six parties is omitted.

```diff
--- clean.py
+++ smelly.py
@@ -1,2 +1,2 @@
 def evaluate(party_count):
-    return 1 <= party_count <= 6+    return party_count >= 1```
