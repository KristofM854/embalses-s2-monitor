# Dashboard GIF

`docs/dashboard.gif` (shown in the main README) is recorded with Playwright against a local
copy of the dashboard with real data:

```bash
git fetch origin images && git worktree add images FETCH_HEAD
mkdir -p /tmp/site && cp -r dashboard/. /tmp/site/ && ln -s "$PWD/data" /tmp/site/data && ln -s "$PWD/images" /tmp/site/images
(cd /tmp/site && python -m http.server 8000 &)
mkdir -p /tmp/frames && node docs/gif/tour.js http://localhost:8000/ /tmp/frames   # needs: npm i playwright
python docs/gif/make_gif.py /tmp/frames docs/dashboard.gif                          # needs: pip install pillow
```

The tour opens the bloom of 14 January 2026 in Hatillo; change the date in `tour.js` if needed.
