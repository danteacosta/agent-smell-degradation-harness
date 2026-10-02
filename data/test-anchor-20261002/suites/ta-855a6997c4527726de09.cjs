module.exports = {
  tests: [
    {
      name: "Saving edits persists both values after reload",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = { work: "8", remaining: "3" };
        });
        await page.goto(url);
        await page.getByRole("textbox", { name: "Work", exact: true }).fill("12");
        await page.getByRole("textbox", { name: "Remaining work", exact: true }).fill("5");
        await page.getByRole("button", { name: "Save", exact: true }).click();
        await page.reload();

        assert.equal(await page.getByRole("textbox", { name: "Work", exact: true }).inputValue(), "12");
        assert.equal(await page.getByRole("textbox", { name: "Remaining work", exact: true }).inputValue(), "5");
      },
    },
    {
      name: "Remaining work equal to Work can be saved",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = { work: "8", remaining: "3" };
        });
        await page.goto(url);
        await page.getByRole("textbox", { name: "Work", exact: true }).fill("10");
        await page.getByRole("textbox", { name: "Remaining work", exact: true }).fill("10");
        await page.getByRole("button", { name: "Save", exact: true }).click();
        await page.reload();

        assert.equal(await page.getByRole("textbox", { name: "Work", exact: true }).inputValue(), "10");
        assert.equal(await page.getByRole("textbox", { name: "Remaining work", exact: true }).inputValue(), "10");
      },
    },
    {
      name: "Increasing Remaining work above Work cannot overwrite saved values",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = { work: "8", remaining: "3" };
        });
        await page.goto(url);
        const work = page.getByRole("textbox", { name: "Work", exact: true });
        const remaining = page.getByRole("textbox", { name: "Remaining work", exact: true });
        const save = page.getByRole("button", { name: "Save", exact: true });

        await work.fill("9");
        await remaining.fill("4");
        await save.click();
        await page.reload();
        assert.equal(await work.inputValue(), "9");
        assert.equal(await remaining.inputValue(), "4");

        await remaining.fill("10");
        if (await save.isEnabled()) await save.click();
        await page.reload();

        assert.equal(await work.inputValue(), "9");
        assert.equal(await remaining.inputValue(), "4");
      },
    },
    {
      name: "Reducing Work below Remaining work cannot overwrite saved values",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = { work: "8", remaining: "3" };
        });
        await page.goto(url);
        const work = page.getByRole("textbox", { name: "Work", exact: true });
        const remaining = page.getByRole("textbox", { name: "Remaining work", exact: true });
        const save = page.getByRole("button", { name: "Save", exact: true });

        await work.fill("12");
        await remaining.fill("5");
        await save.click();
        await page.reload();
        assert.equal(await work.inputValue(), "12");
        assert.equal(await remaining.inputValue(), "5");

        await work.fill("4");
        await remaining.fill("6");
        if (await save.isEnabled()) await save.click();
        await page.reload();

        assert.equal(await work.inputValue(), "12");
        assert.equal(await remaining.inputValue(), "5");
      },
    },
  ],
};
