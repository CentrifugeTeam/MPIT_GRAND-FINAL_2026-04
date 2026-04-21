import type { QueryInterpretation } from "@/entities/analytics";

export type InterpretationHint = {
  confidence: number;
  warnings: string[];
  suggestions: string[];
  glossaryTermsCount?: number;
};

function toHint(interp: QueryInterpretation, glossaryTermsCount?: number): InterpretationHint {
  return {
    confidence: interp.confidence,
    warnings: interp.warnings ?? [],
    suggestions: interp.suggestions ?? [],
    glossaryTermsCount,
  };
}

export function interpretationToHint(
  interp: QueryInterpretation | undefined,
  glossaryTermsCount?: number,
): InterpretationHint | null {
  if (!interp || typeof interp.confidence !== "number") return null;
  return toHint(interp, glossaryTermsCount);
}
