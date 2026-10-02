module.exports = {
  tests: [
    {
      name: "Uploading duplicate content creates a separate document and preserves existing documents",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = {
            documents: [
              { id: "original", title: "Original document", checksum: "same-content" },
              { id: "unrelated", title: "Unrelated document", checksum: "other-content" },
            ],
            upload: { title: "Uploaded copy", checksum: "same-content" },
          };
        });

        await page.goto(url);
        const rows = page.locator("#documents .document");
        assert.equal(await rows.count(), 2);

        await page.getByRole("button", { name: "Upload document", exact: true }).click();
        await page.getByRole("heading", { name: "Uploaded copy", exact: true })
          .waitFor({ state: "visible", timeout: 3000 });

        const readDocuments = () => rows.evaluateAll(elements =>
          elements.map(element => ({
            id: element.dataset.documentId,
            title: element.querySelector("h2").textContent,
          }))
        );

        const documents = await readDocuments();
        assert.equal(documents.length, 3);
        assert.deepEqual(documents.find(document => document.id === "original"), {
          id: "original",
          title: "Original document",
        });
        assert.deepEqual(documents.find(document => document.id === "unrelated"), {
          id: "unrelated",
          title: "Unrelated document",
        });

        const uploaded = documents.filter(document => document.title === "Uploaded copy");
        assert.equal(uploaded.length, 1);
        assert.ok(uploaded[0].id);
        assert.equal(new Set(documents.map(document => document.id)).size, 3);

        await page.reload();
        assert.deepEqual(await readDocuments(), documents);
      },
    },
  ],
};
