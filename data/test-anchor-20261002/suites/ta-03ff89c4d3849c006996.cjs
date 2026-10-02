module.exports = {
  tests: [
    {
      name: "Saving edits persists both values after reload",
      run: async ({ context, page, url, assert }) => {
        page.setDefaultTimeout(3000);
        await context.addInitScript(() => {
          window.initialState = { work: "10", remaining: "6" };
        });
        await page.goto(url);

        await page.getByRole("textbox", { name: "Work", exact: true }).fill("24");
        await page.getByRole("textbox", { name: "Remaining work", exact: true }).fill("9");
        await page.getByRole("button", { name: "Save", exact: true }).click();
        assert.equal(await page.getByRole("status").textContent(), "Saved");

        await page.reload();
        assert.equal(await page.getByRole("textbox", { name: "Work", exact: true }).inputValue(), "24");
        assert.equal(await page.getByRole("textbox", { name: "Remaining work", exact: true }).inputValue(), "9");
      },
    },
    {
      name: "Remaining work equal to Work can be saved",
      run: async ({ context, page, url, assert }) => {
        page.setDefaultTimeout(3000);
        await context.addInitScript(() => {
          window.initialState = { work: "10", remaining: "6" };
        });
        await page.goto(url);

        await page.getByRole("textbox", { name: "Work", exact: true }).fill("8");
        await page.getByRole("textbox", { name: "Remaining work", exact: true }).fill("8");
        await page.getByRole("button", { name: "Save", exact: true }).click();
        assert.equal(await page.getByRole("status").textContent(), "Saved");

        await page.reload();
        assert.equal(await page.getByRole("textbox", { name: "Work", exact: true }).inputValue(), "8");
        assert.equal(await page.getByRole("textbox", { name: "Remaining work", exact: true }).inputValue(), "8");
      },
    },
    {
      name: "Invalid edits leave both previously saved values unchanged",
      run: async ({ context, page, url, assert }) => {
        page.setDefaultTimeout(3000);
        await context.addInitScript(() => {
          window.initialState = { work: "20", remaining: "5" };
        });
        await page.goto(url);

        const work = page.getByRole("textbox", { name: "Work", exact: true });
        const remaining = page.getByRole("textbox", { name: "Remaining work", exact: true });
        const save = page.getByRole("button", { name: "Save", exact: true });

        await work.fill("20");
        await remaining.fill("5");
        await save.click();
        assert.equal(await page.getByRole("status").textContent(), "Saved");

        await work.fill("9");
        await remaining.fill("10");
        await save.click();
        assert.equal(
          await page.getByRole("status").textContent(),
          "Remaining work cannot be greater than Work"
        );

        await page.reload();
        assert.equal(await work.inputValue(), "20");
        assert.equal(await remaining.inputValue(), "5");
      },
    },
    {
      name: "An invalid edit can be corrected and saved with zero remaining work",
      run: async ({ context, page, url, assert }) => {
        page.setDefaultTimeout(3000);
        await context.addInitScript(() => {
          window.initialState = { work: "10", remaining: "6" };
        });
        await page.goto(url);

        const work = page.getByRole("textbox", { name: "Work", exact: true });
        const remaining = page.getByRole("textbox", { name: "Remaining work", exact: true });
        const save = page.getByRole("button", { name: "Save", exact: true });

        await work.fill("3");
        await remaining.fill("4");
        await save.click();
        assert.equal(
          await page.getByRole("status").textContent(),
          "Remaining work cannot be greater than Work"
        );

        await remaining.fill("0");
        await save.click();
        assert.equal(await page.getByRole("status").textContent(), "Saved");

        await page.reload();
        assert.equal(await work.inputValue(), "3");
        assert.equal(await remaining.inputValue(), "0");
      },
    },
  ],
};
