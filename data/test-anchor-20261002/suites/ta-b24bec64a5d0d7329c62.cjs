module.exports = {
  tests: [
    {
      name: "Profile shows the user's name and only their authored articles",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          localStorage.clear();
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
      name: "Favorites lists articles favorited by the profile user regardless of author",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          localStorage.clear();
          window.initialState = {
            articles: [
              { id: 1, title: "Bob's own favorite", author: { username: "bob" }, favoritedBy: ["bob"] },
              { id: 2, title: "Shared favorite", author: { username: "alice" }, favoritedBy: ["alice", "bob"] },
              { id: 3, title: "Bob's unfavorited article", author: { username: "bob" }, favoritedBy: [] },
              { id: 4, title: "Someone else's favorite", author: { username: "alice" }, favoritedBy: ["bobby"] },
            ],
          };
        });

        await page.goto(new URL("/profile/bob/favorites", url).href);
        assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "bob");
        assert.deepEqual(
          (await page.getByRole("heading", { level: 2 }).allTextContents()).sort(),
          ["Bob's own favorite", "Shared favorite"].sort()
        );
      },
    },
    {
      name: "Profile tabs preserve an encoded username and switch article lists",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          localStorage.clear();
          window.initialState = {
            articles: [
              { id: 1, title: "My published article", author: { username: "mary jane" }, favoritedBy: [] },
              { id: 2, title: "My saved article", author: { username: "alice" }, favoritedBy: ["mary jane"] },
              { id: 3, title: "Unrelated article", author: { username: "alice" }, favoritedBy: ["alice"] },
            ],
          };
        });

        const authoredUrl = new URL("/profile/mary%20jane", url).href;
        const favoritesUrl = new URL("/profile/mary%20jane/favorites", url).href;

        await page.goto(authoredUrl);
        assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "mary jane");
        assert.deepEqual(
          await page.getByRole("heading", { level: 2 }).allTextContents(),
          ["My published article"]
        );

        await Promise.all([
          page.waitForURL(favoritesUrl, { timeout: 5000 }),
          page.getByRole("link", { name: "Favorites", exact: true }).click({ timeout: 5000 }),
        ]);
        assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "mary jane");
        assert.deepEqual(
          await page.getByRole("heading", { level: 2 }).allTextContents(),
          ["My saved article"]
        );

        await Promise.all([
          page.waitForURL(authoredUrl, { timeout: 5000 }),
          page.getByRole("link", { name: "My Articles", exact: true }).click({ timeout: 5000 }),
        ]);
        assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "mary jane");
        assert.deepEqual(
          await page.getByRole("heading", { level: 2 }).allTextContents(),
          ["My published article"]
        );
      },
    },
    {
      name: "Profiles with no matching articles show no unrelated articles on either tab",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          localStorage.clear();
          window.initialState = {
            articles: [
              { id: 1, title: "Alice's article", author: { username: "alice" }, favoritedBy: ["bob"] },
              { id: 2, title: "Bob's article", author: { username: "bob" }, favoritedBy: ["alice"] },
            ],
          };
        });

        for (const path of ["/profile/carol", "/profile/carol/favorites"]) {
          await page.goto(new URL(path, url).href);
          assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "carol");
          assert.deepEqual(await page.getByRole("heading", { level: 2 }).allTextContents(), []);
          assert.equal(await page.getByRole("link", { name: "My Articles", exact: true }).isVisible(), true);
          assert.equal(await page.getByRole("link", { name: "Favorites", exact: true }).isVisible(), true);
        }
      },
    },
  ],
};
