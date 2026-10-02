module.exports = {
  tests: [
    {
      name: "Profile shows the requested user and only their authored articles",
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
        assert.deepEqual(await page.getByRole("heading", { level: 1 }).allTextContents(), ["bob"]);
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
              { id: 1, title: "Bob's unfavorited article", author: { username: "bob" }, favoritedBy: ["alice"] },
              { id: 2, title: "Alice's shared favorite", author: { username: "alice" }, favoritedBy: ["alice", "bob"] },
              { id: 3, title: "Bob's own favorite", author: { username: "bob" }, favoritedBy: ["bob"] },
              { id: 4, title: "Bobby's favorite", author: { username: "alice" }, favoritedBy: ["bobby"] },
              { id: 5, title: "Nobody's favorite", author: { username: "carol" }, favoritedBy: [] },
            ],
          };
        });
        await page.goto(new URL("/profile/bob/favorites", url).href);
        assert.deepEqual(await page.getByRole("heading", { level: 1 }).allTextContents(), ["bob"]);
        assert.deepEqual(
          (await page.getByRole("heading", { level: 2 }).allTextContents()).sort(),
          ["Alice's shared favorite", "Bob's own favorite"].sort()
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
              { id: 1, title: "My published article", author: { username: "zoë smith" }, favoritedBy: [] },
              { id: 2, title: "My saved article", author: { username: "alice" }, favoritedBy: ["zoë smith"] },
              { id: 3, title: "Alice's saved article", author: { username: "alice" }, favoritedBy: ["alice"] },
            ],
          };
        });
        const profilePath = "/profile/" + encodeURIComponent("zoë smith");
        await page.goto(new URL(profilePath, url).href);
        assert.deepEqual(await page.getByRole("heading", { level: 1 }).allTextContents(), ["zoë smith"]);
        assert.deepEqual(await page.getByRole("heading", { level: 2 }).allTextContents(), ["My published article"]);

        await Promise.all([
          page.waitForURL(new URL(profilePath + "/favorites", url).href, { timeout: 4000 }),
          page.getByRole("link", { name: "Favorites", exact: true }).click({ timeout: 4000 }),
        ]);
        assert.deepEqual(await page.getByRole("heading", { level: 1 }).allTextContents(), ["zoë smith"]);
        assert.deepEqual(await page.getByRole("heading", { level: 2 }).allTextContents(), ["My saved article"]);

        await Promise.all([
          page.waitForURL(new URL(profilePath, url).href, { timeout: 4000 }),
          page.getByRole("link", { name: "My Articles", exact: true }).click({ timeout: 4000 }),
        ]);
        assert.deepEqual(await page.getByRole("heading", { level: 1 }).allTextContents(), ["zoë smith"]);
        assert.deepEqual(await page.getByRole("heading", { level: 2 }).allTextContents(), ["My published article"]);
      },
    },
    {
      name: "A user without authored or favorited articles sees empty lists",
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
          assert.deepEqual(await page.getByRole("heading", { level: 1 }).allTextContents(), ["carol"]);
          assert.deepEqual(await page.getByRole("heading", { level: 2 }).allTextContents(), []);
          assert.equal(await page.getByText("Alice's article", { exact: true }).count(), 0);
          assert.equal(await page.getByText("Bob's article", { exact: true }).count(), 0);
          assert.equal(await page.getByRole("link", { name: "My Articles", exact: true }).isVisible(), true);
          assert.equal(await page.getByRole("link", { name: "Favorites", exact: true }).isVisible(), true);
        }
      },
    },
  ],
};
