// Authentication logic — Forest Green Edition
document.addEventListener("DOMContentLoaded", () => {
  const loginForm = document.getElementById("login-form");
  const registerForm = document.getElementById("register-form");

  // Redirect if already authenticated
  if (API.isAuthenticated() && (loginForm || registerForm)) {
    window.location.href = "dashboard.html";
    return;
  }

  // Handle Login
  if (loginForm) {
    loginForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const email = document.getElementById("email").value;
      const password = document.getElementById("password").value;
      const submitBtn = loginForm.querySelector('button[type="submit"]');

      try {
        submitBtn.disabled = true;
        submitBtn.innerHTML = `<span>Authenticating...</span>`;

        const data = await API.request("/auth/login", {
          method: "POST",
          body: JSON.stringify({ email, password }),
        });

        API.setToken(data.access_token);
        API.setUser(data.user);
        API.showToast(`Welcome back, ${data.user.display_name}!`, "success");

        setTimeout(() => {
          window.location.href = "dashboard.html";
        }, 500);
      } catch (err) {
        API.showToast(err.message, "error");
      } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = `<span>Sign In</span> <svg style="width: 16px; height: 16px; stroke: currentColor; fill: none; stroke-width: 2.2;" viewBox="0 0 24 24"><line x1="5" y1="12" x2="19" y2="12"></line><polyline points="12 5 19 12 12 19"></polyline></svg>`;
      }
    });

    // Populate Demo Accounts List
    const demoContainer = document.getElementById("demo-account-list");
    if (demoContainer && window.VAULTGUARD_CONFIG?.DEMO_ACCOUNTS) {
      demoContainer.innerHTML = window.VAULTGUARD_CONFIG.DEMO_ACCOUNTS.map((acc) => {
        let iconSvg = `<svg class="icon-svg" viewBox="0 0 24 24"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>`;
        if (acc.role === "OWNER") {
          iconSvg = `<svg class="icon-svg" viewBox="0 0 24 24"><path d="M2 4l3 12h14l3-12-6 7-4-7-4 7-6-7zm3 16h14v2H5v-2z"></path></svg>`;
        } else if (acc.role === "ADMIN") {
          iconSvg = `<svg class="icon-svg" viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>`;
        }

        return `
          <div class="demo-account-list-item demo-btn" data-email="${acc.email}">
            <div class="demo-account-left">
              <span style="color: var(--brand-green);">${iconSvg}</span>
              <span>${acc.name} (${acc.role})</span>
            </div>
            <svg style="width: 14px; height: 14px; stroke: #64748b; fill: none; stroke-width: 2.2;" viewBox="0 0 24 24"><line x1="5" y1="12" x2="19" y2="12"></line><polyline points="12 5 19 12 12 19"></polyline></svg>
          </div>
        `;
      }).join("");

      document.querySelectorAll(".demo-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
          const emailInput = document.getElementById("email");
          const passwordInput = document.getElementById("password");
          if (emailInput && passwordInput) {
            emailInput.value = btn.dataset.email;
            passwordInput.value = "password123";
          }
        });
      });
    }
  }

  // Handle Register
  if (registerForm) {
    registerForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const displayName = document.getElementById("display_name").value;
      const email = document.getElementById("email").value;
      const password = document.getElementById("password").value;
      const role = document.getElementById("role").value;
      const submitBtn = registerForm.querySelector('button[type="submit"]');

      try {
        submitBtn.disabled = true;
        submitBtn.innerText = "Creating account...";

        await API.request("/auth/register", {
          method: "POST",
          body: JSON.stringify({
            display_name: displayName,
            email,
            password,
            role,
          }),
        });

        API.showToast("Account created successfully! Please sign in.", "success");
        setTimeout(() => {
          window.location.href = "login.html";
        }, 800);
      } catch (err) {
        API.showToast(err.message, "error");
      } finally {
        submitBtn.disabled = false;
        submitBtn.innerText = "Register Account";
      }
    });
  }
});
