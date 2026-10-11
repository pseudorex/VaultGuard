// VaultGuard API Client & Utilities — Minimalist Monochrome Edition
const API = {
  getToken() {
    return localStorage.getItem("vg_token");
  },

  setToken(token) {
    localStorage.setItem("vg_token", token);
  },

  getUser() {
    const userStr = localStorage.getItem("vg_user");
    try {
      return userStr ? JSON.parse(userStr) : null;
    } catch {
      return null;
    }
  },

  setUser(user) {
    localStorage.setItem("vg_user", JSON.stringify(user));
  },

  clearAuth() {
    localStorage.removeItem("vg_token");
    localStorage.removeItem("vg_user");
  },

  isAuthenticated() {
    return !!this.getToken();
  },

  async request(endpoint, options = {}) {
    const baseUrl = window.VAULTGUARD_CONFIG?.API_BASE_URL || "http://127.0.0.1:8000/api";
    const url = `${baseUrl}${endpoint.startsWith("/") ? endpoint : "/" + endpoint}`;

    const headers = {
      ...options.headers,
    };

    const token = this.getToken();
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    if (!(options.body instanceof FormData) && !headers["Content-Type"]) {
      headers["Content-Type"] = "application/json";
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      if (response.status === 401) {
        this.clearAuth();
        if (!window.location.pathname.endsWith("login.html") && !window.location.pathname.endsWith("register.html")) {
          window.location.href = "login.html";
        }
        throw new Error("Session expired. Please sign in again.");
      }

      const contentType = response.headers.get("Content-Type") || "";
      if (contentType.includes("application/octet-stream") || response.headers.get("Content-Disposition")) {
        if (!response.ok) {
          const errData = await response.json();
          throw new Error(errData.detail || "Download failed");
        }
        return response;
      }

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "An unexpected error occurred");
      }

      return data;
    } catch (err) {
      console.error(`API Error [${endpoint}]:`, err);
      throw err;
    }
  },

  // Toast Notification System with Minimalist SVGs
  showToast(message, type = "info") {
    let container = document.getElementById("toast-container");
    if (!container) {
      container = document.createElement("div");
      container.id = "toast-container";
      container.className = "toast-container";
      document.body.appendChild(container);
    }

    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    
    let iconSvg = `<svg class="icon-svg" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>`;
    if (type === "success") {
      iconSvg = `<svg class="icon-svg" viewBox="0 0 24 24"><path d="M20 6L9 17l-5-5"></path></svg>`;
    } else if (type === "error") {
      iconSvg = `<svg class="icon-svg" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>`;
    }

    toast.innerHTML = `<span>${iconSvg}</span> <span>${message}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = "0";
      toast.style.transition = "opacity 0.2s";
      setTimeout(() => toast.remove(), 200);
    }, 4000);
  },

  // Navbar Setup
  renderNavbar(activePage = "") {
    const user = this.getUser();
    const navRight = document.getElementById("navbar-right");
    const navLinks = document.getElementById("navbar-links");

    if (navLinks) {
      let linksHtml = `
        <li><a href="dashboard.html" class="nav-link ${activePage === 'dashboard' ? 'active' : ''}">Backups</a></li>
        <li><a href="recovery.html" class="nav-link ${activePage === 'recovery' ? 'active' : ''}">Recovery</a></li>
      `;

      if (user?.role === "CUSTODIAN" || user?.role === "ADMIN") {
        linksHtml += `<li><a href="custodian.html" class="nav-link ${activePage === 'custodian' ? 'active' : ''}">Custodian Queue</a></li>`;
      }

      linksHtml += `<li><a href="audit.html" class="nav-link ${activePage === 'audit' ? 'active' : ''}">Audit Ledger</a></li>`;
      navLinks.innerHTML = linksHtml;
    }

    if (navRight) {
      if (user) {
        let badgeClass = "badge-owner";
        if (user.role === "CUSTODIAN") badgeClass = "badge-custodian";
        if (user.role === "ADMIN") badgeClass = "badge-admin";

        navRight.innerHTML = `
          <div class="user-pill">
            <div class="user-avatar">${user.display_name.charAt(0).toUpperCase()}</div>
            <div style="display: flex; align-items: center; gap: 0.4rem;">
              <span style="font-size: 0.8rem; font-weight: 600; color: #fff;">${user.display_name}</span>
              <span class="badge ${badgeClass}" style="font-size: 0.65rem; padding: 0.1rem 0.35rem;">${user.role}</span>
            </div>
          </div>
          <button id="logout-btn" class="btn btn-outline btn-sm">Sign Out</button>
        `;

        document.getElementById("logout-btn")?.addEventListener("click", () => {
          API.clearAuth();
          window.location.href = "login.html";
        });
      } else {
        navRight.innerHTML = `
          <a href="login.html" class="btn btn-outline btn-sm">Sign In</a>
          <a href="register.html" class="btn btn-primary btn-sm">Register</a>
        `;
      }
    }
  },

  formatBytes(bytes, decimals = 2) {
    if (!+bytes) return '0 B';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`;
  },

  formatDate(dateStr) {
    if (!dateStr) return "-";
    const d = new Date(dateStr);
    return d.toLocaleString();
  }
};
