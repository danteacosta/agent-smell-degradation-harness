module.exports = {
  tests: [
    {
      name: "Profile shows the user's name and authored articles",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = {
            articles: [
              { id: 1, title: "Alice authored", author: { username: "alice" }, favoritedBy: [] },
              { id: 2, title: "Alice authored and favorited", author: { username: "alice" }, favoritedBy: ["alice"] },
              { id: 3, title: "Bob authored, Alice favorited", author: { username: "bob" }, favoritedBy: ["alice"] },
              { id: 4, title: "Unrelated article", author: { username: "carol" }, favoritedBy: [] },
            ],
          };
        });
        await page.goto(`${url.replace(/\/$/, "")}/profile/alice`);
        assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "alice");
        assert.deepEqual(
          (await page.getByRole("heading", { level: 2 }).allTextContents()).sort(),
          ["Alice authored", "Alice authored and favorited"].sort()
        );

        await page.getByRole("link", { name: "Favorites", exact: true }).click();
        await page.waitForURL("**/profile/alice/favorites", { timeout: 3000 });
        assert.deepEqual(
          (await page.getByRole("heading", { level: 2 }).allTextContents()).sort(),
          ["Alice authored and favorited", "Bob authored, Alice favorited"].sort()
        );

        await page.getByRole("link", { name: "My Articles", exact: true }).click();
        await page.waitForURL("**/profile/alice", { timeout: 3000 });
        assert.deepEqual(
          (await page.getByRole("heading", { level: 2 }).allTextContents()).sort(),
          ["Alice authored", "Alice authored and favorited"].sort()
        );
      },
    },
    {
      name: "Favorites direct route shows only articles favorited by that user",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = {
            articles: [
              { id: 1, title: "Own favorite", author: { username: "bob" }, favoritedBy: ["bob"] },
              { id: 2, title: "Shared favorite", author: { username: "alice" }, favoritedBy: ["alice", "bob"] },
              { id: 3, title: "Bob authored only", author: { username: "bob" }, favoritedBy: ["alice"] },
              { id: 4, title: "Alice favorite only", author: { username: "carol" }, favoritedBy: ["alice"] },
              { id: 5, title: "Nobody's favorite", author: { username: "carol" }, favoritedBy: [] },
            ],
          };
        });
        await page.goto(`${url.replace(/\/$/, "")}/profile/bob/favorites`);
        assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "bob");
        const expected = ["Own favorite", "Shared favorite"].sort();
        assert.deepEqual(
          (await page.getByRole("heading", { level: 2 }).allTextContents()).sort(),
          expected
        );

        await page.reload();
        assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "bob");
        assert.deepEqual(
          (await page.getByRole("heading", { level: 2 }).allTextContents()).sort(),
          expected
        );
      },
    },
    {
      name: "Profile tabs preserve the viewed username",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = {
            articles: [
              { id: 1, title: "Bob's writing", author: { username: "bob" }, favoritedBy: [] },
              { id: 2, title: "Bob's favorite", author: { username: "carol" }, favoritedBy: ["bob"] },
              { id: 3, title: "Alice's writing", author: { username: "alice" }, favoritedBy: ["alice"] },
            ],
          };
        });
        await page.goto(`${url.replace(/\/$/, "")}/profile/bob`);
        assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "bob");
        assert.deepEqual(
          await page.getByRole("heading", { level: 2 }).allTextContents(),
          ["Bob's writing"]
        );

        await page.getByRole("link", { name: "Favorites", exact: true }).click();
        await page.waitForURL("**/profile/bob/favorites", { timeout: 3000 });
        assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "bob");
        assert.deepEqual(
          await page.getByRole("heading", { level: 2 }).allTextContents(),
          ["Bob's favorite"]
        );

        await page.getByRole("link", { name: "My Articles", exact: true }).click();
        await page.waitForURL("**/profile/bob", { timeout: 3000 });
        assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "bob");
        assert.deepEqual(
          await page.getByRole("heading", { level: 2 }).allTextContents(),
          ["Bob's writing"]
        );
      },
    },
    {
      name: "Empty authored and favorite lists do not show other users' articles",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = {
            articles: [
              { id: 1, title: "Alice's article", author: { username: "alice" }, favoritedBy: ["alice"] },
              { id: 2, title: "Bob's article", author: { username: "bob" }, favoritedBy: ["bob"] },
            ],
          };
        });
        const base = url.replace(/\/$/, "");
        await page.goto(`${base}/profile/carol`);
        assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "carol");
        assert.deepEqual(await page.getByRole("heading", { level: 2 }).allTextContents(), []);

        await page.goto(`${base}/profile/carol/favorites`);
        assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "carol");
        assert.deepEqual(await page.getByRole("heading", { level: 2 }).allTextContents(), []);
      },
    },
  ],
};
