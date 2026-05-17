"use client";

import { LogOut } from "lucide-react";

export function LogoutButton() {
  function logout() {
    const secureCookie = window.location.protocol === "https:" || process.env.NEXT_PUBLIC_APP_ENV === "production";
    document.cookie = `scanner_token=; path=/; max-age=0; SameSite=Lax${secureCookie ? "; Secure" : ""}`;
    window.location.href = "/login";
  }

  return (
    <button onClick={logout} className="inline-flex items-center gap-2 rounded-md px-3 py-2 text-sm text-muted hover:bg-panelSoft hover:text-ink">
      <LogOut size={16} />
      Logout
    </button>
  );
}
