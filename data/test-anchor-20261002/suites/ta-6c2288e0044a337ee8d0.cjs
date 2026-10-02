module.exports = {
  tests: [
    {
      name: "Profile shows the user and only their authored articles",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = {
            articles: [
              { id: 1, title: "Alice first", author: { username: "alice" }, favoritedBy: [] },
              { id: 2, title: "Bob article", author: { username: "bob" }, favoritedBy: ["alice"] },
              { id: 3, title: "Alice second", author: { username: "alice" }, favoritedBy: ["bob"] },
            ],
          };
        });
        await page.goto(new URL("/profile/alice", url).href);
        assert.equal(await page.locator("h1").innerText(), "alice");
        assert.deepEqual(await page.locator("h2").allTextContents(), ["Alice first", "Alice second"]);
      },
    },
    {
      name: "Favorites include articles favorited by the profile user regardless of author",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = {
            articles: [
              { id: 1, title: "Own favorite", author: { username: "alice" }, favoritedBy: ["alice"] },
              { id: 2, title: "Shared favorite", author: { username: "bob" }, favoritedBy: ["bob", "alice"] },
              { id: 3, title: "Own nonfavorite", author: { username: "alice" }, favoritedBy: ["bob"] },
              { id: 4, title: "Nobody favors this", author: { username: "bob" }, favoritedBy: [] },
            ],
          };
        });
        await page.goto(new URL("/profile/alice/favorites", url).href);
        assert.equal(await page.locator("h1").innerText(), "alice");
        assert.deepEqual(await page.locator("h2").allTextContents(), ["Own favorite", "Shared favorite"]);
        await page.reload();
        assert.deepEqual(await page.locator("h2").allTextContents(), ["Own favorite", "Shared favorite"]);
      },
    },
    {
      name: "Direct routes select the requested username exactly",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = {
            articles: [
              { id: 1, title: "Bob authored", author: { username: "bob" }, favoritedBy: ["alice"] },
              { id: 2, title: "Bob favorite", author: { username: "alice" }, favoritedBy: ["bob"] },
              { id: 3, title: "Bobby only", author: { username: "bobby" }, favoritedBy: ["bobby"] },
            ],
          };
        });
        await page.goto(new URL("/profile/bob", url).href);
        assert.equal(await page.locator("h1").innerText(), "bob");
        assert.deepEqual(await page.locator("h2").allTextContents(), ["Bob authored"]);

        await page.goto(new URL("/profile/bob/favorites", url).href);
        assert.equal(await page.locator("h1").innerText(), "bob");
        assert.deepEqual(await page.locator("h2").allTextContents(), ["Bob favorite"]);
      },
    },
    {
      name: "Profiles without matching articles show neither other users' articles nor favorites",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = {
            articles: [
              { id: 1, title: "Alice article", author: { username: "alice" }, favoritedBy: ["alice"] },
            ],
          };
        });
        for (const path of ["/profile/carol", "/profile/carol/favorites"]) {
          await page.goto(new URL(path, url).href);
          assert.equal(await page.locator("h1").innerText(), "carol");
          assert.deepEqual(await page.locator("h2").allTextContents(), []);
          assert.equal(await page.getByText("Alice article", { exact: true }).count(), 0);
        }
      },
    },
    {
      name: "Profile navigation switches lists while retaining the current user",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = {
            articles: [
              { id: 1, title: "Bob authored", author: { username: "bob" }, favoritedBy: [] },
              { id: 2, title: "Bob favorite", author: { username: "alice" }, favoritedBy: ["bob"] },
            ],
          };
        });
        await page.goto(new URL("/profile/bob", url).href);
        await page.getByRole("link", { name: "Favorites", exact: true }).click({ timeout: 3000 });
        await page.waitForLoadState("load");
        assert.equal(new URL(page.url()).pathname, "/profile/bob/favorites");
        assert.equal(await page.locator("h1").innerText(), "bob");
        assert.deepEqual(await page.locator("h2").allTextContents(), ["Bob favorite"]);

        await page.getByRole("link", { name: "My Articles", exact: true }).click({ timeout: 3000 });
        await page.waitForLoadState("load");
        assert.equal(new URL(page.url()).pathname, "/profile/bob");
        assert.equal(await page.locator("h1").innerText(), "bob");
        assert.deepEqual(await page.locator("h2").allTextContents(), ["Bob authored"]);
      },
    },
  ],
};
