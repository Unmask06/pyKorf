document.addEventListener("DOMContentLoaded", function () {
  // -----------------------------------------------------------------------
  // Criteria options from embedded JSON
  // -----------------------------------------------------------------------
  const codesRaw = document.getElementById("criteria-data").textContent;
  const CODES = JSON.parse(codesRaw);
  // CODES = { "liquid": [["P-SUC-BUB","P-SUC-BUB - ..."], ...], "gas": [...], "two_phase": [...] }

  const PIPE_CRITERIA = JSON.parse(
    document.getElementById("pipe-criteria-values").textContent,
  );
  // PIPE_CRITERIA = { pipe_name: { "state:code": { max_dp, max_vel, min_vel, rho_v2_min, rho_v2_max } } }

  const PIPE_CALCS = JSON.parse(
    document.getElementById("pipe-calcs").textContent,
  );
  // PIPE_CALCS = { pipe_name: { dp_calc, vel_calc, rho_v2_calc } }

  // Build criteria <option> HTML for a given fluid type
  function buildOptions(fluidType, selected) {
    const entries = CODES[fluidType] || [];
    let html = '<option value="">-</option>';
    entries.forEach(function ([code, label]) {
      const sel = code === selected ? " selected" : "";
      html += `<option value="${code}"${sel}>${label}</option>`;
    });
    return html;
  }

  // Format rho_v2 criteria range: "≤ max" for gas (min=0), "min - max" for two-phase, "-" if null
  function fmtRhoV2Range(min, max) {
    if (min == null || max == null) return "-";
    const fmtK = (v) =>
      v >= 1000 ? (v / 1000).toFixed(0) + "k" : v.toFixed(0);
    return min === 0.0
      ? "\u2264 " + fmtK(max)
      : fmtK(min) + " \u2013 " + fmtK(max);
  }

  // Update the read-only criteria value cells for a pipe
  function updateCriteriaDisplay(pipe) {
    const stateEl = document.querySelector(
      `.state-select[data-pipe="${pipe}"]`,
    );
    const criteriaEl = document.querySelector(
      `.criteria-select[data-pipe="${pipe}"]`,
    );
    const dpEl = document.querySelector(`.crit-dp[data-pipe="${pipe}"]`);
    const vminEl = document.querySelector(`.crit-vmin[data-pipe="${pipe}"]`);
    const vmaxEl = document.querySelector(`.crit-vmax[data-pipe="${pipe}"]`);
    const rhov2El = document.querySelector(
      `.crit-rhov2[data-pipe="${pipe}"]`,
    );
    if (!stateEl || !criteriaEl || !dpEl) return;

    const state = stateEl.value;
    const code = criteriaEl.value;
    const key = state + ":" + code;
    const vals = (PIPE_CRITERIA[pipe] || {})[key];

    const fmt = (v) => (v == null ? "-" : v.toFixed(2));

    if (vals && state && code) {
      dpEl.textContent = fmt(vals.max_dp);
      vminEl.textContent = vals.min_vel > 0 ? vals.min_vel.toFixed(2) : "-";
      vmaxEl.textContent = fmt(vals.max_vel);
      if (rhov2El)
        rhov2El.textContent = fmtRhoV2Range(vals.rho_v2_min, vals.rho_v2_max);
    } else {
      dpEl.textContent = "-";
      vminEl.textContent = "-";
      vmaxEl.textContent = "-";
      if (rhov2El) rhov2El.textContent = "-";
    }
  }

  // -----------------------------------------------------------------------
  // Highlight calc cells that breach criteria bounds
  // -----------------------------------------------------------------------
  function checkCalcVsCriteria(pipe) {
    const stateEl = document.querySelector(
      `.state-select[data-pipe="${pipe}"]`,
    );
    const criteriaEl = document.querySelector(
      `.criteria-select[data-pipe="${pipe}"]`,
    );
    const dpCalcEl = document.querySelector(`.calc-dp[data-pipe="${pipe}"]`);
    const velCalcEl = document.querySelector(
      `.calc-vel[data-pipe="${pipe}"]`,
    );
    const rv2CalcEl = document.querySelector(
      `.calc-rhov2[data-pipe="${pipe}"]`,
    );

    // Reset
    [dpCalcEl, velCalcEl, rv2CalcEl].forEach(function (el) {
      if (el) el.classList.remove("text-danger", "fw-semibold");
    });

    if (!stateEl || !criteriaEl) return;
    const state = stateEl.value;
    const code = criteriaEl.value;
    if (!state || !code) return;

    const vals = (PIPE_CRITERIA[pipe] || {})[state + ":" + code];
    const calcs = PIPE_CALCS[pipe] || {};
    if (!vals) return;

    // dP: flag if calc > max_dp (null max_dp means no limit)
    if (dpCalcEl && calcs.dp_calc != null && calcs.dp_calc > 0) {
      if (vals.max_dp != null && calcs.dp_calc > vals.max_dp) {
        dpCalcEl.classList.add("text-danger", "fw-semibold");
      }
    }

    // Velocity: flag if below min (>0) or above max (null = no limit)
    if (velCalcEl && calcs.vel_calc != null && calcs.vel_calc > 0) {
      const tooSlow = vals.min_vel > 0 && calcs.vel_calc < vals.min_vel;
      const tooFast = vals.max_vel != null && calcs.vel_calc > vals.max_vel;
      if (tooSlow || tooFast) {
        velCalcEl.classList.add("text-danger", "fw-semibold");
      }
    }

    // ρV²: flag if outside [min, max] range (min > 0 means a lower bound applies)
    if (rv2CalcEl && calcs.rho_v2_calc != null) {
      const tooLow =
        vals.rho_v2_min != null &&
        vals.rho_v2_min > 0 &&
        calcs.rho_v2_calc < vals.rho_v2_min;
      const tooHigh =
        vals.rho_v2_max != null && calcs.rho_v2_calc > vals.rho_v2_max;
      if (tooLow || tooHigh) {
        rv2CalcEl.classList.add("text-danger", "fw-semibold");
      }
    }
  }

  // -----------------------------------------------------------------------
  // Predict button: disable when every pipe already has state + criteria
  // -----------------------------------------------------------------------
  const btnPredict = document.getElementById("btn-predict");

  function updatePredictBtn() {
    const allFilled = Array.from(
      document.querySelectorAll(".pipe-row"),
    ).every(function (row) {
      const state = row.querySelector(".state-select")?.value;
      const crit = row.querySelector(".criteria-select")?.value;
      return state && crit;
    });
    btnPredict.disabled = allFilled;
    btnPredict.title = allFilled
      ? "All pipes already have State and Criteria assigned"
      : "Auto-fill state from liquid fraction (LF) and predict criteria where possible";
  }

  // -----------------------------------------------------------------------
  // Populate all criteria selects and value cells on page load
  // -----------------------------------------------------------------------
  document.querySelectorAll(".state-select").forEach(function (stateEl) {
    const pipe = stateEl.dataset.pipe;
    const savedCriteria = stateEl.dataset.savedCriteria || "";
    const criteriaEl = document.querySelector(
      `.criteria-select[data-pipe="${pipe}"]`,
    );
    const fluidType = stateEl.value;
    if (fluidType && criteriaEl) {
      criteriaEl.innerHTML = buildOptions(fluidType, savedCriteria);
    }
    updateCriteriaDisplay(pipe);
    checkCalcVsCriteria(pipe);
  });
  updatePredictBtn();

  // -----------------------------------------------------------------------
  // Populate calculated values (dp_calc, vel_calc, rho_v2_calc) on page load
  // -----------------------------------------------------------------------
  (function () {
    const fmtCalc = (v) => (v == null || v === 0 ? "-" : v.toFixed(2));
    const fmtRhoV2Calc = (v) => {
      if (v == null || v === 0) return "-";
      return v >= 1000 ? (v / 1000).toFixed(1) + "k" : v.toFixed(0);
    };
    document.querySelectorAll(".pipe-row").forEach(function (row) {
      const pipe = row.dataset.pipe;
      const c = PIPE_CALCS[pipe] || {};
      const rhov2CalcEl = row.querySelector(".calc-rhov2");
      const dpCalcEl = row.querySelector(".calc-dp");
      const velCalcEl = row.querySelector(".calc-vel");
      if (rhov2CalcEl) rhov2CalcEl.textContent = fmtRhoV2Calc(c.rho_v2_calc);
      if (dpCalcEl) dpCalcEl.textContent = fmtCalc(c.dp_calc);
      if (velCalcEl) velCalcEl.textContent = fmtCalc(c.vel_calc);
    });
  })();

  // -----------------------------------------------------------------------
  // State change → rebuild criteria dropdown + clear value cells
  // -----------------------------------------------------------------------
  document.querySelectorAll(".state-select").forEach(function (stateEl) {
    stateEl.addEventListener("change", function () {
      const pipe = this.dataset.pipe;
      const criteriaEl = document.querySelector(
        `.criteria-select[data-pipe="${pipe}"]`,
      );
      if (!criteriaEl) return;
      const fluidType = this.value;
      criteriaEl.innerHTML = fluidType
        ? buildOptions(fluidType, "")
        : '<option value="">-</option>';
      updateCriteriaDisplay(pipe);
      checkCalcVsCriteria(pipe);
      updatePredictBtn();
    });
  });

  // -----------------------------------------------------------------------
  // Criteria change → update value cells
  // -----------------------------------------------------------------------
  document
    .querySelectorAll(".criteria-select")
    .forEach(function (criteriaEl) {
      criteriaEl.addEventListener("change", function () {
        updateCriteriaDisplay(this.dataset.pipe);
        checkCalcVsCriteria(this.dataset.pipe);
        updatePredictBtn();
      });
    });

  // -----------------------------------------------------------------------
  // Checkbox selection helpers
  // -----------------------------------------------------------------------
  const selectAllCb = document.getElementById("select-all");
  const bulkLabel = document.getElementById("bulk-target-label");

  function visibleRows() {
    return Array.from(document.querySelectorAll(".pipe-row")).filter(
      (r) => r.style.display !== "none",
    );
  }

  function checkedRows() {
    return Array.from(document.querySelectorAll(".row-select:checked")).map(
      (cb) => cb.closest(".pipe-row"),
    );
  }

  function updateBulkUI() {
    const checked = document.querySelectorAll(".row-select:checked").length;
    const visible = visibleRows();
    const visibleChecked = visible.filter(
      (r) => r.querySelector(".row-select").checked,
    ).length;

    if (checked > 0) {
      bulkLabel.textContent = "Set selected rows:";
      bulkApplyBtn.textContent = `Apply to selected (${checked})`;
      bulkApplyBtn.classList.replace(
        "btn-outline-secondary",
        "btn-outline-primary",
      );
    } else {
      bulkLabel.textContent = "Set rows:";
      bulkApplyBtn.textContent = "Apply to visible";
      bulkApplyBtn.classList.replace(
        "btn-outline-primary",
        "btn-outline-secondary",
      );
    }

    // Master checkbox state
    if (visibleChecked === 0) {
      selectAllCb.checked = false;
      selectAllCb.indeterminate = false;
    } else if (visibleChecked === visible.length) {
      selectAllCb.checked = true;
      selectAllCb.indeterminate = false;
    } else {
      selectAllCb.checked = false;
      selectAllCb.indeterminate = true;
    }
  }

  // Select-all toggles all visible rows
  selectAllCb.addEventListener("change", function () {
    visibleRows().forEach(function (row) {
      row.querySelector(".row-select").checked = selectAllCb.checked;
    });
    updateBulkUI();
  });

  // Individual row checkbox
  document.querySelectorAll(".row-select").forEach(function (cb) {
    cb.addEventListener("change", updateBulkUI);
  });

  // -----------------------------------------------------------------------
  // Filter rows by pipe name
  // -----------------------------------------------------------------------
  const filterInput = document.getElementById("pipe-filter");
  filterInput.addEventListener("input", function () {
    const q = this.value.toLowerCase();
    document.querySelectorAll(".pipe-row").forEach(function (row) {
      const name = row.dataset.pipe.toLowerCase();
      row.style.display = name.includes(q) ? "" : "none";
    });
    updateBulkUI();
  });

  // -----------------------------------------------------------------------
  // Bulk-set toolbar: state changes → rebuild bulk criteria select
  // -----------------------------------------------------------------------
  const bulkState = document.getElementById("bulk-state");
  const bulkCriteria = document.getElementById("bulk-criteria");
  const bulkApplyBtn = document.getElementById("btn-bulk-apply");

  bulkState.addEventListener("change", function () {
    const ft = this.value;
    if (ft) {
      bulkCriteria.innerHTML = buildOptions(ft, "");
      bulkCriteria.disabled = false;
    } else {
      bulkCriteria.innerHTML = '<option value="">- Criteria -</option>';
      bulkCriteria.disabled = true;
    }
  });

  bulkApplyBtn.addEventListener("click", function () {
    const ft = bulkState.value;
    const crit = bulkCriteria.value;
    if (!ft) return;

    const targets = checkedRows().length > 0 ? checkedRows() : visibleRows();
    targets.forEach(function (row) {
      const pipe = row.dataset.pipe;
      const stateEl = row.querySelector(".state-select");
      const criteriaEl = row.querySelector(".criteria-select");
      if (!stateEl || !criteriaEl) return;
      stateEl.value = ft;
      criteriaEl.innerHTML = buildOptions(ft, crit);
      criteriaEl.value = crit;
      updateCriteriaDisplay(pipe);
      checkCalcVsCriteria(pipe);
    });
    updatePredictBtn();
  });

  // -----------------------------------------------------------------------
  // Clear all
  // -----------------------------------------------------------------------
  document
    .getElementById("btn-clear-all")
    .addEventListener("click", function () {
      document.querySelectorAll(".state-select").forEach(function (el) {
        el.value = "";
      });
      document.querySelectorAll(".criteria-select").forEach(function (el) {
        el.innerHTML = '<option value="">-</option>';
      });
      document
        .querySelectorAll(".crit-dp, .crit-vmin, .crit-vmax, .crit-rhov2")
        .forEach(function (el) {
          el.textContent = "-";
        });
      document
        .querySelectorAll(".calc-dp, .calc-vel, .calc-rhov2")
        .forEach(function (el) {
          el.classList.remove("text-danger", "fw-semibold");
        });
      document.querySelectorAll(".row-select").forEach(function (cb) {
        cb.checked = false;
      });
      selectAllCb.checked = false;
      selectAllCb.indeterminate = false;
      updateBulkUI();
      updatePredictBtn();
    });

  // -----------------------------------------------------------------------
  // Save / Set spinners
  // -----------------------------------------------------------------------
  document
    .getElementById("criteria-form")
    .addEventListener("submit", function (e) {
      document.getElementById("btn-set").disabled = true;
      document.getElementById("set-spinner").classList.remove("d-none");
    });

  // -----------------------------------------------------------------------
  // Auto-predict spinner
  // -----------------------------------------------------------------------
  document
    .getElementById("predict-form")
    .addEventListener("submit", function () {
      document.getElementById("btn-predict").disabled = true;
      document.getElementById("predict-spinner").classList.remove("d-none");
    });

  // -----------------------------------------------------------------------
  // Column sorting
  // -----------------------------------------------------------------------
  const tbody = document.querySelector("#criteria-table tbody");
  let sortDirection = {};
  let currentSort = null;

  const COL_SELECTOR = {
    index:        (row) => row.querySelector("td:nth-child(2)"),
    pipe:         (row) => row.querySelector("td:nth-child(3)"),
    state:        (row) => row.querySelector(".state-select"),
    criteria:     (row) => row.querySelector(".criteria-select"),
    dp_calc:      (row) => row.querySelector(".calc-dp"),
    dp_max:       (row) => row.querySelector(".crit-dp"),
    vel_calc:     (row) => row.querySelector(".calc-vel"),
    v_min:        (row) => row.querySelector(".crit-vmin"),
    v_max:        (row) => row.querySelector(".crit-vmax"),
    rho_v2_calc:  (row) => row.querySelector(".calc-rhov2"),
    rho_v2_range: (row) => row.querySelector(".crit-rhov2"),
  };

  function getCellValue(row, column) {
    const getter = COL_SELECTOR[column];
    if (!getter) return "";
    const cell = getter(row);
    if (!cell) return "";
    if (cell.tagName === "SELECT") return cell.value;
    const text = cell.textContent.trim();
    return text === "-" ? null : text;
  }

  function getNumericValue(value) {
    if (value === null || value === "") return -Infinity;
    const v = value.trim();
    if (v.endsWith("k")) return parseFloat(v) * 1000;
    const num = parseFloat(v.replace(/,/g, ""));
    return isNaN(num) ? -Infinity : num;
  }

  function sortRows(column, isAscending) {
    const rows = Array.from(tbody.querySelectorAll(".pipe-row"));
    const isNumeric = [
      "index",
      "dp_calc",
      "dp_max",
      "vel_calc",
      "v_min",
      "v_max",
      "rho_v2_calc",
      "rho_v2_range",
    ].includes(column);

    rows.sort((a, b) => {
      let valA = getCellValue(a, column);
      let valB = getCellValue(b, column);

      if (isNumeric) {
        valA = getNumericValue(valA);
        valB = getNumericValue(valB);
        return isAscending ? valA - valB : valB - valA;
      } else {
        valA = (valA || "").toLowerCase();
        valB = (valB || "").toLowerCase();
        if (valA < valB) return isAscending ? -1 : 1;
        if (valA > valB) return isAscending ? 1 : -1;
        return 0;
      }
    });

    rows.forEach((row) => tbody.appendChild(row));
  }

  function updateSortIcons(column) {
    document.querySelectorAll("th.sortable").forEach((th) => {
      if (th.dataset.column === column) {
        const isAsc = sortDirection[column];
        th.classList.remove("sort-asc", "sort-desc");
        th.classList.add(isAsc ? "sort-asc" : "sort-desc");
      } else {
        th.classList.remove("sort-asc", "sort-desc");
      }
    });
  }

  document.querySelectorAll("th.sortable").forEach((th) => {
    th.addEventListener("click", function (e) {
      if (e.target.closest("input")) return;
      const column = this.dataset.column;
      if (!column) return;

      if (currentSort === column) {
        sortDirection[column] = !sortDirection[column];
      } else {
        sortDirection[column] = true;
        currentSort = column;
      }

      sortRows(column, sortDirection[column]);
      updateSortIcons(column);
      updateBulkUI();
    });
  });
});
