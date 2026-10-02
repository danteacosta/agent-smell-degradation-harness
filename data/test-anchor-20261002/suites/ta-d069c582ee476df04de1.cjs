module.exports = {
  tests: [
    {
      name: "Default upload creates a separate duplicate and preserves existing documents",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = {
            documents: [
              {
                id: "original",
                title: "Original document",
                checksum: "matching-content-checksum",
              },
              {
                id: "unrelated",
                title: "Unrelated document",
                checksum: "different-content-checksum",
              },
            ],
            upload: {
              title: "Uploaded duplicate",
              checksum: "matching-content-checksum",
            },
          };
        });

        await page.goto(url);
        const rows = page.locator("#documents .document");
        assert.equal(await rows.count(), 2);

        await page.getByRole("button", { name: "Upload document", exact: true }).click();
        await page.getByRole("heading", {
          name: "Uploaded duplicate",
          exact: true,
        }).waitFor({ state: "visible", timeout: 3000 });

        const verifyDocuments = async () => {
          assert.equal(await rows.count(), 3);
          assert.equal(
            await page.locator('[data-document-id="original"] h2').innerText(),
            "Original document"
          );
          assert.equal(
            await page.locator('[data-document-id="unrelated"] h2').innerText(),
            "Unrelated document"
          );

          const uploaded = rows.filter({
            has: page.getByRole("heading", {
              name: "Uploaded duplicate",
              exact: true,
            }),
          });
          assert.equal(await uploaded.count(), 1);
          assert.equal(await uploaded.isVisible(), true);

          const uploadedId = await uploaded.getAttribute("data-document-id");
          assert.ok(uploadedId);
          assert.notEqual(uploadedId, "original");
          assert.notEqual(uploadedId, "unrelated");
          return uploadedId;
        };

        const uploadedId = await verifyDocuments();

        await page.reload();
        assert.equal(await verifyDocuments(), uploadedId);
      },
    },
  ],
};
