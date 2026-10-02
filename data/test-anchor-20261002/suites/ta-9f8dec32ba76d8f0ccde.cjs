module.exports = {
  tests: [
    {
      name: "Profile shows Alice and only her authored articles",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          localStorage.clear();
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
        assert.equal((await page.locator("#profile-name").innerText()).trim(), "alice");
        assert.deepEqual(
          (await page.locator("#articles .article h2").allTextContents()).sort(),
          ["Alice's first article", "Alice's second article"].sort()
        );
      },
    },
    {
      name: "Favorites route shows articles Alice favorited regardless of author",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          localStorage.clear();
          window.initialState = {
            articles: [
              { id: 1, title: "Own favorite", author: { username: "alice" }, favoritedBy: ["alice"] },
              { id: 2, title: "Shared favorite", author: { username: "bob" }, favoritedBy: ["bob", "alice"] },
              { id: 3, title: "Own unfavorited article", author: { username: "alice" }, favoritedBy: [] },
              { id: 4, title: "Someone else's favorite", author: { username: "carol" }, favoritedBy: ["bob"] },
              { id: 5, title: "Similar username favorite", author: { username: "bob" }, favoritedBy: ["alice2"] },
            ],
          };
        });
        await page.goto(new URL("/profile/alice/favorites", url).href);
        assert.equal((await page.locator("#profile-name").innerText()).trim(), "alice");
        assert.deepEqual(
          (await page.locator("#articles .article h2").allTextContents()).sort(),
          ["Own favorite", "Shared favorite"].sort()
        );
      },
    },
    {
      name: "Profile tabs switch routes and replace the article list",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          localStorage.clear();
          window.initialState = {
            articles: [
              { id: 1, title: "Authored only", author: { username: "alice" }, favoritedBy: [] },
              { id: 2, title: "Favorite only", author: { username: "bob" }, favoritedBy: ["alice"] },
              { id: 3, title: "Authored and favorite", author: { username: "alice" }, favoritedBy: ["alice"] },
            ],
          };
        });
        await page.goto(new URL("/profile/alice", url).href);

        await page.getByRole("link", { name: "Favorites", exact: true }).click({ timeout: 3000 });
        await page.waitForURL(
          target => target.pathname === "/profile/alice/favorites",
          { timeout: 3000 }
        );
        assert.deepEqual(
          (await page.locator("#articles .article h2").allTextContents()).sort(),
          ["Favorite only", "Authored and favorite"].sort()
        );

        await page.getByRole("link", { name: "My Articles", exact: true }).click({ timeout: 3000 });
        await page.waitForURL(
          target => target.pathname === "/profile/alice",
          { timeout: 3000 }
        );
        assert.deepEqual(
          (await page.locator("#articles .article h2").allTextContents()).sort(),
          ["Authored only", "Authored and favorite"].sort()
        );
        assert.equal((await page.locator("#profile-name").innerText()).trim(), "alice");
      },
    },
    {
      name: "Empty favorites do not retain authored articles",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          localStorage.clear();
          window.initialState = {
            articles: [
              { id: 1, title: "Alice's article", author: { username: "alice" }, favoritedBy: ["bob"] },
              { id: 2, title: "Bob's article", author: { username: "bob" }, favoritedBy: [] },
            ],
          };
        });
        await page.goto(new URL("/profile/alice", url).href);
        assert.deepEqual(
          await page.locator("#articles .article h2").allTextContents(),
          ["Alice's article"]
        );
        await page.getByRole("link", { name: "Favorites", exact: true }).click({ timeout: 3000 });
        await page.waitForURL(
          target => target.pathname === "/profile/alice/favorites",
          { timeout: 3000 }
        );
        assert.equal(await page.locator("#articles .article").count(), 0);
        assert.equal((await page.locator("#profile-name").innerText()).trim(), "alice");
      },
    },
    {
      name: "A profile with no authored articles can still have favorites",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          localStorage.clear();
          window.initialState = {
            articles: [
              { id: 1, title: "Alice's favorite", author: { username: "bob" }, favoritedBy: ["alice"] },
              { id: 2, title: "Unrelated article", author: { username: "carol" }, favoritedBy: [] },
            ],
          };
        });
        await page.goto(new URL("/profile/alice/favorites", url).href);
        assert.deepEqual(
          await page.locator("#articles .article h2").allTextContents(),
          ["Alice's favorite"]
        );
        await page.getByRole("link", { name: "My Articles", exact: true }).click({ timeout: 3000 });
        await page.waitForURL(
          target => target.pathname === "/profile/alice",
          { timeout: 3000 }
        );
        assert.equal(await page.locator("#articles .article").count(), 0);
        assert.equal((await page.locator("#profile-name").innerText()).trim(), "alice");
      },
    },
  ],
};
