module.exports = {
  tests: [
    {
      name: "Duplicate-content upload creates a separate document and preserves existing documents",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = {
            documents: [
              {
                id: "existing-document",
                title: "Original invoice",
                checksum: "identical-file-content",
              },
              {
                id: "unrelated-document",
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
        assert.equal(await rows.count(), 2);

        await page.getByRole("button", { name: "Upload document", exact: true }).click();
        await page
          .getByRole("heading", { name: "Uploaded invoice copy", exact: true })
          .waitFor({ state: "visible", timeout: 3000 });

        const readDocuments = () =>
          rows.evaluateAll((elements) =>
            elements.map((element) => ({
              id: element.dataset.documentId,
              title: element.querySelector("h2").textContent,
            }))
          );

        const documents = await readDocuments();
        assert.equal(documents.length, 3);
        assert.deepEqual(
          documents.find((document) => document.id === "existing-document"),
          { id: "existing-document", title: "Original invoice" }
        );
        assert.deepEqual(
          documents.find((document) => document.id === "unrelated-document"),
          { id: "unrelated-document", title: "Unrelated receipt" }
        );

        const uploaded = documents.filter(
          (document) => document.title === "Uploaded invoice copy"
        );
        assert.equal(uploaded.length, 1);
        assert.ok(uploaded[0].id);
        assert.equal(new Set(documents.map((document) => document.id)).size, 3);

        await page.reload();
        await page
          .getByRole("heading", { name: "Uploaded invoice copy", exact: true })
          .waitFor({ state: "visible", timeout: 3000 });
        assert.deepEqual(await readDocuments(), documents);
      },
    },
  ],
};
