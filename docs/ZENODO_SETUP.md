# Zenodo DOI — setup instructions for Daniela

The repository is ready for Zenodo integration. Zenodo will mint a permanent, citable DOI (something like `10.5281/zenodo.XXXXXXX`) that can be referenced in the paper and in the ontology header.

The repo already ships `.zenodo.json` with the correct metadata (title, description, keywords, creators, license, related identifiers including DOIs for the four core references: Xiao 2019, Calvanese 2007, Calvanese 2017, Ortiz & Šimkus 2012). Zenodo will read this file automatically.

## Five steps for you (total time ~10 minutes)

### 1. Sign in to Zenodo with GitHub

Go to https://zenodo.org/login and choose **"Sign in with GitHub"**. Authorise Zenodo to see your GitHub repositories. This uses your existing `teamdaniela-png` GitHub account.

### 2. Enable the repository in Zenodo

Once logged in, go to https://zenodo.org/account/settings/github/

You'll see a list of all your GitHub repositories. Find `teamdaniela-png/ramona-vkg` in the list and toggle the switch to **ON**. This tells Zenodo: "when this repo publishes a new GitHub Release, archive it and mint a DOI".

### 3. Create a fresh GitHub Release to trigger minting

Zenodo only picks up releases created AFTER you flipped the switch. So we need a fresh release tag. I (Claude) can prepare that when you give me the signal:

```bash
# in ramona_vkg_demo/
git tag -a v1.6.2 -m "v1.6.2 — first Zenodo-archived release"
git push origin v1.6.2
gh release create v1.6.2 --title "v1.6.2 — Zenodo DOI release" --notes "First release with DOI via Zenodo. No ontology content changes from v1.6.1."
```

### 4. Zenodo picks it up (1-5 minutes)

Zenodo polls GitHub for new releases and receives a webhook when you push. Within ~5 minutes a new record will appear at https://zenodo.org/deposit with the repository name.

### 5. Verify the DOI

Go to https://zenodo.org/deposit, find the new record, and copy the DOI (format `10.5281/zenodo.1234567`). You can now cite it.

## After the DOI is minted — what we'll do

I'll add the DOI into three places:

- `ontology/ratr-o.ttl` header (new `dct:identifier` triple).
- `README.md` top of file with a DOI badge.
- `docs/RIGOR_STATEMENT.md` at the bottom as the citable reference.

Also the `.zenodo.json` already includes `related_identifiers` pointing to the four foundational papers we cite, so the DOI will appear properly connected in the scholarly graph.

## Why Zenodo and not just GitHub

- **Permanence.** GitHub repos can disappear; Zenodo is CERN-backed and legally obliged to preserve deposits for 20+ years.
- **Citability.** Papers cite DOIs, not repo URLs.
- **Version-specific DOIs.** Every new release gets its own DOI; there is also a "concept DOI" that always resolves to the latest version.
- **Discoverability.** OpenAIRE and Google Scholar index Zenodo deposits.

## Troubleshooting

- If the repository does not show up in Zenodo's GitHub integration, check that the repo is public (it is) and that your GitHub-Zenodo link has the `public_repo` scope. A quick fix is to revoke and re-grant the authorisation at https://github.com/settings/applications
- If the release does not generate a Zenodo record after 15 minutes, check https://zenodo.org/account/settings/github/ for the repository-level log. Zenodo shows an error message there.
- If Zenodo complains about the `.zenodo.json` file, the schema validator error message tells you the offending field. The file in this repo has been tested against the current Zenodo API.

## When to mint v1.7 or later

Every time you make a release (`git tag v1.X` and `gh release create v1.X`), Zenodo will mint a new DOI automatically. No additional action required. We should tag:

- **v1.7** — after O2 R2RML parity is complete (sábado 25 abril).
- **v1.8** — after O3 Ontop demonstrator runs end-to-end with CTDC loaded.
- **v2.0** — after Prof. Ortiz signs off on the paper.

Each of these will produce a new DOI that the paper can cite separately.
