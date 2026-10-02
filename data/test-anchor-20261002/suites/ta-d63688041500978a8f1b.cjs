module.exports = {
  tests: [
    {
      name: "Saving edits persists both values after reload",
      run: async ({ context, page, url, assert }) => {
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
        await context.addInitScript(() => {
          window.initialState = { work: "8", remaining: "4" };
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
      name: "Invalid edits preserve both previously saved values",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = { work: "8", remaining: "4" };
        });
        await page.goto(url);

        const work = page.getByRole("textbox", { name: "Work", exact: true });
        const remaining = page.getByRole("textbox", { name: "Remaining work", exact: true });
        const save = page.getByRole("button", { name: "Save", exact: true });

        await work.fill("20");
        await remaining.fill("5");
        await save.click();
        await page.reload();

        assert.equal(await work.inputValue(), "20");
        assert.equal(await remaining.inputValue(), "5");

        await work.fill("9");
        await remaining.fill("10");
        await save.click();

        assert.equal(await page.getByRole("status").isVisible(), true);
        assert.match(
          await page.getByRole("status").innerText(),
          /Remaining work cannot be greater than Work/i
        );

        await page.reload();
        assert.equal(await work.inputValue(), "20");
        assert.equal(await remaining.inputValue(), "5");
      },
    },
    {
      name: "Correcting invalid Remaining work allows saving",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = { work: "8", remaining: "4" };
        });
        await page.goto(url);

        const work = page.getByRole("textbox", { name: "Work", exact: true });
        const remaining = page.getByRole("textbox", { name: "Remaining work", exact: true });
        const save = page.getByRole("button", { name: "Save", exact: true });

        await work.fill("6");
        await remaining.fill("7");
        await save.click();

        assert.match(
          await page.getByRole("status").innerText(),
          /Remaining work cannot be greater than Work/i
        );

        await remaining.fill("0");
        await save.click();
        await page.reload();

        assert.equal(await work.inputValue(), "6");
        assert.equal(await remaining.inputValue(), "0");
      },
    },
  ],
};
