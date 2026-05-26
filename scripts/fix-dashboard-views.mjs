import fs from "fs";
import path from "path";

const root = path.resolve(import.meta.dirname, "..");
const viewsDir = path.join(root, "apps/web/src/components/dashboard/views");

const entityNames = [
  "projetos",
  "eventos",
  "producoes",
  "financiamentos",
  "orientacoes",
  "formacoes_academicas",
  "producoes_tecnicas",
  "premios",
  "grupos_pesquisa",
];

for (const file of fs.readdirSync(viewsDir)) {
  if (!file.endsWith(".tsx")) continue;
  const p = path.join(viewsDir, file);
  let s = fs.readFileSync(p, "utf8");

  // Remove wrapper closing from mainTab conditional
  s = s.replace(/\n\s*\)\}\s*\n\s*\);\s*\n\}/, "\n  );\n}");

  for (const name of entityNames) {
    s = s.replaceAll(`"d.${name}"`, `"${name}"`);
    s = s.replaceAll(`'d.${name}'`, `'${name}'`);
    s = s.replaceAll(`tab="d.${name}"`, `tab="${name}"`);
  }

  fs.writeFileSync(p, s);
  console.log("fixed", file);
}
