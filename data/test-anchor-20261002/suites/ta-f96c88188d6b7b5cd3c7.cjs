module.exports = {
  tests: [
    {
      name: "Profile shows authored articles and switches to favorites",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = {
            articles: [
              { id: 1, title: "Alice authored only", author: { username: "alice" }, favoritedBy: ["bob"] },
              { id: 2, title: "Alice authored and favorited", author: { username: "alice" }, favoritedBy: ["alice"] },
              { id: 3, title: "Bob article Alice likes", author: { username: "bob" }, favoritedBy: ["alice", "bob"] },
              { id: 4, title: "Unrelated article", author: { username: "carol" }, favoritedBy: ["carol"] },
            ],
          };
        });

        await page.goto(new URL("/profile/alice", url).href);
        assert.equal(await page.locator("h1").innerText(), "alice");
        assert.deepEqual(
          (await page.locator("#articles h2").allTextContents()).sort(),
          ["Alice authored only", "Alice authored and favorited"].sort()
        );

        await Promise.all([
          page.waitForURL("**/profile/alice/favorites", { timeout: 5000 }),
          page.getByRole("link", { name: "Favorites", exact: true }).click({ timeout: 5000 }),
        ]);
        assert.equal(await page.locator("h1").innerText(), "alice");
        assert.deepEqual(
          (await page.locator("#articles h2").allTextContents()).sort(),
          ["Alice authored and favorited", "Bob article Alice likes"].sort()
        );

        await Promise.all([
          page.waitForURL("**/profile/alice", { timeout: 5000 }),
          page.getByRole("link", { name: "My Articles", exact: true }).click({ timeout: 5000 }),
        ]);
        assert.deepEqual(
          (await page.locator("#articles h2").allTextContents()).sort(),
          ["Alice authored only", "Alice authored and favorited"].sort()
        );
      },
    },
    {
      name: "Direct favorites URL uses the requested user's favorites",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = {
            articles: [
              { id: 1, title: "Alice article Bob likes", author: { username: "alice" }, favoritedBy: ["bob"] },
              { id: 2, title: "Bob authored only", author: { username: "bob" }, favoritedBy: ["alice"] },
              { id: 3, title: "Bob authored and favorited", author: { username: "bob" }, favoritedBy: ["bob", "alice"] },
              { id: 4, title: "Alice favorite only", author: { username: "carol" }, favoritedBy: ["alice"] },
            ],
          };
        });

        await page.goto(new URL("/profile/bob/favorites", url).href);
        assert.equal(await page.locator("h1").innerText(), "bob");
        assert.deepEqual(
          (await page.locator("#articles h2").allTextContents()).sort(),
          ["Alice article Bob likes", "Bob authored and favorited"].sort()
        );

        await Promise.all([
          page.waitForURL("**/profile/bob", { timeout: 5000 }),
          page.getByRole("link", { name: "My Articles", exact: true }).click({ timeout: 5000 }),
        ]);
        assert.equal(await page.locator("h1").innerText(), "bob");
        assert.deepEqual(
          (await page.locator("#articles h2").allTextContents()).sort(),
          ["Bob authored only", "Bob authored and favorited"].sort()
        );
      },
    },
    {
      name: "Encoded usernames display correctly and retain their article lists",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = {
            articles: [
              { id: 1, title: "Renée's article", author: { username: "renée" }, favoritedBy: [] },
              { id: 2, title: "Renée's favorite", author: { username: "alice" }, favoritedBy: ["renée"] },
              { id: 3, title: "Different user's article", author: { username: "renee" }, favoritedBy: ["renee"] },
            ],
          };
        });

        const profilePath = "/profile/" + encodeURIComponent("renée");
        await page.goto(new URL(profilePath, url).href);
        assert.equal(await page.locator("h1").innerText(), "renée");
        assert.deepEqual(await page.locator("#articles h2").allTextContents(), ["Renée's article"]);

        await Promise.all([
          page.waitForURL(
            target => decodeURIComponent(target.pathname) === "/profile/renée/favorites",
            { timeout: 5000 }
          ),
          page.getByRole("link", { name: "Favorites", exact: true }).click({ timeout: 5000 }),
        ]);
        assert.equal(await page.locator("h1").innerText(), "renée");
        assert.deepEqual(await page.locator("#articles h2").allTextContents(), ["Renée's favorite"]);
      },
    },
    {
      name: "Users without articles or favorites see no unrelated articles",
      run: async ({ context, page, url, assert }) => {
        await context.addInitScript(() => {
          window.initialState = {
            articles: [
              { id: 1, title: "Alice's article", author: { username: "alice" }, favoritedBy: ["alice"] },
              { id: 2, title: "Bob's article", author: { username: "bob" }, favoritedBy: ["alice", "bob"] },
            ],
          };
        });

        await page.goto(new URL("/profile/carol", url).href);
        assert.equal(await page.locator("h1").innerText(), "carol");
        assert.deepEqual(await page.locator("#articles h2").allTextContents(), []);

        await Promise.all([
          page.waitForURL("**/profile/carol/favorites", { timeout: 5000 }),
          page.getByRole("link", { name: "Favorites", exact: true }).click({ timeout: 5000 }),
        ]);
        assert.equal(await page.locator("h1").innerText(), "carol");
        assert.deepEqual(await page.locator("#articles h2").allTextContents(), []);
      },
    },
  ],
};
