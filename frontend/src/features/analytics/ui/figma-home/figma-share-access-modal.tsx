import { useCallback, useEffect, useState, type ReactNode } from "react";
import { motion } from "motion/react";
import {
  Autocomplete,
  Button,
  Label,
  ListBox,
  SearchField,
  Tag,
  TagGroup,
} from "@heroui/react";
import type { Key } from "@heroui/react";
import { isCancel } from "axios";

import {
  searchUsersByEmail,
  type UserSearchItem,
} from "@/shared/api/auth-api";

type TFn = (key: string, opts?: Record<string, unknown>) => string;

type ShareListItem = {
  id: string;
  email: string;
  uuid: string;
  role: string;
};

function toShareListItems(users: UserSearchItem[]): ShareListItem[] {
  return users.map((u) => ({
    id: u.email,
    email: u.email,
    uuid: u.uuid,
    role: u.role,
  }));
}

export type FigmaShareAccessModalProps = {
  t: TFn;
  open: boolean;
  onClose: () => void;
  onConfirm?: (payload: { emails: string[] }) => void | Promise<void>;
};

type BodyProps = Omit<FigmaShareAccessModalProps, "open">;

function FigmaShareAccessModalBody({ t, onClose, onConfirm }: BodyProps) {
  const [selectedEmails, setSelectedEmails] = useState<Key[]>([]);
  const [busy, setBusy] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const [filterText, setFilterText] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");

  const [shareListItems, setShareListItems] = useState<ShareListItem[]>([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);

  useEffect(() => {
    const id = setTimeout(() => {
      setDebouncedQuery(filterText.trim());
    }, 200);
    return () => clearTimeout(id);
  }, [filterText]);

  useEffect(() => {
    if (debouncedQuery.length < 1) {
      setShareListItems([]);
      setSearchError(null);
      setSearchLoading(false);
      return;
    }

    const ac = new AbortController();
    setSearchLoading(true);
    setSearchError(null);

    void (async () => {
      try {
        const users = await searchUsersByEmail({
          query: debouncedQuery,
          limit: 20,
          signal: ac.signal,
        });
        if (ac.signal.aborted) return;
        setShareListItems(toShareListItems(users));
      } catch (e) {
        if (ac.signal.aborted) return;
        if (isCancel(e)) return;
        setShareListItems([]);
        setSearchError(t("home.figma.shareAccessSearchFailed"));
      } finally {
        if (!ac.signal.aborted) setSearchLoading(false);
      }
    })();

    return () => ac.abort();
  }, [debouncedQuery, t]);

  useEffect(() => {
    const handler = (event: KeyboardEvent) => {
      if (event.key === "Escape" && !busy) onClose();
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [onClose, busy]);

  const canConfirm = selectedEmails.length > 0;

  const handleEmailChange = useCallback(
    (value: Key | Key[] | null) => {
      if (Array.isArray(value)) {
        setSelectedEmails(value);
        return;
      }
      setSelectedEmails(value == null ? [] : [value]);
    },
    [],
  );

  const handleRemoveEmails = (keys: Set<Key>) => {
    setSelectedEmails((prev) => prev.filter((key) => !keys.has(key)));
  };

  async function handleConfirm() {
    if (selectedEmails.length === 0) return;
    setSubmitError(null);
    setBusy(true);
    try {
      await Promise.resolve(
        onConfirm?.({ emails: selectedEmails.map(String) }),
      );
      onClose();
    } catch {
      setSubmitError(t("home.figma.shareModalErrorSend"));
    } finally {
      setBusy(false);
    }
  }

  return (
    <motion.div
      className="fixed inset-0 z-110 flex items-center justify-center p-4"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.2 }}
    >
      <motion.div
        className="absolute inset-0"
        style={{ background: "rgba(0,0,0,0.5)", backdropFilter: "blur(4px)" }}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        onClick={() => !busy && onClose()}
      />

      <motion.div
        className="relative z-10 flex h-[300px] w-[400px] flex-col overflow-y-auto rounded-[24px] bg-[#0D0D0D] p-6"
        initial={{ opacity: 0, scale: 1.03, y: 8 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        transition={{ duration: 0.25, ease: [0.32, 0.72, 0, 1] }}
        role="dialog"
        aria-modal="true"
        aria-labelledby="figma-share-access-title"
      >
        <button
          type="button"
          onClick={onClose}
          disabled={busy}
          className="absolute right-4 top-4 z-10 flex size-8 cursor-pointer items-center justify-center rounded-3xl bg-surface transition-colors hover:bg-surface-secondary active:scale-[0.97] disabled:pointer-events-none disabled:opacity-50"
          aria-label={t("common.close")}
        >
          <svg
            width="10"
            height="10"
            viewBox="0 0 10 10"
            fill="none"
            aria-hidden
          >
            <path
              d="M1 1l8 8M9 1L1 9"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
              className="text-muted"
            />
          </svg>
        </button>

        <h2
          id="figma-share-access-title"
          className="shrink-0 pr-12 font-sans text-base font-semibold text-white"
        >
          {t("home.figma.shareAccessModalTitle")}
        </h2>

        <div className="mt-3 flex flex-col gap-3">
          <p className="text-sm leading-snug text-[#9B9B9B]">
            {t("home.figma.shareAccessModalHint")}
          </p>

          <Autocomplete
            allowsEmptyCollection
            placeholder={t("home.figma.shareAccessEmailPlaceholder")}
            selectionMode="multiple"
            value={selectedEmails}
            onChange={handleEmailChange}
            isDisabled={busy}
            className="w-full"
            items={shareListItems as Iterable<ShareListItem>}
          >
            <Label className="text-sm text-white">
              {t("home.figma.shareAccessEmailLabel")}
            </Label>
            <Autocomplete.Trigger className="min-h-10 rounded-xl border-0 bg-[#1A1A1A]">
              <Autocomplete.Value className="text-sm text-[#fcfcfc]">
                {({
                  defaultChildren,
                  isPlaceholder,
                  state,
                }: {
                  defaultChildren: ReactNode;
                  isPlaceholder: boolean;
                  state: { selectedItems: Array<{ key: Key }> };
                }) => {
                  if (isPlaceholder || state.selectedItems.length === 0) {
                    return defaultChildren;
                  }

                  return (
                    <TagGroup size="sm" onRemove={handleRemoveEmails}>
                      <TagGroup.List className="gap-1.5">
                        {state.selectedItems.map((item) => (
                          <Tag
                            key={String(item.key)}
                            id={String(item.key)}
                            className="border-0 bg-[#2a2a2a] text-white"
                          >
                            {String(item.key)}
                          </Tag>
                        ))}
                      </TagGroup.List>
                    </TagGroup>
                  );
                }}
              </Autocomplete.Value>
              <Autocomplete.ClearButton />
              <Autocomplete.Indicator className="text-white/60" />
            </Autocomplete.Trigger>
            <Autocomplete.Popover>
              <Autocomplete.Filter
                filter={() => true}
                inputValue={filterText}
                onInputChange={setFilterText}
              >
                <SearchField variant="secondary">
                  <SearchField.Group>
                    <SearchField.SearchIcon />
                    <SearchField.Input
                      placeholder={t("home.figma.shareAccessSearchPlaceholder")}
                    />
                    <SearchField.ClearButton />
                  </SearchField.Group>
                </SearchField>
                {searchLoading ? (
                  <p className="px-3 py-2 text-xs text-[#9B9B9B]">…</p>
                ) : null}
                {searchError ? (
                  <p className="px-3 py-1.5 text-xs text-danger">
                    {searchError}
                  </p>
                ) : null}
                <ListBox
                  items={shareListItems as Iterable<ShareListItem>}
                  dependencies={[
                    debouncedQuery,
                    shareListItems,
                    searchLoading,
                    searchError,
                  ]}
                >
                  {(item: ShareListItem) => (
                    <ListBox.Item
                      id={item.id}
                      key={item.id}
                      textValue={item.email}
                    >
                      {item.email}
                      <ListBox.ItemIndicator />
                    </ListBox.Item>
                  )}
                </ListBox>
              </Autocomplete.Filter>
            </Autocomplete.Popover>
          </Autocomplete>
        </div>

        {submitError ? (
          <p className="mt-2 text-xs text-danger shrink-0">{submitError}</p>
        ) : null}

        <div className="mt-6 shrink-0">
          <Button
            className="h-10 w-full rounded-full bg-white text-sm font-medium text-black hover:bg-zinc-200 disabled:opacity-40"
            isDisabled={!canConfirm || busy}
            onPress={() => void handleConfirm()}
          >
            {busy ? "…" : t("home.figma.shareAccessModalConfirm")}
          </Button>
        </div>
      </motion.div>
    </motion.div>
  );
}

export function FigmaShareAccessModal({
  open,
  ...rest
}: FigmaShareAccessModalProps) {
  if (!open) return null;
  return <FigmaShareAccessModalBody {...rest} />;
}
