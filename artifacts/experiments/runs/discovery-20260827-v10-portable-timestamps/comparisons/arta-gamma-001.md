# ARTA-GAMMA-001

Removed condition: The measurable deployment deadline of less than 60 seconds is removed.

```diff
--- clean.py
+++ smelly.py
@@ -1,2 +1,2 @@
 def evaluate(usb_plugged, elapsed_seconds):
-    return usb_plugged and elapsed_seconds < 60
+    return usb_plugged and elapsed_seconds < 120
```
