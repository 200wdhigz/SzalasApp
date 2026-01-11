# 📚 Wiki & Dokumentacja

Ten folder zawiera dokumentację projektu SzalasApp oraz źródła dla GitHub Wiki.

---

## 📁 Struktura

```
wiki/
├── docs/                 # Pliki źródłowe dokumentacji (Markdown)
│   ├── 00_INDEX.md
│   ├── 01_QUICK_START.md
│   └── ...
│
├── export/               # Wygenerowane pliki wiki (tworzone przez workflow)
├── GITHUB_WIKI_GUIDE.md  # Instrukcje publikacji / działania Wiki
└── README.md             # Ten plik
```

> `export/` jest generowane automatycznie przez workflow i nie powinno być edytowane ręcznie.

---

## 🚀 Jak aktualizować GitHub Wiki (zalecane)

Wiki aktualizuje się automatycznie przez GitHub Actions workflow: `.github/workflows/update-wiki.yml`.

### Kiedy się uruchamia?

- po merge / push do `master`
- albo ręcznie (Actions → **update-wiki** → **Run workflow**)

### Co robi workflow?

1. Bierze pliki z `wiki/docs/`
2. Generuje `wiki/export/` (konwersja linków na format GitHub Wiki + generuje `_Sidebar.md` i `_Footer.md`)
3. Wypycha wynik do repozytorium Wiki (`<repo>.wiki`)

✅ **Nie musisz uruchamiać żadnych skryptów lokalnie** i **nie musisz mieć Pythona**.

---

## 🧑‍💻 Aktualizacja ręczna (opcjonalnie)

Jeśli z jakiegoś powodu nie możesz użyć GitHub Actions:

1. Skopiuj pliki z `wiki/docs/` do swojego repo wiki i zachowaj nazwy z mapowania w workflow.
2. Pamiętaj, że w GitHub Wiki linki powinny mieć format: `[tekst](Nazwa-Strony)` (bez `.md`).

W praktyce zalecamy jednak użycie workflow (automatyczne poprawianie linków i plików specjalnych).

---

## 🔄 Workflow aktualizacji (skrót)

1. Edytujesz pliki Markdown w `wiki/docs/`
2. Tworzysz PR → merge do `master`
3. GitHub Actions aktualizuje Wiki automatycznie

---

## ⚠️ Ważne uwagi

- **Nie edytuj** ręcznie plików w `wiki/export/` – są generowane.
- Jeśli chcesz dodać nowy dokument, dodaj go w `wiki/docs/` oraz dopisz w mapowaniu w `.github/workflows/update-wiki.yml`.
