# ARTA-ERTMS-002

Removed condition: The requirement that the driver fail to acknowledge is removed, so the brake can be applied even after a valid acknowledgement.

```diff
--- clean.py
+++ smelly.py
@@ -1,2 +1,2 @@
 def evaluate(ack_required, acknowledged):
-    return 'apply_brake' if ack_required and not acknowledged else 'continue'+    return 'apply_brake' if ack_required else 'continue'```
