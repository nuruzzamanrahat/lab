# Lab Showcase Website

A free, static lab/academic showcase website with **automatically updated publications**
pulled nightly from ORCID and Semantic Scholar. No server, no database, no monthly cost.

## Tech stack

| Layer | Tool | Cost |
|---|---|---|
| Hosting | GitHub Pages | Free |
| Auto-fetch | GitHub Actions | Free (2000 min/month) |
| Publication data | ORCID + Semantic Scholar APIs | Free, no key |
| Contact form | Formspree | Free (50 submissions/month) |
| Analytics | Plausible / Google Analytics | Free tier |

---

## File structure

```
lab-website/
├── index.html              ← Homepage
├── publications.html       ← Full publications list (auto-updated)
├── research.html           ← Research projects
├── team.html               ← Team / people
├── contact.html            ← Contact form
├── css/
│   └── style.css           ← All shared styles
├── js/
│   └── publications.js     ← Renders publications.json on the page
├── data/
│   └── publications.json   ← Auto-generated every night ← DO NOT hand-edit
├── scripts/
│   └── fetch_publications.py   ← The fetch script
└── .github/
    └── workflows/
        └── update-publications.yml   ← Nightly GitHub Actions job
```

---

## Setup guide (one-time, ~2 hours)

### 1. Fork / clone this repo

```bash
git clone https://github.com/your-org/lab-website.git
cd lab-website
```

### 2. Add your ORCID IDs

Every researcher needs a **free ORCID profile**:
1. Go to [https://orcid.org/register](https://orcid.org/register) — takes 2 minutes
2. Add your papers (you can import from CrossRef/DOI automatically)
3. Make sure your profile is set to **public**

Then open `scripts/fetch_publications.py` and update the list:

```python
ORCID_IDS = [
    "0000-0000-0000-XXXX",   # Dr. Your Name
    "0000-0000-0000-YYYY",   # Another Researcher
]
```

### 3. Test the fetch script locally

```bash
pip install requests
python scripts/fetch_publications.py
# → writes data/publications.json
```

Open `index.html` in your browser to verify publications appear.

### 4. Customise the site content

- **`index.html`** — lab name, hero text, research areas, news items
- **`team.html`** — replace placeholder names, roles, and ORCID links
- **`research.html`** — describe your actual projects
- **`css/style.css`** — change `--accent` colour if desired

### 5. Set up the contact form (Formspree)

1. Go to [https://formspree.io](https://formspree.io) — create a free account
2. Create a new form → copy your form ID (looks like `xpzgkrjb`)
3. In `contact.html`, replace `YOUR_FORM_ID`:
   ```html
   <form action="https://formspree.io/f/xpzgkrjb" method="POST">
   ```

### 6. Deploy to GitHub Pages (free)

```bash
git add .
git commit -m "Initial site"
git push origin main
```

Then in your GitHub repo:
- Go to **Settings → Pages**
- Source: **Deploy from branch → main → / (root)**
- Save → your site is live at `https://your-org.github.io/lab-website`

### 7. The automation runs itself

The GitHub Actions workflow (`.github/workflows/update-publications.yml`) runs every night at 02:00 UTC.
It will:
1. Run `fetch_publications.py`
2. Commit the updated `publications.json` if anything changed
3. GitHub Pages automatically rebuilds the site

You can also trigger it manually from **Actions → Update publications → Run workflow**.

---

## Customisation tips

### Change the accent colour
In `css/style.css`, update:
```css
--accent:  #2a9d8f;   /* teal — change to your preference */
--accent-2: #e76f51;  /* coral — used for conference papers */
```

### Add Google Analytics (optional, free)
Paste your GA4 snippet just before `</head>` in each HTML file.

### Add search (optional, free)
[Pagefind](https://pagefind.app) works great with static sites — add full-text search with one command.

### Custom domain (optional, free via GitHub Pages)
In **Settings → Pages → Custom domain**, add `lab.youruniversity.edu.bd`.
Then add a `CNAME` file to the repo root containing your domain.

---

## Troubleshooting

**Publications not loading locally** — browsers block `fetch()` from `file://`. Use a local server:
```bash
python -m http.server 8000
# then open http://localhost:8000
```

**ORCID returns 0 works** — check that your ORCID profile visibility is set to "Everyone" (public).

**GitHub Actions fails** — check the Actions tab for logs. Common fix: make sure `data/` directory exists and is committed.

---

## Total monthly cost: $0
