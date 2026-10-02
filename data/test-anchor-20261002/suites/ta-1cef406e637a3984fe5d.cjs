module.exports = {
  tests: [
    {
      name: "Profile shows username and only authored articles",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          localStorage.clear();
          window.initialState = {
            articles: [
              { id: 1, title: "Alice first", author: { username: "alice" }, favoritedBy: [] },
              { id: 2, title: "Bob favorite", author: { username: "bob" }, favoritedBy: ["alice"] },
              { id: 3, title: "Alice second", author: { username: "alice" }, favoritedBy: ["bob"] },
              { id: 4, title: "Unrelated", author: { username: "carol" }, favoritedBy: [] },
            ],
          };
        });
        await page.goto(new URL("/profile/alice", url).href);
        assert.equal((await page.locator("#profile-name").innerText()).trim(), "alice");
        assert.deepEqual(
          (await page.locator("#articles .article h2").allTextContents()).sort(),
          ["Alice first", "Alice second"]
        );
      },
    },
    {
      name: "Favorites includes exactly articles favorited by the profile user",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          localStorage.clear();
          window.initialState = {
            articles: [
              { id: 1, title: "Own favorite", author: { username: "alice" }, favoritedBy: ["alice"] },
              { id: 2, title: "Shared favorite", author: { username: "bob" }, favoritedBy: ["carol", "alice"] },
              { id: 3, title: "Own nonfavorite", author: { username: "alice" }, favoritedBy: ["bob"] },
              { id: 4, title: "Someone else's favorite", author: { username: "carol" }, favoritedBy: ["bob"] },
              { id: 5, title: "Nobody's favorite", author: { username: "bob" }, favoritedBy: [] },
            ],
          };
        });
        await page.goto(new URL("/profile/alice/favorites", url).href);
        assert.equal((await page.locator("#profile-name").innerText()).trim(), "alice");
        assert.deepEqual(
          (await page.locator("#articles .article h2").allTextContents()).sort(),
          ["Own favorite", "Shared favorite"]
        );
      },
    },
    {
      name: "Profile links switch lists without retaining stale articles",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          localStorage.clear();
          window.initialState = {
            articles: [
              { id: 1, title: "Authored only", author: { username: "alice" }, favoritedBy: [] },
              { id: 2, title: "Favorite only", author: { username: "bob" }, favoritedBy: ["alice"] },
              { id: 3, title: "Both", author: { username: "alice" }, favoritedBy: ["alice"] },
            ],
          };
        });
        await page.goto(new URL("/profile/alice", url).href);
        assert.deepEqual(
          (await page.locator("#articles .article h2").allTextContents()).sort(),
          ["Authored only", "Both"]
        );

        await page.getByRole("link", { name: "Favorites", exact: true }).click({ timeout: 3000 });
        await page.waitForURL(new URL("/profile/alice/favorites", url).href, { timeout: 3000 });
        assert.deepEqual(
          (await page.locator("#articles .article h2").allTextContents()).sort(),
          ["Both", "Favorite only"]
        );

        await page.reload();
        assert.deepEqual(
          (await page.locator("#articles .article h2").allTextContents()).sort(),
          ["Both", "Favorite only"]
        );

        await page.getByRole("link", { name: "My Articles", exact: true }).click({ timeout: 3000 });
        await page.waitForURL(new URL("/profile/alice", url).href, { timeout: 3000 });
        assert.deepEqual(
          (await page.locator("#articles .article h2").allTextContents()).sort(),
          ["Authored only", "Both"]
        );
      },
    },
    {
      name: "No matching articles produces empty authored and favorites lists",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          localStorage.clear();
          window.initialState = {
            articles: [
              { id: 1, title: "Bob's article", author: { username: "bob" }, favoritedBy: ["carol"] },
              { id: 2, title: "Carol's article", author: { username: "carol" }, favoritedBy: [] },
            ],
          };
        });
        for (const path of ["/profile/alice", "/profile/alice/favorites"]) {
          await page.goto(new URL(path, url).href);
          assert.equal((await page.locator("#profile-name").innerText()).trim(), "alice");
          assert.equal(await page.locator("#articles .article").count(), 0);
        }
      },
    },
    {
      name: "Article lists follow the username in the requested route",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          localStorage.clear();
          window.initialState = {
            articles: [
              { id: 1, title: "Alice article", author: { username: "alice" }, favoritedBy: ["bob"] },
              { id: 2, title: "Bob article", author: { username: "bob" }, favoritedBy: ["alice"] },
              { id: 3, title: "Bobby article", author: { username: "bobby" }, favoritedBy: ["bobby"] },
              { id: 4, title: "Bob shared favorite", author: { username: "carol" }, favoritedBy: ["alice", "bob"] },
            ],
          };
        });
        await page.goto(new URL("/profile/bob", url).href);
        assert.deepEqual(
          await page.locator("#articles .article h2").allTextContents(),
          ["Bob article"]
        );

        await page.goto(new URL("/profile/bob/favorites", url).href);
        assert.deepEqual(
          (await page.locator("#articles .article h2").allTextContents()).sort(),
          ["Alice article", "Bob shared favorite"]
        );
      },
    },
  ],
};
