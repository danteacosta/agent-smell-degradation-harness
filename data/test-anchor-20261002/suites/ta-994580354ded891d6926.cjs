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

        assert.deepEqual(await rows.locator("h2").allTextContents(), [
          "Original invoice",
          "Unrelated receipt",
        ]);

        await page.getByRole("button", { name: "Upload document", exact: true }).click();

        const verifyDocuments = async () => {
          assert.equal(
            await rows.count(),
            3,
            "Uploading matching content should create a third document"
          );

          assert.equal(
            await page
              .locator('[data-document-id="existing-document"] h2')
              .textContent(),
            "Original invoice"
          );
          assert.equal(
            await page
              .locator('[data-document-id="unrelated-document"] h2')
              .textContent(),
            "Unrelated receipt"
          );

          const uploaded = rows.filter({
            has: page.getByRole("heading", {
              name: "Uploaded invoice copy",
              exact: true,
            }),
          });
          assert.equal(await uploaded.count(), 1);

          const uploadedId = await uploaded.getAttribute("data-document-id");
          assert.ok(uploadedId, "The uploaded document should have an identity");
          assert.notEqual(uploadedId, "existing-document");
          assert.notEqual(uploadedId, "unrelated-document");
          return uploadedId;
        };

        const uploadedId = await verifyDocuments();

        await page.reload();
        assert.equal(
          await verifyDocuments(),
          uploadedId,
          "The separate uploaded document should persist after reload"
        );
      },
    },
  ],
};
