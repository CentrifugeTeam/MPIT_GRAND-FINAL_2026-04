export type ParsedChatInvitePayload = {
  invite_id: string;
  conversation_id: string;
  owner_email: string;
  chat_title: string;
};

export function parseChatInvitePayload(
  p: Record<string, unknown> | null | undefined,
): ParsedChatInvitePayload {
  const o = p && typeof p === "object" ? p : {};
  return {
    invite_id: String(o.invite_id ?? ""),
    conversation_id: String(o.conversation_id ?? ""),
    owner_email: String(o.owner_email ?? ""),
    chat_title: String(o.chat_title ?? ""),
  };
}

const INITIALS_RE = /[^\s@.]+/g;

/** Two-letter initials for avatar (email local part, or any words in fallback). */
export function getInitialsFromText(raw: string, fallback: string): string {
  const s = (raw || fallback || "").trim();
  if (!s) return "?";
  const at = s.indexOf("@");
  const local = at >= 0 ? s.slice(0, at) : s;
  if (local.length >= 2) {
    if (/[._-]/.test(local)) {
      const parts = local.split(/[._-]+/).filter(Boolean);
      if (parts.length >= 2) {
        return (parts[0]![0]! + parts[1]![0]!).toLowerCase();
      }
    }
    return local.slice(0, 2).toLowerCase();
  }
  const words = s.match(INITIALS_RE) ?? [s];
  if (words.length >= 2) {
    return (words[0]![0]! + words[1]![0]!).toLowerCase();
  }
  return s.slice(0, 2).toLowerCase();
}
