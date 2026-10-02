module.exports = {
  tests: [
    {
      name: "Default upload creates a separate duplicate and preserves existing documents",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = {
            documents: [
              {
                id: "existing-document",
                title: "Original invoice",
                checksum: "identical-file-content-checksum",
              },
              {
                id: "unrelated-document",
                title: "Unrelated report",
                checksum: "different-file-content-checksum",
              },
            ],
            upload: {
              title: "Uploaded invoice copy",
              name: "Uploaded invoice copy",
              checksum: "identical-file-content-checksum",
            },
          };
        });

        await page.goto(url);
        const rows = page.locator("#documents .document");
        assert.equal(await rows.count(), 2);

        await page.getByRole("button", { name: "Upload document", exact: true }).click();
        await rows.nth(2).waitFor({ state: "visible", timeout: 5000 });

        const verifyDocuments = async () => {
          assert.equal(await rows.count(), 3);
          assert.equal(
            await page.locator('[data-document-id="existing-document"] h2').textContent(),
            "Original invoice"
          );
          assert.equal(
            await page.locator('[data-document-id="unrelated-document"] h2').textContent(),
            "Unrelated report"
          );

          const uploaded = rows.filter({
            has: page.getByRole("heading", {
              name: "Uploaded invoice copy",
              exact: true,
            }),
          });
          assert.equal(await uploaded.count(), 1);
          assert.equal(await uploaded.isVisible(), true);

          const ids = await rows.evaluateAll(elements =>
            elements.map(element => element.dataset.documentId)
          );
          assert.equal(new Set(ids).size, 3, "Each document must have a separate identity");
          const uploadedId = await uploaded.getAttribute("data-document-id");
          assert.ok(uploadedId);
          assert.notEqual(uploadedId, "existing-document");
          assert.notEqual(uploadedId, "unrelated-document");
          return uploadedId;
        };

        const uploadedId = await verifyDocuments();
        await page.reload();
        assert.equal(await verifyDocuments(), uploadedId);
      },
    },
  ],
};
