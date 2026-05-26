import { execSync } from "child_process";
import fs from "fs";
import path from "path";

const root = path.resolve(import.meta.dirname, "..");
const content = execSync("git show HEAD:apps/web/src/app/page.tsx", {
  encoding: "utf8",
  cwd: root,
});
const lines = content.split(/\r?\n/);
let body = lines.slice(2723, 3113).join("\n");

for (const v of ["setEditingItem", "handleSaveEdit", "editingItem"]) {
  body = body.replace(new RegExp(`\\b${v}\\b`, "g"), `d.${v}`);
}

const file = `"use client";

import React from "react";
import { Check, Edit2 } from "lucide-react";
import type { EntityTab } from "@/lib/types";
import { useDashboard } from "./DashboardProvider";

export function ValidationEditModal() {
  const d = useDashboard();
  return (
    <>
${body}
    </>
  );
}
`;

const out = path.join(root, "apps/web/src/components/dashboard/ValidationEditModal.tsx");
fs.writeFileSync(out, file);
console.log("Fixed", out);
