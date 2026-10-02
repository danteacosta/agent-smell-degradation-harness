module.exports = {
  tests: [
    {
      name: "Profile shows username and only articles authored by that user",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = {
            articles: [
              { id: 1, title: "Alice's first article", author: { username: "alice" }, favoritedBy: [] },
              { id: 2, title: "Bob's article", author: { username: "bob" }, favoritedBy: ["alice"] },
              { id: 3, title: "Alice's second article", author: { username: "alice" }, favoritedBy: ["bob"] },
              { id: 4, title: "Similar username", author: { username: "alice2" }, favoritedBy: [] },
            ],
          };
        });
        await page.goto(new URL("/profile/alice", url).href);
        assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "alice");
        assert.deepEqual(
          (await page.getByRole("heading", { level: 2 }).allTextContents()).sort(),
          ["Alice's first article", "Alice's second article"].sort()
        );
      },
    },
    {
      name: "Profile identity and authored articles follow the requested username",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = {
            articles: [
              { id: 1, title: "Alice's article", author: { username: "alice" }, favoritedBy: ["bob"] },
              { id: 2, title: "Bob's first article", author: { username: "bob" }, favoritedBy: [] },
              { id: 3, title: "Bob's second article", author: { username: "bob" }, favoritedBy: ["alice"] },
            ],
          };
        });
        await page.goto(new URL("/profile/bob", url).href);
        assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "bob");
        assert.deepEqual(
          (await page.getByRole("heading", { level: 2 }).allTextContents()).sort(),
          ["Bob's first article", "Bob's second article"].sort()
        );
      },
    },
    {
      name: "Favorites route shows the user's favorites regardless of author",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = {
            articles: [
              { id: 1, title: "Own favorite", author: { username: "alice" }, favoritedBy: ["alice"] },
              { id: 2, title: "Another author's favorite", author: { username: "bob" }, favoritedBy: ["bob", "alice"] },
              { id: 3, title: "Own unfavorited article", author: { username: "alice" }, favoritedBy: [] },
              { id: 4, title: "Someone else's favorite", author: { username: "carol" }, favoritedBy: ["alice2"] },
            ],
          };
        });
        await page.goto(new URL("/profile/alice/favorites", url).href);
        assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "alice");
        assert.deepEqual(
          (await page.getByRole("heading", { level: 2 }).allTextContents()).sort(),
          ["Own favorite", "Another author's favorite"].sort()
        );
      },
    },
    {
      name: "Profile tabs preserve the requested user and replace the article list",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = {
            articles: [
              { id: 1, title: "Written by Bob", author: { username: "bob" }, favoritedBy: [] },
              { id: 2, title: "Saved by Bob", author: { username: "carol" }, favoritedBy: ["bob"] },
              { id: 3, title: "Alice only", author: { username: "alice" }, favoritedBy: ["alice"] },
            ],
          };
        });
        await page.goto(new URL("/profile/bob", url).href);
        await Promise.all([
          page.waitForURL("**/profile/*/favorites", { timeout: 4000 }),
          page.getByRole("link", { name: "Favorites", exact: true }).click({ timeout: 4000 }),
        ]);
        assert.equal(new URL(page.url()).pathname, "/profile/bob/favorites");
        assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "bob");
        assert.deepEqual(await page.getByRole("heading", { level: 2 }).allTextContents(), ["Saved by Bob"]);

        await Promise.all([
          page.waitForURL("**/profile/bob", { timeout: 4000 }),
          page.getByRole("link", { name: "My Articles", exact: true }).click({ timeout: 4000 }),
        ]);
        assert.equal(new URL(page.url()).pathname, "/profile/bob");
        assert.deepEqual(await page.getByRole("heading", { level: 2 }).allTextContents(), ["Written by Bob"]);
      },
    },
    {
      name: "A profile with no matching articles does not show another user's articles",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = {
            articles: [
              { id: 1, title: "Bob's article", author: { username: "bob" }, favoritedBy: ["bob"] },
            ],
          };
        });
        await page.goto(new URL("/profile/alice", url).href);
        assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "alice");
        assert.deepEqual(await page.getByRole("heading", { level: 2 }).allTextContents(), []);

        await page.goto(new URL("/profile/alice/favorites", url).href);
        assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "alice");
        assert.deepEqual(await page.getByRole("heading", { level: 2 }).allTextContents(), []);
      },
    },
  ],
};
