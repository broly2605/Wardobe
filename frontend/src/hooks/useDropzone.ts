"use client";

import { useCallback, useRef, useState, type DragEvent } from "react";

const ACCEPTED = ["image/jpeg", "image/png", "image/webp"];
const MAX_BYTES = 10 * 1024 * 1024; // 10MB, matches backend guidance

export interface DropzoneResult {
  accepted: File[];
  rejected: { file: File; reason: string }[];
}

function validate(files: File[]): DropzoneResult {
  const accepted: File[] = [];
  const rejected: { file: File; reason: string }[] = [];
  for (const f of files) {
    if (!ACCEPTED.includes(f.type)) {
      rejected.push({ file: f, reason: "Unsupported type (use JPEG/PNG/WebP)" });
    } else if (f.size > MAX_BYTES) {
      rejected.push({ file: f, reason: "Too large (max 10MB)" });
    } else {
      accepted.push(f);
    }
  }
  return { accepted, rejected };
}

export function useDropzone(onFiles: (result: DropzoneResult) => void) {
  const [isDragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement | null>(null);
  const depth = useRef(0);

  const onDragEnter = useCallback((e: DragEvent) => {
    e.preventDefault();
    depth.current += 1;
    if (e.dataTransfer?.types?.includes("Files")) setDragging(true);
  }, []);

  const onDragOver = useCallback((e: DragEvent) => {
    e.preventDefault();
  }, []);

  const onDragLeave = useCallback((e: DragEvent) => {
    e.preventDefault();
    depth.current -= 1;
    if (depth.current <= 0) {
      depth.current = 0;
      setDragging(false);
    }
  }, []);

  const onDrop = useCallback(
    (e: DragEvent) => {
      e.preventDefault();
      depth.current = 0;
      setDragging(false);
      const files = Array.from(e.dataTransfer?.files ?? []);
      if (files.length) onFiles(validate(files));
    },
    [onFiles],
  );

  const openFileDialog = useCallback(() => inputRef.current?.click(), []);

  const onInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = Array.from(e.target.files ?? []);
      if (files.length) onFiles(validate(files));
      e.target.value = ""; // allow re-selecting the same file
    },
    [onFiles],
  );

  return {
    isDragging,
    inputRef,
    openFileDialog,
    dropzoneProps: { onDragEnter, onDragOver, onDragLeave, onDrop },
    inputProps: {
      ref: inputRef,
      type: "file" as const,
      accept: ACCEPTED.join(","),
      multiple: true,
      className: "hidden",
      onChange: onInputChange,
    },
  };
}
