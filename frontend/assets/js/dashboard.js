// Dashboard logic — Monochrome Edition
document.addEventListener("DOMContentLoaded", async () => {
  if (!API.isAuthenticated()) {
    window.location.href = "login.html";
    return;
  }

  API.renderNavbar("dashboard");

  const backupsList = document.getElementById("backups-tbody");
  const emptyState = document.getElementById("empty-state");
  const statTotalBackups = document.getElementById("stat-total-backups");
  const statActiveBackups = document.getElementById("stat-active-backups");
  const uploadForm = document.getElementById("upload-form");
  const fileInput = document.getElementById("file-input");
  const dropzone = document.getElementById("dropzone");
  const fileNameDisplay = document.getElementById("file-name-display");

  async function loadBackups() {
    try {
      const backups = await API.request("/backups");
      
      if (statTotalBackups) statTotalBackups.innerText = backups.length;
      if (statActiveBackups) statActiveBackups.innerText = backups.filter(b => b.status === "ACTIVE").length;

      if (!backups || backups.length === 0) {
        if (backupsList) backupsList.innerHTML = "";
        if (emptyState) emptyState.style.display = "block";
        return;
      }

      if (emptyState) emptyState.style.display = "none";
      if (backupsList) {
        backupsList.innerHTML = backups.map(b => `
          <tr>
            <td>
              <div style="font-weight: 600; color: #fff;">${escapeHtml(b.original_filename)}</div>
              <div style="font-size: 0.75rem; color: var(--text-muted); font-family: var(--font-mono);">${b.id}</div>
            </td>
            <td>${API.formatBytes(b.size_bytes)}</td>
            <td>
              <span class="badge badge-info">${b.algorithm}</span>
              <span class="badge badge-custodian" style="font-size: 0.65rem;">2-of-3 Shamir</span>
            </td>
            <td>
              <span class="badge ${b.status === 'ACTIVE' ? 'badge-success' : 'badge-danger'}">
                ${b.status}
              </span>
            </td>
            <td style="color: var(--text-secondary); font-size: 0.8rem; font-family: var(--font-mono);">
              ${API.formatDate(b.created_at)}
            </td>
            <td>
              <div style="display: flex; gap: 0.4rem;">
                <a href="backup-details.html?id=${b.id}" class="btn btn-outline btn-sm">Inspect</a>
                <button class="btn btn-danger btn-sm delete-backup-btn" data-id="${b.id}">Delete</button>
              </div>
            </td>
          </tr>
        `).join("");

        document.querySelectorAll(".delete-backup-btn").forEach(btn => {
          btn.addEventListener("click", async () => {
            const id = btn.dataset.id;
            if (confirm("Permanently destroy this encrypted backup and all Shamir key shares?")) {
              try {
                await API.request(`/backups/${id}`, { method: "DELETE" });
                API.showToast("Backup and key shares deleted", "success");
                loadBackups();
              } catch (err) {
                API.showToast(err.message, "error");
              }
            }
          });
        });
      }
    } catch (err) {
      API.showToast(err.message, "error");
    }
  }

  // Handle Drag & Drop
  if (dropzone && fileInput) {
    dropzone.addEventListener("click", () => fileInput.click());

    dropzone.addEventListener("dragover", (e) => {
      e.preventDefault();
      dropzone.classList.add("dragover");
    });

    dropzone.addEventListener("dragleave", () => {
      dropzone.classList.remove("dragover");
    });

    dropzone.addEventListener("drop", (e) => {
      e.preventDefault();
      dropzone.classList.remove("dragover");
      if (e.dataTransfer.files.length > 0) {
        fileInput.files = e.dataTransfer.files;
        updateFileName();
      }
    });

    fileInput.addEventListener("change", updateFileName);

    function updateFileName() {
      if (fileInput.files && fileInput.files[0]) {
        const file = fileInput.files[0];
        if (fileNameDisplay) {
          fileNameDisplay.innerHTML = `Selected: <strong>${escapeHtml(file.name)}</strong> (${API.formatBytes(file.size)})`;
        }
      }
    }
  }

  // Handle Upload Form Submit
  if (uploadForm) {
    uploadForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      if (!fileInput.files || !fileInput.files[0]) {
        API.showToast("Please select a file to encrypt and backup", "error");
        return;
      }

      const file = fileInput.files[0];
      const formData = new FormData();
      formData.append("file", file);

      const submitBtn = uploadForm.querySelector('button[type="submit"]');
      try {
        submitBtn.disabled = true;
        submitBtn.innerText = "Encrypting & Partitioning Shares...";

        await API.request("/backups", {
          method: "POST",
          body: formData,
        });

        API.showToast("File encrypted and backed up with 2-of-3 threshold", "success");
        uploadForm.reset();
        if (fileNameDisplay) fileNameDisplay.innerHTML = "";
        
        document.getElementById("upload-modal")?.classList.remove("active");
        await loadBackups();
      } catch (err) {
        API.showToast(err.message, "error");
      } finally {
        submitBtn.disabled = false;
        submitBtn.innerText = "Encrypt & Store Backup";
      }
    });
  }

  // Upload Modal Open/Close
  const openUploadModalBtn = document.getElementById("open-upload-modal-btn");
  const uploadModal = document.getElementById("upload-modal");
  const closeUploadModalBtn = document.getElementById("close-upload-modal-btn");

  if (openUploadModalBtn && uploadModal) {
    openUploadModalBtn.addEventListener("click", () => {
      uploadModal.classList.add("active");
    });
  }

  if (closeUploadModalBtn && uploadModal) {
    closeUploadModalBtn.addEventListener("click", () => {
      uploadModal.classList.remove("active");
    });
  }

  function escapeHtml(text) {
    if (!text) return "";
    return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  loadBackups();
});
