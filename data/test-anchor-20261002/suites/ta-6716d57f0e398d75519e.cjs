module.exports = {
  tests: [
    {
      name: "Saving edits preserves both values after reload",
      run: async ({ context, page, url, assert }) => {
        page.setDefaultTimeout(3000);
        await context.addInitScript(() => {
          window.initialState = { work: "10", remaining: "4" };
        });
        await page.goto(url);
        await page.evaluate(() => localStorage.clear());
        await page.reload();

        await page.getByRole("textbox", { name: "Work", exact: true }).fill("20");
        await page.getByRole("textbox", { name: "Remaining work", exact: true }).fill("12");
        await page.getByRole("button", { name: "Save", exact: true }).click();
        await page.reload();

        assert.equal(await page.getByRole("textbox", { name: "Work", exact: true }).inputValue(), "20");
        assert.equal(await page.getByRole("textbox", { name: "Remaining work", exact: true }).inputValue(), "12");
      },
    },
    {
      name: "Remaining work equal to Work can be saved",
      run: async ({ context, page, url, assert }) => {
        page.setDefaultTimeout(3000);
        await context.addInitScript(() => {
          window.initialState = { work: "10", remaining: "4" };
        });
        await page.goto(url);
        await page.evaluate(() => localStorage.clear());
        await page.reload();

        await page.getByRole("textbox", { name: "Work", exact: true }).fill("7");
        await page.getByRole("textbox", { name: "Remaining work", exact: true }).fill("7");
        await page.getByRole("button", { name: "Save", exact: true }).click();
        await page.reload();

        assert.equal(await page.getByRole("textbox", { name: "Work", exact: true }).inputValue(), "7");
        assert.equal(await page.getByRole("textbox", { name: "Remaining work", exact: true }).inputValue(), "7");
      },
    },
    {
      name: "Invalid edits show an error and preserve both saved values",
      run: async ({ context, page, url, assert }) => {
        page.setDefaultTimeout(3000);
        await context.addInitScript(() => {
          window.initialState = { work: "10", remaining: "4" };
        });
        await page.goto(url);
        await page.evaluate(() => localStorage.clear());
        await page.reload();

        const work = page.getByRole("textbox", { name: "Work", exact: true });
        const remaining = page.getByRole("textbox", { name: "Remaining work", exact: true });
        const save = page.getByRole("button", { name: "Save", exact: true });

        await work.fill("15");
        await remaining.fill("6");
        await save.click();
        await page.reload();
        assert.equal(await work.inputValue(), "15");
        assert.equal(await remaining.inputValue(), "6");

        await work.fill("9");
        await remaining.fill("10");
        await save.click();

        assert.equal(await page.getByRole("status").isVisible(), true);
        assert.match(
          await page.getByRole("status").innerText(),
          /Remaining work cannot be greater than Work/i
        );

        await page.reload();
        assert.equal(await work.inputValue(), "15");
        assert.equal(await remaining.inputValue(), "6");
      },
    },
    {
      name: "A rejected edit can be corrected and saved",
      run: async ({ context, page, url, assert }) => {
        page.setDefaultTimeout(3000);
        await context.addInitScript(() => {
          window.initialState = { work: "10", remaining: "4" };
        });
        await page.goto(url);
        await page.evaluate(() => localStorage.clear());
        await page.reload();

        const work = page.getByRole("textbox", { name: "Work", exact: true });
        const remaining = page.getByRole("textbox", { name: "Remaining work", exact: true });
        const save = page.getByRole("button", { name: "Save", exact: true });

        await work.fill("2");
        await remaining.fill("9");
        await save.click();
        assert.match(
          await page.getByRole("status").innerText(),
          /Remaining work cannot be greater than Work/i
        );

        await work.fill("12");
        await save.click();
        await page.reload();

        assert.equal(await work.inputValue(), "12");
        assert.equal(await remaining.inputValue(), "9");
      },
    },
  ],
};
