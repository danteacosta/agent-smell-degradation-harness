module.exports = {
  tests: [
    {
      name: "Default upload creates a separate duplicate-content document and preserves existing documents",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          localStorage.removeItem("paperless-duplicate-pilot");
          window.initialState = {
            documents: [
              {
                id: "existing-document",
                title: "Original invoice",
                checksum: "same-content-checksum",
              },
              {
                id: "unrelated-document",
                title: "Unrelated report",
                checksum: "different-content-checksum",
              },
            ],
            upload: {
              title: "Uploaded invoice copy",
              checksum: "same-content-checksum",
            },
          };
        });

        await page.goto(url);
        const rows = page.locator("#documents .document");
        assert.equal(await rows.count(), 2);

        await page.getByRole("button", { name: "Upload document", exact: true }).click();
        await page.waitForFunction(
          () => document.querySelectorAll("#documents .document").length === 3,
          null,
          { timeout: 5000 }
        );

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

        const uploadedId = await uploaded.getAttribute("data-document-id");
        assert.ok(uploadedId, "The uploaded document should have its own identity");
        assert.notEqual(uploadedId, "existing-document");
        assert.notEqual(uploadedId, "unrelated-document");

        const ids = await rows.evaluateAll(elements =>
          elements.map(element => element.dataset.documentId)
        );
        assert.equal(new Set(ids).size, 3, "All three documents must remain separate");
      },
    },
  ],
};
