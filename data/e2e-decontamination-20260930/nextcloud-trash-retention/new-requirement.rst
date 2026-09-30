Additionally, Nextcloud calculates the maximum available space every time a new
file is added. If the deleted files exceed the new maximum allowed space
Nextcloud will expire old deleted files until the limit is met once again.

.. note:: Your administrator may have configured the trash bin retention period 
to override the storage space management. See `admin documentation 
<https://docs.nextcloud.com/server/latest/admin_manual/configuration_server/config_sample_php_parameters.html#deleted-items-trash-bin>`_ for more details.
