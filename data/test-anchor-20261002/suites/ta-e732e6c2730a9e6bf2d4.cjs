module.exports = {
  tests: [
    {
      name: "Saving edits persists both Work and Remaining work",
      run: async ({ context, page, url, assert }) => {
        page.setDefaultTimeout(2000);
        page.setDefaultNavigationTimeout(5000);
        await context.addInitScript(() => {
          window.initialState = { work: "10", remaining: "5" };
        });
        await page.goto(url);

        const work = page.getByRole("textbox", { name: "Work", exact: true });
        const remaining = page.getByRole("textbox", { name: "Remaining work", exact: true });
        await work.fill("12");
        await remaining.fill("7");
        await page.getByRole("button", { name: "Save", exact: true }).click();

        assert.equal(await work.inputValue(), "12");
        assert.equal(await remaining.inputValue(), "7");
        await page.reload();
        assert.equal(await work.inputValue(), "12");
        assert.equal(await remaining.inputValue(), "7");
      },
    },
    {
      name: "Remaining work equal to Work can be saved",
      run: async ({ context, page, url, assert }) => {
        page.setDefaultTimeout(2000);
        page.setDefaultNavigationTimeout(5000);
        await context.addInitScript(() => {
          window.initialState = { work: "10", remaining: "5" };
        });
        await page.goto(url);

        const work = page.getByRole("textbox", { name: "Work", exact: true });
        const remaining = page.getByRole("textbox", { name: "Remaining work", exact: true });
        await work.fill("8");
        await remaining.fill("8");
        await page.getByRole("button", { name: "Save", exact: true }).click();

        await page.reload();
        assert.equal(await work.inputValue(), "8");
        assert.equal(await remaining.inputValue(), "8");
      },
    },
    {
      name: "Increasing Remaining work above Work cannot overwrite saved values",
      run: async ({ context, page, url, assert }) => {
        page.setDefaultTimeout(2000);
        page.setDefaultNavigationTimeout(5000);
        await context.addInitScript(() => {
          window.initialState = { work: "9", remaining: "4" };
        });
        await page.goto(url);

        const work = page.getByRole("textbox", { name: "Work", exact: true });
        const remaining = page.getByRole("textbox", { name: "Remaining work", exact: true });
        const save = page.getByRole("button", { name: "Save", exact: true });

        await work.fill("9");
        await remaining.fill("4");
        await save.click();

        await remaining.fill("10");
        await work.focus();
        if (await save.isEnabled()) await save.click();

        await page.reload();
        assert.equal(await work.inputValue(), "9");
        assert.equal(await remaining.inputValue(), "4");
      },
    },
    {
      name: "Reducing Work below Remaining work cannot overwrite saved values",
      run: async ({ context, page, url, assert }) => {
        page.setDefaultTimeout(2000);
        page.setDefaultNavigationTimeout(5000);
        await context.addInitScript(() => {
          window.initialState = { work: "12", remaining: "4" };
        });
        await page.goto(url);

        const work = page.getByRole("textbox", { name: "Work", exact: true });
        const remaining = page.getByRole("textbox", { name: "Remaining work", exact: true });
        const save = page.getByRole("button", { name: "Save", exact: true });

        await work.fill("12");
        await remaining.fill("4");
        await save.click();

        await work.fill("3");
        await remaining.focus();
        if (await save.isEnabled()) await save.click();

        await page.reload();
        assert.equal(await work.inputValue(), "12");
        assert.equal(await remaining.inputValue(), "4");
      },
    },
  ],
};
