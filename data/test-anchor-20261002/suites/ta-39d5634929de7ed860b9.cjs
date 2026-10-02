module.exports = {
  tests: [
    {
      name: "Saving both edits preserves them after reload",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = { work: "24", remaining: "9" };
        });
        await page.goto(url);
        const work = page.getByRole("textbox", { name: "Work", exact: true });
        const remaining = page.getByRole("textbox", { name: "Remaining work", exact: true });

        await work.fill("36");
        await remaining.fill("12");
        await page.getByRole("button", { name: "Save", exact: true }).click();

        assert.equal(await work.inputValue(), "36");
        assert.equal(await remaining.inputValue(), "12");
        await page.reload();
        assert.equal(await work.inputValue(), "36");
        assert.equal(await remaining.inputValue(), "12");
      },
    },
    {
      name: "Saving only Work preserves Remaining work",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = { work: "20", remaining: "8" };
        });
        await page.goto(url);
        const work = page.getByRole("textbox", { name: "Work", exact: true });
        const remaining = page.getByRole("textbox", { name: "Remaining work", exact: true });

        const previousWork = await work.inputValue();
        const previousRemaining = await remaining.inputValue();
        const editedWork = previousWork === "40" ? "48" : "40";
        await work.fill(editedWork);
        await page.getByRole("button", { name: "Save", exact: true }).click();
        await page.reload();

        assert.equal(await work.inputValue(), editedWork);
        assert.equal(await remaining.inputValue(), previousRemaining);
      },
    },
    {
      name: "Later saves persist zero Remaining work without changing Work",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = { work: "16", remaining: "6" };
        });
        await page.goto(url);
        const work = page.getByRole("textbox", { name: "Work", exact: true });
        const remaining = page.getByRole("textbox", { name: "Remaining work", exact: true });
        const save = page.getByRole("button", { name: "Save", exact: true });

        await work.fill("18.5");
        await remaining.fill("4.5");
        await save.click();
        await page.reload();
        assert.equal(await work.inputValue(), "18.5");
        assert.equal(await remaining.inputValue(), "4.5");

        await remaining.fill("0");
        await save.click();
        await page.reload();

        assert.equal(await work.inputValue(), "18.5");
        assert.equal(await remaining.inputValue(), "0");
      },
    },
  ],
};
