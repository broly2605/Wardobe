"use client";

import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";

export function ConnectionError({ message }: { message: string }) {
  return (
    <Card className="mx-auto max-w-lg p-8 text-center">
      <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-rose-500/15 text-2xl">
        ⚠️
      </div>
      <h2 className="text-lg font-semibold text-foreground">
        Something went wrong
      </h2>
      <p className="mt-2 text-sm text-muted">{message}</p>
      <p className="mt-1 text-xs text-muted">
        Make sure the backend is running on port 8000.
      </p>
      <div className="mt-6">
        <Button onClick={() => window.location.reload()}>Retry</Button>
      </div>
    </Card>
  );
}
