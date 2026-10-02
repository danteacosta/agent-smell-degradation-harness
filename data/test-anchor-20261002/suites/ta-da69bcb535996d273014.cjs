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
        assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "bob");
        assert.deepEqual(
          (await page.getByRole("heading", { level: 2 }).allTextContents()).sort(),
          ["Bob's first article", "Bob's second article"].sort()
        );
      },
    },
    {
      name: "Direct favorites route shows articles favorited by the profile user",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = {
            articles: [
              { id: 1, title: "Favorite from Alice", author: { username: "alice" }, favoritedBy: ["bob"] },
              { id: 2, title: "Bob's own favorite", author: { username: "bob" }, favoritedBy: ["alice", "bob"] },
              { id: 3, title: "Bob's unfavorited article", author: { username: "bob" }, favoritedBy: [] },
              { id: 4, title: "Someone else's favorite", author: { username: "carol" }, favoritedBy: ["bobby", "alice"] },
            ],
          };
        });
        await page.goto(new URL("/profile/bob/favorites", url).href);
        assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "bob");
        assert.deepEqual(
          (await page.getByRole("heading", { level: 2 }).allTextContents()).sort(),
          ["Favorite from Alice", "Bob's own favorite"].sort()
        );
      },
    },
    {
      name: "Profile navigation switches lists while preserving the username",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = {
            articles: [
              { id: 1, title: "Carol authored this", author: { username: "carol" }, favoritedBy: [] },
              { id: 2, title: "Carol favorited this", author: { username: "alice" }, favoritedBy: ["carol"] },
            ],
          };
        });
        await page.goto(new URL("/profile/carol", url).href);
        assert.deepEqual(await page.getByRole("heading", { level: 2 }).allTextContents(), ["Carol authored this"]);

        await Promise.all([
          page.waitForURL(new URL("/profile/carol/favorites", url).href, { timeout: 5000 }),
          page.getByRole("link", { name: "Favorites", exact: true }).click({ timeout: 5000 }),
        ]);
        assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "carol");
        assert.deepEqual(await page.getByRole("heading", { level: 2 }).allTextContents(), ["Carol favorited this"]);

        await Promise.all([
          page.waitForURL(new URL("/profile/carol", url).href, { timeout: 5000 }),
          page.getByRole("link", { name: "My Articles", exact: true }).click({ timeout: 5000 }),
        ]);
        assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "carol");
        assert.deepEqual(await page.getByRole("heading", { level: 2 }).allTextContents(), ["Carol authored this"]);
      },
    },
    {
      name: "Profiles with no matching articles keep both lists empty",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = {
            articles: [
              { id: 1, title: "Alice's article", author: { username: "alice" }, favoritedBy: ["bob"] },
            ],
          };
        });
        for (const path of ["/profile/dana", "/profile/dana/favorites"]) {
          await page.goto(new URL(path, url).href);
          assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "dana");
          assert.deepEqual(await page.getByRole("heading", { level: 2 }).allTextContents(), []);
          assert.equal(await page.getByRole("link", { name: "My Articles", exact: true }).isVisible(), true);
          assert.equal(await page.getByRole("link", { name: "Favorites", exact: true }).isVisible(), true);
        }
      },
    },
  ],
};
