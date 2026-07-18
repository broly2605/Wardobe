"use client";

import { useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import type { AppStatus, ScanStatus } from "@/lib/types";
import { useTheme } from "@/providers/ThemeProvider";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Skeleton } from "@/components/ui/Skeleton";
import { ConnectionError } from "@/components/ConnectionError";
import { MoonIcon, SparklesIcon, SunIcon } from "@/components/icons";
import { humanize } from "@/lib/format";

export default function SettingsPage() {
  const { theme, setTheme } = useTheme();
  const [appStatus, setAppStatus] = useState<AppStatus | null>(null);
  const [scanStatus, setScanStatus] = useState<ScanStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    Promise.all([api.appStatus(), api.scanStatus()])
      .then(([app, scan]) => {
        if (!alive) return;
        setAppStatus(app);
        setScanStatus(scan);
      })
      .catch((e) => {
        if (!alive) return;
        setError(e instanceof ApiError ? e.message : "Failed to load settings.");
      })
      .finally(() => alive && setLoading(false));
    return () => {
      alive = false;
    };
  }, []);

  if (error) return <ConnectionError message={error} />;

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      {/* Appearance */}
      <Card className="p-5">
        <h3 className="text-base font-semibold text-foreground">Appearance</h3>
        <p className="mt-1 text-sm text-muted">
          Choose how Wardrobe looks. Your preference is saved on this device.
        </p>
        <div className="mt-4 grid grid-cols-2 gap-3">
          <ThemeOption
            active={theme === "light"}
            onClick={() => setTheme("light")}
            icon={<SunIcon width={20} height={20} />}
            label="Light"
          />
          <ThemeOption
            active={theme === "dark"}
            onClick={() => setTheme("dark")}
            icon={<MoonIcon width={20} height={20} />}
            label="Dark"
          />
        </div>
      </Card>

      {/* AI / scanner status */}
      <Card className="p-5">
        <h3 className="flex items-center gap-2 text-base font-semibold text-foreground">
          <SparklesIcon width={18} height={18} /> Scanner & AI
        </h3>
        <p className="mt-1 text-sm text-muted">
          Read-only status of the detection pipeline, reported by the backend.
        </p>

        {loading ? (
          <div className="mt-4 space-y-3">
            <Skeleton className="h-6 w-full" />
            <Skeleton className="h-6 w-full" />
            <Skeleton className="h-6 w-2/3" />
          </div>
        ) : (
          <dl className="mt-4 space-y-3 text-sm">
            <Row label="AI vision tagging">
              <Badge tone={appStatus?.ai_enabled ? "success" : "default"}>
                {appStatus?.ai_enabled ? "Enabled" : "Heuristic fallback"}
              </Badge>
            </Row>
            {appStatus?.ai_model && (
              <Row label="Vision model">
                <span className="font-medium text-foreground">
                  {appStatus.ai_model}
                </span>
              </Row>
            )}
            <Row label="Background removal">
              <Badge
                tone={
                  scanStatus?.background_removal_available
                    ? "success"
                    : "warning"
                }
              >
                {scanStatus?.background_removal_available
                  ? "Available"
                  : "Unavailable"}
              </Badge>
            </Row>
            <Row label="Weather provider">
              <span className="font-medium text-foreground">
                {humanize(appStatus?.weather_provider)}
              </span>
            </Row>
            <Row label="Environment">
              <span className="font-medium text-foreground">
                {humanize(appStatus?.app_env)}
              </span>
            </Row>
          </dl>
        )}

        {!loading && scanStatus && (
          <div className="mt-4 border-t border-border pt-4">
            <p className="mb-2 text-xs font-medium uppercase tracking-wide text-muted">
              Detected attributes
            </p>
            <div className="flex flex-wrap gap-1.5">
              {scanStatus.detected_attributes.map((a) => (
                <Badge key={a}>{humanize(a)}</Badge>
              ))}
            </div>
          </div>
        )}

        {!loading && !appStatus?.ai_enabled && (
          <p className="mt-4 rounded-xl bg-amber-500/10 p-3 text-xs text-amber-600 dark:text-amber-400">
            AI vision is off. Set <code>OPENAI_API_KEY</code> in the backend
            environment to enable richer auto-tagging. Scans still work using
            the computer-vision fallback.
          </p>
        )}
      </Card>

      <p className="text-center text-xs text-muted">
        Wardrobe · single-user local build
      </p>
    </div>
  );
}

function ThemeOption({
  active,
  onClick,
  icon,
  label,
}: {
  active: boolean;
  onClick: () => void;
  icon: React.ReactNode;
  label: string;
}) {
  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-3 rounded-xl border px-4 py-3 text-sm font-medium transition-all ${
        active
          ? "border-brand bg-brand-soft text-brand"
          : "border-border text-muted hover:border-brand/40 hover:text-foreground"
      }`}
    >
      {icon}
      {label}
    </button>
  );
}

function Row({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex items-center justify-between">
      <dt className="text-muted">{label}</dt>
      <dd>{children}</dd>
    </div>
  );
}
