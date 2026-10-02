module.exports = {
  tests: [
    {
      name: "Default duplicate upload creates a separate document and preserves both existing documents",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = {
            documents: [
              {
                id: "existing-document",
                title: "Original invoice",
                checksum: "matching-content-checksum",
              },
              {
                id: "unrelated-document",
                title: "Unrelated receipt",
                checksum: "different-content-checksum",
              },
            ],
            upload: {
              title: "Uploaded invoice copy",
              checksum: "matching-content-checksum",
            },
          };
        });

        await page.goto(url);
        const rows = page.locator("#documents .document");

        const snapshot = () =>
          rows.evaluateAll(elements =>
            elements.map(element => ({
              id: element.getAttribute("data-document-id"),
              title: element.querySelector("h2").textContent,
            }))
          );

        const original = [
          { id: "existing-document", title: "Original invoice" },
          { id: "unrelated-document", title: "Unrelated receipt" },
        ];
        assert.deepEqual(await snapshot(), original);

        await page.getByRole("button", { name: "Upload document", exact: true })
          .click({ timeout: 3000 });

        assert.equal(await rows.count(), 3, "The duplicate must create a third document");

        const afterUpload = await snapshot();
        for (const expected of original) {
          assert.deepEqual(
            afterUpload.find(document => document.id === expected.id),
            expected,
            "Existing documents must retain their identity and title"
          );
        }

        const copies = afterUpload.filter(
          document => document.title === "Uploaded invoice copy"
        );
        assert.equal(copies.length, 1);
        assert.ok(copies[0].id, "The uploaded document must have an identity");
        assert.equal(
          new Set(afterUpload.map(document => document.id)).size,
          3,
          "All three documents must have distinct identities"
        );
        assert.equal(
          await page.getByRole("heading", {
            name: "Uploaded invoice copy",
            exact: true,
          }).isVisible(),
          true
        );

        await page.reload();
        assert.deepEqual(
          await snapshot(),
          afterUpload,
          "The new document and both existing documents must survive a reload"
        );
      },
    },
  ],
};
