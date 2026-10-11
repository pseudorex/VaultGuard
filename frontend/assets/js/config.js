// VaultGuard Frontend Configuration
window.VAULTGUARD_CONFIG = {
  API_BASE_URL: "http://127.0.0.1:8000/api",
  DEMO_ACCOUNTS: [
    { email: "owner@demo.com", role: "OWNER", name: "Owner Demo" },
    { email: "custodian1@demo.com", role: "CUSTODIAN", name: "Alice (Custodian 1)" },
    { email: "custodian2@demo.com", role: "CUSTODIAN", name: "Bob (Custodian 2)" },
    { email: "custodian3@demo.com", role: "CUSTODIAN", name: "Carol (Custodian 3)" },
    { email: "admin@demo.com", role: "ADMIN", name: "Admin" }
  ]
};
