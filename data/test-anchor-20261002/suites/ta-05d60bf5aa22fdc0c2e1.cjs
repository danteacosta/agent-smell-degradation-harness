module.exports = {
  tests: [
    {
      name: "Default upload keeps matching and unrelated documents and adds a separate document",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          localStorage.clear();
          window.initialState = {
            documents: [
              {
                id: "existing",
                title: "Existing invoice",
                checksum: "identical-file-content",
              },
              {
                id: "unrelated",
                title: "Unrelated receipt",
                checksum: "different-file-content",
              },
            ],
            upload: {
              title: "Uploaded invoice copy",
              checksum: "identical-file-content",
            },
          };
        });

        await page.goto(url);
        const rows = page.locator("#documents .document");
        assert.deepEqual(await rows.locator("h2").allTextContents(), [
          "Existing invoice",
          "Unrelated receipt",
        ]);

        await page.getByRole("button", { name: "Upload document", exact: true }).click();

        assert.equal(
          await rows.count(),
          3,
          "Uploading matching content should create a third document"
        );
        assert.deepEqual(await rows.locator("h2").allTextContents(), [
          "Existing invoice",
          "Unrelated receipt",
          "Uploaded invoice copy",
        ]);

        const original = page.locator('[data-document-id="existing"]');
        const unrelated = page.locator('[data-document-id="unrelated"]');
        assert.equal(await original.locator("h2").textContent(), "Existing invoice");
        assert.equal(await unrelated.locator("h2").textContent(), "Unrelated receipt");

        const uploaded = rows.filter({
          has: page.getByRole("heading", {
            name: "Uploaded invoice copy",
            exact: true,
          }),
        });
        assert.equal(await uploaded.count(), 1);
        const newId = await uploaded.getAttribute("data-document-id");
        assert.ok(newId, "The uploaded document should have its own identity");
        assert.notEqual(newId, "existing");
        assert.notEqual(newId, "unrelated");
      },
    },
  ],
};
