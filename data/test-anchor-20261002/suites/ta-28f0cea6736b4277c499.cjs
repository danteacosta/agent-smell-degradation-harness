module.exports = {
  tests: [
    {
      name: "Saving edits persists both Work and Remaining work",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = { work: "5", remaining: "2" };
        });
        await page.goto(url);
        const work = page.getByRole("textbox", { name: "Work", exact: true });
        const remaining = page.getByRole("textbox", { name: "Remaining work", exact: true });
        const save = page.getByRole("button", { name: "Save", exact: true });

        await work.fill("5");
        await remaining.fill("2");
        await save.click();

        await work.fill("10");
        await remaining.fill("9");
        await save.click();
        await page.reload();

        assert.equal(await work.inputValue(), "10");
        assert.equal(await remaining.inputValue(), "9");
      },
    },
    {
      name: "Remaining work equal to Work can be saved",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = { work: "8", remaining: "3" };
        });
        await page.goto(url);
        const work = page.getByRole("textbox", { name: "Work", exact: true });
        const remaining = page.getByRole("textbox", { name: "Remaining work", exact: true });
        const save = page.getByRole("button", { name: "Save", exact: true });

        await work.fill("8");
        await remaining.fill("3");
        await save.click();

        await work.fill("6.5");
        await remaining.fill("6.5");
        await save.click();
        await page.reload();

        assert.equal(await work.inputValue(), "6.5");
        assert.equal(await remaining.inputValue(), "6.5");
      },
    },
    {
      name: "Remaining work greater than Work cannot overwrite saved values",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = { work: "8", remaining: "4" };
        });
        await page.goto(url);
        const work = page.getByRole("textbox", { name: "Work", exact: true });
        const remaining = page.getByRole("textbox", { name: "Remaining work", exact: true });
        const save = page.getByRole("button", { name: "Save", exact: true });

        await work.fill("8");
        await remaining.fill("4");
        await save.click();

        await work.fill("9");
        await remaining.fill("10");
        await save.click();
        await page.reload();

        assert.equal(await work.inputValue(), "8");
        assert.equal(await remaining.inputValue(), "4");
      },
    },
    {
      name: "Lowering Work below Remaining work is rejected and corrected edits can save",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = { work: "10", remaining: "6" };
        });
        await page.goto(url);
        const work = page.getByRole("textbox", { name: "Work", exact: true });
        const remaining = page.getByRole("textbox", { name: "Remaining work", exact: true });
        const save = page.getByRole("button", { name: "Save", exact: true });

        await work.fill("10");
        await remaining.fill("6");
        await save.click();

        await work.fill("5");
        await save.click();
        await page.reload();

        assert.equal(await work.inputValue(), "10");
        assert.equal(await remaining.inputValue(), "6");

        await work.fill("5");
        await save.click();
        await remaining.fill("4");
        await save.click();
        await page.reload();

        assert.equal(await work.inputValue(), "5");
        assert.equal(await remaining.inputValue(), "4");
      },
    },
  ],
};
