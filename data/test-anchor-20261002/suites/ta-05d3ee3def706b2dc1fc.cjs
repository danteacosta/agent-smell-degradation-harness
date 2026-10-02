module.exports = {
  tests: [
    {
      name: "Saving edits persists both values after reload",
      run: async ({ context, page, url, assert }) => {
        page.setDefaultTimeout(3000);
        await context.addInitScript(() => {
          window.initialState = { work: "8", remaining: "4" };
        });
        await page.goto(url);
        await page.getByRole("textbox", { name: "Work", exact: true }).fill("12");
        await page.getByRole("textbox", { name: "Remaining work", exact: true }).fill("9");
        await page.getByRole("button", { name: "Save", exact: true }).click();
        await page.reload();
        assert.equal(await page.getByRole("textbox", { name: "Work", exact: true }).inputValue(), "12");
        assert.equal(await page.getByRole("textbox", { name: "Remaining work", exact: true }).inputValue(), "9");
      },
    },
    {
      name: "Remaining work equal to Work can be saved",
      run: async ({ context, page, url, assert }) => {
        page.setDefaultTimeout(3000);
        await context.addInitScript(() => {
          window.initialState = { work: "10", remaining: "3" };
        });
        await page.goto(url);
        await page.getByRole("textbox", { name: "Work", exact: true }).fill("6");
        await page.getByRole("textbox", { name: "Remaining work", exact: true }).fill("6");
        await page.getByRole("button", { name: "Save", exact: true }).click();
        await page.reload();
        assert.equal(await page.getByRole("textbox", { name: "Work", exact: true }).inputValue(), "6");
        assert.equal(await page.getByRole("textbox", { name: "Remaining work", exact: true }).inputValue(), "6");
      },
    },
    {
      name: "Zero remaining work can be saved",
      run: async ({ context, page, url, assert }) => {
        page.setDefaultTimeout(3000);
        await context.addInitScript(() => {
          window.initialState = { work: "10", remaining: "3" };
        });
        await page.goto(url);
        await page.getByRole("textbox", { name: "Remaining work", exact: true }).fill("0");
        await page.getByRole("button", { name: "Save", exact: true }).click();
        await page.reload();
        assert.equal(await page.getByRole("textbox", { name: "Work", exact: true }).inputValue(), "10");
        assert.equal(await page.getByRole("textbox", { name: "Remaining work", exact: true }).inputValue(), "0");
      },
    },
    {
      name: "Excess remaining work cannot overwrite saved values",
      run: async ({ context, page, url, assert }) => {
        page.setDefaultTimeout(3000);
        await context.addInitScript(() => {
          window.initialState = { work: "8", remaining: "2" };
        });
        await page.goto(url);
        const work = page.getByRole("textbox", { name: "Work", exact: true });
        const remaining = page.getByRole("textbox", { name: "Remaining work", exact: true });
        const save = page.getByRole("button", { name: "Save", exact: true });

        await work.fill("9");
        await remaining.fill("3");
        await save.click();
        await page.reload();
        assert.equal(await work.inputValue(), "9");
        assert.equal(await remaining.inputValue(), "3");

        await remaining.fill("10");
        await remaining.blur();
        if (await save.isEnabled()) await save.click();
        await page.reload();
        assert.equal(await work.inputValue(), "9");
        assert.equal(await remaining.inputValue(), "3");
      },
    },
    {
      name: "Reducing Work below remaining is rejected and correction can be saved",
      run: async ({ context, page, url, assert }) => {
        page.setDefaultTimeout(3000);
        await context.addInitScript(() => {
          window.initialState = { work: "12", remaining: "4" };
        });
        await page.goto(url);
        const work = page.getByRole("textbox", { name: "Work", exact: true });
        const remaining = page.getByRole("textbox", { name: "Remaining work", exact: true });
        const save = page.getByRole("button", { name: "Save", exact: true });

        await work.fill("10");
        await remaining.fill("6");
        await save.click();
        await page.reload();
        assert.equal(await work.inputValue(), "10");
        assert.equal(await remaining.inputValue(), "6");

        await work.fill("5");
        await work.blur();
        if (await save.isEnabled()) await save.click();
        await page.reload();
        assert.equal(await work.inputValue(), "10");
        assert.equal(await remaining.inputValue(), "6");

        await work.fill("5");
        await remaining.fill("7");
        await remaining.blur();
        if (await save.isEnabled()) await save.click();

        await remaining.fill("4");
        await save.click();
        await page.reload();
        assert.equal(await work.inputValue(), "5");
        assert.equal(await remaining.inputValue(), "4");
      },
    },
  ],
};
