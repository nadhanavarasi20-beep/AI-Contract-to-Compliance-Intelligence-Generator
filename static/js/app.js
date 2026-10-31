// AI Contract-to-Compliance Intelligence Generator - Interactive Client
let currentReport = null;
let currentContractFile = null;
let currentPolicyFile = null;

document.addEventListener("DOMContentLoaded", () => {
    initDropzones();
    initSettings();
    initFilters();
});

// Settings Management
function initSettings() {
    const savedKey = localStorage.getItem("gemini_api_key") || "";
    const keyInput = document.getElementById("settingsApiKey");
    if (keyInput && savedKey) {
        keyInput.value = savedKey;
        updateKeyStatusBadge(true);
    }

    const savedModel = localStorage.getItem("gemini_model") || "gemini-2.5-flash";
    const modelSelect = document.getElementById("settingsModel");
    if (modelSelect && savedModel) {
        modelSelect.value = savedModel;
    }
}

function saveSettings() {
    const keyInput = document.getElementById("settingsApiKey");
    const modelSelect = document.getElementById("settingsModel");
    if (keyInput) {
        localStorage.setItem("gemini_api_key", keyInput.value.trim());
        updateKeyStatusBadge(!!keyInput.value.trim());
    }
    if (modelSelect) {
        localStorage.setItem("gemini_model", modelSelect.value);
    }
    showToast("Settings updated successfully!", "success");
    closeModal("settingsModal");
}

function updateKeyStatusBadge(hasKey) {
    const badge = document.getElementById("engineStatusBadge");
    if (badge) {
        if (hasKey) {
            badge.innerHTML = `<span class="w-2 h-2 rounded-full bg-emerald-400 mr-1.5 pulse-dot"></span> Gemini-3.8-Flash (API Configured)`;
            badge.className = "inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-emerald-950/60 text-emerald-300 border border-emerald-800/60";
        } else {
            badge.innerHTML = `<span class="w-2 h-2 rounded-full bg-blue-400 mr-1.5"></span> Gemini-3.8-Flash (Quota-Shield Local Engine Active)`;
            badge.className = "inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-blue-950/60 text-blue-300 border border-blue-800/60";
        }
    }
}

async function testApiKeyConnection() {
    const keyInput = document.getElementById("settingsApiKey");
    const testResult = document.getElementById("testKeyResult");
    const apiKey = keyInput ? keyInput.value.trim() : "";

    if (!apiKey) {
        testResult.innerHTML = `<span class="text-rose-400">Please enter an API key to test.</span>`;
        return;
    }

    testResult.innerHTML = `<span class="text-blue-400">Testing connection to Gemini API...</span>`;
    
    try {
        const formData = new FormData();
        formData.append("gemini_api_key", apiKey);
        const res = await fetch("/api/test-key", { method: "POST", body: formData });
        const data = await res.json();
        
        if (data.valid) {
            testResult.innerHTML = `<span class="text-emerald-400">✓ ${data.message}</span>`;
            localStorage.setItem("gemini_api_key", apiKey);
            updateKeyStatusBadge(true);
        } else {
            testResult.innerHTML = `<span class="text-amber-400">Notice: ${data.message}</span><br/><span class="text-xs text-slate-400">System will seamlessly use the built-in Local Intelligence Engine with 0 errors.</span>`;
        }
    } catch (e) {
        testResult.innerHTML = `<span class="text-rose-400">Error connecting to test endpoint: ${e.message}</span>`;
    }
}

// Dropzone Handling
function initDropzones() {
    setupSingleDropzone("contractDropzone", "contractFileInput", "contractFileInfo", (file) => {
        currentContractFile = file;
    });

    setupSingleDropzone("policyDropzone", "policyFileInput", "policyFileInfo", (file) => {
        currentPolicyFile = file;
    });
}

function setupSingleDropzone(zoneId, inputId, infoId, onFileSelected) {
    const dropzone = document.getElementById(zoneId);
    const input = document.getElementById(inputId);
    const info = document.getElementById(infoId);

    if (!dropzone || !input) return;

    ['dragenter', 'dragover'].forEach(event => {
        dropzone.addEventListener(event, (e) => {
            e.preventDefault();
            dropzone.classList.add('dragover');
        });
    });

    ['dragleave', 'drop'].forEach(event => {
        dropzone.addEventListener(event, (e) => {
            e.preventDefault();
            dropzone.classList.remove('dragover');
        });
    });

    dropzone.addEventListener('drop', (e) => {
        if (e.dataTransfer.files.length > 0) {
            const file = e.dataTransfer.files[0];
            input.files = e.dataTransfer.files;
            onFileSelected(file);
            updateFileInfo(info, file);
        }
    });

    input.addEventListener('change', () => {
        if (input.files.length > 0) {
            const file = input.files[0];
            onFileSelected(file);
            updateFileInfo(info, file);
        }
    });
}

function updateFileInfo(infoElement, file) {
    if (!infoElement) return;
    const sizeKb = (file.size / 1024).toFixed(1);
    infoElement.innerHTML = `
        <div class="flex items-center justify-between p-2.5 rounded-lg bg-slate-800/90 border border-slate-700 text-xs">
            <div class="flex items-center space-x-2 truncate">
                <svg class="w-4 h-4 text-emerald-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
                <span class="font-medium text-slate-200 truncate">${file.name}</span>
            </div>
            <span class="text-slate-400 shrink-0">${sizeKb} KB</span>
        </div>
    `;
}

// 1-Click Sample Ingestion
async function loadSampleDocuments() {
    try {
        const res = await fetch("/api/samples");
        const data = await res.json();
        
        currentContractFile = null;
        currentPolicyFile = null;

        const contractInfo = document.getElementById("contractFileInfo");
        const policyInfo = document.getElementById("policyFileInfo");

        if (contractInfo) {
            contractInfo.innerHTML = `
                <div class="flex items-center justify-between p-2.5 rounded-lg bg-emerald-950/40 border border-emerald-800/60 text-xs text-emerald-300">
                    <span class="font-medium">Loaded Sample: ${data.contract.filename}</span>
                    <span class="text-emerald-400">PDF Ready</span>
                </div>
            `;
        }

        if (policyInfo) {
            policyInfo.innerHTML = `
                <div class="flex items-center justify-between p-2.5 rounded-lg bg-emerald-950/40 border border-emerald-800/60 text-xs text-emerald-300">
                    <span class="font-medium">Loaded Sample: ${data.policy.filename}</span>
                    <span class="text-emerald-400">PDF Ready</span>
                </div>
            `;
        }

        showToast("Sample Vendor Contract and Corporate Policy loaded!", "success");
    } catch (e) {
        showToast("Error loading samples: " + e.message, "error");
    }
}

// Main Pipeline Trigger
async function runAnalysis() {
    const runBtn = document.getElementById("runAnalysisBtn");
    const progressSection = document.getElementById("progressSection");
    const resultsSection = document.getElementById("resultsSection");
    const progressStatus = document.getElementById("progressStatus");
    const progressBar = document.getElementById("progressBar");

    const forceFallback = document.getElementById("forceFallbackCheckbox")?.checked || false;
    const apiKey = localStorage.getItem("gemini_api_key") || "";
    const modelName = localStorage.getItem("gemini_model") || "gemini-2.5-flash";

    const formData = new FormData();
    if (currentContractFile) {
        formData.append("contract_file", currentContractFile);
    }
    if (currentPolicyFile) {
        formData.append("policy_file", currentPolicyFile);
    }
    if (apiKey) {
        formData.append("gemini_api_key", apiKey);
    }
    formData.append("model_name", modelName);
    formData.append("force_fallback", forceFallback);

    // Disable button & show animated steps
    runBtn.disabled = true;
    runBtn.classList.add("opacity-60", "cursor-not-allowed");
    progressSection.classList.remove("hidden");
    resultsSection.classList.add("hidden");

    const steps = [
        "Parsing PDF Documents & Extracting Structured Text...",
        "Identifying Discrete Clauses & Section Boundaries...",
        "Indexing Clauses in Vector Store & Initializing RAG Engine...",
        "Analyzing Legal Commitments & Extracting Obligations...",
        "Detecting Contract Renewal, Cure, and Notice Deadlines...",
        "Evaluating Liability, IP, and Breach Notification Risks...",
        "Comparing Terms against Internal Compliance Policy Standards...",
        "Detecting Missing Policy Clauses & Drafting Redline Clauses...",
        "Compiling Structured Legal Compliance Intelligence Report..."
    ];

    let stepIndex = 0;
    const progressInterval = setInterval(() => {
        if (stepIndex < steps.length) {
            progressStatus.innerText = steps[stepIndex];
            const pct = Math.round(((stepIndex + 1) / steps.length) * 90);
            progressBar.style.width = `${pct}%`;
            stepIndex++;
        }
    }, 600);

    try {
        const response = await fetch("/api/analyze", {
            method: "POST",
            body: formData
        });

        clearInterval(progressInterval);
        progressBar.style.width = "100%";
        progressStatus.innerText = "Compliance Intelligence Successfully Generated!";

        const data = await response.json();

        if (data.success && data.report) {
            currentReport = data.report;
            renderReportDashboard(data.report);
            setTimeout(() => {
                progressSection.classList.add("hidden");
                resultsSection.classList.remove("hidden");
                resultsSection.scrollIntoView({ behavior: 'smooth' });
            }, 500);
            showToast("Compliance Intelligence report ready!", "success");
        } else {
            showToast("Analysis Error: " + (data.message || "Failed to parse document"), "error");
            progressSection.classList.add("hidden");
        }
    } catch (e) {
        clearInterval(progressInterval);
        progressSection.classList.add("hidden");
        showToast("Network / Server Error: " + e.message, "error");
    } finally {
        runBtn.disabled = false;
        runBtn.classList.remove("opacity-60", "cursor-not-allowed");
    }
}

// Render Results
function renderReportDashboard(report) {
    // 1. Metadata & Badges
    document.getElementById("reportIdDisplay").innerText = report.report_id;
    document.getElementById("contractNameDisplay").innerText = report.contract_name;
    document.getElementById("policyNameDisplay").innerText = report.policy_name;
    document.getElementById("engineUsedDisplay").innerText = report.engine_name;

    const fallbackBadge = document.getElementById("fallbackIndicatorBadge");
    if (fallbackBadge) {
        if (report.is_fallback_active) {
            fallbackBadge.classList.remove("hidden");
            fallbackBadge.title = report.fallback_reason || "Quota shield active";
        } else {
            fallbackBadge.classList.add("hidden");
        }
    }

    // 2. Score Meter & Grade
    const scoreVal = report.compliance_score;
    const scoreEl = document.getElementById("complianceScoreVal");
    const gradeEl = document.getElementById("complianceGradeVal");
    const scoreBar = document.getElementById("scoreCircleBar");

    if (scoreEl) scoreEl.innerText = `${scoreVal}%`;
    if (gradeEl) {
        gradeEl.innerText = `Grade ${report.grade}`;
        if (scoreVal >= 80) {
            gradeEl.className = "text-sm font-semibold px-2.5 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800";
        } else if (scoreVal >= 65) {
            gradeEl.className = "text-sm font-semibold px-2.5 py-0.5 rounded bg-amber-950 text-amber-400 border border-amber-800";
        } else {
            gradeEl.className = "text-sm font-semibold px-2.5 py-0.5 rounded bg-rose-950 text-rose-400 border border-rose-800";
        }
    }

    if (scoreBar) {
        const circumference = 2 * Math.PI * 45;
        const offset = circumference - (scoreVal / 100) * circumference;
        scoreBar.style.strokeDasharray = `${circumference}`;
        scoreBar.style.strokeDashoffset = `${offset}`;
        scoreBar.style.stroke = scoreVal >= 80 ? '#10B981' : (scoreVal >= 65 ? '#F59E0B' : '#EF4444');
    }

    // 3. Metric Chips
    const highRisks = report.risk_breakdown?.high || 0;
    const medRisks = report.risk_breakdown?.medium || 0;
    document.getElementById("highRiskCount").innerText = highRisks;
    document.getElementById("medRiskCount").innerText = medRisks;
    document.getElementById("missingCount").innerText = report.missing_clauses.length;
    document.getElementById("obligationsCount").innerText = report.obligations.length;
    document.getElementById("deadlinesCount").innerText = report.deadlines.length;

    // 4. Executive Summary
    document.getElementById("executiveSummaryText").innerText = report.executive_summary;

    // 5. Render All Tab Panes
    renderPolicyComparisons(report.policy_comparisons);
    renderRisks(report.risks);
    renderMissingClauses(report.missing_clauses);
    renderObligations(report.obligations);
    renderDeadlines(report.deadlines);
    renderClauses(report.contract_clauses, report.policy_clauses);
}

// Tab 1: Policy Comparison
function renderPolicyComparisons(comparisons) {
    const container = document.getElementById("policyComparisonTableBody");
    if (!container) return;

    if (!comparisons || comparisons.length === 0) {
        container.innerHTML = `<tr><td colspan="5" class="py-6 text-center text-slate-400">No policy comparisons generated.</td></tr>`;
        return;
    }

    container.innerHTML = comparisons.map(c => {
        let badgeClass = "badge-compliant";
        if (c.status === "Non-Compliant") badgeClass = "badge-noncompliant";
        else if (c.status === "Missing") badgeClass = "badge-missing";
        else if (c.status === "Partially Compliant") badgeClass = "badge-med";

        const hasContractCitation = !!c.contract_citation;
        const citationBtn = hasContractCitation
            ? `<button onclick="openCitationModal(${escapeJson(c.contract_citation)})" class="text-xs text-blue-400 hover:text-blue-300 underline font-medium">Sec ${c.contract_citation.section_number} (P.${c.contract_citation.page_number})</button>`
            : `<span class="text-xs text-slate-500 italic">Not in contract</span>`;

        return `
            <tr class="border-b border-slate-800/80 hover:bg-slate-800/40 transition">
                <td class="py-3 px-4 text-xs font-mono text-slate-400">${c.policy_requirement_id}</td>
                <td class="py-3 px-4">
                    <div class="text-sm font-semibold text-slate-200">${c.policy_title}</div>
                    <div class="text-xs text-slate-400 mt-0.5">${c.policy_rule}</div>
                </td>
                <td class="py-3 px-4">
                    <span class="px-2.5 py-1 rounded text-xs font-semibold ${badgeClass}">${c.status}</span>
                </td>
                <td class="py-3 px-4 text-xs text-slate-300 leading-relaxed">
                    <div class="font-medium text-slate-200">${c.contract_finding}</div>
                    <div class="text-slate-400 mt-1">${c.gap_analysis}</div>
                </td>
                <td class="py-3 px-4 whitespace-nowrap">
                    ${citationBtn}
                </td>
            </tr>
        `;
    }).join("");
}

// Tab 2: Risks
function renderRisks(risks) {
    const container = document.getElementById("risksContainer");
    if (!container) return;

    if (!risks || risks.length === 0) {
        container.innerHTML = `<div class="p-6 text-center text-slate-400 glass-card rounded-xl">No legal or operational risks flagged.</div>`;
        return;
    }

    container.innerHTML = risks.map(r => {
        const isHigh = r.severity === "High";
        const badgeClass = isHigh ? "badge-high" : (r.severity === "Medium" ? "badge-med" : "badge-low");
        const cardBorder = isHigh ? "border-rose-900/40 hover:border-rose-700/60" : "border-slate-800 hover:border-slate-700";

        return `
            <div class="glass-card rounded-xl p-5 border ${cardBorder} space-y-3">
                <div class="flex items-start justify-between gap-3">
                    <div>
                        <div class="flex items-center space-x-2">
                            <span class="px-2 py-0.5 rounded text-xs font-bold uppercase ${badgeClass}">${r.severity}</span>
                            <span class="text-xs font-medium text-slate-400 uppercase tracking-wider">${r.category}</span>
                            <span class="text-xs font-mono text-slate-500">${r.id}</span>
                        </div>
                        <h4 class="text-base font-semibold text-slate-100 mt-1.5">${r.risk_title}</h4>
                    </div>
                    <button onclick="openCitationModal(${escapeJson(r.citation)})" class="text-xs text-blue-400 hover:text-blue-300 bg-slate-800/80 px-2.5 py-1 rounded border border-slate-700 whitespace-nowrap">
                        Sec ${r.citation.section_number} (P.${r.citation.page_number})
                    </button>
                </div>
                <div class="text-xs text-slate-300 leading-relaxed">
                    <span class="text-slate-400 font-medium">Risk Rationale:</span> ${r.rationale}
                </div>
                <div class="p-3 rounded-lg bg-slate-900/90 border border-slate-800 text-xs">
                    <div class="flex items-center justify-between mb-1">
                        <span class="text-emerald-400 font-semibold flex items-center gap-1">
                            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"></path></svg>
                            Recommended Redline & Counsel Action:
                        </span>
                        <button onclick="copyToClipboard('${escapeStr(r.recommendation)}')" class="text-[11px] text-slate-400 hover:text-white underline">Copy</button>
                    </div>
                    <div class="text-slate-200 italic font-mono text-[11px] leading-relaxed">${r.recommendation}</div>
                </div>
            </div>
        `;
    }).join("");
}

// Tab 3: Missing Clauses
function renderMissingClauses(missing) {
    const container = document.getElementById("missingClausesContainer");
    if (!container) return;

    if (!missing || missing.length === 0) {
        container.innerHTML = `<div class="p-6 text-center text-slate-400 glass-card rounded-xl">All mandatory compliance policy clauses are present!</div>`;
        return;
    }

    container.innerHTML = missing.map(m => {
        return `
            <div class="glass-card rounded-xl p-5 border border-amber-900/40 space-y-3">
                <div class="flex items-start justify-between">
                    <div>
                        <div class="flex items-center space-x-2">
                            <span class="px-2 py-0.5 rounded text-xs font-bold badge-missing">Missing Clause</span>
                            <span class="text-xs font-mono text-slate-400">${m.policy_source_section}</span>
                        </div>
                        <h4 class="text-base font-semibold text-amber-200 mt-1">${m.required_clause_name}</h4>
                    </div>
                    <button onclick="openCitationModal(${escapeJson(m.policy_citation)})" class="text-xs text-slate-400 hover:text-white bg-slate-800 px-2 py-1 rounded border border-slate-700">
                        Policy Source
                    </button>
                </div>
                <div class="text-xs text-slate-300">
                    <span class="text-slate-400 font-medium">Compliance Vulnerability:</span> ${m.description}
                </div>
                <div class="p-3.5 rounded-lg bg-slate-900/90 border border-amber-900/50 text-xs">
                    <div class="flex items-center justify-between mb-1.5">
                        <span class="text-amber-400 font-semibold">Standard Legally-Vetted Clause to Insert:</span>
                        <button onclick="copyToClipboard('${escapeStr(m.suggested_redline_text)}')" class="text-xs px-2 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-800 hover:bg-amber-900">
                            Copy Clause
                        </button>
                    </div>
                    <p class="text-slate-200 font-mono text-[11px] leading-relaxed">"${m.suggested_redline_text}"</p>
                </div>
            </div>
        `;
    }).join("");
}

// Tab 4: Obligations
function renderObligations(obligations) {
    const container = document.getElementById("obligationsTableBody");
    if (!container) return;

    container.innerHTML = obligations.map(o => {
        let partyColor = "text-purple-400 bg-purple-950/60 border-purple-800";
        if (o.party === "Vendor") partyColor = "text-emerald-400 bg-emerald-950/60 border-emerald-800";
        else if (o.party === "Client") partyColor = "text-blue-400 bg-blue-950/60 border-blue-800";

        return `
            <tr class="border-b border-slate-800/80 hover:bg-slate-800/30 transition obligation-row" data-party="${o.party}">
                <td class="py-3 px-4 text-xs font-mono text-slate-500">${o.id}</td>
                <td class="py-3 px-4">
                    <span class="px-2.5 py-0.5 rounded text-xs font-semibold border ${partyColor}">${o.party}</span>
                </td>
                <td class="py-3 px-4 text-xs font-medium text-slate-300">${o.obligation_type}</td>
                <td class="py-3 px-4 text-xs text-slate-200 leading-relaxed">${o.duty_summary}</td>
                <td class="py-3 px-4 whitespace-nowrap">
                    <button onclick="openCitationModal(${escapeJson(o.citation)})" class="text-xs text-blue-400 hover:text-blue-300 underline font-medium">
                        Sec ${o.citation.section_number}
                    </button>
                </td>
            </tr>
        `;
    }).join("");
}

// Tab 5: Deadlines
function renderDeadlines(deadlines) {
    const container = document.getElementById("deadlinesTimeline");
    if (!container) return;

    container.innerHTML = deadlines.map((d, idx) => {
        return `
            <div class="relative pl-8 pb-6 border-l-2 border-slate-800 last:border-transparent last:pb-0">
                <div class="absolute -left-[9px] top-0.5 w-4 h-4 rounded-full bg-blue-500 border-2 border-slate-900 shadow"></div>
                <div class="glass-card rounded-xl p-4 border border-slate-800">
                    <div class="flex items-center justify-between">
                        <span class="px-2.5 py-0.5 rounded text-xs font-bold bg-blue-950 text-blue-300 border border-blue-800">${d.date_or_period}</span>
                        <span class="text-xs text-slate-400">${d.deadline_type}</span>
                    </div>
                    <div class="text-sm font-semibold text-slate-200 mt-2">${d.trigger_event}</div>
                    <div class="text-xs text-slate-400 italic mt-1">${d.description}</div>
                    <div class="mt-2 text-right">
                        <button onclick="openCitationModal(${escapeJson(d.citation)})" class="text-xs text-blue-400 hover:text-blue-300 underline">
                            Source: Sec ${d.citation.section_number} (P.${d.citation.page_number})
                        </button>
                    </div>
                </div>
            </div>
        `;
    }).join("");
}

// Tab 6: Clause Inspector
function renderClauses(contractClauses, policyClauses) {
    const container = document.getElementById("clauseInspectorList");
    if (!container) return;

    const allClauses = [
        ...(contractClauses || []).map(c => ({ ...c, docTag: "Contract" })),
        ...(policyClauses || []).map(p => ({ ...p, docTag: "Policy" }))
    ];

    container.innerHTML = allClauses.map(c => {
        const isContract = c.docTag === "Contract";
        const tagClass = isContract ? "bg-blue-950 text-blue-300 border-blue-800" : "bg-purple-950 text-purple-300 border-purple-800";

        return `
            <div class="glass-card rounded-xl p-4 border border-slate-800 space-y-2 clause-card" data-search="${(c.title + ' ' + c.text).toLowerCase()}">
                <div class="flex items-center justify-between">
                    <div class="flex items-center space-x-2">
                        <span class="px-2 py-0.5 rounded text-xs font-semibold border ${tagClass}">${c.docTag}</span>
                        <span class="text-xs font-mono text-slate-400">Sec ${c.section_num}</span>
                        <h5 class="text-sm font-semibold text-slate-200">${c.title}</h5>
                    </div>
                    <span class="text-xs text-slate-500">Page ${c.page}</span>
                </div>
                <p class="text-xs text-slate-300 leading-relaxed font-mono bg-slate-900/60 p-3 rounded-lg border border-slate-800/80 whitespace-pre-wrap">${c.text}</p>
            </div>
        `;
    }).join("");
}

// Filtering
function initFilters() {
    // Party filter for Obligations
    const partySelect = document.getElementById("partyFilterSelect");
    if (partySelect) {
        partySelect.addEventListener("change", (e) => {
            const filter = e.target.value;
            document.querySelectorAll(".obligation-row").forEach(row => {
                if (filter === "All" || row.getAttribute("data-party") === filter) {
                    row.style.display = "";
                } else {
                    row.style.display = "none";
                }
            });
        });
    }

    // Search filter for Clauses
    const searchInput = document.getElementById("clauseSearchInput");
    if (searchInput) {
        searchInput.addEventListener("input", (e) => {
            const query = e.target.value.toLowerCase().trim();
            document.querySelectorAll(".clause-card").forEach(card => {
                const searchContent = card.getAttribute("data-search") || "";
                if (!query || searchContent.includes(query)) {
                    card.style.display = "";
                } else {
                    card.style.display = "none";
                }
            });
        });
    }
}

// Tab Switching
function switchTab(tabId) {
    document.querySelectorAll(".tab-pane").forEach(pane => pane.classList.add("hidden"));
    document.querySelectorAll(".tab-btn").forEach(btn => btn.classList.remove("active"));

    const targetPane = document.getElementById(`tabPane-${tabId}`);
    const targetBtn = document.getElementById(`tabBtn-${tabId}`);

    if (targetPane) targetPane.classList.remove("hidden");
    if (targetBtn) targetBtn.classList.add("active");
}

// Modals
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.classList.remove("hidden");
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.classList.add("hidden");
}

function openCitationModal(citation) {
    if (!citation) return;
    document.getElementById("citationDocName").innerText = citation.document_name;
    document.getElementById("citationSectionNumber").innerText = citation.section_number;
    document.getElementById("citationSectionTitle").innerText = citation.section_title;
    document.getElementById("citationPageNumber").innerText = citation.page_number;
    document.getElementById("citationSnippet").innerText = `"${citation.snippet}"`;
    openModal("citationModal");
}

// Export Handlers
function downloadPdfReport() {
    if (!currentReport) {
        showToast("No active report to download.", "error");
        return;
    }
    window.open(`/api/reports/${currentReport.report_id}/pdf`, '_blank');
}

function exportJsonReport() {
    if (!currentReport) {
        showToast("No active report to export.", "error");
        return;
    }
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(currentReport, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute("href", dataStr);
    downloadAnchor.setAttribute("download", `Compliance_Report_${currentReport.report_id}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
}

// Utility: Copy to Clipboard
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showToast("Copied to clipboard!", "success");
    }).catch(() => {
        showToast("Failed to copy", "error");
    });
}

function escapeJson(obj) {
    return JSON.stringify(obj).replace(/"/g, '&quot;');
}

function escapeStr(str) {
    if (!str) return "";
    return str.replace(/'/g, "\\'").replace(/"/g, '&quot;').replace(/\n/g, ' ');
}

// Toast Notifications
function showToast(message, type = "info") {
    const toast = document.createElement("div");
    let bg = "bg-slate-800 border-slate-700 text-slate-200";
    if (type === "success") bg = "bg-emerald-950 border-emerald-700 text-emerald-200";
    if (type === "error") bg = "bg-rose-950 border-rose-700 text-rose-200";

    toast.className = `fixed bottom-5 right-5 z-50 flex items-center p-3.5 rounded-xl border shadow-xl text-xs font-medium space-x-2 transition-all transform duration-300 ${bg}`;
    toast.innerHTML = `<span>${message}</span>`;
    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = "0";
        setTimeout(() => toast.remove(), 300);
    }, 3500);
}
