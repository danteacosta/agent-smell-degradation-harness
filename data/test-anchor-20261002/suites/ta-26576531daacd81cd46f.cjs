module.exports = {
  tests: [
    {
      name: "Duplicate upload preserves both existing documents after reload",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = {
            documents: [
              {
                id: "existing",
                title: "Original invoice",
                checksum: "identical-file-content",
              },
              {
                id: "unrelated",
                title: "Unrelated receipt",
                checksum: "different-file-content",
              },
            ],
            upload: {
              id: "new-upload",
              title: "Renamed invoice copy",
              checksum: "identical-file-content",
            },
          };
        });

        await page.goto(url);

        const verifyDocuments = async () => {
          assert.equal(await page.locator(".document").count(), 2);
          assert.deepEqual(
            (await page.locator(".document h2").allTextContents()).sort(),
            ["Original invoice", "Unrelated receipt"]
          );
          assert.equal(
            await page.locator('[data-document-id="existing"]').count(),
            1
          );
          assert.equal(
            await page.locator('[data-document-id="unrelated"]').count(),
            1
          );
          assert.equal(
            await page.getByRole("heading", {
              name: "Renamed invoice copy",
              exact: true,
            }).count(),
            0
          );
        };

        await verifyDocuments();
        await page.getByRole("button", {
          name: "Upload document",
          exact: true,
        }).click();
        await verifyDocuments();

        await page.reload();
        await verifyDocuments();
      },
    },
  ],
};
