module.exports = {
  tests: [
    {
      name: "Saving edits persists both Work and Remaining work",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = { work: "10", remaining: "6" };
        });
        await page.goto(url);
        await page.getByRole("textbox", { name: "Work", exact: true }).fill("20");
        await page.getByRole("textbox", { name: "Remaining work", exact: true }).fill("8");
        await page.getByRole("button", { name: "Save", exact: true }).click();

        await page.reload();
        assert.equal(await page.getByRole("textbox", { name: "Work", exact: true }).inputValue(), "20");
        assert.equal(await page.getByRole("textbox", { name: "Remaining work", exact: true }).inputValue(), "8");
      },
    },
    {
      name: "Remaining work equal to Work can be saved",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = { work: "10", remaining: "6" };
        });
        await page.goto(url);
        await page.getByRole("textbox", { name: "Work", exact: true }).fill("12");
        await page.getByRole("textbox", { name: "Remaining work", exact: true }).fill("12");
        await page.getByRole("button", { name: "Save", exact: true }).click();

        await page.reload();
        assert.equal(await page.getByRole("textbox", { name: "Work", exact: true }).inputValue(), "12");
        assert.equal(await page.getByRole("textbox", { name: "Remaining work", exact: true }).inputValue(), "12");
      },
    },
    {
      name: "Remaining work greater than Work cannot replace saved values",
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
        await page.reload();

        await work.fill("9");
        await remaining.fill("10");
        if (await save.isEnabled()) {
          await save.click();
        }

        await page.reload();
        assert.equal(await work.inputValue(), "10", "Invalid edits must not persist Work");
        assert.equal(await remaining.inputValue(), "6", "Invalid edits must not persist Remaining work");
      },
    },
    {
      name: "Reducing Work below saved Remaining work cannot be saved",
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
        await page.reload();

        await work.fill("5");
        if (await save.isEnabled()) {
          await save.click();
        }

        await page.reload();
        assert.equal(await work.inputValue(), "10", "Work must not be saved below Remaining work");
        assert.equal(await remaining.inputValue(), "6");
      },
    },
  ],
};
