import type { Metadata } from "next";
import { cookies } from "next/headers";
import Link from "next/link";
import { LogoutButton } from "@/components/LogoutButton";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI Trading Scanner MVP",
  description: "Rule-based market scanner and trade journal"
};

const nav = [
  { href: "/", label: "Dashboard" },
  { href: "/intelligence", label: "Intelligence" },
  { href: "/scanner", label: "Scanner" },
  { href: "/signals", label: "Signals" },
  { href: "/backtests", label: "Backtests" },
  { href: "/scanner/runs", label: "Scan Runs" },
  { href: "/journal", label: "Journal" },
  { href: "/performance", label: "Performance" }
];

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  const isLoggedIn = Boolean((await cookies()).get("scanner_token")?.value);

  return (
    <html lang="en">
      <body>
        <div className="min-h-screen bg-[#0c1017]">
          <header className="border-b border-border bg-surface">
            <div className="mx-auto flex max-w-7xl flex-col gap-3 px-4 py-4 sm:flex-row sm:items-center sm:justify-between">
              <Link href="/" className="text-lg font-semibold text-ink">AI Trading Scanner</Link>
              <nav className="flex flex-wrap gap-2 text-sm">
                {nav.map((item) => (
                  <Link key={item.href} href={item.href} className="rounded-md px-3 py-2 text-muted hover:bg-panelSoft hover:text-ink">
                    {item.label}
                  </Link>
                ))}
                {isLoggedIn ? <LogoutButton /> : null}
              </nav>
            </div>
          </header>
          <main className="mx-auto max-w-7xl px-4 py-6">{children}</main>
        </div>
      </body>
    </html>
  );
}
