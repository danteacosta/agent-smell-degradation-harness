# ARTA-ERTMS-001

Removed condition: The scope condition requiring active RBC supervision is removed.

```diff
--- clean.py
+++ smelly.py
@@ -1,2 +1,2 @@
 def evaluate(rbc_supervision, authorized):
-    return 'block' if rbc_supervision and not authorized else 'allow'+    return 'block' if not authorized else 'allow'```
