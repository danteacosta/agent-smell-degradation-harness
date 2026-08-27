# ARTA-NFR-002

Removed condition: The enforcement outcome that denies unauthorized users is omitted; classification alone is not access control.

```diff
--- clean.py
+++ smelly.py
@@ -1,2 +1,2 @@
 def evaluate(authorized):
-    return 'allow' if authorized else 'deny'
+    return 'allow'
```
