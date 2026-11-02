const DEMO_REAGENTS = [
    "67-64-1",          // Acetone (Flammable)
    "7697-37-2",        // Nitric Acid (Oxidizer / Acid)
    "7647-01-0",        // Hydrochloric Acid (Corrosive Acid)
    "1310-73-2",        // Sodium Hydroxide (Corrosive Base)
    "26628-22-8",       // Sodium Azide (Acute Toxic)
    "7440-23-5",        // Sodium Metal (Water-Reactive)
    "64-19-7",          // Acetic Acid Glacial (Flammable / Corrosive)
    "7647-14-5"         // Sodium Chloride (General Storage)
];

const inputEl = document.getElementById("chemical-input");
const btnDemo = document.getElementById("btn-demo");
const btnClear = document.getElementById("btn-clear");
const btnAnalyze = document.getElementById("btn-analyze");
const btnPrint = document.getElementById("btn-print");
const statusMsg = document.getElementById("status-msg");
const resultsArea = document.getElementById("results-area");
const conflictsSection = document.getElementById("conflicts-section");
const conflictsList = document.getElementById("conflicts-list");
const conflictCountBadge = document.getElementById("conflict-count-badge");
const cabinetsGrid = document.getElementById("cabinets-grid");
const matrixTable = document.getElementById("matrix-table");
const cellInspector = document.getElementById("cell-inspector");

btnDemo.addEventListener("click", () => {
    inputEl.value = DEMO_REAGENTS.join("\n");
    runAnalysis();
});

btnClear.addEventListener("click", () => {
    inputEl.value = "";
    resultsArea.classList.add("hidden");
    statusMsg.textContent = "";
});

btnPrint.addEventListener("click", () => {
    window.print();
});

btnAnalyze.addEventListener("click", runAnalysis);

async function runAnalysis() {
    const raw = inputEl.value.trim();
    if (!raw) {
        statusMsg.textContent = "Please enter at least one CAS number or chemical name.";
        return;
    }

    const queries = raw
        .split(/[\n,;]+/)
        .map(s => s.trim())
        .filter(Boolean);

    btnAnalyze.disabled = true;
    statusMsg.textContent = `Analyzing ${queries.length} chemical(s) via GHS & PubChem...`;

    try {
        const response = await fetch("/api/analyze", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ queries })
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || "Failed to analyze inventory.");
        }

        const data = await response.json();
        renderResults(data);
        statusMsg.textContent = `Completed: ${data.chemicals.length} substance(s) segregated into ${data.cabinets.length} cabinet(s).`;
    } catch (err) {
        statusMsg.textContent = `Error: ${err.message}`;
    } finally {
        btnAnalyze.disabled = false;
    }
}

function renderResults(data) {
    resultsArea.classList.remove("hidden");

    // 1. Render Conflicts
    conflictsList.innerHTML = "";
    if (data.conflicts.length > 0) {
        conflictsSection.classList.remove("hidden");
        conflictCountBadge.textContent = `${data.conflicts.length} Conflict(s)`;
        data.conflicts.forEach(c => {
            const li = document.createElement("li");
            li.innerHTML = `<strong>${c.chem_a}</strong> (${c.group_a}) + <strong>${c.chem_b}</strong> (${c.group_b}) — <span style="color:#991b1b">${c.reason}</span>`;
            conflictsList.appendChild(li);
        });
    } else {
        conflictsSection.classList.add("hidden");
    }

    // 2. Render Segregated Cabinets
    cabinetsGrid.innerHTML = "";
    data.cabinets.forEach(cab => {
        const card = document.createElement("div");
        card.className = "cabinet-card";
        card.style.borderTopColor = cab.badge_color;

        const itemsHtml = cab.chemicals.map(ch => {
            const hBadges = (ch.normalized_h_codes.length ? ch.normalized_h_codes : ["No GHS H-Codes"])
                .map(code => `<span class="h-badge">${code}</span>`)
                .join("");
            return `
                <div class="chem-item">
                    <div>
                        <div class="chem-name">${ch.name}</div>
                        <div class="chem-cas">CAS: ${ch.cas}</div>
                    </div>
                    <div class="h-badges">${hBadges}</div>
                </div>
            `;
        }).join("");

        card.innerHTML = `
            <div class="cabinet-header">
                <div class="cabinet-title">${cab.cabinet_name}</div>
            </div>
            <div class="cabinet-desc">${cab.description}</div>
            <div>${itemsHtml}</div>
        `;
        cabinetsGrid.appendChild(card);
    });

    // 3. Render N x N Matrix
    matrixTable.innerHTML = "";
    const chems = data.chemicals;

    const thead = document.createElement("thead");
    const headerRow = document.createElement("tr");
    headerRow.innerHTML = `<th>Chemical</th>` + chems.map((c, idx) => `<th>#${idx + 1}<br>${c.name}</th>`).join("");
    thead.appendChild(headerRow);
    matrixTable.appendChild(thead);

    const tbody = document.createElement("tbody");
    data.matrix.forEach((row, i) => {
        const tr = document.createElement("tr");
        const rowHeader = document.createElement("th");
        rowHeader.style.textAlign = "left";
        rowHeader.textContent = `#${i + 1} ${chems[i].name} (${chems[i].group_title})`;
        tr.appendChild(rowHeader);

        row.forEach((cell, j) => {
            const td = document.createElement("td");
            if (cell.status === "self") {
                td.className = "cell-self";
                td.textContent = "—";
            } else if (cell.status === "compatible") {
                td.className = "cell-compatible";
                td.textContent = "OK";
            } else if (cell.status === "caution") {
                td.className = "cell-caution";
                td.textContent = "CAUTION";
            } else {
                td.className = "cell-incompatible";
                td.textContent = "STOP";
            }

            if (cell.status !== "self") {
                const showDetail = () => {
                    cellInspector.innerHTML = `<strong>${chems[i].name}</strong> + <strong>${chems[j].name}</strong>: [${cell.status.toUpperCase()}] ${cell.reason}`;
                };
                td.addEventListener("mouseenter", showDetail);
                td.addEventListener("click", showDetail);
            }
            tr.appendChild(td);
        });
        tbody.appendChild(tr);
    });
    matrixTable.appendChild(tbody);
}