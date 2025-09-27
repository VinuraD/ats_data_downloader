// Crypto Data Downloader - Frontend JavaScript

class CryptoDownloader {
  constructor() {
    this.socket = null;
    this.jobs = {};
    this.selectedSymbol = null;
    this.resolutions = [];
    this.currentPlotRendered = false;
    this.deleteModal = null;
    this.deleteModalMessageEl = null;
    this.deleteModalWarningEl = null;
    this.deleteModalConfirmBtn = null;
    this.pendingDeleteJobId = null;

    this.init();
  }

  init() {
    this.initSocketIO();
    this.loadResolutions();
    this.bindEvents();
    this.initDatePickers();
    this.initDeleteModal();
    this.loadJobs();
  }

  initSocketIO() {
    this.socket = io();

    this.socket.on("connect", () => {
      console.log("Connected to server");
    });

    this.socket.on("disconnect", () => {
      console.log("Disconnected from server");
    });

    this.socket.on("job_update", (jobData) => {
      console.log("Job update received:", jobData);
      this.updateJob(jobData);
    });
  }

  async loadResolutions() {
    try {
      const response = await fetch("/api/resolutions");
      const data = await response.json();

      if (data.success) {
        this.resolutions = data.resolutions;
        this.populateResolutionSelect();
      }
    } catch (error) {
      console.error("Error loading resolutions:", error);
    }
  }

  populateResolutionSelect() {
    const select = document.getElementById("resolution");
    select.innerHTML = '<option value="">Select resolution...</option>';

    // Group by category
    const categories = {};
    this.resolutions.forEach((res) => {
      if (!categories[res.category]) {
        categories[res.category] = [];
      }
      categories[res.category].push(res);
    });

    // Add optgroups
    Object.keys(categories).forEach((category) => {
      const optgroup = document.createElement("optgroup");
      optgroup.label = category;

      categories[category].forEach((res) => {
        const option = document.createElement("option");
        option.value = res.id;
        option.textContent = res.name;
        optgroup.appendChild(option);
      });

      select.appendChild(optgroup);
    });
  }

  bindEvents() {
    // Symbol search
    const symbolSearch = document.getElementById("symbol-search");
    const searchBtn = document.getElementById("search-btn");

    symbolSearch.addEventListener("input", (e) => {
      this.debounce(() => this.searchSymbols(e.target.value), 300)();
    });

    searchBtn.addEventListener("click", () => {
      this.searchSymbols(symbolSearch.value);
    });

    // Download form
    const downloadForm = document.getElementById("download-form");
    downloadForm.addEventListener("submit", (e) => {
      e.preventDefault();
      this.startDownload();
    });

    // Refresh jobs
    const refreshBtn = document.getElementById("refresh-jobs");
    refreshBtn.addEventListener("click", () => {
      this.loadJobs();
    });

    // Plot modal lifecycle events
    const plotModalEl = document.getElementById("plotModal");
    if (plotModalEl) {
      plotModalEl.addEventListener("shown.bs.modal", () => {
        if (this.currentPlotRendered) {
          setTimeout(() => {
            Plotly.Plots.resize("plot-container");
          }, 0);
        }
      });
      plotModalEl.addEventListener("hidden.bs.modal", () => {
        if (this.currentPlotRendered) {
          Plotly.purge("plot-container");
          this.currentPlotRendered = false;
        }
        const plotContainer = document.getElementById("plot-container");
        if (plotContainer) {
          plotContainer.innerHTML = `
            <div class="d-flex justify-content-center align-items-center h-100">
              <div class="spinner-border" role="status">
                <span class="visually-hidden">Loading chart...</span>
              </div>
            </div>
          `;
        }
        const plotInfo = document.getElementById("plot-info");
        if (plotInfo) {
          plotInfo.innerHTML = "";
        }
      });
    }
  }

  initDeleteModal() {
    const modalEl = document.getElementById("deleteModal");
    if (!modalEl) {
      return;
    }

    this.deleteModal = new bootstrap.Modal(modalEl);
    this.deleteModalMessageEl = document.getElementById("delete-modal-message");
    this.deleteModalWarningEl = document.getElementById("delete-modal-warning");
    this.deleteModalConfirmBtn = document.getElementById("confirm-delete-btn");

    if (this.deleteModalConfirmBtn) {
      this.deleteModalConfirmBtn.addEventListener("click", async () => {
        if (!this.pendingDeleteJobId) {
          return;
        }
        try {
          this.deleteModalConfirmBtn.disabled = true;
          this.deleteModalConfirmBtn.innerHTML =
            '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Deleting...';
          await this.deleteJob(this.pendingDeleteJobId, true);
        } finally {
          this.deleteModalConfirmBtn.disabled = false;
          this.deleteModalConfirmBtn.innerHTML =
            '<i class="bi bi-trash"></i> Delete';
        }
      });
    }

    modalEl.addEventListener("hidden.bs.modal", () => {
      this.pendingDeleteJobId = null;
      if (this.deleteModalWarningEl) {
        this.deleteModalWarningEl.classList.add("d-none");
      }
    });
  }

  debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  }

  async searchSymbols(query) {
    if (!query || query.length < 2) {
      document.getElementById("symbol-results").innerHTML = "";
      return;
    }

    try {
      const response = await fetch(
        `/api/symbols?search=${encodeURIComponent(query)}`,
      );
      const data = await response.json();

      if (data.success) {
        this.displaySymbolResults(data.symbols);
      }
    } catch (error) {
      console.error("Error searching symbols:", error);
    }
  }

  displaySymbolResults(symbols) {
    const container = document.getElementById("symbol-results");

    if (symbols.length === 0) {
      container.innerHTML =
        '<small class="text-muted">No symbols found</small>';
      return;
    }

    const html = symbols
      .map(
        (symbol) => `
            <div class="symbol-result" data-symbol="${symbol.symbol_id}">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <strong>${symbol.asset_id_base}/${symbol.asset_id_quote}</strong>
                        <div class="symbol-exchange">${symbol.exchange_id}</div>
                    </div>
                    <small class="text-muted">${symbol.symbol_id}</small>
                </div>
            </div>
        `,
      )
      .join("");

    container.innerHTML = html;

    // Bind click events
    container.querySelectorAll(".symbol-result").forEach((element) => {
      element.addEventListener("click", () => {
        this.selectSymbol(element.dataset.symbol, element);
      });
    });
  }

  selectSymbol(symbolId, element) {
    // Update UI
    document.querySelectorAll(".symbol-result").forEach((el) => {
      el.classList.remove("selected");
    });
    element.classList.add("selected");

    // Update form
    document.getElementById("selected-symbol").value = symbolId;
    document.getElementById("symbol-search").value = symbolId;
    this.selectedSymbol = symbolId;

    // Clear results after selection
    setTimeout(() => {
      document.getElementById("symbol-results").innerHTML = "";
    }, 1000);
  }

  initDatePickers() {
    const startInput = document.getElementById("start-date");
    const endInput = document.getElementById("end-date");

    if (!startInput || !endInput) {
      return;
    }

    const today = new Date();
    const commonOptions = {
      format: "yyyy-mm-dd",
      autoclose: true,
      todayHighlight: true,
      clearBtn: true,
      endDate: today, // Prevent future date selection
    };

    window.jQuery(startInput).datepicker(commonOptions);
    window.jQuery(endInput).datepicker(commonOptions);

    window.jQuery(startInput).on("changeDate", (e) => {
      const selectedDate = e.format("yyyy-mm-dd");
      window.jQuery(endInput).datepicker("setStartDate", selectedDate);
    });

    window.jQuery(endInput).on("changeDate", (e) => {
      const selectedDate = e.format("yyyy-mm-dd");
      window.jQuery(startInput).datepicker("setEndDate", selectedDate);
    });
  }

  async startDownload() {
    const form = document.getElementById("download-form");
    const formData = new FormData(form);

    if (!this.selectedSymbol) {
      this.showAlert("Please select a trading pair", "warning");
      return;
    }

    const startDate = formData.get("start_date");
    const endDate = formData.get("end_date");

    if (!startDate || !endDate) {
      this.showAlert("Please select both start and end dates", "warning");
      return;
    }

    const downloadData = {
      symbol: this.selectedSymbol,
      period_id: formData.get("period_id"),
      start_date: startDate,
      end_date: endDate,
    };

    if (!downloadData.period_id) {
      this.showAlert("Please select a resolution", "warning");
      return;
    }

    try {
      const downloadBtn = document.getElementById("download-btn");
      downloadBtn.disabled = true;
      downloadBtn.innerHTML =
        '<i class="bi bi-hourglass-split"></i> Starting...';

      const response = await fetch("/api/jobs", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(downloadData),
      });

      const data = await response.json();

      if (data.success) {
        this.showAlert("Download started successfully!", "success");
        form.reset();
        this.selectedSymbol = null;
        document.getElementById("selected-symbol").value = "";
        this.resetDatePickers();
      } else {
        this.showAlert(`Error: ${data.error}`, "danger");
      }
    } catch (error) {
      console.error("Error starting download:", error);
      this.showAlert("Failed to start download", "danger");
    } finally {
      const downloadBtn = document.getElementById("download-btn");
      downloadBtn.disabled = false;
      downloadBtn.innerHTML = '<i class="bi bi-download"></i> Start Download';
    }
  }

  async loadJobs() {
    try {
      const response = await fetch("/api/jobs");
      const data = await response.json();

      if (data.success) {
        this.displayJobs(data.jobs);
      }
    } catch (error) {
      console.error("Error loading jobs:", error);
    }
  }

  displayJobs(jobs) {
    const container = document.getElementById("jobs-container");

    if (jobs.length === 0) {
      container.innerHTML = `
        <div class="text-center text-muted py-4 empty-state">
          <i class="bi bi-inbox" style="font-size: 2rem;"></i>
          <p class="mt-2">No download jobs yet</p>
          <small>Start a download to see jobs here</small>
        </div>
      `;
      this.jobs = {};
      return;
    }

    this.jobs = {};
    const html = jobs
      .map((job) => {
        this.jobs[job.job_id] = job;
        return this.createJobHTML(job);
      })
      .join("");
    container.innerHTML = html;

    // Bind job actions
    this.bindJobActions();
  }

  createJobHTML(job) {
    const statusClass = `status-${job.status}`;
    let statusText = job.status.charAt(0).toUpperCase() + job.status.slice(1);

    // Handle missing data
    if (
      job.status === "completed" &&
      job.error &&
      job.error.includes("File not found")
    ) {
      statusText += " (Missing Data)";
    }

    const createdAt = job.started_at
      ? new Date(job.started_at).toLocaleString()
      : "Start time unavailable";
    const dateInfo =
      job.start_date && job.end_date
        ? `${job.start_date} → ${job.end_date}`
        : job.start_date
          ? `From ${job.start_date}`
          : job.end_date
            ? `Until ${job.end_date}`
            : "Date range not specified";
    const candleInfo = job.candle_count ? `${job.candle_count} candles` : "";
    const messageText = job.message || "";

    return `
      <div class="card mb-3 job-item" data-job-id="${job.job_id}">
        <div class="card-body">
          <div class="row align-items-center">
            <div class="col-md-3">
              <h6 class="mb-1">${job.symbol}</h6>
              <small class="text-muted">${job.period_id}</small>
            </div>
            <div class="col-md-3">
              <span class="badge ${statusClass}">${statusText}</span>
              <br /><small class="text-muted">${createdAt}</small>
            </div>
            <div class="col-md-3">
              <div class="text-muted small">${dateInfo}</div>
              ${candleInfo ? `<div class="text-muted small">${candleInfo}</div>` : ""}
            </div>
            <div class="col-md-3 text-end">
              <div class="btn-group">
                ${
                  job.status === "completed" &&
                  !(job.error && job.error.includes("File not found"))
                    ? `
                      <button class="btn btn-sm btn-outline-info job-view-btn" data-job-id="${job.job_id}" title="View">
                        <i class="bi bi-eye"></i>
                      </button>
                      <button class="btn btn-sm btn-outline-success job-download-btn" data-job-id="${job.job_id}" title="Download">
                        <i class="bi bi-download"></i>
                      </button>
                    `
                    : ""
                }
                <button class="btn btn-sm btn-outline-danger job-delete-btn" data-job-id="${job.job_id}" title="Delete">
                  <i class="bi bi-trash"></i>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    `;
  }

  updateJob(jobData) {
    const existingJobElement = document.querySelector(
      `[data-job-id="${jobData.job_id}"]`,
    );

    this.jobs[jobData.job_id] = jobData;

    if (existingJobElement) {
      // Update existing job
      const html = this.createJobHTML(jobData);
      existingJobElement.outerHTML = html;
    } else {
      // Add new job
      const container = document.getElementById("jobs-container");
      if (container.querySelector(".empty-state")) {
        container.innerHTML = "";
      }

      const html = this.createJobHTML(jobData);
      container.insertAdjacentHTML("afterbegin", html);

      // Add animation class
      const newJobElement = container.querySelector(
        `[data-job-id="${jobData.job_id}"]`,
      );
      newJobElement.classList.add("new");
    }

    // Re-bind actions
    this.bindJobActions();
  }

  bindJobActions() {
    // View buttons
    document.querySelectorAll(".job-view-btn").forEach((btn) => {
      btn.addEventListener("click", async (e) => {
        const jobId = e.target.closest("[data-job-id]").dataset.jobId;
        await this.viewPlot(jobId);
      });
    });

    // Download buttons
    document.querySelectorAll(".job-download-btn").forEach((btn) => {
      btn.addEventListener("click", async (e) => {
        const jobId = e.target.closest("[data-job-id]").dataset.jobId;
        window.open(`/api/download/${jobId}`, "_blank");
      });
    });

    // Delete buttons
    document.querySelectorAll(".job-delete-btn").forEach((btn) => {
      btn.addEventListener("click", async (e) => {
        const jobId = e.target.closest("[data-job-id]").dataset.jobId;
        const job = this.jobs[jobId];
        this.pendingDeleteJobId = jobId;
        if (this.deleteModalMessageEl) {
          const dateInfo =
            job.start_date && job.end_date
              ? `from <strong>${job.start_date}</strong> to <strong>${job.end_date}</strong>`
              : "";
          this.deleteModalMessageEl.innerHTML = `Are you sure you want to delete the download job for <strong>${job.symbol}</strong> (${job.period_id})${dateInfo ? ` ${dateInfo}` : ""}?`;
        }
        if (
          this.deleteModalWarningEl &&
          job.status === "completed" &&
          job.error &&
          job.error.includes("File not found")
        ) {
          this.deleteModalWarningEl.classList.remove("d-none");
        } else if (this.deleteModalWarningEl) {
          this.deleteModalWarningEl.classList.add("d-none");
        }
        if (this.deleteModal) {
          this.deleteModal.show();
        }
      });
    });
  }

  async deleteJob(jobId, fromModal = false) {
    try {
      const response = await fetch(`/api/jobs/${jobId}`, {
        method: "DELETE",
      });

      const data = await response.json();

      if (data.success) {
        // Remove from UI
        const jobElement = document.querySelector(`[data-job-id="${jobId}"]`);
        if (jobElement) {
          jobElement.remove();
        }

        // Remove from cache
        delete this.jobs[jobId];

        // Check if no jobs left
        const container = document.getElementById("jobs-container");
        if (!container.querySelector(".job-item")) {
          this.displayJobs([]);
        }

        this.showAlert("Job deleted successfully", "success");
        if (fromModal && this.deleteModal) {
          this.deleteModal.hide();
        }
      } else {
        this.showAlert(`Error: ${data.error}`, "danger");
      }
    } catch (error) {
      console.error("Error deleting job:", error);
      this.showAlert("Failed to delete job", "danger");
    }
  }

  async viewPlot(jobId) {
    try {
      // Show modal with loading spinner
      const modal = new bootstrap.Modal(document.getElementById("plotModal"));
      const plotContainer = document.getElementById("plot-container");
      const plotInfo = document.getElementById("plot-info");

      // Reset container
      plotContainer.innerHTML = `
                <div class="d-flex justify-content-center align-items-center h-100">
                    <div class="spinner-border" role="status">
                        <span class="visually-hidden">Loading chart...</span>
                    </div>
                </div>
            `;
      plotInfo.innerHTML = "";

      modal.show();

      // Fetch plot data
      console.log(`Fetching plot data for job: ${jobId}`);
      const response = await fetch(`/api/view/${jobId}`);
      console.log(`API response status: ${response.status}`);

      const data = await response.json();
      console.log("API response data:", data);

      if (data.success) {
        // Update modal title
        document.getElementById("plotModalLabel").innerHTML = `
                    <i class="bi bi-graph-up"></i>
                    ${data.job_info.symbol} - ${data.job_info.period_id}
                `;

        // Clear loading spinner
        Plotly.purge("plot-container");
        plotContainer.innerHTML = "";

        console.log("Creating Plotly chart...");
        console.log("Plot data structure:", data.plot_data);

        // Create Plotly chart
        try {
          await Plotly.newPlot(
            "plot-container",
            data.plot_data.data,
            data.plot_data.layout,
            {
              responsive: true,
              displayModeBar: true,
              modeBarButtonsToRemove: ["pan2d", "lasso2d", "select2d"],
              displaylogo: false,
            },
          );
          Plotly.Plots.resize("plot-container");
          this.currentPlotRendered = true;
          console.log("✅ Chart created successfully");
        } catch (plotError) {
          console.error("❌ Error creating chart:", plotError);
          plotContainer.innerHTML = `
                        <div class="alert alert-danger">
                            <i class="bi bi-exclamation-triangle"></i>
                            Error rendering chart: ${plotError.message}
                        </div>
                    `;
          return;
        }

        // Show job info
        plotInfo.innerHTML = `
                    <div class="alert alert-info">
                        <strong>Data Info:</strong> 
                        ${data.job_info.records} records | 
                        ${data.job_info.limit} candles requested |
                        Resolution: ${data.job_info.period_id}
                    </div>
                `;
      } else {
        console.error("API error:", data.error);
        plotContainer.innerHTML = `
                    <div class="alert alert-danger">
                        <i class="bi bi-exclamation-triangle"></i>
                        Failed to load chart: ${data.error}
                    </div>
                `;
      }
    } catch (error) {
      console.error("Error viewing plot:", error);
      this.currentPlotRendered = false;
      Plotly.purge("plot-container");
      document.getElementById("plot-container").innerHTML = `
                <div class="alert alert-danger">
                    <i class="bi bi-exclamation-triangle"></i>
                    Error loading chart: ${error.message}
                </div>
            `;
    }
  }

  showAlert(message, type) {
    // Create alert element
    const alert = document.createElement("div");
    alert.className = `alert alert-${type} alert-dismissible fade show`;
    alert.style.position = "fixed";
    alert.style.top = "20px";
    alert.style.right = "20px";
    alert.style.zIndex = "9999";
    alert.style.minWidth = "300px";

    alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

    document.body.appendChild(alert);

    // Auto remove after 5 seconds
    setTimeout(() => {
      if (alert.parentNode) {
        alert.remove();
      }
    }, 5000);
  }

  resetDatePickers() {
    const startInput = document.getElementById("start-date");
    const endInput = document.getElementById("end-date");

    if (startInput && endInput) {
      window.jQuery(startInput).datepicker("clearDates");
      window.jQuery(endInput).datepicker("clearDates");
      window.jQuery(endInput).datepicker("setStartDate", null);
      window.jQuery(startInput).datepicker("setEndDate", null);
    }
  }
}

// Initialize app when DOM is loaded
document.addEventListener("DOMContentLoaded", () => {
  new CryptoDownloader();
});
