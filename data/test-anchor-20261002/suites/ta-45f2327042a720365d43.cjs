module.exports = {
  tests: [
    {
      name: "Duplicate-content upload creates a separate document and preserves existing documents",
      run: async ({ context, page, url, assert }) => {
        page.setDefaultTimeout(3000);

        await context.addInitScript(() => {
          window.initialState = {
            documents: [
              {
                id: "original",
                title: "Original invoice",
                checksum: "identical-file-content",
              },
              {
                id: "unrelated",
                title: "Unrelated report",
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

        const readDocuments = () =>
          page.locator("#documents .document").evaluateAll(rows =>
            rows.map(row => ({
              id: row.dataset.documentId,
              title: row.querySelector("h2").textContent,
            }))
          );

        const before = await readDocuments();
        assert.equal(before.length, 2);
        assert.deepEqual(before, [
          { id: "original", title: "Original invoice" },
          { id: "unrelated", title: "Unrelated report" },
        ]);

        await page.getByRole("button", { name: "Upload document" }).click();
        await page.getByRole("heading", {
          name: "Uploaded invoice copy",
          exact: true,
        }).waitFor();

        const after = await readDocuments();
        assert.equal(after.length, 3, "The duplicate upload should add a document");

        for (const existing of before) {
          assert.deepEqual(
            after.find(document => document.id === existing.id),
            existing,
            "Each existing document should remain unchanged"
          );
        }

        const created = after.filter(
          document => !before.some(existing => existing.id === document.id)
        );
        assert.equal(created.length, 1);
        assert.ok(created[0].id, "The uploaded document should have its own identity");
        assert.equal(created[0].title, "Uploaded invoice copy");
        assert.equal(new Set(after.map(document => document.id)).size, 3);

        await page.reload();
        await page.getByRole("heading", {
          name: "Uploaded invoice copy",
          exact: true,
        }).waitFor();

        const persisted = await readDocuments();
        assert.equal(persisted.length, 3);
        for (const document of after) {
          assert.deepEqual(
            persisted.find(item => item.id === document.id),
            document,
            "All three documents should survive reload unchanged"
          );
        }
      },
    },
  ],
};
