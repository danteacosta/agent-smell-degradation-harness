### Document Splitting {#document-splitting}

If document splitting is enabled, Paperless splits _after_ a separator barcode by default.
This means:

-   any page containing the configured separator barcode starts a new document, starting with the **next** page
-   pages containing the separator barcode are discarded

This is intended for dedicated separator sheets such as PATCH-T pages.

If [`PAPERLESS_CONSUMER_BARCODE_RETAIN_SPLIT_PAGES`](configuration.md#PAPERLESS_CONSUMER_BARCODE_RETAIN_SPLIT_PAGES)
is enabled, the page containing the separator barcode is retained instead. In this mode,
each page containing the separator barcode becomes the **first** page of a new document.

