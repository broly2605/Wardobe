"use client";

import type { ReactNode } from "react";
import { Sidebar } from "./Sidebar";
import { MobileNav } from "./MobileNav";
import { TopBar } from "./TopBar";
import { PageTransition } from "./PageTransition";

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen">
      <Sidebar />
      <div className="lg:pl-64">
        <div className="mx-auto max-w-6xl px-4 pb-28 pt-4 lg:pb-10">
          <TopBar />
          <main>
            <PageTransition>{children}</PageTransition>
          </main>
        </div>
      </div>
      <MobileNav />
    </div>
  );
}
