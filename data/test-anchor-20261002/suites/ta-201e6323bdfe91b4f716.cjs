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
        assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "bob");
        assert.deepEqual(
          (await page.getByRole("heading", { level: 2 }).allTextContents()).sort(),
          ["Bob's first article", "Bob's second article"].sort()
        );
      },
    },
    {
      name: "Favorites lists exactly the articles favorited by the requested user",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          localStorage.clear();
          window.initialState = {
            articles: [
              { id: 1, title: "Shared favorite", author: { username: "alice" }, favoritedBy: ["alice", "bob"] },
              { id: 2, title: "Own favorite", author: { username: "bob" }, favoritedBy: ["bob"] },
              { id: 3, title: "Own unfavorited article", author: { username: "bob" }, favoritedBy: [] },
              { id: 4, title: "Someone else's favorite", author: { username: "carol" }, favoritedBy: ["alice", "bobby"] },
            ],
          };
        });

        await page.goto(new URL("/profile/bob/favorites", url).href);
        assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "bob");
        assert.deepEqual(
          (await page.getByRole("heading", { level: 2 }).allTextContents()).sort(),
          ["Shared favorite", "Own favorite"].sort()
        );
      },
    },
    {
      name: "Profile links switch lists while preserving the encoded username",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          localStorage.clear();
          window.initialState = {
            articles: [
              { id: 1, title: "My published article", author: { username: "zoë smith" }, favoritedBy: [] },
              { id: 2, title: "My saved article", author: { username: "alice" }, favoritedBy: ["zoë smith"] },
              { id: 3, title: "Unrelated article", author: { username: "alice" }, favoritedBy: ["alice"] },
            ],
          };
        });

        const profilePath = `/profile/${encodeURIComponent("zoë smith")}`;
        await page.goto(new URL(profilePath, url).href);

        assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "zoë smith");
        assert.deepEqual(
          await page.getByRole("heading", { level: 2 }).allTextContents(),
          ["My published article"]
        );

        await Promise.all([
          page.waitForURL(new URL(`${profilePath}/favorites`, url).href, { timeout: 5000 }),
          page.getByRole("link", { name: "Favorites", exact: true }).click({ timeout: 5000 }),
        ]);
        assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "zoë smith");
        assert.deepEqual(
          await page.getByRole("heading", { level: 2 }).allTextContents(),
          ["My saved article"]
        );

        await Promise.all([
          page.waitForURL(new URL(profilePath, url).href, { timeout: 5000 }),
          page.getByRole("link", { name: "My Articles", exact: true }).click({ timeout: 5000 }),
        ]);
        assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "zoë smith");
        assert.deepEqual(
          await page.getByRole("heading", { level: 2 }).allTextContents(),
          ["My published article"]
        );
      },
    },
    {
      name: "A user with no authored articles or favorites sees empty lists",
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
          assert.equal(await page.getByRole("heading", { level: 2 }).count(), 0);
          assert.equal(await page.getByRole("link", { name: "My Articles", exact: true }).isVisible(), true);
          assert.equal(await page.getByRole("link", { name: "Favorites", exact: true }).isVisible(), true);
        }
      },
    },
  ],
};
