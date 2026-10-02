module.exports = {
  tests: [
    {
      name: "Duplicate upload preserves both existing documents after reload",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = {
            documents: [
              {
                id: "original",
                title: "Original invoice",
                checksum: "matching-content-checksum",
              },
              {
                id: "unrelated",
                title: "Unrelated report",
                checksum: "different-content-checksum",
              },
            ],
            upload: {
              id: "new-upload",
              title: "Invoice copy",
              checksum: "matching-content-checksum",
            },
          };
        });

        await page.goto(url);
        const upload = page.getByRole("button", {
          name: "Upload document",
          exact: true,
        });
        await upload.waitFor({ state: "visible", timeout: 5000 });

        const checkDocuments = async () => {
          assert.equal(await page.locator(".document").count(), 2);
          assert.equal(
            await page
              .locator('[data-document-id="original"]')
              .getByRole("heading", { level: 2 })
              .textContent(),
            "Original invoice"
          );
          assert.equal(
            await page
              .locator('[data-document-id="unrelated"]')
              .getByRole("heading", { level: 2 })
              .textContent(),
            "Unrelated report"
          );
          assert.equal(
            await page.getByRole("heading", {
              name: "Invoice copy",
              exact: true,
            }).count(),
            0
          );
        };

        await checkDocuments();
        await upload.click({ timeout: 5000 });
        await checkDocuments();

        await page.reload();
        await upload.waitFor({ state: "visible", timeout: 5000 });
        await checkDocuments();
      },
    },
  ],
};
