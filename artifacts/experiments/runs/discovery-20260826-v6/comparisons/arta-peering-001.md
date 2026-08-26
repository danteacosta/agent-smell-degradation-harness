# ARTA-PEERING-001

Removed condition: The rejection response is removed; detection can occur without preventing the request.

```diff
--- clean.py
+++ smelly.py
@@ -1,2 +1,2 @@
 def evaluate(malicious):
-    return 'reject' if malicious else 'allow'+    return 'allow'```
