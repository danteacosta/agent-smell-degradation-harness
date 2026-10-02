module.exports = {
  tests: [
    {
      name: "Profile shows the username and only their authored articles",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = {
            articles: [
              { id: 1, title: "Alice's first article", author: { username: "alice" }, favoritedBy: [] },
              { id: 2, title: "Alice's second article", author: { username: "alice" }, favoritedBy: ["bob"] },
              { id: 3, title: "Bob's article", author: { username: "bob" }, favoritedBy: ["alice"] },
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
      name: "Favorites lists articles favorited by the profile user regardless of author",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = {
            articles: [
              { id: 1, title: "Favorite by Bob", author: { username: "bob" }, favoritedBy: ["bob", "alice"] },
              { id: 2, title: "Own favorite", author: { username: "alice" }, favoritedBy: ["alice"] },
              { id: 3, title: "Own unfavorited article", author: { username: "alice" }, favoritedBy: [] },
              { id: 4, title: "Someone else's favorite", author: { username: "carol" }, favoritedBy: ["bob"] },
              { id: 5, title: "Similar user's favorite", author: { username: "bob" }, favoritedBy: ["alice2"] },
            ],
          };
        });

        await page.goto(new URL("/profile/alice/favorites", url).href);
        assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "alice");
        assert.deepEqual(
          (await page.getByRole("heading", { level: 2 }).allTextContents()).sort(),
          ["Favorite by Bob", "Own favorite"].sort()
        );
      },
    },
    {
      name: "Profile navigation preserves an encoded username and switches article lists",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = {
            articles: [
              { id: 1, title: "Renée's article", author: { username: "renée" }, favoritedBy: [] },
              { id: 2, title: "Renée's favorite", author: { username: "bob" }, favoritedBy: ["renée"] },
              { id: 3, title: "Alice's article", author: { username: "alice" }, favoritedBy: ["alice"] },
            ],
          };
        });

        await page.goto(new URL("/profile/ren%C3%A9e", url).href);
        assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "renée");
        assert.deepEqual(
          await page.getByRole("heading", { level: 2 }).allTextContents(),
          ["Renée's article"]
        );

        await Promise.all([
          page.waitForURL("**/profile/ren%C3%A9e/favorites", { timeout: 5000 }),
          page.getByRole("link", { name: "Favorites", exact: true }).click({ timeout: 5000 }),
        ]);
        assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "renée");
        assert.deepEqual(
          await page.getByRole("heading", { level: 2 }).allTextContents(),
          ["Renée's favorite"]
        );

        await Promise.all([
          page.waitForURL("**/profile/ren%C3%A9e", { timeout: 5000 }),
          page.getByRole("link", { name: "My Articles", exact: true }).click({ timeout: 5000 }),
        ]);
        assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "renée");
        assert.deepEqual(
          await page.getByRole("heading", { level: 2 }).allTextContents(),
          ["Renée's article"]
        );
      },
    },
    {
      name: "A user with no authored or favorite articles sees empty lists",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
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
          assert.deepEqual(
            await page.getByRole("heading", { level: 2 }).allTextContents(),
            []
          );
          assert.equal(await page.getByRole("link", { name: "My Articles", exact: true }).isVisible(), true);
          assert.equal(await page.getByRole("link", { name: "Favorites", exact: true }).isVisible(), true);
        }
      },
    },
  ],
};
