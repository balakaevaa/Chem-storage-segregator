# ChemSegregate — GHS Chemical Compatibility Matrix & Cabinet Segregator

Free, open-source web utility for laboratory chemists, safety officers (EHS), and stockroom managers to evaluate pairwise chemical compatibility and automatically segregate chemical inventories into compliant storage cabinets.

## Key Features
- **Automated GHS Classification via PubChem API:** Enter CAS numbers or chemical names to retrieve GHS Hazard Statements (H-codes) automatically.
- **Intelligent Acid vs. Base Segregation:** Distinguishes between corrosive acids (`CORROSIVE_ACID`) and corrosive bases/alkalies (`CORROSIVE_BASE`) that share the same `H314` / `H290` GHS codes.
- **Hierarchy-Driven Cabinet Assignment:** Segregates reagents into 8 standard storage groups based on US OSHA, NFPA, and EU TRGS 510 safety priority rules:
  1. Water-Reactive & Pyrophoric (`H250`, `H260`, `H261`)
  2. Oxidizing Agents (`H270`, `H271`, `H272`)
  3. Flammable Liquids & Solids (`H220`–`H228`)
  4. Acutely Toxic & Poisons (`H300`, `H301`, `H310`, `H311`, `H330`, `H331`)
  5. Corrosive Acids (`H290`, `H314` + Acid nomenclature)
  6. Corrosive Bases (`H290`, `H314` + Alkali/Amine nomenclature)
  7. Chronic Health Hazards / CMR (`H340`–`H372`)
  8. General Laboratory Storage
- **Interactive $N \times N$ Compatibility Matrix:** Color-coded (`OK`, `CAUTION`, `STOP`) grid with specific chemical hazard explanations on hover/click.
- **Print-Ready Cabinet Door Checklists:** Clean `@media print` stylesheet for exporting PDF storage plans or posting directly on cabinet doors.

## Companion Tool
- Need print-ready GHS/CLP bottle labels? Use **[GHS Chemical Label Generator](https://ghs-chemical-label-generator.onrender.com/)**.

## Local Setup & Testing
```bash
python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate # macOS/Linux
pip install -r requirements.txt

# Run unit & API tests
pytest -v

# Start local server
uvicorn app.main:app --reload