# Borrador del pull request a perma-id/w3id.org (NO enviado)

Archivo a crear en el fork: `ids/ratr-o/.htaccess` (contenido = `htaccess.ratr-o` de esta carpeta).

**Título:** Add ratr-o: Ramona Anti-Trafficking and Recruitment-fraud Ontology

**Cuerpo:**

Adds `ids/ratr-o/` for RATR-O, an OWL 2 QL ontology for detecting fraudulent job offers and
trafficking recruitment in Latin America, developed during a BMEIA Dialogue Residency at the
Institute of Logic and Computation, TU Wien.

- `https://w3id.org/ratr-o` → HTML documentation (default) or Turtle (`Accept: text/turtle`), 303.
- `https://w3id.org/ratr-o/1.9` → Turtle of the tagged release v1.9, 303.
- `https://w3id.org/ratr-o/data/...` → documentation, 302 (instance IRIs of a virtual knowledge graph).

Targets are GitHub Pages (`text/turtle; charset=utf-8` verified) and raw.githubusercontent.com.
Maintainer: GitHub user teamdaniela-png.

**Commit message:** `Add ratr-o identifier for the RATR-O ontology`

## Cómo se manda (cuando Daniela diga)

1. `gh repo fork perma-id/w3id.org --clone` (cuenta teamdaniela-png)
2. Crear `ids/ratr-o/.htaccess`, correr `node tools/check/bin/w3id-check.js`
3. Commit, push al fork, `gh pr create` con el título y cuerpo de arriba.
