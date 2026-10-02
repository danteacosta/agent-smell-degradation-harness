module.exports = {
  tests: [
    {
      name: "Default upload accepts duplicate content and preserves existing documents",
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

        await page.getByRole("heading", {
          name: "Original invoice",
          exact: true,
        }).waitFor({ timeout: 3000 });
        assert.equal(await rows.count(), 2);

        await page.getByRole("button", {
          name: "Upload document",
          exact: true,
        }).click({ timeout: 3000 });

        const uploadedHeading = page.getByRole("heading", {
          name: "Uploaded invoice copy",
          exact: true,
        });
        await uploadedHeading.waitFor({ timeout: 3000 });

        const verifyDocuments = async () => {
          assert.equal(await rows.count(), 3);
          assert.equal(
            await page.locator(
              '[data-document-id="existing-document"] h2'
            ).innerText(),
            "Original invoice"
          );
          assert.equal(
            await page.locator(
              '[data-document-id="unrelated-document"] h2'
            ).innerText(),
            "Unrelated receipt"
          );
          assert.equal(await uploadedHeading.count(), 1);
          assert.equal(await uploadedHeading.isVisible(), true);

          const ids = await rows.evaluateAll(elements =>
            elements.map(element => element.getAttribute("data-document-id"))
          );
          assert.ok(ids.every(id => typeof id === "string" && id.length > 0));
          assert.equal(new Set(ids).size, 3);
          assert.ok(ids.includes("existing-document"));
          assert.ok(ids.includes("unrelated-document"));
          return ids;
        };

        const idsAfterUpload = await verifyDocuments();

        await page.reload();
        await uploadedHeading.waitFor({ timeout: 3000 });

        const idsAfterReload = await verifyDocuments();
        assert.deepEqual(idsAfterReload.sort(), idsAfterUpload.sort());
      },
    },
  ],
};
