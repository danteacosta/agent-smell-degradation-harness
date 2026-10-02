module.exports = {
  tests: [
    {
      name: "Saving both edited values persists them after reload",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = { work: "10", remaining: "6" };
        });
        await page.goto(url);

        const work = page.getByRole("textbox", { name: "Work", exact: true });
        const remaining = page.getByRole("textbox", { name: "Remaining work", exact: true });

        await work.fill("24");
        await remaining.fill("9");
        await page.getByRole("button", { name: "Save", exact: true }).click();

        assert.equal(await work.inputValue(), "24");
        assert.equal(await remaining.inputValue(), "9");

        await page.reload();

        assert.equal(await work.inputValue(), "24");
        assert.equal(await remaining.inputValue(), "9");
      },
    },
    {
      name: "Subsequent saves update each field while preserving the other",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = { work: "12", remaining: "8" };
        });
        await page.goto(url);

        const work = page.getByRole("textbox", { name: "Work", exact: true });
        const remaining = page.getByRole("textbox", { name: "Remaining work", exact: true });
        const save = page.getByRole("button", { name: "Save", exact: true });

        await work.fill("12");
        await remaining.fill("8");
        await save.click();
        await page.reload();

        await work.fill("20");
        await save.click();
        await page.reload();

        assert.equal(await work.inputValue(), "20");
        assert.equal(await remaining.inputValue(), "8");

        await remaining.fill("3");
        await save.click();
        await page.reload();

        assert.equal(await work.inputValue(), "20");
        assert.equal(await remaining.inputValue(), "3");
      },
    },
    {
      name: "Zero values replace previously saved nonzero values",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = { work: "10", remaining: "5" };
        });
        await page.goto(url);

        const work = page.getByRole("textbox", { name: "Work", exact: true });
        const remaining = page.getByRole("textbox", { name: "Remaining work", exact: true });
        const save = page.getByRole("button", { name: "Save", exact: true });

        await work.fill("10");
        await remaining.fill("5");
        await save.click();
        await page.reload();

        await remaining.fill("0");
        await save.click();
        await page.reload();

        assert.equal(await work.inputValue(), "10");
        assert.equal(await remaining.inputValue(), "0");

        await work.fill("0");
        await save.click();
        await page.reload();

        assert.equal(await work.inputValue(), "0");
        assert.equal(await remaining.inputValue(), "0");
      },
    },
  ],
};
