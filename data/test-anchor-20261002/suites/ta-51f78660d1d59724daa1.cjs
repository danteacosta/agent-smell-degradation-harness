module.exports = {
  tests: [
    {
      name: "Default upload creates a separate duplicate and preserves documents after reload",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = {
            documents: [
              { id: "original", title: "Original invoice", checksum: "same-content" },
              { id: "unrelated", title: "Unrelated receipt", checksum: "other-content" },
            ],
            upload: {
              title: "Uploaded invoice copy",
              checksum: "same-content",
            },
          };
        });

        await page.goto(url);
        const rows = page.locator("#documents > section");
        assert.equal(await rows.count(), 2);

        await page.getByRole("button", { name: "Upload document", exact: true }).click();

        const verifyDocuments = async () => {
          assert.equal(await rows.count(), 3, "Matching content should create a third document");

          const original = page.locator('[data-document-id="original"]');
          const unrelated = page.locator('[data-document-id="unrelated"]');
          assert.equal(await original.count(), 1);
          assert.equal(await unrelated.count(), 1);
          assert.equal(await original.getByRole("heading").innerText(), "Original invoice");
          assert.equal(await unrelated.getByRole("heading").innerText(), "Unrelated receipt");

          const uploaded = rows.filter({
            has: page.getByRole("heading", { name: "Uploaded invoice copy", exact: true }),
          });
          assert.equal(await uploaded.count(), 1);
          assert.equal(await uploaded.isVisible(), true);

          const newId = await uploaded.getAttribute("data-document-id");
          assert.ok(newId, "The upload should have its own identity");
          assert.notEqual(newId, "original");
          assert.notEqual(newId, "unrelated");
          return newId;
        };

        const uploadedId = await verifyDocuments();
        await page.reload();
        assert.equal(await verifyDocuments(), uploadedId, "The new document should persist");
      },
    },
  ],
};
