import { useEffect, useState } from "react";
import { motion } from "motion/react";
import {
  Autocomplete,
  Button,
  Label,
  ListBox,
  SearchField,
  Tag,
  TagGroup,
  Tabs,
  useFilter,
} from "@heroui/react";
import type { Key } from "@heroui/react";

type TFn = (key: string, opts?: Record<string, unknown>) => string;

const SHARE_EMAIL_OPTIONS = [
  "owner@company.com",
  "analyst@company.com",
  "manager@company.com",
];

type ShareAccessMode = "readonly" | "editable";

export type FigmaShareAccessModalProps = {
  t: TFn;
  open: boolean;
  onClose: () => void;
  onConfirm?: (payload: { mode: ShareAccessMode; emails: string[] }) => void;
};

type BodyProps = Omit<FigmaShareAccessModalProps, "open">;

function FigmaShareAccessModalBody({ t, onClose, onConfirm }: BodyProps) {
  const { contains } = useFilter({ sensitivity: "base" });
  const [mode, setMode] = useState<ShareAccessMode>("readonly");
  const [selectedEmails, setSelectedEmails] = useState<Key[]>([]);

  useEffect(() => {
    const handler = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [onClose]);

  const canConfirm = selectedEmails.length > 0;

  function handleEmailChange(value: Key | Key[] | null) {
    if (Array.isArray(value)) {
      setSelectedEmails(value);
      return;
    }
    setSelectedEmails(value == null ? [] : [value]);
  }

  function handleRemoveEmails(keys: Set<Key>) {
    setSelectedEmails((prev) => prev.filter((key) => !keys.has(key)));
  }

  function handleConfirm() {
    if (selectedEmails.length === 0) return;
    onConfirm?.({ mode, emails: selectedEmails.map(String) });
    onClose();
  }

  return (
    <motion.div
      className="fixed inset-0 z-110 flex items-start justify-center pt-[18vh]"
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
        onClick={onClose}
      />

      <motion.div
        className="relative z-10 w-full max-w-[480px] overflow-hidden rounded-[24px] border border-solid border-[#28282c] bg-[#18181b]"
        initial={{ opacity: 0, scale: 1.03, y: 8 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        transition={{ duration: 0.25, ease: [0.32, 0.72, 0, 1] }}
        role="dialog"
        aria-modal="true"
        aria-labelledby="figma-share-access-title"
      >
        <div className="flex items-center justify-between border-b border-[#28282c] px-5 py-4">
          <h2
            id="figma-share-access-title"
            className="font-sans text-base font-medium text-[#fcfcfc]"
          >
            {t("home.figma.shareAccessModalTitle")}
          </h2>
          <Button
            isIconOnly
            size="sm"
            aria-label={t("home.figma.shareAccessModalClose")}
            className="size-8 rounded-[24px] bg-[#27272a] text-[#a1a1aa] hover:bg-[#323236] hover:text-[#fcfcfc]"
            onPress={onClose}
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
              />
            </svg>
          </Button>
        </div>

        <div className="flex flex-col gap-4 px-5 py-4">
          <p className="text-sm leading-snug text-[#a1a1aa]">
            {t("home.figma.shareAccessModalHint")}
          </p>

          <Tabs
            selectedKey={mode}
            onSelectionChange={(key) => setMode(key as ShareAccessMode)}
            className="w-full"
          >
            <Tabs.ListContainer>
              <Tabs.List
                aria-label={t("home.figma.shareAccessModalTabsAria")}
                className="w-full rounded-[28px] bg-[#27272a] p-1 gap-1"
              >
                <Tabs.Tab
                  id="readonly"
                  className="rounded-[20px] px-3 py-1.5 text-sm font-medium text-[#a1a1aa] data-[selected=true]:text-[#fcfcfc]"
                >
                  {t("home.figma.shareAccessReadOnly")}
                  <Tabs.Indicator className="rounded-[20px] bg-[#3f3f46]" />
                </Tabs.Tab>
                <Tabs.Tab
                  id="editable"
                  className="rounded-[20px] px-3 py-1.5 text-sm font-medium text-[#a1a1aa] data-[selected=true]:text-[#fcfcfc]"
                >
                  {t("home.figma.shareAccessEditable")}
                  <Tabs.Indicator className="rounded-[20px] bg-[#3f3f46]" />
                </Tabs.Tab>
              </Tabs.List>
            </Tabs.ListContainer>
          </Tabs>

          <Autocomplete
            placeholder={t("home.figma.shareAccessEmailPlaceholder")}
            selectionMode="multiple"
            value={selectedEmails}
            onChange={handleEmailChange}
            className="w-full"
          >
            <Label>{t("home.figma.shareAccessEmailLabel")}</Label>
            <Autocomplete.Trigger className="rounded-xl bg-[#27272a]">
              <Autocomplete.Value className="text-sm text-[#fcfcfc]">
                {({ defaultChildren, isPlaceholder, state }: any) => {
                  if (isPlaceholder || state.selectedItems.length === 0) {
                    return defaultChildren;
                  }

                  return (
                    <TagGroup size="sm" onRemove={handleRemoveEmails}>
                      <TagGroup.List>
                        {state.selectedItems.map((item: { key: Key }) => (
                          <Tag key={String(item.key)} id={String(item.key)}>
                            {String(item.key)}
                          </Tag>
                        ))}
                      </TagGroup.List>
                    </TagGroup>
                  );
                }}
              </Autocomplete.Value>
              <Autocomplete.ClearButton />
              <Autocomplete.Indicator />
            </Autocomplete.Trigger>
            <Autocomplete.Popover>
              <Autocomplete.Filter filter={contains}>
                <SearchField variant="secondary">
                  <SearchField.Group>
                    <SearchField.SearchIcon />
                    <SearchField.Input
                      placeholder={t("home.figma.shareAccessSearchPlaceholder")}
                    />
                    <SearchField.ClearButton />
                  </SearchField.Group>
                </SearchField>
                <ListBox>
                  {SHARE_EMAIL_OPTIONS.map((email) => (
                    <ListBox.Item key={email} id={email} textValue={email}>
                      {email}
                      <ListBox.ItemIndicator />
                    </ListBox.Item>
                  ))}
                </ListBox>
              </Autocomplete.Filter>
            </Autocomplete.Popover>
          </Autocomplete>
        </div>

        <div className="flex justify-end gap-2 border-t border-[#28282c] px-5 py-4">
          <Button
            className="rounded-[24px] bg-[#27272a] px-4 py-2 text-sm font-medium text-[#fcfcfc] hover:bg-[#323236]"
            onPress={onClose}
          >
            {t("home.figma.shareAccessModalCancel")}
          </Button>
          <Button
            className="rounded-[24px] bg-[#fcfcfc] px-4 py-2 text-sm font-medium text-[#18181b] hover:bg-[#e4e4e7] disabled:opacity-40"
            isDisabled={!canConfirm}
            onPress={handleConfirm}
          >
            {t("home.figma.shareAccessModalConfirm")}
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

