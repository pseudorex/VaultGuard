// Audit ledger and cryptographic hash-chain verifier — Forest Green Edition
document.addEventListener("DOMContentLoaded", async () => {
  if (!API.isAuthenticated()) {
    window.location.href = "login.html";
    return;
  }

  API.renderNavbar("audit");

  const auditTbody = document.getElementById("audit-tbody");
  const emptyState = document.getElementById("audit-empty-state");
  const verifyChainBtn = document.getElementById("verify-chain-btn");
  const chainResultBox = document.getElementById("chain-result-box");

  async function loadAuditEvents() {
    try {
      const events = await API.request("/audit-events?limit=100");

      if (!events || events.length === 0) {
        if (auditTbody) auditTbody.innerHTML = "";
        if (emptyState) emptyState.style.display = "block";
        return;
      }

      if (emptyState) emptyState.style.display = "none";
      if (auditTbody) {
        auditTbody.innerHTML = events.map(ev => {
          let outcomeBadge = "badge-success";
          if (ev.outcome === "FAILURE" || ev.outcome === "TAMPERED") outcomeBadge = "badge-danger";

          return `
            <tr>
              <td style="font-size: 0.8rem; color: var(--text-secondary); white-space: nowrap; font-family: var(--font-mono);">
                ${API.formatDate(ev.timestamp)}
              </td>
              <td>
                <div style="font-weight: 700; color: var(--brand-dark);">${escapeHtml(ev.actor_name || 'System / Anonymous')}</div>
                <div style="font-size: 0.75rem; color: var(--text-muted); font-family: var(--font-mono);">${ev.actor_id ? ev.actor_id.slice(0, 8) + '...' : 'SYSTEM'}</div>
              </td>
              <td>
                <span class="badge badge-info" style="font-family: var(--font-mono); font-size: 0.7rem;">${ev.action}</span>
              </td>
              <td style="font-size: 0.85rem; color: var(--text-secondary);">
                ${ev.target_type} ${ev.target_id ? `(${ev.target_id.slice(0, 8)}...)` : ''}
              </td>
              <td>
                <span class="badge ${outcomeBadge}">${ev.outcome}</span>
              </td>
              <td>
                <div style="display: flex; flex-direction: column; gap: 0.25rem;">
                  <div style="font-size: 0.72rem; color: var(--text-muted);">
                    Prev: <span class="hash-pill" title="${ev.previous_hash}">${ev.previous_hash.slice(0, 12)}...</span>
                  </div>
                  <div style="font-size: 0.72rem; color: var(--text-muted);">
                    Curr: <span class="hash-pill" style="color: #15803d; border-color: #86efac; background: #f0fdf4;" title="${ev.event_hash}">${ev.event_hash.slice(0, 12)}...</span>
                  </div>
                </div>
              </td>
            </tr>
          `;
        }).join("");
      }
    } catch (err) {
      API.showToast(err.message, "error");
    }
  }

  // Handle Hash Chain Verification
  if (verifyChainBtn) {
    verifyChainBtn.addEventListener("click", async () => {
      try {
        verifyChainBtn.disabled = true;
        verifyChainBtn.innerHTML = `<span>Verifying Cryptographic Chain...</span>`;

        const result = await API.request("/audit-events/verify-chain", {
          method: "POST",
        });

        if (chainResultBox) {
          chainResultBox.style.display = "block";
          if (result.is_valid) {
            chainResultBox.className = "card";
            chainResultBox.style.border = "1px solid #86efac";
            chainResultBox.style.background = "#f0fdf4";
            chainResultBox.innerHTML = `
              <div style="display: flex; align-items: flex-start; gap: 0.85rem;">
                <div style="width: 32px; height: 32px; background: #dcfce7; border: 1px solid #86efac; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: #15803d; font-weight: 800; font-size: 0.9rem;">✓</div>
                <div>
                  <div style="font-weight: 800; color: #166534; font-size: 1rem;">
                    AUDIT HASH CHAIN: VERIFIED & UNBROKEN
                  </div>
                  <div style="font-size: 0.88rem; color: #1f2937; margin-top: 0.25rem;">
                    ${result.message}
                  </div>
                  <div style="font-size: 0.78rem; color: #4b5563; margin-top: 0.4rem; font-family: var(--font-mono);">
                    Verified Events: ${result.total_events} | Genesis: ${result.genesis_hash.slice(0, 12)}... | Latest Hash: ${result.latest_hash ? result.latest_hash.slice(0, 16) + '...' : 'N/A'}
                  </div>
                </div>
              </div>
            `;
          } else {
            chainResultBox.className = "card";
            chainResultBox.style.border = "1px solid #fca5a5";
            chainResultBox.style.background = "#fef2f2";
            chainResultBox.innerHTML = `
              <div style="display: flex; align-items: flex-start; gap: 0.85rem;">
                <div style="width: 32px; height: 32px; background: #fee2e2; border: 1px solid #fca5a5; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: #b91c1c; font-weight: 800; font-size: 0.9rem;">!</div>
                <div>
                  <div style="font-weight: 800; color: #991b1b; font-size: 1rem;">
                    HASH CHAIN CORRUPTION OR TAMPERING DETECTED
                  </div>
                  <div style="font-size: 0.88rem; color: #7f1d1d; margin-top: 0.25rem;">
                    ${result.message}
                  </div>
                  <div style="font-size: 0.78rem; color: #6b7280; margin-top: 0.4rem; font-family: var(--font-mono);">
                    Broken at Event ID: <span class="hash-pill" style="color: #b91c1c; border-color: #fca5a5; background: #fee2e2;">${result.broken_event_id}</span>
                  </div>
                </div>
              </div>
            `;
          }
        }
      } catch (err) {
        API.showToast(err.message, "error");
      } finally {
        verifyChainBtn.disabled = false;
        verifyChainBtn.innerHTML = `
          <svg style="width: 16px; height: 16px; stroke: currentColor; fill: none; stroke-width: 2.2;" viewBox="0 0 24 24">
            <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path>
            <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path>
          </svg>
          <span>Verify Hash Chain Integrity</span>
        `;
      }
    });
  }

  function escapeHtml(text) {
    if (!text) return "";
    return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  loadAuditEvents();
});
