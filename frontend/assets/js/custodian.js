// Custodian approval queue logic — Monochrome Edition
document.addEventListener("DOMContentLoaded", async () => {
  if (!API.isAuthenticated()) {
    window.location.href = "login.html";
    return;
  }

  const currentUser = API.getUser();
  if (currentUser?.role !== "CUSTODIAN" && currentUser?.role !== "ADMIN") {
    API.showToast("Access restricted: Custodian permissions required", "error");
    window.location.href = "dashboard.html";
    return;
  }

  API.renderNavbar("custodian");

  const queueTbody = document.getElementById("custodian-queue-tbody");
  const emptyState = document.getElementById("queue-empty-state");

  async function loadQueue() {
    try {
      const requests = await API.request("/recovery-requests");
      
      if (!requests || requests.length === 0) {
        if (queueTbody) queueTbody.innerHTML = "";
        if (emptyState) emptyState.style.display = "block";
        return;
      }

      if (emptyState) emptyState.style.display = "none";
      if (queueTbody) {
        queueTbody.innerHTML = requests.map(req => {
          const hasVoted = req.approvals && req.approvals.some(a => a.custodian_id === currentUser.id);
          const isPending = req.status === "PENDING";
          const isRequester = req.requester_id === currentUser.id;

          let actionsHtml = "";
          if (hasVoted) {
            actionsHtml = `<span class="badge badge-info">Voted</span>`;
          } else if (isRequester) {
            actionsHtml = `<span class="badge badge-pending">Requester (Separation of Duty)</span>`;
          } else if (!isPending) {
            actionsHtml = `<span class="badge badge-pending">Closed (${req.status})</span>`;
          } else {
            actionsHtml = `
              <div style="display: flex; gap: 0.4rem;">
                <button class="btn btn-primary btn-sm approve-btn" data-id="${req.id}">
                  Approve
                </button>
                <button class="btn btn-danger btn-sm reject-btn" data-id="${req.id}">
                  Reject
                </button>
              </div>
            `;
          }

          return `
            <tr>
              <td>
                <div style="font-weight: 600; color: #fff;">${escapeHtml(req.original_filename || req.backup_id)}</div>
                <div style="font-size: 0.75rem; color: var(--text-muted); font-family: var(--font-mono);">ID: ${req.id}</div>
              </td>
              <td style="color: var(--text-secondary); max-width: 250px;">
                "${escapeHtml(req.reason)}"
              </td>
              <td>
                <span class="badge ${req.status === 'APPROVED' ? 'badge-success' : req.status === 'PENDING' ? 'badge-pending' : 'badge-danger'}">
                  ${req.status}
                </span>
                <div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 0.2rem; font-family: var(--font-mono);">
                  ${req.approval_count} / ${req.required_approvals} approvals
                </div>
              </td>
              <td style="color: var(--text-secondary); font-size: 0.8rem; font-family: var(--font-mono);">
                ${API.formatDate(req.created_at)}
              </td>
              <td>${actionsHtml}</td>
            </tr>
          `;
        }).join("");

        document.querySelectorAll(".approve-btn").forEach(btn => {
          btn.addEventListener("click", () => handleVote(btn.dataset.id, "approve"));
        });

        document.querySelectorAll(".reject-btn").forEach(btn => {
          btn.addEventListener("click", () => handleVote(btn.dataset.id, "reject"));
        });
      }
    } catch (err) {
      API.showToast(err.message, "error");
    }
  }

  async function handleVote(requestId, decision) {
    const comment = prompt(`Enter optional comment for ${decision.toUpperCase()} decision:`, "");
    if (comment === null) return;

    try {
      await API.request(`/recovery-requests/${requestId}/${decision}`, {
        method: "POST",
        body: JSON.stringify({ comment: comment || undefined }),
      });

      API.showToast(`Decision recorded: ${decision.toUpperCase()}`, "success");
      loadQueue();
    } catch (err) {
      API.showToast(err.message, "error");
    }
  }

  function escapeHtml(text) {
    if (!text) return "";
    return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  loadQueue();
});
