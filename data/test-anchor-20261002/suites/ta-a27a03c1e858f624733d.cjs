module.exports = {
  tests: [
    {
      name: "Profile shows the user and only their authored articles",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
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
        assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "alice");
        assert.deepEqual(
          (await page.getByRole("heading", { level: 2 }).allTextContents()).sort(),
          ["Alice first", "Alice second"]
        );
      },
    },
    {
      name: "Favorites includes all favorited articles regardless of author",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = {
            articles: [
              { id: 1, title: "Own favorite", author: { username: "alice" }, favoritedBy: ["alice"] },
              { id: 2, title: "Shared favorite", author: { username: "bob" }, favoritedBy: ["carol", "alice"] },
              { id: 3, title: "Own unfavorited", author: { username: "alice" }, favoritedBy: ["bob"] },
              { id: 4, title: "Nobody favorite", author: { username: "carol" }, favoritedBy: [] },
              { id: 5, title: "Similar username", author: { username: "bob" }, favoritedBy: ["alice2"] },
            ],
          };
        });
        await page.goto(new URL("/profile/alice/favorites", url).href);
        assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "alice");
        assert.deepEqual(
          (await page.getByRole("heading", { level: 2 }).allTextContents()).sort(),
          ["Own favorite", "Shared favorite"]
        );
      },
    },
    {
      name: "Article tabs retain the visited profile and survive reload",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = {
            articles: [
              { id: 1, title: "Bob authored", author: { username: "bob" }, favoritedBy: ["alice"] },
              { id: 2, title: "Bob saved", author: { username: "carol" }, favoritedBy: ["bob"] },
              { id: 3, title: "Alice only", author: { username: "alice" }, favoritedBy: ["alice"] },
            ],
          };
        });
        await page.goto(new URL("/profile/bob", url).href);
        assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "bob");
        assert.deepEqual(await page.getByRole("heading", { level: 2 }).allTextContents(), ["Bob authored"]);

        await Promise.all([
          page.waitForURL(new URL("/profile/bob/favorites", url).href, { timeout: 4000 }),
          page.getByRole("link", { name: "Favorites", exact: true }).click({ timeout: 4000 }),
        ]);
        assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "bob");
        assert.deepEqual(await page.getByRole("heading", { level: 2 }).allTextContents(), ["Bob saved"]);

        await page.reload();
        assert.deepEqual(await page.getByRole("heading", { level: 2 }).allTextContents(), ["Bob saved"]);

        await Promise.all([
          page.waitForURL(new URL("/profile/bob", url).href, { timeout: 4000 }),
          page.getByRole("link", { name: "My Articles", exact: true }).click({ timeout: 4000 }),
        ]);
        assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "bob");
        assert.deepEqual(await page.getByRole("heading", { level: 2 }).allTextContents(), ["Bob authored"]);
      },
    },
    {
      name: "A profile with no matching articles shows neither other users' articles nor favorites",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = {
            articles: [
              { id: 1, title: "Alice article", author: { username: "alice" }, favoritedBy: ["bob"] },
              { id: 2, title: "Bob article", author: { username: "bob" }, favoritedBy: ["alice"] },
            ],
          };
        });
        for (const path of ["/profile/carol", "/profile/carol/favorites"]) {
          await page.goto(new URL(path, url).href);
          assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "carol");
          assert.deepEqual(await page.getByRole("heading", { level: 2 }).allTextContents(), []);
        }
      },
    },
    {
      name: "Encoded usernames display correctly and select the correct articles",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = {
            articles: [
              { id: 1, title: "Renée authored", author: { username: "renée" }, favoritedBy: [] },
              { id: 2, title: "Renée saved", author: { username: "bob" }, favoritedBy: ["renée"] },
              { id: 3, title: "Different user", author: { username: "renee" }, favoritedBy: ["renee"] },
            ],
          };
        });
        await page.goto(new URL("/profile/" + encodeURIComponent("renée"), url).href);
        assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "renée");
        assert.deepEqual(await page.getByRole("heading", { level: 2 }).allTextContents(), ["Renée authored"]);

        await Promise.all([
          page.waitForURL(
            new URL("/profile/" + encodeURIComponent("renée") + "/favorites", url).href,
            { timeout: 4000 }
          ),
          page.getByRole("link", { name: "Favorites", exact: true }).click({ timeout: 4000 }),
        ]);
        assert.equal(await page.getByRole("heading", { level: 1 }).innerText(), "renée");
        assert.deepEqual(await page.getByRole("heading", { level: 2 }).allTextContents(), ["Renée saved"]);
      },
    },
  ],
};
