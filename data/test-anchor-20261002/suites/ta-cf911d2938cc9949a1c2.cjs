module.exports = {
  tests: [
    {
      name: "Duplicate content uploads as a separate document and preserves existing documents",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = {
            documents: [
              { id: "original", title: "Original invoice", checksum: "matching-content" },
              { id: "unrelated", title: "Unrelated report", checksum: "different-content" },
            ],
            upload: {
              title: "Uploaded invoice copy",
              checksum: "matching-content",
            },
          };
        });

        await page.goto(url);

        const rows = page.locator("#documents > section");
        const snapshot = () =>
          rows.evaluateAll(elements =>
            elements.map(element => ({
              id: element.dataset.documentId,
              title: element.querySelector("h2").textContent,
            }))
          );

        const before = await snapshot();
        assert.deepEqual(before, [
          { id: "original", title: "Original invoice" },
          { id: "unrelated", title: "Unrelated report" },
        ]);

        await page.getByRole("button", { name: "Upload document", exact: true }).click();
        await page.getByRole("heading", {
          name: "Uploaded invoice copy",
          exact: true,
        }).waitFor({ state: "visible", timeout: 3000 });

        const after = await snapshot();
        assert.equal(after.length, 3, "Uploading matching content must add a document");

        for (const existing of before) {
          assert.deepEqual(
            after.find(document => document.id === existing.id),
            existing,
            "Existing documents must retain their identities and titles"
          );
        }

        const uploaded = after.filter(document => document.title === "Uploaded invoice copy");
        assert.equal(uploaded.length, 1);
        assert.ok(uploaded[0].id, "The uploaded document must have an identity");
        assert.ok(
          before.every(document => document.id !== uploaded[0].id),
          "The uploaded document must have a separate identity"
        );
        assert.equal(new Set(after.map(document => document.id)).size, 3);

        await page.reload();
        await page.getByRole("heading", {
          name: "Uploaded invoice copy",
          exact: true,
        }).waitFor({ state: "visible", timeout: 3000 });

        assert.deepEqual(await snapshot(), after, "All three documents must survive reload");
      },
    },
  ],
};
