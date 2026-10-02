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
              { id: 4, title: "Anonymous article", favoritedBy: [] },
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
      name: "Favorites lists articles favorited by the profile user",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = {
            articles: [
              { id: 1, title: "Alice's favorite", author: { username: "bob" }, favoritedBy: ["alice"] },
              { id: 2, title: "Shared favorite", author: { username: "carol" }, favoritedBy: ["bob", "alice"] },
              { id: 3, title: "Alice's unfavorited article", author: { username: "alice" }, favoritedBy: [] },
              { id: 4, title: "Bob's favorite", author: { username: "carol" }, favoritedBy: ["bob"] },
              { id: 5, title: "No favorites recorded", author: { username: "alice" } },
            ],
          };
        });
        await page.goto(new URL("/profile/alice/favorites", url).href);
        assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "alice");
        assert.deepEqual(
          (await page.getByRole("heading", { level: 2 }).allTextContents()).sort(),
          ["Alice's favorite", "Shared favorite"].sort()
        );
      },
    },
    {
      name: "Profile tabs preserve the user and survive reload",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = {
            articles: [
              { id: 1, title: "Bob wrote this", author: { username: "bob" }, favoritedBy: [] },
              { id: 2, title: "Bob likes this", author: { username: "alice" }, favoritedBy: ["bob"] },
              { id: 3, title: "Alice likes this", author: { username: "carol" }, favoritedBy: ["alice"] },
            ],
          };
        });
        await page.goto(new URL("/profile/bob", url).href);
        await Promise.all([
          page.waitForURL(new URL("/profile/bob/favorites", url).href, { timeout: 5000 }),
          page.getByRole("link", { name: "Favorites", exact: true }).click({ timeout: 5000 }),
        ]);
        assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "bob");
        assert.deepEqual(await page.getByRole("heading", { level: 2 }).allTextContents(), ["Bob likes this"]);

        await page.reload();
        assert.deepEqual(await page.getByRole("heading", { level: 2 }).allTextContents(), ["Bob likes this"]);

        await Promise.all([
          page.waitForURL(new URL("/profile/bob", url).href, { timeout: 5000 }),
          page.getByRole("link", { name: "My Articles", exact: true }).click({ timeout: 5000 }),
        ]);
        assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "bob");
        assert.deepEqual(await page.getByRole("heading", { level: 2 }).allTextContents(), ["Bob wrote this"]);
      },
    },
    {
      name: "Profiles without matching articles do not show other users' articles",
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
          assert.deepEqual(await page.getByRole("heading", { level: 2 }).allTextContents(), []);
          assert.equal(await page.getByRole("link", { name: "My Articles", exact: true }).isVisible(), true);
          assert.equal(await page.getByRole("link", { name: "Favorites", exact: true }).isVisible(), true);
        }
      },
    },
    {
      name: "Encoded usernames display correctly and retain their profile when switching tabs",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = {
            articles: [
              { id: 1, title: "Renée's article", author: { username: "renée" }, favoritedBy: [] },
              { id: 2, title: "Renée's favorite", author: { username: "alice" }, favoritedBy: ["renée"] },
              { id: 3, title: "Another user's article", author: { username: "renee" }, favoritedBy: ["renee"] },
            ],
          };
        });
        const profilePath = "/profile/" + encodeURIComponent("renée");
        await page.goto(new URL(profilePath, url).href);
        assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "renée");
        assert.deepEqual(await page.getByRole("heading", { level: 2 }).allTextContents(), ["Renée's article"]);

        await Promise.all([
          page.waitForURL(new URL(profilePath + "/favorites", url).href, { timeout: 5000 }),
          page.getByRole("link", { name: "Favorites", exact: true }).click({ timeout: 5000 }),
        ]);
        assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "renée");
        assert.deepEqual(await page.getByRole("heading", { level: 2 }).allTextContents(), ["Renée's favorite"]);
      },
    },
  ],
};
