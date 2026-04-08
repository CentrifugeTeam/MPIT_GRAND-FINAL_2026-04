import React from "react";
import { Button, Disclosure, DisclosureGroup, Separator } from "@heroui/react";
import { Icon } from "@iconify/react";
import qrCodeImage from "./assets/qr-code.png";

export function ProductsPage() {
  const [expandedKeys, setExpandedKeys] = React.useState(
    new Set<string | number>(["preview"]),
  );

  return (
    <div className="flex justify-center py-4">
      <div className="w-92.25">
        <DisclosureGroup
          allowsMultipleExpanded
          expandedKeys={expandedKeys}
          onExpandedChange={setExpandedKeys}
        >
          <Disclosure aria-label="Preview HeroUI Native" id="preview">
            <Disclosure.Heading>
              <Button slot="trigger" variant="ghost" fullWidth>
                <div className="flex w-full items-center gap-2">
                  <Icon icon="tabler:qrcode" width={16} height={16} />
                  Preview HeroUI Native
                </div>
                <Disclosure.Indicator />
              </Button>
            </Disclosure.Heading>
            <Disclosure.Content>
              <Disclosure.Body className="flex flex-col items-center gap-4 rounded-3xl bg-surface px-6 py-4 text-center">
                <p className="text-xs text-muted">
                  Scan this QR code with your camera app to preview the HeroUI
                  native components.
                </p>
                <img
                  alt="Expo Go QR Code"
                  className="h-45 w-45 object-cover"
                  src={qrCodeImage}
                />
                <p className="text-xs text-muted">
                  Expo must be installed on your device.
                </p>
                <Button variant="primary">
                  <Icon icon="tabler:brand-apple-filled" width={16} height={16} />
                  Download on App Store
                </Button>
              </Disclosure.Body>
            </Disclosure.Content>
          </Disclosure>

          <Separator />

          <Disclosure aria-label="Download App" id="download">
            <Disclosure.Heading>
              <Button slot="trigger" variant="ghost" fullWidth>
                <div className="flex w-full items-center gap-2">
                  <Icon
                    icon="tabler:brand-apple-filled"
                    width={16}
                    height={16}
                  />
                  Download App
                </div>
                <Disclosure.Indicator />
              </Button>
            </Disclosure.Heading>
            <Disclosure.Content>
              <Disclosure.Body className="flex flex-col items-center gap-4 rounded-3xl bg-surface px-6 py-4 text-center">
                <Button variant="primary">
                  <Icon
                    icon="tabler:brand-apple-filled"
                    width={16}
                    height={16}
                  />
                  Download on App Store
                </Button>
              </Disclosure.Body>
            </Disclosure.Content>
          </Disclosure>
        </DisclosureGroup>
      </div>
    </div>
  );
}
