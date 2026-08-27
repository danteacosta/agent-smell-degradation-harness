# ARTA-FUN-001

Removed condition: The permission rule restricting speech to the initiator is removed.

```diff
--- clean.py
+++ smelly.py
@@ -1,2 +1,2 @@
 def evaluate(speaker_is_initiator):
-    return 'speak' if speaker_is_initiator else 'listen'
+    return 'speak'
```
