module.exports = {
  tests: [
    {
      name: "Saving edits persists both work values after reload",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = { work: "20", remaining: "5" };
        });
        await page.goto(url);

        const work = page.getByRole("textbox", { name: "Work", exact: true });
        const remaining = page.getByRole("textbox", { name: "Remaining work", exact: true });

        await work.fill("12");
        await remaining.fill("9");
        await page.getByRole("button", { name: "Save", exact: true }).click();

        assert.equal(await work.inputValue(), "12");
        assert.equal(await remaining.inputValue(), "9");

        await page.reload();
        assert.equal(await work.inputValue(), "12");
        assert.equal(await remaining.inputValue(), "9");
      },
    },
    {
      name: "Remaining work greater than Work cannot overwrite saved values",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = { work: "20", remaining: "6" };
        });
        await page.goto(url);

        const work = page.getByRole("textbox", { name: "Work", exact: true });
        const remaining = page.getByRole("textbox", { name: "Remaining work", exact: true });
        const save = page.getByRole("button", { name: "Save", exact: true });

        await work.fill("20");
        await remaining.fill("6");
        await save.click();

        await work.fill("8");
        await remaining.fill("9");
        await save.click();

        assert.match(
          await page.getByRole("status").innerText(),
          /remaining work cannot be greater than work/i
        );

        await page.reload();
        assert.equal(await work.inputValue(), "20");
        assert.equal(await remaining.inputValue(), "6");
      },
    },
    {
      name: "Remaining work equal to Work is accepted and persisted",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = { work: "20", remaining: "5" };
        });
        await page.goto(url);

        const work = page.getByRole("textbox", { name: "Work", exact: true });
        const remaining = page.getByRole("textbox", { name: "Remaining work", exact: true });

        await work.fill("7");
        await remaining.fill("7");
        await page.getByRole("button", { name: "Save", exact: true }).click();

        await page.reload();
        assert.equal(await work.inputValue(), "7");
        assert.equal(await remaining.inputValue(), "7");
      },
    },
    {
      name: "An invalid edit can be corrected and saved with zero remaining work",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = { work: "20", remaining: "5" };
        });
        await page.goto(url);

        const work = page.getByRole("textbox", { name: "Work", exact: true });
        const remaining = page.getByRole("textbox", { name: "Remaining work", exact: true });
        const save = page.getByRole("button", { name: "Save", exact: true });

        await work.fill("4");
        await remaining.fill("5");
        await save.click();

        assert.match(
          await page.getByRole("status").innerText(),
          /remaining work cannot be greater than work/i
        );

        await remaining.fill("0");
        await save.click();

        assert.equal(await page.getByRole("status").innerText(), "Saved.");

        await page.reload();
        assert.equal(await work.inputValue(), "4");
        assert.equal(await remaining.inputValue(), "0");
      },
    },
  ],
};
