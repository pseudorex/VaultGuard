// Recovery tracking & restoration download logic — Monochrome Edition
document.addEventListener("DOMContentLoaded", async () => {
  if (!API.isAuthenticated()) {
    window.location.href = "login.html";
    return;
  }

  API.renderNavbar("recovery");

  const recoveryTbody = document.getElementById("recovery-tbody");
  const emptyState = document.getElementById("recovery-empty-state");

  async function loadRequests() {
    try {
      const requests = await API.request("/recovery-requests");
      
      if (!requests || requests.length === 0) {
        if (recoveryTbody) recoveryTbody.innerHTML = "";
        if (emptyState) emptyState.style.display = "block";
        return;
      }

      if (emptyState) emptyState.style.display = "none";
      if (recoveryTbody) {
        recoveryTbody.innerHTML = requests.map(req => {
          let statusBadgeClass = "badge-pending";
          if (req.status === "APPROVED") statusBadgeClass = "badge-success";
          if (req.status === "COMPLETED") statusBadgeClass = "badge-admin";
          if (req.status === "REJECTED" || req.status === "FAILED") statusBadgeClass = "badge-danger";

          const approvalsList = req.approvals && req.approvals.length > 0 
            ? req.approvals.map(a => `
                <div style="font-size: 0.75rem; margin-top: 0.25rem;">
                  <span class="badge ${a.decision === 'APPROVE' ? 'badge-success' : 'badge-danger'}" style="font-size: 0.65rem; padding: 0.1rem 0.3rem;">${a.decision}</span>
                  <strong>${escapeHtml(a.custodian_name || 'Custodian')}</strong>: <span style="color: var(--text-muted);">${escapeHtml(a.comment || 'No comment')}</span>
                </div>
              `).join("")
            : '<span style="color: var(--text-muted); font-size: 0.8rem;">Awaiting custodian reviews...</span>';

          let actionContent = "";
          if (req.status === "APPROVED") {
            actionContent = `
              <button class="btn btn-primary btn-sm restore-btn" data-id="${req.id}">
                Restore & Download
              </button>
            `;
          } else if (req.status === "COMPLETED") {
            actionContent = `<span style="color: #ffffff; font-weight: 600; font-size: 0.8rem;">Restored</span>`;
          } else if (req.status === "PENDING") {
            actionContent = `<span style="color: var(--text-muted); font-size: 0.8rem;">Pending (${2 - req.approval_count} required)</span>`;
          } else {
            actionContent = `<span style="color: #f87171; font-size: 0.8rem;">${req.status}</span>`;
          }

          return `
            <tr>
              <td>
                <div style="font-weight: 600; color: #fff;">${escapeHtml(req.original_filename || req.backup_id)}</div>
                <div style="font-size: 0.75rem; color: var(--text-muted); font-family: var(--font-mono);">ID: ${req.id}</div>
                <div style="font-size: 0.8rem; color: var(--text-secondary); margin-top: 0.2rem;">Reason: "${escapeHtml(req.reason)}"</div>
              </td>
              <td>
                <span class="badge ${statusBadgeClass}">${req.status}</span>
                <div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 0.25rem; font-family: var(--font-mono);">
                  ${req.approval_count} of ${req.required_approvals} approvals
                </div>
              </td>
              <td>${approvalsList}</td>
              <td style="color: var(--text-secondary); font-size: 0.8rem; font-family: var(--font-mono);">
                ${API.formatDate(req.created_at)}
              </td>
              <td>${actionContent}</td>
            </tr>
          `;
        }).join("");

        document.querySelectorAll(".restore-btn").forEach(btn => {
          btn.addEventListener("click", async () => {
            const reqId = btn.dataset.id;
            try {
              btn.disabled = true;
              btn.innerText = "Reconstructing & Decrypting...";

              const response = await API.request(`/recovery-requests/${reqId}/restore`, {
                method: "POST",
              });

              let filename = "restored_file.dat";
              const disp = response.headers.get("Content-Disposition");
              if (disp && disp.includes("filename*=")) {
                const parts = disp.split("filename*=");
                if (parts[1]) filename = decodeURIComponent(parts[1].replace(/UTF-8''/i, '').replace(/["']/g, ''));
              } else if (disp && disp.includes("filename=")) {
                const match = disp.match(/filename="?([^"]+)"?/);
                if (match && match[1]) filename = match[1];
              }

              const blob = await response.blob();
              const downloadUrl = window.URL.createObjectURL(blob);
              const a = document.createElement("a");
              a.href = downloadUrl;
              a.download = filename;
              document.body.appendChild(a);
              a.click();
              a.remove();
              window.URL.revokeObjectURL(downloadUrl);

              API.showToast(`Restored "${filename}" successfully`, "success");
              loadRequests();
            } catch (err) {
              API.showToast(err.message, "error");
              btn.disabled = false;
              btn.innerText = "Restore & Download";
            }
          });
        });
      }
    } catch (err) {
      API.showToast(err.message, "error");
    }
  }

  function escapeHtml(text) {
    if (!text) return "";
    return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  loadRequests();
});
