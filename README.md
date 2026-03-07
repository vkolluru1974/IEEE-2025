# GitHub Pages site

This repository contains a minimal static site configured for GitHub Pages and Google Search Console verification.

Steps I took (automated):
- Created `index.html`, `about.html`, `robots.txt`, and `sitemap.xml`.
- Added a GitHub Actions workflow (in `.github/workflows/pages.yml`) to deploy to GitHub Pages on `main` branch pushes.

What you need to do:
1. Create a new GitHub repository named `REPO_NAME` under the GitHub account `USERNAME`.
2. Push this project to that repository and set the default branch to `main`.
3. In the repo settings -> Pages, ensure the site is published from the `main` branch and the root folder (or let the workflow configure Pages automatically).
4. Open Google Search Console (https://search.google.com/search-console) and add a new property for the published site (https://USERNAME.github.io or https://USERNAME.github.io/REPO_NAME). Verify ownership: either
   - Use the HTML meta tag verification and paste the provided meta tag into `index.html` (replace the placeholder), OR
   - Upload the HTML verification file that Google provides into this repository root.
5. After verification, request indexing for the site URL inside Search Console and submit the sitemap URL: `https://USERNAME.github.io/REPO_NAME/sitemap.xml`.

If you want me to push the repository to GitHub and configure the repository name and username, tell me the GitHub username and repository name and I'll push and open the repo for you.
