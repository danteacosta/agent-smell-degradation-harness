module.exports = {
  tests: [
    {
      name: "Saving edits persists both work values after reload",
      run: async ({ context, page, url, assert }) => {
        page.setDefaultTimeout(3000);
        await context.addInitScript(() => {
          window.initialState = { work: "8", remaining: "3" };
        });
        await page.goto(url);
        const work = page.getByRole("textbox", { name: "Work", exact: true });
        const remaining = page.getByRole("textbox", { name: "Remaining work", exact: true });

        await work.fill("12");
        await remaining.fill("9");
        await page.getByRole("button", { name: "Save", exact: true }).click();
        await page.reload();

        assert.equal(await work.inputValue(), "12");
        assert.equal(await remaining.inputValue(), "9");
      },
    },
    {
      name: "Remaining work above Work is rejected without changing saved values",
      run: async ({ context, page, url, assert }) => {
        page.setDefaultTimeout(3000);
        await context.addInitScript(() => {
          window.initialState = { work: "20", remaining: "5" };
        });
        await page.goto(url);
        const work = page.getByRole("textbox", { name: "Work", exact: true });
        const remaining = page.getByRole("textbox", { name: "Remaining work", exact: true });
        const save = page.getByRole("button", { name: "Save", exact: true });

        await work.fill("18");
        await remaining.fill("4");
        await save.click();

        await work.fill("9");
        await remaining.fill("12");
        await save.click();

        assert.match(
          await page.getByRole("status").innerText(),
          /Remaining work cannot be greater than Work/i
        );

        await page.reload();
        assert.equal(await work.inputValue(), "18");
        assert.equal(await remaining.inputValue(), "4");
      },
    },
    {
      name: "Remaining work equal to Work can be saved",
      run: async ({ context, page, url, assert }) => {
        page.setDefaultTimeout(3000);
        await context.addInitScript(() => {
          window.initialState = { work: "10", remaining: "2" };
        });
        await page.goto(url);
        const work = page.getByRole("textbox", { name: "Work", exact: true });
        const remaining = page.getByRole("textbox", { name: "Remaining work", exact: true });

        await work.fill("6");
        await remaining.fill("6");
        await page.getByRole("button", { name: "Save", exact: true }).click();
        await page.reload();

        assert.equal(await work.inputValue(), "6");
        assert.equal(await remaining.inputValue(), "6");
      },
    },
    {
      name: "An invalid edit can be corrected and saved with zero remaining work",
      run: async ({ context, page, url, assert }) => {
        page.setDefaultTimeout(3000);
        await context.addInitScript(() => {
          window.initialState = { work: "10", remaining: "5" };
        });
        await page.goto(url);
        const work = page.getByRole("textbox", { name: "Work", exact: true });
        const remaining = page.getByRole("textbox", { name: "Remaining work", exact: true });
        const save = page.getByRole("button", { name: "Save", exact: true });

        await work.fill("3");
        await remaining.fill("4");
        await save.click();
        assert.match(
          await page.getByRole("status").innerText(),
          /Remaining work cannot be greater than Work/i
        );

        await remaining.fill("0");
        await save.click();
        await page.reload();

        assert.equal(await work.inputValue(), "3");
        assert.equal(await remaining.inputValue(), "0");
      },
    },
  ],
};
