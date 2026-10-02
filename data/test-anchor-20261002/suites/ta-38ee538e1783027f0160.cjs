module.exports = {
  tests: [
    {
      name: "Default upload creates a separate duplicate and preserves existing documents",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = {
            documents: [
              { id: "original", title: "Original invoice", checksum: "same-content" },
              { id: "unrelated", title: "Unrelated report", checksum: "other-content" },
            ],
            upload: {
              title: "Uploaded invoice copy",
              checksum: "same-content",
            },
          };
        });

        await page.goto(url);
        const rows = page.locator("section.document");

        const readDocuments = () =>
          rows.evaluateAll(elements =>
            elements.map(element => ({
              id: element.dataset.documentId,
              title: element.querySelector("h2").textContent,
            }))
          );

        const originalDocuments = [
          { id: "original", title: "Original invoice" },
          { id: "unrelated", title: "Unrelated report" },
        ];
        assert.deepEqual(await readDocuments(), originalDocuments);

        await page.getByRole("button", { name: "Upload document", exact: true }).click();

        const afterUpload = await readDocuments();
        assert.equal(afterUpload.length, 3, "Matching content must create another document");

        for (const original of originalDocuments) {
          assert.deepEqual(
            afterUpload.find(document => document.id === original.id),
            original,
            "Each existing document must remain unchanged"
          );
        }

        const uploaded = afterUpload.find(
          document => document.title === "Uploaded invoice copy"
        );
        assert.ok(uploaded, "The uploaded document must be visible");
        assert.ok(uploaded.id, "The new document must have an identity");
        assert.equal(new Set(afterUpload.map(document => document.id)).size, 3);

        await page.reload();
        assert.deepEqual(
          await readDocuments(),
          afterUpload,
          "All three documents must remain after reloading"
        );
      },
    },
  ],
};
