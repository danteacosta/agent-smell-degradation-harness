module.exports = {
  tests: [
    {
      name: "Profile shows the requested user and only their authored articles",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = {
            articles: [
              { id: 1, title: "Bob's first article", author: { username: "bob" }, favoritedBy: [] },
              { id: 2, title: "Alice's article", author: { username: "alice" }, favoritedBy: ["bob"] },
              { id: 3, title: "Bob's second article", author: { username: "bob" }, favoritedBy: ["alice"] },
              { id: 4, title: "Bobby's article", author: { username: "bobby" }, favoritedBy: [] },
            ],
          };
        });

        await page.goto(new URL("/profile/bob", url).href);
        assert.equal(await page.locator("h1").innerText(), "bob");
        assert.deepEqual(
          (await page.locator("h2").allTextContents()).sort(),
          ["Bob's first article", "Bob's second article"].sort()
        );
      },
    },
    {
      name: "Favorites shows articles favorited by the requested user regardless of author",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = {
            articles: [
              { id: 1, title: "Alice's shared favorite", author: { username: "alice" }, favoritedBy: ["alice", "bob"] },
              { id: 2, title: "Bob's own favorite", author: { username: "bob" }, favoritedBy: ["bob"] },
              { id: 3, title: "Bob's unfavorited article", author: { username: "bob" }, favoritedBy: [] },
              { id: 4, title: "Only Alice likes this", author: { username: "carol" }, favoritedBy: ["alice"] },
              { id: 5, title: "Only Bobby likes this", author: { username: "carol" }, favoritedBy: ["bobby"] },
            ],
          };
        });

        await page.goto(new URL("/profile/bob/favorites", url).href);
        assert.equal(await page.locator("h1").innerText(), "bob");
        assert.deepEqual(
          (await page.locator("h2").allTextContents()).sort(),
          ["Alice's shared favorite", "Bob's own favorite"].sort()
        );
      },
    },
    {
      name: "Profile links switch article lists while preserving the requested user",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = {
            articles: [
              { id: 1, title: "Carol wrote this", author: { username: "carol" }, favoritedBy: [] },
              { id: 2, title: "Carol likes this", author: { username: "alice" }, favoritedBy: ["carol"] },
              { id: 3, title: "Unrelated article", author: { username: "bob" }, favoritedBy: ["alice"] },
            ],
          };
        });

        await page.goto(new URL("/profile/carol", url).href);
        assert.deepEqual(await page.locator("h2").allTextContents(), ["Carol wrote this"]);

        await Promise.all([
          page.waitForURL(new URL("/profile/carol/favorites", url).href, { timeout: 5000 }),
          page.getByRole("link", { name: "Favorites", exact: true }).click({ timeout: 5000 }),
        ]);
        assert.equal(await page.locator("h1").innerText(), "carol");
        assert.deepEqual(await page.locator("h2").allTextContents(), ["Carol likes this"]);

        await Promise.all([
          page.waitForURL(new URL("/profile/carol", url).href, { timeout: 5000 }),
          page.getByRole("link", { name: "My Articles", exact: true }).click({ timeout: 5000 }),
        ]);
        assert.equal(await page.locator("h1").innerText(), "carol");
        assert.deepEqual(await page.locator("h2").allTextContents(), ["Carol wrote this"]);
      },
    },
    {
      name: "A user with no authored or favorited articles has empty lists",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = {
            articles: [
              { id: 1, title: "Alice's article", author: { username: "alice" }, favoritedBy: ["bob"] },
              { id: 2, title: "Bob's article", author: { username: "bob" }, favoritedBy: ["alice"] },
            ],
          };
        });

        for (const path of ["/profile/dana", "/profile/dana/favorites"]) {
          await page.goto(new URL(path, url).href);
          assert.equal(await page.locator("h1").innerText(), "dana");
          assert.deepEqual(await page.locator("h2").allTextContents(), []);
          assert.equal(await page.getByRole("link", { name: "My Articles", exact: true }).isVisible(), true);
          assert.equal(await page.getByRole("link", { name: "Favorites", exact: true }).isVisible(), true);
        }
      },
    },
  ],
};
