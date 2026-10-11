// Backup details and integrity inspection — Forest Green Edition
document.addEventListener("DOMContentLoaded", async () => {
  if (!API.isAuthenticated()) {
    window.location.href = "login.html";
    return;
  }

  API.renderNavbar("dashboard");

  const urlParams = new URLSearchParams(window.location.search);
  const backupId = urlParams.get("id");

  if (!backupId) {
    API.showToast("No backup specified", "error");
    window.location.href = "dashboard.html";
    return;
  }

  const filenameEl = document.getElementById("backup-filename");
  const idEl = document.getElementById("backup-id");
  const sizeEl = document.getElementById("backup-size");
  const algEl = document.getElementById("backup-alg");
  const statusEl = document.getElementById("backup-status");
  const createdEl = document.getElementById("backup-created");
  const verifyBtn = document.getElementById("verify-integrity-btn");
  const verifyResultBox = document.getElementById("verify-result-box");
  const recoveryReasonInput = document.getElementById("recovery-reason");
  const requestRecoveryForm = document.getElementById("request-recovery-form");

  async function loadDetails() {
    try {
      const backup = await API.request(`/backups/${backupId}`);
      if (filenameEl) filenameEl.innerText = backup.original_filename;
      if (idEl) idEl.innerText = backup.id;
      if (sizeEl) sizeEl.innerText = API.formatBytes(backup.size_bytes);
      if (algEl) algEl.innerText = backup.algorithm;
      if (statusEl) {
        statusEl.className = `badge ${backup.status === 'ACTIVE' ? 'badge-success' : 'badge-danger'}`;
        statusEl.innerText = backup.status;
      }
      if (createdEl) createdEl.innerText = API.formatDate(backup.created_at);
    } catch (err) {
      API.showToast(err.message, "error");
    }
  }

  // Handle Live Integrity Verification
  if (verifyBtn) {
    verifyBtn.addEventListener("click", async () => {
      try {
        verifyBtn.disabled = true;
        verifyBtn.innerHTML = `<span>Reconstructing 2-of-3 Key & Authenticating...</span>`;

        const result = await API.request(`/backups/${backupId}/verify`, { method: "POST" });

        if (verifyResultBox) {
          verifyResultBox.style.display = "block";
          if (result.is_valid) {
            verifyResultBox.className = "card";
            verifyResultBox.style.border = "1px solid #86efac";
            verifyResultBox.style.background = "#f0fdf4";
            verifyResultBox.innerHTML = `
              <div style="display: flex; align-items: flex-start; gap: 0.85rem;">
                <div style="width: 32px; height: 32px; background: #dcfce7; border: 1px solid #86efac; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: #15803d; font-weight: 800; font-size: 0.9rem;">✓</div>
                <div>
                  <div style="font-weight: 800; color: #166534; font-size: 1rem;">STATUS: ${result.status}</div>
                  <div style="font-size: 0.88rem; color: #1f2937; margin-top: 0.25rem;">${result.message}</div>
                  <div style="font-size: 0.78rem; color: #4b5563; margin-top: 0.4rem; font-family: var(--font-mono);">
                    Checked at: ${API.formatDate(result.checked_at)} | Scheme: AES-256-GCM + 2-of-3 Shamir
                  </div>
                </div>
              </div>
            `;
          } else {
            verifyResultBox.className = "card";
            verifyResultBox.style.border = "1px solid #fca5a5";
            verifyResultBox.style.background = "#fef2f2";
            verifyResultBox.innerHTML = `
              <div style="display: flex; align-items: flex-start; gap: 0.85rem;">
                <div style="width: 32px; height: 32px; background: #fee2e2; border: 1px solid #fca5a5; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: #b91c1c; font-weight: 800; font-size: 0.9rem;">!</div>
                <div>
                  <div style="font-weight: 800; color: #991b1b; font-size: 1rem;">INTEGRITY VIOLATION DETECTED: ${result.status}</div>
                  <div style="font-size: 0.88rem; color: #7f1d1d; margin-top: 0.25rem;">${result.message}</div>
                  <div style="font-size: 0.78rem; color: #6b7280; margin-top: 0.4rem; font-family: var(--font-mono);">
                    Checked at: ${API.formatDate(result.checked_at)}
                  </div>
                </div>
              </div>
            `;
          }
        }
      } catch (err) {
        API.showToast(err.message, "error");
      } finally {
        verifyBtn.disabled = false;
        verifyBtn.innerHTML = `
          <svg style="width: 16px; height: 16px; stroke: currentColor; fill: none; stroke-width: 2.2;" viewBox="0 0 24 24">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
            <path d="M9 12l2 2 4-4"></path>
          </svg>
          <span>Run Cryptographic Integrity Check</span>
        `;
      }
    });
  }

  // Handle Recovery Request Submission
  if (requestRecoveryForm) {
    requestRecoveryForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const reason = recoveryReasonInput.value;
      const submitBtn = requestRecoveryForm.querySelector('button[type="submit"]');

      try {
        submitBtn.disabled = true;
        submitBtn.innerText = "Submitting Request...";

        await API.request(`/backups/${backupId}/recovery-requests`, {
          method: "POST",
          body: JSON.stringify({ reason }),
        });

        API.showToast("Recovery request created for custodian review", "success");
        setTimeout(() => {
          window.location.href = "recovery.html";
        }, 600);
      } catch (err) {
        API.showToast(err.message, "error");
      } finally {
        submitBtn.disabled = false;
        submitBtn.innerText = "Submit Recovery Request";
      }
    });
  }

  loadDetails();
});
