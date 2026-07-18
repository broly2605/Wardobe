import type { Color } from "@/lib/types";

/** A row of overlapping color swatches (primary/secondary detected colors). */
export function ColorDots({
  colors,
  size = 18,
}: {
  colors: Pick<Color, "hex" | "name">[];
  size?: number;
}) {
  if (!colors.length) return null;
  return (
    <div className="flex items-center">
      {colors.map((c, i) => (
        <span
          key={`${c.hex}-${i}`}
          title={c.name}
          className="rounded-full border-2 border-surface"
          style={{
            backgroundColor: c.hex,
            width: size,
            height: size,
            marginLeft: i === 0 ? 0 : -size / 3,
            zIndex: colors.length - i,
          }}
        />
      ))}
    </div>
  );
}
